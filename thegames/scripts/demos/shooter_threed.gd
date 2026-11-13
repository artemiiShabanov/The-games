extends Demo
## Демка шутер × «продвинутые», каталог `docs/specs/demos_catalog.md`: «оборона аванпоста»
## (#123, решение и приёмы сложности 2026-11-13; образцы Left 4 Dead, Doom, Resident Evil 4).
## Вид от первого лица с настила вышки: мышь или правый стик обзор (стрелки тоже крутят
## взгляд), ход шагом по настилу, A или левая кнопка мыши выстрел, B или правая перезарядка.
## Враги шестью волнами идут к вышке с трёх сторон, встают у неё и бьют. Бегун падает с пули,
## щитоносца берут в голову над щитом или на замахе, бутылку метателя сбивают или уходят от
## неё, у великана слабое место это голова на замахе; бочка с порохом сносит всех рядом.
## Барабан на шесть, запас конечный, пополняется у ящика на настиле. План волн из
## `OutpostPlanGen` по сиду записи; правила и боты живут в `OutpostSim` (без окна, им же
## проверяются сто сидов), демка ведёт его шагами по 1/60 с, рисует и озвучивает его события.
##
## Общие баги (#44) и баг технологии `camera_clip` живут в `Demo` и `ThreedScreen`, демка только
## зовёт хуки. Баги жанра и баланса для этой демки включит #126.

const PLACEHOLDER_SLOTS: Array[String] = ["enemy", "prop", "gun"]
const MELODY := [0, 3, 7, 3, 0, 3, 7, 10, 8, 7, 3, 7, 8, 7, 3, null,
	0, 3, 7, 3, 0, 3, 7, 12, 10, 8, 7, 3, 2, 3, 0, null]
const BASS := [-12, -12, -12, -12, -9, -9, -9, -9, -4, -4, -4, -4, -5, -5, -7, -7]
const ISLAND := 58.0
const KIND_NAMES := ["БЕГУН", "ЩИТ", "МЕТАТЕЛЬ", "ВЕЛИКАН"]

var tuning: ShooterThreedTuning
var plan: OutpostPlan
var sim: OutpostSim
var gun: LowpolyModel
var foe_nodes: Array[Node3D] = []
var foe_models: Array[LowpolyModel] = []
var bottle_nodes: Array[LowpolyModel] = []
var keg_nodes: Array[LowpolyModel] = []
var tracer: MeshInstance3D
var blast: MeshInstance3D

var yaw := 0.0
var pitch := 0.0
var _time := 0.0
var _stop_left := 0.0
var _want_fire := false
var _want_reload := false
var _mouse_down := false
var _kick := 0.0
var _hurt := 0.0
var _hurt_yaw := 0.0
var _marker := 0.0
var _marker_head := false
var _block := 0.0
var _shake := 0.0
var _tracer_left := 0.0
var _blast_left := 0.0
var _wave_note := 0.0
var _music: AudioStreamPlayer
var _sfx := {}


func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _on_start() -> void:
	tuning = ShooterThreedTuning.load_default()
	plan = OutpostPlanGen.generate(record.seed if record != null else 1, tuning)
	sim = OutpostSim.create(plan, tuning)
	lowpoly_screen(_draw_hud)
	look_start()
	lowpoly.camera.fov = tuning.fov
	yaw = sim.yaw
	_build_world()
	_setup_audio()
	_sync(0.0)


func _setup_audio() -> void:
	var quiet := embedded
	_music = Sfx.music(Sfx.tracker_loop(MELODY, BASS, 140.0), tuning.music_db if not quiet else -80.0)
	add_child(_music)
	bug_music = _music
	if not quiet:
		_music.play()
	_sfx["go"] = Sfx.player(Sfx.blip(880.0, 0.3, 0.4, 6.0))
	_sfx["shot"] = Sfx.player(Sfx.thud(0.09, 0.6))
	_sfx["hit"] = Sfx.player(Sfx.blip(1320.0, 0.05, 0.3, 30.0))
	_sfx["kill"] = Sfx.player(Sfx.blip(660.0, 0.12, 0.35, 14.0))
	_sfx["block"] = Sfx.player(Sfx.blip(2100.0, 0.06, 0.3, 24.0))
	_sfx["boom"] = Sfx.player(Sfx.thud(0.45, 0.8))
	_sfx["pop"] = Sfx.player(Sfx.blip(1700.0, 0.08, 0.3, 18.0))
	_sfx["hurt"] = Sfx.player(Sfx.thud(0.16, 0.5))
	_sfx["reload"] = Sfx.player(Sfx.blip(420.0, 0.08, 0.25, 12.0))
	_sfx["reloaded"] = Sfx.player(Sfx.blip(620.0, 0.08, 0.3, 14.0))
	_sfx["empty"] = Sfx.player(Sfx.blip(240.0, 0.05, 0.25, 30.0))
	_sfx["refill"] = Sfx.player(Sfx.blip(990.0, 0.18, 0.35, 8.0))
	_sfx["wave"] = Sfx.player(Sfx.blip(523.0, 0.3, 0.35, 5.0))
	_sfx["finish"] = Sfx.player(Sfx.blip(880.0, 0.5, 0.4, 5.0))
	for p in _sfx.values():
		(p as AudioStreamPlayer).volume_db = tuning.sfx_db if not quiet else -80.0
		add_child(p)


func _play(name: String) -> void:
	bug_play(_sfx[name])


# --- Мир ---------------------------------------------------------------------------------------

func _add(mesh: Mesh, at: Vector3, parent: Node3D = null) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.position = at
	(parent if parent != null else lowpoly.world).add_child(node)
	return node


func _cylinder(at: Vector3, radius: float, height: float, material: Material, parent: Node3D = null, sides := 12) -> MeshInstance3D:
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = sides
	mesh.rings = 1
	mesh.material = material
	return _add(mesh, at, parent)


func _glow(color: Color, alpha := 1.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(color, alpha)
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	if alpha < 1.0:
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
	return m


func _build_world() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed if record != null else 1, ":outpost-look"))
	var screen := lowpoly as ThreedScreen
	# Остров: песчаный круг с неровным краем, пляж уходит в воду.
	var tool := SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	var segments := 64
	var rim: Array[Vector3] = []
	var shore: Array[Vector3] = []
	var ph := rng.randf_range(0.0, TAU)
	for k in segments:
		var a := TAU * k / segments
		var r := ISLAND * (1.0 + 0.06 * sin(3.0 * a + ph) + 0.04 * sin(7.0 * a + ph * 2.0))
		rim.append(Vector3(cos(a) * r, 0.0, sin(a) * r))
		shore.append(Vector3(cos(a) * (r + 16.0), -2.2, sin(a) * (r + 16.0)))
	for k in segments:
		var n := (k + 1) % segments
		for p: Vector3 in [Vector3.ZERO, rim[k], rim[n], rim[k], shore[k], shore[n], rim[k], shore[n], rim[n]]:
			tool.set_uv(Vector2(p.x, p.z) / 4.5)
			tool.add_vertex(p)
	tool.generate_normals()
	tool.generate_tangents()
	var ground := tool.commit()
	ground.surface_set_material(0, lowpoly.tex_material(lowpoly_texture("sand")))
	_add(ground, Vector3.ZERO)
	screen.add_water(Vector3(0.0, -0.7, 0.0), 1300.0)
	# Трава пятнами с неровным краем.
	var grass := SurfaceTool.new()
	grass.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in 9:
		var a := rng.randf_range(0.0, TAU)
		var mid := Vector3(cos(a), 0.0, sin(a)) * rng.randf_range(12.0, 46.0) + Vector3(0.0, 0.03, 0.0)
		var size := rng.randf_range(4.0, 8.0)
		var shift := rng.randf_range(0.0, TAU)
		var edge: Array[Vector3] = []
		for k in 24:
			var b := TAU * k / 24.0
			var r := size * (1.0 + 0.18 * sin(3.0 * b + shift) + 0.1 * sin(5.0 * b + shift * 2.0))
			edge.append(mid + Vector3(cos(b) * r, 0.0, sin(b) * r * 0.75))
		for k in 24:
			for p: Vector3 in [mid, edge[k], edge[(k + 1) % 24]]:
				grass.set_normal(Vector3.UP)
				grass.set_uv(Vector2(p.x, p.z) / 3.0)
				grass.add_vertex(p)
	grass.generate_tangents()
	var lawn := grass.commit()
	lawn.surface_set_material(0, lowpoly.tex_material(lowpoly_texture("grass")))
	_add(lawn, Vector3.ZERO)
	# Пальмы и камни по острову; на путях врагов их нет.
	var palm := lowpoly_set.model("palm", true).texture
	for i in 26:
		var a := rng.randf_range(0.0, TAU)
		var clear := true
		for side in plan.sides:
			var to_side := OutpostPlan.dir(side)
			if absf(angle_difference(atan2(to_side.y, to_side.x), a)) < 0.5:
				clear = false
		var at := Vector3(cos(a), 0.0, sin(a)) * rng.randf_range(16.0, ISLAND - 4.0)
		if not clear and at.length() < 46.0:
			continue
		if rng.randf() < 0.6 and not is_pink("prop"):
			screen.add_palm(palm, at, rng.randf_range(-PI, PI), rng.randf_range(4.4, 6.4), rng)
		else:
			var rock := spawn_model("prop", "rock")
			rock.position = at
			rock.rotation.y = rng.randf_range(-PI, PI)
			rock.scale = Vector3.ONE * rng.randf_range(1.3, 2.6)
	_build_tower()
	for i in plan.kegs.size():
		var keg := spawn_model("prop", "keg")
		keg.position = Vector3(plan.kegs[i].x, 0.0, plan.kegs[i].y)
		keg.scale = Vector3.ONE * 2.0
		keg_nodes.append(keg)
	for i in 3:
		var bottle := spawn_model("prop", "bottle")
		bottle.visible = false
		bottle.scale = Vector3.ONE * 1.6
		bottle_nodes.append(bottle)
	# След пули и вспышка взрыва.
	var line := BoxMesh.new()
	line.size = Vector3(0.025, 0.025, 1.0)
	line.material = _glow(Color(1.0, 0.92, 0.6))
	tracer = _add(line, Vector3.ZERO)
	tracer.visible = false
	tracer.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var ball := SphereMesh.new()
	ball.radius = 1.0
	ball.height = 2.0
	ball.material = _glow(Color(1.0, 0.62, 0.2), 0.75)
	blast = _add(ball, Vector3.ZERO)
	blast.visible = false
	blast.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# Револьвер в кадре.
	gun = spawn_model("gun", "pistol", lowpoly.camera)
	gun.scale = Vector3.ONE * 0.42


## Вышка: настил на сваях, перила из столбиков с канатом, ящик с патронами.
func _build_tower() -> void:
	var planks := lowpoly.tex_material(lowpoly_texture("planks"), {"uv_scale": Vector2(3.0, 3.0)})
	var wood := lowpoly.tex_material(lowpoly_texture("planks"), {"uv_scale": Vector2(1.0, 3.0)})
	var cord := lowpoly.tex_material(lowpoly_texture("sail"), {"tint": Color(0.8, 0.68, 0.48)})
	var deck := tuning.deck_height
	var radius := tuning.deck_radius
	_cylinder(Vector3(0.0, deck - 0.11, 0.0), radius, 0.22, planks, null, 28)
	for k in 6:
		var a := TAU * k / 6.0 + 0.3
		_cylinder(Vector3(cos(a) * (radius - 0.5), deck / 2.0 - 0.1, sin(a) * (radius - 0.5)), 0.16, deck, wood)
	for k in 12:
		var a := TAU * k / 12.0
		_cylinder(Vector3(cos(a) * (radius - 0.08), deck + 0.48, sin(a) * (radius - 0.08)), 0.055, 0.96, wood, null, 6)
	for up: float in [0.5, 0.94]:
		var ring := TorusMesh.new()
		ring.inner_radius = radius - 0.11
		ring.outer_radius = radius - 0.05
		ring.rings = 48
		ring.ring_segments = 6
		ring.material = cord
		_add(ring, Vector3(0.0, deck + up, 0.0))
	# Частокол вокруг вышки: враги встают перед ним. В нём проёмы со сторон атаки не нужны,
	# колья ниже настила и обзору не мешают.
	var stake_rng := RandomNumberGenerator.new()
	stake_rng.seed = 7
	for k in 46:
		var a := TAU * k / 46.0
		var tall := stake_rng.randf_range(1.3, 1.75)
		var stake := _cylinder(Vector3(cos(a) * 6.1, tall / 2.0 - 0.1, sin(a) * 6.1), 0.13, tall, wood, null, 6)
		stake.rotation = Vector3(stake_rng.randf_range(-0.06, 0.06), 0.0, stake_rng.randf_range(-0.06, 0.06))
	var flag := spawn_model("prop", "flag")
	flag.position = Vector3(plan.crate.x * 1.25, deck - 0.4, plan.crate.y * 1.25)
	flag.scale = Vector3.ONE * 1.5
	var crate := spawn_model("prop", "crate")
	crate.position = Vector3(plan.crate.x, deck, plan.crate.y)
	crate.rotation.y = 0.4
	crate.scale = Vector3.ONE * 0.85
	# Патроны на ящике: три латунных столбика.
	var brass := StandardMaterial3D.new()
	brass.albedo_color = Color(0.86, 0.66, 0.24)
	brass.metallic = 0.8
	brass.roughness = 0.3
	for k in 3:
		_cylinder(Vector3(plan.crate.x + (k - 1) * 0.14, deck + 0.82, plan.crate.y), 0.045, 0.2, brass, null, 8)


## Модель врага под его род: скелет, скелет со щитом, скелет с бутылкой, капитан-великан.
func _spawn_foe(f: OutpostSim.Foe) -> void:
	var holder := Node3D.new()
	lowpoly.world.add_child(holder)
	var model := spawn_model("enemy", "captain" if f.kind == OutpostPlan.Kind.BRUTE else "enemy", holder)
	model.scale = Vector3.ONE * f.scale
	var rig := model as RigModel
	if rig != null and f.kind == OutpostPlan.Kind.THROWER:
		rig.material.set_shader_parameter("tint", Color(0.72, 1.0, 0.7))
	if f.kind == OutpostPlan.Kind.SHIELD and not model.pink:
		var wood := lowpoly.tex_material(lowpoly_texture("planks"), {"tint": Color(0.75, 0.55, 0.4)})
		var shield := _cylinder(Vector3(0.0, 0.95, -0.45), 0.6, 0.07, wood, holder, 16)
		shield.rotation.x = PI / 2.0
		shield.name = "Shield"
		var iron := StandardMaterial3D.new()
		iron.albedo_color = Color(0.4, 0.42, 0.46)
		iron.metallic = 0.7
		iron.roughness = 0.4
		var boss := _cylinder(Vector3(0.0, 0.06, 0.0), 0.16, 0.08, iron, shield, 10)
		boss.name = "Boss"
	foe_nodes.append(holder)
	foe_models.append(model)


# --- Шаг -------------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	_hurt = maxf(_hurt - delta, 0.0)
	_marker = maxf(_marker - delta, 0.0)
	_block = maxf(_block - delta, 0.0)
	_shake = maxf(_shake - delta * 3.0, 0.0)
	_kick = maxf(_kick - delta * 7.0, 0.0)
	_wave_note = maxf(_wave_note - delta, 0.0)
	# Нажатия ловятся раз за кадр (с багом залипания из `Demo.bug_press`), правила берут их по одному.
	if not bot_driven() and running:
		var mouse := look_fire()
		if GameInput.a_just_pressed() or (mouse and not _mouse_down):
			bug_press(func() -> void: _want_fire = true)
		_mouse_down = mouse
		if GameInput.b_just_pressed() or (look_enabled and Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT)):
			bug_press(func() -> void: _want_reload = true)
	# Фризы в бою с догоном времени (`Demo.bug_frame`).
	bug_frame(delta, sim.phase == OutpostSim.Phase.PLAY, _step)


func _step(dt: float) -> void:
	_time += dt
	bug_input_tick()
	var hold := minf(_stop_left, dt)
	_stop_left -= hold
	var left := dt - hold
	while left > 0.0001 and running:
		var h := minf(left, OutpostSim.DT)
		left -= h
		var move := Vector2.ZERO
		var fire := false
		var reload := false
		if bot_driven():
			sim.bot(active_bot_mode(), h)
			move = sim.bot_move
			yaw = sim.bot_yaw
			pitch = sim.bot_pitch
			fire = sim.bot_fire
			reload = sim.bot_reload
		else:
			# Обзор мышью и правым стиком; стрелки тоже крутят взгляд (с багом управления из
			# прошлого, `Demo.bug_axis`).
			var turn := look_take(h)
			var axis := bug_axis(GameInput.axis())
			yaw = wrapf(yaw - turn.x - axis.x * 2.2 * h, -PI, PI)
			pitch = clampf(pitch - turn.y - axis.y * 1.4 * h, -1.4, 1.2)
			move = GameInput.walk()
			fire = _want_fire
			reload = _want_reload
			_want_fire = false
			_want_reload = false
		sim.step(h, move, yaw, pitch, fire, reload)
		for ev in sim.events:
			_on_event(ev)
		sim.events.clear()
		if _stop_left > 0.0:
			break
	_sync(dt)


func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"go":
			_play("go")
		&"wave":
			_wave_note = 2.0
			if int(ev[1]) > 0:
				_play("wave")
		&"shot":
			_play("shot")
			_kick = 1.0
			_tracer_left = 0.06
			var from := lowpoly.camera.global_transform * Vector3(0.28, -0.2, -0.9)
			var to: Vector3 = ev[1]
			tracer.visible = true
			tracer.scale = Vector3(1.0, 1.0, maxf(from.distance_to(to), 0.1))
			tracer.look_at_from_position((from + to) / 2.0, to, Vector3.UP)
		&"hit":
			_play("hit")
			_marker = 0.18
			_marker_head = ev[2]
		&"kill":
			_play("kill")
			_stop_left = tuning.hit_stop
		&"block":
			_play("block")
			_block = 0.6
		&"boom":
			_play("boom")
			var at := plan.kegs[int(ev[1])]
			keg_nodes[int(ev[1])].visible = false
			blast.position = Vector3(at.x, 0.8, at.y)
			blast.visible = true
			_blast_left = 0.32
			_shake = 1.0
		&"pop":
			_play("pop")
		&"hurt":
			_play("hurt")
			_hurt = 0.7
			_hurt_yaw = ev[2]
			_shake = maxf(_shake, 0.5)
		&"reload":
			_play("reload")
		&"reloaded":
			_play("reloaded")
		&"empty":
			_play("empty")
		&"refill":
			_play("refill")
		&"win":
			end_demo(true)
		&"dead", &"timeout":
			end_demo(false)


func _on_end(goal: bool) -> void:
	_music.stop()
	if goal:
		_play("finish")
	if AutoTest.enabled and not embedded:
		AutoTest.note("shooter threed: %s за %.1f с, здоровья %d, волна %d из %d, выстрелов %d, попаданий %d, в щит %d, убито %d из %d, бочек %d, пополнений %d" % [
				"выстоял" if goal else "не выстоял", sim.time, sim.health, sim.wave + 1, plan.waves.size(), sim.shots, sim.hits, sim.blocked,
				sim.kills, plan.total(), sim.booms, sim.refills])


func _result_title(goal: bool) -> String:
	return "аванпост устоял" if goal else "аванпост пал"


func _result_caption() -> String:
	return "волна %d из %d · убито %d · %d с" % [sim.wave + 1, plan.waves.size(), sim.kills, int(round(sim.time))]


# --- Картинка --------------------------------------------------------------------------------

func _sync(dt: float) -> void:
	while foe_nodes.size() < sim.foes.size():
		_spawn_foe(sim.foes[foe_nodes.size()])
	for i in sim.foes.size():
		_pose_foe(sim.foes[i], foe_nodes[i], foe_models[i])
	for i in bottle_nodes.size():
		var node := bottle_nodes[i]
		node.visible = i < sim.bottles.size()
		if node.visible:
			node.position = sim.bottles[i].at()
			node.rotation = Vector3(_time * 9.0 + i, _time * 4.0, 0.0)
	_tracer_left -= dt
	if _tracer_left <= 0.0:
		tracer.visible = false
	if _blast_left > 0.0:
		_blast_left -= dt
		var k := 1.0 - _blast_left / 0.32
		blast.scale = Vector3.ONE * tuning.keg_blast * lerpf(0.25, 1.0, sqrt(clampf(k, 0.0, 1.0)))
		((blast.mesh as SphereMesh).material as StandardMaterial3D).albedo_color.a = 0.75 * (1.0 - k)
		blast.visible = _blast_left > 0.0
	# Камера в глазах героя.
	var eye := sim.eye()
	var jitter := Vector3(sin(_time * 63.0), cos(_time * 49.0), 0.0) * 0.05 * _shake
	lowpoly.camera.position = eye + jitter
	lowpoly.camera.rotation = Vector3(pitch + _kick * 0.025, yaw, 0.0)
	# Револьвер: отдача и опускание на перезарядке.
	var dip := sin(clampf(sim.reload_left / tuning.reload_seconds, 0.0, 1.0) * PI) if sim.reload_left > 0.0 else 0.0
	gun.position = Vector3(0.3, -0.27 - dip * 0.3, -0.62 + _kick * 0.07)
	gun.rotation = Vector3(_kick * 0.3 - dip * 0.9, 0.0, 0.0)


func _pose_foe(f: OutpostSim.Foe, node: Node3D, model: LowpolyModel) -> void:
	node.position = Vector3(f.pos.x, 0.0, f.pos.y)
	node.rotation.y = atan2(f.pos.x, f.pos.y)
	if f.state == OutpostSim.State.DEAD:
		# Падает навзничь и уходит в песок.
		var fall := clampf(f.dead_for / 0.35, 0.0, 1.0)
		model.rotation.x = fall * PI / 2.0
		node.position.y = -maxf(f.dead_for - 1.2, 0.0) * 1.2
		node.visible = f.dead_for < 2.2
		model.flash(false)
		return
	model.flash(f.hit_for < 0.07)
	if model.pink:
		return
	var rig := model as RigModel
	if f.state == OutpostSim.State.WALK:
		model.walk(f.walked * (2.6 if f.kind == OutpostPlan.Kind.RUNNER else 2.2) / f.scale, 0.75 if f.kind == OutpostPlan.Kind.RUNNER else 0.5)
		return
	model.walk(0.0, 0.0)
	if rig == null:
		return
	# У вышки: замах перед ударом, щит на замахе уходит в сторону.
	var wind := clampf(1.0 - f.cooldown / maxf(f.windup if f.windup > 0.0 else 0.45, 0.01), 0.0, 1.0) if f.cooldown < maxf(f.windup, 0.45) else 0.0
	rig.pose({&"arm_r": 0.4 + wind * 2.5, &"fore_r": 0.6 + wind * 0.5, &"arm_l": 0.5, &"fore_l": 1.1})
	rig.joint(&"spine", Vector3(-wind * 0.2, 0.0, 0.0))
	rig.joint(&"head", Vector3(0.45, 0.0, 0.0))
	var shield := node.get_node_or_null("Shield") as Node3D
	if shield != null:
		shield.position = Vector3(0.0 + (0.75 if f.winding() else 0.0), 0.95, -0.45 + (0.3 if f.winding() else 0.0))


# --- HUD ---------------------------------------------------------------------------------------

func _draw_hud(canvas: CanvasItem) -> void:
	if sim == null:
		return
	var h := ThreedHud.begin(canvas, lowpoly)
	var view := lowpoly.view
	var mid := view / 2.0
	# Ранен: красная дуга с той стороны, откуда ударили.
	if _hurt > 0.0:
		h.rect(Rect2(Vector2.ZERO, view), Color(0.85, 0.1, 0.08, _hurt * 0.22))
		var side := angle_difference(yaw, _hurt_yaw)
		var at := -PI / 2.0 - side
		h.arc(mid, 58.0, at - 0.45, at + 0.45, Color(ThreedHud.RED, minf(_hurt * 1.6, 1.0)), 3.0)
	# Враги за кадром: стрелки по кругу от прицела; красные уже бьют.
	for f in sim.foes:
		if f.state == OutpostSim.State.DEAD:
			continue
		var bearing := angle_difference(yaw, atan2(-(f.pos.x - sim.pos.x), -(f.pos.y - sim.pos.y)))
		if absf(bearing) < 0.75:
			continue
		var at := -PI / 2.0 - bearing
		var dir := Vector2(cos(at), sin(at))
		var tip := mid + dir * 70.0
		var across := Vector2(-dir.y, dir.x)
		var color := ThreedHud.RED if f.state == OutpostSim.State.ATTACK else ThreedHud.GOLD
		h.polygon(PackedVector2Array([tip, tip - dir * 7.0 + across * 4.0, tip - dir * 7.0 - across * 4.0]), Color(0.0, 0.0, 0.0, 0.45))
		h.polygon(PackedVector2Array([tip - dir * 1.0, tip - dir * 6.2 + across * 3.0, tip - dir * 6.2 - across * 3.0]), color)
	# Слабое место великана на замахе.
	for f in sim.foes:
		if f.kind == OutpostPlan.Kind.BRUTE and f.winding() and not lowpoly.camera.is_position_behind(sim.head_of(f)):
			var at := lowpoly.project(sim.head_of(f))
			h.arc(at, 7.0 + sin(_time * 14.0) * 1.2, 0.0, TAU, ThreedHud.RED, 1.4)
	# Прицел: точка и кольцо; на перезарядке вместо него заполняющийся круг.
	if sim.reload_left > 0.0:
		var k := 1.0 - sim.reload_left / tuning.reload_seconds
		h.arc(mid, 9.0, 0.0, TAU, Color(0.0, 0.0, 0.0, 0.4), 3.2)
		h.arc(mid, 9.0, -PI / 2.0, -PI / 2.0 + TAU * maxf(k, 0.01), ThreedHud.GOLD, 2.0)
	else:
		var spread := 5.0 + _kick * 4.0
		for k in 4:
			var dir := Vector2.RIGHT.rotated(PI / 2.0 * k)
			h.line(mid + dir * (spread + 0.4), mid + dir * (spread + 5.6), Color(0.0, 0.0, 0.0, 0.5), 2.0)
			h.line(mid + dir * (spread + 1.0), mid + dir * (spread + 5.0), ThreedHud.WHITE, 1.0)
		h.circle(mid, 1.5, Color(0.0, 0.0, 0.0, 0.5))
		h.circle(mid, 0.9, ThreedHud.WHITE)
	if _marker > 0.0:
		var color := ThreedHud.RED if _marker_head else ThreedHud.WHITE
		for k in 4:
			var dir := Vector2(1.0, 1.0).normalized().rotated(PI / 2.0 * k)
			h.line(mid + dir * 4.0, mid + dir * 9.0, color, 1.4)
	if _block > 0.0:
		h.text(mid + Vector2(0.0, 22.0), "ЩИТ: БЕЙ В ГОЛОВУ", 6.5, Color(ThreedHud.GOLD, minf(_block * 3.0, 1.0)), 0, Color(0.0, 0.0, 0.0, 0.6))
	# Волна сверху по центру: номер и сколько врагов осталось.
	h.panel(Rect2(mid.x - 62.0, 9.0, 124.0, 30.0), 7.0)
	h.text(Vector2(mid.x - 54.0, 17.5), "ВОЛНА", 5.2, ThreedHud.DIM, -1)
	h.text(Vector2(mid.x - 54.0, 29.0), "%d / %d" % [sim.wave + 1, plan.waves.size()], 11.0, ThreedHud.GOLD if _wave_note > 0.0 and int(_wave_note * 6.0) % 2 == 0 else ThreedHud.WHITE, -1)
	h.text(Vector2(mid.x + 54.0, 17.5), "ВРАГОВ", 5.2, ThreedHud.DIM, 1)
	h.text(Vector2(mid.x + 54.0, 29.0), str(sim.left_total()), 11.0, ThreedHud.WHITE, 1)
	for w in plan.waves.size():
		h.circle(Vector2(mid.x - 12.5 + w * 5.0, 24.0), 1.7, ThreedHud.GOLD if w < sim.wave else (ThreedHud.WHITE if w == sim.wave else ThreedHud.FAINT))
	# Здоровье слева внизу.
	h.panel(Rect2(10.0, view.y - 38.0, 112.0, 28.0), 7.0)
	h.heart(Vector2(24.0, view.y - 24.0), 6.4, ThreedHud.RED)
	var life := float(sim.health) / tuning.health
	h.bar(Vector2(38.0, view.y - 21.0), Vector2(112.0, view.y - 21.0), ThreedHud.FAINT, 4.0)
	if life > 0.0:
		h.bar(Vector2(38.0, view.y - 21.0), Vector2(38.0 + 74.0 * life, view.y - 21.0), ThreedHud.RED if life < 0.35 else ThreedHud.GREEN, 4.0)
	h.text(Vector2(38.0, view.y - 30.0), str(sim.health), 6.5, ThreedHud.WHITE, -1)
	# Патроны справа внизу: барабан и запас.
	h.panel(Rect2(view.x - 122.0, view.y - 38.0, 112.0, 28.0), 7.0)
	for i in tuning.clip:
		var c := Vector2(view.x - 112.0 + i * 9.5, view.y - 24.0)
		h.bar(c + Vector2(0.0, -5.0), c + Vector2(0.0, 5.0), ThreedHud.GOLD if i < sim.clip else ThreedHud.FAINT, 4.6)
	var dry := sim.reserve == 0
	h.text(Vector2(view.x - 18.0, view.y - 28.5), str(sim.reserve), 11.0, ThreedHud.RED if dry else ThreedHud.WHITE, 1)
	h.text(Vector2(view.x - 18.0, view.y - 17.0), "ЗАПАС", 4.6, ThreedHud.DIM, 1)
	# Подсказка про ящик: когда запас кончается.
	if sim.reserve <= tuning.clip and sim.phase == OutpostSim.Phase.PLAY:
		var crate := Vector3(plan.crate.x, tuning.deck_height + 1.2, plan.crate.y)
		if not lowpoly.camera.is_position_behind(crate):
			var at := lowpoly.project(crate)
			h.text(at, "ПАТРОНЫ", 6.0, ThreedHud.GOLD, 0, Color(0.0, 0.0, 0.0, 0.6))
		if dry and sim.clip <= 2:
			h.text(Vector2(view.x - 66.0, view.y - 46.0), "К ЯЩИКУ ЗА ПАТРОНАМИ", 5.6, ThreedHud.RED if int(_time * 4.0) % 2 == 0 else ThreedHud.GOLD,
					0, Color(0.0, 0.0, 0.0, 0.6))
	if sim.crate_left > 0.0:
		h.arc(mid, 14.0, -PI / 2.0, -PI / 2.0 + TAU * sim.crate_left / tuning.crate_seconds, ThreedHud.GOLD, 1.6)
	if sim.phase == OutpostSim.Phase.COUNTDOWN:
		h.text(Vector2(mid.x, mid.y - 30.0), str(ceili(sim.countdown)), 46.0, ThreedHud.WHITE, 0, Color(0.05, 0.07, 0.11, 0.8))
	h.end()
