class_name CoverEditor
extends Control
## Редактор обложки коробки (`docs/specs/cover.md`): спокойный этап перед выходом игры, без
## таймера и без влияния на продажи. Слева коробка в объёме, справа вкладки со строками.
## Клавиатура: вверх и вниз строка, влево и вправо значение, A применить, R случайная обложка.
## Мышь: стикер и название тянутся по коробке, колесо меняет размер (с Shift поворот), за пустое
## место коробка крутится. Обложка открывается уже собранной случайно, фокус на «Готово»: этап
## пролистывается одной кнопкой. По «Готово» пишет обложку и её картинку в запись.

signal finished

enum Tab { BACK_FILL, TITLE, STICKERS, SHOTS }
enum RowKind { CHOICE, COLOR, TRAY, ACTION }

const TAB_NAMES: Array[String] = ["Фон", "Название", "Стикеры", "Оборот"]
const SIDE_NAMES: Array[String] = ["Лицевая", "Оборот"]
const SECTION := "Обложка"
const BOX_WIDTH := 700.0
const ROW_HEIGHT := 58.0
const ROW_GAP := 8.0
const SWATCH := 26.0
const THUMB := 50.0

var record: GameRecord
var studio := ""
var release := 0
## Имя файла картинки коробки без расширения, в каталоге кадров профиля.
var shot_name := ""
var cover: Dictionary = {}

var tab := Tab.BACK_FILL
var side := CoverData.Side.FRONT
## Выбранный предмет: `CoverFace.NONE`, `CoverFace.TITLE` или номер стикера.
var selected := CoverFace.NONE
var moving := false
var tray_index := 0
## Фокус: 0 вкладки, 1.. строки, после них ряд кнопок; `button` 0 «Случайно», 1 «Готово».
var focus := 0
var button := 1

var card: CardFrame
var box: CoverBox

var _ids := PackedStringArray()
var _arts := PackedStringArray()
var _rng := RandomNumberGenerator.new()
var _tune: CoverTuning
var _rows: Array[Dictionary] = []
var _rows_box: VBoxContainer
var _tab_pills: Array[PanelContainer] = []
var _tab_labels: Array[Label] = []
var _tabs_row: PanelContainer
var _tabs_lift: JellyLift
var _buttons: Array[PanelContainer] = []
var _button_labels: Array[Label] = []
var _button_lifts: Array[JellyLift] = []
var _hint: HintPill
var _box_area: Control
var _drag := 0  # 0 нет, 1 крутим коробку, 2 тянем предмет
var _drag_grab := Vector2.ZERO
var _drag_last := Vector2.ZERO
var _finishing := false
var _row_key := ""


func setup(record_: GameRecord, studio_: String, release_ := 0) -> void:
	record = record_
	studio = studio_
	release = release_
	_tune = CoverData.tuning()
	_ids = CoverStickers.ids_for(record.genre, record.tech)
	_arts = CoverStickers.backgrounds(record.genre, record.tech)
	_rng.seed = hash([record.seed, record.title, "cover editor"])
	cover = record.cover.duplicate(true) if not record.cover.is_empty() else CoverData.default_for(record)
	if shot_name == "":
		shot_name = "cover_%d" % record.seed


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()
	_rebuild_rows()
	focus = _button_focus()
	_refresh()
	Debug.add_action(SECTION, "Случайная обложка", randomize_cover)
	Debug.add_choice(SECTION, "Эффект фона", CoverData.FX_NAMES,
			func() -> String: return CoverData.FX_NAMES[int(CoverData.side(cover, side).get("fx", 0))],
			func(v: String) -> void:
				change(&"fx", CoverData.FX_NAMES.find(v) - int(CoverData.side(cover, side).get("fx", 0)))
				_changed())
	Debug.watch("обложка", func() -> String: return "вкладка %s, сторона %d, выбран %d, стикеров %d" % [
			TAB_NAMES[tab], side, selected, CoverData.stickers(cover).size()])
	card.raise_card()


func _exit_tree() -> void:
	Debug.clear_section(SECTION)


# --- Сборка экрана ------------------------------------------------------------------------------

func _build() -> void:
	var header := HintPill.header(ShellHeader.release(release, "%s · %s" % [tr("Обложка"), record.title])
			if release > 0 else "%s · %s" % [tr("Обложка"), record.title])
	header.position = Vector2(Style.EDGE, Style.HEADER_Y - Style.PILL_HEIGHT / 2.0)
	add_child(header)
	card = CardFrame.new()
	add_child(card)
	var inner := CardFrame.inner_size()
	var content := card.content
	# Коробка на сером поле: на белой карточке светлая обложка потерялась бы.
	_box_area = Panel.new()
	_box_area.add_theme_stylebox_override("panel", Style.flat(Style.SURFACE_2, Style.R_CARD, Color.TRANSPARENT, 0))
	_box_area.position = Vector2.ZERO
	_box_area.size = Vector2(BOX_WIDTH, inner.y)
	content.add_child(_box_area)
	var shadow := Control.new()
	shadow.size = _box_area.size
	shadow.draw.connect(func() -> void:
		shadow.draw_set_transform(Vector2(shadow.size.x / 2.0, shadow.size.y - 70.0), 0.0, Vector2(1.0, 0.16))
		shadow.draw_circle(Vector2.ZERO, 210.0, Color(0, 0, 0, 0.08))
		shadow.draw_circle(Vector2.ZERO, 160.0, Color(0, 0, 0, 0.08)))
	_box_area.add_child(shadow)
	box = CoverBox.new()
	box.setup(record, studio)
	box.cover = cover
	box.size = _box_area.size
	_box_area.add_child(box)

	var right := VBoxContainer.new()
	right.position = Vector2(BOX_WIDTH + Style.GAP_CARDS, 0.0)
	right.size = Vector2(inner.x - BOX_WIDTH - Style.GAP_CARDS, inner.y)
	right.add_theme_constant_override("separation", 12)
	content.add_child(right)
	# Вкладки: одна строка фокуса, влево и вправо переключают.
	_tabs_row = PanelContainer.new()
	_tabs_row.custom_minimum_size = Vector2(0, ROW_HEIGHT + 8.0)
	var tabs_sb := Style.flat(Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 0)
	tabs_sb.set_content_margin_all(6)
	_tabs_row.add_theme_stylebox_override("panel", tabs_sb)
	right.add_child(_tabs_row)
	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 6)
	_tabs_row.add_child(tabs)
	for i in TAB_NAMES.size():
		var pill := PanelContainer.new()
		pill.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var l := _label(TAB_NAMES[i], Style.FONT_BODY, Style.INK)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		pill.add_child(l)
		tabs.add_child(pill)
		_tab_pills.append(pill)
		_tab_labels.append(l)
	_tabs_lift = Jelly.button(_tabs_row)
	_rows_box = VBoxContainer.new()
	_rows_box.add_theme_constant_override("separation", int(ROW_GAP))
	_rows_box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.add_child(_rows_box)
	var buttons := HBoxContainer.new()
	buttons.add_theme_constant_override("separation", Style.GAP_CARDS)
	right.add_child(buttons)
	for text: String in ["Случайно", "Готово"]:
		var b := PanelContainer.new()
		b.custom_minimum_size = Vector2(0, Style.BUTTON_HEIGHT)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var l := _label(text, Style.FONT_H2, Style.INK)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		b.add_child(l)
		buttons.add_child(b)
		_buttons.append(b)
		_button_labels.append(l)
		_button_lifts.append(Jelly.button(b))
	_hint = HintPill.make("")
	add_child(HintPill.bottom_bar(_hint, Style.HINTS_BOTTOM))
	MouseUi.pass_through(self)


func _label(text: String, font_size: int, ink: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", ink)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


# --- Строки вкладки -----------------------------------------------------------------------------

func _row_ids() -> Array[StringName]:
	var out: Array[StringName] = []
	match tab:
		Tab.BACK_FILL:
			out = [&"side", &"fx"]
			if int(CoverData.side(cover, side).get("fx", 0)) == CoverData.FX_ART:
				out.append(&"art")
			out.append_array([&"color", &"color2", &"case"])
		Tab.TITLE:
			out = [&"font", &"tcolor", &"tstyle", &"tsize", &"trot", &"tmove"]
		Tab.STICKERS:
			out = [&"side", &"tray"]
			if selected >= 0:
				out.append_array([&"which", &"ssize", &"srot", &"sstyle", &"smove", &"sdel"])
		Tab.SHOTS:
			for i in CoverData.SHOT_SLOTS:
				out.append(StringName("shot%d" % i))
	return out


func _row_title(id: StringName) -> String:
	match id:
		&"side": return "Сторона"
		&"fx": return "Эффект"
		&"art": return "Картинка"
		&"color": return "Цвет фона"
		&"color2": return "Второй цвет"
		&"case": return "Цвет коробки"
		&"font": return "Шрифт"
		&"tcolor": return "Цвет"
		&"tstyle", &"sstyle": return "Стиль"
		&"tsize", &"ssize": return "Размер"
		&"trot", &"srot": return "Поворот"
		&"tmove", &"smove": return "Положение"
		&"tray": return "Новый стикер"
		&"which": return "Стикер"
		&"sdel": return "Убрать стикер"
		&"shot0": return "Кадр 1"
		&"shot1": return "Кадр 2"
	return String(id)


func _row_kind(id: StringName) -> RowKind:
	match id:
		&"color", &"color2", &"case", &"tcolor":
			return RowKind.COLOR
		&"tray":
			return RowKind.TRAY
		&"tmove", &"smove", &"sdel":
			return RowKind.ACTION
	return RowKind.CHOICE


func _rebuild_rows() -> void:
	var ids := _row_ids()
	var key := "%d:%s" % [tab, ids]
	if key != _row_key:
		_row_key = key
		for child in _rows_box.get_children():
			_rows_box.remove_child(child)
			child.queue_free()
		_rows.clear()
		for id in ids:
			_rows.append(_make_row(id))
		MouseUi.pass_through(_rows_box)
	focus = clampi(focus, 0, _button_focus())
	_refresh()


func _make_row(id: StringName) -> Dictionary:
	var kind := _row_kind(id)
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(0, ROW_HEIGHT if kind != RowKind.TRAY else ROW_HEIGHT + 14.0)
	var sb := Style.flat(Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 0)
	sb.content_margin_left = 22
	sb.content_margin_right = 18
	panel.add_theme_stylebox_override("panel", sb)
	_rows_box.add_child(panel)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 12)
	panel.add_child(h)
	var name := _label(_row_title(id), Style.FONT_BODY, Style.INK_2 if kind != RowKind.ACTION else Style.INK)
	name.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(name)
	var row := {"id": id, "kind": kind, "panel": panel, "name": name, "lift": Jelly.button(panel)}
	match kind:
		RowKind.CHOICE:
			var value := _label("", Style.FONT_BODY, Style.INK)
			value.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
			value.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			value.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			value.custom_minimum_size = Vector2(330, 0)
			h.add_child(value)
			row["value"] = value
		RowKind.COLOR:
			var strip := HBoxContainer.new()
			strip.add_theme_constant_override("separation", 5)
			strip.alignment = BoxContainer.ALIGNMENT_END
			h.add_child(strip)
			var swatches: Array[Panel] = []
			for c in CoverData.palette():
				var s := Panel.new()
				s.custom_minimum_size = Vector2(SWATCH, SWATCH)
				s.size_flags_vertical = Control.SIZE_SHRINK_CENTER
				strip.add_child(s)
				swatches.append(s)
			row["swatches"] = swatches
		RowKind.TRAY:
			var strip := HBoxContainer.new()
			strip.add_theme_constant_override("separation", 6)
			strip.alignment = BoxContainer.ALIGNMENT_END
			h.add_child(strip)
			var thumbs: Array[Panel] = []
			for id_ in _ids:
				var cell := Panel.new()
				cell.custom_minimum_size = Vector2(THUMB, THUMB)
				cell.size_flags_vertical = Control.SIZE_SHRINK_CENTER
				strip.add_child(cell)
				var view := CoverFace.StickerView.new()
				view.setup(record, {"id": id_, "style": 0}, Vector2.ONE)
				view.place(Vector2(THUMB, THUMB) / 2.0, THUMB - 12.0)
				cell.add_child(view)
				thumbs.append(cell)
			row["thumbs"] = thumbs
	return row


func _button_focus() -> int:
	return _rows.size() + 1


func _focused_row() -> Dictionary:
	return _rows[focus - 1] if focus >= 1 and focus <= _rows.size() else {}


func _refresh() -> void:
	for i in _tab_pills.size():
		var on := i == tab
		_tab_pills[i].add_theme_stylebox_override("panel", Style.flat(Style.INK if on else Color.TRANSPARENT, Style.R_CTL - 4, Color.TRANSPARENT, 0))
		_tab_labels[i].add_theme_color_override("font_color", Style.SURFACE_SOLID if on else Style.INK_2)
	_tabs_lift.focused = focus == 0
	for i in _rows.size():
		var row := _rows[i]
		var on := focus == i + 1
		(row["lift"] as JellyLift).focused = on
		var id: StringName = row["id"]
		match row["kind"]:
			RowKind.CHOICE:
				(row["value"] as Label).text = "‹   %s   ›" % _value_text(id)
			RowKind.COLOR:
				var current := CoverData.palette_index(_color_of(id))
				var swatches: Array[Panel] = row["swatches"]
				var colors := CoverData.palette()
				for k in swatches.size():
					var picked := k == current
					var d := SWATCH + (10.0 if picked else 0.0)
					swatches[k].custom_minimum_size = Vector2(d, d)
					var sb := Style.flat(colors[k], Style.R_PILL, Color.TRANSPARENT, 0)
					sb.set_border_width_all(4 if picked else 1)
					sb.border_color = Style.INK if picked else Color(Style.INK, 0.12)
					swatches[k].add_theme_stylebox_override("panel", sb)
			RowKind.TRAY:
				var thumbs: Array[Panel] = row["thumbs"]
				for k in thumbs.size():
					var picked := k == tray_index
					var sb := Style.flat(Style.SURFACE_SOLID, 12, Color.TRANSPARENT, 0)
					sb.set_border_width_all(4 if picked else 0)
					sb.border_color = Style.INK
					thumbs[k].add_theme_stylebox_override("panel", sb)
				(row["name"] as Label).text = tr("Новый стикер") if _stickers_left() > 0 else tr("Стикеров максимум")
			RowKind.ACTION:
				var active := moving and (id == &"tmove" or id == &"smove")
				(row["name"] as Label).text = tr("Двигать стрелками") if active else tr(_row_title(id))
	for i in _buttons.size():
		var on := focus == _button_focus() and button == i
		_buttons[i].add_theme_stylebox_override("panel", Style.flat(Style.INK if on else Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 0))
		_button_labels[i].add_theme_color_override("font_color", Style.SURFACE_SOLID if on else Style.INK)
		_button_lifts[i].focused = on
	if moving:
		_hint.label().text = tr("← → ↑ ↓ двигать · %s готово") % GameInput.key(GameInput.A)
	else:
		_hint.label().text = tr("↑ ↓ строка · ← → изменить · %s применить · R случайно") % GameInput.key(GameInput.A)
	if box != null:
		for s in 2:
			var f := box.face(s)
			if f != null:
				f.select(selected if s == side else CoverFace.NONE)


func _value_text(id: StringName) -> String:
	var t := CoverData.title(cover)
	var s := _sticker()
	match id:
		&"side":
			return tr(SIDE_NAMES[side])
		&"fx":
			return tr(CoverData.FX_NAMES[int(CoverData.side(cover, side).get("fx", 0))])
		&"art":
			return "%d / %d" % [maxi(_arts.find(String(CoverData.side(cover, side).get("art", ""))), 0) + 1, _arts.size()]
		&"font":
			return tr(CoverData.FONT_NAMES[posmod(int(t.get("font", 0)), CoverData.FONT_NAMES.size())])
		&"tstyle":
			return tr(CoverData.STYLE_NAMES[posmod(int(t.get("style", 0)), CoverData.STYLE_NAMES.size())])
		&"tsize":
			return "%d %%" % roundi(float(t.get("size", 1.0)) * 100.0)
		&"trot":
			return "%s°" % String.num(float(t.get("rot", 0.0)), 1)
		&"which":
			var mine := _side_stickers()
			return "%d / %d" % [mine.find(selected) + 1, mine.size()]
		&"ssize":
			return "%d %%" % roundi(float(s.get("size", 1.0)) * 100.0)
		&"srot":
			return "%s°" % String.num(float(s.get("rot", 0.0)), 1)
		&"sstyle":
			return tr(CoverData.STYLE_NAMES[posmod(int(s.get("style", 0)), CoverData.STYLE_NAMES.size())])
	if String(id).begins_with("shot"):
		var slot := int(String(id).trim_prefix("shot"))
		var at := record.shots.find(String(CoverData.shots(cover)[slot]))
		return tr("Нет кадров") if record.shots.is_empty() else "%d / %d" % [maxi(at, 0) + 1, record.shots.size()]
	return ""


func _color_of(id: StringName) -> Color:
	match id:
		&"color":
			return CoverData.color(CoverData.side(cover, side), "color")
		&"color2":
			return CoverData.color(CoverData.side(cover, side), "color2")
		&"case":
			return CoverData.color(cover, "case")
	return CoverData.color(CoverData.title(cover), "color")


func _set_color(id: StringName, index: int) -> void:
	var colors := CoverData.palette()
	var value := CoverData.hex(colors[posmod(index, colors.size())])
	match id:
		&"color":
			CoverData.side(cover, side)["color"] = value
		&"color2":
			CoverData.side(cover, side)["color2"] = value
		&"case":
			cover["case"] = value
		_:
			CoverData.title(cover)["color"] = value
	_changed()


# --- Состояние ---------------------------------------------------------------------------------

func _sticker() -> Dictionary:
	var list := CoverData.stickers(cover)
	return list[selected] if selected >= 0 and selected < list.size() else {}


## Номера стикеров текущей стороны.
func _side_stickers() -> Array[int]:
	var out: Array[int] = []
	var list := CoverData.stickers(cover)
	for i in list.size():
		if int((list[i] as Dictionary).get("side", 0)) == side:
			out.append(i)
	return out


func _stickers_left() -> int:
	return _tune.max_stickers - CoverData.stickers(cover).size()


## Обложка изменилась: перерисовать коробку и строки.
func _changed() -> void:
	if box != null:
		box.set_cover(cover)
	_rebuild_rows()


func set_tab(t: int) -> void:
	t = posmod(t, TAB_NAMES.size())
	if t == tab:
		return
	tab = t as Tab
	moving = false
	match tab:
		Tab.TITLE:
			set_side(CoverData.Side.FRONT)
			selected = CoverFace.TITLE
		Tab.SHOTS:
			set_side(CoverData.Side.BACK)
			selected = CoverFace.NONE
		Tab.STICKERS:
			var mine := _side_stickers()
			selected = mine[-1] if not mine.is_empty() else CoverFace.NONE
		_:
			selected = CoverFace.NONE
	ShellSounds.play(&"tick")
	_rebuild_rows()


func set_side(s: int) -> void:
	if s == side:
		return
	side = s as CoverData.Side
	moving = false
	if box != null:
		box.turn_to(side)
	if tab == Tab.STICKERS:
		var mine := _side_stickers()
		selected = mine[-1] if not mine.is_empty() else CoverFace.NONE
	elif tab == Tab.TITLE and side == CoverData.Side.BACK:
		selected = CoverFace.NONE
	_rebuild_rows()


## Выбрать предмет на стороне `side_` (клик по коробке): вкладка переключается под него.
func select_object(index: int, side_: int) -> void:
	side = side_ as CoverData.Side
	selected = index
	moving = false
	tab = Tab.TITLE if index == CoverFace.TITLE else Tab.STICKERS
	_rebuild_rows()


## Значение строки `id` на шаг `dir` (−1 или 1).
func change(id: StringName, dir: int) -> void:
	var t := CoverData.title(cover)
	var s := _sticker()
	match id:
		&"side":
			set_side(1 - side)
			return
		&"fx":
			var d := CoverData.side(cover, side)
			# «Из игры» есть только там, где у технологии есть фоновые картинки.
			d["fx"] = posmod(int(d.get("fx", 0)) + dir, CoverData.FX_NAMES.size() if not _arts.is_empty() else CoverData.FX_ART)
			if int(d["fx"]) == CoverData.FX_ART and not _arts.has(String(d.get("art", ""))):
				d["art"] = _arts[0]
		&"art":
			if _arts.is_empty():
				return
			var d := CoverData.side(cover, side)
			d["art"] = _arts[posmod(_arts.find(String(d.get("art", ""))) + dir, _arts.size())]
		&"color", &"color2", &"case", &"tcolor":
			_set_color(id, CoverData.palette_index(_color_of(id)) + dir)
			return
		&"font":
			t["font"] = posmod(int(t.get("font", 0)) + dir, CoverData.FONT_NAMES.size())
		&"tstyle":
			t["style"] = posmod(int(t.get("style", 0)) + dir, CoverData.STYLE_NAMES.size())
		&"tsize":
			t["size"] = clampf(snappedf(float(t.get("size", 1.0)) + dir * _tune.size_step, 0.01), _tune.title_size_min, _tune.title_size_max)
		&"trot":
			t["rot"] = _step_rot(float(t.get("rot", 0.0)), dir)
		&"tray":
			if _ids.is_empty():
				return
			tray_index = posmod(tray_index + dir, _ids.size())
			_refresh()
			return
		&"which":
			var mine := _side_stickers()
			if mine.is_empty():
				return
			selected = mine[posmod(mine.find(selected) + dir, mine.size())]
			_refresh()
			return
		&"ssize":
			if s.is_empty():
				return
			s["size"] = clampf(snappedf(float(s.get("size", 1.0)) + dir * _tune.size_step, 0.01), _tune.size_min, _tune.size_max)
		&"srot":
			if s.is_empty():
				return
			s["rot"] = _step_rot(float(s.get("rot", 0.0)), dir)
		&"sstyle":
			if s.is_empty():
				return
			s["style"] = posmod(int(s.get("style", 0)) + dir, CoverData.STYLE_NAMES.size())
		_:
			if String(id).begins_with("shot"):
				if record.shots.is_empty():
					return
				var slot := int(String(id).trim_prefix("shot"))
				var list := CoverData.shots(cover)
				list[slot] = record.shots[posmod(record.shots.find(String(list[slot])) + dir, record.shots.size())]
			else:
				return
	_changed()


## Поворот на шаг по сетке шага: из любого начального угла (у случайной обложки он дробный)
## строка проходит через ровные значения, в том числе 0.
func _step_rot(deg: float, dir: int) -> float:
	var step := _tune.rot_step
	var cell := deg / step
	var next := (floorf(cell + 0.001) + 1.0 if dir > 0 else ceilf(cell - 0.001) - 1.0) * step
	return wrapf(next, -180.0, 180.0)


## A на строке: действие строки, у строк выбора следующий вариант.
func activate(id: StringName) -> void:
	match id:
		&"tmove", &"smove":
			moving = not moving
			ShellSounds.play(&"tick")
			_refresh()
		&"tray":
			add_sticker(tray_index)
		&"sdel":
			remove_sticker()
		_:
			change(id, 1)
			ShellSounds.play(&"tick")


## Новый стикер `index` из лотка в середину текущей стороны; `false`, если места нет.
func add_sticker(index: int) -> bool:
	if _ids.is_empty() or _stickers_left() <= 0:
		ShellSounds.play(&"miss")
		return false
	tray_index = posmod(index, _ids.size())
	var list := CoverData.stickers(cover)
	# Чуть в сторону от прошлого, чтобы новые не ложились стопкой.
	var n := _side_stickers().size()
	list.append({"id": _ids[tray_index], "side": side,
			"x": 0.5 + 0.08 * ((n % 3) - 1), "y": 0.55 + 0.06 * ((n % 4) - 1.5),
			"size": 1.0, "rot": 0.0, "style": 1})
	selected = list.size() - 1
	tab = Tab.STICKERS
	ShellSounds.play(&"done")
	_changed()
	return true


func remove_sticker() -> void:
	var list := CoverData.stickers(cover)
	if selected < 0 or selected >= list.size():
		return
	list.remove_at(selected)
	var mine := _side_stickers()
	selected = mine[-1] if not mine.is_empty() else CoverFace.NONE
	moving = false
	ShellSounds.play(&"tick")
	focus = mini(focus, 2)
	_changed()


## Сдвинуть выбранный предмет на `step` долей лица.
func move_selected(step: Vector2) -> void:
	var d := CoverData.title(cover) if selected == CoverFace.TITLE else _sticker()
	if d.is_empty():
		return
	d["x"] = clampf(float(d.get("x", 0.5)) + step.x, 0.0, 1.0)
	d["y"] = clampf(float(d.get("y", 0.5)) + step.y, 0.0, 1.0)
	if box != null:
		box.set_cover(cover)
		_refresh()


## R: новая случайная обложка, кадры и вкладка остаются.
func randomize_cover() -> void:
	cover = CoverData.random(_rng, _ids, record.shots, _arts)
	moving = false
	if tab == Tab.TITLE:
		selected = CoverFace.TITLE
	elif tab == Tab.STICKERS:
		var mine := _side_stickers()
		selected = mine[-1] if not mine.is_empty() else CoverFace.NONE
	else:
		selected = CoverFace.NONE
	ShellSounds.play(&"done")
	if box != null:
		box.spin()
	_changed()


## «Готово»: обложка и картинка коробки в запись.
func finish() -> void:
	if _finishing:
		return
	_finishing = true
	selected = CoverFace.NONE
	moving = false
	_refresh()
	ShellSounds.play(&"done")
	record.cover = cover.duplicate(true)
	if box != null:
		var img: Image = await box.snapshot(_tune.snapshot_px)
		if img != null:
			DirAccess.make_dir_recursive_absolute(Profile.shots_dir())
			var path := Profile.shots_dir() + shot_name + ".png"
			if img.save_png(path) == OK:
				record.cover_shot = path
				AutoTest.note("cover: %s" % path)
	finished.emit()


# --- Ввод ---------------------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if _finishing:
		return
	if MouseUi.is_motion(event) or MouseUi.is_mouse(event):
		_mouse(event)
		return
	var key := event as InputEventKey
	if key != null and key.pressed and not key.echo and key.keycode == KEY_R:
		randomize_cover()
		get_viewport().set_input_as_handled()
		return
	var dir := Vector2.ZERO
	if event.is_action_pressed(GameInput.LEFT, true):
		dir = Vector2.LEFT
	elif event.is_action_pressed(GameInput.RIGHT, true):
		dir = Vector2.RIGHT
	elif event.is_action_pressed(GameInput.UP, true):
		dir = Vector2.UP
	elif event.is_action_pressed(GameInput.DOWN, true):
		dir = Vector2.DOWN
	if moving:
		if dir != Vector2.ZERO:
			move_selected(dir * _tune.move_step)
		elif not event.is_echo() and (GameInput.is_a(event) or GameInput.is_b(event)):
			moving = false
			ShellSounds.play(&"tick")
			_refresh()
		else:
			return
		get_viewport().set_input_as_handled()
		return
	if dir.y != 0.0:
		if event.is_echo():
			return
		set_focus(focus + int(dir.y))
	elif dir.x != 0.0:
		step_focused(int(dir.x), event.is_echo())
	elif not event.is_echo() and GameInput.is_a(event):
		press_focused()
	else:
		return
	get_viewport().set_input_as_handled()


func set_focus(f: int) -> void:
	f = clampi(f, 0, _button_focus())
	if f == focus:
		return
	focus = f
	ShellSounds.play(&"tick")
	_refresh()


## Влево или вправо на строке в фокусе.
func step_focused(dir: int, echo := false) -> void:
	if focus == 0:
		if not echo:
			set_tab(tab + dir)
	elif focus == _button_focus():
		if not echo and button != clampi(button + dir, 0, 1):
			button = clampi(button + dir, 0, 1)
			ShellSounds.play(&"tick")
			_refresh()
	else:
		var row := _focused_row()
		if row["kind"] == RowKind.ACTION:
			return
		change(row["id"], dir)
		if not echo:
			ShellSounds.play(&"tick")


func press_focused() -> void:
	if focus == 0:
		set_tab(tab + 1)
	elif focus == _button_focus():
		_button_lifts[button].press()
		if button == 0:
			randomize_cover()
		else:
			finish()
	else:
		var row := _focused_row()
		(row["lift"] as JellyLift).press()
		activate(row["id"])


func _mouse(event: InputEvent) -> void:
	var viewport := get_viewport()
	var button_event := event as InputEventMouseButton
	var motion := event as InputEventMouseMotion
	if button_event != null and button_event.button_index == MOUSE_BUTTON_LEFT and not button_event.pressed:
		if _drag == 1 and box.facing() != side:
			# Коробку докрутили до другой стороны: дальше правим её.
			side = box.facing() as CoverData.Side
			if tab == Tab.STICKERS:
				var mine := _side_stickers()
				selected = mine[-1] if not mine.is_empty() else CoverFace.NONE
			elif tab == Tab.TITLE:
				selected = CoverFace.TITLE if side == CoverData.Side.FRONT else CoverFace.NONE
			_rebuild_rows()
		_drag = 0
		return
	if motion != null:
		if _drag == 1:
			# По разнице положений, а не `relative`: у подставленного ввода автотеста его нет.
			box.drag(motion.position - _drag_last)
			_drag_last = motion.position
		elif _drag == 2:
			var hit := box.pick(motion.position)
			if not hit.is_empty() and int(hit["side"]) == side:
				var d := CoverData.title(cover) if selected == CoverFace.TITLE else _sticker()
				if not d.is_empty():
					var uv: Vector2 = hit["uv"]
					d["x"] = clampf(uv.x - _drag_grab.x, 0.0, 1.0)
					d["y"] = clampf(uv.y - _drag_grab.y, 0.0, 1.0)
					box.set_cover(cover)
					_refresh()
		else:
			_hover(event)
		return
	if MouseUi.hit(_box_area, event):
		var step := MouseUi.wheel(event)
		if step != 0:
			if selected != CoverFace.NONE:
				var rotate := button_event != null and button_event.shift_pressed
				var title := selected == CoverFace.TITLE
				change((&"trot" if title else &"srot") if rotate else (&"tsize" if title else &"ssize"), -step)
			MouseUi.consume(viewport)
			return
		if MouseUi.is_click(event):
			var hit := box.pick(button_event.position)
			_drag = 1
			_drag_last = button_event.position
			if not hit.is_empty():
				var uv: Vector2 = hit["uv"]
				var index := box.face(int(hit["side"])).object_at(uv)
				if index != CoverFace.NONE:
					select_object(index, int(hit["side"]))
					var d := CoverData.title(cover) if index == CoverFace.TITLE else _sticker()
					_drag_grab = uv - Vector2(float(d.get("x", 0.5)), float(d.get("y", 0.5)))
					_drag = 2
					ShellSounds.play(&"tick")
			MouseUi.consume(viewport)
		return
	if not MouseUi.is_click(event):
		return
	for i in _tab_pills.size():
		if MouseUi.hit(_tab_pills[i], event):
			focus = 0
			set_tab(i)
			_refresh()
			MouseUi.consume(viewport)
			return
	for i in _buttons.size():
		if MouseUi.hit(_buttons[i], event):
			focus = _button_focus()
			button = i
			_refresh()
			press_focused()
			MouseUi.consume(viewport)
			return
	for i in _rows.size():
		var row := _rows[i]
		if not MouseUi.hit(row["panel"], event):
			continue
		focus = i + 1
		_click_row(row, event)
		MouseUi.consume(viewport)
		return


func _click_row(row: Dictionary, event: InputEvent) -> void:
	var id: StringName = row["id"]
	match row["kind"]:
		RowKind.CHOICE:
			# Левая половина значения листает назад, правая вперёд.
			var value: Label = row["value"]
			var p: Vector2 = MouseUi.point(event)
			change(id, -1 if p.x < MouseUi.rect_of(value).get_center().x else 1)
			ShellSounds.play(&"tick")
			_refresh()
		RowKind.COLOR:
			var swatches: Array[Panel] = row["swatches"]
			for k in swatches.size():
				if MouseUi.hit(swatches[k], event):
					_set_color(id, k)
					ShellSounds.play(&"tick")
					return
			_refresh()
		RowKind.TRAY:
			var thumbs: Array[Panel] = row["thumbs"]
			for k in thumbs.size():
				if MouseUi.hit(thumbs[k], event):
					add_sticker(k)
					return
			_refresh()
		RowKind.ACTION:
			(row["lift"] as JellyLift).press()
			activate(id)


## Наведение переносит фокус, как стрелки.
func _hover(event: InputEvent) -> void:
	if moving:
		return
	var f := -1
	if MouseUi.hit(_tabs_row, event):
		f = 0
	for i in _rows.size():
		if MouseUi.hit(_rows[i]["panel"], event):
			f = i + 1
	var b := button
	for i in _buttons.size():
		if MouseUi.hit(_buttons[i], event):
			f = _button_focus()
			b = i
	if f >= 0 and (f != focus or b != button):
		focus = f
		button = b
		_refresh()
