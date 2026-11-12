extends Demo
## Пробная демка low poly, камера за спиной (#108) для `lowpoly_test`: не жанр, а проверка
## основы. Матрос бежит по цепочке неровных песчаных островов (`LowpolyTerrain`) над морем к флагу: стрелки ход относительно камеры,
## A прыжок через провалы. На островах дублоны, скелеты ходят поперёк, в углах бочки, сундуки и
## пушки. Упал в море или задел скелета: минус жизнь и назад на край острова, жизней три.
## Камера `LowpolyFollowCam`, модели слотов через `spawn_model`, общие баги через хуки `Demo`.
## Бот WIN обходит скелетов и прыгает у края, LOSE бежит прямо без прыжков.

const ISLANDS := 9
const SPEED := 6.0
const JUMP := 8.5
const GRAVITY := 20.0
const COYOTE := 0.15
const SEA_Y := -3.0
const LIVES := 3
const ENEMY_SPEED := 1.6
const ENEMY_REACH := 2.2
const HIT_RADIUS := 0.8
const COIN_RADIUS := 0.9
const SAFE_SECONDS := 1.0
const MELODY := [0, null, 4, 7, 12, null, 7, 4, 5, null, 9, 12, 17, null, 12, 9,
	7, null, 11, 14, 19, null, 14, 11, 12, null, 7, null, 4, 2, 0, null]
const BASS := [-12, -12, -5, -5, -7, -7, 0, 0, -5, -5, 2, 2, -12, -12, -5, -5]
const HEART := [".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."]

## Острова: центр верхней грани и размеры по x и z. Вперёд это −Z.
var centers: Array[Vector3] = []
var sizes: Array[Vector2] = []
var coins: Array[Vector3] = []
var taken: Array[bool] = []
var coin_nodes: Array[LowpolyModel] = []
## Скелеты: место, остров, направление шага по x.
var enemies: Array[Vector3] = []
var enemy_island: Array[int] = []
var enemy_dir: Array[float] = []
var enemy_nodes: Array[LowpolyModel] = []
var terrains: Array[LowpolyTerrain] = []
var shadows: Array[MeshInstance3D] = []
var flag_pos := Vector3.ZERO
var flag: LowpolyModel
var hero: LowpolyModel
var cam: LowpolyFollowCam
var hero_pos := Vector3.ZERO
var hero_vy := 0.0
var heading := 0.0
var grounded := true
## Остров, на котором герой стоял последним: сюда его возвращает потеря жизни.
var island := 0
var lives := LIVES
var collected := 0
## Сколько метров пробежал и от чего терял жизни (проверки).
var travelled := 0.0
var deaths: Array[String] = []
var _air := 0.0
var _safe := 0.0
var _moving := false
var _axis := Vector2.ZERO
var _t := 0.0
var _bot_jump_wait := 0.0
var _bot_aligned := true
var _coin_sfx: AudioStreamPlayer
var _jump_sfx: AudioStreamPlayer
var _hurt_sfx: AudioStreamPlayer


func _placeholder_slots() -> Array[String]:
	return ["enemy", "coin", "prop"]


func _on_start() -> void:
	lowpoly_screen(_draw_hud)
	cam = LowpolyFollowCam.make(lowpoly.tuning)
	_build_level()
	hero = spawn_model("hero", "hero")
	hero_pos = centers[0] + Vector3(0.0, 0.0, sizes[0].y / 2.0 - 1.5)
	hero_pos.y = terrains[0].height_at(hero_pos.x, hero_pos.z)
	cam.step(0.0, hero_pos, heading, false)
	var quiet := -80.0 if embedded else 0.0
	var music := Sfx.music(Sfx.tracker_loop(MELODY, BASS, 132.0), -10.0 + quiet)
	add_child(music)
	bug_music = music
	music.play()
	_coin_sfx = Sfx.player(Sfx.blip(1318.0, 0.12, 0.35, 14.0), -6.0 + quiet)
	_jump_sfx = Sfx.player(Sfx.blip(520.0, 0.1, 0.3, 10.0), -8.0 + quiet)
	_hurt_sfx = Sfx.player(Sfx.thud(0.16, 0.5), -4.0 + quiet)
	for p: AudioStreamPlayer in [_coin_sfx, _jump_sfx, _hurt_sfx]:
		add_child(p)
	_sync()


func _build_level() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed if record != null else 1, ":behind"))
	var c := Vector3.ZERO
	var prop_names := ["barrel", "chest", "cannon", "rock"]
	for i in ISLANDS:
		# Остров со скелетом длиннее: есть где приземлиться до него и выровняться после.
		var guarded := i >= 2 and i % 2 == 0 and i < ISLANDS - 1
		var s := Vector2(6.0, rng.randf_range(10.5, 12.0) if guarded else rng.randf_range(6.0, 9.0))
		if i > 0:
			var gap := rng.randf_range(1.4, 2.2)
			c = Vector3(c.x + rng.randf_range(-2.0, 2.0), c.y + rng.randf_range(-0.6, 0.6),
					c.z - sizes[i - 1].y / 2.0 - gap - s.y / 2.0)
		centers.append(c)
		sizes.append(s)
		# Остров: сетка в метр, бугры и ямки, край осыпается; по бокам скала до воды.
		var t := LowpolyTerrain.make(c - Vector3(s.x / 2.0, 0.0, s.y / 2.0), 1.0, int(s.x), roundi(s.y))
		t.cell = 1.0
		t.origin = c - Vector3(t.nx / 2.0, 0.0, t.nz / 2.0)
		sizes[i] = Vector2(t.nx, t.nz)
		for iz in t.nz + 1:
			for ix in t.nx + 1:
				var edge := ix == 0 or iz == 0 or ix == t.nx or iz == t.nz
				t.set_h(ix, iz, rng.randf_range(-0.14, 0.14) - (0.3 if edge else 0.0))
		t.build(lowpoly, lowpoly_texture("sand"), 3.0, lowpoly_texture("rock"), SEA_Y - 0.2)
		terrains.append(t)
		if guarded:
			enemies.append(c + Vector3(rng.randf_range(-ENEMY_REACH, ENEMY_REACH), 0.0, 0.0))
			shadows.append(lowpoly.add_shadow(0.4))
			enemy_island.append(i)
			enemy_dir.append(1.0 if rng.randf() < 0.5 else -1.0)
			enemy_nodes.append(spawn_model("enemy", "enemy"))
		elif i > 0:
			var prop := spawn_model("prop", prop_names[rng.randi_range(0, prop_names.size() - 1)])
			prop.position = c + Vector3((1.0 if rng.randf() < 0.5 else -1.0) * 2.3, 0.0, rng.randf_range(-1.0, 1.0) * (s.y / 2.0 - 1.0))
			prop.position.y = t.height_at(prop.position.x, prop.position.z) - 0.05
			prop.rotation.y = rng.randf_range(-PI, PI)
		if i > 0 and i < ISLANDS - 1:
			for k in rng.randi_range(1, 2):
				var at := c + Vector3(rng.randf_range(-1.5, 1.5), 0.0, (0.5 - k) * s.y * 0.45)
				coins.append(Vector3(at.x, t.height_at(at.x, at.z) + 0.5, at.z))
				taken.append(false)
				coin_nodes.append(spawn_model("coin", "coin"))
	var last := ISLANDS - 1
	flag_pos = centers[last] - Vector3(0.0, 0.0, sizes[last].y / 2.0 - 1.2)
	flag = spawn_model("finish", "flag")
	flag_pos.y = terrains[last].height_at(flag_pos.x, flag_pos.z)
	flag.position = flag_pos
	var mid := (centers[0].z + centers[last].z) / 2.0
	lowpoly.add_plane(Vector3(0.0, SEA_Y, mid), Vector2(360.0, 360.0), lowpoly_texture("water"), 6.0,
			{"uv_scroll": Vector2(0.02, 0.035), "affine": 0.0})
	shadows.append(lowpoly.add_shadow(0.42))


func _game_input(event: InputEvent) -> void:
	if GameInput.is_a(event):
		bug_press(_jump)


## Бот WIN: к ближнему краю следующего острова, прыжок у края; скелета обходит с той стороны,
## где его нет, или ждёт, пока тот уйдёт с середины. LOSE: вперёд без прыжков.
func _bot_step(delta: float) -> void:
	_bot_jump_wait = maxf(_bot_jump_wait - delta, 0.0)
	if active_bot_mode() == AutoTest.BotMode.LOSE:
		_axis = cam.to_axis(Vector3(0.0, 0.0, -1.0))
		return
	var c := centers[island]
	var far_edge := c.z - sizes[island].y / 2.0
	var target := flag_pos
	var aligned := true
	if island < ISLANDS - 1:
		var n := centers[island + 1]
		target = Vector3(clampf(hero_pos.x, n.x - 2.0, n.x + 2.0), 0.0, n.z + sizes[island + 1].y / 2.0 - 1.0)
		aligned = absf(hero_pos.x - n.x) < 2.5
		# У края не напротив следующего острова: сначала вбок, прыжок потом.
		if not aligned and hero_pos.z - far_edge < 1.8:
			target = Vector3(n.x, 0.0, hero_pos.z)
	# По дороге дублоны своего острова, что ещё впереди.
	for i in coins.size():
		if not taken[i] and _island_under(coins[i]) == island and coins[i].z < hero_pos.z - 0.3 and coins[i].z > far_edge + 1.8:
			target = Vector3(coins[i].x, 0.0, coins[i].z)
			break
	for i in enemies.size():
		if enemy_island[i] != island or hero_pos.z < enemies[i].z - 0.6:
			continue
		var off := enemies[i].x - c.x
		var leaving := signf(enemy_dir[i]) == signf(off)
		if (absf(off) < 1.0 or (absf(off) < 1.6 and not leaving)) and hero_pos.z - enemies[i].z < 3.6:
			_axis = Vector2.ZERO
			return
		target = Vector3(c.x - signf(off if off != 0.0 else 1.0) * 2.2, 0.0, enemies[i].z - 1.4)
	var to := Vector3(target.x - hero_pos.x, 0.0, target.z - hero_pos.z)
	_axis = cam.to_axis(to.normalized()) if to.length() > 0.2 else Vector2.ZERO
	# В воздухе над новым островом не лететь дальше: залипший прыжок иначе уносит за край.
	var below := _island_under(hero_pos)
	if not grounded and below > island and hero_pos.z < centers[below].z + sizes[below].y / 2.0 - 0.8:
		_axis = Vector2.ZERO
	_bot_aligned = aligned
	if grounded and aligned and island < ISLANDS - 1 and hero_pos.z - far_edge < 1.4 and _bot_jump_wait <= 0.0:
		_bot_jump_wait = 0.5
		bug_press(_jump)


func _on_tick(delta: float) -> void:
	if not bot_driven():
		_axis = GameInput.axis()
	bug_audio_tick(delta)
	bug_input_tick()
	bug_frame(delta, _moving, _step)


func _step(dt: float) -> void:
	var axis := bug_axis(_axis)
	var left := dt
	while left > 0.0 and running:
		var h := minf(left, 1.0 / 60.0)
		_sim(h, axis)
		left -= h
	_sync()


func _sim(h: float, axis: Vector2) -> void:
	_t += h
	_safe = maxf(_safe - h, 0.0)
	var dir := cam.to_world(axis).limit_length(1.0)
	_moving = dir.length() > 0.1
	if _moving:
		heading = atan2(-dir.x, -dir.z)
		var next := hero_pos + dir * SPEED * h
		if not _in_wall(next):
			travelled += (next - hero_pos).length()
			hero_pos = next
	var before := hero_pos.y
	hero_vy -= GRAVITY * h
	hero_pos.y += hero_vy * h
	var under := _island_under(hero_pos)
	var floor_y := terrains[under].height_at(hero_pos.x, hero_pos.z) if under >= 0 else -INF
	# Земля неровная: стоящего героя она несёт за собой, падающий садится на неё сверху.
	if under >= 0 and hero_vy <= 0.0 and (grounded or before >= floor_y - 0.25) and hero_pos.y <= floor_y + (0.3 if grounded else 0.0):
		hero_pos.y = floor_y
		hero_vy = 0.0
		var landed := not grounded
		grounded = true
		island = under
		_air = 0.0
		if landed and bug_take_stick():
			_jump()
	else:
		grounded = false
		_air += h
	# Бот WIN у самого края прыгает сразу, мимо очереди ввода: после фриза мир догоняет время
	# без него, и запоздалое нажатие пришлось бы уже за краем.
	if bot_driven() and active_bot_mode() == AutoTest.BotMode.WIN and grounded and _bot_aligned and island < ISLANDS - 1 \
			and hero_pos.z - (centers[island].z - sizes[island].y / 2.0) < 0.25:
		_jump()
	if hero_pos.y < SEA_Y + 0.3:
		_lose_life("море после острова %d" % island)
		return
	for i in enemies.size():
		var c := centers[enemy_island[i]]
		var e := enemies[i]
		e.x += enemy_dir[i] * ENEMY_SPEED * h
		e.y = terrains[enemy_island[i]].height_at(e.x, e.z)
		if absf(e.x - c.x) > ENEMY_REACH:
			e.x = c.x + signf(e.x - c.x) * ENEMY_REACH
			enemy_dir[i] = -enemy_dir[i]
		enemies[i] = e
		if _safe <= 0.0 and Vector2(e.x - hero_pos.x, e.z - hero_pos.z).length() < HIT_RADIUS and absf(e.y - hero_pos.y) < 1.2:
			_lose_life("скелет на острове %d" % enemy_island[i])
			return
	for i in coins.size():
		if not taken[i] and coins[i].distance_to(hero_pos + Vector3(0.0, 0.5, 0.0)) < COIN_RADIUS:
			taken[i] = true
			collected += 1
			coin_nodes[i].visible = false
			bug_play(_coin_sfx)
	cam.step(h, hero_pos, heading, _moving and dir.dot(cam.forward()) > -0.3)
	if Vector2(flag_pos.x - hero_pos.x, flag_pos.z - hero_pos.z).length() < 1.2 and grounded:
		end_demo(true)


func _jump() -> void:
	if (grounded or _air < COYOTE) and hero_vy <= 0.0:
		hero_vy = JUMP
		grounded = false
		_air = COYOTE
		bug_stick()
		bug_play(_jump_sfx)


func _lose_life(why: String) -> void:
	lives -= 1
	deaths.append(why)
	bug_play(_hurt_sfx)
	bug_clear_stick()
	if lives <= 0:
		end_demo(false)
		return
	hero_pos = centers[island] + Vector3(0.0, 0.0, sizes[island].y / 2.0 - 1.0)
	hero_pos.y = terrains[island].height_at(hero_pos.x, hero_pos.z)
	hero_vy = 0.0
	grounded = true
	_safe = SAFE_SECONDS


## Остров под точкой или −1.
func _island_under(p: Vector3) -> int:
	for i in centers.size():
		if absf(p.x - centers[i].x) <= sizes[i].x / 2.0 and absf(p.z - centers[i].z) <= sizes[i].y / 2.0:
			return i
	return -1


## Точка ниже края острова внутри него: в борт не войти.
func _in_wall(p: Vector3) -> bool:
	var i := _island_under(p)
	return i >= 0 and p.y < terrains[i].height_at(p.x, p.z) - 0.45


func _sync() -> void:
	hero.position = hero_pos
	hero.rotation.y = heading
	hero.visible = _safe <= 0.0 or int(_t * 16.0) % 2 == 0
	if not grounded:
		hero.walk(PI / 2.0, 0.9)
	else:
		hero.walk(_t * 14.0, 0.8 if _moving else 0.0)
	for i in enemy_nodes.size():
		enemy_nodes[i].position = enemies[i]
		enemy_nodes[i].rotation.y = -PI / 2.0 if enemy_dir[i] > 0.0 else PI / 2.0
		enemy_nodes[i].walk(_t * 8.0, 0.5)
	for i in coin_nodes.size():
		coin_nodes[i].position = coins[i] + Vector3(0.0, sin(_t * 3.0 + i) * 0.12 - 0.35, 0.0)
		coin_nodes[i].rotation.y = _t * 3.0 + i
	for i in enemy_nodes.size():
		shadows[i].position = enemies[i] + Vector3(0.0, 0.04, 0.0)
	var below := _island_under(hero_pos)
	var hero_shadow := shadows[shadows.size() - 1]
	hero_shadow.visible = below >= 0 and hero_pos.y >= terrains[below].height_at(hero_pos.x, hero_pos.z) - 0.1
	if hero_shadow.visible:
		hero_shadow.position = Vector3(hero_pos.x, terrains[below].height_at(hero_pos.x, hero_pos.z) + 0.04, hero_pos.z)
	var cloth := flag.part(&"cloth")
	if cloth != null:
		cloth.rotation.y = sin(_t * 3.0) * 0.25
	cam.apply(lowpoly.camera)


func _draw_hud(canvas: CanvasItem) -> void:
	var dark := lowpoly.palette[LowpolyScreen.DARK].darkened(0.5)
	var red := lowpoly.palette[LowpolyScreen.DANGER]
	var gold := lowpoly.palette[LowpolyScreen.BONUS]
	var white := lowpoly.palette[LowpolyScreen.LIGHT]
	for i in LIVES:
		_draw_heart(canvas, Vector2(12.0 + i * 26.0, 10.0), red if i < lives else dark.lightened(0.25), dark)
	var at := Vector2(lowpoly.view.x - 92.0, 10.0)
	canvas.draw_circle(at + Vector2(9.0, 9.0), 10.0, dark)
	canvas.draw_circle(at + Vector2(9.0, 9.0), 8.0, gold.darkened(0.25))
	canvas.draw_circle(at + Vector2(8.0, 8.0), 6.0, gold)
	PixelFont16.draw(canvas, at + Vector2(26.0, 1.0), "%d/%d" % [collected, coins.size()], white, gold, dark, 2.0)


## Сердце пикселями ×3: обводка, заливка, блик сверху.
func _draw_heart(canvas: CanvasItem, at: Vector2, fill: Color, outline: Color) -> void:
	for pass_ in 2:
		for y in HEART.size():
			for x in 7:
				if HEART[y][x] != "#":
					continue
				var r := Rect2(at + Vector2(x, y) * 3.0, Vector2(3.0, 3.0))
				if pass_ == 0:
					canvas.draw_rect(r.grow(2.0), outline)
				else:
					canvas.draw_rect(r, fill.lightened(0.3) if y < 2 else (fill if y < 4 else fill.darkened(0.2)))


func _result_title(goal: bool) -> String:
	return "доплыл до флага" if goal else "утонул"


func _result_caption() -> String:
	return "дублонов %d из %d" % [collected, coins.size()]
