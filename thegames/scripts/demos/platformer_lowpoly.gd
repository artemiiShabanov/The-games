extends Demo
## Демка платформер × low poly, каталог `docs/specs/demos_catalog.md`: «тропа вглубь экрана»
## (#112, решение 2026-11-12: не парящие острова с двойным прыжком, а узкая тропа от камеры).
## Песчаная коса уходит от камеры в море; герой бежит по ней, камера за спиной и не
## поворачивается. Стрелки ход (вверх это вперёд), A прыжок. Ямы с водой между кусками тропы,
## узкие мостики, ряды ящиков поперёк (прыжок сверху разбивает ящик, даёт дублон и
## подбрасывает), скелеты ходят поперёк тропы. Вода и скелет стоят жизни и возвращают к началу
## куска; три жизни вместо таймера. Цель: маяк в конце косы.
## Уровень из `SpitLevelGen` по сиду записи. Правила и боты живут в `SpitSim` (без окна, им же
## проверяются сто сидов); демка ведёт его шагами по 1/60 с, рисует и озвучивает его события.
## Картинка на `LowpolyScreen` в духе первой PlayStation: коса из кусков `LowpolyTerrain` с
## обрывом в воду, мостики из досок, по сторонам островки с пальмами, камнями и пушками, маяк
## на островке за концом тропы.
##
## Общие баги (#44) и баг технологии `mesh_holes` живут в `Demo` и `LowpolyScreen`, демка только
## зовёт хуки: фризы `bug_frame`, заикание музыки, ввод с опозданием и залипший прыжок
## (повторяется после приземления), розовые заглушки вместо скелетов, дублонов, ящиков, пальм и
## маяка. Баги жанра и баланса для этой демки включит #117 (`SpitSim` их уже умеет).

const PLACEHOLDER_SLOTS: Array[String] = ["enemy", "bonus", "obstacle", "prop", "finish"]
const MELODY := [0, null, 4, 7, 12, null, 7, 4, 5, null, 9, 12, 17, null, 12, 9,
	7, null, 11, 14, 19, null, 14, 11, 12, null, 7, null, 4, 2, 0, null]
const BASS := [-12, -12, -5, -5, -7, -7, 0, 0, -5, -5, 2, 2, -12, -12, -5, -5]
const HEART := [".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."]
## Вода ниже самой низкой точки тропы на столько.
const WATER_DROP := 1.7
const DECOR := ["palm", "palm", "palm", "rock", "barrel", "chest", "cannon"]
const DEBRIS_LIFE := 0.7

var tuning: PlatformerLowpolyTuning
var level: SpitLevel
var sim: SpitSim
var cam: LowpolyFollowCam
var hero: LowpolyModel
var hero_shadow: MeshInstance3D
var guard_nodes: Array[LowpolyModel] = []
var guard_shadows: Array[MeshInstance3D] = []
var coin_nodes: Array[LowpolyModel] = []
var crate_nodes: Array[LowpolyModel] = []
var water_y := -3.0

var _time := 0.0
var _walk := 0.0
var _stop := 0.0
var _hurt := 0.0
var _cam_y := 0.0
## Обломки ящиков: [узел, скорость, возраст].
var _debris: Array[Array] = []
var _music: AudioStreamPlayer
var _sfx := {}


func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _on_start() -> void:
	tuning = PlatformerLowpolyTuning.load_default()
	level = SpitLevelGen.generate(record.seed if record != null else 1)
	sim = SpitSim.create(level, tuning)
	lowpoly_screen(_draw_hud)
	cam = LowpolyFollowCam.make(lowpoly.tuning)
	cam.distance = tuning.cam_distance
	cam.height = tuning.cam_height
	cam.look_height = tuning.cam_look
	_build_world()
	_setup_audio()
	_cam_y = sim.pos.y
	cam.step(0.0, sim.pos, 0.0, false)
	_sync(0.0)


func _setup_audio() -> void:
	var quiet := embedded
	_music = Sfx.music(Sfx.tracker_loop(MELODY, BASS, 132.0), tuning.music_db if not quiet else -80.0)
	add_child(_music)
	bug_music = _music
	if not quiet:
		_music.play()
	_sfx["jump"] = Sfx.player(Sfx.blip(520.0, 0.1, 0.3, 10.0))
	_sfx["land"] = Sfx.player(Sfx.thud(0.06, 0.2))
	_sfx["coin"] = Sfx.player(Sfx.blip(1318.0, 0.12, 0.35, 14.0))
	_sfx["smash"] = Sfx.player(Sfx.thud(0.14, 0.45))
	_sfx["hurt"] = Sfx.player(Sfx.thud(0.2, 0.55))
	_sfx["pop"] = Sfx.player(Sfx.blip(520.0, 0.1, 0.25, 26.0))
	_sfx["finish"] = Sfx.player(Sfx.blip(880.0, 0.5, 0.4, 5.0))
	for p in _sfx.values():
		(p as AudioStreamPlayer).volume_db = tuning.sfx_db if not quiet else -80.0
		add_child(p)


func _play(name: String) -> void:
	bug_play(_sfx[name])


# --- Мир ---------------------------------------------------------------------------------------

func _build_world() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed if record != null else 1, ":spit-look"))
	var low := INF
	for p in level.pieces:
		low = minf(low, minf(p.h0, p.h1))
	water_y = low - WATER_DROP
	var sand := lowpoly_texture("sand")
	var grass := lowpoly_texture("grass")
	var rock := lowpoly_texture("rock")
	var planks := lowpoly_texture("planks")
	for i in level.pieces.size():
		var p := level.pieces[i]
		if p.kind == SpitLevel.Kind.BRIDGE:
			_build_bridge(p, planks)
			continue
		var land := LowpolyTerrain.make(Vector3(p.left(), 0.0, p.z1()), 1.0, p.width, p.length)
		for iz in p.length + 1:
			for ix in p.width + 1:
				var edge := ix == 0 or ix == p.width
				land.set_h(ix, iz, p.height(p.z1() + iz) + (rng.randf_range(-0.34, -0.2) if edge else rng.randf_range(-0.04, 0.04)))
		var top := grass if p.kind == SpitLevel.Kind.GUARD or p.kind == SpitLevel.Kind.END else sand
		land.build(lowpoly, top, 3.0, rock, water_y - 0.3)
	_build_finish(level.finish_piece(), grass, rock)
	_build_decor(rng, sand, grass, rock)
	var mid_z := -level.length() / 2.0
	lowpoly.add_plane(Vector3(0.0, water_y, mid_z), Vector2(260.0, level.length() + 260.0), lowpoly_texture("water"), 6.0,
			{"uv_scroll": Vector2(0.02, 0.035), "affine": 0.0})
	for c in level.crates:
		var node := spawn_model("obstacle", "crate")
		node.position = c
		node.rotation.y = rng.randf_range(-0.12, 0.12)
		crate_nodes.append(node)
	for i in level.coins.size():
		coin_nodes.append(spawn_model("bonus", "coin"))
	for i in level.guards.size():
		guard_nodes.append(spawn_model("enemy", "enemy"))
		guard_shadows.append(lowpoly.add_shadow(0.4))
	hero = spawn_model("hero", "hero")
	hero_shadow = lowpoly.add_shadow(0.42)


## Мостик: настил из досок и столбики по краям.
func _build_bridge(p: SpitLevel.Piece, planks: Texture2D) -> void:
	var mid := Vector3(p.x, p.h0 - 0.1, p.z0 - p.length / 2.0)
	lowpoly.add_box(mid, Vector3(p.width, 0.2, p.length), planks, 2.0)
	var z := p.z0 - 0.5
	while z > p.z1():
		for side: float in [-1.0, 1.0]:
			lowpoly.add_box(Vector3(p.x + side * (p.width / 2.0 - 0.08), (p.h0 + water_y) / 2.0, z),
					Vector3(0.16, p.h0 - water_y + 0.7, 0.16), planks, 1.0)
		z -= 2.0


## Островок с маяком сразу за концом тропы, на её высоте.
func _build_finish(last: SpitLevel.Piece, grass: Texture2D, rock: Texture2D) -> void:
	var side := 9
	var land := LowpolyTerrain.make(Vector3(last.x - side / 2.0 - 0.5, 0.0, last.z1() - side), 1.0, side + 1, side)
	for iz in side + 1:
		for ix in side + 2:
			var edge := ix == 0 or ix == side + 1 or iz == 0
			land.set_h(ix, iz, last.h1 + (-0.3 if edge else 0.0))
	land.build(lowpoly, grass, 3.0, rock, water_y - 0.3)
	var tower := spawn_model("finish", "lighthouse")
	tower.position = Vector3(last.x, last.h1 - 0.05, last.z1() - side / 2.0)


## Островки по сторонам косы: пальмы, камни, бочки, сундуки и пушки. Только вид.
func _build_decor(rng: RandomNumberGenerator, sand: Texture2D, grass: Texture2D, rock: Texture2D) -> void:
	var z := -6.0
	var side := 1.0
	while z > -level.length() - 12.0:
		# Островок не ближе трёх метров к борту любого куска тропы рядом: его не спутать с тропой.
		var cells := rng.randi_range(3, 5)
		var border := -INF
		for p in level.pieces:
			if p.z1() - 6.0 < z and p.z0 + 6.0 > z:
				border = maxf(border, side * p.x + p.width / 2.0)
		if border == -INF:
			border = side * level.finish_piece().x + level.finish_piece().width / 2.0
		var at := Vector3(side * (border + cells / 2.0 + rng.randf_range(3.0, 8.0)), 0.0, z)
		var land := LowpolyTerrain.make(Vector3(at.x - cells / 2.0, 0.0, at.z - cells / 2.0), 1.0, cells, cells)
		var peak := water_y + rng.randf_range(0.7, 1.5)
		for iz in cells + 1:
			for ix in cells + 1:
				var rim := ix == 0 or iz == 0 or ix == cells or iz == cells
				land.set_h(ix, iz, water_y - 0.2 if rim else peak + rng.randf_range(-0.2, 0.1))
		land.build(lowpoly, grass if rng.randf() < 0.5 else sand, 3.0, rock, water_y - 0.3)
		var prop := spawn_model("prop", DECOR[rng.randi_range(0, DECOR.size() - 1)])
		prop.position = Vector3(at.x, land.height_at(at.x, at.z) - 0.08, at.z)
		prop.rotation.y = rng.randf_range(-PI, PI)
		z -= rng.randf_range(5.0, 9.0)
		side = -side


# --- Ввод ------------------------------------------------------------------------------------

func _game_input(event: InputEvent) -> void:
	if GameInput.is_a(event):
		# С багом управления нажатие уходит в очередь с задержкой (`Demo.bug_press`).
		bug_press(_jump)
		get_viewport().set_input_as_handled()


## Прыжок; с багом управления удачный прыжок залипает и повторится после приземления.
func _jump() -> void:
	if running and sim.jump():
		bug_stick()


# --- Шаг -------------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	_hurt = maxf(_hurt - delta, 0.0)
	# Стоп-кадр на потере жизни: мир стоит, герой залит белым.
	if _stop > 0.0:
		_stop -= delta
		if _stop <= 0.0:
			hero.flash(false)
		return
	# Фризы в движении с догоном времени (`Demo.bug_frame`).
	bug_frame(delta, sim.moving or not sim.grounded, _step)


func _step(dt: float) -> void:
	_time += dt
	bug_input_tick()
	var left := dt
	# Правила шагами по 1/60 с; бот решает на каждом шаге, поэтому догон времени после фриза его
	# не ослепляет.
	while left > 0.0001 and running and _stop <= 0.0:
		var h := minf(left, SpitSim.DT)
		left -= h
		var raw := GameInput.axis()
		if bot_driven():
			raw = sim.bot(active_bot_mode())
			if sim.bot_jump:
				_jump()
		# Ось движения: с багом управления из прошлого на delay_ms (`Demo.bug_axis`).
		sim.step(h, bug_axis(raw))
		for ev in sim.events:
			_on_event(ev)
		sim.events.clear()
	_sync(dt)


## Событие правил: звук, эффект, заметка автотеста, конец демки.
func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"jump":
			_play("jump")
		&"land":
			_play("land")
			if bug_take_stick():
				_jump()
		&"coin":
			coin_nodes[int(ev[1])].visible = false
			_play("coin")
		&"smash":
			var i := int(ev[1])
			crate_nodes[i].visible = false
			_spawn_debris(level.crates[i])
			_play("smash")
			_play("coin")
		&"pop":
			guard_nodes[int(ev[1])].visible = false
			guard_shadows[int(ev[1])].visible = false
			_play("pop")
		&"hurt":
			_play("hurt")
			bug_clear_stick()
			_stop = tuning.hit_stop
			_hurt = 0.45
			hero.flash(true)
			if AutoTest.enabled and not embedded:
				AutoTest.note("platformer lowpoly: жизнь %d потеряна: %s" % [sim.hits, sim.hurt_log[sim.hurt_log.size() - 1]])
		&"win":
			end_demo(true)
		&"lose":
			end_demo(false)


func _on_end(goal: bool) -> void:
	_music.stop()
	if goal:
		_play("finish")
	if AutoTest.enabled and not embedded:
		AutoTest.note("platformer lowpoly: %s за %.1f с, пройдено %d %%, жизней %d, падений %d, дублонов %d из %d" % [
				"маяк" if goal else "провал", elapsed, roundi(sim.progress() * 100.0), sim.lives, sim.falls, sim.coins_got,
				level.coins.size() + level.crates.size()])


func _result_title(goal: bool) -> String:
	return "добрался до маяка" if goal else "не добрался"


func _result_caption() -> String:
	return "дублоны %d из %d · %d с" % [sim.coins_got, level.coins.size() + level.crates.size(), int(round(elapsed))]


# --- Картинка --------------------------------------------------------------------------------

## Обломки разбитого ящика: четыре маленьких ящика разлетаются и падают.
func _spawn_debris(at: Vector3) -> void:
	if is_pink("obstacle"):
		return
	for k in 4:
		var piece := lowpoly.model(lowpoly_set.model("crate"))
		piece.scale = Vector3.ONE * 0.36
		piece.position = at + Vector3(0.0, 0.4, 0.0)
		lowpoly.world.add_child(piece)
		var a := TAU * k / 4.0 + 0.6
		_debris.append([piece, Vector3(sin(a) * 2.6, 4.5, cos(a) * 2.6), 0.0])


func _sync(dt: float) -> void:
	hero.position = sim.pos
	hero.rotation.y = sim.facing
	hero.visible = sim.invuln <= 0.0 or _stop > 0.0 or int(_time * 16.0) % 2 == 0
	if not sim.grounded:
		hero.walk(PI / 2.0, 0.9)
	elif sim.moving:
		_walk += dt * 13.0
		hero.walk(_walk, 0.85)
	else:
		hero.walk(0.0, 0.0)
	var floor_y := level.ground_at(sim.pos.x, sim.pos.z)
	hero_shadow.visible = floor_y > -INF and sim.pos.y >= floor_y - 0.1
	if hero_shadow.visible:
		hero_shadow.position = Vector3(sim.pos.x, floor_y + 0.04, sim.pos.z)
		_cam_y = lerpf(_cam_y, floor_y, clampf(5.0 * dt, 0.0, 1.0))
	for i in guard_nodes.size():
		var g := sim.guard_pos(i)
		guard_nodes[i].position = g
		guard_nodes[i].rotation.y = -PI / 2.0 if level.guard_dir(i, sim.time * sim.enemy_mult) > 0.0 else PI / 2.0
		guard_nodes[i].walk(_time * 9.0, 0.55)
		guard_shadows[i].position = g + Vector3(0.0, 0.04, 0.0)
	for i in coin_nodes.size():
		coin_nodes[i].position = sim.coin_pos(i) + Vector3(0.0, sin(_time * 3.0 + i) * 0.1 - 0.35, 0.0)
		coin_nodes[i].rotation.y = _time * 3.2 + i
	for i in range(_debris.size() - 1, -1, -1):
		var d := _debris[i]
		var node: LowpolyModel = d[0]
		var vel: Vector3 = d[1]
		vel.y -= 16.0 * dt
		node.position += vel * dt
		node.rotation += Vector3(7.0, 5.0, 3.0) * dt
		d[1] = vel
		d[2] = float(d[2]) + dt
		if float(d[2]) >= DEBRIS_LIFE:
			node.queue_free()
			_debris.remove_at(i)
	# Камера за спиной смотрит вдоль тропы и не поворачивается; по высоте идёт за землёй, не за прыжком.
	cam.step(dt, Vector3(sim.pos.x, _cam_y, sim.pos.z), 0.0, false)
	cam.apply(lowpoly.camera)


func _draw_hud(canvas: CanvasItem) -> void:
	var dark := lowpoly.ink(LowpolyScreen.DARK).darkened(0.5)
	var red := lowpoly.ink(LowpolyScreen.DANGER)
	var gold := lowpoly.ink(LowpolyScreen.BONUS)
	var white := lowpoly.ink(LowpolyScreen.LIGHT)
	var view := lowpoly.view
	if _hurt > 0.0:
		canvas.draw_rect(Rect2(Vector2.ZERO, view), Color(red, _hurt * 0.8))
	for i in tuning.lives:
		_draw_heart(canvas, Vector2(10.0 + i * 20.0, 9.0), red if i < sim.lives else dark.lightened(0.25), dark)
	# Дублоны справа.
	var text := str(sim.coins_got)
	var at := Vector2(view.x - 34.0 - PixelFont16.width(text, 2.0), 8.0)
	canvas.draw_circle(at + Vector2(8.0, 8.0), 9.0, dark)
	canvas.draw_circle(at + Vector2(8.0, 8.0), 7.0, gold.darkened(0.25))
	canvas.draw_circle(at + Vector2(7.0, 7.0), 5.0, gold)
	PixelFont16.draw(canvas, at + Vector2(22.0, 0.0), text, white, gold, dark, 2.0)
	# Путь до маяка: полоса с обводкой и заливкой сверху светлее.
	var bar := Rect2(roundf(view.x / 2.0 - 70.0), 11.0, 140.0, 8.0)
	canvas.draw_rect(bar.grow(2.0), dark)
	canvas.draw_rect(bar, dark.lightened(0.2))
	var fill := Rect2(bar.position, Vector2(roundf(bar.size.x * sim.progress()), bar.size.y))
	canvas.draw_rect(fill, gold.darkened(0.2))
	canvas.draw_rect(Rect2(fill.position, Vector2(fill.size.x, 3.0)), gold.lightened(0.25))
	canvas.draw_rect(Rect2(bar.end.x - 3.0, bar.position.y - 5.0, 3.0, 18.0), dark)
	canvas.draw_rect(Rect2(bar.end.x - 2.0, bar.position.y - 4.0, 1.0, 16.0), red)


## Сердце пикселями ×2: обводка, заливка, блик сверху.
func _draw_heart(canvas: CanvasItem, at: Vector2, fill: Color, outline: Color) -> void:
	for pass_ in 2:
		for y in HEART.size():
			for x in 7:
				if HEART[y][x] != "#":
					continue
				var r := Rect2(at + Vector2(x, y) * 2.0, Vector2(2.0, 2.0))
				if pass_ == 0:
					canvas.draw_rect(r.grow(1.0), outline)
				else:
					canvas.draw_rect(r, fill.lightened(0.3) if y < 2 else (fill if y < 4 else fill.darkened(0.2)))
