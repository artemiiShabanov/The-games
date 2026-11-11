extends Control
## Тест основы ASCII-демок (#88). По умолчанию лист глифов трёх сеттингов: каждый своей
## палитрой, слоты с глифом, чернилами и словом, под ними пробная сцена и легенда; под
## автотестом проверки читаемости (`SettingDef`): все слоты есть и узкие в атласе, чернила в
## палитре, земля из разрешённых глифов, герой самый плотный из не-земли, глифы попарно
## различимы, пищалка даёт звук. `--probe` (или «ASCII: пробная демка» в дебаг-меню) запускает
## пробную демку `ascii_probe_demo.gd` в карточке: бот WIN доходит до флага, LOSE стоит;
## `--bugs` все общие баги, `--bug=<id>` один, `--setting=N` сеттинг, `--no-checks` без проверок.

const ProbeDemo := preload("res://debug/scenes/ascii_probe_demo.gd")
## Минимум различающихся пикселей между двумя глифами одного сеттинга.
const MIN_DIFF_PX := 10
## Общие баги, которые показывает основа (технологический ASCII приходит с «Разгони», #89).
const COMMON_BUGS: Array[StringName] = [&"frame_drops", &"audio_stutter", &"sticky_input",
		&"pink_placeholders", &"alien_palette"]
const SHEET_COLS := 40

var demo: Demo
var record: GameRecord
var _args := {}
var _phase := 0
var _saw_pink := false


func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	_args = AutoTest.parse_args(OS.get_cmdline_user_args()) if AutoTest.enabled else {}
	var probe := _args.has("probe") or (not AutoTest.enabled and Debug.ascii_probe)
	Debug.ascii_probe = false
	if probe:
		if AutoTest.enabled and not _args.has("no-checks"):
			AutoTest.require("ascii probe")
		_launch()
		return
	_build_sheet()
	if AutoTest.enabled and not _args.has("no-checks"):
		AutoTest.require("ascii checks")
		_check_settings()
		_check_audio()
		await _check_embedded()
		AutoTest.fulfill("ascii checks")


# --- Лист глифов ------------------------------------------------------------------------------

func _build_sheet() -> void:
	var rows := int(Style.SCREEN.y / (AsciiGrid.CELL.y * Demo.ASCII_SCALE))
	for s in SettingDef.IDS.size():
		var def := SettingDef.of(s as Game.Setting)
		var g := AsciiGrid.make(SHEET_COLS, rows, def.ascii_palette)
		g.scale = Vector2.ONE * Demo.ASCII_SCALE
		g.position = Vector2(s * SHEET_COLS * AsciiGrid.CELL.x * Demo.ASCII_SCALE, 0)
		add_child(g)
		g.text(1, 1, SettingDef.IDS[s].to_upper(), 2)
		for i in SettingDef.ASCII_SLOTS.size():
			var slot := SettingDef.ASCII_SLOTS[i]
			g.put(2, 3 + i, def.ascii_glyph(slot), def.ascii_ink(slot))
			g.text(4, 3 + i, String(slot), 3)
			g.text(14, 3 + i, str(def.ascii_names.get(slot, "")), 1)
		var top := 4 + SettingDef.ASCII_SLOTS.size()
		_sample(g, def, top)


## Кусок уровня под слотами: так глифы видно рядом, как в демке.
func _sample(g: AsciiGrid, def: SettingDef, top: int) -> void:
	var put := func(x: int, y: int, slot: StringName) -> void:
		g.put(x, y, def.ascii_glyph(slot), def.ascii_ink(slot))
	var floor_y := top + 7
	for x in SHEET_COLS:
		put.call(x, floor_y, &"ground")
		put.call(x, floor_y + 1, &"ground")
	for y in range(top, floor_y):
		put.call(0, y, &"wall")
		put.call(SHEET_COLS - 1, y, &"wall")
	for x in range(12, 26):
		put.call(x, floor_y - 4, &"platform")
	for p in [[3, &"hero"], [7, &"bonus"], [9, &"bonus"], [13, &"prop_a"], [17, &"enemy"], [21, &"obstacle"],
			[24, &"enemy_2"], [28, &"vehicle"], [30, &"rival"], [33, &"prop_b"], [37, &"finish"]]:
		put.call(int(p[0]), floor_y - 1, p[1])
	for p in [[14, &"ball"], [18, &"shot"], [22, &"goal"]]:
		put.call(int(p[0]), floor_y - 5, p[1])
	var line := def.ascii_legend([&"hero", &"enemy", &"bonus"])
	g.text((SHEET_COLS - line.length()) / 2, floor_y + 3, line, 3)


# --- Проверки ---------------------------------------------------------------------------------

func _check_settings() -> void:
	for s in SettingDef.IDS.size():
		var def := SettingDef.of(s as Game.Setting)
		var id := SettingDef.IDS[s]
		var bits: Dictionary[StringName, Array] = {}
		_expect(def.ascii_palette.size() >= 2, "%s: палитра %d цветов" % [id, def.ascii_palette.size()])
		for slot in SettingDef.ASCII_SLOTS:
			var ch := def.ascii_glyph(slot)
			if not def.ascii_glyphs.has(slot) or not AsciiGrid.has_glyph(ch):
				_expect(false, "%s: у слота %s нет узкого глифа «%s»" % [id, slot, ch])
				continue
			var ink := def.ascii_ink(slot)
			_expect(ink >= 1 and ink < def.ascii_palette.size(), "%s: чернила %d у %s вне палитры" % [id, ink, slot])
			_expect(def.ascii_names.has(slot), "%s: у %s нет слова для легенды" % [id, slot])
			if slot in SettingDef.ASCII_TERRAIN:
				_expect(SettingDef.ASCII_TERRAIN_GLYPHS.contains(ch), "%s: %s «%s» не из %s" % [id, slot, ch, SettingDef.ASCII_TERRAIN_GLYPHS])
			bits[slot] = AsciiGrid.glyph_bits(ch)
		var hero := _count(bits.get(&"hero", []))
		for slot in bits:
			if slot != &"hero" and not slot in SettingDef.ASCII_TERRAIN:
				_expect(_count(bits[slot]) < hero, "%s: %s «%s» плотнее героя (%d ≥ %d)" % [id, slot,
						def.ascii_glyph(slot), _count(bits[slot]), hero])
		var slots := bits.keys()
		for i in slots.size():
			for j in range(i + 1, slots.size()):
				var d := _diff(bits[slots[i]], bits[slots[j]])
				_expect(d >= MIN_DIFF_PX, "%s: %s и %s почти одинаковые (%d px)" % [id, slots[i], slots[j], d])
		var legend := def.ascii_legend([&"hero", &"enemy", &"bonus", &"finish"])
		_expect(legend.length() <= Demo.ascii_size().x, "%s: легенда длиннее экрана" % id)
		AutoTest.note("ascii %s: герой %d px, легенда «%s»" % [id, hero, legend])
	AutoTest.note("ascii: сетка %s, глифов в атласе %d" % [Demo.ascii_size(), AsciiCodepoints.CODES.size()])


func _check_audio() -> void:
	var beep := Sfx.beep(440.0, 0.1)
	var loop := Sfx.beeper_loop(ProbeDemo.MELODY)
	_expect(beep.data.size() > 1000 and loop.data.size() > 10000, "пищалка без звука")


## Встроенный режим (стрим ленты): та же сетка, уменьшенная в рамку 480×270, бот идёт сам.
func _check_embedded() -> void:
	var holder := Control.new()
	holder.position = Vector2(1400, 780)
	add_child(holder)
	var d: Demo = ProbeDemo.new()
	d.setup(GameRecord.create(Game.Genre.PLATFORMER, Game.Tech.ASCII, 3, "Стрим"), &"feed")
	d.embed(Vector2(480, 270))
	holder.add_child(d)
	d.start()
	await get_tree().create_timer(0.6).timeout
	var px := d.ascii.pixel_size() * d.ascii.scale
	_expect(px.x <= 480.5 and px.y <= 270.5 and d.ascii.scale.x < 1.0, "встроенная сетка %s не в рамке" % px)
	_expect(d.get("hero").x > 2, "встроенный бот стоит")
	holder.queue_free()


static func _count(b: Array) -> int:
	var n := 0
	for v: bool in b:
		n += int(v)
	return n


static func _diff(a: Array, b: Array) -> int:
	var n := 0
	for i in mini(a.size(), b.size()):
		n += int(a[i] != b[i])
	return n


# --- Пробная демка ----------------------------------------------------------------------------

func _launch() -> void:
	record = GameRecord.create(Game.Genre.PLATFORMER, Game.Tech.ASCII, Debug.demo_seed, "Проба ASCII",
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
	if demo != null and demo.ascii != null and demo.ascii.dump().contains("?"):
		_saw_pink = true


func _on_finished(_r: GameRecord, reached: bool) -> void:
	var probe := demo
	demo = null
	if not AutoTest.enabled or _args.has("no-checks"):
		probe.queue_free()
		_launch()
		return
	match _phase:
		0:
			_expect(reached, "WIN: бот не дошёл до флага")
			_expect(record.has_bug(&"pink_placeholders") == _saw_pink, "розовые «?» %s при баге %s" % [_saw_pink,
					record.has_bug(&"pink_placeholders")])
			_expect((probe.ascii.material != null) == record.has_bug(&"alien_palette"), "чужая палитра не на сетке")
			AutoTest.note("ascii probe: %d дублонов, %.1f с, баги %s" % [probe.collected, probe.elapsed, record.bug_ids])
			probe.queue_free()
			AutoTest.fulfill("ascii probe")
			_phase = 1


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("ascii: " + what)
