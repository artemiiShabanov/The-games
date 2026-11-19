extends Control
## Тестовая сцена обложки коробки (`docs/specs/cover.md`): редактор на фоне. Под ботом: обложка
## по умолчанию от сида одна и та же, вкладки и строки меняют словарь, стикеры добавляются до
## предела и убираются, предмет двигается, «Случайно» даёт другую, «Готово» пишет в запись.
## Кадр: `--no-checks [--genre=racing] [--tech=vector|bit8|bit16|lowpoly|threed] [--setting=N]
## [--seed=N] [--tab=0..3] [--side=back] [--fx=0..8] [--art=N] [--random=N] [--focus=N]`.

const GENRES := {"platformer": Game.Genre.PLATFORMER, "racing": Game.Genre.RACING, "shooter": Game.Genre.SHOOTER,
		"sport": Game.Genre.SPORT, "fighting": Game.Genre.FIGHTING}
const TECHS := {"vector": Game.Tech.VECTOR, "bit8": Game.Tech.BIT8, "bit16": Game.Tech.BIT16,
		"lowpoly": Game.Tech.LOWPOLY, "threed": Game.Tech.THREED}

var editor: CoverEditor
var record: GameRecord
var _done := false


func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var args := AutoTest.parse_args(OS.get_cmdline_user_args())
	Debug.skip_cards = true
	Profile.use_test_file()
	var genre: Game.Genre = GENRES.get(str(args.get("genre", "platformer")), Game.Genre.PLATFORMER)
	var tech: Game.Tech = TECHS.get(str(args.get("tech", "bit8")), Game.Tech.BIT8)
	record = GameRecord.create(genre, tech, int(args.get("seed", 7)), "Сундук мертвеца", int(args.get("setting", 0)) as Game.Setting)
	record.shots = _fake_shots()
	record.shot = record.shots[0]
	editor = CoverEditor.new()
	editor.setup(record, "Тихая гавань", 3)
	editor.finished.connect(func() -> void: _done = true)
	add_child(editor)
	# Без автотеста сцена просто держит редактор: можно собирать обложку руками.
	if args.has("no-checks") or not AutoTest.enabled:
		AutoTest.bot_mode = AutoTest.BotMode.OFF
		for i in int(args.get("random", 0)):
			editor.randomize_cover()
		if args.has("fx"):
			CoverData.side(editor.cover, CoverData.Side.FRONT)["fx"] = int(args["fx"])
			CoverData.side(editor.cover, CoverData.Side.BACK)["fx"] = int(args["fx"])
			var arts := CoverStickers.backgrounds(record.genre, record.tech)
			if not arts.is_empty():
				CoverData.side(editor.cover, CoverData.Side.FRONT)["art"] = arts[int(args.get("art", 0)) % arts.size()]
				CoverData.side(editor.cover, CoverData.Side.BACK)["art"] = arts[(int(args.get("art", 0)) + 1) % arts.size()]
			editor._changed()
		if args.has("tab"):
			editor.set_tab(int(args["tab"]))
		if str(args.get("side", "")) == "back":
			editor.set_side(CoverData.Side.BACK)
			editor.box.turn_to(CoverData.Side.BACK, true)
		if args.has("focus"):
			editor.set_focus(int(args["focus"]))
		return
	AutoTest.require("cover checks")
	_check.call_deferred()


## Кадры плейтеста заглушками: три цветных прямоугольника в каталоге кадров автотеста.
func _fake_shots() -> PackedStringArray:
	var out := PackedStringArray()
	DirAccess.make_dir_recursive_absolute(Profile.shots_dir())
	var tones: Array[Color] = [Color("#2B6CB0"), Color("#C05621"), Color("#2F855A")]
	for i in tones.size():
		var img := Image.create(480, 270, false, Image.FORMAT_RGBA8)
		img.fill(tones[i])
		img.fill_rect(Rect2i(40 + i * 90, 150, 120, 80), tones[i].lightened(0.4))
		img.fill_rect(Rect2i(0, 230, 480, 40), tones[i].darkened(0.4))
		var path := Profile.shots_dir() + "cover_test_%d.png" % i
		img.save_png(path)
		out.append(path)
	return out


func _check() -> void:
	var tune := CoverData.tuning()
	# Обложка по умолчанию от сида: одна и та же, с названием и стикерами игры.
	var a := CoverData.default_for(record)
	var b := CoverData.default_for(record)
	_expect(a == b and not a.is_empty(), "обложка по умолчанию от сида одна")
	_expect(editor.cover == a, "редактор открыт с обложкой по умолчанию")
	var ids := CoverStickers.ids_for(record.genre, record.tech)
	_expect(not ids.is_empty(), "у игры есть стикеры")
	for s: Dictionary in CoverData.stickers(a):
		_expect(ids.has(String(s["id"])), "стикер из ассетов игры: %s" % s["id"])
	_expect(CoverData.shots(a).size() == CoverData.SHOT_SLOTS and String(CoverData.shots(a)[0]) == record.shots[0], "кадры плейтеста в окнах оборота")
	for genre: Game.Genre in Game.Genre.values():
		for tech: Game.Tech in Game.Tech.values():
			_expect(not CoverStickers.ids_for(genre, tech).is_empty(), "стикеры пары %s × %s" % [Game.genre_name(genre), Game.tech_name(tech)])
	_expect(editor.focus == editor._button_focus() and editor.button == 1, "фокус на «Готово»: этап пролистывается одной кнопкой")
	# Фон: эффект, цвета, коробка.
	var front := CoverData.side(editor.cover, CoverData.Side.FRONT)
	var fx := int(front["fx"])
	editor.change(&"fx", 1)
	_expect(int(CoverData.side(editor.cover, CoverData.Side.FRONT)["fx"]) == (fx + 1) % CoverData.FX_NAMES.size(), "эффект фона листается")
	# «Из игры»: у ретро фон плиткой из ассетов игры, у примитива такого эффекта нет.
	CoverData.side(editor.cover, CoverData.Side.FRONT)["fx"] = CoverData.FX_ART - 1
	editor.change(&"fx", 1)
	var arts := CoverStickers.backgrounds(record.genre, record.tech)
	_expect(int(CoverData.side(editor.cover, CoverData.Side.FRONT)["fx"]) == CoverData.FX_ART
			and arts.has(String(CoverData.side(editor.cover, CoverData.Side.FRONT)["art"])), "эффект «Из игры» ставит картинку игры")
	_expect(editor._row_ids().has(&"art"), "строка «Картинка» появляется с эффектом «Из игры»")
	var art_at := arts.find(String(CoverData.side(editor.cover, CoverData.Side.FRONT)["art"]))
	editor.change(&"art", 1)
	_expect(String(CoverData.side(editor.cover, CoverData.Side.FRONT)["art"]) == arts[(art_at + 1) % arts.size()], "картинка листается")
	editor.change(&"fx", 1)
	_expect(int(CoverData.side(editor.cover, CoverData.Side.FRONT)["fx"]) == 0, "эффекты по кругу")
	_expect(CoverStickers.backgrounds(Game.Genre.RACING, Game.Tech.VECTOR).is_empty(), "у примитива фонов из игры нет")
	var case := str(editor.cover["case"])
	editor.change(&"case", 1)
	_expect(str(editor.cover["case"]) != case, "цвет коробки меняется")
	editor.change(&"side", 1)
	_expect(editor.side == CoverData.Side.BACK, "сторона: оборот")
	var back_color := str(CoverData.side(editor.cover, CoverData.Side.BACK)["color"])
	editor.change(&"color", 1)
	_expect(str(CoverData.side(editor.cover, CoverData.Side.BACK)["color"]) != back_color
			and CoverData.side(editor.cover, CoverData.Side.FRONT)["color"] == front["color"], "цвет фона меняется только у своей стороны")
	# Название: вкладка возвращает лицевую и выбирает название.
	editor.set_tab(CoverEditor.Tab.TITLE)
	_expect(editor.side == CoverData.Side.FRONT and editor.selected == CoverFace.TITLE, "вкладка названия: лицевая, название выбрано")
	var font := int(CoverData.title(editor.cover)["font"])
	editor.change(&"font", 1)
	_expect(int(CoverData.title(editor.cover)["font"]) == (font + 1) % CoverData.FONT_NAMES.size(), "шрифт листается")
	for i in 40:
		editor.change(&"tsize", 1)
	_expect(is_equal_approx(float(CoverData.title(editor.cover)["size"]), tune.title_size_max), "размер названия упирается в предел")
	var x := float(CoverData.title(editor.cover)["x"])
	editor.activate(&"tmove")
	_expect(editor.moving, "режим «Положение»")
	editor.move_selected(Vector2(tune.move_step, 0.0))
	_expect(is_equal_approx(float(CoverData.title(editor.cover)["x"]), minf(x + tune.move_step, 1.0)), "название двигается")
	editor.activate(&"tmove")
	# Поворот с дробного угла встаёт на сетку шага и проходит через ноль.
	CoverData.title(editor.cover)["rot"] = 3.0
	editor.change(&"trot", -1)
	_expect(is_zero_approx(float(CoverData.title(editor.cover)["rot"])), "поворот названия встаёт в 0: %s" % CoverData.title(editor.cover)["rot"])
	editor.change(&"trot", -1)
	_expect(is_equal_approx(float(CoverData.title(editor.cover)["rot"]), -tune.rot_step), "дальше шаг от нуля")
	# Стикеры: до предела, потом отказ; убрать.
	editor.set_tab(CoverEditor.Tab.STICKERS)
	var guard := 0
	while editor.add_sticker(guard % ids.size()) and guard < 100:
		guard += 1
	_expect(CoverData.stickers(editor.cover).size() == tune.max_stickers, "стикеров не больше %d: %d" % [tune.max_stickers, CoverData.stickers(editor.cover).size()])
	_expect(editor.selected == tune.max_stickers - 1, "новый стикер выбран")
	editor.change(&"sstyle", 1)
	editor.change(&"srot", 1)
	var last: Dictionary = CoverData.stickers(editor.cover)[-1]
	_expect(int(last["style"]) == 2 and is_equal_approx(float(last["rot"]), tune.rot_step), "стиль и поворот стикера")
	editor.remove_sticker()
	_expect(CoverData.stickers(editor.cover).size() == tune.max_stickers - 1, "стикер убран")
	# Оборот: кадр в окне листается по кадрам плейтеста.
	editor.set_tab(CoverEditor.Tab.SHOTS)
	_expect(editor.side == CoverData.Side.BACK, "вкладка оборота поворачивает коробку")
	editor.change(&"shot0", 1)
	_expect(String(CoverData.shots(editor.cover)[0]) == record.shots[1], "кадр оборота листается")
	# Случайно: другая обложка, кадры остаются из плейтеста.
	var before := editor.cover.duplicate(true)
	editor.randomize_cover()
	_expect(editor.cover != before, "«Случайно» даёт другую обложку")
	_expect(record.shots.has(String(CoverData.shots(editor.cover)[0])), "у случайной обложки кадры плейтеста")
	# Коробка: точка в центре экрана коробки попадает в сторону, которая смотрит на игрока.
	await get_tree().process_frame
	await get_tree().process_frame
	editor.box.turn_to(CoverData.Side.FRONT, true)
	editor.box.sway = false
	editor.box._apply_rotation()
	var hit := editor.box.pick(editor.box.get_global_rect().get_center())
	_expect(not hit.is_empty() and int(hit["side"]) == CoverData.Side.FRONT and (hit["uv"] as Vector2).distance_to(Vector2(0.5, 0.5)) < 0.1,
			"центр коробки это середина лицевой: %s" % hit)
	editor.box.turn_to(CoverData.Side.BACK, true)
	editor.box._apply_rotation()
	hit = editor.box.pick(editor.box.get_global_rect().get_center())
	_expect(not hit.is_empty() and int(hit["side"]) == CoverData.Side.BACK, "после поворота в центре оборот: %s" % hit)
	editor.box.sway = true
	# Готово: обложка в записи, сигнал.
	editor.finish()
	for i in 6:
		await get_tree().process_frame
	_expect(_done and record.cover == editor.cover and not record.cover.is_empty(), "«Готово» пишет обложку в запись")
	if DisplayServer.get_name() != "headless":
		_expect(record.cover_shot != "" and FileAccess.file_exists(record.cover_shot), "картинка коробки сохранена: %s" % record.cover_shot)
	var entry := GalleryEntry.of(record, 1, 3, "Тихая гавань")
	_expect(entry.cover == record.cover and entry.to_record().cover == record.cover, "обложка доходит до галереи и обратно")
	AutoTest.note("cover: по умолчанию, фон, название, стикеры, оборот, случайно, попадание в коробку, готово")
	AutoTest.fulfill("cover checks")


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("cover: " + what)
