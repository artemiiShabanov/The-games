extends Demo
## Демка гонки × «продвинутые», каталог `docs/specs/demos_catalog.md`: «спринт» (#122, решение
## и приёмы сложности 2026-11-13; образцы Gran Turismo, Colin McRae Rally, DiRT). Заезд из
## точки в точку по острову против трёх соперников, итог это место. Влево и вправо руль,
## вверх (или A) газ, вниз (или B) тормоз и задний ход; мышь и правый стик дают оглядеться,
## камера возвращается сама. Физика заметно честнее, чем у кольца с дрифтом: в поворот надо
## входить, оттормозившись, газ в повороте выносит наружу, рыхлый песок и мокрый настил
## держат хуже, на гребне машина легче, передачи переключаются сами с провалом тяги. Трасса
## из `SprintTrackGen` по сиду записи; правила, соперники и боты живут в `SprintSim` (без
## окна, им же проверяются сто сидов), демка ведёт его шагами по 1/60 с, рисует и озвучивает.
##
## Общие баги (#44) и баг технологии `camera_clip` живут в `Demo` и `ThreedScreen`, демка только
## зовёт хуки. Баги жанра и баланса для этой демки включит #126.

const PLACEHOLDER_SLOTS: Array[String] = ["hero", "rival", "prop", "finish"]
const MELODY := [0, null, 7, 5, 3, null, 5, 7, 10, null, 7, 5, 3, 5, 0, null,
	0, null, 7, 5, 3, null, 5, 7, 12, 10, 7, 5, 3, 2, 0, null]
const BASS := [-12, -12, -12, -5, -9, -9, -9, -5, -14, -14, -14, -7, -12, -12, -10, -10]
const SCALE := 1.25
const WHEEL := 0.32 * SCALE
const BEACH := 15.0
const CURB := 0.55
const PUFFS := 28

var tuning: RacingThreedTuning
var track: SprintTrack
var sim: SprintSim
var water_y := 0.0
var car_nodes: Array[Node3D] = []
var car_models: Array[LowpolyModel] = []

var _time := 0.0
var _stop_left := 0.0
var _flash := 0.0
var _shake := 0.0
var _cam_yaw := 0.0
var _look := Vector2.ZERO
var _look_idle := 9.0
var _shift_blink := 0.0
var _revs := 0.0
var _map := PackedVector2Array()
var _map_origin := Vector2.ZERO
var _map_scale := 1.0
var _puffs: Array[MeshInstance3D] = []
var _puff_life: Array[float] = []
var _puff_next := 0
var _puff_wait := 0.0
var _music: AudioStreamPlayer
var _engine: AudioStreamPlayer
var _sfx := {}


func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _on_start() -> void:
	tuning = RacingThreedTuning.load_default()
	track = SprintTrackGen.generate(record.seed if record != null else 1, null, tuning)
	sim = SprintSim.create(track, tuning)
	if has_bug(&"wild_physics"):
		sim.grip_mult = bug_param(&"wild_physics", &"sprint_grip_mult", 0.45)
		sim.rival_mult = bug_param(&"wild_physics", &"sprint_rival_mult", 1.15)
	sim.walls_open = has_bug(&"through_walls")
	if has_bug(&"sneeze_enemies"):
		sim.sneeze = true
		sim.sneeze_seconds = bug_param(&"sneeze_enemies", &"off_track_s", 2.5)
	if has_bug(&"unreachable_coins"):
		sim.goal_extra = bug_param(&"unreachable_coins", &"sprint_goal_extra", 900.0)
	lowpoly_screen(_draw_hud)
	look_start()
	_build_world()
	_build_puffs()
	_setup_audio()
	_cam_yaw = sim.player().yaw
	_sync(0.0)


func _setup_audio() -> void:
	var quiet := embedded
	_music = Sfx.music(Sfx.tracker_loop(MELODY, BASS, 148.0), tuning.music_db if not quiet else -80.0)
	add_child(_music)
	bug_music = _music
	if not quiet:
		_music.play()
	# Мотор: короткая петля из двух гармоник, высота идёт за оборотами.
	var samples := PackedFloat32Array()
	var period := Sfx.MIX_RATE / 90
	for i in period * 8:
		var k := float(i) / period
		samples.append(0.45 * (fposmod(k, 1.0) * 2.0 - 1.0) + 0.3 * sin(TAU * k * 0.5) + 0.12 * sin(TAU * k * 3.0))
	var loop := Sfx._wav(samples)
	loop.loop_mode = AudioStreamWAV.LOOP_FORWARD
	loop.loop_end = samples.size()
	_engine = Sfx.player(loop, tuning.engine_db if not quiet else -80.0)
	add_child(_engine)
	if not quiet:
		_engine.play()
	_sfx["go"] = Sfx.player(Sfx.blip(880.0, 0.3, 0.4, 6.0))
	_sfx["shift"] = Sfx.player(Sfx.thud(0.05, 0.3))
	_sfx["wall"] = Sfx.player(Sfx.thud(0.14, 0.45))
	_sfx["crash"] = Sfx.player(Sfx.thud(0.3, 0.7))
	_sfx["hit"] = Sfx.player(Sfx.thud(0.1, 0.4))
	_sfx["finish"] = Sfx.player(Sfx.blip(880.0, 0.5, 0.4, 5.0))
	for p in _sfx.values():
		(p as AudioStreamPlayer).volume_db = tuning.sfx_db if not quiet else -80.0
		add_child(p)


func _play(name: String) -> void:
	bug_play(_sfx[name])


# --- Мир ---------------------------------------------------------------------------------------

func _tool() -> SurfaceTool:
	var tool := SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	return tool


## Четырёхугольник a-b-c-d (a и b на ближнем сечении, c и d на дальнем, a и d слева по ходу).
func _quad(tool: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, ua: Vector2, ub: Vector2, uc: Vector2, ud: Vector2) -> void:
	for item: Array in [[a, ua], [d, ud], [c, uc], [a, ua], [c, uc], [b, ub]]:
		tool.set_uv(item[1])
		tool.add_vertex(item[0])


func _commit(tool: SurfaceTool, tex: String, extra := {}) -> void:
	tool.generate_normals()
	tool.generate_tangents()
	var mesh := tool.commit()
	if mesh.get_surface_count() == 0:
		return
	mesh.surface_set_material(0, lowpoly.tex_material(lowpoly_texture(tex), extra))
	var node := MeshInstance3D.new()
	node.mesh = mesh
	lowpoly.world.add_child(node)


## Сечение трассы в `s`: точки слева направо. Дорога, обочина, бортик, пляж до воды; на
## сужении обочины нет, за дорогой обрыв.
func _section(s: float, rng_shift: float) -> Dictionary:
	var half := track.half(s)
	var verge := tuning.verge * track.shoulder(s)
	var out := {}
	for side: float in [-1.0, 1.0]:
		var key := "l" if side < 0.0 else "r"
		out[key + "0"] = track.world(s, side * half)
		out[key + "1"] = track.world(s, side * (half + verge), -0.12 * track.shoulder(s))
		out[key + "2"] = track.world(s, side * (half + verge), CURB * track.shoulder(s))
		out[key + "3"] = track.world(s, side * (half + verge + 0.7), CURB * track.shoulder(s))
		var beach := track.world(s, side * (half + verge + 0.7 + BEACH * track.shoulder(s) * (1.0 + 0.25 * sin(s * 0.05 + rng_shift + side))
				+ 1.2 * (1.0 - track.shoulder(s))))
		beach.y = water_y - 1.2
		out[key + "4"] = beach
	return out


func _build_world() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed if record != null else 1, ":sprint-look"))
	var low := INF
	for h in track.heights:
		low = minf(low, h)
	water_y = low - 2.2
	var shift := rng.randf_range(0.0, TAU)
	var roads: Array[SurfaceTool] = [_tool(), _tool(), _tool()]
	var grass := _tool()
	var curb := _tool()
	var beach := _tool()
	var cliff := _tool()
	var step := track.step
	var s := -24.0
	var prev := _section(s, shift)
	while s < track.length + 90.0:
		var next := _section(s + step, shift)
		var mid := s + step / 2.0
		var v0 := s / 4.0
		var v1 := (s + step) / 4.0
		var kind := track.surface(clampf(mid, 0.0, track.length))
		_quad(roads[kind], prev["l0"], prev["r0"], next["r0"], next["l0"], Vector2(0.0, v0), Vector2(2.0, v0), Vector2(2.0, v1), Vector2(0.0, v1))
		var open := track.shoulder(mid) > 0.02
		for key: String in ["l", "r"]:
			var flip := key == "l"
			var strips: Array = [[grass, "0", "1", 1.0], [curb, "1", "2", 0.25], [curb, "2", "3", 0.3], [beach if open else cliff, "3", "4", 4.0]]
			for strip: Array in strips:
				var a: Vector3 = prev[key + str(strip[1])]
				var b: Vector3 = prev[key + str(strip[2])]
				var c: Vector3 = next[key + str(strip[2])]
				var d: Vector3 = next[key + str(strip[1])]
				var wide: float = strip[3]
				if flip:
					_quad(strip[0], b, a, d, c, Vector2(wide, v0), Vector2(0.0, v0), Vector2(0.0, v1), Vector2(wide, v1))
				else:
					_quad(strip[0], a, b, c, d, Vector2(0.0, v0), Vector2(wide, v0), Vector2(wide, v1), Vector2(0.0, v1))
		prev = next
		s += step
	_commit(roads[SprintTrack.Surface.ROAD], "road")
	_commit(roads[SprintTrack.Surface.SAND], "sand", {"tint": Color(1.0, 0.93, 0.8)})
	_commit(roads[SprintTrack.Surface.PLANKS], "planks", {"rough": 0.3, "tint": Color(0.72, 0.74, 0.8)})
	_commit(grass, "grass")
	_commit(curb, "cliff")
	_commit(beach, "sand")
	_commit(cliff, "cliff")
	var center := (track.points[0] + track.points[track.count() - 1]) / 2.0
	(lowpoly as ThreedScreen).add_water(Vector3(center.x, water_y, center.y), 1500.0)
	_build_rails()
	_build_decor(rng)
	# Камни на плечах сужений.
	for rock in track.rocks:
		var stone := spawn_model("prop", "rock")
		stone.position = track.world(rock.x, rock.y, -0.15)
		stone.scale = Vector3.ONE * rock.z / 0.6
		stone.rotation.y = rng.randf_range(-PI, PI)
	# Старт и финиш: флаги и перекладина; за финишем маяк.
	for gate: float in [34.0, track.length]:
		var half := track.half(gate)
		for side: float in [-1.0, 1.0]:
			var flag := spawn_model("prop", "flag")
			flag.position = track.world(gate, side * (half + 0.6))
			flag.rotation.y = track.yaw(gate) + PI / 2.0
			flag.scale = Vector3.ONE * 1.6
		var bar := lowpoly.add_box(Vector3.ZERO, Vector3(half * 2.0 + 1.6, 0.45, 0.3), lowpoly_texture("sail"), 1.5)
		bar.position = track.world(gate, 0.0, 5.0)
		bar.rotation.y = track.yaw(gate)
	var tower := spawn_model("finish", "lighthouse")
	tower.position = track.world(track.length + 70.0, track.full_half + tuning.verge + 6.0, -0.5)
	for i in sim.cars.size():
		var holder := Node3D.new()
		lowpoly.world.add_child(holder)
		var model := spawn_model("rival" if i > 0 else "hero", "cart_rival" if i > 0 else "cart", holder)
		model.scale = Vector3.ONE * SCALE
		car_nodes.append(holder)
		car_models.append(model)


## Перила мостков на сужениях: столбики и два каната.
func _build_rails() -> void:
	var wood := lowpoly.tex_material(lowpoly_texture("planks"))
	var cord := lowpoly.tex_material(lowpoly_texture("sail"), {"tint": Color(0.8, 0.68, 0.48)})
	for r in track.narrows:
		var s := r.x
		while s <= r.y:
			for side: float in [-1.0, 1.0]:
				var post := MeshInstance3D.new()
				var box := BoxMesh.new()
				box.size = Vector3(0.16, 1.0, 0.16)
				box.material = wood
				post.mesh = box
				post.position = track.world(s, side * (track.half(s) + 0.1), 0.5)
				lowpoly.world.add_child(post)
				if s + 4.0 <= r.y:
					for up: float in [0.55, 0.92]:
						var a := track.world(s, side * (track.half(s) + 0.1), up)
						var b := track.world(s + 4.0, side * (track.half(s + 4.0) + 0.1), up)
						var rope := MeshInstance3D.new()
						var line := BoxMesh.new()
						line.size = Vector3(0.05, 0.05, a.distance_to(b))
						line.material = cord
						rope.mesh = line
						lowpoly.world.add_child(rope)
						rope.look_at_from_position((a + b) / 2.0, b, Vector3.UP)
			s += 4.0


## Пальмы, камни, бочки и ящики на пляже за бортиком.
func _build_decor(rng: RandomNumberGenerator) -> void:
	var palm := lowpoly_set.model("palm", true).texture
	var s := rng.randf_range(0.0, 8.0)
	var side := 1.0
	while s < track.length + 60.0:
		if track.shoulder(s) > 0.95:
			var off := rng.randf_range(2.0, BEACH * 0.55)
			var at := track.world(s, side * (track.half(s) + tuning.verge + 0.7 + off))
			at.y = lerpf(track.height(s) + CURB, water_y - 1.2, off / BEACH) - 0.15
			if rng.randf() < 0.55 and not is_pink("prop"):
				(lowpoly as ThreedScreen).add_palm(palm, at, rng.randf_range(-PI, PI), rng.randf_range(4.2, 6.0), rng)
			else:
				var names := ["rock", "rock", "barrel", "crate", "chest"]
				var prop := spawn_model("prop", names[rng.randi_range(0, names.size() - 1)])
				prop.position = at
				prop.rotation.y = rng.randf_range(-PI, PI)
				if rng.randf() < 0.5:
					prop.scale = Vector3.ONE * rng.randf_range(1.2, 2.2)
		s += rng.randf_range(7.0, 15.0)
		side = -side if rng.randf() < 0.7 else side


## Клубы пыли и дыма из-под колёс: запас мягких кружков лицом к камере.
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
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		var quad := QuadMesh.new()
		quad.material = m
		var node := MeshInstance3D.new()
		node.mesh = quad
		node.visible = false
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		lowpoly.world.add_child(node)
		_puffs.append(node)
		_puff_life.append(0.0)


func _puff(at: Vector3, color: Color) -> void:
	var node := _puffs[_puff_next]
	_puff_life[_puff_next] = 1.0
	_puff_next = (_puff_next + 1) % PUFFS
	node.position = at
	node.visible = true
	((node.mesh as QuadMesh).material as StandardMaterial3D).albedo_color = color


# --- Шаг -------------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	_flash = maxf(_flash - delta * 2.5, 0.0)
	_shake = maxf(_shake - delta * 3.0, 0.0)
	_shift_blink = maxf(_shift_blink - delta, 0.0)
	# Обзор мышью: камера отходит от хода и сама возвращается.
	var turn := look_take(delta)
	if turn.length() > 0.0004:
		_look_idle = 0.0
		_look.x = clampf(_look.x - turn.x, -2.6, 2.6)
		_look.y = clampf(_look.y + turn.y, -0.25, 0.6)
	else:
		_look_idle += delta
		if _look_idle > 0.7:
			_look = _look.lerp(Vector2.ZERO, 1.0 - exp(-tuning.cam_return * delta))
	# Фризы в движении с догоном времени (`Demo.bug_frame`).
	bug_frame(delta, sim.countdown <= 0.0 and absf(sim.player().speed) > 1.0, _step)


func _step(dt: float) -> void:
	_time += dt
	bug_input_tick()
	var hold := minf(_stop_left, dt)
	_stop_left -= hold
	var left := dt - hold
	while left > 0.0001 and running:
		var h := minf(left, SprintSim.DT)
		left -= h
		var steer := 0.0
		var gas := 0.0
		if bot_driven():
			sim.bot(active_bot_mode())
			steer = sim.bot_steer
			gas = sim.bot_gas
		else:
			# Ход с багом управления из прошлого (`Demo.bug_axis`).
			var axis := bug_axis(GameInput.axis())
			steer = axis.x
			gas = -axis.y
			if GameInput.b_pressed():
				gas = -1.0
			elif GameInput.a_pressed():
				gas = maxf(gas, 1.0)
		sim.step(h, steer, gas)
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
		&"shift":
			_play("shift")
			_shift_blink = 0.35
		&"wall":
			_play("wall")
			_shake = maxf(_shake, 0.5)
		&"crash":
			_play("crash")
			_shake = 1.0
			_flash = 1.0
			_stop_left = tuning.hit_stop
			if AutoTest.enabled and not embedded:
				AutoTest.note("racing threed: камень на %.0f м" % sim.player().s)
		&"hit":
			_play("hit")
			_shake = maxf(_shake, 0.35)
		&"finish":
			end_demo(true)
		&"timeout":
			end_demo(false)


func _on_end(goal: bool) -> void:
	_music.stop()
	_engine.stop()
	if goal:
		_play("finish")
	if AutoTest.enabled and not embedded:
		AutoTest.note("racing threed: %s за %.1f с, место %d, предел %.0f км/ч, переключений %d, бортов %d, камней %d, касаний %d" % [
				"доехал" if goal else "не доехал (%.0f м)" % sim.player().s, sim.time, sim.place(), sim.top * 3.6, sim.shifts, sim.scrapes,
				sim.crashes, sim.bumps])


func _result_title(goal: bool) -> String:
	return "%d место" % sim.place() if goal else "не доехал"


func _result_caption() -> String:
	return "из %d · %d с · ударов %d" % [sim.cars.size(), int(round(sim.time)), sim.scrapes + sim.crashes]


# --- Картинка --------------------------------------------------------------------------------

func _sync(dt: float) -> void:
	var me := sim.player()
	var top_speed := tuning.gear_speeds[tuning.gear_speeds.size() - 1]
	for i in sim.cars.size():
		var car := sim.cars[i]
		var node := car_nodes[i]
		node.position = Vector3(car.pos.x, track.height(car.s), car.pos.y)
		# Машина лежит на уклоне дороги.
		var along := car.forward().dot(track.forward(car.s))
		node.rotation = Vector3(atan(track.slope(car.s)) * along, car.yaw, 0.0)
		var model := car_models[i]
		if model.pink:
			continue
		# Кузов клюёт на торможении, приседает на разгоне, кренится наружу поворота.
		var pitch := clampf(car.ax * 0.011, -0.12, 0.09) if i == 0 else 0.0
		var roll := clampf(-car.ay * 0.012, -0.14, 0.14) if i == 0 else clampf(-track.curve(car.s) * car.speed * car.speed * 0.012, -0.12, 0.12)
		model.rotation = Vector3(pitch, 0.0, roll)
		for axle: StringName in [&"axle_f", &"axle_r"]:
			var part := model.part(axle)
			if part != null:
				part.rotation.x -= car.speed * dt / WHEEL
				if axle == &"axle_f" and i == 0:
					part.rotation.y = -car.steer * 0.4
	# Мотор: высота по оборотам, на переключении проваливается.
	if _engine.playing:
		var revs := me.rpm * (0.6 if me.shift_left > 0.0 else 1.0)
		_engine.pitch_scale = lerpf(_engine.pitch_scale, 0.55 + revs * 1.25, clampf(14.0 * dt, 0.0, 1.0))
	# Пыль на песке и обочине, дым на скольжении.
	_puff_wait -= dt
	var at := Vector3(me.pos.x, track.height(me.s), me.pos.y)
	var dusty := me.surface == SprintTrack.Surface.SAND or me.surface == SprintTrack.Surface.VERGE
	if _puff_wait <= 0.0 and absf(me.speed) > 4.0 and (dusty or me.slide > 0.45):
		_puff_wait = 0.035
		var back := me.forward() * -1.1
		var wide := Vector2(-back.y, back.x).normalized() * (0.7 if _puff_next % 2 == 0 else -0.7)
		_puff(at + Vector3(back.x + wide.x, 0.25, back.y + wide.y), Color(0.86, 0.76, 0.56, 0.7) if dusty else Color(0.85, 0.85, 0.88, 0.55))
	for i in PUFFS:
		if _puff_life[i] <= 0.0:
			continue
		_puff_life[i] -= dt * 1.4
		var node := _puffs[i]
		node.visible = _puff_life[i] > 0.0
		node.position.y += dt * 0.9
		node.scale = Vector3.ONE * lerpf(3.4, 0.9, _puff_life[i])
		var m := (node.mesh as QuadMesh).material as StandardMaterial3D
		m.albedo_color.a = 0.6 * maxf(_puff_life[i], 0.0)
	# Камера за машиной смотрит по ходу: в заносе машину видно боком.
	var heading := atan2(-me.vel.x, -me.vel.y) if me.vel.length() > 4.0 and me.speed > 0.0 else me.yaw
	_cam_yaw = lerp_angle(_cam_yaw, heading, 1.0 - exp(-5.5 * dt)) if dt > 0.0 else heading
	var yaw := _cam_yaw + _look.x
	var back_dir := Vector3(sin(yaw), 0.0, cos(yaw))
	var eye := at + back_dir * tuning.cam_distance * cos(_look.y * 0.6) + Vector3(0.0, tuning.cam_height + _look.y * 5.0, 0.0)
	var jitter := _shake + (0.18 if me.surface == SprintTrack.Surface.VERGE and absf(me.speed) > 5.0 else 0.0)
	eye += Vector3(sin(_time * 61.0), cos(_time * 47.0), 0.0) * 0.07 * jitter
	eye.y = maxf(eye.y, water_y + 1.0)
	lowpoly.camera.transform = Transform3D(Basis.IDENTITY, eye).looking_at(at + Vector3(0.0, tuning.cam_look, 0.0))
	lowpoly.camera.fov = tuning.cam_fov + tuning.cam_fov_speed * clampf(absf(me.speed) / top_speed, 0.0, 1.0)


# --- HUD: в полном разрешении, плашки тёмного стекла (плейтест 2026-11-13) --------------------

## Карта трассы для HUD: ось, вписанная в `size`.
func _build_map(size: Vector2) -> void:
	var low := Vector2(INF, INF)
	var high := -low
	for p in track.points:
		low = low.min(p)
		high = high.max(p)
	_map_scale = minf(size.x / maxf(high.x - low.x, 1.0), size.y / maxf(high.y - low.y, 1.0))
	_map_origin = (low + high) / 2.0
	_map.clear()
	for i in range(0, track.count(), 3):
		_map.append((track.points[i] - _map_origin) * _map_scale)
	_map.append((track.points[track.count() - 1] - _map_origin) * _map_scale)


func _draw_hud(canvas: CanvasItem) -> void:
	if sim == null:
		return
	var h := ThreedHud.begin(canvas, lowpoly)
	var view := lowpoly.view
	var me := sim.player()
	if _flash > 0.0:
		h.rect(Rect2(Vector2.ZERO, view), Color(1.0, 1.0, 1.0, _flash * 0.4))
	# Место: слева сверху.
	h.panel(Rect2(10.0, 9.0, 78.0, 36.0), 7.0)
	h.text(Vector2(17.0, 17.0), "МЕСТО", 5.2, ThreedHud.DIM, -1)
	var place := sim.place()
	h.text(Vector2(17.0, 31.5), str(place), 20.0, ThreedHud.GOLD if place == 1 else ThreedHud.WHITE, -1)
	h.text(Vector2(36.0, 34.0), "из %d" % sim.cars.size(), 7.0, ThreedHud.DIM, -1)
	for i in sim.cars.size():
		var filled := i >= place - 1
		h.circle(Vector2(63.0 + i * 6.2, 34.0), 2.1, (ThreedHud.GOLD if i == place - 1 else ThreedHud.FAINT) if filled else ThreedHud.RED)
	# Время: справа сверху.
	h.panel(Rect2(view.x - 88.0, 9.0, 78.0, 36.0), 7.0)
	h.text(Vector2(view.x - 81.0, 17.0), "ВРЕМЯ", 5.2, ThreedHud.DIM, -1)
	h.text(Vector2(view.x - 81.0, 31.5), "%d:%04.1f" % [int(sim.time) / 60, fmod(sim.time, 60.0)], 15.0, ThreedHud.WHITE, -1)
	# Путь до финиша сверху по центру: сужения засечками, соперники точками, игрок бегунком.
	var from := Vector2(view.x / 2.0 - 92.0, 20.0)
	var span := 184.0
	h.panel(Rect2(from.x - 12.0, 11.0, span + 24.0, 18.0), 9.0)
	h.bar(from, from + Vector2(span, 0.0), ThreedHud.FAINT, 2.6)
	for r in track.narrows:
		h.line(from + Vector2(span * r.x / track.length, 0.0), from + Vector2(span * r.y / track.length, 0.0), ThreedHud.DIM, 2.6)
	h.bar(from, from + Vector2(span * sim.progress(), 0.0), ThreedHud.GOLD, 2.6)
	for cell in 6:
		h.rect(Rect2(from.x + span + 3.0 + (cell % 2) * 2.2, 15.6 + (cell / 2) * 2.2 + (0.0 if cell % 2 == 0 else 0.0), 2.2, 2.2),
				ThreedHud.WHITE if (cell + cell / 2) % 2 == 0 else Color(0.0, 0.0, 0.0, 0.6))
	for i in range(1, sim.cars.size()):
		var dot := from + Vector2(span * clampf(sim.cars[i].s / track.length, 0.0, 1.0), 0.0)
		h.circle(dot, 2.9, Color(0.0, 0.0, 0.0, 0.55))
		h.circle(dot, 2.1, ThreedHud.RED)
	var knob := from + Vector2(span * sim.progress(), 0.0)
	h.circle(knob, 4.4, Color(0.0, 0.0, 0.0, 0.55))
	h.circle(knob, 3.4, ThreedHud.GOLD)
	h.circle(knob + Vector2(-0.9, -0.9), 1.1, Color(1.0, 1.0, 1.0, 0.7))
	# Карта трассы слева внизу.
	var box := Rect2(10.0, view.y - 86.0, 96.0, 76.0)
	if _map.is_empty():
		_build_map(box.size - Vector2(18.0, 18.0))
	h.panel(box, 7.0)
	var mid := box.position + box.size / 2.0
	var road := PackedVector2Array()
	for p in _map:
		road.append(mid + p)
	h.polyline(road, Color(0.0, 0.0, 0.0, 0.5), 3.4)
	h.polyline(road, ThreedHud.DIM, 1.6)
	for r in track.narrows:
		var part := PackedVector2Array()
		var at := r.x
		while at <= r.y:
			part.append(mid + (track.center(at) - _map_origin) * _map_scale)
			at += 6.0
		if part.size() > 1:
			h.polyline(part, ThreedHud.WHITE, 2.4)
	h.circle(road[road.size() - 1], 2.4, ThreedHud.WHITE)
	for i in range(sim.cars.size() - 1, -1, -1):
		var dot := mid + (sim.cars[i].pos - _map_origin) * _map_scale
		h.circle(dot, 3.2 if i == 0 else 2.6, Color(0.0, 0.0, 0.0, 0.6))
		h.circle(dot, 2.4 if i == 0 else 1.8, ThreedHud.GOLD if i == 0 else ThreedHud.RED)
	# Тахометр справа внизу: шкала оборотов с делениями и красной зоной, стрелка, передача,
	# скорость.
	var hub := Vector2(view.x - 52.0, view.y - 50.0)
	var a0 := PI * 0.75
	var sweep := PI * 1.5
	h.circle(hub, 43.0, Color(0.0, 0.0, 0.0, 0.25))
	h.circle(hub, 41.0, h.glass)
	h.arc(hub, 41.0, 0.0, TAU, h.edge, 0.6)
	h.arc(hub, 34.0, a0, a0 + sweep, ThreedHud.FAINT, 3.2)
	h.arc(hub, 34.0, a0 + sweep * tuning.shift_up, a0 + sweep, Color(ThreedHud.RED, 0.75), 3.2)
	var revs := clampf(me.rpm * (0.55 if me.shift_left > 0.0 else 1.0), 0.0, 1.0)
	_revs = lerpf(_revs, revs, 0.35)
	var hot := _revs > tuning.shift_up - 0.06
	h.arc(hub, 34.0, a0, a0 + sweep * maxf(_revs, 0.005), ThreedHud.RED if hot else ThreedHud.GOLD, 3.2)
	for tick in 9:
		var angle := a0 + sweep * tick / 8.0
		var dir := Vector2(cos(angle), sin(angle))
		h.line(hub + dir * 29.5, hub + dir * 26.0, ThreedHud.WHITE if tick < 8 else ThreedHud.RED, 0.9)
		if tick % 2 == 0:
			h.text(hub + dir * 21.5, str(tick), 4.6, ThreedHud.DIM)
	var needle := Vector2(cos(a0 + sweep * _revs), sin(a0 + sweep * _revs))
	h.line(hub - needle * 4.0, hub + needle * 30.0, Color(0.0, 0.0, 0.0, 0.45), 2.2)
	h.line(hub - needle * 4.0, hub + needle * 30.0, ThreedHud.RED if hot else ThreedHud.WHITE, 1.2)
	h.circle(hub, 12.5, h.deep)
	h.arc(hub, 12.5, 0.0, TAU, h.edge, 0.5)
	var blink := _shift_blink > 0.0 and int(_shift_blink * 16.0) % 2 == 0
	h.text(hub + Vector2(0.0, -0.5), "R" if me.speed < -0.5 else str(me.gear + 1), 15.0, ThreedHud.GOLD if blink or me.shift_left > 0.0 else ThreedHud.WHITE)
	h.text(hub + Vector2(0.0, 23.5), "%d" % roundi(absf(me.speed) * 3.6), 10.5, ThreedHud.WHITE)
	h.text(hub + Vector2(0.0, 32.5), "КМ/Ч", 4.2, ThreedHud.DIM)
	# Лампа переключения: горит у отсечки.
	h.circle(hub + Vector2(0.0, -24.0), 2.6, ThreedHud.RED if hot else Color(1.0, 1.0, 1.0, 0.12))
	if sim.countdown > 0.0:
		h.text(Vector2(view.x / 2.0, view.y / 2.0 - 30.0), str(ceili(sim.countdown)), 46.0, ThreedHud.WHITE, 0, Color(0.05, 0.07, 0.11, 0.8))
	h.end()
