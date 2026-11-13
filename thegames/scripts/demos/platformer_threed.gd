extends Demo
## Демка платформер × «продвинутые», каталог `docs/specs/demos_catalog.md`: «крюк-кошка» (#121,
## решение и приёмы сложности 2026-11-13, плейтест того же дня; образцы Bionic Commando,
## Spider-Man, Uncharted). Герой идёт по островам к маяку. Камера за спиной крутится мышью или
## правым стиком и сама доворачивает за ходом, если её не трогать; ход считается от камеры,
## герой поворачивается туда, куда бежит. A прыжок, B или левая кнопка мыши крюк. Пропасти
## трёх видов: простой прыжок, уступ (герой цепляется руками за край и забирается) и кольца
## на реях: зажал крюк рядом с кольцом (на нём горит отметка), герой повисает на одной руке и
## качается; отпустил, летит по касательной. В воздухе герой рулит. На островах стоит
## реквизит, сквозь него не пройти, на бочку и ящик можно запрыгнуть. Жизней три, вода снимает
## одну и возвращает на последний остров. Уровень из `HookLevelGen` по сиду записи. Правила и
## боты живут в `HookSim` (без окна, им же проверяются сто сидов); демка ведёт его шагами по
## 1/60 с, рисует и озвучивает его события.
##
## Общие баги (#44) и баг технологии `camera_clip` живут в `Demo` и `ThreedScreen`, демка только
## зовёт хуки. Баги жанра и баланса для этой демки включит #126.

const PLACEHOLDER_SLOTS: Array[String] = ["hero", "prop", "finish"]
const MELODY := [0, 4, 7, 12, 11, 7, 4, null, 5, 9, 12, 16, 14, 12, 9, null,
	0, 4, 7, 12, 14, 12, 11, 7, 5, 4, 2, 4, 5, 7, 0, null]
const BASS := [-12, -12, -5, -5, -7, -7, -3, -3, -12, -12, -5, -5, -7, -7, -5, -5]
## Высота поднятой кисти над ступнями и вынос плеча.
const GRIP := 2.02
const SHOULDER := 0.2
const SEGMENTS := 48

var tuning: PlatformerThreedTuning
var level: HookLevel
var sim: HookSim
var hero: LowpolyModel
var ring_nodes: Array[Node3D] = []
var rope: MeshInstance3D
## Рукоять крюка в правой кисти и сам крюк: в покое на рукояти, на зацепе висит на кольце.
var handle: Node3D
var claw: Node3D
var hand: BoneAttachment3D

var cam_yaw := 0.0
var cam_pitch := 0.3
var _focus := Vector3.ZERO
var _look_idle := 9.0
var _time := 0.0
var _walk := 0.0
var _want_jump := false
var _hurt := 0.0
var _stop_left := 0.0
## Тело на верёвке: куда смотрит его верх и скорость этого направления (пружина за верёвкой).
var _hang := Vector3.UP
var _hang_vel := Vector3.ZERO
var _hooked := 0.0
var _music: AudioStreamPlayer
var _sfx := {}


func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _on_start() -> void:
	tuning = PlatformerThreedTuning.load_default()
	level = HookLevelGen.generate(record.seed if record != null else 1, null, tuning)
	if has_bug(&"unreachable_coins"):
		# Недостижимая цель: кольца последней пропасти висят выше верёвки.
		for r in level.rings:
			if r.gap == level.gaps.size() - 1:
				r.pos.y += bug_param(&"unreachable_coins", &"hook_ring_rise", 7.0)
	sim = HookSim.create(level, tuning)
	if has_bug(&"wild_physics"):
		sim.jump_mult = bug_param(&"wild_physics", &"hook_jump_mult", 1.7)
		sim.swing_mult = bug_param(&"wild_physics", &"hook_swing_mult", 1.6)
	if has_bug(&"sneeze_enemies"):
		sim.ring_hold = bug_param(&"sneeze_enemies", &"hook_ring_hold", 0.7)
	lowpoly_screen(_draw_hud)
	look_start()
	_build_world()
	_setup_audio()
	cam_yaw = sim.facing
	cam_pitch = tuning.cam_pitch
	_focus = sim.pos + Vector3(0.0, tuning.cam_look, 0.0)
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
	_sfx["grab"] = Sfx.player(Sfx.thud(0.06, 0.3))
	_sfx["land"] = Sfx.player(Sfx.thud(0.1, 0.4))
	_sfx["splash"] = Sfx.player(Sfx.thud(0.3, 0.6))
	_sfx["finish"] = Sfx.player(Sfx.blip(880.0, 0.5, 0.4, 5.0))
	for p in _sfx.values():
		(p as AudioStreamPlayer).volume_db = tuning.sfx_db if not quiet else -80.0
		add_child(p)


func _play(name: String) -> void:
	bug_play(_sfx[name])


# --- Мир ---------------------------------------------------------------------------------------

func _cylinder(at: Vector3, radius: float, height: float, material: Material, parent: Node3D = null) -> MeshInstance3D:
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = 12
	mesh.rings = 1
	mesh.material = material
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.position = at
	(parent if parent != null else lowpoly.world).add_child(node)
	return node


func _commit(tool: SurfaceTool, material: Material, smooth: bool) -> void:
	if smooth:
		tool.generate_normals()
	tool.generate_tangents()
	var mesh := tool.commit()
	mesh.surface_set_material(0, material)
	var node := MeshInstance3D.new()
	node.mesh = mesh
	lowpoly.world.add_child(node)


## Остров: плоский верх по неровному краю (песок, у больших в середине трава) и скала вниз
## под воду, с выступами и сужением.
func _build_islet(it: HookLevel.Islet, rng: RandomNumberGenerator, water: float) -> void:
	var top := SurfaceTool.new()
	top.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rim: Array[Vector3] = []
	for k in SEGMENTS:
		var a := TAU * k / SEGMENTS
		rim.append(it.pos + Vector3(cos(a), 0.0, sin(a)) * it.radius_at(a))
	for k in SEGMENTS:
		for p: Vector3 in [it.pos, rim[k], rim[(k + 1) % SEGMENTS]]:
			top.set_normal(Vector3.UP)
			top.set_uv(Vector2(p.x, p.z) / 3.2)
			top.add_vertex(p)
	_commit(top, lowpoly.tex_material(lowpoly_texture("sand")), false)
	if it.radius > 3.0:
		# Трава: пятно в середине со своим неровным краем, чуть выше песка.
		var grass := SurfaceTool.new()
		grass.begin(Mesh.PRIMITIVE_TRIANGLES)
		var ph := rng.randf_range(0.0, TAU)
		var patch: Array[Vector3] = []
		for k in SEGMENTS:
			var a := TAU * k / SEGMENTS
			var r := it.radius_at(a) * (0.66 + 0.07 * sin(4.0 * a + ph) + 0.05 * sin(7.0 * a + ph * 2.0))
			patch.append(it.pos + Vector3(cos(a) * r, 0.035, sin(a) * r))
		for k in SEGMENTS:
			for p: Vector3 in [it.pos + Vector3(0.0, 0.035, 0.0), patch[k], patch[(k + 1) % SEGMENTS]]:
				grass.set_normal(Vector3.UP)
				grass.set_uv(Vector2(p.x, p.z) / 2.6)
				grass.add_vertex(p)
		_commit(grass, lowpoly.tex_material(lowpoly_texture("grass")), false)
	# Скала: пояса вниз, у каждого своя неровность.
	var tall := it.pos.y - water
	var belts: Array[Vector3] = [Vector3(0.0, 1.0, 0.0), Vector3(0.4, 1.03, 0.02), Vector3(tall * 0.5, 0.93, 0.07), Vector3(tall, 0.8, 0.1),
			Vector3(tall + 7.0, 0.62, 0.12)]
	var phases := [rng.randf_range(0.0, TAU), rng.randf_range(0.0, TAU), rng.randf_range(0.0, TAU)]
	var side := SurfaceTool.new()
	side.begin(Mesh.PRIMITIVE_TRIANGLES)
	var around := maxf(roundf(TAU * it.radius / 3.0), 2.0)
	var grid: Array = []
	for b in belts.size():
		var row: Array[Vector3] = []
		for k in SEGMENTS + 1:
			var a := TAU * (k % SEGMENTS) / SEGMENTS
			var bump := 1.0 + belts[b].z * (sin(6.0 * a + phases[0] + b) + 0.6 * sin(11.0 * a + phases[1] - b * 2.0) + 0.4 * sin(17.0 * a + phases[2]))
			var r := it.radius_at(a) * belts[b].y * bump
			row.append(Vector3(it.pos.x + cos(a) * r, it.pos.y - belts[b].x, it.pos.z + sin(a) * r))
		grid.append(row)
	for b in belts.size() - 1:
		for k in SEGMENTS:
			var ua: Vector3 = grid[b][k]
			var ub: Vector3 = grid[b][k + 1]
			var la: Vector3 = grid[b + 1][k]
			var lb: Vector3 = grid[b + 1][k + 1]
			var u0 := around * k / SEGMENTS
			var u1 := around * (k + 1) / SEGMENTS
			var v0 := belts[b].x / 3.0
			var v1 := belts[b + 1].x / 3.0
			for item: Array in [[ua, u0, v0], [la, u0, v1], [lb, u1, v1], [ua, u0, v0], [lb, u1, v1], [ub, u1, v0]]:
				side.set_uv(Vector2(item[1], item[2]))
				side.add_vertex(item[0])
	_commit(side, lowpoly.tex_material(lowpoly_texture("cliff")), true)


func _metal(color: Color, glow := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.metallic = 0.75
	m.roughness = 0.34
	if glow > 0.0:
		m.emission_enabled = true
		m.emission = color * glow
	return m


func _build_world() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed if record != null else 1, ":hook-look"))
	var water := sim.water
	var mid := (level.islets[0].pos + level.islets[level.islets.size() - 1].pos) / 2.0
	(lowpoly as ThreedScreen).add_water(Vector3(mid.x, water, mid.z), 900.0)
	for it in level.islets:
		_build_islet(it, rng, water)
	for p in level.props:
		if p.name == "palm" and not is_pink("prop"):
			(lowpoly as ThreedScreen).add_palm(lowpoly_set.model("palm", true).texture, p.pos, p.yaw, p.height * rng.randf_range(0.9, 1.15), rng)
			continue
		var tower := p.name == "lighthouse"
		var prop := spawn_model("finish" if tower else "prop", p.name)
		prop.position = p.pos
		prop.rotation.y = p.yaw
	# Кольца на реях: мачта стоит в воде сбоку от пути, рея над пропастью, кольцо под ней.
	var gold := _metal(Color(0.93, 0.72, 0.22), 0.45)
	var wood := lowpoly.tex_material(lowpoly_texture("planks"), {"uv_scale": Vector2(1.0, 4.0)})
	var beam_wood := lowpoly.tex_material(lowpoly_texture("planks"), {"uv_scale": Vector2(2.0, 1.0)})
	for i in level.rings.size():
		var r := level.rings[i]
		var dir := level.gaps[r.gap].dir
		var side := 1.0 if i % 2 == 0 else -1.0
		var foot := r.pos + Vector3(-dir.y, 0.0, dir.x) * side * 3.0
		var top := r.pos.y + r.amp + 1.5
		_cylinder(Vector3(foot.x, (water - 6.0 + top) / 2.0, foot.z), 0.16, top - water + 6.0, wood)
		var node := Node3D.new()
		node.position = r.pos
		node.rotation.y = atan2(-dir.x, -dir.y)
		lowpoly.world.add_child(node)
		var yard := MeshInstance3D.new()
		var beam := BoxMesh.new()
		beam.size = Vector3(4.2, 0.14, 0.14)
		beam.material = beam_wood
		yard.mesh = beam
		yard.position = Vector3(side * 1.25, 1.0, 0.0)
		node.add_child(yard)
		var chain := MeshInstance3D.new()
		var link := BoxMesh.new()
		link.size = Vector3(0.05, 0.6, 0.05)
		link.material = gold
		chain.mesh = link
		chain.position = Vector3(0.0, 0.7, 0.0)
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
	hero = spawn_model("hero", "hero")
	_build_hook()


## Крюк-кошка: рукоять в правой кисти, крюк с тремя лапами и верёвка между ними.
func _build_hook() -> void:
	var iron := _metal(Color(0.34, 0.36, 0.4))
	var grip := lowpoly.tex_material(lowpoly_texture("planks"), {"tint": Color(0.6, 0.45, 0.32)})
	handle = Node3D.new()
	_cylinder(Vector3.ZERO, 0.03, 0.2, grip, handle)
	_cylinder(Vector3(0.0, 0.11, 0.0), 0.045, 0.03, iron, handle)
	claw = Node3D.new()
	_cylinder(Vector3(0.0, -0.09, 0.0), 0.022, 0.2, iron, claw)
	for k in 3:
		var arm := Node3D.new()
		arm.rotation.y = TAU * k / 3.0
		claw.add_child(arm)
		var out := _cylinder(Vector3(0.07, 0.02, 0.0), 0.018, 0.17, iron, arm)
		out.rotation.z = -1.05
		var tip := _cylinder(Vector3(0.14, -0.03, 0.0), 0.016, 0.11, iron, arm)
		tip.rotation.z = 0.25
	lowpoly.world.add_child(claw)
	var rig := hero as RigModel
	if rig != null and rig.has_joint(&"hand_r"):
		hand = BoneAttachment3D.new()
		rig.skeleton.add_child(hand)
		hand.bone_name = "hand_r"
		hand.add_child(handle)
		handle.position = Vector3(0.0, -0.06, 0.0)
		handle.rotation.x = PI / 2.0
	else:
		hero.add_child(handle)
		handle.position = Vector3(SHOULDER, 1.0, 0.0)
	rope = MeshInstance3D.new()
	var line := CylinderMesh.new()
	line.top_radius = 0.022
	line.bottom_radius = 0.022
	line.height = 1.0
	line.radial_segments = 6
	line.material = lowpoly.tex_material(lowpoly_texture("sail"), {"tint": Color(0.8, 0.68, 0.48)})
	rope.mesh = line
	rope.visible = false
	lowpoly.world.add_child(rope)


# --- Шаг -------------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	_hurt = maxf(_hurt - delta, 0.0)
	if not bot_driven() and running and GameInput.a_just_pressed():
		bug_press(func() -> void: _want_jump = true)
	_turn_camera(delta)
	# Фризы в движении с догоном времени (`Demo.bug_frame`).
	bug_frame(delta, sim.mode != HookSim.Mode.DOWN and sim.phase == HookSim.Phase.PLAY, _step)


## Камера: мышь и правый стик крутят её вокруг героя; если её не трогают, она сама
## доворачивает за ходом героя (на верёвке за курсом пропасти).
func _turn_camera(delta: float) -> void:
	var turn := look_take(delta)
	if turn.length() > 0.0004:
		_look_idle = 0.0
		cam_yaw = wrapf(cam_yaw - turn.x, -PI, PI)
		cam_pitch = clampf(cam_pitch + turn.y, tuning.cam_pitch_min, tuning.cam_pitch_max)
		return
	_look_idle += delta
	if _look_idle < tuning.cam_auto_delay or sim.phase != HookSim.Phase.PLAY:
		return
	var flat := Vector2(sim.vel.x, sim.vel.z)
	var want := cam_yaw
	var pull := 0.0
	if sim.mode == HookSim.Mode.SWING:
		var dir := level.gaps[mini(sim.ground, level.gaps.size() - 1)].dir
		want = atan2(-dir.x, -dir.y)
		pull = 1.0
	elif flat.length() > 1.5:
		want = atan2(-flat.x, -flat.y)
		# Бегущего на камеру она не разворачивает.
		pull = clampf(flat.length() / tuning.run_speed, 0.0, 1.0) if absf(angle_difference(cam_yaw, want)) < 2.3 else 0.0
	cam_yaw = lerp_angle(cam_yaw, want, (1.0 - exp(-tuning.cam_auto * delta)) * pull)
	cam_pitch = lerpf(cam_pitch, tuning.cam_pitch, (1.0 - exp(-0.8 * delta)) * pull)


func _step(dt: float) -> void:
	_time += dt
	bug_input_tick()
	var hold := minf(_stop_left, dt)
	_stop_left -= hold
	var left := dt - hold
	while left > 0.0001 and running:
		var h := minf(left, HookSim.DT)
		left -= h
		var move := Vector2.ZERO
		var jump := false
		var hook := false
		if bot_driven():
			sim.bot(active_bot_mode())
			move = sim.bot_move
			jump = sim.bot_jump
			hook = sim.bot_hook
		else:
			# Ход от камеры, с багом управления из прошлого (`Demo.bug_axis`).
			var axis := bug_axis(GameInput.axis())
			var forward := Vector2(-sin(cam_yaw), -cos(cam_yaw))
			move = forward * -axis.y + Vector2(-forward.y, forward.x) * axis.x
			sim.aim = forward
			jump = _want_jump
			hook = GameInput.b_pressed() or look_fire()
			_want_jump = false
		sim.step(h, move, jump, hook)
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
			_hooked = 0.0
			_hang = (ring_nodes[int(ev[1])].position - sim.pos).normalized()
			_hang_vel = Vector3.ZERO
		&"snap":
			_play("land")
			ring_nodes[int(ev[1])].visible = false
		&"release":
			_play("release")
		&"grab":
			_play("grab")
		&"land", &"climb":
			_play("land")
		&"splash":
			_play("splash")
			_hurt = 0.6
			_stop_left = tuning.hit_stop
			if AutoTest.enabled and not embedded:
				AutoTest.note("platformer threed: в воде на %.1f с, остров %d, жизней %d" % [sim.time, sim.islet, sim.lives])
		&"finish":
			end_demo(true)
		&"dead", &"timeout":
			end_demo(false)


func _on_end(goal: bool) -> void:
	_music.stop()
	if goal:
		_play("finish")
	if AutoTest.enabled and not embedded:
		AutoTest.note("platformer threed: %s за %.1f с, жизней %d, прыжков %d, уступов %d, зацепов %d, падений %d, остров %d из %d" % [
				"дошёл" if goal else "не дошёл", sim.time, sim.lives, sim.jumps, sim.climbs, sim.hooks, sim.falls, sim.islet, level.gaps.size()])


func _result_caption() -> String:
	return "%d с · зацепов %d · падений %d" % [int(round(sim.time)), sim.hooks, sim.falls]


# --- Картинка --------------------------------------------------------------------------------

func _sync(dt: float) -> void:
	for i in ring_nodes.size():
		ring_nodes[i].position = level.ring_pos(i, sim.time)
	hero.visible = sim.mode != HookSim.Mode.DOWN
	var swinging := sim.mode == HookSim.Mode.SWING
	var forward := Vector3(-sin(sim.facing), 0.0, -cos(sim.facing))
	if swinging:
		# Тело висит на правой руке и догоняет верёвку пружиной: отстаёт на разгоне, доколебывается.
		var top := ring_nodes[sim.ring].position - Vector3(0.0, 0.4, 0.0)
		var up_rope := (top - sim.pos).normalized()
		if dt > 0.0:
			var h := minf(dt, 0.05)
			_hang_vel += ((up_rope - _hang) * 55.0 - _hang_vel * 6.0) * h
			_hang = (_hang + _hang_vel * h).normalized()
		var back := -(forward - _hang * forward.dot(_hang)).normalized()
		var right := _hang.cross(back).normalized()
		hero.basis = Basis(right, _hang, right.cross(_hang).normalized())
		hero.position = sim.pos + up_rope * GRIP - _hang * GRIP - right * SHOULDER
		_hooked += dt
	else:
		hero.basis = Basis.from_euler(Vector3(0.0, sim.facing, 0.0))
		hero.position = sim.pos
	_pose(dt, forward)
	# Крюк: в покое на рукояти, на зацепе летит к кольцу и висит на нём; верёвка от кисти.
	var palm := handle.global_position if handle.is_inside_tree() else sim.pos + Vector3(0.0, 1.0, 0.0)
	rope.visible = swinging
	claw.visible = hero.visible
	if swinging:
		var top := ring_nodes[sim.ring].position - Vector3(0.0, 0.36, 0.0)
		var tip := palm.lerp(top, clampf(_hooked / 0.07, 0.0, 1.0))
		claw.global_transform = Transform3D(Basis.IDENTITY, tip - Vector3(0.0, 0.02, 0.0))
		var span := tip - palm
		rope.position = (palm + tip) / 2.0
		if span.length() > 0.05:
			var up := span.normalized()
			var side := up.cross(Vector3.FORWARD if absf(up.dot(Vector3.FORWARD)) < 0.95 else Vector3.RIGHT).normalized()
			rope.basis = Basis(side, up * span.length(), side.cross(up).normalized())
	elif handle.is_inside_tree():
		claw.global_transform = handle.global_transform * Transform3D(Basis.IDENTITY, Vector3(0.0, 0.2, 0.0))
	# Камера на орбите вокруг героя.
	var want := Vector3(sim.pos.x, maxf(sim.pos.y, sim.water + 0.5), sim.pos.z) + Vector3(0.0, tuning.cam_look, 0.0)
	_focus = _focus.lerp(want, 1.0 - exp(-tuning.cam_follow * dt)) if dt > 0.0 else want
	var eye := _focus + Vector3(sin(cam_yaw) * cos(cam_pitch), sin(cam_pitch), cos(cam_yaw) * cos(cam_pitch)) * tuning.cam_distance
	eye.y = maxf(eye.y, sim.water + 0.9)
	lowpoly.camera.transform = Transform3D(Basis.IDENTITY, eye).looking_at(_focus + Vector3(0.0, 0.4, 0.0))


## Поза героя: бег, полёт, подъём на уступ, вис на одной руке.
func _pose(dt: float, forward: Vector3) -> void:
	var flat := Vector2(sim.vel.x, sim.vel.z).length()
	var pace := clampf(flat / tuning.run_speed, 0.0, 1.0)
	if hero.pink:
		return
	var rig := hero as RigModel
	match sim.mode:
		HookSim.Mode.GROUND:
			# Шаг реже, чем раньше: около трёх шагов в секунду на полном бегу.
			_walk += dt * (4.0 + 5.5 * pace) * (1.0 if pace > 0.05 else 0.0)
			hero.walk(_walk if pace > 0.05 else 0.0, 0.72 * pace)
			if rig != null:
				rig.joint(&"hips", Vector3(-0.1 * pace, 0.0, 0.0))
		HookSim.Mode.SWING:
			if rig == null:
				hero.walk(0.0, 0.0)
				return
			# Насколько тело отстало от верёвки вперёд-назад и вбок: ноги и свободная рука
			# отстают сильнее, корпус гнётся.
			var top := ring_nodes[sim.ring].position - sim.pos
			var lag := top.normalized() - _hang
			var along := clampf(lag.dot(forward) * 4.0 + _hang_vel.dot(forward) * 0.12, -1.0, 1.0)
			var across := clampf(lag.dot(hero.basis.x) * 4.0, -0.7, 0.7)
			rig.pose({&"arm_r": Vector3(3.05, 0.0, 0.12), &"fore_r": 0.06, &"hand_r": 0.0,
					&"arm_l": Vector3(0.15 - along * 0.5, 0.0, -0.08 - absf(across) * 0.4), &"fore_l": 0.35 + absf(along) * 0.3,
					&"leg_l": Vector3(0.95 - along * 0.9, 0.0, -across * 0.6), &"leg_r": Vector3(0.6 - along * 0.75, 0.0, -across * 0.6),
					&"shin_l": -1.45 - absf(along) * 0.25, &"shin_r": -1.1 - absf(along) * 0.25, &"foot_l": 0.45, &"foot_r": 0.4})
			rig.joint(&"hips", Vector3(-along * 0.2, 0.0, 0.0))
			rig.joint(&"spine", Vector3(-along * 0.3, 0.15, across * 0.3))
			rig.joint(&"chest", Vector3(-along * 0.2, 0.2, across * 0.25 - 0.1))
			rig.joint(&"head", Vector3(-0.35 + along * 0.2, -0.2, 0.0))
		HookSim.Mode.CLIMB:
			if rig == null:
				hero.walk(1.2, 0.5)
				return
			var k := clampf(1.0 - sim.climb_left / tuning.climb_seconds, 0.0, 1.0)
			var arms := lerpf(2.9, 0.5, smoothstep(0.25, 0.9, k))
			rig.pose({&"arm_l": arms, &"arm_r": arms, &"fore_l": 0.3 + sin(k * PI) * 1.2, &"fore_r": 0.3 + sin(k * PI) * 1.2,
					&"leg_l": 0.2 + sin(k * PI) * 1.2, &"leg_r": 0.1, &"shin_l": -0.4 - sin(k * PI) * 1.3, &"shin_r": -0.3,
					&"foot_l": 0.2, &"foot_r": 0.3})
			rig.joint(&"hips", Vector3.ZERO)
			rig.joint(&"spine", Vector3(-0.2 * sin(k * PI), 0.0, 0.0))
			rig.joint(&"chest", Vector3.ZERO)
			rig.joint(&"head", Vector3(-0.3 * (1.0 - k), 0.0, 0.0))
		_:
			if rig == null:
				hero.walk(1.2, 0.5)
				return
			# Группировка: колени к груди, корпус вперёд, руки перед собой; на взлёте чуть раскрыт.
			var rise := clampf(sim.vel.y / 8.0, -1.0, 1.0)
			var open := maxf(rise, 0.0) * 0.35
			rig.pose({&"arm_l": Vector3(0.8 + open, 0.0, -0.25), &"arm_r": Vector3(1.0 + open, 0.0, 0.25), &"fore_l": 1.1, &"fore_r": 1.0,
					&"leg_l": 1.25 - open, &"leg_r": 0.95 - open, &"shin_l": -1.75 + open, &"shin_r": -1.5 + open, &"foot_l": 0.35, &"foot_r": 0.3})
			rig.joint(&"hips", Vector3(-0.18, 0.0, 0.0))
			rig.joint(&"spine", Vector3(-0.28, 0.0, 0.0))
			rig.joint(&"chest", Vector3(-0.16, 0.0, 0.0))
			rig.joint(&"head", Vector3(0.12, 0.0, 0.0))


# --- HUD: в полном разрешении, плашки тёмного стекла (плейтест 2026-11-13) --------------------

func _draw_hud(canvas: CanvasItem) -> void:
	if sim == null:
		return
	var h := ThreedHud.begin(canvas, lowpoly)
	var view := lowpoly.view
	# Отметка на кольце, до которого достаёт крюк.
	if sim.phase == HookSim.Phase.PLAY and (sim.mode == HookSim.Mode.GROUND or sim.mode == HookSim.Mode.AIR):
		var i := sim.target()
		if i >= 0 and not lowpoly.camera.is_position_behind(ring_nodes[i].position):
			var at := lowpoly.project(ring_nodes[i].position)
			var size := 9.0 + sin(_time * 9.0) * 1.2
			h.arc(at, size + 0.6, 0.0, TAU, Color(0.0, 0.0, 0.0, 0.45), 2.4)
			for k in 4:
				h.arc(at, size, TAU * k / 4.0 + _time * 1.5, TAU * k / 4.0 + _time * 1.5 + 1.1, ThreedHud.GOLD, 1.4)
	if _hurt > 0.0:
		h.rect(Rect2(Vector2.ZERO, view), Color(0.75, 0.9, 1.0, _hurt * 0.55))
	# Жизни слева сверху.
	h.panel(Rect2(10.0, 9.0, 22.0 + tuning.lives * 17.0, 26.0), 7.0)
	for i in tuning.lives:
		var c := Vector2(29.0 + i * 17.0, 21.5)
		var alive := i < sim.lives
		h.heart(c + Vector2(0.0, 0.7), 7.0, Color(0.0, 0.0, 0.0, 0.4))
		h.heart(c, 6.2, ThreedHud.RED if alive else ThreedHud.FAINT)
		if alive:
			h.circle(c + Vector2(-2.4, -2.5), 1.2, Color(1.0, 1.0, 1.0, 0.75))
	# Время справа сверху.
	h.panel(Rect2(view.x - 76.0, 9.0, 66.0, 26.0), 7.0)
	h.text(Vector2(view.x - 43.0, 22.0), "%d:%04.1f" % [int(sim.time) / 60, fmod(sim.time, 60.0)], 11.5)
	# Путь до маяка сверху по центру: острова точками (камни мельче), герой бегунком.
	var from := Vector2(view.x / 2.0 - 92.0, 22.0)
	var span := 184.0
	h.panel(Rect2(from.x - 12.0, 13.0, span + 24.0, 18.0), 9.0)
	h.bar(from, from + Vector2(span, 0.0), ThreedHud.FAINT, 2.6)
	var done := span * sim.progress()
	h.bar(from, from + Vector2(done, 0.0), ThreedHud.GOLD, 2.6)
	var n := level.gaps.size()
	for i in level.islets.size():
		var dot := from + Vector2(span * i / n, 0.0)
		var big := level.islets[i].radius > 2.2
		h.circle(dot, 2.3 if big else 1.4, ThreedHud.WHITE if i <= sim.islet else ThreedHud.DIM)
	var knob := from + Vector2(done, 0.0)
	h.circle(knob, 4.4, Color(0.0, 0.0, 0.0, 0.55))
	h.circle(knob, 3.4, ThreedHud.GOLD)
	h.circle(knob + Vector2(-0.9, -0.9), 1.1, Color(1.0, 1.0, 1.0, 0.7))
	if sim.phase == HookSim.Phase.COUNTDOWN:
		h.text(Vector2(view.x / 2.0, view.y / 2.0 - 30.0), str(ceili(sim.countdown)), 46.0, ThreedHud.WHITE, 0, Color(0.05, 0.07, 0.11, 0.8))
	h.end()
