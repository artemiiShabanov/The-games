extends Demo
## Демка шутер × low poly, каталог `docs/specs/demos_catalog.md`: «рельсовый тир» (#114, решение
## 2026-11-12, приёмы сложности 2026-11-13, образцы Virtua Cop, Time Crisis, House of the
## Dead). Камера сама едет по острову от остановки к остановке; игрок водит прицел (стрелки,
## мышь или правый стик) и стреляет (A или кнопка мыши), B перезаряжает обойму на шесть. Враги
## высовываются из-за бочек и ящиков, над каждым сжимается кольцо: сомкнулось, он стреляет и
## снимает жизнь. Метатель кидает бутылку, её сбивают в полёте; у капитана две жизни; в пленных
## с поднятыми руками стрелять нельзя; в переезде сбоку выбегают бегуны; бочка с порохом
## снимает всех врагов рядом. Жизней три, цель: доехать до флага.
## Маршрут из `RailLevelGen` по сиду записи. Правила и боты живут в `RailSim` (без окна, им же
## проверяются сто сидов); демка ведёт его шагами по 1/60 с, рисует и озвучивает его события.
## Картинка на `LowpolyScreen` в духе первой PlayStation: песчаные дюны, вода вокруг, пальмы и
## камни по краям, пистолет в кадре.
##
## Общие баги (#44) и баг технологии `mesh_holes` живут в `Demo` и `LowpolyScreen`, демка только
## зовёт хуки: фризы `bug_frame`, заикание музыки, ввод с опозданием, розовые заглушки вместо
## врагов, укрытий и флага. Баги жанра и баланса для этой демки включит #117.

const PLACEHOLDER_SLOTS: Array[String] = ["enemy", "prop", "finish"]
const MELODY := [0, null, 3, 0, 7, null, 5, 3, 0, null, 3, 0, 10, 8, 7, null,
	0, null, 3, 0, 7, null, 5, 3, 12, 10, 8, 7, 5, 3, 2, null]
const BASS := [-12, -12, -12, -12, -9, -9, -9, -9, -7, -7, -7, -7, -5, -5, -7, -7]
const DECOR := ["palm", "palm", "rock", "rock", "chest"]
const WHITE := Color(0.95, 0.93, 0.86)
const DUST := Color(0.78, 0.66, 0.44)
const HOT := Color(1.0, 0.6, 0.2)
const GLASS := Color(0.45, 0.8, 0.5)
const PUFFS := 40

var tuning: ShooterLowpolyTuning
var level: RailLevel
var sim: RailSim
## Прицел в кадре: x и y от −1 до 1, y вниз.
var aim := Vector2.ZERO
var foe_models: Array[LowpolyModel] = []
var foe_shadows: Array[MeshInstance3D] = []
var foe_bottles: Array[LowpolyModel] = []
var keg_nodes: Array[Node3D] = []
var bottle_nodes: Array[LowpolyModel] = []
var gun: LowpolyModel

var _time := 0.0
var _want_fire := false
var _want_reload := false
var _mouse_down := false
var _kick := 0.0
var _shake := 0.0
var _hurt := 0.0
var _boom := 0.0
var _stop_left := 0.0
var _shout := ""
var _shout_left := 0.0
var _flash := PackedFloat32Array()
var _dead := PackedFloat32Array()
var _shake_rng := RandomNumberGenerator.new()
var _puffs: Array[MeshInstance3D] = []
var _puff_age := PackedFloat32Array()
var _puff_life := PackedFloat32Array()
var _puff_size := PackedFloat32Array()
var _puff_vel := PackedVector3Array()
var _puff_next := 0
var _puff_tex: Texture2D
var _music: AudioStreamPlayer
var _sfx := {}


func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _on_start() -> void:
	tuning = ShooterLowpolyTuning.load_default()
	level = RailLevelGen.generate(record.seed if record != null else 1, null, tuning)
	sim = RailSim.create(level, tuning)
	lowpoly_screen(_draw_hud)
	lowpoly.camera.fov = tuning.fov
	look_start()
	_build_world()
	_build_actors()
	_build_puffs()
	_setup_audio()
	_sync(0.0)


func _setup_audio() -> void:
	var quiet := embedded
	_music = Sfx.music(Sfx.tracker_loop(MELODY, BASS, 138.0), tuning.music_db if not quiet else -80.0)
	add_child(_music)
	bug_music = _music
	if not quiet:
		_music.play()
	_sfx["go"] = Sfx.player(Sfx.blip(880.0, 0.3, 0.4, 6.0))
	_sfx["shot"] = Sfx.player(Sfx.thud(0.09, 0.55))
	_sfx["kill"] = Sfx.player(Sfx.blip(330.0, 0.16, 0.4, 14.0))
	_sfx["wound"] = Sfx.player(Sfx.blip(520.0, 0.08, 0.35, 20.0))
	_sfx["fire"] = Sfx.player(Sfx.thud(0.16, 0.5))
	_sfx["throw"] = Sfx.player(Sfx.blip(700.0, 0.12, 0.25, 9.0))
	_sfx["smash"] = Sfx.player(Sfx.hiss(0.18, 0.2))
	_sfx["boom"] = Sfx.player(Sfx.thud(0.4, 0.7))
	_sfx["hurt"] = Sfx.player(Sfx.blip(160.0, 0.3, 0.5, 7.0))
	_sfx["empty"] = Sfx.player(Sfx.blip(1400.0, 0.04, 0.25, 40.0))
	_sfx["reload"] = Sfx.player(Sfx.blip(240.0, 0.1, 0.3, 16.0))
	_sfx["loaded"] = Sfx.player(Sfx.blip(620.0, 0.1, 0.35, 14.0))
	_sfx["finish"] = Sfx.player(Sfx.blip(880.0, 0.5, 0.4, 5.0))
	for p in _sfx.values():
		(p as AudioStreamPlayer).volume_db = tuning.sfx_db if not quiet else -80.0
		add_child(p)


func _play(name: String) -> void:
	bug_play(_sfx[name])


# --- Мир ---------------------------------------------------------------------------------------

func _build_world() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed if record != null else 1, ":rail-look"))
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	for s in level.stops:
		lo = lo.min(Vector2(s.pos.x, s.pos.z))
		hi = hi.max(Vector2(s.pos.x, s.pos.z))
	var margin := level.shore_from + 16.0
	lo -= Vector2(margin, margin)
	hi += Vector2(margin, margin)
	var cell := 2.0
	var land := LowpolyTerrain.make(Vector3(lo.x, 0.0, lo.y), cell, ceili((hi.x - lo.x) / cell), ceili((hi.y - lo.y) / cell))
	for iz in land.nz + 1:
		for ix in land.nx + 1:
			land.set_h(ix, iz, level.height(lo.x + ix * cell, lo.y + iz * cell))
	land.build(lowpoly, lowpoly_texture("sand"), 3.0)
	var mid := (lo + hi) / 2.0
	lowpoly.add_plane(Vector3(mid.x, 0.0, mid.y), Vector2(520.0, 520.0), lowpoly_texture("water"), 6.0,
			{"uv_scroll": Vector2(0.02, 0.035), "affine": 0.0})
	# Укрытия и бочки с порохом.
	for c in level.covers:
		var name := "crate" if c.shape == RailLevel.Shape.CRATE else "barrel"
		var node := spawn_model("prop", name)
		node.position = c.pos - Vector3(0.0, 0.06, 0.0)
		node.rotation.y = c.yaw
		node.scale = Vector3.ONE * (c.height / lowpoly_set.model(name).bounds().size.y)
	for k in level.kegs:
		var node := spawn_model("prop", "keg")
		node.position = k.pos
		node.rotation.y = rng.randf_range(-PI, PI)
		node.scale = Vector3.ONE * 2.6
		keg_nodes.append(node)
	# Пальмы, камни и сундуки вдали от остановок: за укрытиями, а не перед ними.
	var placed := 0
	for tries in 400:
		if placed >= 26:
			break
		var p := Vector3(rng.randf_range(lo.x, hi.x), 0.0, rng.randf_range(lo.y, hi.y))
		var near := INF
		for s in level.stops:
			near = minf(near, Vector2(s.pos.x - p.x, s.pos.z - p.z).length())
		p.y = level.height(p.x, p.z)
		if near < 17.5 or p.y < 0.5:
			continue
		var prop := spawn_model("prop", DECOR[rng.randi_range(0, DECOR.size() - 1)])
		prop.position = p - Vector3(0.0, 0.1, 0.0)
		prop.rotation.y = rng.randf_range(-PI, PI)
		placed += 1
	# Флаг на финише.
	var last := level.stops[level.stops.size() - 1]
	var ahead := level.ground(last.pos + RailLevelGen._forward(last.yaw) * 4.0)
	var flag := spawn_model("finish", "flag")
	flag.position = ahead
	flag.rotation.y = last.yaw
	flag.scale = Vector3.ONE * 1.4
	# Пистолет в кадре: ствол смотрит туда же, куда прицел.
	gun = spawn_model("gun", "pistol", lowpoly.camera)
	gun.scale = Vector3.ONE * 0.42


func _build_actors() -> void:
	for i in level.foes.size():
		var foe := level.foes[i]
		var name := "captain" if foe.kind == RailLevel.Kind.CAPTAIN else ("hero" if foe.kind == RailLevel.Kind.HOSTAGE else "enemy")
		var model := spawn_model("enemy", name)
		model.visible = false
		foe_models.append(model)
		var shadow := lowpoly.add_shadow(0.4)
		shadow.visible = false
		foe_shadows.append(shadow)
		var bottle: LowpolyModel = null
		if foe.kind == RailLevel.Kind.THROWER and not model.pink and model.part(&"arm_r") != null:
			bottle = spawn_model("enemy", "bottle", model.part(&"arm_r"))
			bottle.position = Vector3(0.0, -0.75, 0.0)
		foe_bottles.append(bottle)
		_flash.append(0.0)
		_dead.append(0.0)


## Клубы дыма и искр: квадраты лицом к камере с вырезом по альфе, по кругу из запаса.
func _build_puffs() -> void:
	var img := Image.create(8, 8, false, Image.FORMAT_RGBA8)
	for y in 8:
		for x in 8:
			var d := Vector2(x - 3.5, y - 3.5).length()
			var edge := 3.7 if (x + y) % 2 == 0 else 3.3
			var shade := 0.72 if y > 4 else (1.0 if y < 3 and x < 5 else 0.86)
			img.set_pixel(x, y, Color(shade, shade, shade, 1.0 if d < edge else 0.0))
	_puff_tex = ImageTexture.create_from_image(img)
	var verts := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	for item: Array in [[-0.5, -0.5, 0, 1], [0.5, -0.5, 1, 1], [0.5, 0.5, 1, 0], [-0.5, -0.5, 0, 1], [0.5, 0.5, 1, 0], [-0.5, 0.5, 0, 0]]:
		LowpolyScreen.push(verts, normals, uvs, Vector3(item[0], item[1], 0.0), Vector3(0, 0, 1), Vector2(item[2], item[3]))
	LowpolyScreen.flip_last(verts, normals, uvs, 2)
	var mesh := LowpolyScreen._commit(verts, normals, uvs, _puff_material(WHITE))
	for i in PUFFS:
		var node := MeshInstance3D.new()
		node.mesh = mesh
		node.visible = false
		lowpoly.world.add_child(node)
		_puffs.append(node)
		_puff_age.append(-1.0)
		_puff_life.append(0.4)
		_puff_size.append(0.5)
		_puff_vel.append(Vector3.ZERO)


func _puff_material(color: Color) -> ShaderMaterial:
	return lowpoly.tex_material(_puff_tex, {"lit": 0.0, "fog_amount": 0.0, "tint": color})


func _puff(at: Vector3, vel: Vector3, color: Color, size: float, life: float) -> void:
	var i := _puff_next
	_puff_next = (_puff_next + 1) % _puffs.size()
	_puffs[i].position = at
	_puffs[i].set_surface_override_material(0, _puff_material(color))
	_puff_age[i] = 0.0
	_puff_life[i] = life
	_puff_size[i] = size
	_puff_vel[i] = vel


func _burst(at: Vector3, count: int, color: Color, size: float, speed: float) -> void:
	for k in count:
		var dir := Vector3(_shake_rng.randf_range(-1.0, 1.0), _shake_rng.randf_range(0.1, 1.0), _shake_rng.randf_range(-1.0, 1.0)).normalized()
		_puff(at, dir * speed * _shake_rng.randf_range(0.5, 1.0), color, size * _shake_rng.randf_range(0.7, 1.1),
				_shake_rng.randf_range(0.3, 0.55))


# --- Шаг -------------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	_hurt = maxf(_hurt - delta, 0.0)
	_boom = maxf(_boom - delta, 0.0)
	_shout_left = maxf(_shout_left - delta, 0.0)
	# Нажатия ловятся раз за кадр (с багом залипания из `Demo.bug_press`), правила берут их по одному.
	if not bot_driven() and running:
		var mouse := look_fire()
		if GameInput.a_just_pressed() or (mouse and not _mouse_down):
			bug_press(func() -> void: _want_fire = true)
		_mouse_down = mouse
		if GameInput.b_just_pressed() or (look_enabled and Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT)):
			bug_press(func() -> void: _want_reload = true)
	# Фризы в бою с догоном времени (`Demo.bug_frame`).
	bug_frame(delta, sim.phase != RailSim.Phase.COUNTDOWN, _step)


func _step(dt: float) -> void:
	_time += dt
	bug_input_tick()
	# Стоп-кадр на попадании: мир стоит, картинка живёт.
	var hold := minf(_stop_left, dt)
	_stop_left -= hold
	var left := dt - hold
	while left > 0.0001 and running:
		var h := minf(left, RailSim.DT)
		left -= h
		var fire := false
		var reload := false
		if bot_driven():
			sim.bot(active_bot_mode(), h)
			aim = sim.bot_aim
			fire = sim.bot_fire
			reload = sim.bot_reload
		else:
			# Прицел стрелками (с багом управления из прошлого), мышью и правым стиком.
			var axis := bug_axis(GameInput.axis())
			var tan_half := tan(deg_to_rad(tuning.fov) / 2.0)
			var turn := look_take(h)
			aim += Vector2(axis.x * 1.5 / tuning.aspect, axis.y) * tuning.aim_speed * h
			aim += Vector2(turn.x / (tan_half * tuning.aspect), turn.y / tan_half)
			aim = aim.clamp(Vector2(-tuning.aim_edge, -tuning.aim_edge), Vector2(tuning.aim_edge, tuning.aim_edge))
			fire = _want_fire
			reload = _want_reload
			_want_fire = false
			_want_reload = false
		sim.step(h, aim, fire, reload)
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
		&"shot":
			_play("shot")
			_kick = 1.0
			var kind: StringName = ev[2]
			var at: Vector3 = ev[1]
			if kind == &"cover":
				_burst(at, 3, DUST, 0.3, 1.6)
			elif kind == &"foe":
				_burst(at, 3, WHITE, 0.28, 1.8)
		&"kill":
			_play("kill")
			_flash[ev[1]] = tuning.hit_flash
			_stop_left = tuning.hit_stop
		&"wound":
			_play("wound")
			_flash[ev[1]] = tuning.hit_flash
			_stop_left = tuning.hit_stop
		&"hostage":
			_play("hurt")
			_hurt = 0.6
			_shake = 1.0
			_shout = "ПЛЕННЫЙ!"
			_shout_left = 1.2
		&"fire":
			_play("fire")
			_puff(sim.feet(ev[1]) + Vector3(0.0, 1.35, 0.0), Vector3(0.0, 0.8, 0.0), HOT, 0.5, 0.25)
		&"throw":
			_play("throw")
		&"smash":
			_play("smash")
			_burst(ev[1], 6, GLASS, 0.3, 2.4)
		&"boom":
			_play("boom")
			_boom = 0.25
			_shake = 0.7
			var keg := level.kegs[ev[1]]
			keg_nodes[ev[1]].visible = false
			_burst(keg.pos + Vector3(0.0, 0.6, 0.0), 9, HOT, 1.5, 4.5)
			_burst(keg.pos + Vector3(0.0, 0.8, 0.0), 7, WHITE, 1.2, 3.0)
		&"hurt":
			_play("hurt")
			_hurt = 0.6
			_shake = 1.0
		&"empty":
			_play("empty")
		&"reload":
			_play("reload")
		&"loaded":
			_play("loaded")
		&"finish":
			end_demo(true)
		&"dead", &"timeout":
			end_demo(false)


func _on_end(goal: bool) -> void:
	_music.stop()
	if goal:
		_play("finish")
	if AutoTest.enabled and not embedded:
		AutoTest.note("shooter lowpoly: %s за %.1f с, жизней %d, выстрелов %d, попаданий %d, убито %d из %d, в пленных %d" % [
				"дошёл" if goal else "не дошёл", sim.time, sim.lives, sim.shots, sim.hits, sim.kills, level.hostiles(), sim.hostage_hits])


func _result_caption() -> String:
	return "убито %d из %d · точность %d%% · жизней %d" % [sim.kills, level.hostiles(), int(round(100.0 * sim.hits / maxf(sim.shots, 1.0))),
			maxi(sim.lives, 0)]


# --- Картинка --------------------------------------------------------------------------------

func _sync(dt: float) -> void:
	# Камера: рельсы, шаг в переезде, тряска от ранения и взрыва.
	_shake = maxf(_shake - dt / tuning.shake, 0.0)
	var cam := sim.cam
	if sim.phase == RailSim.Phase.MOVE:
		cam.y += sin(_time * 9.0) * 0.035
	var jolt := Vector3(_shake_rng.randf_range(-1.0, 1.0), _shake_rng.randf_range(-1.0, 1.0), 0.0) * _shake * 0.07
	var basis := RailLevel.basis_of(sim.look)
	lowpoly.camera.position = cam + basis * jolt
	lowpoly.camera.basis = basis
	# Пистолет: ствол за прицелом, отдача, при перезарядке уходит вниз.
	_kick = maxf(_kick - dt * 7.0, 0.0)
	var dip := sin(clampf(1.0 - sim.reload_left / tuning.reload, 0.0, 1.0) * PI) if sim.reload_left > 0.0 else 0.0
	gun.position = Vector3(0.3 + aim.x * 0.08, -0.26 - aim.y * 0.05 - dip * 0.3, -0.62 + _kick * 0.07)
	gun.rotation = Vector3(-aim.y * 0.28 + _kick * 0.3 - dip * 0.9, -aim.x * 0.5, 0.0)
	for i in level.foes.size():
		_sync_foe(i, dt)
	# Бутылки в полёте.
	while bottle_nodes.size() < sim.bottles.size():
		var node := spawn_model("enemy", "bottle")
		node.scale = Vector3.ONE * 1.5
		bottle_nodes.append(node)
	for i in bottle_nodes.size():
		bottle_nodes[i].visible = i < sim.bottles.size()
		if i < sim.bottles.size():
			bottle_nodes[i].position = sim.bottle_pos(sim.bottles[i])
			bottle_nodes[i].rotation = Vector3(_time * 11.0, _time * 3.0, 0.0)
	# Клубы.
	var face := lowpoly.camera.basis.orthonormalized()
	for i in _puffs.size():
		if _puff_age[i] < 0.0:
			continue
		_puff_age[i] += dt
		var k := _puff_age[i] / _puff_life[i]
		if k >= 1.0:
			_puff_age[i] = -1.0
			_puffs[i].visible = false
			continue
		_puffs[i].position += _puff_vel[i] * dt
		_puff_vel[i] *= maxf(1.0 - 3.0 * dt, 0.0)
		var size := _puff_size[i] * (0.45 + 0.55 * minf(k * 3.0, 1.0)) * (1.0 - maxf(k - 0.6, 0.0) / 0.4)
		_puffs[i].basis = face.scaled(Vector3.ONE * maxf(size, 0.01))
		_puffs[i].visible = true


func _sync_foe(i: int, dt: float) -> void:
	var foe := level.foes[i]
	var actor := sim.actors[i]
	var model := foe_models[i]
	var shadow := foe_shadows[i]
	_flash[i] = maxf(_flash[i] - dt, 0.0)
	model.flash(_flash[i] > 0.0)
	if actor.state == RailSim.State.WAIT or actor.state == RailSim.State.GONE:
		model.visible = false
		shadow.visible = false
		return
	var at := sim.feet(i)
	var to_cam := sim.cam - at
	var yaw := atan2(-to_cam.x, -to_cam.z)
	shadow.visible = false
	if actor.state == RailSim.State.DEAD:
		# Падает на спину и уходит в песок.
		_dead[i] += dt
		model.visible = _dead[i] < 1.3
		model.position = at - Vector3(0.0, maxf(_dead[i] - 0.7, 0.0) * 1.6, 0.0)
		model.rotation = Vector3(-minf(_dead[i] / 0.28, 1.0) * PI * 0.5, yaw, 0.0)
		return
	model.visible = true
	model.position = at
	var runner := foe.kind == RailLevel.Kind.RUNNER
	if runner:
		shadow.visible = true
		shadow.position = at + Vector3(0.0, 0.05, 0.0)
		if actor.state != RailSim.State.OUT:
			# Бежит боком к камере: в кадр или из кадра.
			var run := foe.out - foe.hide
			if actor.state == RailSim.State.DUCK:
				run = -run
			yaw = atan2(-run.x, -run.z)
	model.rotation = Vector3(0.0, yaw, 0.0)
	if model.pink:
		return
	var arm_l := model.part(&"arm_l")
	var arm_r := model.part(&"arm_r")
	var bottle := foe_bottles[i]
	if runner and actor.state != RailSim.State.OUT:
		model.walk(_time * 14.0, 0.9)
		return
	model.walk(0.0, 0.0)
	var aiming := clampf(actor.timer / 0.2, 0.0, 1.0) if actor.state == RailSim.State.OUT else 0.0
	match foe.kind:
		RailLevel.Kind.HOSTAGE:
			arm_l.rotation.x = PI
			arm_r.rotation.x = PI
		RailLevel.Kind.THROWER:
			# Замах за голову, бросок в конце.
			var swing := clampf(actor.timer / foe.aim, 0.0, 1.0) if actor.state == RailSim.State.OUT else 0.0
			arm_r.rotation.x = lerpf(PI * 0.75, PI * 1.15, swing) if actor.state != RailSim.State.DUCK else PI * 0.4
			if bottle != null:
				bottle.visible = actor.state != RailSim.State.DUCK
		_:
			arm_r.rotation.x = aiming * PI * 0.5


func _to_px(ndc: Vector2) -> Vector2:
	return ((ndc + Vector2.ONE) / 2.0 * lowpoly.view).round()


func _draw_hud(canvas: CanvasItem) -> void:
	var dark := lowpoly.ink(LowpolyScreen.DARK).darkened(0.5)
	var red := lowpoly.ink(LowpolyScreen.DANGER)
	var gold := lowpoly.ink(LowpolyScreen.BONUS)
	var white := lowpoly.ink(LowpolyScreen.LIGHT)
	var view := lowpoly.view
	if sim == null:
		return
	# Кольца над врагами: сжимается, под конец краснеет и мигает.
	for i in sim.actors.size():
		var left := sim.ring(i)
		if left < 0.0:
			continue
		var at := sim.to_screen(sim.feet(i) + Vector3(0.0, 1.3, 0.0))
		if at.z <= 0.0:
			continue
		var center := _to_px(Vector2(at.x, at.y))
		var radius := lerpf(6.0, 24.0, left)
		var late := left < 0.35
		var color := red if late else gold
		if late and int(_time * 14.0) % 2 == 0:
			color = white
		canvas.draw_arc(center, radius, 0.0, TAU, 16, dark, 4.0)
		canvas.draw_arc(center, radius, 0.0, TAU, 16, color, 2.0)
		canvas.draw_arc(center, 6.0, 0.0, TAU, 10, Color(dark, 0.7), 1.0)
	# Бутылка в полёте: красная метка.
	for b in sim.bottles:
		var at := sim.to_screen(sim.bottle_pos(b))
		if at.z > 0.0:
			var c := _to_px(Vector2(at.x, at.y))
			var r := lerpf(5.0, 12.0, b.k)
			canvas.draw_rect(Rect2(c - Vector2(r, r), Vector2(r, r) * 2.0), dark, false, 3.0)
			canvas.draw_rect(Rect2(c - Vector2(r, r), Vector2(r, r) * 2.0), red if int(_time * 12.0) % 2 == 0 else white, false, 1.0)
	# Вспышки: ранение красным, взрыв белым.
	if _hurt > 0.0:
		canvas.draw_rect(Rect2(Vector2.ZERO, view), Color(red, _hurt * 0.8))
	if _boom > 0.0:
		canvas.draw_rect(Rect2(Vector2.ZERO, view), Color(white, _boom * 2.4))
	# Прицел.
	var p := _to_px(aim)
	for arm: Vector2 in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]:
		var a := p + arm * 4.0
		var b := p + arm * 9.0
		canvas.draw_rect(Rect2(a.min(b) - Vector2(1.5, 1.5), (a - b).abs() + Vector2(3, 3)), dark)
	for arm: Vector2 in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]:
		var a := p + arm * 4.0
		var b := p + arm * 9.0
		canvas.draw_rect(Rect2(a.min(b) - Vector2(0.5, 0.5), (a - b).abs() + Vector2(1, 1)), white)
	canvas.draw_rect(Rect2(p - Vector2(1.5, 1.5), Vector2(3, 3)), dark)
	canvas.draw_rect(Rect2(p - Vector2(0.5, 0.5), Vector2(1, 1)), red)
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
	# Путь сверху по центру: полоска с отметками остановок.
	var bar := Rect2(roundf(view.x / 2.0 - 70.0), 10.0, 140.0, 4.0)
	canvas.draw_rect(bar.grow(2.0), dark)
	canvas.draw_rect(bar, dark.lightened(0.25))
	canvas.draw_rect(Rect2(bar.position, Vector2(roundf(bar.size.x * sim.progress()), bar.size.y)), gold)
	for i in level.stops.size():
		var x := bar.position.x + roundf(bar.size.x * i / (level.stops.size() - 1))
		canvas.draw_rect(Rect2(x - 1.0, bar.position.y - 2.0, 2.0, bar.size.y + 4.0), white if i <= sim.stop else dark)
	# Счёт справа сверху.
	var score := "%d/%d" % [sim.kills, level.hostiles()]
	PixelFont16.draw(canvas, Vector2(view.x - 10.0 - PixelFont16.width(score, 1.0), 6.0), score, white, gold, dark, 1.0)
	# Обойма справа снизу.
	for i in tuning.clip:
		var o := Vector2(view.x - 14.0 - i * 9.0, view.y - 24.0)
		canvas.draw_rect(Rect2(o - Vector2.ONE, Vector2(7, 16)), dark)
		if i < sim.ammo:
			canvas.draw_rect(Rect2(o + Vector2(0, 4), Vector2(5, 10)), gold.darkened(0.2))
			canvas.draw_rect(Rect2(o + Vector2(0, 4), Vector2(2, 10)), gold)
			canvas.draw_rect(Rect2(o + Vector2(1, 0), Vector2(3, 4)), white)
		else:
			canvas.draw_rect(Rect2(o + Vector2(0, 4), Vector2(5, 10)), dark.lightened(0.2))
	if sim.reload_left > 0.0:
		var load := Rect2(view.x - 14.0 - (tuning.clip - 1) * 9.0, view.y - 32.0, tuning.clip * 9.0 - 4.0, 4.0)
		canvas.draw_rect(load.grow(1.0), dark)
		canvas.draw_rect(Rect2(load.position, Vector2(roundf(load.size.x * (1.0 - sim.reload_left / tuning.reload)), load.size.y)), white)
	elif sim.ammo <= 0 and int(_time * 6.0) % 2 == 0:
		var text := "ПУСТО"
		PixelFont16.draw(canvas, Vector2(view.x - 12.0 - PixelFont16.width(text, 1.0), view.y - 44.0), text, white, red, dark, 1.0)
	# Отсчёт и окрик.
	if sim.phase == RailSim.Phase.COUNTDOWN:
		var count := str(ceili(sim.countdown))
		PixelFont16.draw(canvas, Vector2(roundf(view.x / 2.0 - PixelFont16.width(count, 5.0) / 2.0), roundf(view.y / 2.0 - 40.0)), count,
				white, gold, dark, 5.0)
	elif _shout_left > 0.0:
		PixelFont16.draw(canvas, Vector2(roundf(view.x / 2.0 - PixelFont16.width(_shout, 2.0) / 2.0), roundf(view.y / 2.0 - 50.0)), _shout,
				white, red, dark, 2.0)
