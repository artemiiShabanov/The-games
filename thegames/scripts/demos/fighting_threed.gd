extends Demo
## Демка файтинг × «продвинутые», каталог `docs/specs/demos_catalog.md`: «дуэль на саблях»
## (#125, решение и приёмы сложности 2026-11-13; образцы For Honor, Mount & Blade, Sekiro).
## Матрос против капитана на палубе, камера из-за плеча героя. Влево, вверх, вправо ставят
## саблю с этой стороны: это и блок, и сторона удара. A удар, B шаг назад. Замах капитана
## показывает сторону: блок надо держать там же; финт на полпути меняет сторону, связку из
## двух-трёх ударов надо отбить целиком, от выпада (блок его не держит) уходят шагом назад.
## После связки капитан открыт; в паузе он держит стойку, бить надо туда, где сабли нет. План
## капитана из `SaberPlanGen` по сиду записи; правила и боты живут в `SaberSim` (без окна, им
## же проверяются сто сидов), демка ведёт его шагами по 1/60 с, рисует и озвучивает события.
##
## Общие баги (#44) и баг технологии `camera_clip` живут в `Demo` и `ThreedScreen`, демка только
## зовёт хуки. Баги жанра и баланса для этой демки включит #126.

const PLACEHOLDER_SLOTS: Array[String] = ["hero", "enemy", "prop"]
const MELODY := [0, 3, 5, 7, 10, 7, 5, 3, 0, 3, 5, 8, 7, 5, 3, null,
	0, 3, 5, 7, 10, 12, 10, 7, 8, 7, 5, 3, 2, 3, 0, null]
const BASS := [-12, -12, -5, -5, -9, -9, -5, -5, -4, -4, -9, -9, -7, -7, -5, -5]
const HERO_AT := Vector3(-0.5, 0.0, 1.0)
const RIVAL_AT := Vector3(0.12, 0.0, -0.8)
const SIDE_NAMES := ["СЛЕВА", "СВЕРХУ", "СПРАВА"]
## Стойки правой руки с саблей по сторонам бойца (его слева, сверху, справа): плечо, локоть,
## наклон сабли в кисти.
const GUARDS := [
	{"arm": Vector3(1.05, 0.0, -0.75), "fore": 1.25, "blade": Vector3(0.1, 0.0, 0.35)},
	{"arm": Vector3(2.25, 0.0, 0.25), "fore": 0.85, "blade": Vector3(0.2, 0.0, 1.45)},
	{"arm": Vector3(0.8, 0.0, 0.55), "fore": 1.3, "blade": Vector3(0.1, 0.0, -0.35)},
]
## Удар: рука вытянута вперёд, сабля смотрит в соперника.
const CUT := {"arm": Vector3(1.45, 0.0, 0.0), "fore": 0.25, "blade": Vector3(1.15, 0.0, 0.0)}

var tuning: FightingThreedTuning
var plan: SaberPlan
var sim: SaberSim
var hero: LowpolyModel
var rival: LowpolyModel
var hero_blade: Node3D
var rival_blade: Node3D
var spark: MeshInstance3D

var _time := 0.0
var _stop_left := 0.0
var _want_strike := false
var _want_back := false
var _shake := 0.0
var _hero_flash := 0.0
var _rival_flash := 0.0
var _hero_cut := 0.0
var _rival_cut := 0.0
var _rival_cut_side := 1
var _spark_left := 0.0
var _note := ""
var _note_left := 0.0
var _note_color := Color.WHITE
var _music: AudioStreamPlayer
var _sfx := {}


func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _on_start() -> void:
	tuning = FightingThreedTuning.load_default()
	plan = SaberPlanGen.generate(record.seed if record != null else 1, tuning)
	sim = SaberSim.create(plan, tuning)
	lowpoly_screen(_draw_hud)
	lowpoly.camera.fov = 47.0
	_build_world()
	_setup_audio()
	_sync(0.0)


func _setup_audio() -> void:
	var quiet := embedded
	_music = Sfx.music(Sfx.tracker_loop(MELODY, BASS, 136.0), tuning.music_db if not quiet else -80.0)
	add_child(_music)
	bug_music = _music
	if not quiet:
		_music.play()
	_sfx["go"] = Sfx.player(Sfx.blip(880.0, 0.3, 0.4, 6.0))
	_sfx["swing"] = Sfx.player(Sfx.hiss(0.12, 0.2))
	_sfx["clang"] = Sfx.player(Sfx.blip(2300.0, 0.12, 0.4, 16.0))
	_sfx["hit"] = Sfx.player(Sfx.thud(0.12, 0.5))
	_sfx["hurt"] = Sfx.player(Sfx.thud(0.2, 0.65))
	_sfx["warn"] = Sfx.player(Sfx.blip(330.0, 0.25, 0.35, 5.0))
	_sfx["step"] = Sfx.player(Sfx.hiss(0.1, 0.12))
	_sfx["finish"] = Sfx.player(Sfx.blip(880.0, 0.5, 0.4, 5.0))
	for p in _sfx.values():
		(p as AudioStreamPlayer).volume_db = tuning.sfx_db if not quiet else -80.0
		add_child(p)


func _play(name: String) -> void:
	bug_play(_sfx[name])


# --- Мир ---------------------------------------------------------------------------------------

func _add(mesh: Mesh, at: Vector3, parent: Node3D = null, material: Material = null) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.position = at
	if material != null:
		node.material_override = material
	(parent if parent != null else lowpoly.world).add_child(node)
	return node


func _box(size: Vector3) -> BoxMesh:
	var mesh := BoxMesh.new()
	mesh.size = size
	return mesh


func _metal(color: Color, rough := 0.3) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.metallic = 0.85
	m.roughness = rough
	return m


## Сабля: рукоять, гарда и клинок вдоль оси кисти (клинок смотрит вверх, когда предплечье
## вытянуто вперёд). Висит на кости правой кисти.
func _saber(model: LowpolyModel, gold: bool) -> Node3D:
	var holder := Node3D.new()
	var rig := model as RigModel
	if rig == null or not rig.has_joint(&"hand_r"):
		model.add_child(holder)
		holder.position = Vector3(0.25, 1.1, -0.3)
		return holder
	var hand := BoneAttachment3D.new()
	rig.skeleton.add_child(hand)
	hand.bone_name = "hand_r"
	hand.add_child(holder)
	holder.position = Vector3(0.0, -0.07, 0.0)
	var pivot := Node3D.new()
	pivot.rotation.x = -PI / 2.0
	holder.add_child(pivot)
	var grip := CylinderMesh.new()
	grip.top_radius = 0.022
	grip.bottom_radius = 0.022
	grip.height = 0.16
	grip.radial_segments = 8
	_add(grip, Vector3.ZERO, pivot, lowpoly.tex_material(lowpoly_texture("planks"), {"tint": Color(0.45, 0.3, 0.2)}))
	_add(_box(Vector3(0.16, 0.025, 0.07)), Vector3(0.0, 0.09, 0.0), pivot, _metal(Color(0.9, 0.7, 0.25) if gold else Color(0.5, 0.5, 0.55)))
	_add(_box(Vector3(0.045, 0.86, 0.012)), Vector3(0.0, 0.53, 0.0), pivot, _metal(Color(0.86, 0.88, 0.92), 0.18))
	return holder


func _build_world() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed if record != null else 1, ":saber-look"))
	var screen := lowpoly as ThreedScreen
	screen.add_water(Vector3(0.0, -3.2, 0.0), 1200.0)
	# Палуба: настил, борта, мачта, реквизит за спиной капитана.
	var planks := lowpoly_texture("planks")
	var deck := lowpoly.add_box(Vector3(0.0, -0.25, -2.0), Vector3(9.0, 0.5, 26.0), planks, 5.0)
	deck.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for side: float in [-1.0, 1.0]:
		lowpoly.add_box(Vector3(side * 4.4, 0.45, -2.0), Vector3(0.22, 0.9, 26.0), planks, 5.0)
		lowpoly.add_box(Vector3(side * 4.4, 0.98, -2.0), Vector3(0.34, 0.12, 26.0), planks, 5.0)
	var wood := lowpoly.tex_material(planks, {"uv_scale": Vector2(1.0, 5.0)})
	var mast := CylinderMesh.new()
	mast.top_radius = 0.24
	mast.bottom_radius = 0.3
	mast.height = 13.0
	_add(mast, Vector3(-0.6, 6.5, -6.5), null, wood)
	var sail := lowpoly.add_box(Vector3(-0.6, 8.2, -6.4), Vector3(6.6, 4.6, 0.06), lowpoly_texture("sail"), 2.0)
	sail.rotation.y = 0.12
	lowpoly.add_box(Vector3(-0.6, 10.6, -6.5), Vector3(7.0, 0.16, 0.16), planks, 3.0)
	for item: Array in [["barrel", Vector3(-3.2, 0.0, -4.4)], ["barrel", Vector3(-3.6, 0.0, -3.4)], ["crate", Vector3(3.3, 0.0, -5.2)],
			["crate", Vector3(3.4, 0.85, -5.2)], ["chest", Vector3(2.9, 0.0, -3.4)], ["cannon", Vector3(-3.4, 0.0, 0.4)],
			["cannon", Vector3(3.4, 0.0, -0.8)], ["keg", Vector3(3.6, 0.0, 1.6)]]:
		var prop := spawn_model("prop", item[0])
		prop.position = item[1]
		prop.rotation.y = rng.randf_range(-0.5, 0.5) + (PI / 2.0 if item[0] == "cannon" and (item[1] as Vector3).x > 0.0 else (-PI / 2.0 if item[0] == "cannon" else 0.0))
	hero = spawn_model("hero", "hero")
	hero.position = HERO_AT
	rival = spawn_model("enemy", "captain")
	rival.position = RIVAL_AT
	rival.rotation.y = PI
	for model: LowpolyModel in [hero, rival]:
		var rig := model as RigModel
		if rig != null:
			rig.smooth = 22.0
	hero_blade = _saber(hero, false)
	rival_blade = _saber(rival, true)
	# Искра на клинках.
	var ball := SphereMesh.new()
	ball.radius = 0.14
	ball.height = 0.28
	var glow := StandardMaterial3D.new()
	glow.albedo_color = Color(1.0, 0.9, 0.55)
	glow.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	spark = _add(ball, Vector3.ZERO, null, glow)
	spark.visible = false
	spark.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


# --- Шаг -------------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	_shake = maxf(_shake - delta * 3.0, 0.0)
	_hero_flash = maxf(_hero_flash - delta, 0.0)
	_rival_flash = maxf(_rival_flash - delta, 0.0)
	_hero_cut = maxf(_hero_cut - delta, 0.0)
	_rival_cut = maxf(_rival_cut - delta, 0.0)
	_spark_left = maxf(_spark_left - delta, 0.0)
	_note_left = maxf(_note_left - delta, 0.0)
	if not bot_driven() and running:
		if GameInput.a_just_pressed():
			bug_press(func() -> void: _want_strike = true)
		if GameInput.b_just_pressed():
			bug_press(func() -> void: _want_back = true)
	# Фризы в бою с догоном времени (`Demo.bug_frame`).
	bug_frame(delta, sim.phase == SaberSim.Phase.PLAY, _step)


func _step(dt: float) -> void:
	_time += dt
	bug_input_tick()
	var hold := minf(_stop_left, dt)
	_stop_left -= hold
	var left := dt - hold
	while left > 0.0001 and running:
		var h := minf(left, SaberSim.DT)
		left -= h
		var side := -1
		var strike := false
		var back := false
		if bot_driven():
			sim.bot(active_bot_mode(), h)
			side = sim.bot_side
			strike = sim.bot_strike
			back = sim.bot_back
		else:
			# Стойка стрелками (с багом управления из прошлого, `Demo.bug_axis`).
			var axis := bug_axis(GameInput.axis())
			if axis.y < -0.5 and absf(axis.y) >= absf(axis.x):
				side = SaberPlan.Side.TOP
			elif axis.x < -0.5:
				side = SaberPlan.Side.LEFT
			elif axis.x > 0.5:
				side = SaberPlan.Side.RIGHT
			strike = _want_strike
			back = _want_back
			_want_strike = false
			_want_back = false
		sim.step(h, side, strike, back)
		for ev in sim.events:
			_on_event(ev)
		sim.events.clear()
		if _stop_left > 0.0:
			break
	_sync(dt)


func _say(text: String, color: Color) -> void:
	_note = text
	_note_color = color
	_note_left = 0.7


func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"go":
			_play("go")
		&"swing":
			_play("swing")
		&"land":
			_play("hit")
			_hero_cut = 0.16
			_rival_flash = 0.1
			_stop_left = tuning.hit_stop
			_shake = maxf(_shake, 0.4)
			_say("ПОПАЛ", ThreedHud.GREEN)
		&"parried":
			_play("clang")
			_hero_cut = 0.16
			_spark_left = 0.12
			_say("ОТБИТО", ThreedHud.RED)
		&"windup":
			if ev[2]:
				_play("warn")
		&"block":
			_play("clang")
			_rival_cut = 0.16
			_rival_cut_side = ev[1]
			_spark_left = 0.12
			_shake = maxf(_shake, 0.25)
			_say("БЛОК", ThreedHud.WHITE)
		&"hurt":
			_play("hurt")
			_rival_cut = 0.16
			_rival_cut_side = ev[1]
			_hero_flash = 0.12
			_stop_left = tuning.hit_stop
			_shake = 1.0
			if AutoTest.enabled and not embedded:
				AutoTest.note("fighting threed: пропущен удар %s на %.1f с, здоровья %d" % [SIDE_NAMES[int(ev[1])].to_lower(), sim.time, sim.hero_hp])
		&"dodge":
			_rival_cut = 0.16
			_say("УШЁЛ", ThreedHud.GREEN)
		&"step":
			_play("step")
		&"win":
			end_demo(true)
		&"dead", &"timeout":
			end_demo(false)


func _on_end(goal: bool) -> void:
	_music.stop()
	if goal:
		_play("finish")
	if AutoTest.enabled and not embedded:
		AutoTest.note("fighting threed: %s за %.1f с, здоровья %d, у соперника %d, попал %d, отбито соперником %d, блоков %d, пропущено %d, уходов %d" % [
				"победил" if goal else "не победил", sim.time, sim.hero_hp, sim.rival_hp, sim.landed, sim.parried, sim.blocks, sim.taken, sim.dodges])


func _result_title(goal: bool) -> String:
	return "победа" if goal else "поражение"


func _result_caption() -> String:
	return "%d с · попал %d · блоков %d · пропустил %d" % [int(round(sim.time)), sim.landed, sim.blocks, sim.taken]


# --- Картинка --------------------------------------------------------------------------------

## Поза бойца: стойка `side` (с его стороны), замах 0..1 (сабля отведена дальше), удар 0..1
## (рука вперёд), вес шага назад.
func _pose(model: LowpolyModel, blade: Node3D, side: int, wind: float, cut: float, lean: float) -> void:
	if model.pink:
		return
	var rig := model as RigModel
	if rig == null:
		model.walk(0.0, 0.0)
		return
	var g: Dictionary = GUARDS[side]
	var arm: Vector3 = g["arm"]
	var fore: float = g["fore"]
	var tilt: Vector3 = g["blade"]
	# Замах: рука уходит дальше в свою сторону и выше, сабля заваливается назад.
	var out := -1.0 if side == 0 else (1.0 if side == 2 else 0.0)
	arm += Vector3(0.25 if side != 1 else 0.45, 0.0, out * 0.45) * wind
	fore += 0.35 * wind
	tilt += Vector3(-0.7, 0.0, out * 0.25) * wind
	arm = arm.lerp(CUT["arm"], cut)
	fore = lerpf(fore, CUT["fore"], cut)
	tilt = tilt.lerp(CUT["blade"], cut)
	rig.pose({&"arm_r": arm, &"fore_r": fore, &"arm_l": Vector3(-0.35, 0.0, -0.35), &"fore_l": 0.7,
			&"leg_l": 0.42 - lean * 0.3, &"leg_r": -0.34 - lean * 0.2, &"shin_l": -0.5, &"shin_r": -0.32, &"foot_l": 0.1, &"foot_r": 0.5})
	rig.joint(&"hips", Vector3(-0.08, -0.35, 0.0))
	rig.joint(&"spine", Vector3(-0.12 - cut * 0.25 + lean * 0.2, 0.2 - out * 0.18 * (1.0 - cut), 0.0))
	rig.joint(&"chest", Vector3(-cut * 0.15, 0.15 - out * 0.15 * (1.0 - cut), 0.0))
	rig.joint(&"head", Vector3(0.05, 0.0, 0.0))
	blade.rotation = blade.rotation.lerp(tilt, 0.4)


func _sync(dt: float) -> void:
	# Герой: стойка, замах своего удара, удар, шаг назад.
	var swing := 1.0 - sim.hero_left / tuning.swing if sim.hero == SaberSim.Hero.SWING else 0.0
	var away := 0.0
	if sim.hero == SaberSim.Hero.STEP:
		away = sin(clampf(1.0 - sim.hero_left / tuning.step_seconds, 0.0, 1.0) * PI / 2.0)
	elif sim.hero == SaberSim.Hero.RETURN:
		away = clampf(sim.hero_left / tuning.step_return, 0.0, 1.0)
	hero.position = HERO_AT + Vector3(0.0, 0.0, 1.15 * away)
	var hero_side := int(sim.swing_side if sim.hero == SaberSim.Hero.SWING else sim.guard)
	var low := 1.0 if sim.hero == SaberSim.Hero.RETURN or sim.hero == SaberSim.Hero.STUN else 0.0
	_pose(hero, hero_blade, hero_side, sin(swing * PI) * 0.8 if swing < 0.6 else 0.0, maxf(clampf((swing - 0.6) / 0.4, 0.0, 1.0), _hero_cut / 0.16), away)
	if low > 0.0 and hero is RigModel and not hero.pink:
		(hero as RigModel).pose({&"arm_r": Vector3(0.35, 0.0, 0.3), &"fore_r": 0.5})
	hero.flash(_hero_flash > 0.0)
	# Капитан стоит лицом к герою: его «слева» это право игрока, стороны зеркалятся.
	var shown := int(sim.shown())
	var wind := sim.windup_k()
	var rival_side := 2 - (shown if _rival_cut <= 0.0 else _rival_cut_side)
	var lunge := sim.lunging()
	rival.position = RIVAL_AT + Vector3(0.0, 0.0, (0.55 * wind * wind if lunge else 0.0) + (0.3 if _rival_cut > 0.0 else 0.0)
			- (0.25 if sim.rival == SaberSim.Rival.FLINCH else 0.0))
	_pose(rival, rival_blade, rival_side, wind if sim.rival == SaberSim.Rival.WINDUP else 0.0, _rival_cut / 0.16,
			0.5 if sim.rival == SaberSim.Rival.OPEN else 0.0)
	if sim.rival == SaberSim.Rival.OPEN and rival is RigModel and not rival.pink:
		# Открыт после связки: сабля опущена в сторону.
		(rival as RigModel).pose({&"arm_r": Vector3(0.3, 0.0, 0.7), &"fore_r": 0.3})
	rival.flash(_rival_flash > 0.0)
	# Искра между клинками на блоке.
	spark.visible = _spark_left > 0.0
	if spark.visible:
		spark.position = (hero.position + rival.position) / 2.0 + Vector3(0.1, 1.45, 0.0)
		spark.scale = Vector3.ONE * (0.6 + _spark_left * 9.0)
	# Камера из-за правого плеча героя.
	var eye := Vector3(1.15, 1.95, 3.45 + away * 0.5) + Vector3(sin(_time * 61.0), cos(_time * 47.0), 0.0) * 0.05 * _shake
	lowpoly.camera.transform = Transform3D(Basis.IDENTITY, eye).looking_at(Vector3(-0.05, 1.22, -0.7))


# --- HUD ---------------------------------------------------------------------------------------

## Три дуги сторон вокруг точки: слева, сверху, справа; `active` горит цветом `color`.
func _sides(h: ThreedHud, at: Vector2, radius: float, active: int, color: Color, width: float, faint: Color) -> void:
	var spans := [[PI * 0.8, PI * 1.2], [PI * 1.3, PI * 1.7], [-PI * 0.2, PI * 0.2]]
	for i in 3:
		var on := i == active
		h.arc(at, radius, spans[i][0], spans[i][1], Color(0.0, 0.0, 0.0, 0.4), width + 1.6)
		h.arc(at, radius, spans[i][0], spans[i][1], color if on else faint, width if on else width * 0.6)


func _draw_hud(canvas: CanvasItem) -> void:
	if sim == null:
		return
	var h := ThreedHud.begin(canvas, lowpoly)
	var view := lowpoly.view
	var mid := view / 2.0
	if _hero_flash > 0.0:
		h.rect(Rect2(Vector2.ZERO, view), Color(0.85, 0.1, 0.08, 0.25))
	# Стороны капитана: его стойка белым; на замахе сторона удара красным, кольцо сжимается к
	# моменту удара; выпад красным со всех сторон.
	var chest := lowpoly.project(rival.position + Vector3(0.0, 1.3, 0.0))
	var shown := int(sim.shown())
	if sim.phase == SaberSim.Phase.PLAY:
		if sim.lunging():
			var k := sim.windup_k()
			for i in 3:
				_sides(h, chest, 36.0, i, ThreedHud.RED, 3.0, ThreedHud.RED)
			h.arc(chest, 36.0 + 26.0 * (1.0 - k), 0.0, TAU, Color(ThreedHud.RED, 0.8), 1.4)
			h.text(chest + Vector2(0.0, -46.0), "ВЫПАД: ШАГ НАЗАД", 7.5, ThreedHud.RED if int(_time * 8.0) % 2 == 0 else ThreedHud.GOLD, 0,
					Color(0.0, 0.0, 0.0, 0.6))
		elif sim.rival == SaberSim.Rival.WINDUP:
			var k := sim.windup_k()
			_sides(h, chest, 36.0, shown, ThreedHud.RED, 3.4, ThreedHud.FAINT)
			h.arc(chest, 36.0 + 26.0 * (1.0 - k), 0.0, TAU, Color(ThreedHud.RED, 0.7), 1.2)
		elif sim.rival == SaberSim.Rival.OPEN:
			_sides(h, chest, 36.0, -1, ThreedHud.WHITE, 2.6, ThreedHud.FAINT)
			h.text(chest + Vector2(0.0, -42.0), "ОТКРЫТ", 8.0, ThreedHud.GREEN, 0, Color(0.0, 0.0, 0.0, 0.6))
		else:
			_sides(h, chest, 36.0, shown, ThreedHud.WHITE, 2.8, ThreedHud.FAINT)
		# Стойка героя: золотом у его плеча.
		var mine := lowpoly.project(hero.position + Vector3(0.0, 1.35, 0.0))
		_sides(h, mine, 24.0, int(sim.guard) if sim.guarding() or sim.hero == SaberSim.Hero.SWING else -1, ThreedHud.GOLD, 2.6, ThreedHud.FAINT)
	# Здоровье: герой слева сверху, капитан справа.
	for who in 2:
		var left := who == 0
		var box := Rect2(10.0 if left else view.x - 170.0, 9.0, 160.0, 26.0)
		h.panel(box, 7.0)
		h.text(Vector2(box.position.x + (8.0 if left else 152.0), 16.5), "МАТРОС" if left else "КАПИТАН", 5.2, ThreedHud.DIM, -1 if left else 1)
		var life := float(sim.hero_hp) / tuning.hero_hp if left else float(sim.rival_hp) / tuning.rival_hp
		var a := Vector2(box.position.x + 9.0, 27.0)
		var b := Vector2(box.position.x + 151.0, 27.0)
		h.bar(a, b, ThreedHud.FAINT, 4.4)
		if life > 0.0:
			if left:
				h.bar(a, a.lerp(b, life), ThreedHud.RED if life < 0.3 else ThreedHud.GREEN, 4.4)
			else:
				h.bar(b.lerp(a, life), b, ThreedHud.RED, 4.4)
		h.text(Vector2(box.position.x + (152.0 if left else 8.0), 16.5), str(sim.hero_hp if left else sim.rival_hp), 6.0, ThreedHud.WHITE, 1 if left else -1)
	h.panel(Rect2(mid.x - 30.0, 9.0, 60.0, 26.0), 7.0)
	h.text(Vector2(mid.x, 22.0), "%d:%02d" % [int(sim.time) / 60, int(sim.time) % 60], 11.0)
	if _note_left > 0.0:
		h.text(Vector2(mid.x, mid.y - 70.0), _note, 12.0, Color(_note_color, minf(_note_left * 3.0, 1.0)), 0, Color(0.0, 0.0, 0.0, 0.55))
	if sim.phase == SaberSim.Phase.COUNTDOWN:
		h.text(Vector2(mid.x, mid.y - 30.0), str(ceili(sim.countdown)), 46.0, ThreedHud.WHITE, 0, Color(0.05, 0.07, 0.11, 0.8))
	h.end()
