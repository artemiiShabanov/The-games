extends Demo
## Демка спорт × «продвинутые», каталог `docs/specs/demos_catalog.md`: сноуборд, у пиратов
## «спуск по дюне» на доске (#124, решение и приёмы сложности 2026-11-13; образцы SSX, 1080°
## Snowboarding, Alto's Adventure). Камера за спиной, райдер едет вниз сам. Влево и вправо
## кант, A держать и отпустить прыжок (чем дольше, тем выше), B или вниз присед; мышь и правый
## стик дают оглядеться. Надо доехать до
## пляжа, пройдя не меньше двух третей ворот: ворота к концу уже, чаще и дальше в стороны.
## Доска на скорости перекладывается медленно, резкий руль против дуги срывает кант, в приседе
## быстрее, но поворот хуже; трамплины перелетают полосу камней, приземляться надо почти по
## склону; удар о камень или пальму это падение. Склон из `DuneCourseGen` по сиду записи;
## правила и боты живут в `DuneSim` (без окна, им же проверяются сто сидов), демка ведёт его
## шагами по 1/60 с, рисует и озвучивает его события.
##
## Общие баги (#44) и баг технологии `camera_clip` живут в `Demo` и `ThreedScreen`, демка только
## зовёт хуки. Баги жанра и баланса для этой демки включит #126.

const PLACEHOLDER_SLOTS: Array[String] = ["hero", "prop", "finish"]
const MELODY := [7, null, 12, 14, 16, null, 14, 12, 9, null, 12, 14, 16, 19, 16, null,
	7, null, 12, 14, 16, null, 14, 12, 17, 16, 14, 12, 11, 12, 7, null]
const BASS := [-5, -5, -5, -5, -8, -8, -8, -8, -3, -3, -3, -3, -5, -5, -7, -7]
const SIDE := 36.0
const PUFFS := 26
const LEFT_FLAG := Color(0.9, 0.24, 0.2)
const RIGHT_FLAG := Color(0.2, 0.42, 0.9)

var tuning: SportThreedTuning
var course: DuneCourse
var sim: DuneSim
var rider: Node3D
var hero: LowpolyModel
var board: MeshInstance3D
var gate_flags: Array[Array] = []
var trail: MeshInstance3D
## Струи песчинок: из-под канта и хвост за доской.
var jets: Array[CPUParticles3D] = []
var _trail_mesh: ImmediateMesh
## След: левая и правая точка борозды и разрыв перед ней (прыжок).
var _trail: Array[Array] = []
var _trail_s := -100.0

var _time := 0.0
var _stop_left := 0.0
## Сглаженный сгиб коленей, секунд мигания после срыва канта.
var _bend := 0.55
var _blink := 0.0
var _was_caught := false
var _cam_yaw := 0.0
var _look := Vector2.ZERO
var _look_idle := 9.0
var _shake := 0.0
var _note := ""
var _note_left := 0.0
var _note_good := true
var _tumble := 0.0
var _puffs: Array[MeshInstance3D] = []
var _puff_life: Array[float] = []
var _puff_next := 0
var _puff_wait := 0.0
var _music: AudioStreamPlayer
var _wind: AudioStreamPlayer
var _sfx := {}


func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _on_start() -> void:
	tuning = SportThreedTuning.load_default()
	course = DuneCourseGen.generate(record.seed if record != null else 1, tuning)
	sim = DuneSim.create(course, tuning)
	if has_bug(&"wild_physics"):
		sim.air_mult = bug_param(&"wild_physics", &"dune_air_mult", 1.8)
		sim.air_gravity = bug_param(&"wild_physics", &"dune_air_gravity", 0.45)
	if has_bug(&"ball_to_space"):
		sim.space_every = maxi(int(bug_param(&"ball_to_space", &"dune_space_every", 2.0)), 1)
	if has_bug(&"sneeze_enemies"):
		sim.gust = bug_param(&"sneeze_enemies", &"dune_gust", 7.0)
	if has_bug(&"unreachable_coins"):
		sim.goal_extra = maxi(int(bug_param(&"unreachable_coins", &"dune_goal_extra", 8.0)), 1)
	lowpoly_screen(_draw_hud)
	look_start()
	lowpoly.camera.fov = tuning.cam_fov
	_build_world()
	_build_puffs()
	_setup_audio()
	_cam_yaw = course.yaw(sim.s)
	_sync(0.0)


func _setup_audio() -> void:
	var quiet := embedded
	_music = Sfx.music(Sfx.tracker_loop(MELODY, BASS, 144.0), tuning.music_db if not quiet else -80.0)
	add_child(_music)
	bug_music = _music
	if not quiet:
		_music.play()
	# Шорох песка под доской: петля шума, громкость по скорости.
	var hiss := Sfx.hiss(0.6, 0.2)
	hiss.loop_mode = AudioStreamWAV.LOOP_FORWARD
	hiss.loop_end = hiss.data.size() / 2
	_wind = Sfx.player(hiss, -40.0)
	add_child(_wind)
	if not quiet:
		_wind.play()
	_sfx["go"] = Sfx.player(Sfx.blip(880.0, 0.3, 0.4, 6.0))
	_sfx["gate"] = Sfx.player(Sfx.blip(1180.0, 0.12, 0.35, 12.0))
	_sfx["miss"] = Sfx.player(Sfx.blip(220.0, 0.16, 0.3, 10.0))
	_sfx["ramp"] = Sfx.player(Sfx.blip(520.0, 0.2, 0.3, 6.0))
	_sfx["land"] = Sfx.player(Sfx.thud(0.1, 0.4))
	_sfx["catch"] = Sfx.player(Sfx.hiss(0.2, 0.2))
	_sfx["fall"] = Sfx.player(Sfx.thud(0.3, 0.65))
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


func _cylinder(at: Vector3, radius: float, height: float, material: Material, parent: Node3D = null) -> MeshInstance3D:
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = 8
	mesh.rings = 1
	mesh.material = material
	return _add(mesh, at, parent)


func _paint(color: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = 0.8
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	return m


## Точка склона с рябью барханов за краем трассы.
func _ground(s: float, x: float) -> Vector3:
	var p := course.world(s, x)
	var out := clampf((absf(x) - course.half_width) / 8.0, 0.0, 1.0)
	p.y += out * (0.5 * sin(s * 0.11 + x * 0.3) + 0.35 * sin(s * 0.047 - x * 0.21))
	return p


func _build_world() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed if record != null else 1, ":dune-look"))
	var screen := lowpoly as ThreedScreen
	# Склон: сетка поперёк линии склона, по краям барханы стеной.
	var tool := SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	var columns := 14
	var step := course.step
	var s := -24.0
	while s < course.length + 76.0:
		for c in columns:
			var x0 := lerpf(-SIDE, SIDE, float(c) / columns)
			var x1 := lerpf(-SIDE, SIDE, float(c + 1) / columns)
			var a := _ground(s, x0)
			var b := _ground(s, x1)
			var c2 := _ground(s + step, x1)
			var d := _ground(s + step, x0)
			for p: Vector3 in [a, d, c2, a, c2, b]:
				tool.set_uv(Vector2(p.x, p.z) / 5.0)
				tool.add_vertex(p)
		s += step
	tool.generate_normals()
	tool.generate_tangents()
	var ground := tool.commit()
	ground.surface_set_material(0, screen.ground_material(lowpoly_texture("sand"), Color(1.12, 1.08, 0.98)))
	_add(ground, Vector3.ZERO)
	# Внизу пляж и море.
	var low := course.height(course.length + 70.0)
	screen.add_water(Vector3(course.sway(course.length), low + 0.6, -course.length - 360.0), 1500.0)
	var wood := lowpoly.tex_material(lowpoly_texture("planks"), {"uv_scale": Vector2(1.0, 2.0)})
	# Ворота: слева красный флаг, справа синий.
	for g in course.gates:
		var pair: Array = []
		for side: float in [-1.0, 1.0]:
			var foot := course.world(g.s, g.x + side * g.half)
			_cylinder(foot + Vector3(0.0, 1.4, 0.0), 0.06, 2.8, wood)
			var cloth := BoxMesh.new()
			cloth.size = Vector3(0.95, 0.62, 0.03)
			cloth.material = _paint(LEFT_FLAG if side < 0.0 else RIGHT_FLAG)
			var flag := _add(cloth, foot + Vector3(-side * 0.5, 2.4, 0.0))
			flag.rotation.y = course.yaw(g.s)
			pair.append(flag)
		gate_flags.append(pair)
	# Трамплины: дощатый клин перед кромкой.
	for r in course.ramps:
		var wedge := SurfaceTool.new()
		wedge.begin(Mesh.PRIMITIVE_TRIANGLES)
		var half := r.width / 2.0
		var a := course.world(r.s - course.ramp_length, r.x - half, 0.02)
		var b := course.world(r.s - course.ramp_length, r.x + half, 0.02)
		var c := course.world(r.s, r.x + half, course.ramp_height)
		var d := course.world(r.s, r.x - half, course.ramp_height)
		var e := course.world(r.s, r.x + half, -0.3)
		var f := course.world(r.s, r.x - half, -0.3)
		for item: Array in [[a, 0, 0], [d, 0, 3], [c, 2, 3], [a, 0, 0], [c, 2, 3], [b, 2, 0], [d, 0, 0], [f, 0, 0.6], [e, 2, 0.6], [d, 0, 0],
				[e, 2, 0.6], [c, 2, 0], [a, 0, 0], [f, 1, 0.6], [d, 1, 0], [b, 0, 0], [c, 1, 0], [e, 1, 0.6]]:
			wedge.set_uv(Vector2(item[1], item[2]))
			wedge.add_vertex(item[0])
		wedge.generate_normals()
		wedge.generate_tangents()
		var mesh := wedge.commit()
		mesh.surface_set_material(0, lowpoly.tex_material(lowpoly_texture("planks")))
		_add(mesh, Vector3.ZERO)
	# Барьеры: частокол из брёвен поперёк пути с перекладиной.
	for b in course.bars:
		var posts := int(b.half * 2.0 / 0.9)
		for k in posts + 1:
			var px := b.x - b.half + b.half * 2.0 * k / posts
			var post := _cylinder(course.world(b.s, px, b.height / 2.0 - 0.15), 0.15, b.height + 0.3 + 0.12 * sin(k * 1.9), wood)
			post.rotation = Vector3(0.06 * sin(k * 2.3), 0.0, 0.05 * cos(k * 1.7))
		var rail := BoxMesh.new()
		rail.size = Vector3(b.half * 2.0 + 0.4, 0.16, 0.14)
		rail.material = lowpoly.tex_material(lowpoly_texture("planks"), {"uv_scale": Vector2(4.0, 1.0)})
		var beam := _add(rail, course.world(b.s + 0.2, b.x, b.height * 0.62))
		beam.rotation.y = course.yaw(b.s)
		beam.rotation.z = atan2(course.height(b.s, b.x + b.half) - course.height(b.s, b.x - b.half), b.half * 2.0)
	# Препятствия: камни и пальмы.
	var palm := lowpoly_set.model("palm", true).texture
	for r in course.rocks:
		var at := course.world(r.s, r.x, -0.12)
		if r.tall and not is_pink("prop"):
			screen.add_palm(palm, at, rng.randf_range(-PI, PI), rng.randf_range(4.4, 5.6), rng)
		else:
			var rock := spawn_model("prop", "rock")
			rock.position = at
			rock.rotation.y = rng.randf_range(-PI, PI)
			rock.scale = Vector3.ONE * r.radius / 0.6
	# Барханы по бокам: пальмы, камни, обломки.
	var at_s := rng.randf_range(0.0, 20.0)
	var flank := 1.0
	while at_s < course.length + 40.0:
		var off := course.half_width + rng.randf_range(3.5, 13.0)
		var at := _ground(at_s, flank * off) - Vector3(0.0, 0.15, 0.0)
		if rng.randf() < 0.6 and not is_pink("prop"):
			screen.add_palm(palm, at, rng.randf_range(-PI, PI), rng.randf_range(4.2, 6.2), rng)
		else:
			var names := ["rock", "rock", "barrel", "crate", "chest"]
			var prop := spawn_model("prop", names[rng.randi_range(0, names.size() - 1)])
			prop.position = at
			prop.rotation.y = rng.randf_range(-PI, PI)
			prop.scale = Vector3.ONE * rng.randf_range(1.2, 2.4)
		at_s += rng.randf_range(9.0, 20.0)
		flank = -flank if rng.randf() < 0.7 else flank
	# Финиш: растяжка между мачтами и маяк на пляже.
	for side: float in [-1.0, 1.0]:
		_cylinder(course.world(course.length, side * course.half_width, 3.0), 0.14, 6.4, wood)
	var banner := lowpoly.add_box(Vector3.ZERO, Vector3(course.half_width * 2.0, 0.9, 0.08), lowpoly_texture("sail"), 3.0)
	banner.position = course.world(course.length, 0.0, 5.4)
	var tower := spawn_model("finish", "lighthouse")
	tower.position = course.world(course.length + 62.0, course.half_width * 0.9, -0.4)
	# Райдер: доска и матрос боком на ней.
	rider = Node3D.new()
	lowpoly.world.add_child(rider)
	var deck := BoxMesh.new()
	deck.size = Vector3(0.34, 0.05, 1.55)
	deck.material = lowpoly.tex_material(lowpoly_texture("planks"), {"tint": Color(1.0, 0.86, 0.7)})
	# Доска живёт в мире и каждый кадр встаёт под стопы модели (плейтест 2026-11-13).
	board = _add(deck, Vector3.ZERO)
	hero = spawn_model("hero", "hero", rider)
	hero.position = Vector3(0.0, 0.06, 0.0)
	_build_sand()


## След доски на песке и песчинки из-под неё.
func _build_sand() -> void:
	var groove := StandardMaterial3D.new()
	groove.vertex_color_use_as_albedo = true
	groove.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	groove.roughness = 1.0
	groove.cull_mode = BaseMaterial3D.CULL_DISABLED
	_trail_mesh = ImmediateMesh.new()
	trail = _add(_trail_mesh, Vector3.ZERO)
	trail.material_override = groove
	trail.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# Песчинка: мягкий кружок.
	var fade := Gradient.new()
	fade.set_color(0, Color(1.0, 1.0, 1.0, 1.0))
	fade.set_color(1, Color(1.0, 1.0, 1.0, 0.0))
	var dot := GradientTexture2D.new()
	dot.gradient = fade
	dot.fill = GradientTexture2D.FILL_RADIAL
	dot.fill_from = Vector2(0.5, 0.5)
	dot.fill_to = Vector2(0.5, 0.05)
	dot.width = 16
	dot.height = 16
	var grain := StandardMaterial3D.new()
	grain.albedo_color = Color(0.9, 0.8, 0.57, 0.9)
	grain.albedo_texture = dot
	grain.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	grain.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	grain.billboard_keep_scale = true
	grain.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	var speck := QuadMesh.new()
	speck.size = Vector2(0.055, 0.055)
	speck.material = grain
	for i in 2:
		var jet := CPUParticles3D.new()
		jet.mesh = speck
		jet.amount = 520 if i == 0 else 260
		jet.lifetime = 0.75
		jet.local_coords = false
		jet.spread = 26.0 if i == 0 else 40.0
		jet.initial_velocity_min = 5.0
		jet.initial_velocity_max = 11.0
		jet.gravity = Vector3(0.0, -15.0, 0.0)
		jet.scale_amount_min = 0.5
		jet.scale_amount_max = 1.6
		jet.emitting = false
		jet.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		lowpoly.world.add_child(jet)
		jets.append(jet)


func _build_puffs() -> void:
	var gradient := Gradient.new()
	gradient.set_color(0, Color(1.0, 1.0, 1.0, 0.85))
	gradient.set_color(1, Color(1.0, 1.0, 1.0, 0.0))
	var tex := GradientTexture2D.new()
	tex.gradient = gradient
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(0.5, 0.0)
	tex.width = 48
	tex.height = 48
	for i in PUFFS:
		var m := StandardMaterial3D.new()
		m.albedo_texture = tex
		m.albedo_color = Color(0.93, 0.83, 0.6, 0.6)
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		var quad := QuadMesh.new()
		quad.material = m
		var node := _add(quad, Vector3.ZERO)
		node.visible = false
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_puffs.append(node)
		_puff_life.append(0.0)


func _puff(at: Vector3) -> void:
	_puffs[_puff_next].position = at
	_puffs[_puff_next].visible = true
	_puff_life[_puff_next] = 1.0
	_puff_next = (_puff_next + 1) % PUFFS


# --- Шаг -------------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	_shake = maxf(_shake - delta * 3.0, 0.0)
	_note_left = maxf(_note_left - delta, 0.0)
	_blink = maxf(_blink - delta, 0.0)
	var turn := look_take(delta)
	if turn.length() > 0.0004:
		_look_idle = 0.0
		_look.x = clampf(_look.x - turn.x, -2.4, 2.4)
		_look.y = clampf(_look.y + turn.y, -0.2, 0.6)
	else:
		_look_idle += delta
		if _look_idle > 0.7:
			_look = _look.lerp(Vector2.ZERO, 1.0 - exp(-2.5 * delta))
	# Фризы в движении с догоном времени (`Demo.bug_frame`).
	bug_frame(delta, sim.countdown <= 0.0 and sim.fallen_left <= 0.0, _step)


func _step(dt: float) -> void:
	_time += dt
	bug_input_tick()
	var hold := minf(_stop_left, dt)
	_stop_left -= hold
	var left := dt - hold
	while left > 0.0001 and running:
		var h := minf(left, DuneSim.DT)
		left -= h
		var steer := 0.0
		var jump := false
		var crouch := false
		if bot_driven():
			sim.bot(active_bot_mode())
			steer = sim.bot_steer
			jump = sim.bot_jump
			crouch = sim.bot_crouch
		else:
			# Кант с багом управления из прошлого (`Demo.bug_axis`).
			var axis := bug_axis(GameInput.axis())
			steer = axis.x
			crouch = GameInput.b_pressed() or axis.y > 0.5
			jump = GameInput.a_pressed()
		sim.step(h, steer, jump, crouch)
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
		&"gate":
			var ok: bool = ev[2]
			_play("gate" if ok else "miss")
			_note = "ЕСТЬ!" if ok else "МИМО"
			_note_good = ok
			_note_left = 0.8
			for flag: MeshInstance3D in gate_flags[int(ev[1])]:
				((flag.mesh as BoxMesh).material as StandardMaterial3D).albedo_color = Color(0.3, 0.8, 0.4) if ok else Color(0.45, 0.45, 0.45)
		&"ramp":
			_play("ramp")
		&"hop":
			_play("ramp")
		&"land":
			_play("land")
			_shake = maxf(_shake, 0.4)
		&"catch":
			_play("catch")
			_was_caught = true
			_note = "СРЫВ КАНТА"
			_note_good = false
			_note_left = 0.8
			_shake = maxf(_shake, 0.5)
		&"fall":
			_play("fall")
			_shake = 1.0
			_stop_left = tuning.hit_stop
			_tumble = 0.0
			if AutoTest.enabled and not embedded:
				AutoTest.note("sport threed: падение на %.0f м" % sim.s)
		&"finish":
			end_demo(sim.won)
		&"timeout":
			end_demo(false)


func _on_end(goal: bool) -> void:
	_music.stop()
	_wind.stop()
	if goal:
		_play("finish")
	if AutoTest.enabled and not embedded:
		AutoTest.note("sport threed: %s за %.1f с, ворот %d из %d (надо %d), падений %d, срывов канта %d, трамплинов %d, предел %.0f км/ч" % [
				"прошёл" if goal else "не прошёл", sim.time, sim.passed, course.gates.size(), sim.need(), sim.falls, sim.catches, sim.jumps,
				sim.top * 3.6])


func _result_title(goal: bool) -> String:
	return "спуск засчитан" if goal else ("мало ворот" if sim.finished else "не доехал")


func _result_caption() -> String:
	return "ворот %d из %d · %d с · падений %d" % [sim.passed, course.gates.size(), int(round(sim.time)), sim.falls]


# --- Картинка --------------------------------------------------------------------------------

func _sync(dt: float) -> void:
	var at := course.world(sim.s, sim.x, sim.lift + sim.ride)
	var line := course.yaw(sim.s)
	var tilt := atan(course.slope(sim.s))
	# На клине трамплина доска задирается по нему.
	var climb := atan(course.ramp_height / course.ramp_length) if sim.ride > 0.0 else 0.0
	rider.position = at
	var fallen := sim.fallen_left > 0.0
	var caught := sim.catch_left > 0.0
	if fallen:
		# Кувырок и лёжа.
		_tumble += dt
		rider.rotation = Vector3(-tilt, line, 0.0)
		hero.rotation = Vector3(minf(_tumble * 9.0, PI / 2.0), -PI / 2.0, 0.0)
		hero.position = Vector3(0.0, 0.25, 0.0)
	else:
		# Доска по курсу и по уклону, с креном на кант. Натянутый кант видно заранее: райдера
		# заваливает сильнее и трясёт; на срыве доску мотает.
		var shake := sim.strain * sim.strain
		var wobble := sin(_time * 47.0) * 0.07 * shake + (sin(_time * 31.0) * 0.28 if caught else 0.0)
		var roll := -sim.edge * (0.42 + 0.5 * sim.strain) + wobble
		var skid := sin(_time * 23.0) * 0.35 if caught else sin(_time * 39.0) * 0.05 * shake
		rider.rotation = Vector3((-tilt * cos(sim.heading) if not sim.airborne else -tilt * 0.4) + climb, line - sim.heading + skid, roll)
	# После срыва, когда руль вернулся, модель мигает белым.
	if _was_caught and not caught:
		_was_caught = false
		_blink = 0.9
	hero.flash(_blink > 0.0 and int(_blink * 12.0) % 2 == 0)
	_pose(fallen)
	# Во встроенном режиме (лента) демка стартует раньше, чем попадает в дерево сцены: мировых
	# координат у доски и следа ещё нет.
	if rider.is_inside_tree():
		_place_board(fallen, line, tilt)
		_sand(dt, at, line, tilt, fallen)
	# Шорох песка по скорости.
	if _wind.playing:
		var loud := clampf(sim.speed / 44.0, 0.0, 1.0) * (0.0 if sim.airborne or fallen else 1.0)
		_wind.volume_db = lerpf(_wind.volume_db, lerpf(-40.0, tuning.sfx_db - 8.0, loud), clampf(8.0 * dt, 0.0, 1.0))
		_wind.pitch_scale = 0.7 + loud * 0.6 + absf(sim.edge) * 0.25
	# Песок из-под канта.
	_puff_wait -= dt
	if _puff_wait <= 0.0 and not sim.airborne and not fallen and sim.speed > 5.0 and (absf(sim.edge) > 0.35 or sim.catch_left > 0.0):
		_puff_wait = 0.03
		_puff(at + Vector3(0.0, 0.2, 0.9).rotated(Vector3.UP, line - sim.heading))
	for i in PUFFS:
		if _puff_life[i] <= 0.0:
			continue
		_puff_life[i] -= dt * 1.6
		var node := _puffs[i]
		node.visible = _puff_life[i] > 0.0
		node.position.y += dt * 1.1
		node.scale = Vector3.ONE * lerpf(3.0, 0.8, _puff_life[i])
		((node.mesh as QuadMesh).material as StandardMaterial3D).albedo_color.a = 0.55 * maxf(_puff_life[i], 0.0)
	# Камера за спиной выше по склону: смотрит вниз по линии склона с поправкой на курс.
	var want := line - sim.heading * 0.45
	_cam_yaw = lerp_angle(_cam_yaw, want, 1.0 - exp(-5.0 * dt)) if dt > 0.0 else want
	var yaw := _cam_yaw + _look.x
	var back := Vector3(sin(yaw), 0.0, cos(yaw))
	var ground := course.world(sim.s, sim.x, sim.ride)
	var eye := ground + back * tuning.cam_distance + Vector3(0.0, tuning.cam_height + tan(tilt) * tuning.cam_distance + _look.y * 5.0, 0.0)
	eye += Vector3(sin(_time * 61.0), cos(_time * 47.0), 0.0) * 0.07 * _shake
	lowpoly.camera.transform = Transform3D(Basis.IDENTITY, eye).looking_at(ground - back * 7.0 + Vector3(0.0, 1.0 - tan(tilt) * 7.0 + sim.lift * 0.5, 0.0))
	lowpoly.camera.fov = tuning.cam_fov + 14.0 * clampf(sim.speed / 46.0, 0.0, 1.0)


## Доска стоит под стопами модели: середина между ними, вдоль линии от стопы к стопе, верх по
## голеням. Упавший райдер доску теряет: она кувыркается рядом.
func _place_board(fallen: bool, line: float, tilt: float) -> void:
	var rig := hero as RigModel
	if fallen or rig == null or hero.pink:
		var beside := rider.global_transform * Vector3(0.9, 0.2, 0.3)
		board.global_transform = Transform3D(Basis.from_euler(Vector3(-tilt, line + _tumble * 6.0, 0.5)), beside) if fallen \
				else rider.global_transform * Transform3D(Basis.IDENTITY, Vector3(0.0, 0.03, 0.0))
		return
	var bones := rig.skeleton
	var left := bones.global_transform * bones.get_bone_global_pose(bones.find_bone("foot_l"))
	var right := bones.global_transform * bones.get_bone_global_pose(bones.find_bone("foot_r"))
	var along := (left.origin - right.origin).normalized()
	var up := ((left.basis.y + right.basis.y) / 2.0).normalized()
	var across := along.cross(up).normalized()
	up = across.cross(along).normalized()
	# Ось доски (её z) идёт от стопы к стопе; подошва на 8 см ниже кости стопы.
	board.global_transform = Transform3D(Basis(across, up, along), (left.origin + right.origin) / 2.0 - up * 0.105)


## Песок: борозда следа за доской и песчинки. След шире на канте, рвётся в прыжке и гаснет к
## хвосту; из-под канта летит струя вбок, за доской на скорости хвост.
func _sand(dt: float, at: Vector3, line: float, tilt: float, fallen: bool) -> void:
	var grounded := not sim.airborne and not fallen and sim.countdown <= 0.0
	var yaw := line - sim.heading
	var forward := Vector3(-sin(yaw), 0.0, -cos(yaw))
	var side := Vector3(-forward.z, 0.0, forward.x)
	if absf(sim.s - _trail_s) > 1.1:
		_trail_s = sim.s
		if grounded:
			var half := 0.17 + 0.4 * absf(sim.edge)
			# След идёт под доской, а не под серединой модели (плейтест 2026-11-13).
			var mid := course.world(sim.s, sim.x, sim.ride + 0.035)
			mid.x = board.global_position.x
			mid.z = board.global_position.z
			_trail.append([mid - side * half, mid + side * half, _trail.is_empty() or _trail[_trail.size() - 1].is_empty()])
		elif not _trail.is_empty() and not _trail[_trail.size() - 1].is_empty():
			_trail.append([])
		while _trail.size() > 110:
			_trail.pop_front()
		_trail_mesh.clear_surfaces()
		var quads := 0
		for i in range(1, _trail.size()):
			quads += 0 if _trail[i].is_empty() or _trail[i - 1].is_empty() else 1
		if quads > 0:
			_trail_mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
			for i in range(1, _trail.size()):
				if _trail[i].is_empty() or _trail[i - 1].is_empty():
					continue
				var a: Array = _trail[i - 1]
				var b: Array = _trail[i]
				var fade0 := float(i - 1) / _trail.size()
				var fade1 := float(i) / _trail.size()
				for item: Array in [[a[0], fade0], [b[0], fade1], [b[1], fade1], [a[0], fade0], [b[1], fade1], [a[1], fade0]]:
					_trail_mesh.surface_set_normal(Vector3.UP)
					_trail_mesh.surface_set_color(Color(0.3, 0.22, 0.12, 0.6 * float(item[1])))
					_trail_mesh.surface_add_vertex(item[0])
			_trail_mesh.surface_end()
	# Песчинки: струя из-под канта в сторону от дуги и хвост назад.
	var carve := absf(sim.edge) * clampf(sim.speed / 30.0, 0.0, 1.3) + (0.8 if sim.catch_left > 0.0 else 0.0)
	var spray := jets[0]
	spray.emitting = grounded and carve > 0.12
	var under := Vector3(board.global_position.x, at.y, board.global_position.z)
	spray.position = under + Vector3(0.0, 0.1, 0.0) - forward * 0.3
	spray.direction = (side * -signf(sim.edge) * 1.0 + Vector3.UP * 0.75 - forward * 0.3).normalized()
	spray.initial_velocity_max = 6.0 + sim.speed * 0.22
	var tail := jets[1]
	tail.emitting = grounded and sim.speed > 8.0
	tail.position = under + Vector3(0.0, 0.08, 0.0) - forward * 0.8
	tail.direction = (Vector3.UP * 0.55 - forward).normalized()
	tail.initial_velocity_max = 3.0 + sim.speed * 0.12


## Поза райдера: стойка боком с согнутыми коленями, присед ниже, руки для равновесия, в
## воздухе группировка.
func _pose(fallen: bool) -> void:
	if hero.pink:
		return
	var rig := hero as RigModel
	if rig == null:
		hero.walk(0.0, 0.0)
		return
	if fallen:
		rig.pose({&"arm_l": 2.4, &"arm_r": 2.0, &"fore_l": 0.4, &"fore_r": 0.6, &"leg_l": 0.5, &"leg_r": -0.2, &"shin_l": -0.9, &"shin_r": -0.4})
		return
	var low := 1.0 if sim.crouch else 0.0
	var air := 1.0 if sim.airborne else 0.0
	var load := sim.charge / tuning.charge_seconds
	var lean := sim.edge * (0.35 + 0.3 * sim.strain)
	# Сгиб коленей сглажен, и корпус опущен ровно на него: ступни стоят на доске.
	_bend = lerpf(_bend, 0.5 + low * 0.45 + air * 0.3 + load * 0.55, 0.3)
	var splay := 0.34
	var leg := (0.41 * cos(_bend) + 0.41 * cos(_bend * 0.75)) * cos(splay)
	hero.rotation = Vector3(0.0, -PI / 2.0, 0.0)
	hero.position = Vector3(-0.41 * (sin(_bend) - sin(_bend * 0.75)), 0.055 - (0.82 - leg), 0.0)
	rig.smooth = 40.0
	rig.pose({&"leg_l": Vector3(_bend, 0.0, -splay), &"leg_r": Vector3(_bend, 0.0, splay), &"shin_l": -_bend * 1.75, &"shin_r": -_bend * 1.75,
			&"foot_l": Vector3(_bend * 0.75, 0.0, splay), &"foot_r": Vector3(_bend * 0.75, 0.0, -splay),
			&"arm_l": Vector3(0.3 + low * 0.5, 0.0, -1.0 + low * 0.5 - lean - sim.strain * 0.5), &"arm_r": Vector3(0.3 + low * 0.5 + air * 0.9, 0.0, 1.0 - low * 0.5 - lean + sim.strain * 0.5),
			&"fore_l": 0.4 + low * 0.5, &"fore_r": 0.4 + low * 0.5 + air * 0.6})
	rig.joint(&"hips", Vector3(-0.15 - low * 0.25 - load * 0.2, 0.0, 0.0))
	rig.joint(&"spine", Vector3(-0.2 - low * 0.3 - air * 0.15 - load * 0.25, 0.25, lean))
	rig.joint(&"chest", Vector3(-0.1 - low * 0.15, 0.35, lean * 0.6))
	rig.joint(&"head", Vector3(0.3 + low * 0.3, 0.75, 0.0))


# --- HUD ---------------------------------------------------------------------------------------

func _draw_hud(canvas: CanvasItem) -> void:
	if sim == null:
		return
	var h := ThreedHud.begin(canvas, lowpoly)
	var view := lowpoly.view
	var mid := view / 2.0
	var total := course.gates.size()
	# Следующие ворота: метка над ними или стрелка, если они за кадром.
	if sim.next_gate < total and sim.countdown <= 0.0:
		var g := course.gates[sim.next_gate]
		var top := course.world(g.s, g.x, 3.6)
		var at := lowpoly.project(top)
		if not lowpoly.camera.is_position_behind(top) and at.x > 14.0 and at.x < view.x - 14.0:
			var bob := sin(_time * 7.0) * 1.2
			h.polygon(PackedVector2Array([at + Vector2(0.0, 5.0 + bob), at + Vector2(-5.0, -3.0 + bob), at + Vector2(5.0, -3.0 + bob)]), Color(0.0, 0.0, 0.0, 0.45))
			h.polygon(PackedVector2Array([at + Vector2(0.0, 3.6 + bob), at + Vector2(-3.8, -2.4 + bob), at + Vector2(3.8, -2.4 + bob)]), ThreedHud.GOLD)
		else:
			var side := 1.0 if at.x >= mid.x else -1.0
			var tip := Vector2(mid.x + side * (mid.x - 16.0), mid.y)
			h.polygon(PackedVector2Array([tip, tip + Vector2(-side * 9.0, -6.0), tip + Vector2(-side * 9.0, 6.0)]), ThreedHud.GOLD)
	# Ворота: слева сверху счёт и точки по порядку.
	h.panel(Rect2(10.0, 9.0, 96.0, 44.0), 7.0)
	h.text(Vector2(17.0, 17.0), "ВОРОТА", 5.2, ThreedHud.DIM, -1)
	h.text(Vector2(17.0, 30.5), str(sim.passed), 17.0, ThreedHud.GREEN if sim.passed >= sim.need() else ThreedHud.WHITE, -1)
	h.text(Vector2(99.0, 27.0), "из %d" % total, 6.5, ThreedHud.DIM, 1)
	h.text(Vector2(99.0, 35.5), "надо %d" % sim.need(), 5.4, ThreedHud.GOLD, 1)
	for i in total:
		var dot := Vector2(18.0 + i * (80.0 / maxf(total - 1, 1)), 46.0)
		var color := ThreedHud.FAINT
		if i < sim.marks.size():
			color = ThreedHud.GREEN if sim.marks[i] > 0 else ThreedHud.RED
		elif i == sim.next_gate:
			color = ThreedHud.WHITE
		h.circle(dot, 1.5, color)
	# Время справа сверху.
	h.panel(Rect2(view.x - 88.0, 9.0, 78.0, 36.0), 7.0)
	h.text(Vector2(view.x - 81.0, 17.0), "ВРЕМЯ", 5.2, ThreedHud.DIM, -1)
	h.text(Vector2(view.x - 81.0, 31.5), "%d:%04.1f" % [int(sim.time) / 60, fmod(sim.time, 60.0)], 15.0, ThreedHud.WHITE, -1)
	# Путь до пляжа сверху по центру: ворота засечками, трамплины треугольниками.
	var from := Vector2(mid.x - 84.0, 20.0)
	var span := 168.0
	h.panel(Rect2(from.x - 12.0, 11.0, span + 24.0, 18.0), 9.0)
	h.bar(from, from + Vector2(span, 0.0), ThreedHud.FAINT, 2.6)
	h.bar(from, from + Vector2(span * sim.progress(), 0.0), ThreedHud.GOLD, 2.6)
	for i in total:
		var tick := from + Vector2(span * course.gates[i].s / course.length, 0.0)
		var color := ThreedHud.DIM
		if i < sim.marks.size():
			color = ThreedHud.GREEN if sim.marks[i] > 0 else ThreedHud.RED
		h.line(tick + Vector2(0.0, -3.0), tick + Vector2(0.0, 3.0), color, 0.9)
	var knob := from + Vector2(span * sim.progress(), 0.0)
	h.circle(knob, 4.4, Color(0.0, 0.0, 0.0, 0.55))
	h.circle(knob, 3.4, ThreedHud.GOLD)
	# Скорость справа внизу: дуга, число, присед.
	var hub := Vector2(view.x - 46.0, view.y - 44.0)
	h.circle(hub, 37.0, Color(0.0, 0.0, 0.0, 0.25))
	h.circle(hub, 35.0, h.glass)
	h.arc(hub, 35.0, 0.0, TAU, h.edge, 0.6)
	var a0 := PI * 0.75
	var sweep := PI * 1.5
	h.arc(hub, 28.5, a0, a0 + sweep, ThreedHud.FAINT, 3.0)
	var fast := clampf(sim.speed / 50.0, 0.0, 1.0)
	h.arc(hub, 28.5, a0, a0 + sweep * maxf(fast, 0.01), ThreedHud.GOLD if not sim.crouch else ThreedHud.GREEN, 3.0)
	h.text(hub + Vector2(0.0, -3.0), "%d" % roundi(sim.speed * 3.6), 17.0)
	h.text(hub + Vector2(0.0, 10.5), "КМ/Ч", 4.4, ThreedHud.DIM)
	h.text(hub + Vector2(0.0, 21.0), "ПРИСЕД" if sim.crouch else "", 4.6, ThreedHud.GREEN)
	# Заряд прыжка: дуга под райдером, пока держат кнопку.
	if sim.charge > 0.0:
		var power := sim.charge / tuning.charge_seconds
		var c := Vector2(mid.x, view.y - 20.0)
		h.arc(c, 9.0, PI, TAU, Color(0.0, 0.0, 0.0, 0.4), 3.4)
		h.arc(c, 9.0, PI, PI + PI * maxf(power, 0.02), ThreedHud.GREEN if power >= 1.0 else ThreedHud.GOLD, 2.2)
	if _note_left > 0.0:
		h.text(Vector2(mid.x, mid.y - 46.0), _note, 11.0, Color(ThreedHud.GREEN if _note_good else ThreedHud.RED, minf(_note_left * 3.0, 1.0)), 0,
				Color(0.0, 0.0, 0.0, 0.55))
	if sim.fallen_left > 0.0:
		h.text(Vector2(mid.x, mid.y - 20.0), "УПАЛ", 16.0, ThreedHud.RED, 0, Color(0.0, 0.0, 0.0, 0.6))
	if sim.countdown > 0.0:
		h.text(Vector2(mid.x, mid.y - 30.0), str(ceili(sim.countdown)), 46.0, ThreedHud.WHITE, 0, Color(0.05, 0.07, 0.11, 0.8))
	h.end()
