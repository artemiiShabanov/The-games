extends Demo
## Демка платформер × «продвинутые», каталог `docs/specs/demos_catalog.md`: «крюк-кошка» (#121,
## решение и приёмы сложности 2026-11-13, образцы Bionic Commando, Spider-Man, Uncharted).
## Герой бежит по островкам-скалам к маяку, камера за спиной. Между островками пропасти над
## водой, над ними кольца на реях. Стрелки ход, A прыжок, B крюк: зажал рядом с кольцом
## (над ним горит отметка), герой цепляется и качается маятником; отпустил, летит по
## касательной. Всё решает момент: рано отпустил, недолёт; поздно, взлетел и упал назад. Дальше
## по уровню кольца идут цепочками без опоры между ними, на разной высоте, ходят вверх-вниз, а
## островки мельчают. Жизней три, вода снимает одну и возвращает на последний островок.
## Уровень из `HookLevelGen` по сиду записи. Правила и боты живут в `HookSim` (без окна, им же
## проверяются сто сидов); демка ведёт его шагами по 1/60 с, рисует и озвучивает его события.
##
## Общие баги (#44) и баг технологии `camera_clip` живут в `Demo` и `ThreedScreen`, демка только
## зовёт хуки. Баги жанра и баланса для этой демки включит #126.

const PLACEHOLDER_SLOTS: Array[String] = ["hero", "prop", "finish"]
const MELODY := [0, 4, 7, 12, 11, 7, 4, null, 5, 9, 12, 16, 14, 12, 9, null,
	0, 4, 7, 12, 14, 12, 11, 7, 5, 4, 2, 4, 5, 7, 0, null]
const BASS := [-12, -12, -5, -5, -7, -7, -3, -3, -12, -12, -5, -5, -7, -7, -5, -5]
const DECOR := ["palm", "barrel", "crate", "rock", "chest"]
const HAND := 1.95

var tuning: PlatformerThreedTuning
var level: HookLevel
var sim: HookSim
var cam: LowpolyFollowCam
var hero: LowpolyModel
var ring_nodes: Array[Node3D] = []
var rope: MeshInstance3D

var _time := 0.0
var _walk := 0.0
var _last_s := 0.0
var _want_jump := false
var _hurt := 0.0
var _stop_left := 0.0
var _music: AudioStreamPlayer
var _sfx := {}


func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _on_start() -> void:
	tuning = PlatformerThreedTuning.load_default()
	level = HookLevelGen.generate(record.seed if record != null else 1, null, tuning)
	sim = HookSim.create(level, tuning)
	lowpoly_screen(_draw_hud)
	cam = LowpolyFollowCam.make(lowpoly.tuning)
	cam.distance = tuning.cam_distance
	cam.height = tuning.cam_height
	cam.look_height = tuning.cam_look
	cam.turn = tuning.cam_turn
	_build_world()
	_setup_audio()
	_last_s = sim.s
	cam.step(0.0, level.world(sim.s, sim.u, sim.y), level.yaw_at(sim.s), false)
	_sync(0.0)


func _setup_audio() -> void:
	var quiet := embedded
	_music = Sfx.music(Sfx.tracker_loop(MELODY, BASS, 132.0), tuning.music_db if not quiet else -80.0)
	add_child(_music)
	bug_music = _music
	if not quiet:
		_music.play()
	_sfx["go"] = Sfx.player(Sfx.blip(880.0, 0.3, 0.4, 6.0))
	_sfx["jump"] = Sfx.player(Sfx.blip(520.0, 0.12, 0.3, 10.0))
	_sfx["hook"] = Sfx.player(Sfx.blip(1180.0, 0.07, 0.35, 26.0))
	_sfx["release"] = Sfx.player(Sfx.hiss(0.16, 0.14))
	_sfx["land"] = Sfx.player(Sfx.thud(0.1, 0.4))
	_sfx["splash"] = Sfx.player(Sfx.thud(0.3, 0.6))
	_sfx["finish"] = Sfx.player(Sfx.blip(880.0, 0.5, 0.4, 5.0))
	for p in _sfx.values():
		(p as AudioStreamPlayer).volume_db = tuning.sfx_db if not quiet else -80.0
		add_child(p)


func _play(name: String) -> void:
	bug_play(_sfx[name])


# --- Мир ---------------------------------------------------------------------------------------

func _cylinder(at: Vector3, radius: float, height: float, tex: Texture2D, tile: Vector2, taper := 1.0) -> MeshInstance3D:
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius * taper
	mesh.height = height
	mesh.radial_segments = 20
	mesh.rings = 2
	mesh.material = lowpoly.tex_material(tex, {"uv_scale": tile})
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.position = at
	lowpoly.world.add_child(node)
	return node


func _build_world() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed if record != null else 1, ":hook-look"))
	var water := sim.water
	var mid := (level.islets[0].pos + level.islets[level.islets.size() - 1].pos) / 2.0
	lowpoly.add_plane(Vector3(mid.x, water, mid.z), Vector2(620.0, 620.0), lowpoly_texture("water"), 6.0,
			{"uv_scroll": Vector2(0.02, 0.035), "affine": 0.0})
	var rock := lowpoly_texture("rock")
	var sand := lowpoly_texture("sand")
	for i in level.islets.size():
		var it := level.islets[i]
		var tall := it.y - water + 1.5
		# Скала сужается книзу, сверху шапка песка.
		_cylinder(Vector3(it.pos.x, it.y - tall / 2.0 - 0.1, it.pos.z), it.radius, tall, rock, Vector2(maxf(roundf(it.radius * 2.0), 2.0),
				maxf(roundf(tall / 2.0), 1.0)), 0.72)
		_cylinder(Vector3(it.pos.x, it.y - 0.06, it.pos.z), it.radius + 0.04, 0.12, sand, Vector2(2.0, 2.0))
		# Реквизит на краях больших островков, сбоку от пути.
		if it.radius > 2.0 and i > 0 and i < level.islets.size() - 1:
			var side := 1.0 if rng.randf() < 0.5 else -1.0
			var prop := spawn_model("prop", DECOR[rng.randi_range(0, DECOR.size() - 1)])
			prop.position = level.world(it.s + rng.randf_range(-0.6, 0.6), side * (it.radius - 0.75), it.y)
			prop.rotation.y = rng.randf_range(-PI, PI)
	# Кольца на реях: мачта сбоку от пути, рея над пропастью, кольцо под ней.
	var gold := StandardMaterial3D.new()
	gold.albedo_color = Color(0.93, 0.72, 0.22)
	gold.metallic = 0.7
	gold.roughness = 0.32
	gold.emission_enabled = true
	gold.emission = Color(0.5, 0.36, 0.08)
	var wood := lowpoly_texture("planks")
	for i in level.rings.size():
		var r := level.rings[i]
		var side := 1.0 if i % 2 == 0 else -1.0
		var foot := level.world(r.s, side * 2.4, water)
		var top := r.y + r.amp + 1.3
		_cylinder(Vector3(foot.x, (water + top) / 2.0, foot.z), 0.13, top - water, wood, Vector2(1.0, maxf(roundf((top - water) / 2.0), 1.0)))
		var node := Node3D.new()
		node.position = level.world(r.s, 0.0, r.y)
		node.rotation.y = level.yaw_at(r.s)
		lowpoly.world.add_child(node)
		var yard := MeshInstance3D.new()
		var beam := BoxMesh.new()
		beam.size = Vector3(3.2, 0.12, 0.12)
		beam.material = lowpoly.tex_material(wood, {"uv_scale": Vector2(2.0, 1.0)})
		yard.mesh = beam
		yard.position = Vector3(side * 1.1, 0.95, 0.0)
		node.add_child(yard)
		var chain := MeshInstance3D.new()
		var link := BoxMesh.new()
		link.size = Vector3(0.05, 0.55, 0.05)
		link.material = gold
		chain.mesh = link
		chain.position = Vector3(0.0, 0.66, 0.0)
		node.add_child(chain)
		var hoop := MeshInstance3D.new()
		var torus := TorusMesh.new()
		torus.inner_radius = 0.3
		torus.outer_radius = 0.42
		torus.material = gold
		hoop.mesh = torus
		hoop.rotation.x = PI / 2.0
		node.add_child(hoop)
		ring_nodes.append(node)
	# Верёвка крюка.
	rope = MeshInstance3D.new()
	var line := CylinderMesh.new()
	line.top_radius = 0.025
	line.bottom_radius = 0.025
	line.height = 1.0
	line.radial_segments = 6
	line.material = lowpoly.tex_material(lowpoly_texture("sail"), {"tint": Color(0.82, 0.7, 0.5)})
	rope.mesh = line
	rope.visible = false
	lowpoly.world.add_child(rope)
	# Маяк на последнем островке.
	var last := level.islets[level.islets.size() - 1]
	var tower := spawn_model("finish", "lighthouse")
	tower.position = level.world(last.s + 1.2, 0.0, last.y)
	tower.scale = Vector3.ONE * 0.5
	hero = spawn_model("hero", "hero")


# --- Шаг -------------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	_hurt = maxf(_hurt - delta, 0.0)
	if not bot_driven() and running and GameInput.a_just_pressed():
		bug_press(func() -> void: _want_jump = true)
	# Фризы в движении с догоном времени (`Demo.bug_frame`).
	bug_frame(delta, sim.mode != HookSim.Mode.DOWN and sim.phase == HookSim.Phase.PLAY, _step)


func _step(dt: float) -> void:
	_time += dt
	bug_input_tick()
	var hold := minf(_stop_left, dt)
	_stop_left -= hold
	var left := dt - hold
	while left > 0.0001 and running:
		var h := minf(left, HookSim.DT)
		left -= h
		var forward := 0.0
		var side := 0.0
		var jump := false
		var hook := false
		if bot_driven():
			sim.bot(active_bot_mode())
			forward = sim.bot_forward
			side = sim.bot_side
			jump = sim.bot_jump
			hook = sim.bot_hook
		else:
			# Ход с багом управления из прошлого (`Demo.bug_axis`).
			var axis := bug_axis(GameInput.axis())
			forward = -axis.y
			side = axis.x
			jump = _want_jump
			hook = GameInput.b_pressed()
			_want_jump = false
		sim.step(h, forward, side, jump, hook)
		for ev in sim.events:
			_on_event(ev)
		sim.events.clear()
		if _stop_left > 0.0:
			break
	_sync(dt)


## Событие правил: звук, эффект, конец демки.
func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"go":
			_play("go")
		&"jump":
			_play("jump")
		&"hook":
			_play("hook")
		&"release":
			_play("release")
		&"land":
			_play("land")
		&"splash":
			_play("splash")
			_hurt = 0.6
			_stop_left = tuning.hit_stop
			if AutoTest.enabled and not embedded:
				AutoTest.note("platformer threed: в воде на %.1f с, островок %d, жизней %d" % [sim.time, sim.islet, sim.lives])
		&"finish":
			end_demo(true)
		&"dead", &"timeout":
			end_demo(false)


func _on_end(goal: bool) -> void:
	_music.stop()
	if goal:
		_play("finish")
	if AutoTest.enabled and not embedded:
		AutoTest.note("platformer threed: %s за %.1f с, жизней %d, зацепов %d, падений %d, островок %d из %d" % ["дошёл" if goal else "не дошёл",
				sim.time, sim.lives, sim.hooks, sim.falls, sim.islet, level.gaps()])


func _result_caption() -> String:
	return "%d с · зацепов %d · падений %d" % [int(round(sim.time)), sim.hooks, sim.falls]


# --- Картинка --------------------------------------------------------------------------------

func _sync(dt: float) -> void:
	var yaw := level.yaw_at(sim.s)
	var at := level.world(sim.s, sim.u, sim.y)
	for i in ring_nodes.size():
		ring_nodes[i].position.y = level.ring_y(i, sim.time)
	hero.visible = sim.mode != HookSim.Mode.DOWN
	hero.position = at
	var swinging := sim.mode == HookSim.Mode.SWING
	# На верёвке тело вытянуто вдоль неё: кольцо над головой.
	hero.rotation = Vector3(sim.theta if swinging else 0.0, yaw, 0.0)
	_pose(dt)
	rope.visible = swinging
	if swinging:
		var hand := at + hero.basis * Vector3(0.0, HAND, 0.0)
		var top := ring_nodes[sim.ring].position - Vector3(0.0, 0.36, 0.0)
		var span := top - hand
		rope.position = (hand + top) / 2.0
		if span.length() > 0.05:
			var up := span.normalized()
			var side := up.cross(Vector3.FORWARD if absf(up.dot(Vector3.FORWARD)) < 0.95 else Vector3.RIGHT).normalized()
			rope.basis = Basis(side, up * span.length(), side.cross(up).normalized())
	cam.step(dt, Vector3(at.x, maxf(at.y, sim.water + 1.0), at.z), yaw, true)
	cam.apply(lowpoly.camera)


## Поза героя: бег по островку, поджатые ноги в полёте, вытянутые руки на верёвке.
func _pose(dt: float) -> void:
	_walk += absf(sim.s - _last_s) * 5.5
	_last_s = sim.s
	if hero.pink:
		return
	var rig := hero as RigModel
	match sim.mode:
		HookSim.Mode.GROUND:
			hero.walk(_walk, clampf(absf(sim.vs) / tuning.run_speed, 0.0, 1.0) * 0.75)
			if rig != null:
				rig.joint(&"hips", Vector3.ZERO)
		HookSim.Mode.SWING:
			if rig != null:
				var trail := clampf(-sim.omega * 0.22, -0.7, 0.7)
				rig.pose({&"arm_l": 3.0, &"arm_r": 3.0, &"fore_l": 0.15, &"fore_r": 0.15, &"leg_l": trail + 0.15, &"leg_r": trail - 0.1,
						&"shin_l": -0.5, &"shin_r": -0.25, &"foot_l": 0.4, &"foot_r": 0.4})
				rig.joint(&"spine", Vector3(trail * 0.3, 0.0, 0.0))
				rig.joint(&"chest", Vector3(trail * 0.2, 0.0, 0.0))
				rig.joint(&"head", Vector3(-0.25, 0.0, 0.0))
			else:
				hero.walk(0.0, 0.0)
		_:
			if rig != null:
				var rise := clampf(sim.vy / 8.0, -1.0, 1.0)
				rig.pose({&"arm_l": 2.2 + rise * 0.5, &"arm_r": 2.4 + rise * 0.5, &"fore_l": 0.4, &"fore_r": 0.3, &"leg_l": 0.7 - rise * 0.3,
						&"leg_r": -0.15 - rise * 0.2, &"shin_l": -1.1, &"shin_r": -0.6, &"foot_l": 0.3, &"foot_r": 0.3})
				rig.joint(&"spine", Vector3(0.15, 0.0, 0.0))
				rig.joint(&"chest", Vector3(0.0, 0.0, 0.0))
				rig.joint(&"head", Vector3(-0.1, 0.0, 0.0))
			else:
				hero.walk(1.2, 0.5)


func _draw_hud(canvas: CanvasItem) -> void:
	if sim == null:
		return
	var dark := lowpoly.ink(LowpolyScreen.DARK).darkened(0.5)
	var red := lowpoly.ink(LowpolyScreen.DANGER)
	var gold := lowpoly.ink(LowpolyScreen.BONUS)
	var white := lowpoly.ink(LowpolyScreen.LIGHT)
	var view := lowpoly.view
	# Отметка над кольцом, до которого достаёт крюк.
	if sim.phase == HookSim.Phase.PLAY and (sim.mode == HookSim.Mode.GROUND or sim.mode == HookSim.Mode.AIR):
		var i := sim.target()
		if i >= 0:
			var at := lowpoly.project(ring_nodes[i].position)
			var size := 9.0 + sin(_time * 10.0) * 1.5
			for corner: Vector2 in [Vector2(-1, -1), Vector2(1, -1), Vector2(1, 1), Vector2(-1, 1)]:
				var p := at + corner * size
				canvas.draw_rect(Rect2(p - Vector2(2.5, 2.5), Vector2(5, 5)), dark)
				canvas.draw_rect(Rect2(p - Vector2(1.5, 1.5), Vector2(3, 3)), gold)
			PixelFont16.draw(canvas, (at + Vector2(-PixelFont16.width("B", 1.0) / 2.0, -size - 14.0)).floor(), "B", white, gold, dark, 1.0)
	if _hurt > 0.0:
		canvas.draw_rect(Rect2(Vector2.ZERO, view), Color(lowpoly.ink(LowpolyScreen.GROUND_2).lightened(0.3), _hurt * 0.8))
	# Жизни слева сверху: сердца.
	for i in tuning.lives:
		var o := Vector2(10.0 + i * 16.0, 8.0)
		var color := red if i < sim.lives else dark.lightened(0.25)
		for row: Array in [[1, 0, 4, 2], [7, 0, 4, 2], [0, 1, 12, 4], [1, 5, 10, 2], [2, 7, 8, 1], [3, 8, 6, 1], [4, 9, 4, 1], [5, 10, 2, 1]]:
			canvas.draw_rect(Rect2(o + Vector2(row[0], row[1]) - Vector2.ONE, Vector2(row[2], row[3]) + Vector2(2, 2)), dark)
		for row: Array in [[1, 0, 4, 2], [7, 0, 4, 2], [0, 1, 12, 4], [1, 5, 10, 2], [2, 7, 8, 1], [3, 8, 6, 1], [4, 9, 4, 1], [5, 10, 2, 1]]:
			canvas.draw_rect(Rect2(o + Vector2(row[0], row[1]), Vector2(row[2], row[3])), color)
		if i < sim.lives:
			canvas.draw_rect(Rect2(o + Vector2(2, 1), Vector2(2, 2)), white)
	# Путь до маяка сверху по центру: островки отметками.
	var bar := Rect2(roundf(view.x / 2.0 - 80.0), 10.0, 160.0, 4.0)
	canvas.draw_rect(bar.grow(2.0), dark)
	canvas.draw_rect(bar, dark.lightened(0.25))
	canvas.draw_rect(Rect2(bar.position, Vector2(roundf(bar.size.x * sim.progress()), bar.size.y)), gold)
	for i in level.islets.size():
		var x := bar.position.x + roundf(bar.size.x * (level.islets[i].s - level.islets[0].s) / level.length())
		canvas.draw_rect(Rect2(x - 1.0, bar.position.y - 2.0, 2.0, bar.size.y + 4.0), white if i <= sim.islet else dark)
	if sim.phase == HookSim.Phase.COUNTDOWN:
		var text := str(ceili(sim.countdown))
		PixelFont16.draw(canvas, Vector2(roundf(view.x / 2.0 - PixelFont16.width(text, 5.0) / 2.0), roundf(view.y / 2.0 - 40.0)), text,
				white, gold, dark, 5.0)
