extends Demo
## Демка файтинг × «продвинутые», каталог `docs/specs/demos_catalog.md`: «один против всех»
## (#125, второе решение 2026-11-13 вместо дуэли на саблях; образцы Batman: Arkham, Shadow of
## Mordor, Sleeping Dogs). Матрос один на палубе, пираты волнами выходят вокруг него, камера
## сверху-сзади держит всех в кадре. Стик выбирает сторону; A удар: герой сам перелетает к
## ближнему врагу в эту сторону, удары подряд копят серию; A подержать это сильный удар,
## он сбивает щит. B без стика контратака: перехватывает замах, над которым горит метка; B
## со стиком перекат: только он спасает от ножа (красная метка). Серия от пяти удваивает
## урон, каждые десять ударов дают добивание. План волн из `FrayPlanGen` по сиду записи;
## правила и боты живут в `FraySim` (без окна, им же проверяются сто сидов), демка ведёт его
## шагами по 1/60 с, рисует и озвучивает события.
##
## Общие баги (#44) и баг технологии `camera_clip` живут в `Demo` и `ThreedScreen`, демка только
## зовёт хуки. Баги жанра и баланса для этой демки включит #126.

const PLACEHOLDER_SLOTS: Array[String] = ["hero", "enemy", "prop"]
const MELODY := [0, 3, 5, 7, 10, 7, 5, 3, 0, 3, 5, 8, 7, 5, 3, null,
	0, 3, 5, 7, 10, 12, 10, 7, 8, 7, 5, 3, 2, 3, 0, null]
const BASS := [-12, -12, -5, -5, -9, -9, -5, -5, -4, -4, -9, -9, -7, -7, -5, -5]

var tuning: FightingThreedTuning
var plan: FrayPlan
var sim: FraySim
var hero: LowpolyModel
var foe_nodes: Array[Node3D] = []
var foe_models: Array[LowpolyModel] = []

var _time := 0.0
var _stop_left := 0.0
var _want_b := false
var _shake := 0.0
var _hero_flash := 0.0
var _punch := 0.0
var _punch_kind := 0
var _focus := Vector3.ZERO
var _note := ""
var _note_left := 0.0
var _note_color := Color.WHITE
var _combo_pop := 0.0
var _music: AudioStreamPlayer
var _sfx := {}


func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _on_start() -> void:
	tuning = FightingThreedTuning.load_default()
	plan = FrayPlanGen.generate(record.seed if record != null else 1, tuning)
	sim = FraySim.create(plan, tuning)
	lowpoly_screen(_draw_hud)
	lowpoly.camera.fov = 50.0
	_build_world()
	_setup_audio()
	_sync(0.0)


func _setup_audio() -> void:
	var quiet := embedded
	_music = Sfx.music(Sfx.tracker_loop(MELODY, BASS, 148.0), tuning.music_db if not quiet else -80.0)
	add_child(_music)
	bug_music = _music
	if not quiet:
		_music.play()
	_sfx["go"] = Sfx.player(Sfx.blip(880.0, 0.3, 0.4, 6.0))
	_sfx["dash"] = Sfx.player(Sfx.hiss(0.08, 0.14))
	_sfx["hit"] = Sfx.player(Sfx.thud(0.1, 0.55))
	_sfx["ko"] = Sfx.player(Sfx.thud(0.22, 0.7))
	_sfx["clang"] = Sfx.player(Sfx.blip(2100.0, 0.1, 0.35, 18.0))
	_sfx["counter"] = Sfx.player(Sfx.blip(1320.0, 0.14, 0.4, 12.0))
	_sfx["dodge"] = Sfx.player(Sfx.hiss(0.14, 0.14))
	_sfx["hurt"] = Sfx.player(Sfx.thud(0.2, 0.65))
	_sfx["warn"] = Sfx.player(Sfx.blip(440.0, 0.1, 0.25, 12.0))
	_sfx["special"] = Sfx.player(Sfx.blip(1760.0, 0.25, 0.35, 6.0))
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


func _metal(color: Color, rough := 0.3) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.metallic = 0.85
	m.roughness = rough
	return m


func _build_world() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed if record != null else 1, ":fray-look"))
	var screen := lowpoly as ThreedScreen
	screen.add_water(Vector3(0.0, -3.2, 0.0), 1200.0)
	# Палуба: настил шире круга драки, борта, мачта с парусом, реквизит по краям.
	var planks := lowpoly_texture("planks")
	var deck := lowpoly.add_box(Vector3(0.0, -0.25, 0.0), Vector3(19.0, 0.5, 30.0), planks, 5.0)
	deck.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for side: float in [-1.0, 1.0]:
		lowpoly.add_box(Vector3(side * 9.4, 0.45, 0.0), Vector3(0.24, 0.9, 30.0), planks, 5.0)
		lowpoly.add_box(Vector3(side * 9.4, 0.98, 0.0), Vector3(0.36, 0.12, 30.0), planks, 5.0)
	var mast := CylinderMesh.new()
	mast.top_radius = 0.26
	mast.bottom_radius = 0.34
	mast.height = 14.0
	_add(mast, Vector3(0.0, 7.0, -10.5), null, lowpoly.tex_material(planks, {"uv_scale": Vector2(1.0, 5.0)}))
	lowpoly.add_box(Vector3(0.0, 9.4, -10.4), Vector3(9.0, 5.0, 0.06), lowpoly_texture("sail"), 2.0)
	lowpoly.add_box(Vector3(0.0, 12.0, -10.5), Vector3(9.6, 0.18, 0.18), planks, 3.0)
	for item: Array in [["barrel", Vector3(-8.4, 0.0, -6.4)], ["barrel", Vector3(-8.5, 0.0, -5.3)], ["crate", Vector3(8.3, 0.0, -7.0)],
			["crate", Vector3(8.3, 0.85, -7.0)], ["chest", Vector3(8.2, 0.0, -4.6)], ["cannon", Vector3(-8.3, 0.0, 1.4)],
			["cannon", Vector3(8.3, 0.0, -0.8)], ["cannon", Vector3(-8.3, 0.0, -2.6)], ["keg", Vector3(8.4, 0.0, 3.6)],
			["barrel", Vector3(-8.4, 0.0, 5.2)], ["crate", Vector3(-7.4, 0.0, -9.0)], ["crate", Vector3(6.6, 0.0, -9.4)]]:
		var prop := spawn_model("prop", item[0])
		prop.position = item[1]
		var cannon: bool = item[0] == "cannon"
		prop.rotation.y = (PI / 2.0 if (item[1] as Vector3).x > 0.0 else -PI / 2.0) if cannon else rng.randf_range(-0.6, 0.6)
	hero = spawn_model("hero", "hero")
	var rig := hero as RigModel
	if rig != null:
		rig.smooth = 26.0


## Модель пирата под его род: простой, со щитом в левой руке, с ножом в правой.
func _spawn_foe(f: FraySim.Pirate) -> void:
	var holder := Node3D.new()
	lowpoly.world.add_child(holder)
	var model := spawn_model("enemy", "enemy", holder)
	var rig := model as RigModel
	if rig != null:
		rig.smooth = 20.0
		if f.kind == FrayPlan.Kind.KNIFE:
			rig.material.set_shader_parameter("tint", Color(1.0, 0.72, 0.68))
		elif f.kind == FrayPlan.Kind.SHIELD:
			rig.material.set_shader_parameter("tint", Color(0.74, 0.86, 1.0))
	if not model.pink:
		if f.kind == FrayPlan.Kind.SHIELD:
			var disc := CylinderMesh.new()
			disc.top_radius = 0.56
			disc.bottom_radius = 0.56
			disc.height = 0.07
			disc.radial_segments = 16
			var shield := _add(disc, Vector3(-0.1, 1.0, -0.42), holder, lowpoly.tex_material(lowpoly_texture("planks"), {"tint": Color(0.75, 0.55, 0.4)}))
			shield.rotation.x = PI / 2.0
			shield.name = "Shield"
			var boss := CylinderMesh.new()
			boss.top_radius = 0.16
			boss.bottom_radius = 0.2
			boss.height = 0.08
			_add(boss, Vector3(0.0, 0.07, 0.0), shield, _metal(Color(0.5, 0.52, 0.56), 0.4))
		elif f.kind == FrayPlan.Kind.KNIFE and rig != null and rig.has_joint(&"hand_r"):
			var hand := BoneAttachment3D.new()
			rig.skeleton.add_child(hand)
			hand.bone_name = "hand_r"
			var blade := BoxMesh.new()
			blade.size = Vector3(0.04, 0.012, 0.42)
			_add(blade, Vector3(0.0, -0.08, -0.24), hand, _metal(Color(0.9, 0.92, 0.96), 0.15))
	foe_nodes.append(holder)
	foe_models.append(model)


# --- Шаг -------------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	_shake = maxf(_shake - delta * 3.0, 0.0)
	_hero_flash = maxf(_hero_flash - delta, 0.0)
	_punch = maxf(_punch - delta, 0.0)
	_note_left = maxf(_note_left - delta, 0.0)
	_combo_pop = maxf(_combo_pop - delta * 4.0, 0.0)
	if not bot_driven() and running and GameInput.b_just_pressed():
		bug_press(func() -> void: _want_b = true)
	# Фризы в бою с догоном времени (`Demo.bug_frame`).
	bug_frame(delta, sim.phase == FraySim.Phase.PLAY, _step)


func _step(dt: float) -> void:
	_time += dt
	bug_input_tick()
	var hold := minf(_stop_left, dt)
	_stop_left -= hold
	var left := dt - hold
	while left > 0.0001 and running:
		var h := minf(left, FraySim.DT)
		left -= h
		var dir := Vector2.ZERO
		var a := false
		var b := false
		if bot_driven():
			sim.bot(active_bot_mode(), h)
			dir = sim.bot_dir
			a = sim.bot_a
			b = sim.bot_b
		else:
			# Стик в мире: вверх это от камеры. С багом управления из прошлого (`Demo.bug_axis`).
			dir = bug_axis(GameInput.axis())
			a = GameInput.a_pressed()
			b = _want_b
			_want_b = false
		sim.step(h, dir, a, b)
		for ev in sim.events:
			_on_event(ev)
		sim.events.clear()
		if _stop_left > 0.0:
			break
	_sync(dt)


func _say(text: String, color: Color) -> void:
	_note = text
	_note_color = color
	_note_left = 0.8


func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"go":
			_play("go")
		&"dash":
			_play("dash")
		&"hit":
			_play("hit")
			_punch = 0.2
			_punch_kind = sim.landed % 3
			_stop_left = tuning.hit_stop
			_shake = maxf(_shake, 0.3 if not ev[2] else 0.6)
			_combo_pop = 1.0
		&"break":
			_play("clang")
			_punch = 0.25
			_punch_kind = 3
			_shake = maxf(_shake, 0.6)
			_combo_pop = 1.0
			_say("ЩИТ СБИТ", ThreedHud.GREEN)
		&"bounce":
			_play("clang")
			_shake = maxf(_shake, 0.4)
			_say("ЩИТ: ДЕРЖИ УДАР", ThreedHud.RED)
		&"ko":
			_play("ko")
			_shake = maxf(_shake, 0.7)
			_stop_left = tuning.hit_stop * (3.0 if ev[2] else 1.6)
			if ev[2]:
				_punch = 0.3
				_punch_kind = 3
				_say("ДОБИВАНИЕ", ThreedHud.GOLD)
		&"counter":
			_play("counter")
			_punch = 0.25
			_punch_kind = 2
			_stop_left = tuning.hit_stop
			_combo_pop = 1.0
			_say("ПЕРЕХВАТ", ThreedHud.GREEN)
		&"dodge":
			_play("dodge")
		&"windup":
			_play("warn")
		&"special":
			_play("special")
		&"hurt":
			_play("hurt")
			_hero_flash = 0.14
			_stop_left = tuning.hit_stop
			_shake = 1.0
			if AutoTest.enabled and not embedded:
				AutoTest.note("fighting threed: пропущен удар на %.1f с, здоровья %d" % [sim.time, sim.hero_hp])
		&"win":
			end_demo(true)
		&"dead", &"timeout":
			end_demo(false)


func _on_end(goal: bool) -> void:
	_music.stop()
	if goal:
		_play("finish")
	if AutoTest.enabled and not embedded:
		AutoTest.note("fighting threed: %s за %.1f с, здоровья %d, уложил %d из %d, ударов %d, контратак %d, перекатов %d, отскоков %d, пропущено %d, добиваний %d, лучшая серия %d" % [
				"победил" if goal else "не победил", sim.time, sim.hero_hp, sim.kos, plan.total(), sim.landed, sim.counters, sim.dodges,
				sim.bounces, sim.taken, sim.specials, sim.best])


func _result_title(goal: bool) -> String:
	return "палуба чиста" if goal else "поражение"


func _result_caption() -> String:
	return "уложил %d из %d · серия %d · %d с" % [sim.kos, plan.total(), sim.best, int(round(sim.time))]


# --- Картинка --------------------------------------------------------------------------------

func _sync(dt: float) -> void:
	while foe_nodes.size() < sim.foes.size():
		_spawn_foe(sim.foes[foe_nodes.size()])
	for i in sim.foes.size():
		_pose_foe(sim.foes[i], foe_nodes[i], foe_models[i], i)
	hero.position = Vector3(sim.pos.x, 0.0, sim.pos.y)
	hero.rotation = Vector3(0.0, sim.facing, 0.0)
	_pose_hero()
	hero.flash(_hero_flash > 0.0)
	# Камера сверху-сзади: идёт за героем вполсилы, чтобы круг драки оставался в кадре.
	var want := Vector3(sim.pos.x * 0.7, 0.0, sim.pos.y * 0.7)
	_focus = _focus.lerp(want, 1.0 - exp(-4.0 * dt)) if dt > 0.0 else want
	var eye := _focus + Vector3(0.0, 6.4, 7.2) + Vector3(sin(_time * 61.0), cos(_time * 47.0), 0.0) * 0.06 * _shake
	lowpoly.camera.transform = Transform3D(Basis.IDENTITY, eye).looking_at(_focus + Vector3(0.0, 0.9, -0.6))


## Поза героя: стойка, подлёт, удары по очереди (рука, рука, нога), сильный удар двумя
## руками, перехват, перекат, пропущенный удар.
func _pose_hero() -> void:
	if hero.pink:
		return
	var rig := hero as RigModel
	if rig == null:
		hero.walk(_time * 8.0 if sim.hero == FraySim.Hero.DASH else 0.0, 0.5)
		return
	var arm_l := Vector3(0.9, 0.0, -0.2)
	var arm_r := Vector3(0.9, 0.0, 0.2)
	var fore_l := 1.6
	var fore_r := 1.6
	var leg_l := 0.3
	var leg_r := -0.3
	var shin_l := -0.4
	var shin_r := -0.3
	var spine := Vector3(-0.1, 0.0, 0.0)
	var roll := 0.0
	if _punch > 0.0:
		match _punch_kind:
			0:
				arm_r = Vector3(1.55, 0.0, 0.0)
				fore_r = 0.1
				spine = Vector3(-0.2, -0.45, 0.0)
			1:
				arm_l = Vector3(1.55, 0.0, 0.0)
				fore_l = 0.1
				spine = Vector3(-0.2, 0.45, 0.0)
			2:
				leg_r = 1.5
				shin_r = -0.1
				spine = Vector3(0.25, 0.0, 0.0)
			_:
				arm_l = Vector3(1.3, 0.0, 0.0)
				arm_r = Vector3(1.3, 0.0, 0.0)
				fore_l = 0.2
				fore_r = 0.2
				spine = Vector3(-0.45, 0.0, 0.0)
	else:
		match sim.hero:
			FraySim.Hero.DASH:
				arm_l = Vector3(-0.6, 0.0, -0.3)
				arm_r = Vector3(-0.8, 0.0, 0.3)
				leg_l = 0.9
				leg_r = -0.7
				spine = Vector3(-0.4, 0.0, 0.0)
			FraySim.Hero.HEAVY:
				arm_l = Vector3(2.7, 0.0, 0.0)
				arm_r = Vector3(2.7, 0.0, 0.0)
				fore_l = 0.6
				fore_r = 0.6
				spine = Vector3(0.25, 0.0, 0.0)
			FraySim.Hero.DODGE:
				roll = clampf(1.0 - sim.hero_left / tuning.dodge_seconds, 0.0, 1.0) * TAU
				leg_l = 1.4
				leg_r = 1.2
				shin_l = -1.9
				shin_r = -1.8
				spine = Vector3(-0.7, 0.0, 0.0)
			FraySim.Hero.STUN:
				arm_l = Vector3(-0.3, 0.0, -0.7)
				arm_r = Vector3(-0.3, 0.0, 0.7)
				spine = Vector3(0.4, 0.0, 0.0)
			_:
				if sim.held > 0.08:
					# Заряд сильного удара: руки отведены назад.
					var k := clampf(sim.held / tuning.heavy_hold, 0.0, 1.0)
					arm_l = Vector3(0.9 - 1.6 * k, 0.0, -0.3)
					arm_r = Vector3(0.9 - 1.6 * k, 0.0, 0.3)
					spine = Vector3(-0.1 - 0.2 * k, 0.0, 0.0)
	rig.pose({&"arm_l": arm_l, &"arm_r": arm_r, &"fore_l": fore_l, &"fore_r": fore_r, &"leg_l": leg_l, &"leg_r": leg_r,
			&"shin_l": shin_l, &"shin_r": shin_r, &"foot_l": 0.1, &"foot_r": 0.3})
	rig.joint(&"hips", Vector3.ZERO)
	rig.joint(&"spine", spine)
	rig.joint(&"chest", Vector3(0.0, spine.y * 0.5, 0.0))
	rig.joint(&"head", Vector3(0.1, 0.0, 0.0))
	hero.rotation.x = -roll
	hero.position.y = 0.55 * sin(roll * 0.5) if roll > 0.0 else 0.0


func _pose_foe(f: FraySim.Pirate, node: Node3D, model: LowpolyModel, index: int) -> void:
	node.position = Vector3(f.pos.x, 0.0, f.pos.y)
	var to := sim.pos - f.pos
	if f.state != FraySim.Foe.OUT and f.state != FraySim.Foe.DOWN:
		node.rotation.y = atan2(-to.x, -to.y)
	model.flash(f.hit_for < 0.07)
	var lying := f.state == FraySim.Foe.OUT or f.state == FraySim.Foe.DOWN
	# Упавший лежит навзничь; выбывший через полторы секунды уходит под палубу.
	var fall := clampf(f.hit_for / 0.25, 0.0, 1.0) if lying else 0.0
	model.rotation.x = fall * PI / 2.0
	node.position.y = -maxf(f.out_for - 1.5, 0.0) * 1.4 if f.state == FraySim.Foe.OUT else 0.0
	node.visible = not (f.state == FraySim.Foe.OUT and f.out_for > 2.6)
	var shield := node.get_node_or_null("Shield") as Node3D
	if shield != null:
		# Сбитый щит висит сбоку.
		var up := not (f.state == FraySim.Foe.STUNNED or lying)
		shield.position = shield.position.lerp(Vector3(-0.1, 1.0, -0.42) if up else Vector3(-0.75, 0.55, 0.0), 0.3)
	if model.pink:
		return
	var rig := model as RigModel
	if rig == null:
		model.walk(_time * 6.0 + index, 0.4 if f.state == FraySim.Foe.WALK else 0.0)
		return
	match f.state:
		FraySim.Foe.WALK:
			model.walk(_time * 6.0 + index * 1.7, 0.35)
			rig.pose({&"arm_r": Vector3(0.8, 0.0, 0.2), &"fore_r": 1.5, &"arm_l": Vector3(0.9, 0.0, -0.2), &"fore_l": 1.4})
		FraySim.Foe.WINDUP:
			var k := clampf(1.0 - f.left / f.total, 0.0, 1.0)
			model.walk(_time * 9.0 + index, 0.3)
			rig.pose({&"arm_r": Vector3(0.6 + 2.2 * k, 0.0, 0.35), &"fore_r": 1.2 - 0.6 * k, &"arm_l": Vector3(0.9, 0.0, -0.2), &"fore_l": 1.4})
			rig.joint(&"spine", Vector3(0.25 * k, -0.3 * k, 0.0))
		FraySim.Foe.RECOVER:
			model.walk(0.0, 0.0)
			rig.pose({&"arm_r": Vector3(1.3, 0.0, 0.0), &"fore_r": 0.2, &"arm_l": Vector3(0.4, 0.0, -0.3), &"fore_l": 0.8})
			rig.joint(&"spine", Vector3(-0.4, 0.3, 0.0))
		FraySim.Foe.STAGGER:
			model.walk(0.0, 0.0)
			rig.pose({&"arm_r": Vector3(-0.4, 0.0, 0.8), &"arm_l": Vector3(-0.4, 0.0, -0.8), &"fore_r": 0.6, &"fore_l": 0.6})
			rig.joint(&"spine", Vector3(0.45, 0.0, 0.0))
		FraySim.Foe.STUNNED:
			model.walk(0.0, 0.0)
			rig.pose({&"arm_r": Vector3(0.2, 0.0, 0.3), &"arm_l": Vector3(0.2, 0.0, -0.3), &"fore_r": 0.3, &"fore_l": 0.3})
			rig.joint(&"spine", Vector3(-0.35, sin(_time * 5.0) * 0.2, 0.0))
			rig.joint(&"head", Vector3(-0.5, sin(_time * 5.0) * 0.3, 0.0))
		_:
			model.walk(0.0, 0.0)
			rig.pose({&"arm_r": Vector3(-0.3, 0.0, 1.0), &"arm_l": Vector3(-0.3, 0.0, -1.0)})


# --- HUD ---------------------------------------------------------------------------------------

func _draw_hud(canvas: CanvasItem) -> void:
	if sim == null:
		return
	var h := ThreedHud.begin(canvas, lowpoly)
	var view := lowpoly.view
	var mid := view / 2.0
	if _hero_flash > 0.0:
		h.rect(Rect2(Vector2.ZERO, view), Color(0.85, 0.1, 0.08, 0.25))
	# Метки над замахнувшимися: кольцо сжимается к удару. Белая это контратака, красная с
	# стрелками это нож: только перекат.
	for f in sim.foes:
		if not f.winding():
			continue
		var at := lowpoly.project(Vector3(f.pos.x, 2.25, f.pos.y))
		var k := clampf(1.0 - f.left / f.total, 0.0, 1.0)
		var knife := f.kind == FrayPlan.Kind.KNIFE
		var color := ThreedHud.RED if knife else Color(0.55, 0.85, 1.0)
		var hot := f.left <= tuning.counter_window
		h.circle(at, 7.2, Color(0.0, 0.0, 0.0, 0.5))
		h.circle(at, 6.0, color if hot else Color(color, 0.55))
		h.arc(at, 7.0 + 12.0 * (1.0 - k), 0.0, TAU, color, 1.2)
		if knife:
			for side: float in [-1.0, 1.0]:
				h.polygon(PackedVector2Array([at + Vector2(side * 12.5, 0.0), at + Vector2(side * 8.5, -3.2), at + Vector2(side * 8.5, 3.2)]), color)
			h.text(at, "!", 8.0, ThreedHud.WHITE)
		else:
			h.text(at, "B", 6.5, Color(0.05, 0.1, 0.18))
	# Заряд сильного удара у героя.
	if sim.held > 0.06 and sim.hero == FraySim.Hero.READY:
		var at := lowpoly.project(Vector3(sim.pos.x, 2.3, sim.pos.y))
		h.arc(at, 6.5, -PI / 2.0, -PI / 2.0 + TAU * clampf(sim.held / tuning.heavy_hold, 0.02, 1.0), ThreedHud.GOLD, 1.8)
	# Здоровье слева сверху.
	h.panel(Rect2(10.0, 9.0, 150.0, 26.0), 7.0)
	h.heart(Vector2(23.0, 22.0), 6.0, ThreedHud.RED)
	var life := float(sim.hero_hp) / tuning.hero_hp
	h.bar(Vector2(36.0, 24.5), Vector2(150.0, 24.5), ThreedHud.FAINT, 4.2)
	if life > 0.0:
		h.bar(Vector2(36.0, 24.5), Vector2(36.0 + 114.0 * life, 24.5), ThreedHud.RED if life < 0.3 else ThreedHud.GREEN, 4.2)
	h.text(Vector2(36.0, 15.5), str(sim.hero_hp), 6.0, ThreedHud.WHITE, -1)
	# Враги и волна справа сверху.
	h.panel(Rect2(view.x - 126.0, 9.0, 116.0, 30.0), 7.0)
	h.text(Vector2(view.x - 118.0, 17.0), "ВРАГОВ", 5.2, ThreedHud.DIM, -1)
	h.text(Vector2(view.x - 118.0, 29.0), str(sim.left_total()), 11.5, ThreedHud.WHITE, -1)
	h.text(Vector2(view.x - 18.0, 17.0), "ВОЛНА", 5.2, ThreedHud.DIM, 1)
	for w in plan.waves.size():
		h.circle(Vector2(view.x - 18.0 - (plan.waves.size() - 1 - w) * 6.0, 29.0), 1.9,
				ThreedHud.GOLD if w < sim.wave else (ThreedHud.WHITE if w == sim.wave else ThreedHud.FAINT))
	# Серия справа: число, кольцо остатка времени, удвоенный удар и добивание.
	if sim.combo > 0:
		var c := Vector2(view.x - 44.0, mid.y - 8.0)
		var size := 22.0 + _combo_pop * 6.0
		var strong := sim.combo >= tuning.strong_combo
		h.circle(c, 27.0, Color(0.0, 0.0, 0.0, 0.25))
		h.circle(c, 25.0, h.glass)
		h.arc(c, 25.0, 0.0, TAU, h.edge, 0.6)
		h.arc(c, 21.5, -PI / 2.0, -PI / 2.0 + TAU * clampf(sim.combo_left / tuning.combo_seconds, 0.0, 1.0), ThreedHud.GOLD if strong else ThreedHud.WHITE, 2.2)
		h.text(c + Vector2(0.0, -2.0), str(sim.combo), size * 0.72, ThreedHud.GOLD if strong else ThreedHud.WHITE)
		h.text(c + Vector2(0.0, 13.0), "УДАР ×2" if strong else "СЕРИЯ", 4.4, ThreedHud.GOLD if strong else ThreedHud.DIM)
		if sim.special:
			h.text(c + Vector2(0.0, 36.0), "ДОБИВАНИЕ", 6.5, ThreedHud.GOLD if int(_time * 6.0) % 2 == 0 else ThreedHud.WHITE, 0, Color(0.0, 0.0, 0.0, 0.6))
	if _note_left > 0.0:
		h.text(Vector2(mid.x, 58.0), _note, 11.0, Color(_note_color, minf(_note_left * 3.0, 1.0)), 0, Color(0.0, 0.0, 0.0, 0.55))
	if sim.phase == FraySim.Phase.COUNTDOWN:
		h.text(Vector2(mid.x, mid.y - 30.0), str(ceili(sim.countdown)), 46.0, ThreedHud.WHITE, 0, Color(0.05, 0.07, 0.11, 0.8))
	h.end()
