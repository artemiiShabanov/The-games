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
## `--setting=N`, `--seed=N`, `--no-checks` без проверок.

const ProbeBehind := preload("res://debug/scenes/lowpoly_probe_behind.gd")
const ProbeFirst := preload("res://debug/scenes/lowpoly_probe_first.gd")
const COMMON_BUGS: Array[StringName] = [&"frame_drops", &"audio_stutter", &"sticky_input",
		&"pink_placeholders", &"alien_palette"]
## Меши стартового набора; у двуногих есть ноги и руки.
const MODELS: Array[String] = ["hero", "enemy", "coin", "rock", "barrel", "chest", "flag", "cannon"]
const BIPEDS: Array[String] = ["hero", "enemy"]
const TEXTURES: Array[String] = ["sand", "planks", "water", "rock", "sail", "sky"]
const MAX_ATLAS := 64
const COLUMNS := 5
const CELL := 2.2

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
		m.position = at
		_sheet.world.add_child(m)
		_sheet.add_shadow(0.45).position = at + Vector3(0.0, 0.03, 0.0)
		_models.append(m)
		_labels.append("заглушка" if is_pink else "%s %d" % [names[i], def.triangles() if def != null else 0])
	_sheet.camera.transform = Transform3D(Basis.IDENTITY, Vector3(0.0, 3.4, 6.2)).looking_at(Vector3(0.0, 0.7, 0.0))


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
			_expect(box.position.y > -0.01 and box.size.y > 0.1 and box.size.y < 3.5, "%s: меш %s стоит не на нуле или не того роста: %s" % [id, name, box])
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
