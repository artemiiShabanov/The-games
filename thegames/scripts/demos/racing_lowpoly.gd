extends Demo
## Демка гонки × low poly, каталог `docs/specs/demos_catalog.md`: «кольцо с дрифтом» (#113,
## решение 2026-11-12, правила 2026-11-13, образец Crash Team Racing). Шлюпка на колёсах под
## парусом едет по извилистой замкнутой трассе, два круга против трёх соперников, старт
## последним; камера за шлюпкой. Влево и вправо руль, вверх (или W) газ, вниз тормоз, A дрифт:
## в заносе копится заряд, на выходе он даёт ускорение. Борта отбрасывают; где их нет, вылет в
## воду стоит пары секунд. Грязь у внутреннего края поворотов тормозит, полосы попутного ветра
## ускоряют, трамплин перебрасывает через промоину, если хватило скорости. Цели нет: гонка
## кончается финишем, итог это место.
## Трасса из `RingTrackGen` по сиду записи. Правила и боты живут в `RingSim` (без окна, им же
## проверяются сто сидов); демка ведёт его шагами по 1/60 с, рисует и озвучивает его события.
## Картинка на `LowpolyScreen` в духе первой PlayStation: трасса лентой с каменными бортами и
## травяными откосами к воде, участки без бортов настилом из досок, по откосам пальмы и камни,
## маяк внутри кольца.
##
## Общие баги (#44) и баг технологии `mesh_holes` живут в `Demo` и `LowpolyScreen`, демка только
## зовёт хуки: фризы `bug_frame`, заикание музыки, ввод с опозданием, розовые заглушки вместо
## соперников, пальм и маяка. Баги жанра и баланса для этой демки включит #117.

const PLACEHOLDER_SLOTS: Array[String] = ["rival", "prop", "finish"]
const MELODY := [0, 0, 7, null, 5, 5, 3, null, 0, 0, 7, 10, 12, null, 10, 7,
	5, 5, 12, null, 10, 10, 8, null, 7, 5, 3, 5, 7, null, 0, null]
const BASS := [-12, -12, -12, -5, -7, -7, -7, 0, -12, -12, -12, -5, -9, -9, -7, -7]
const DECOR := ["palm", "palm", "rock", "barrel", "crate"]
## Борт: высота и ширина верха. Откос за ним: ширина до воды.
const WALL_HEIGHT := 0.6
const WALL_TOP := 0.5
const VERGE := 7.0
const WATER_DROP := 1.6
const WHEEL := 0.32

var tuning: RacingLowpolyTuning
var track: RingTrack
var sim: RingSim
var cam: LowpolyFollowCam
var car_nodes: Array[Node3D] = []
var car_models: Array[LowpolyModel] = []
var car_shadows: Array[MeshInstance3D] = []
var water_y := -3.0

var _time := 0.0
var _lean := 0.0
var _flash := 0.0
var _map := PackedVector2Array()
var _map_origin := Vector2.ZERO
var _map_scale := 1.0
var _map_size := Vector2.ZERO
var _music: AudioStreamPlayer
var _sfx := {}


func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _on_start() -> void:
	tuning = RacingLowpolyTuning.load_default()
	track = RingTrackGen.generate(record.seed if record != null else 1)
	sim = RingSim.create(track, tuning)
	lowpoly_screen(_draw_hud)
	cam = LowpolyFollowCam.make(lowpoly.tuning)
	cam.distance = tuning.cam_distance
	cam.height = tuning.cam_height
	cam.look_height = tuning.cam_look
	cam.turn = tuning.cam_turn
	_build_world()
	_build_map()
	_setup_audio()
	var me := sim.player()
	cam.step(0.0, track.world(me.s, me.d), me.yaw, false)
	_sync(0.0)


func _setup_audio() -> void:
	var quiet := embedded
	_music = Sfx.music(Sfx.tracker_loop(MELODY, BASS, 150.0), tuning.music_db if not quiet else -80.0)
	add_child(_music)
	bug_music = _music
	if not quiet:
		_music.play()
	_sfx["go"] = Sfx.player(Sfx.blip(880.0, 0.3, 0.4, 6.0))
	_sfx["drift"] = Sfx.player(Sfx.hiss(0.25, 0.14))
	_sfx["boost"] = Sfx.player(Sfx.blip(660.0, 0.25, 0.4, 5.0))
	_sfx["wind"] = Sfx.player(Sfx.blip(990.0, 0.2, 0.3, 8.0))
	_sfx["bump"] = Sfx.player(Sfx.thud(0.12, 0.45))
	_sfx["splash"] = Sfx.player(Sfx.thud(0.3, 0.6))
	_sfx["jump"] = Sfx.player(Sfx.blip(520.0, 0.18, 0.3, 6.0))
	_sfx["lap"] = Sfx.player(Sfx.blip(1318.0, 0.2, 0.35, 10.0))
	_sfx["finish"] = Sfx.player(Sfx.blip(880.0, 0.5, 0.4, 5.0))
	for p in _sfx.values():
		(p as AudioStreamPlayer).volume_db = tuning.sfx_db if not quiet else -80.0
		add_child(p)


func _play(name: String) -> void:
	bug_play(_sfx[name])


# --- Мир ---------------------------------------------------------------------------------------

## Четырёхугольник в набор граней лицом в сторону `face`.
static func _quad(m: Array, a: Vector3, b: Vector3, c: Vector3, d: Vector3, face: Vector3, ua: Vector2, ub: Vector2, uc: Vector2,
		ud: Vector2) -> void:
	var n := (b - a).cross(c - a).normalized()
	if n.dot(face) < 0.0:
		# Обход в другую сторону: меняются местами второй и четвёртый угол.
		var swap := b
		b = d
		d = swap
		var swap_uv := ub
		ub = ud
		ud = swap_uv
		n = (b - a).cross(c - a).normalized()
	var verts: PackedVector3Array = m[0]
	var normals: PackedVector3Array = m[1]
	var uvs: PackedVector2Array = m[2]
	for item: Array in [[a, ua], [b, ub], [c, uc], [a, ua], [c, uc], [d, ud]]:
		LowpolyScreen.push(verts, normals, uvs, item[0], n, item[1])
	LowpolyScreen.flip_last(verts, normals, uvs, 2)
	m[0] = verts
	m[1] = normals
	m[2] = uvs


static func _mesh() -> Array:
	return [PackedVector3Array(), PackedVector3Array(), PackedVector2Array()]


func _commit(m: Array, tex: Texture2D, extra := {}) -> void:
	if (m[0] as PackedVector3Array).is_empty():
		return
	var node := MeshInstance3D.new()
	node.mesh = LowpolyScreen._commit(m[0], m[1], m[2], lowpoly.tex_material(tex, extra))
	lowpoly.world.add_child(node)


func _build_world() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed if record != null else 1, ":ring-look"))
	var low := INF
	for h in track.heights:
		low = minf(low, h)
	water_y = low - WATER_DROP
	var road := _mesh()
	var deck := _mesh()
	var walls := _mesh()
	var verge := _mesh()
	var half := track.half_width
	var n := track.count()
	var step := track.step
	for i in n:
		var s0 := i * step
		var s1 := s0 + step
		var mid := s0 + step / 2.0
		if track.in_gap(mid):
			continue
		var v0 := s0 / 4.0
		var v1 := s1 / 4.0
		var open := track.is_open(mid)
		_quad(deck if open else road, track.world(s0, -half), track.world(s0, half), track.world(s1, half), track.world(s1, -half),
				Vector3.UP, Vector2(0.0, v0), Vector2(2.0, v0), Vector2(2.0, v1), Vector2(0.0, v1))
		for side: float in [-1.0, 1.0]:
			var out0 := track.right(s0) * side
			var out1 := track.right(s1) * side
			var face := Vector3((out0.x + out1.x) / 2.0, 0.0, (out0.y + out1.y) / 2.0)
			var a := track.world(s0, side * half)
			var b := track.world(s1, side * half)
			if open:
				# Настил над водой: бок до воды.
				_quad(deck, a, b, Vector3(b.x, water_y - 0.3, b.z), Vector3(a.x, water_y - 0.3, a.z), face,
						Vector2(v0, 0.0), Vector2(v1, 0.0), Vector2(v1, 1.5), Vector2(v0, 1.5))
				continue
			var up := Vector3(0.0, WALL_HEIGHT, 0.0)
			var a_out := track.world(s0, side * (half + WALL_TOP), WALL_HEIGHT)
			var b_out := track.world(s1, side * (half + WALL_TOP), WALL_HEIGHT)
			_quad(walls, a, b, b + up, a + up, -face, Vector2(v0, 0.3), Vector2(v1, 0.3), Vector2(v1, 0.0), Vector2(v0, 0.0))
			_quad(walls, a + up, b + up, b_out, a_out, Vector3.UP, Vector2(v0, 0.0), Vector2(v1, 0.0), Vector2(v1, 0.25), Vector2(v0, 0.25))
			var a_far := track.world(s0, side * (half + VERGE))
			var b_far := track.world(s1, side * (half + VERGE))
			a_far.y = water_y - 0.3
			b_far.y = water_y - 0.3
			_quad(verge, a_out, b_out, b_far, a_far, Vector3.UP + face, Vector2(v0, 0.0), Vector2(v1, 0.0), Vector2(v1, 2.2), Vector2(v0, 2.2))
	_commit(road, lowpoly_texture("road"))
	_commit(deck, lowpoly_texture("planks"))
	_commit(walls, lowpoly_texture("rock"))
	_commit(verge, lowpoly_texture("grass"))
	_build_marks()
	_build_ramp()
	_build_decor(rng)
	var center := Vector2.ZERO
	for p in track.points:
		center += p / n
	lowpoly.add_plane(Vector3(center.x, water_y, center.y), Vector2(520.0, 520.0), lowpoly_texture("water"), 6.0,
			{"uv_scroll": Vector2(0.02, 0.035), "affine": 0.0})
	# Маяк на островке внутри кольца.
	var islet := LowpolyTerrain.make(Vector3(center.x - 4.0, 0.0, center.y - 4.0), 1.0, 8, 8)
	for iz in 9:
		for ix in 9:
			var rim := ix == 0 or iz == 0 or ix == 8 or iz == 8
			islet.set_h(ix, iz, water_y - 0.2 if rim else water_y + 1.2)
	islet.build(lowpoly, lowpoly_texture("grass"), 3.0, lowpoly_texture("rock"), water_y - 0.3)
	var tower := spawn_model("finish", "lighthouse")
	tower.position = Vector3(center.x, water_y + 1.15, center.y)
	# Старт: флаги по бокам и перекладина.
	for side: float in [-1.0, 1.0]:
		var flag := spawn_model("prop", "flag")
		flag.position = track.world(0.0, side * (half + 0.3), WALL_HEIGHT)
		flag.rotation.y = track.yaw(0.0) + PI / 2.0
	var bar := lowpoly.add_box(Vector3.ZERO, Vector3(half * 2.0 + 1.0, 0.3, 0.3), lowpoly_texture("sail"), 1.5)
	bar.position = track.world(0.0, 0.0, 3.2)
	bar.rotation.y = track.yaw(0.0)
	for i in sim.cars.size():
		var holder := Node3D.new()
		lowpoly.world.add_child(holder)
		var model := spawn_model("rival" if i > 0 else "hero", "cart_rival" if i > 0 else "cart", holder)
		car_nodes.append(holder)
		car_models.append(model)
		car_shadows.append(lowpoly.add_shadow(1.1))


## Грязь и полосы ветра поверх дороги.
func _build_marks() -> void:
	var mud := _mesh()
	var wind := _mesh()
	var half := track.half_width
	for m in track.muds:
		var span := fposmod(m.s1 - m.s0, track.length)
		var k := 0.0
		while k < span:
			var s0 := m.s0 + k
			var s1 := m.s0 + minf(k + track.step, span)
			var inner := m.side * (half - m.width)
			var outer := m.side * half
			_quad(mud, track.world(s0, inner, 0.04), track.world(s0, outer, 0.04), track.world(s1, outer, 0.04), track.world(s1, inner, 0.04),
					Vector3.UP, Vector2(0.0, s0 / 3.0), Vector2(1.0, s0 / 3.0), Vector2(1.0, s1 / 3.0), Vector2(0.0, s1 / 3.0))
			k += track.step
	for w in track.winds:
		var span := fposmod(w.s1 - w.s0, track.length)
		var k := 0.0
		while k < span:
			var s0 := w.s0 + k
			var s1 := w.s0 + minf(k + track.step, span)
			_quad(wind, track.world(s0, w.d - w.half, 0.06), track.world(s0, w.d + w.half, 0.06), track.world(s1, w.d + w.half, 0.06),
					track.world(s1, w.d - w.half, 0.06), Vector3.UP, Vector2(0.0, -k / 2.6), Vector2(1.0, -k / 2.6),
					Vector2(1.0, -(k + track.step) / 2.6), Vector2(0.0, -(k + track.step) / 2.6))
			k += track.step
	_commit(mud, lowpoly_texture("mud"))
	_commit(wind, lowpoly_texture("wind"), {"uv_scroll": Vector2(0.0, 1.6), "lit": 0.0, "affine": 0.0})


## Трамплин: наклонный настил перед промоиной и обрез дороги за ней.
func _build_ramp() -> void:
	var ramp := _mesh()
	var half := track.half_width
	var from := track.ramp_s - track.ramp_run
	var lift := Vector3(0.0, 1.1, 0.0)
	var a := track.world(from, -half, 0.03)
	var b := track.world(from, half, 0.03)
	var c := track.world(track.ramp_s, half) + lift
	var d := track.world(track.ramp_s, -half) + lift
	_quad(ramp, a, b, c, d, Vector3.UP, Vector2(0, 0), Vector2(2, 0), Vector2(2, 1.5), Vector2(0, 1.5))
	var fwd := track.forward(track.ramp_s)
	var front := Vector3(fwd.x, 0.0, fwd.y)
	_quad(ramp, d, c, c - lift - Vector3(0.0, 2.0, 0.0), d - lift - Vector3(0.0, 2.0, 0.0), front, Vector2(0, 0), Vector2(2, 0), Vector2(2, 0.8), Vector2(0, 0.8))
	var after := track.ramp_s + track.ramp_gap
	var e := track.world(after, -half)
	var f := track.world(after, half)
	_quad(ramp, e, f, Vector3(f.x, water_y - 0.3, f.z), Vector3(e.x, water_y - 0.3, e.z), -front, Vector2(0, 0), Vector2(2, 0), Vector2(2, 1.0), Vector2(0, 1.0))
	_commit(ramp, lowpoly_texture("planks"))


## Пальмы, камни, бочки и ящики на откосах за бортами.
func _build_decor(rng: RandomNumberGenerator) -> void:
	var half := track.half_width
	var s := rng.randf_range(4.0, 9.0)
	var side := 1.0
	while s < track.length:
		if not track.is_open(s) and not track.in_gap(s) and absf(track.delta(s, 0.0)) > 6.0:
			var off := rng.randf_range(1.6, 4.6)
			var k := off / (VERGE - WALL_TOP)
			var at := track.world(s, side * (half + WALL_TOP + off))
			at.y = lerpf(track.height(s) + WALL_HEIGHT, water_y - 0.3, k) - 0.1
			var prop := spawn_model("prop", DECOR[rng.randi_range(0, DECOR.size() - 1)])
			prop.position = at
			prop.rotation.y = rng.randf_range(-PI, PI)
		s += rng.randf_range(6.0, 12.0)
		side = -side


## Мини-карта: точки оси в рамке HUD.
func _build_map() -> void:
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	for p in track.points:
		lo = lo.min(p)
		hi = hi.max(p)
	var box := Vector2(74.0, 56.0)
	var scale := minf(box.x / maxf(hi.x - lo.x, 1.0), box.y / maxf(hi.y - lo.y, 1.0))
	_map_origin = lo
	_map_scale = scale
	_map_size = (hi - lo) * scale
	for i in range(0, track.count(), 2):
		_map.append((track.points[i] - lo) * scale)
	_map.append(_map[0])


# --- Шаг -------------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	_flash = maxf(_flash - delta, 0.0)
	# Фризы в движении с догоном времени (`Demo.bug_frame`).
	bug_frame(delta, absf(sim.player().speed) > 1.0, _step)


func _step(dt: float) -> void:
	_time += dt
	bug_input_tick()
	var left := dt
	# Правила шагами по 1/60 с; бот решает на каждом шаге.
	while left > 0.0001 and running:
		var h := minf(left, RingSim.DT)
		left -= h
		var axis := GameInput.axis()
		var drift := GameInput.a_pressed()
		if bot_driven():
			sim.bot(active_bot_mode())
			axis = Vector2(sim.bot_steer, -sim.bot_gas)
			drift = sim.bot_drift
		# Руль и газ: с багом управления из прошлого на delay_ms (`Demo.bug_axis`).
		axis = bug_axis(axis)
		sim.step(h, axis.x, -axis.y, drift)
		for ev in sim.events:
			_on_event(ev)
		sim.events.clear()
	_sync(dt)


## Событие правил: звук, эффект, конец демки.
func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"go":
			_play("go")
		&"drift":
			_play("drift")
		&"boost":
			_play("boost")
		&"wind":
			_play("wind")
		&"bump", &"hit":
			_play("bump")
		&"splash":
			_play("splash")
			_flash = 0.5
			if AutoTest.enabled and not embedded:
				AutoTest.note("racing lowpoly: в воде на %.1f с, место на круге %.0f м" % [sim.time, sim.player().s])
		&"jump":
			_play("jump")
		&"land":
			_play("bump")
		&"lap":
			_play("lap")
		&"finish":
			end_demo(true)
		&"timeout":
			end_demo(false)


func _on_end(goal: bool) -> void:
	_music.stop()
	if goal:
		_play("finish")
	if AutoTest.enabled and not embedded:
		AutoTest.note("racing lowpoly: %s за %.1f с, место %d из %d, в воде %d, бортов %d, ускорений от дрифта %d" % [
				"финиш" if goal else "не доехал", sim.time, sim.place(), sim.cars.size(), sim.sinks, sim.bumps, sim.boosts])


func _result_title(goal: bool) -> String:
	return "%d место" % sim.place() if goal else "не доехал"


func _result_caption() -> String:
	return "из %d · %d с · в воде %d" % [sim.cars.size(), int(round(sim.time)), sim.sinks]


# --- Картинка --------------------------------------------------------------------------------

func _sync(dt: float) -> void:
	var me := sim.player()
	for i in sim.cars.size():
		var car := sim.cars[i]
		var node := car_nodes[i]
		var at := Vector3(car.pos.x, track.height(car.s) + sim.air_height(car), car.pos.y)
		node.position = at
		node.rotation.y = car.yaw
		node.visible = car.sunk <= 0.0
		car_shadows[i].visible = node.visible
		car_shadows[i].position = Vector3(car.pos.x, track.height(car.s) + 0.05, car.pos.y)
		var model := car_models[i]
		if not model.pink:
			for axle: StringName in [&"axle_f", &"axle_r"]:
				var part := model.part(axle)
				if part != null:
					part.rotation.x -= car.speed * dt / WHEEL
	# Занос: корпус довёрнут в поворот и накренён.
	var lean := me.drift_dir * 0.35 if me.drifting else 0.0
	_lean = lerpf(_lean, lean, clampf(8.0 * dt, 0.0, 1.0))
	car_models[0].rotation.y = -_lean
	car_models[0].rotation.z = -_lean * 0.3
	# Камера смотрит по ходу, а не по носу: в заносе шлюпку видно боком.
	var heading := atan2(-me.vel.x, -me.vel.y) if me.vel.length() > 3.0 else me.yaw
	cam.step(dt, Vector3(me.pos.x, track.height(me.s), me.pos.y), heading, true)
	cam.apply(lowpoly.camera)


func _draw_hud(canvas: CanvasItem) -> void:
	var dark := lowpoly.ink(LowpolyScreen.DARK).darkened(0.5)
	var red := lowpoly.ink(LowpolyScreen.DANGER)
	var gold := lowpoly.ink(LowpolyScreen.BONUS)
	var white := lowpoly.ink(LowpolyScreen.LIGHT)
	var blue := lowpoly.ink(LowpolyScreen.GROUND_2).lightened(0.3)
	var view := lowpoly.view
	var me := sim.player()
	if _flash > 0.0:
		canvas.draw_rect(Rect2(Vector2.ZERO, view), Color(blue, _flash * 0.9))
	# Место крупно слева, круг по центру.
	PixelFont16.draw(canvas, Vector2(10.0, 6.0), str(sim.place()), white, gold, dark, 3.0)
	PixelFont16.draw(canvas, Vector2(34.0, 18.0), "/%d" % sim.cars.size(), white, white, dark, 1.0)
	var lap := "КРУГ %d/%d" % [sim.lap_of(me), tuning.laps]
	PixelFont16.draw(canvas, Vector2(roundf(view.x / 2.0 - PixelFont16.width(lap, 1.0) / 2.0), 8.0), lap, white, white, dark, 1.0)
	# Скорость и заряд заноса слева внизу.
	var bar := Rect2(10.0, view.y - 20.0, 110.0, 8.0)
	canvas.draw_rect(bar.grow(2.0), dark)
	canvas.draw_rect(bar, dark.lightened(0.2))
	var boosted := me.boost > 0.0
	var fill := clampf(absf(me.speed) / (tuning.top_speed * tuning.boost_mult), 0.0, 1.0)
	var color := gold if boosted else white
	canvas.draw_rect(Rect2(bar.position, Vector2(roundf(bar.size.x * fill), bar.size.y)), color.darkened(0.25))
	canvas.draw_rect(Rect2(bar.position, Vector2(roundf(bar.size.x * fill), 3.0)), color)
	var limit := bar.position.x + roundf(bar.size.x / tuning.boost_mult)
	canvas.draw_rect(Rect2(limit, bar.position.y - 2.0, 1.0, bar.size.y + 4.0), dark)
	if me.drifting:
		var charge := Rect2(10.0, view.y - 32.0, 70.0, 5.0)
		var ready := me.charge >= tuning.charge_min
		canvas.draw_rect(charge.grow(2.0), dark)
		canvas.draw_rect(charge, dark.lightened(0.2))
		canvas.draw_rect(Rect2(charge.position, Vector2(roundf(charge.size.x * clampf(me.charge / tuning.charge_full, 0.0, 1.0)), charge.size.y)),
				gold if ready and int(_time * 12.0) % 2 == 0 else red)
	# Мини-карта справа внизу.
	var origin := Vector2(view.x - _map_size.x - 12.0, view.y - _map_size.y - 12.0)
	var line := PackedVector2Array()
	for p in _map:
		line.append(origin + p)
	canvas.draw_polyline(line, dark, 5.0)
	canvas.draw_polyline(line, white.darkened(0.25), 2.0)
	for i in range(sim.cars.size() - 1, -1, -1):
		var dot := origin + (sim.cars[i].pos - _map_origin) * _map_scale
		canvas.draw_rect(Rect2(dot - Vector2(3, 3), Vector2(6, 6)), dark)
		canvas.draw_rect(Rect2(dot - Vector2(2, 2), Vector2(4, 4)), red if i > 0 else gold)
	# Отсчёт и вода.
	if sim.countdown > 0.0:
		var count := str(ceili(sim.countdown))
		PixelFont16.draw(canvas, Vector2(roundf(view.x / 2.0 - PixelFont16.width(count, 5.0) / 2.0), roundf(view.y / 2.0 - 40.0)), count,
				white, gold, dark, 5.0)
	elif me.sunk > 0.0:
		var text := "В ВОДЕ"
		PixelFont16.draw(canvas, Vector2(roundf(view.x / 2.0 - PixelFont16.width(text, 2.0) / 2.0), roundf(view.y / 2.0 - 20.0)), text,
				white, blue, dark, 2.0)
