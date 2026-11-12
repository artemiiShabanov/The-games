extends Control
## Тест основы low poly (#108). По умолчанию лист: все меши стартового набора на песке под
## небом сеттинга, крутятся; подписи с числом треугольников, последним стоит розовая заглушка
## (`--setting=N` сеттинг, у космоса и замков пока пиратские меши и текстуры). Под автотестом
## проверки: каждый меш грузится, не больше 300 треугольников, части, нормали и развёртка целы,
## атлас не крупнее 64 пикселей, у героя и врага есть ноги и руки, текстуры уровня на месте,
## модель собирается в узлы на шейдере PS1, грани смотрят наружу, земля отдаёт высоту по своим
## треугольникам, камера за спиной встаёт позади цели и доворачивает за курсом, вид от первого
## лица поворачивает и идёт куда смотрит, розовая заглушка и чужая палитра работают, обе пробные
## демки идут во встроенном режиме. `--probe=behind` или `--probe=first` (или «Low poly: проба
## за спиной», «Low poly: проба от первого лица» в дебаг-меню) запускает пробную демку в
## карточке: бот WIN добирается до конца; `--bugs` все общие баги, `--bug=<id>` один,
## `--setting=N`, `--seed=N`, `--no-checks` без проверок. `--look` проверяет обзор мышью и правым
## стиком (#109): движение мыши поворачивает и наклоняет камеру пробы от первого лица и курс
## рейкастера 16/32 по чувствительности из настроек, пауза его глушит, стик считает мёртвую зону,
## правый стик снят с действий `look_left` и `look_right`.

const ProbeBehind := preload("res://debug/scenes/lowpoly_probe_behind.gd")
const ProbeFirst := preload("res://debug/scenes/lowpoly_probe_first.gd")
const COMMON_BUGS: Array[StringName] = [&"frame_drops", &"audio_stutter", &"sticky_input",
		&"pink_placeholders", &"alien_palette", &"mesh_holes"]
## Меши стартового набора; у двуногих есть ноги и руки.
const MODELS: Array[String] = ["palm", "lighthouse", "hoop", "flag", "cannon", "cart", "cart_rival", "hero", "enemy", "captain",
		"chest", "barrel", "crate", "rock", "pistol", "coin", "bottle", "ball", "keg"]
const BIPEDS: Array[String] = ["hero", "enemy", "captain"]
## Модели в руке: ноль в рукояти, на земле не стоят.
const HELD: Array[String] = ["pistol"]
## Выше этого модель на листе уменьшается, метры.
const SHEET_TALL := 3.0
const TEXTURES: Array[String] = ["sand", "planks", "water", "rock", "sail", "grass", "road", "mud", "wind", "sky"]
const MAX_ATLAS := 64
const COLUMNS := 7
const CELL := 2.7

var demo: Demo
var record: GameRecord
var _args := {}
var _probe := ""
var _sheet: LowpolyScreen
var _setting: SettingDef
var _models: Array[LowpolyModel] = []
var _labels: Array[String] = []
var _t := 0.0


func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Color("#26323F")
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	_args = AutoTest.parse_args(OS.get_cmdline_user_args()) if AutoTest.enabled else {}
	_probe = str(_args.get("probe", "")) if AutoTest.enabled else Debug.lowpoly_probe
	Debug.lowpoly_probe = ""
	if AutoTest.enabled and _args.has("look"):
		AutoTest.require("look checks")
		await _check_look()
		AutoTest.fulfill("look checks")
		return
	if _probe != "":
		if AutoTest.enabled and not _args.has("no-checks"):
			AutoTest.require("lowpoly probe")
		_launch()
		return
	_build_sheet()
	if AutoTest.enabled and not _args.has("no-checks"):
		AutoTest.require("lowpoly checks")
		_check_assets()
		_check_screen()
		_check_cameras()
		await _check_embedded()
		AutoTest.fulfill("lowpoly checks")


func _process(delta: float) -> void:
	_t += delta
	for i in _models.size():
		_models[i].rotation.y = _t * 0.8 + i * 0.6
		_models[i].walk(_t * 8.0, 0.6)


# --- Лист --------------------------------------------------------------------------------------

func _build_sheet() -> void:
	_setting = SettingDef.of(int(_args.get("setting", Debug.demo_setting)) as Game.Setting)
	_sheet = LowpolyScreen.make(Vector2(Style.SCREEN), false, _setting.colors_lowpoly(), _setting.sky_lowpoly(),
			_setting.texture_lowpoly("sky"), Debug.lowpoly_scale)
	_sheet.draw_hud = _draw_sheet_hud
	add_child(_sheet)
	var names := MODELS.duplicate()
	names.append("chest")
	var rows := ceili(float(names.size()) / COLUMNS)
	_sheet.add_plane(Vector3.ZERO, Vector2(COLUMNS * CELL + 6.0, rows * CELL + 6.0), _setting.texture_lowpoly("sand"), 3.0)
	_sheet.add_plane(Vector3(0.0, -0.4, 0.0), Vector2(300.0, 300.0), _setting.texture_lowpoly("water"), 6.0,
			{"uv_scroll": Vector2(0.02, 0.035), "affine": 0.0})
	for i in names.size():
		var def := _setting.model(names[i])
		var is_pink := i == names.size() - 1
		var at := Vector3((i % COLUMNS - (COLUMNS - 1) / 2.0) * CELL, 0.0, (i / COLUMNS - (rows - 1) / 2.0) * CELL)
		var m := _sheet.pink_model(def) if is_pink else _sheet.model(def)
		m.position = at + (Vector3(0.0, 0.9, 0.0) if HELD.has(names[i]) else Vector3.ZERO)
		var tall := def.bounds().size.y if def != null else 1.0
		if tall > SHEET_TALL:
			m.scale = Vector3.ONE * SHEET_TALL / tall
		_sheet.world.add_child(m)
		_sheet.add_shadow(0.45).position = at + Vector3(0.0, 0.03, 0.0)
		_models.append(m)
		_labels.append("заглушка" if is_pink else "%s %d%s" % [names[i], def.triangles() if def != null else 0,
				" (1:%d)" % roundi(tall / SHEET_TALL) if tall > SHEET_TALL else ""])
	_sheet.camera.transform = Transform3D(Basis.IDENTITY, Vector3(0.0, 6.0, 10.6)).looking_at(Vector3(0.0, 0.8, 0.0))


func _draw_sheet_hud(canvas: CanvasItem) -> void:
	var dark := Color("#16141A")
	var white := Color("#F4EFE6")
	var own := _setting.lowpoly_colors.size() >= LowpolyScreen.ROLES
	PixelFont16.draw(canvas, Vector2(8.0, 6.0), "low poly: %s%s" % [SettingDef.IDS[_setting.setting],
			"" if own else " (меши и текстуры пиратов)"], white, white, dark, 1.0)
	for i in _models.size():
		var at := _sheet.camera.unproject_position(_models[i].position + Vector3(0.0, -0.05, 0.75))
		PixelFont16.draw(canvas, (at - Vector2(PixelFont16.width(_labels[i], 1.0) / 2.0, 0.0)).floor(), _labels[i], white, white, dark, 1.0)


# --- Проверки ----------------------------------------------------------------------------------

func _check_assets() -> void:
	var pirates := SettingDef.of(Game.Setting.PIRATES)
	_expect(pirates.lowpoly_colors.size() == LowpolyScreen.ROLES, "у пиратов цветов HUD low poly %d, нужно %d" % [
			pirates.lowpoly_colors.size(), LowpolyScreen.ROLES])
	var most := 0
	for s in SettingDef.IDS.size():
		var def := SettingDef.of(s as Game.Setting)
		var id := SettingDef.IDS[s]
		_expect(def.colors_lowpoly().size() == LowpolyScreen.ROLES, "%s: цветов HUD low poly %d" % [id, def.colors_lowpoly().size()])
		for name in TEXTURES:
			var tex := def.texture_lowpoly(name)
			_expect(tex != null and tex.get_width() <= MAX_ATLAS * 2 and tex.get_height() <= MAX_ATLAS, "%s: текстура уровня %s" % [id, name])
		for name in MODELS:
			var m := def.model(name)
			_expect(m != null, "%s: нет меша %s" % [id, name])
			if m == null:
				continue
			most = maxi(most, m.triangles())
			_expect(m.triangles() > 0 and m.triangles() <= LowpolyScreen.MAX_TRIS, "%s: у меша %s треугольников %d" % [id, name, m.triangles()])
			_expect(m.vertices.size() % 3 == 0 and m.normals.size() == m.vertices.size() and m.uvs.size() == m.vertices.size(),
					"%s: у меша %s вершин %d, нормалей %d, развёртки %d" % [id, name, m.vertices.size(), m.normals.size(), m.uvs.size()])
			_expect(m.texture != null and m.texture.get_width() <= MAX_ATLAS and m.texture.get_height() <= MAX_ATLAS,
					"%s: у меша %s нет атласа или он крупнее %d" % [id, name, MAX_ATLAS])
			var parts := m.part_names.size()
			var sum := 0
			for i in parts:
				sum += m.part_tris[i]
				_expect(m.part_parents[i] >= -1 and m.part_parents[i] < parts and m.part_parents[i] != i, "%s: у меша %s родитель части %d" % [id, name, m.part_parents[i]])
			_expect(parts > 0 and m.part_pivots.size() == parts and sum == m.triangles(), "%s: у меша %s части не сходятся" % [id, name])
			for uv in m.uvs:
				if uv.x < -0.001 or uv.x > 1.001 or uv.y < -0.001 or uv.y > 1.001:
					_expect(false, "%s: у меша %s развёртка за краем атласа: %s" % [id, name, uv])
					break
			if BIPEDS.has(name):
				for limb: StringName in [&"leg_l", &"leg_r", &"arm_l", &"arm_r"]:
					_expect(m.part_index(limb) >= 0, "%s: у %s нет части %s" % [id, name, limb])
				_expect(m.bounds().size.y > 1.6 and m.bounds().size.y < 1.95 and m.bounds().size.x < 0.75, "%s: у %s не человеческие пропорции: %s" % [id, name, m.bounds().size])
			var box := m.bounds()
			_expect(HELD.has(name) or box.position.y > -0.01 and box.size.y > 0.1 and box.size.y < 10.0, "%s: меш %s стоит не на нуле или не того роста: %s" % [id, name, box])
	# Провал «Проверни» (мини-игра технологии low poly) даёт баг «дыры в моделях» (#111), и у бага
	# есть слова под все пять жанров.
	var doorway := MinigamePool.find(MinigamePool.load_all(), &"doorway")
	_expect(doorway != null and doorway.scene != null, "«Проверни» всё ещё заглушка")
	var failed := GameRecord.create(Game.Genre.PLATFORMER, Game.Tech.LOWPOLY, 1, "Провал")
	var given := BugCatalog.load_default().apply_fail(doorway, failed)
	_expect(given != null and given.id == &"mesh_holes", "провал «Проверни» дал баг %s, не mesh_holes" % [given.id if given else &""])
	var holes_bug := BugCatalog.load_default().by_id(&"mesh_holes")
	_expect(holes_bug != null and holes_bug.spectacular, "mesh_holes не зрелищный")
	for g in Game.Genre.size():
		_expect(holes_bug != null and holes_bug.tweet_by_genre.has(g) and holes_bug.clip_by_genre.has(g), "mesh_holes: нет слов для жанра %d" % g)
	AutoTest.note("lowpoly: мешей %d, в меше до %d треугольников, текстур уровня %d" % [MODELS.size(), most, TEXTURES.size()])


## Экран: модель собирается в узлы по частям на шейдере PS1, грани смотрят наружу, земля,
## заглушка и чужая палитра.
func _check_screen() -> void:
	var pirates := SettingDef.of(Game.Setting.PIRATES)
	var s := LowpolyScreen.make(Vector2(480, 270), true, pirates.colors_lowpoly(), pirates.sky_lowpoly(), pirates.texture_lowpoly("sky"))
	add_child(s)
	_expect(s.viewport.own_world_3d and s.size.x <= 480.5 and s.view.x >= 159.0, "экран low poly %s в рамке 480×270" % s.view)
	_expect(not s.alien and s.pink_count == 0, "заглушки или чужая палитра без бага")
	_expect(s.sky_dome != null and s.material != null, "нет неба или дизеринга")
	var def := pirates.model("hero")
	var hero := s.model(def)
	s.world.add_child(hero)
	_expect(hero.parts.size() == def.part_names.size(), "у модели героя частей %d из %d" % [hero.parts.size(), def.part_names.size()])
	var faces := 0
	for node in hero.parts.values():
		var mesh := node.mesh as ArrayMesh
		faces += mesh.surface_get_array_len(0) / 3
		var mat := mesh.surface_get_material(0) as ShaderMaterial
		_expect(mat != null and mat.shader == LowpolyScreen.PS1_SHADER and mat.get_shader_parameter("tex") == def.texture, "часть героя не на шейдере PS1 со своим атласом")
	_expect(faces == def.triangles(), "в узлах героя граней %d, в меше %d" % [faces, def.triangles()])
	_expect(hero.part(&"head").get_parent() == hero.part(&"body"), "голова героя не на теле")
	# Грани наружу: у бочки и у ящика уровня обход по часовой стрелке совпадает с нормалью от центра.
	var barrel := s.model(pirates.model("barrel"))
	var crate := s.add_box(Vector3.ZERO, Vector3(5.0, 1.0, 2.0), pirates.texture_lowpoly("planks"))
	for item: Array in [[barrel.part(&"body").mesh, Vector3(0.0, 0.43, 0.0), 60], [crate.mesh, Vector3.ZERO, 2 * (2 * 1 + 2 * 1 + 1 * 1) * 2]]:
		var arrays := (item[0] as ArrayMesh).surface_get_arrays(0)
		var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var out := 0
		for t in verts.size() / 3:
			var mid := (verts[t * 3] + verts[t * 3 + 1] + verts[t * 3 + 2]) / 3.0 - (item[1] as Vector3)
			var wound := (verts[t * 3 + 2] - verts[t * 3]).cross(verts[t * 3 + 1] - verts[t * 3])
			if wound.dot(mid) > 0.0:
				out += 1
		_expect(out == verts.size() / 3 and out == int(item[2]), "наружу смотрят %d граней из %d, ждали %d" % [out, verts.size() / 3, int(item[2])])
	barrel.free()
	hero.walk(PI / 2.0, 0.5)
	_expect(is_equal_approx(hero.part(&"leg_l").rotation.x, 0.5) and is_equal_approx(hero.part(&"leg_r").rotation.x, -0.5), "шаг не качает ноги")
	# Земля: высота в узлах своя, между ними по треугольникам, юбка и верх построены.
	var land := LowpolyTerrain.make(Vector3(10.0, 2.0, -4.0), 1.0, 3, 2)
	land.set_h(1, 1, 0.5)
	land.set_h(2, 1, -0.25)
	_expect(is_equal_approx(land.height_at(11.0, -3.0), 2.5) and is_equal_approx(land.height_at(10.0, -4.0), 2.0), "земля: высота в узлах")
	_expect(is_equal_approx(land.height_at(11.5, -3.0), 2.125) and is_equal_approx(land.height_at(10.5, -3.5), 2.25), "земля: высота между узлами %.3f %.3f" % [
			land.height_at(11.5, -3.0), land.height_at(10.5, -3.5)])
	_expect(land.inside(12.9, -2.1) and not land.inside(13.1, -3.0), "земля: границы")
	var built := land.build(s, pirates.texture_lowpoly("sand"), 2.0, pirates.texture_lowpoly("rock"), 0.0)
	_expect(built.get_child_count() == 2 and ((built.get_child(0) as MeshInstance3D).mesh as ArrayMesh).surface_get_array_len(0) == 3 * 2 * 2 * 3
			and ((built.get_child(1) as MeshInstance3D).mesh as ArrayMesh).surface_get_array_len(0) == 10 * 6, "земля: меш верха или обрыва")
	var pink := s.pink_model(def)
	s.world.add_child(pink)
	_expect(pink.pink and pink.parts.is_empty() and s.pink_count == 1, "розовая заглушка не заглушка")
	var mat := s.tex_material(def.texture)
	_expect(is_zero_approx(float(mat.get_shader_parameter("hue_shift"))), "чужая палитра без бага")
	s.set_alien(0.45)
	_expect(s.alien and is_equal_approx(float(mat.get_shader_parameter("hue_shift")), 0.45), "чужая палитра не сдвинула оттенок")
	_expect(is_equal_approx(float(s.tex_material(pirates.texture_lowpoly("rock")).get_shader_parameter("hue_shift")), 0.45), "новый материал без чужой палитры")
	_expect(is_zero_approx(float((s.sky_dome.mesh.surface_get_material(0) as ShaderMaterial).get_shader_parameter("hue_shift"))), "чужая палитра тронула небо")
	# Дыры в моделях (#111): выключены без бага, включаются на старых и новых материалах, небо цело;
	# у каждой грани свой номер, у модели и уровня разная метка.
	_expect(is_zero_approx(s.holes) and is_zero_approx(float(mat.get_shader_parameter("holes"))), "дыры в моделях без бага")
	s.set_holes(0.24, 0.05, 0.14, 1.4)
	_expect(is_equal_approx(float(mat.get_shader_parameter("holes")), 0.24) and is_equal_approx(float(mat.get_shader_parameter("holes_level")), 0.05), "дыры не дошли до материала")
	_expect(is_equal_approx(float(s.tex_material(pirates.texture_lowpoly("sail")).get_shader_parameter("holes")), 0.24), "новый материал без дыр")
	_expect(is_zero_approx(float((s.sky_dome.mesh.surface_get_material(0) as ShaderMaterial).get_shader_parameter("holes"))), "дыры в небе")
	var marks: PackedColorArray = (hero.part(&"body").mesh as ArrayMesh).surface_get_arrays(0)[Mesh.ARRAY_COLOR]
	var crate_marks: PackedColorArray = (crate.mesh as ArrayMesh).surface_get_arrays(0)[Mesh.ARRAY_COLOR]
	_expect(marks.size() > 6 and is_equal_approx(marks[0].r, marks[2].r) and not is_equal_approx(marks[0].r, marks[3].r)
			and is_zero_approx(marks[0].g) and is_equal_approx(crate_marks[0].g, 1.0), "номера граней или метка уровня")
	s.queue_free()


## Камера за спиной и вид от первого лица.
func _check_cameras() -> void:
	var t := LowpolyTuning.load_default()
	var cam := LowpolyFollowCam.make(t)
	var target := Vector3(3.0, 1.0, -5.0)
	for i in 120:
		cam.step(1.0 / 60.0, target, 0.0, true)
	var back := cam.position - target
	_expect(back.z > 0.0 and absf(back.z - t.follow_distance) < 0.1 and absf(back.y - t.follow_height) < 0.1, "камера за спиной не позади цели: %s" % back)
	_expect(cam.to_world(Vector2(0, -1)).is_equal_approx(Vector3(0, 0, -1)) and cam.to_world(Vector2(1, 0)).is_equal_approx(Vector3(1, 0, 0)), "ввод не по камере")
	_expect(cam.to_axis(cam.to_world(Vector2(0.3, -0.8))).is_equal_approx(Vector2(0.3, -0.8)), "ввод и направление не обратны")
	# Герой повернул вправо (в +X): камера доворачивает и встаёт слева от него.
	for i in 300:
		cam.step(1.0 / 60.0, target, -PI / 2.0, true)
	_expect((cam.position - target).x < -t.follow_distance * 0.9, "камера не довернула за курсом: %s" % (cam.position - target))
	var still := cam.yaw
	cam.step(1.0 / 60.0, target, PI / 2.0, false)
	_expect(is_equal_approx(cam.yaw, still), "камера доворачивает без спроса")
	var node := Camera3D.new()
	cam.apply(node)
	_expect((-node.transform.basis.z).dot((target - cam.position).normalized()) > 0.9, "камера не смотрит на цель")
	var fp := LowpolyFirstPerson.make(t)
	_expect(fp.wish(Vector2(0, 1)).is_equal_approx(Vector3(0, 0, -1)), "первое лицо: вперёд не −Z")
	fp.turn(1.0, 0.25)
	_expect(fp.forward().x > 0.0 and fp.wish(Vector2(1, 0)).z > 0.0, "первое лицо: поворот вправо не вправо")
	_expect(fp.bearing_to(Vector3(0, 0, -10)) < 0.0 and fp.bearing_to(Vector3(10, 0, 0)) > 0.0, "первое лицо: пеленг не туда")
	fp.look_by(Vector2(0.0, 10.0))
	_expect(is_equal_approx(fp.pitch, -t.pitch_limit), "первое лицо: наклон без предела")
	fp.apply(node)
	_expect(is_equal_approx(node.position.y, t.eye_height) and node.transform.basis.z.y > 0.0, "первое лицо: камера не на высоте глаз или не смотрит вниз")
	node.free()


## Встроенный режим (стрим ленты): обе пробы в рамке 480×270, бот идёт сам.
func _check_embedded() -> void:
	for script: GDScript in [ProbeBehind, ProbeFirst]:
		var holder := Control.new()
		holder.position = Vector2(1400, 780)
		add_child(holder)
		var d: Demo = script.new()
		d.setup(GameRecord.create(Game.Genre.PLATFORMER, Game.Tech.LOWPOLY, 3, "Стрим"), &"feed")
		d.embed(Vector2(480, 270))
		holder.add_child(d)
		d.start()
		await get_tree().create_timer(1.0).timeout
		_expect(d.lowpoly != null and d.lowpoly.size.x <= 480.5 and d.lowpoly.size.y <= 270.5, "встроенный экран low poly не в рамке")
		_expect(float(d.get("travelled")) > 1.0, "встроенный бот стоит: %.2f м" % float(d.get("travelled")))
		_expect(not d.lowpoly.alien and d.lowpoly.pink_count == 0, "баги без бага во встроенной пробе")
		holder.queue_free()


# --- Обзор мышью и стиком (#109) ----------------------------------------------------------------

func _check_look() -> void:
	AutoTest.bot_mode = AutoTest.BotMode.OFF
	var look := LookTuning.load_default()
	var saved := Vector2(Options.mouse_look, Options.stick_look)
	Options.mouse_look = 0.5
	Options.stick_look = 0.5
	for action: StringName in [GameInput.LOOK_LEFT, GameInput.LOOK_RIGHT]:
		for ev in InputMap.action_get_events(action):
			_expect(not ev is InputEventJoypadMotion, "правый стик остался клавишей в %s" % action)
	# Проба от первого лица: мышь вправо и вниз.
	var probe: Demo = ProbeFirst.new()
	probe.setup(GameRecord.create(Game.Genre.SHOOTER, Game.Tech.LOWPOLY, 1, "Обзор"), &"debug")
	add_child(probe)
	probe.start()
	await _until_running(probe)
	var fp: LowpolyFirstPerson = probe.get("fp")
	_expect(probe.look_enabled and Input.mouse_mode == Input.MOUSE_MODE_VISIBLE, "обзор не включён или автотест захватил курсор")
	var yaw := fp.yaw
	await _mouse(Vector2(200, 50))
	var per_px := look.mouse_speed(0.5)
	_expect(is_equal_approx(fp.yaw, yaw - 200.0 * per_px) and is_equal_approx(fp.pitch, -50.0 * per_px), "мышь: курс %.3f → %.3f, наклон %.3f, ждали −%.3f и −%.3f" % [
			yaw, fp.yaw, fp.pitch, 200.0 * per_px, 50.0 * per_px])
	Options.mouse_look = 1.0
	yaw = fp.yaw
	await _mouse(Vector2(-100, 0))
	_expect(is_equal_approx(fp.yaw, yaw + 100.0 * look.mouse_max) and look.mouse_max > per_px, "чувствительность мыши из настроек не действует")
	await _mouse(Vector2(0, 100000))
	_expect(is_equal_approx(fp.pitch, -fp.pitch_limit), "наклон мышью без предела: %.2f" % fp.pitch)
	# Пауза глушит обзор и после неё ничего не накоплено.
	probe._open_pause()
	yaw = fp.yaw
	await _mouse(Vector2(300, 0))
	probe._resume()
	await get_tree().process_frame
	await get_tree().process_frame
	_expect(is_equal_approx(fp.yaw, yaw), "мышь на паузе повернула камеру")
	# Правый стик: мёртвая зона, скорость по настройке, наклон медленнее.
	_expect(probe.look_stick(Vector2(look.stick_deadzone * 0.9, 0.0), 1.0) == Vector2.ZERO, "стик в мёртвой зоне поворачивает")
	var full := probe.look_stick(Vector2(1.0, 0.0), 0.5)
	_expect(is_equal_approx(full.x, look.stick_speed(0.5) * 0.5) and is_zero_approx(full.y), "стик до упора: %s" % full)
	var down := probe.look_stick(Vector2(0.0, 1.0), 1.0)
	_expect(is_equal_approx(down.y, look.stick_speed(0.5) * look.stick_pitch), "наклон стиком: %s" % down)
	Options.stick_look = 0.0
	_expect(is_equal_approx(probe.look_stick(Vector2(1.0, 0.0), 1.0).x, look.stick_min) and look.stick_min < look.stick_max, "чувствительность стика из настроек не действует")
	probe.queue_free()
	await get_tree().process_frame
	# Во встроенном режиме (стрим ленты) обзора нет.
	var stream: Demo = ProbeFirst.new()
	stream.setup(GameRecord.create(Game.Genre.SHOOTER, Game.Tech.LOWPOLY, 1, "Стрим"), &"feed")
	stream.embed(Vector2(480, 270))
	add_child(stream)
	stream.start()
	_expect(not stream.look_enabled, "обзор включён во встроенной демке")
	stream.queue_free()
	# Рейкастер 16/32: мышь поворачивает курс.
	Options.mouse_look = 0.5
	var shooter := DemoCatalog.create(GameRecord.create(Game.Genre.SHOOTER, Game.Tech.BIT16, 1, "Обзор"))
	_expect(shooter != null, "нет демки шутер × 16/32")
	if shooter != null:
		shooter.setup(GameRecord.create(Game.Genre.SHOOTER, Game.Tech.BIT16, 1, "Обзор"), &"debug")
		add_child(shooter)
		shooter.start()
		await _until_running(shooter)
		var sim: HoldSim = shooter.get("sim")
		var angle := sim.angle
		await _mouse(Vector2(100, 0))
		_expect(is_equal_approx(angle_difference(angle, sim.angle), 100.0 * per_px), "рейкастер: курс %.3f → %.3f, ждали +%.3f" % [angle, sim.angle, 100.0 * per_px])
		shooter.queue_free()
	Options.mouse_look = saved.x
	Options.stick_look = saved.y
	AutoTest.note("look: мышь %.4f рад/пиксель на середине, стик %.1f рад/с, пауза глушит, рейкастер поворачивает" % [per_px, look.stick_speed(0.5)])


func _until_running(d: Demo) -> void:
	for i in 240:
		if d.running:
			return
		await get_tree().process_frame


## Движение захваченной мыши на `rel` пикселей и два кадра на обработку.
func _mouse(rel: Vector2) -> void:
	var m := InputEventMouseMotion.new()
	m.relative = rel
	m.screen_relative = rel
	get_viewport().push_input(m, true)
	await get_tree().process_frame
	await get_tree().process_frame
	await get_tree().process_frame


# --- Пробные демки -----------------------------------------------------------------------------

func _launch() -> void:
	record = GameRecord.create(Game.Genre.PLATFORMER if _probe != "first" else Game.Genre.SHOOTER, Game.Tech.LOWPOLY,
			int(_args.get("seed", Debug.demo_seed)), "Проба low poly", int(_args.get("setting", Debug.demo_setting)) as Game.Setting)
	if AutoTest.enabled:
		if _args.has("bugs"):
			for id in COMMON_BUGS:
				record.add_bug(id)
		if _args.has("bug"):
			record.add_bug(StringName(str(_args["bug"])))
	else:
		for id in Debug.demo_bugs:
			record.add_bug(id)
	demo = ProbeFirst.new() if _probe == "first" else ProbeBehind.new()
	demo.setup(record, &"debug")
	demo.demo_finished.connect(_on_finished)
	add_child(demo)
	demo.start()


func _on_finished(_r: GameRecord, reached: bool) -> void:
	var probe := demo
	demo = null
	if not AutoTest.enabled or _args.has("no-checks"):
		probe.queue_free()
		_launch()
		return
	var win := AutoTest.bot_mode != AutoTest.BotMode.LOSE
	_expect(reached == win, "бот %s: проба %s кончилась %s" % ["WIN" if win else "LOSE", _probe, reached])
	_expect(record.has_bug(&"pink_placeholders") == (probe.lowpoly.pink_count > 0), "розовых заглушек %d при баге %s" % [
			probe.lowpoly.pink_count, record.has_bug(&"pink_placeholders")])
	_expect(probe.lowpoly.alien == record.has_bug(&"alien_palette"), "чужая палитра %s при баге %s" % [probe.lowpoly.alien,
			record.has_bug(&"alien_palette")])
	_expect((probe.lowpoly.holes > 0.0) == record.has_bug(&"mesh_holes"), "дыры в моделях %.2f при баге %s" % [probe.lowpoly.holes,
			record.has_bug(&"mesh_holes")])
	if win:
		_expect(int(probe.get("collected")) > 0, "бот не собрал ни одного дублона")
	else:
		_expect(int(probe.get("lives")) == 0, "бот LOSE кончил с жизнями %d" % int(probe.get("lives")))
	AutoTest.note("lowpoly probe %s: дублонов %d, жизней %d%s, %.1f с, %.0f м, экран %s, баги %s" % [_probe, int(probe.get("collected")),
			int(probe.get("lives")), " (%s)" % ", ".join(probe.get("deaths")) if probe.get("deaths") else "", probe.elapsed,
			float(probe.get("travelled")), probe.lowpoly.view, record.bug_ids])
	probe.queue_free()
	AutoTest.fulfill("lowpoly probe")


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("lowpoly: " + what)
