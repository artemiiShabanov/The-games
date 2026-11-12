extends Control
## Тест основы 16/32-bit (#95). По умолчанию лист: у каждого сеттинга палитра из 16 цветов и
## все ленты кадров в движении (у космоса и замков пока пиратские). Под автотестом проверки:
## палитра есть и в ней 16 цветов, каждая лента грузится, кадр 32 пикселя и число кадров
## сходится, цвета пиратских спрайтов не выходят из палитры, вид вглубь уменьшает дальнее,
## обе пробные демки идут во встроенном режиме. `--probe=side` или `--probe=depth` (или
## «16/32: проба сбоку», «16/32: проба вглубь» в дебаг-меню) запускает пробную демку в карточке:
## бот WIN добирается до конца; `--bugs` все общие баги, `--bug=<id>` один, `--setting=N`,
## `--no-checks` без проверок.

const ProbeSide := preload("res://debug/scenes/bit16_probe_side.gd")
const ProbeDepth := preload("res://debug/scenes/bit16_probe_depth.gd")
const COMMON_BUGS: Array[StringName] = [&"frame_drops", &"audio_stutter", &"sticky_input",
		&"pink_placeholders", &"alien_palette"]
## Ленты стартового набора и сколько в каждой кадров; 0 значит не лента кадров, а слой фона.
const SPRITES := {"hero_run": 6, "hero_jump": 1, "hero_back": 6, "enemy_walk": 6, "enemy_front": 6, "coin": 6,
		"flag": 6, "ground": 1, "ground_inner": 1, "rock": 1, "chest": 1, "par_sky": 0, "par_far": 0, "par_mid": 0}
const SHEET_SCALE := 3.0

var demo: Demo
var record: GameRecord
var _args := {}
var _probe := ""
var _saw_pink := false
var _sheet: Control
## Ленты листа по сеттингу и имени: лист держит их сам, иначе текстура освободится до отрисовки.
var _textures := {}
var _t := 0.0


func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Color("#26323F")
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	_args = AutoTest.parse_args(OS.get_cmdline_user_args()) if AutoTest.enabled else {}
	_probe = str(_args.get("probe", "")) if AutoTest.enabled else Debug.bit16_probe
	Debug.bit16_probe = ""
	if _probe != "":
		if AutoTest.enabled and not _args.has("no-checks"):
			AutoTest.require("bit16 probe")
		_launch()
		return
	_build_sheet()
	if AutoTest.enabled and not _args.has("no-checks"):
		AutoTest.require("bit16 checks")
		_check_assets()
		_check_scaler()
		await _check_embedded()
		AutoTest.fulfill("bit16 checks")


func _process(delta: float) -> void:
	_t += delta
	if _sheet != null:
		_sheet.queue_redraw()
	if demo != null and demo.bit16 != null and demo.bit16.pink_drawn > 0:
		_saw_pink = true


# --- Лист --------------------------------------------------------------------------------------

func _build_sheet() -> void:
	_sheet = Control.new()
	_sheet.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_sheet.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_sheet.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_sheet.draw.connect(_draw_sheet)
	add_child(_sheet)
	var col_w := float(Style.SCREEN.x) / SettingDef.IDS.size()
	for s in SettingDef.IDS.size():
		var title := Label.new()
		title.text = "%s%s" % [SettingDef.IDS[s], "" if _own_sprites(s) else " (спрайты пиратов)"]
		title.position = Vector2(s * col_w + 24, 14)
		add_child(title)


func _own_sprites(s: int) -> bool:
	return ResourceLoader.exists(SettingDef.of(s as Game.Setting).sprites_16bit + "hero_run.png")


func _draw_sheet() -> void:
	var col_w := float(Style.SCREEN.x) / SettingDef.IDS.size()
	for s in SettingDef.IDS.size():
		var def := SettingDef.of(s as Game.Setting)
		var x0 := s * col_w + 24.0
		var pal := def.colors16()
		for i in pal.size():
			_sheet.draw_rect(Rect2(x0 + i * 34.0, 52.0, 30.0, 30.0), pal[i])
		var y := 104.0
		var x := x0
		for name: String in SPRITES:
			var key := "%d:%s" % [s, name]
			if not _textures.has(key):
				_textures[key] = def.sprite16(name)
			var tex: Texture2D = _textures[key]
			if tex == null:
				continue
			var frames: int = SPRITES[name]
			if frames == 0:
				# Слой фона целиком, вдвое мельче листа.
				if x > x0:
					x = x0
					y += 32.0 * SHEET_SCALE + 10.0
				_sheet.draw_texture_rect(tex, Rect2(x0, y, tex.get_width() * 2.0, tex.get_height() * 2.0), false)
				y += tex.get_height() * 2.0 + 10.0
				continue
			var frame := int(_t * 8.0) % frames
			var size := Vector2(32.0, tex.get_height()) * SHEET_SCALE
			if x + size.x > x0 + col_w - 40.0:
				x = x0
				y += size.y + 10.0
			_sheet.draw_texture_rect_region(tex, Rect2(Vector2(x, y), size), Rect2(frame * 32.0, 0, 32.0, tex.get_height()))
			x += size.x + 10.0


# --- Проверки ----------------------------------------------------------------------------------

func _check_assets() -> void:
	var pirates := SettingDef.of(Game.Setting.PIRATES)
	_expect(pirates.bit16_colors.size() == 16, "у пиратов в палитре 16/32 цветов %d, нужно 16" % pirates.bit16_colors.size())
	var allowed := {}
	for c in pirates.bit16_colors:
		allowed[c.to_rgba32()] = true
	for s in SettingDef.IDS.size():
		var def := SettingDef.of(s as Game.Setting)
		var id := SettingDef.IDS[s]
		_expect(def.colors16().size() == 16, "%s: палитра 16/32 из %d цветов" % [id, def.colors16().size()])
		for name: String in SPRITES:
			var tex := def.sprite16(name)
			_expect(tex != null, "%s: нет ленты %s" % [id, name])
			if tex == null:
				continue
			var frames: int = SPRITES[name]
			if frames > 0:
				_expect(tex.get_width() == frames * Bit16Screen.FRAME and Bit16Screen.frames(tex) == frames,
						"%s: лента %s шириной %d, а кадров должно быть %d" % [id, name, tex.get_width(), frames])
				_expect(tex.get_height() == 32 or tex.get_height() == 64, "%s: лента %s высотой %d" % [id, name, tex.get_height()])
	# Пиратские спрайты нарисованы только цветами своей палитры.
	var stray := 0
	for name: String in SPRITES:
		var img := pirates.sprite16(name).get_image()
		for y in img.get_height():
			for x in img.get_width():
				var c := img.get_pixel(x, y)
				if c.a > 0.5 and not allowed.has(Color(c.r, c.g, c.b, 1.0).to_rgba32()):
					stray += 1
	_expect(stray == 0, "в пиратских спрайтах 16/32 пикселей вне палитры: %d" % stray)
	AutoTest.note("bit16: лент %d, палитра 16 цветов, пикселей вне палитры %d" % [SPRITES.size(), stray])


## Вид вглубь: дальнее мельче и выше на экране, строка экрана и расстояние обратны друг другу.
func _check_scaler() -> void:
	var sc := Scaler16.make(Vector2(832, 416))
	var near := sc.project(0.0, 100.0)
	var far := sc.project(0.0, 800.0)
	_expect(near.z > far.z and near.y > far.y and far.y > sc.horizon, "вид вглубь: ближнее %s, дальнее %s" % [near, far])
	_expect(absf(sc.depth_at(near.y) - 100.0) < 1.0, "вид вглубь: строка %.1f даёт расстояние %.1f" % [near.y, sc.depth_at(near.y)])
	_expect(is_equal_approx(sc.project(0.0, sc.focal).z, 1.0), "вид вглубь: на фокусе масштаб не 1")
	var side := sc.project(60.0, 200.0)
	_expect(side.x > sc.view.x / 2.0, "вид вглубь: правее по миру не правее на экране")


## Встроенный режим (стрим ленты): обе пробы в рамке 480×270, бот идёт сам.
func _check_embedded() -> void:
	for script: GDScript in [ProbeSide, ProbeDepth]:
		var holder := Control.new()
		holder.position = Vector2(1400, 780)
		add_child(holder)
		var d: Demo = script.new()
		d.setup(GameRecord.create(Game.Genre.PLATFORMER, Game.Tech.BIT16, 3, "Стрим"), &"feed")
		d.embed(Vector2(480, 270))
		holder.add_child(d)
		d.start()
		await get_tree().create_timer(0.6).timeout
		_expect(d.bit16 != null and d.bit16.size.x <= 480.5 and d.bit16.size.y <= 270.5, "встроенный экран 16/32 не в рамке")
		var moved := float(d.get("hero_x")) > 90.0 if script == ProbeSide else float(d.get("dist")) > 60.0
		_expect(moved, "встроенный бот стоит")
		holder.queue_free()


# --- Пробные демки -----------------------------------------------------------------------------

func _launch() -> void:
	record = GameRecord.create(Game.Genre.PLATFORMER, Game.Tech.BIT16, Debug.demo_seed, "Проба 16/32",
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
	demo = ProbeDepth.new() if _probe == "depth" else ProbeSide.new()
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
	_expect(reached, "WIN: бот не дошёл до конца пробы %s" % _probe)
	_expect(record.has_bug(&"pink_placeholders") == _saw_pink, "розовые заглушки %s при баге %s" % [_saw_pink,
			record.has_bug(&"pink_placeholders")])
	_expect((probe.bit16.world.material != null) == record.has_bug(&"alien_palette"), "чужая палитра не на слое мира")
	_expect(int(probe.get("collected")) > 0, "бот не собрал ни одного дублона")
	AutoTest.note("bit16 probe %s: дублонов %d, %.1f с, экран %s, баги %s" % [_probe, int(probe.get("collected")), probe.elapsed,
			probe.bit16.view, record.bug_ids])
	probe.queue_free()
	AutoTest.fulfill("bit16 probe")


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("bit16: " + what)
