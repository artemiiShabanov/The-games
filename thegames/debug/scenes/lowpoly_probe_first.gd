extends Demo
## Пробная демка low poly от первого лица (#108) для `lowpoly_test`: не жанр, а проверка основы.
## Палуба за фальшбортом, на ней мачты, бочки, сундуки и пушки; надо собрать все дублоны, не
## попадаясь скелетам, которые ходят туда-сюда. Задел скелет: минус жизнь и отбрасывает, жизней
## три. WASD ход и стрейф, стрелки влево, вправо обзор (`GameInput.walk`, `look`), мышь и правый
## стик смотрят по сторонам и вверх-вниз (`Demo.look_take`, #109). Модели слотов через `spawn_model`,
## общие баги через хуки `Demo`. Бот WIN идёт к ближайшему дублону и обходит помехи стрейфом,
## LOSE идёт на скелетов.

const HALF := 11.0
const SPEED := 5.0
const BODY := 0.35
const COINS := 8
const PROPS := 7
const ENEMIES := 3
const LIVES := 3
const ENEMY_REACH := 3.0
const HIT_RADIUS := 0.9
const COIN_RADIUS := 0.9
const SAFE_SECONDS := 1.5
const MELODY := [0, 3, 7, null, 10, 7, 3, null, 5, 8, 12, null, 10, 8, 5, null,
	7, 10, 14, null, 12, 10, 7, null, 3, 5, 7, 10, 7, 5, 3, null]
const BASS := [-12, -12, -9, -9, -7, -7, -4, -4, -5, -5, -2, -2, -9, -9, -12, -12]
const HEART := [".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."]

## Помехи: x, z и радиус в `Vector3(x, радиус, z)`.
var blocks: Array[Vector3] = []
var coins: Array[Vector3] = []
var taken: Array[bool] = []
var coin_nodes: Array[LowpolyModel] = []
## Скелеты: середина пути, ось пути, сдвиг фазы; место сейчас.
var enemy_home: Array[Vector3] = []
var enemy_axis: Array[Vector3] = []
var enemy_phase: Array[float] = []
var enemies: Array[Vector3] = []
var enemy_nodes: Array[LowpolyModel] = []
var shadows: Array[MeshInstance3D] = []
var fp: LowpolyFirstPerson
var lives := LIVES
var collected := 0
## Сколько метров прошёл (проверки).
var travelled := 0.0
var _walk := Vector2.ZERO
var _look := 0.0
var _safe := 0.0
var _hurt := 0.0
var _moving := false
var _t := 0.0
var _coin_sfx: AudioStreamPlayer
var _hurt_sfx: AudioStreamPlayer


func _placeholder_slots() -> Array[String]:
	return ["enemy", "coin", "prop"]


func _on_start() -> void:
	lowpoly_screen(_draw_hud)
	fp = LowpolyFirstPerson.make(lowpoly.tuning)
	look_start()
	_build_level()
	var quiet := -80.0 if embedded else 0.0
	var music := Sfx.music(Sfx.tracker_loop(MELODY, BASS, 120.0), -10.0 + quiet)
	add_child(music)
	bug_music = music
	music.play()
	_coin_sfx = Sfx.player(Sfx.blip(1318.0, 0.12, 0.35, 14.0), -6.0 + quiet)
	_hurt_sfx = Sfx.player(Sfx.thud(0.16, 0.5), -4.0 + quiet)
	add_child(_coin_sfx)
	add_child(_hurt_sfx)
	_sync()


func _build_level() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed if record != null else 1, ":first"))
	var side := HALF * 2.0 + 1.0
	var wood := lowpoly_texture("planks")
	lowpoly.add_plane(Vector3.ZERO, Vector2(side, side), wood, 4.0)
	for s: float in [-1.0, 1.0]:
		lowpoly.add_box(Vector3(s * (HALF + 0.25), 0.55, 0.0), Vector3(0.5, 1.1, side), wood, 2.0)
		lowpoly.add_box(Vector3(0.0, 0.55, s * (HALF + 0.25)), Vector3(side, 1.1, 0.5), wood, 2.0)
		# Мачта с реей и парусом: ориентир, видно с любого места палубы.
		var mast := Vector3(s * 4.5, 0.0, -s * 3.0)
		lowpoly.add_box(mast + Vector3(0.0, 4.5, 0.0), Vector3(0.6, 9.0, 0.6), wood, 2.0)
		lowpoly.add_box(mast + Vector3(0.0, 7.0, 0.0), Vector3(5.6, 0.3, 0.3), wood, 2.0)
		lowpoly.add_box(mast + Vector3(0.0, 5.2, 0.0), Vector3(5.0, 3.2, 0.08), lowpoly_texture("sail"), 2.5)
		blocks.append(Vector3(mast.x, 0.55, mast.z))
	lowpoly.add_plane(Vector3(0.0, -2.0, 0.0), Vector2(360.0, 360.0), lowpoly_texture("water"), 6.0,
			{"uv_scroll": Vector2(0.02, 0.035), "affine": 0.0})
	var prop_names := ["barrel", "chest", "cannon", "rock"]
	var prop_radius := [0.5, 0.6, 0.75, 0.75]
	var tries := 0
	var placed := 0
	while placed < PROPS and tries < 400:
		tries += 1
		var p := Vector3(rng.randf_range(-HALF + 2.0, HALF - 2.0), 0.0, rng.randf_range(-HALF + 2.0, HALF - 2.0))
		if p.length() < 3.0 or _near_block(p, 3.0):
			continue
		var kind := rng.randi_range(0, prop_names.size() - 1)
		var prop := spawn_model("prop", prop_names[kind])
		prop.position = p
		prop.rotation.y = rng.randf_range(-PI, PI)
		blocks.append(Vector3(p.x, prop_radius[kind], p.z))
		placed += 1
	tries = 0
	while coins.size() < COINS and tries < 800:
		tries += 1
		var p := Vector3(rng.randf_range(-HALF + 1.5, HALF - 1.5), 0.0, rng.randf_range(-HALF + 1.5, HALF - 1.5))
		var ok := p.length() > 3.0 and not _near_block(p, 1.6)
		for c in coins:
			ok = ok and c.distance_to(p) > 2.5
		if ok:
			coins.append(p)
			taken.append(false)
			coin_nodes.append(spawn_model("coin", "coin"))
	tries = 0
	while enemy_home.size() < ENEMIES and tries < 400:
		tries += 1
		var p := Vector3(rng.randf_range(-HALF + 4.0, HALF - 4.0), 0.0, rng.randf_range(-HALF + 4.0, HALF - 4.0))
		var axis := Vector3.RIGHT if rng.randf() < 0.5 else Vector3.BACK
		if p.length() < 5.0 or _near_block(p - axis * ENEMY_REACH, 1.2) or _near_block(p, 1.2) or _near_block(p + axis * ENEMY_REACH, 1.2):
			continue
		enemy_home.append(p)
		enemy_axis.append(axis)
		enemy_phase.append(rng.randf_range(0.0, TAU))
		enemies.append(p)
		enemy_nodes.append(spawn_model("enemy", "enemy"))
		shadows.append(lowpoly.add_shadow(0.4))


## Ближе `margin` к краю любой помехи.
func _near_block(p: Vector3, margin: float) -> bool:
	for b in blocks:
		if Vector2(p.x - b.x, p.z - b.z).length() < b.y + margin:
			return true
	return false


## Бот WIN: поворот к ближайшему дублону, ход вперёд; помеху или скелета впереди обходит
## стрейфом, от скелета вплотную пятится. LOSE: идёт на ближайшего скелета.
func _bot_step(_delta: float) -> void:
	var lose := active_bot_mode() == AutoTest.BotMode.LOSE
	var target := Vector3.ZERO
	var best := INF
	var pool := enemies if lose else coins
	for i in pool.size():
		if not lose and taken[i]:
			continue
		var d := pool[i].distance_to(fp.position)
		if d < best:
			best = d
			target = pool[i]
	var bearing := fp.bearing_to(target)
	_look = clampf(bearing * 3.0, -1.0, 1.0)
	_walk = Vector2(0.0, 1.0 if absf(bearing) < 0.6 else 0.0)
	if lose:
		return
	for b in blocks:
		var to := Vector3(b.x - fp.position.x, 0.0, b.z - fp.position.z)
		if to.length() < b.y + 1.3 and to.dot(fp.forward()) > 0.0:
			_walk.x = -signf(to.dot(fp.right())) if absf(to.dot(fp.right())) > 0.05 else 1.0
	for e in enemies:
		var to := Vector3(e.x - fp.position.x, 0.0, e.z - fp.position.z)
		if to.length() < 3.0 and to.dot(fp.forward()) > 0.0:
			_walk.x = -signf(to.dot(fp.right())) if absf(to.dot(fp.right())) > 0.05 else 1.0
			if to.length() < 1.9:
				_walk.y = -1.0


func _on_tick(delta: float) -> void:
	if not bot_driven():
		_walk = GameInput.walk()
		_look = GameInput.look()
	bug_audio_tick(delta)
	bug_input_tick()
	fp.look_by(look_take(delta))
	bug_frame(delta, _moving, _step)


func _step(dt: float) -> void:
	var walk := bug_axis(_walk)
	var left := dt
	while left > 0.0 and running:
		var h := minf(left, 1.0 / 60.0)
		_sim(h, walk)
		left -= h
	_sync()


func _sim(h: float, walk: Vector2) -> void:
	_t += h
	_safe = maxf(_safe - h, 0.0)
	_hurt = maxf(_hurt - h, 0.0)
	fp.turn(_look, h)
	var dir := fp.wish(walk).limit_length(1.0)
	_moving = dir.length() > 0.1 or absf(_look) > 0.1
	var from := fp.position
	fp.position = _collide(fp.position + dir * SPEED * h)
	travelled += fp.position.distance_to(from)
	for i in enemies.size():
		enemies[i] = enemy_home[i] + enemy_axis[i] * sin(_t * 0.5 + enemy_phase[i]) * ENEMY_REACH
		var away := fp.position - enemies[i]
		if _safe <= 0.0 and away.length() < HIT_RADIUS:
			lives -= 1
			_safe = SAFE_SECONDS
			_hurt = 0.5
			bug_play(_hurt_sfx)
			if lives <= 0:
				end_demo(false)
				return
			fp.position = _collide(fp.position + (away.normalized() if away.length() > 0.01 else fp.forward() * -1.0) * 1.5)
	for i in coins.size():
		if not taken[i] and coins[i].distance_to(fp.position) < COIN_RADIUS:
			taken[i] = true
			collected += 1
			coin_nodes[i].visible = false
			bug_play(_coin_sfx)
	if collected >= coins.size():
		end_demo(true)


## Шаг в точку `p` с учётом фальшборта и помех: из круга помехи выталкивает наружу.
func _collide(p: Vector3) -> Vector3:
	for b in blocks:
		var off := Vector2(p.x - b.x, p.z - b.z)
		var reach := b.y + BODY
		if off.length() < reach:
			off = off.normalized() * reach if off.length() > 0.001 else Vector2(reach, 0.0)
			p.x = b.x + off.x
			p.z = b.z + off.y
	p.x = clampf(p.x, -HALF + BODY, HALF - BODY)
	p.z = clampf(p.z, -HALF + BODY, HALF - BODY)
	return p


func _sync() -> void:
	for i in enemy_nodes.size():
		var speed := cos(_t * 0.5 + enemy_phase[i])
		var facing := enemy_axis[i] * (1.0 if speed >= 0.0 else -1.0)
		enemy_nodes[i].position = enemies[i]
		enemy_nodes[i].rotation.y = atan2(-facing.x, -facing.z)
		enemy_nodes[i].walk(_t * 8.0, 0.5 * absf(speed))
		shadows[i].position = enemies[i] + Vector3(0.0, 0.04, 0.0)
	for i in coin_nodes.size():
		coin_nodes[i].position = coins[i] + Vector3(0.0, 0.45 + sin(_t * 3.0 + i) * 0.12, 0.0)
		coin_nodes[i].rotation.y = _t * 3.0 + i
	fp.apply(lowpoly.camera)


func _draw_hud(canvas: CanvasItem) -> void:
	var dark := lowpoly.palette[LowpolyScreen.DARK].darkened(0.5)
	var red := lowpoly.palette[LowpolyScreen.DANGER]
	var gold := lowpoly.palette[LowpolyScreen.BONUS]
	var white := lowpoly.palette[LowpolyScreen.LIGHT]
	if _hurt > 0.0:
		canvas.draw_rect(Rect2(Vector2.ZERO, lowpoly.view), Color(red, _hurt * 0.9))
	var mid := (lowpoly.view / 2.0).floor()
	for arm: Vector2 in [Vector2(6, 0), Vector2(-6, 0), Vector2(0, 6), Vector2(0, -6)]:
		canvas.draw_rect(Rect2(mid + arm - Vector2(2, 2), Vector2(4, 4)), dark)
		canvas.draw_rect(Rect2(mid + arm - Vector2(1, 1), Vector2(2, 2)), white)
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
	return "собрал всё" if goal else "попался"


func _result_caption() -> String:
	return "дублонов %d из %d" % [collected, coins.size()]
