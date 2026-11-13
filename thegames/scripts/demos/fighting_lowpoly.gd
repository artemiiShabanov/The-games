extends Demo
## Демка файтинг × low poly, каталог `docs/specs/demos_catalog.md`: «один на один сбоку в
## объёме» (#116, решение 2026-11-04, приёмы сложности 2026-11-13, образцы Tekken, Virtua
## Fighter, Battle Arena Toshinden; плейтест 2026-11-13: без приседа, удар ногой на второй
## кнопке). Матрос против капитана на палубе, вид сбоку. Влево и вправо ходьба, A удар рукой
## (попавший продолжается связкой до трёх), B удар ногой (дольше, дальше и больнее, им можно
## закончить связку), вниз блок, вверх шаг в глубину. Капитан бьёт связками по плану из сида,
## замах читается: рука отведена назад, колено поднято или обе руки над головой с красным
## знаком, это сильный удар, который блок не держит. Шаг в глубину уводит от любого удара и открывает
## бок соперника: удар сбоку в полтора раза сильнее. Отвечать можно, когда связка кончилась в
## блок или мимо; удар героя мимо или в блок оставляет открытым героя. Бой до нокаута.
## План из `SparPlanGen` по сиду записи. Правила и боты живут в `SparSim` (без окна, им же
## проверяются сто сидов); демка ведёт его шагами по 1/60 с, рисует и озвучивает его события.
##
## Общие баги (#44) и баг технологии `mesh_holes` живут в `Demo` и `LowpolyScreen`, демка только
## зовёт хуки: фризы `bug_frame`, заикание музыки, ввод с опозданием, розовые заглушки вместо
## соперника и реквизита. Баги жанра и баланса для этой демки включит #117.

const PLACEHOLDER_SLOTS: Array[String] = ["rival", "prop", "finish"]
const MELODY := [0, 0, 3, null, 5, 3, 0, null, 7, 7, 10, null, 8, 7, 5, null,
	0, 0, 3, 5, 7, null, 5, 3, 8, 7, 5, 3, 2, null, 0, null]
const BASS := [-12, -12, -12, -12, -7, -7, -7, -7, -9, -9, -9, -9, -5, -5, -7, -7]
const WHITE := Color(0.95, 0.93, 0.86)
const HOT := Color(1.0, 0.6, 0.2)
const PUFFS := 24

var tuning: FightingLowpolyTuning
var plan: SparPlan
var sim: SparSim
var models: Array[LowpolyModel] = []
var shadows: Array[MeshInstance3D] = []

var _time := 0.0
var _stop_left := 0.0
var _flash := [0.0, 0.0]
var _ko := [0.0, 0.0]
var _walk := [0.0, 0.0]
var _last_x := [0.0, 0.0]
var _body_y := [0.0, 0.0]
var _leg_y := [0.0, 0.0]
## Здоровье, каким его показывает белый след свежего урона.
var _trail := [1.0, 1.0]
var _shake := 0.0
var _popup := ""
var _popup_left := 0.0
var _popup_good := true
var _ko_wait := 0.0
var _ko_goal := false
var _want_strike := false
var _want_kick := false
var _want_step := 0
var _was_up := false
## Углы суставов бойцов сейчас (плавно идут к позе) и какой рукой бьёт следующий удар.
var _joints: Array[Dictionary] = [{}, {}]
var _lead := [false, false]
var _rng := RandomNumberGenerator.new()
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
	tuning = FightingLowpolyTuning.load_default()
	plan = SparPlanGen.generate(record.seed if record != null else 1)
	sim = SparSim.create(plan, tuning)
	# Баги жанра и баланса (#117): удары сквозь соперника, невесомость, нокаут от чиха,
	# бессмертный соперник.
	if has_bug(&"ghost_hits"):
		sim.ghost_every = maxi(int(bug_param(&"ghost_hits", &"pass_every", 2.0)), 1)
	if has_bug(&"wild_physics"):
		sim.launch = bug_param(&"wild_physics", &"spar_launch", 2.2)
	sim.sneeze = has_bug(&"sneeze_enemies")
	sim.immortal = has_bug(&"unreachable_coins")
	lowpoly_screen(_draw_hud)
	lowpoly.camera.fov = 40.0
	_build_world()
	_build_puffs()
	_setup_audio()
	_sync(0.0)


func _setup_audio() -> void:
	var quiet := embedded
	_music = Sfx.music(Sfx.tracker_loop(MELODY, BASS, 144.0), tuning.music_db if not quiet else -80.0)
	add_child(_music)
	bug_music = _music
	if not quiet:
		_music.play()
	_sfx["go"] = Sfx.player(Sfx.blip(880.0, 0.3, 0.4, 6.0))
	_sfx["swing"] = Sfx.player(Sfx.hiss(0.1, 0.14))
	_sfx["heavy"] = Sfx.player(Sfx.blip(180.0, 0.35, 0.4, 5.0))
	_sfx["hit"] = Sfx.player(Sfx.thud(0.12, 0.6))
	_sfx["hurt"] = Sfx.player(Sfx.thud(0.2, 0.7))
	_sfx["block"] = Sfx.player(Sfx.blip(900.0, 0.07, 0.35, 26.0))
	_sfx["whiff"] = Sfx.player(Sfx.hiss(0.14, 0.1))
	_sfx["step"] = Sfx.player(Sfx.blip(420.0, 0.08, 0.25, 16.0))
	_sfx["ko"] = Sfx.player(Sfx.thud(0.4, 0.7))
	_sfx["finish"] = Sfx.player(Sfx.blip(880.0, 0.5, 0.4, 5.0))
	for p in _sfx.values():
		(p as AudioStreamPlayer).volume_db = tuning.sfx_db if not quiet else -80.0
		add_child(p)


func _play(name: String) -> void:
	bug_play(_sfx[name])


# --- Мир ---------------------------------------------------------------------------------------

func _build_world() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed if record != null else 1, ":spar-look"))
	lowpoly.add_plane(Vector3(0.0, -1.4, 0.0), Vector2(520.0, 520.0), lowpoly_texture("water"), 6.0,
			{"uv_scroll": Vector2(0.02, 0.035), "affine": 0.0})
	# Палуба и борт позади бойцов.
	lowpoly.add_box(Vector3(0.0, -0.7, -0.6), Vector3(tuning.arena_half * 2.0 + 3.0, 1.4, 8.4), lowpoly_texture("planks"), 2.0)
	lowpoly.add_box(Vector3(0.0, 0.45, -4.6), Vector3(tuning.arena_half * 2.0 + 3.0, 0.9, 0.25), lowpoly_texture("planks"), 1.5)
	# Реквизит вдоль борта: за спинами бойцов, в бой не лезет.
	var x := -tuning.arena_half - 0.6
	while x < tuning.arena_half + 0.8:
		var name: String = ["barrel", "crate", "barrel", "cannon", "chest", "crate"][rng.randi_range(0, 5)]
		var prop := spawn_model("prop", name)
		prop.position = Vector3(x, 0.0, rng.randf_range(-4.0, -2.9))
		prop.rotation.y = rng.randf_range(-0.6, 0.6) + (PI if name == "cannon" else 0.0)
		x += rng.randf_range(1.4, 2.6)
	var flag := spawn_model("finish", "flag")
	flag.position = Vector3(tuning.arena_half + 0.4, 0.0, -3.9)
	flag.scale = Vector3.ONE * 1.05
	var tower := spawn_model("prop", "lighthouse")
	tower.position = Vector3(-14.0, -1.4, -34.0)
	for i in 2:
		var model := spawn_model("hero" if i == 0 else "rival", "hero" if i == 0 else "captain")
		models.append(model)
		shadows.append(lowpoly.add_shadow(0.45))
		var body := model.part(&"body") if not model.pink else null
		_body_y[i] = body.position.y if body != null else 0.0
		_leg_y[i] = model.part(&"leg_l").position.y if body != null else 0.0
	_last_x = [sim.hero.x, sim.rival.x]


## Искры и пыль ударов: квадраты лицом к камере с вырезом по альфе.
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


func _burst(at: Vector3, count: int, color: Color, size: float, speed: float) -> void:
	for k in count:
		var i := _puff_next
		_puff_next = (_puff_next + 1) % _puffs.size()
		var dir := Vector3(_rng.randf_range(-1.0, 1.0), _rng.randf_range(-0.3, 1.0), _rng.randf_range(-0.5, 1.0)).normalized()
		_puffs[i].position = at
		_puffs[i].set_surface_override_material(0, _puff_material(color))
		_puff_age[i] = 0.0
		_puff_life[i] = _rng.randf_range(0.22, 0.4)
		_puff_size[i] = size * _rng.randf_range(0.7, 1.1)
		_puff_vel[i] = dir * speed * _rng.randf_range(0.5, 1.0)


# --- Шаг -------------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	_popup_left = maxf(_popup_left - delta, 0.0)
	if _ko_wait > 0.0:
		_ko_wait -= delta
		if _ko_wait <= 0.0:
			end_demo(_ko_goal)
			return
	# Нажатия ловятся раз за кадр (с багом залипания из `Demo.bug_press`), правила берут их по одному.
	if not bot_driven() and running:
		var axis := GameInput.axis()
		if GameInput.a_just_pressed():
			bug_press(func() -> void: _want_strike = true)
		if GameInput.b_just_pressed():
			bug_press(func() -> void: _want_kick = true)
		var up := axis.y < -0.5
		if up and not _was_up:
			bug_press(func() -> void: _want_step = -1)
		_was_up = up
	# Фризы в бою с догоном времени (`Demo.bug_frame`).
	bug_frame(delta, sim.phase == SparSim.Phase.FIGHT, _step)


func _step(dt: float) -> void:
	_time += dt
	bug_input_tick()
	# Стоп-кадр на попадании: мир стоит, картинка живёт.
	var hold := minf(_stop_left, dt)
	_stop_left -= hold
	var left := dt - hold
	while left > 0.0001 and running:
		var h := minf(left, SparSim.DT)
		left -= h
		var c := SparSim.Controls.new()
		if bot_driven():
			sim.bot(active_bot_mode())
			c = sim.bot_controls
		else:
			# Ходьба и присед с багом управления из прошлого (`Demo.bug_axis`).
			var axis := bug_axis(GameInput.axis())
			c.move = axis.x
			c.block = axis.y > 0.5
			c.strike = _want_strike
			c.kick = _want_kick
			c.step = _want_step
			_want_strike = false
			_want_kick = false
			_want_step = 0
		sim.step(h, c)
		for ev in sim.events:
			_on_event(ev)
		sim.events.clear()
		if _stop_left > 0.0:
			break
	_sync(dt)


func _fighter(i: int) -> SparSim.Fighter:
	return sim.hero if i == 0 else sim.rival


## Событие правил: звук, эффект, конец демки.
func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"go":
			_play("go")
		&"windup":
			_play("heavy" if ev[1] == 1 and ev[2] == SparPlan.Move.HEAVY else "swing")
			if ev[2] == SparPlan.Move.PUNCH:
				_lead[ev[1]] = not _lead[ev[1]]
		&"hit":
			var who: int = ev[1]
			var f := _fighter(who)
			_play("hurt" if who == 0 else "hit")
			_flash[who] = tuning.hit_flash
			_stop_left = tuning.hit_stop * (1.6 if ev[4] or ev[3] else 1.0)
			_shake = 1.0 if who == 0 else 0.5
			var kick := _fighter(1 - who).move == SparPlan.Move.KICK
			_burst(Vector3(f.x, 1.0 if kick else 1.4, f.z + 0.3), 7 if ev[4] or ev[3] else 4, HOT if ev[4] or ev[3] else WHITE, 0.4, 2.6)
			if ev[3]:
				_say("СБОКУ!", true)
			elif ev[4] and who == 0:
				_say("СИЛЬНЫЙ", false)
		&"block":
			_play("block")
			var f := _fighter(ev[1])
			_burst(Vector3(f.x + (0.35 if ev[1] == 0 else -0.35), 1.2, 0.3), 3, WHITE, 0.25, 1.6)
			if ev[1] == 0:
				_say("БЛОК", true)
		&"ghost":
			_play("whiff")
			_say("НАСКВОЗЬ", false)
		&"whiff":
			_play("whiff")
			if ev[1] == 1 and sim.rival.flank > 0.0:
				_say("УШЁЛ", true)
		&"step":
			_play("step")
		&"tired":
			_say("ВЫДОХСЯ", true)
		&"ko":
			# Итог не сразу: нокаут сначала виден, боец падает.
			_play("ko")
			_stop_left = 0.25
			_shake = 1.0
			_ko_goal = ev[1] == 1
			_ko_wait = tuning.ko_seconds
		&"timeout":
			end_demo(false)


func _say(text: String, good: bool) -> void:
	_popup = text
	_popup_good = good
	_popup_left = 0.7


func _on_end(goal: bool) -> void:
	_music.stop()
	if goal:
		_play("finish")
	if AutoTest.enabled and not embedded:
		AutoTest.note("fighting lowpoly: %s за %.1f с, здоровье %d против %d, попал %d (сбоку %d), блоков %d, уходов %d, пропустил %d" % [
				"победил" if goal else "проиграл", sim.time, sim.hero.hp, sim.rival.hp, sim.hero_hits, sim.flank_hits, sim.blocks, sim.dodges,
				sim.taken])


func _result_title(goal: bool) -> String:
	return "нокаут" if goal else "проиграл"


func _result_caption() -> String:
	return "%d с · здоровья %d · сбоку %d · блоков %d" % [int(round(sim.time)), maxi(sim.hero.hp, 0), sim.flank_hits, sim.blocks]


# --- Картинка --------------------------------------------------------------------------------

func _sync(dt: float) -> void:
	_shake = maxf(_shake - dt * 5.0, 0.0)
	# Камера сбоку: смотрит на середину между бойцами, слегка поворачивается за ними и за
	# шагом в глубину.
	var mid := (sim.hero.x + sim.rival.x) / 2.0
	var wide := clampf((sim.gap() - 1.3) * 0.5, 0.0, 1.6)
	var eye := Vector3(mid * 0.55 + sim.hero.z * 0.5, 1.45, 4.7 + wide)
	eye += Vector3(_rng.randf_range(-1.0, 1.0), _rng.randf_range(-1.0, 1.0), 0.0) * _shake * 0.05
	lowpoly.camera.position = eye
	lowpoly.camera.basis = Basis.looking_at(Vector3(mid, 1.0, 0.0) - eye)
	for i in 2:
		_pose(i, dt)
		var maxhp := float(tuning.hero_hp if i == 0 else tuning.rival_hp)
		var now := maxf(_fighter(i).hp, 0) / maxhp
		_trail[i] = maxf(now, _trail[i] - dt * 0.35)
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
		_puff_vel[i] *= maxf(1.0 - 4.0 * dt, 0.0)
		var size := _puff_size[i] * (0.45 + 0.55 * minf(k * 3.0, 1.0)) * (1.0 - maxf(k - 0.6, 0.0) / 0.4)
		_puffs[i].basis = face.scaled(Vector3.ONE * maxf(size, 0.01))
		_puffs[i].visible = true


## Поза бойца: углы плеч, локтей, бёдер и коленей по состоянию; суставы идут к позе плавно
## (анимации без скелета). Углы в радианах: плечо и бедро плюс это вперёд, локоть плюс это
## сгиб, колено минус это сгиб.
func _pose(i: int, dt: float) -> void:
	var f := _fighter(i)
	var model := models[i]
	var facing := 1.0 if i == 0 else -1.0
	_flash[i] = maxf(_flash[i] - dt, 0.0)
	model.flash(_flash[i] > 0.0)
	var at := Vector3(f.x, 0.0, f.z)
	shadows[i].position = at + Vector3(0.0, 0.03, 0.0)
	var walked := absf(f.x - float(_last_x[i]))
	_last_x[i] = f.x
	_walk[i] = float(_walk[i]) + walked * 7.0
	var p := f.progress()
	# Боевая стойка: кулаки у подбородка, колени согнуты, одна нога впереди.
	var pose := {&"arm_l": 0.95, &"fore_l": 1.55, &"arm_r": 0.55, &"fore_r": 1.75, &"leg_l": 0.38, &"shin_l": -0.55,
			&"leg_r": -0.3, &"shin_r": -0.3, &"lean": 0.0, &"twist": 0.0, &"drop": 0.07}
	# Бьющая рука чередуется от удара к удару.
	var arm := &"arm_l" if _lead[i] else &"arm_r"
	var fore := &"fore_l" if _lead[i] else &"fore_r"
	var turn := -1.0 if _lead[i] else 1.0
	var speed := 22.0
	match f.state:
		SparSim.State.IDLE:
			if f.block:
				# Блок: предплечья стоят перед лицом, локти прижаты.
				pose.merge({&"arm_l": 1.35, &"fore_l": 2.05, &"arm_r": 1.25, &"fore_r": 2.15, &"lean": 0.1, &"drop": 0.12}, true)
			elif walked > 0.0005:
				var phase := float(_walk[i])
				pose.merge({&"leg_l": 0.2 + sin(phase) * 0.5, &"shin_l": -0.35 - maxf(cos(phase), 0.0) * 0.7,
						&"leg_r": -0.1 - sin(phase) * 0.5, &"shin_r": -0.35 - maxf(-cos(phase), 0.0) * 0.7}, true)
		SparSim.State.STEP:
			var phase := _time * 16.0
			pose.merge({&"leg_l": 0.3 + sin(phase) * 0.45, &"shin_l": -0.8, &"leg_r": -0.3 - sin(phase) * 0.45, &"shin_r": -0.8,
					&"drop": 0.16}, true)
		SparSim.State.WINDUP:
			match f.move:
				SparPlan.Move.PUNCH:
					# Рука отведена назад, локоть согнут, корпус закручен.
					pose.merge({arm: -0.75, fore: 2.2, &"twist": 0.45 * turn, &"lean": 0.08}, true)
				SparPlan.Move.KICK:
					# Колено поднято к груди.
					pose.merge({&"leg_r": 1.45, &"shin_r": -1.9, &"lean": 0.2, &"leg_l": 0.1, &"shin_l": -0.25}, true)
				SparPlan.Move.HEAVY:
					# Обе руки занесены над головой.
					pose.merge({&"arm_l": 2.9, &"fore_l": 0.5, &"arm_r": 2.9, &"fore_r": 0.5, &"lean": 0.32, &"drop": 0.0}, true)
					speed = 9.0
		SparSim.State.RECOVER:
			# Удар нанесён: конечность выпрямлена, потом возвращается в стойку.
			if p < 0.55:
				speed = 45.0
				match f.move:
					SparPlan.Move.PUNCH:
						pose.merge({arm: 1.55, fore: 0.05, &"twist": -0.4 * turn, &"lean": -0.16}, true)
					SparPlan.Move.KICK:
						pose.merge({&"leg_r": 1.5, &"shin_r": -0.05, &"lean": 0.36, &"leg_l": 0.05, &"shin_l": -0.15,
								&"arm_l": 0.6, &"arm_r": -0.3}, true)
					SparPlan.Move.HEAVY:
						pose.merge({&"arm_l": 1.15, &"fore_l": 0.1, &"arm_r": 1.15, &"fore_r": 0.1, &"lean": -0.4, &"drop": 0.16}, true)
		SparSim.State.STUN:
			pose.merge({&"arm_l": -0.3, &"fore_l": 0.8, &"arm_r": -0.5, &"fore_r": 0.6, &"lean": 0.42 * sin(PI * minf(p, 1.0)),
					&"shin_l": -0.8, &"shin_r": -0.6}, true)
			speed = 30.0
		SparSim.State.KO:
			_ko[i] = float(_ko[i]) + dt
			var k := minf(float(_ko[i]) / 0.5, 1.0)
			pose = {&"arm_l": -0.9, &"fore_l": 0.3, &"arm_r": -0.6, &"fore_r": 0.5, &"leg_l": 0.25, &"shin_l": -0.4, &"leg_r": 0.05,
					&"shin_r": -0.15, &"lean": PI * 0.5 * k, &"twist": 0.0, &"drop": 0.1 * k}
			speed = 40.0
	var now: Dictionary = _joints[i]
	var blend := clampf(speed * dt, 0.0, 1.0) if not now.is_empty() else 1.0
	for key: StringName in pose:
		now[key] = lerpf(float(now.get(key, pose[key])), float(pose[key]), blend)
	# Невесомость: от удара боец летит по дуге.
	model.position = at + Vector3(0.0, sin(PI * clampf(f.air / tuning.stun, 0.0, 1.0)) * 1.4, 0.0)
	model.rotation = Vector3(float(now[&"lean"]), -facing * PI / 2.0 + float(now[&"twist"]) * facing, 0.0)
	if model.pink:
		return
	for key: StringName in [&"arm_l", &"fore_l", &"arm_r", &"fore_r", &"leg_l", &"shin_l", &"leg_r", &"shin_r"]:
		var part := model.part(key)
		if part != null:
			part.rotation.x = float(now[key])
	# Корпус опускается вместе с согнутыми коленями и слегка дышит.
	var drop := float(now[&"drop"])
	model.part(&"body").position.y = float(_body_y[i]) - drop + sin(_time * 3.0 + i) * 0.01
	for key: StringName in [&"leg_l", &"leg_r"]:
		model.part(key).position.y = float(_leg_y[i]) - drop


## Точка мира в пикселях экрана демки.
func _px(p: Vector3) -> Vector2:
	var cam := lowpoly.camera
	var local := cam.basis.inverse() * (p - cam.position)
	if local.z > -0.1:
		return Vector2.INF
	var view := lowpoly.view
	var half := tan(deg_to_rad(cam.fov) / 2.0)
	return Vector2(view.x / 2.0 + local.x / -local.z / half * view.y / 2.0, view.y / 2.0 - local.y / -local.z / half * view.y / 2.0)


func _draw_hud(canvas: CanvasItem) -> void:
	if sim == null:
		return
	var dark := lowpoly.ink(LowpolyScreen.DARK).darkened(0.5)
	var red := lowpoly.ink(LowpolyScreen.DANGER)
	var gold := lowpoly.ink(LowpolyScreen.BONUS)
	var white := lowpoly.ink(LowpolyScreen.LIGHT)
	var view := lowpoly.view
	# Полосы здоровья: герой слева, соперник справа, убывают к середине; белый след свежего урона.
	var width := roundf(view.x / 2.0 - 34.0)
	for i in 2:
		var f := _fighter(i)
		var maxhp := float(tuning.hero_hp if i == 0 else tuning.rival_hp)
		var now := maxf(f.hp, 0) / maxhp
		var bar := Rect2(12.0 if i == 0 else view.x - 12.0 - width, 20.0, width, 9.0)
		canvas.draw_rect(bar.grow(2.0), dark)
		canvas.draw_rect(bar, dark.lightened(0.22))
		for layer: Array in [[float(_trail[i]), white], [now, gold if i == 0 else red]]:
			var w := roundf(bar.size.x * float(layer[0]))
			var x := bar.position.x if i == 0 else bar.end.x - w
			canvas.draw_rect(Rect2(x, bar.position.y, w, bar.size.y), layer[1])
		var w_now := roundf(bar.size.x * now)
		canvas.draw_rect(Rect2(bar.position.x if i == 0 else bar.end.x - w_now, bar.position.y, w_now, 3.0), Color(white, 0.45))
		var name := "МАТРОС" if i == 0 else "КАПИТАН"
		PixelFont16.draw(canvas, Vector2(bar.position.x if i == 0 else bar.end.x - PixelFont16.width(name, 1.0), 4.0), name, white, white, dark, 1.0)
	# Сильный удар: красный знак над соперником, пока он замахивается.
	if sim.rival.state == SparSim.State.WINDUP and sim.rival.move == SparPlan.Move.HEAVY:
		var at := _px(Vector3(sim.rival.x, 2.35, sim.rival.z))
		if at != Vector2.INF and int(_time * 10.0) % 2 == 0:
			PixelFont16.draw(canvas, Vector2(roundf(at.x - PixelFont16.width("!", 3.0) / 2.0), roundf(at.y - 22.0)), "!", white, red, dark, 3.0)
	# Соперник открыт сбоку: отметка над ним.
	if sim.rival.flank > 0.0 and sim.phase == SparSim.Phase.FIGHT:
		var at := _px(Vector3(sim.rival.x, 2.2, sim.rival.z))
		if at != Vector2.INF:
			var w := roundf(26.0 * sim.rival.flank / tuning.flank_seconds)
			canvas.draw_rect(Rect2(roundf(at.x - 14.0), roundf(at.y - 3.0), 28.0, 6.0), dark)
			canvas.draw_rect(Rect2(roundf(at.x - 13.0), roundf(at.y - 2.0), w, 4.0), gold)
	if sim.phase == SparSim.Phase.COUNTDOWN:
		var text := str(ceili(sim.countdown))
		PixelFont16.draw(canvas, Vector2(roundf(view.x / 2.0 - PixelFont16.width(text, 5.0) / 2.0), roundf(view.y / 2.0 - 50.0)), text,
				white, gold, dark, 5.0)
	elif _popup_left > 0.0:
		PixelFont16.draw(canvas, Vector2(roundf(view.x / 2.0 - PixelFont16.width(_popup, 2.0) / 2.0), 44.0), _popup, white,
				gold if _popup_good else red, dark, 2.0)
