extends Control
## Тест векторной основы (#88). По умолчанию лист контуров трёх сеттингов: каждый своим
## векторным экраном и цветами, все слоты контурами с подписью и штриховые цифры; под
## автотестом проверки: у каждого слота каждого сеттинга есть контур, он не пустой и не
## разросся (точек не больше `MAX_POINTS`), цвета луча заданы, цифры рисуются. `--probe` (или
## «Вектор: пробная демка» в дебаг-меню) запускает пробную демку в карточке: бот WIN бежит до
## флага; `--bugs` все общие баги, `--bug=<id>` один, `--setting=N`, `--no-checks` без проверок.

const ProbeDemo := preload("res://debug/scenes/vector_probe_demo.gd")
const MAX_POINTS := 60
const COMMON_BUGS: Array[StringName] = [&"frame_drops", &"audio_stutter", &"sticky_input",
		&"pink_placeholders", &"alien_palette"]
const SHEET_PX := 5.0

var demo: Demo
var record: GameRecord
var _args := {}
var _saw_pink := false
var _segments := 0


func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Color.BLACK
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	_args = AutoTest.parse_args(OS.get_cmdline_user_args()) if AutoTest.enabled else {}
	var probe := _args.has("probe") or (not AutoTest.enabled and Debug.vector_probe)
	Debug.vector_probe = false
	if probe:
		if AutoTest.enabled and not _args.has("no-checks"):
			AutoTest.require("vector probe")
		_launch()
		return
	_build_sheet()
	if AutoTest.enabled and not _args.has("no-checks"):
		AutoTest.require("vector checks")
		_check_settings()
		await _check_embedded()
		AutoTest.fulfill("vector checks")


# --- Лист контуров ---------------------------------------------------------------------------

func _build_sheet() -> void:
	var col_w := float(Style.SCREEN.x) / SettingDef.IDS.size()
	for s in SettingDef.IDS.size():
		var def := SettingDef.of(s as Game.Setting)
		var area := Vector2(col_w, Style.SCREEN.y)
		var v := VectorScreen.make(area, area, def.vector_colors)
		v.position = Vector2(s * col_w, 0)
		v.draw_fn = _sheet_drawer(def)
		add_child(v)
		var title := Label.new()
		title.text = SettingDef.IDS[s]
		title.position = Vector2(s * col_w + 24, 16)
		title.add_theme_color_override("font_color", def.vector_colors[2])
		add_child(title)
		var slots := SettingDef.VECTOR_SLOTS.keys()
		for i in slots.size():
			var l := Label.new()
			l.text = String(slots[i])
			l.position = Vector2(s * col_w + 24 + (i % 3) * 210, 150 + (i / 3) * 170)
			l.add_theme_color_override("font_color", Color(def.vector_colors[1], 0.6))
			l.add_theme_font_size_override("font_size", Style.FONT_CAPTION)
			add_child(l)


func _sheet_drawer(def: SettingDef) -> Callable:
	return func(v: VectorScreen) -> void:
		var slots := SettingDef.VECTOR_SLOTS.keys()
		for i in slots.size():
			var slot: StringName = slots[i]
			var c := Vector2(110 + (i % 3) * 210, 100 + (i / 3) * 170)
			v.shape(def.vector_contours(slot), c, SHEET_PX, def.vector_ink(slot))
		v.digits(Vector2(24, 1000), "0123456789 :/-+x!", 36.0, 2)
		v.line(Vector2(24, 980), Vector2(600, 980), 1)


# --- Проверки ---------------------------------------------------------------------------------

func _check_settings() -> void:
	for s in SettingDef.IDS.size():
		var def := SettingDef.of(s as Game.Setting)
		var id := SettingDef.IDS[s]
		_expect(def.vector_colors.size() >= 4, "%s: цветов луча %d, нужно фон и три чернил" % [id, def.vector_colors.size()])
		var total := 0
		for slot in SettingDef.VECTOR_SLOTS:
			var cs := def.vector_contours(slot)
			var n := 0
			var box := Rect2()
			for c in cs:
				n += c.size()
				for p in c:
					box = box.expand(p)
			_expect(not cs.is_empty(), "%s: у слота %s нет контура" % [id, slot])
			_expect(n <= MAX_POINTS, "%s: контур %s разросся, %d точек" % [id, slot, n])
			_expect(box.size.x <= 32.0 and box.size.y <= 64.0, "%s: контур %s больше спрайта %s" % [id, slot, box.size])
			total += n
		AutoTest.note("vector %s: %d слотов, точек всего %d" % [id, SettingDef.VECTOR_SLOTS.size(), total])
	# Квадрат 4×4 с дыркой: внешний обход 4 точки, дырка в пиксель отброшена.
	var img := Image.create(6, 6, false, Image.FORMAT_RGBA8)
	img.fill_rect(Rect2i(1, 1, 4, 4), Color.WHITE)
	img.set_pixel(2, 2, Color(0, 0, 0, 0))
	var traced := VectorShapes.trace(img)
	_expect(traced.size() == 1 and traced[0].size() == 4, "трассировка квадрата дала %s" % [traced])


## Встроенный режим (стрим ленты): тот же экран в рамке 480×270, бот бежит сам.
func _check_embedded() -> void:
	var holder := Control.new()
	holder.position = Vector2(1400, 780)
	add_child(holder)
	var d: Demo = ProbeDemo.new()
	d.setup(GameRecord.create(Game.Genre.PLATFORMER, Game.Tech.VECTOR, 3, "Стрим"), &"feed")
	d.embed(Vector2(480, 270))
	holder.add_child(d)
	d.start()
	await get_tree().create_timer(0.6).timeout
	_expect(d.vector.size.x <= 480.5 and d.vector.size.y <= 270.5, "встроенный экран %s не в рамке" % d.vector.size)
	_expect(float(d.get("hero_x")) > 130.0, "встроенный бот стоит")
	holder.queue_free()


# --- Пробная демка ----------------------------------------------------------------------------

func _launch() -> void:
	record = GameRecord.create(Game.Genre.PLATFORMER, Game.Tech.VECTOR, Debug.demo_seed, "Проба вектора",
			int(_args.get("setting", Debug.demo_setting)) as Game.Setting)
	if AutoTest.enabled:
		if _args.has("bugs"):
			for id in COMMON_BUGS:
				record.add_bug(id)
		if _args.has("bug"):
			record.add_bug(StringName(str(_args["bug"])))
	else:
		for id in Debug.demo_bugs:
			record.add_bug(id)
	demo = ProbeDemo.new()
	demo.setup(record, &"debug")
	demo.demo_finished.connect(_on_finished)
	add_child(demo)
	demo.start()


func _process(_delta: float) -> void:
	if demo == null or demo.vector == null:
		return
	if demo.vector.pink_drawn > 0:
		_saw_pink = true
	_segments = maxi(_segments, demo.vector.segments)


func _on_finished(_r: GameRecord, reached: bool) -> void:
	var probe := demo
	demo = null
	if not AutoTest.enabled or _args.has("no-checks"):
		probe.queue_free()
		_launch()
		return
	_expect(reached, "WIN: бот не добежал до флага")
	_expect(record.has_bug(&"pink_placeholders") == _saw_pink, "розовые кресты %s при баге %s" % [_saw_pink,
			record.has_bug(&"pink_placeholders")])
	_expect((probe.vector.material != null) == record.has_bug(&"alien_palette"), "чужая палитра не на экране")
	_expect(_segments > 50, "за кадр нарисовано всего %d отрезков" % _segments)
	AutoTest.note("vector probe: %d монет, %.1f с, до %d отрезков за кадр, баги %s" % [probe.collected,
			probe.elapsed, _segments, record.bug_ids])
	probe.queue_free()
	AutoTest.fulfill("vector probe")


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("vector: " + what)
