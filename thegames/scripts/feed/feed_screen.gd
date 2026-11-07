class_name FeedScreen
extends Control
## Экран ленты отклика, спека `docs/specs/success.md`, концепт `04`: в большой карточке
## `CardFrame` поверх студии колонка 880 по центру: два твита, карточки трёх критиков с
## оценками, клип стримера с кадром бага (кадр пока рисованная заглушка), ещё два твита, три
## карточки цифр и кнопки «В демо» и «Дальше». Элементы появляются по очереди, колонка
## листается вверх-вниз, влево-вправо переводят фокус между кнопками, A подтверждает, B это
## «Дальше». Над карточкой пилюли «Релиз N · Отклик · #Тег» и денег. Лица пока буква в круге.

signal demo_requested
signal finished

const COLUMN_WIDTH := 880
const TWEET_INSET := 40
const ITEM_GAP := 16
const CLIP_HEIGHT := 300
const STAGGER_SECONDS := 0.08
const SCROLL_STEP := 240.0

var content: FeedContent
var release := 1
var cash := 0
var focus_demo := false

var card: CardFrame
var _scroll: ScrollContainer
var _column: VBoxContainer
var _buttons: Array[PanelContainer] = []
var _button_labels: Array[Label] = []
var _items: Array[Control] = []
var _revealed := false


func setup(content_: FeedContent, release_: int, cash_: int) -> void:
	content = content_
	release = release_
	cash = cash_


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()
	await card.raise_card()
	_reveal()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_echo():
		return
	if event.is_action_pressed(GameInput.DOWN):
		_scroll_by(SCROLL_STEP)
	elif event.is_action_pressed(GameInput.UP):
		_scroll_by(-SCROLL_STEP)
	elif event.is_action_pressed(GameInput.LEFT):
		set_focus_demo(true)
	elif event.is_action_pressed(GameInput.RIGHT):
		set_focus_demo(false)
	elif GameInput.is_a(event):
		confirm()
	elif GameInput.is_b(event):
		ShellSounds.play(&"done")
		finished.emit()
	else:
		return
	get_viewport().set_input_as_handled()


func set_focus_demo(v: bool) -> void:
	if focus_demo == v:
		return
	focus_demo = v
	ShellSounds.play(&"tick")
	_refresh_buttons()
	scroll_to_end()


func confirm() -> void:
	ShellSounds.play(&"done")
	if focus_demo:
		demo_requested.emit()
	else:
		finished.emit()


# --- Построение ---------------------------------------------------------------------------------

func _build() -> void:
	var header := HintPill.header("Релиз %d · Отклик · %s" % [release, content.tag])
	header.position = Vector2(Style.EDGE, Style.HEADER_Y - Style.PILL_HEIGHT / 2.0)
	add_child(header)
	var right := HBoxContainer.new()
	right.alignment = BoxContainer.ALIGNMENT_END
	right.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	right.offset_left = Style.EDGE
	right.offset_right = -Style.EDGE
	right.offset_top = Style.HEADER_Y - Style.PILL_HEIGHT / 2.0
	right.offset_bottom = right.offset_top + Style.PILL_HEIGHT
	right.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(right)
	var money := HintPill.header(Style.format_money(cash))
	var money_label := money.get_child(0) as Label
	money_label.add_theme_font_override("font", Style.mono_font())
	money_label.add_theme_color_override("font_color", Style.MONEY)
	right.add_child(money)

	card = CardFrame.new()
	add_child(card)
	var inner := CardFrame.inner_size()
	_scroll = ScrollContainer.new()
	_scroll.position = Vector2((inner.x - COLUMN_WIDTH) / 2.0, 0)
	_scroll.size = Vector2(COLUMN_WIDTH, inner.y)
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	_scroll.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.content.add_child(_scroll)
	_column = VBoxContainer.new()
	_column.custom_minimum_size = Vector2(COLUMN_WIDTH, 0)
	_column.add_theme_constant_override("separation", ITEM_GAP)
	_column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_scroll.add_child(_column)

	for item in content.items:
		var node: Control
		match item.kind:
			FeedContent.Kind.TWEET:
				node = _make_tweet(item)
			FeedContent.Kind.CRITIC:
				node = _make_critic(item)
			FeedContent.Kind.CLIP:
				node = _make_clip(item)
			FeedContent.Kind.NUMBERS:
				node = _make_numbers(item)
		_column.add_child(node)
		_items.append(node)
	var buttons := _make_buttons()
	_column.add_child(buttons)
	_items.append(buttons)
	_column.add_child(_spacer(8))
	for n in _items:
		n.modulate.a = 0.0 if not Debug.skip_cards else 1.0
	_refresh_buttons()

	var hints := HBoxContainer.new()
	hints.alignment = BoxContainer.ALIGNMENT_CENTER
	hints.add_theme_constant_override("separation", 16)
	hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hints.offset_top = -(Style.PILL_HEIGHT + 16)
	hints.offset_bottom = -16
	hints.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hints.add_child(HintPill.make("↑ ↓ листать"))
	hints.add_child(HintPill.make("← → кнопка"))
	hints.add_child(HintPill.make("A выбрать · B дальше"))
	add_child(hints)


## Элементы проявляются по очереди сверху вниз.
func _reveal() -> void:
	if _revealed:
		return
	_revealed = true
	if Debug.skip_cards:
		return
	for i in _items.size():
		var n := _items[i]
		n.position.y += Style.SCREEN_SLIDE_PX
		var tw := create_tween().set_parallel(true).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_property(n, "modulate:a", 1.0, Style.SWITCH_SECONDS).set_delay(i * STAGGER_SECONDS)
		tw.tween_property(n, "position:y", n.position.y - Style.SCREEN_SLIDE_PX, Style.SWITCH_SECONDS).set_delay(i * STAGGER_SECONDS)


func _scroll_by(dy: float) -> void:
	var target := clampf(_scroll.scroll_vertical + dy, 0.0, maxf(_column.size.y - _scroll.size.y, 0.0))
	if Debug.skip_cards:
		_scroll.scroll_vertical = int(target)
		return
	create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC).tween_property(_scroll, "scroll_vertical", int(target), Style.FOCUS_MOVE_SECONDS)


func scroll_to_end() -> void:
	_scroll_by(_column.size.y)


## Твит: ник, текст, хэштег в цвете фокуса; уже карточек критиков на TWEET_INSET с каждой
## стороны.
func _make_tweet(item: FeedContent.Item) -> Control:
	var wrap := MarginContainer.new()
	wrap.add_theme_constant_override("margin_left", TWEET_INSET)
	wrap.add_theme_constant_override("margin_right", TWEET_INSET)
	wrap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.card())
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	wrap.add_child(panel)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 16)
	panel.add_child(row)
	row.add_child(_face(Style.INK_3, "", 48))
	var col := VBoxContainer.new()
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.add_theme_constant_override("separation", 4)
	row.add_child(col)
	col.add_child(_label(item.handle, Style.FONT_CAPTION, Style.INK_3))
	var text := RichTextLabel.new()
	text.bbcode_enabled = true
	text.fit_content = true
	text.scroll_active = false
	text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	text.add_theme_font_size_override("normal_font_size", Style.FONT_BODY)
	text.add_theme_color_override("default_color", Style.INK)
	var t := item.text
	var tag_at := t.find("#")
	if tag_at >= 0:
		var tag_end := t.find(" ", tag_at)
		if tag_end < 0:
			tag_end = t.length()
		t = t.substr(0, tag_at) + "[color=%s]%s[/color]" % [Style.FOCUS.to_html(false), t.substr(tag_at, tag_end - tag_at)] + t.substr(tag_end)
	text.text = t
	col.add_child(text)
	return wrap


func _make_critic(item: FeedContent.Item) -> Control:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.card(true))
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 24)
	panel.add_child(row)
	row.add_child(_face(item.person.accent, item.person.name.substr(0, 1), 96))
	var col := VBoxContainer.new()
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.add_theme_constant_override("separation", 4)
	row.add_child(col)
	col.add_child(_label("Критик · " + item.person.subtitle, Style.FONT_CAPTION, Style.INK_3))
	col.add_child(_label(item.person.name, Style.FONT_H2, Style.INK))
	var quote := _label(item.text, Style.FONT_BODY, Style.INK)
	quote.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	col.add_child(quote)
	var score_box := HBoxContainer.new()
	score_box.alignment = BoxContainer.ALIGNMENT_BEGIN
	score_box.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	score_box.add_theme_constant_override("separation", 2)
	row.add_child(score_box)
	var big := _label(_score_text(item.score), 64, Style.INK)
	big.add_theme_font_override("font", Style.mono_font())
	score_box.add_child(big)
	var denom := _label("/10", Style.FONT_BODY, Style.INK_3)
	denom.size_flags_vertical = Control.SIZE_SHRINK_END
	score_box.add_child(denom)
	return panel


## Клип: шапка стримера, реплика, кадр 16:9 со штампом бага, кнопкой воспроизведения и подписью.
func _make_clip(item: FeedContent.Item) -> Control:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.card(true))
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 16)
	panel.add_child(col)
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 24)
	col.add_child(head)
	head.add_child(_face(item.person.accent, item.person.name.substr(0, 1), 96))
	var info := VBoxContainer.new()
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	info.add_theme_constant_override("separation", 4)
	head.add_child(info)
	info.add_child(_label("Стример · " + item.person.subtitle, Style.FONT_CAPTION, Style.INK_3))
	info.add_child(_label(item.person.name, Style.FONT_H2, Style.INK))
	var quote := _label(item.text, Style.FONT_BODY, Style.INK)
	quote.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.add_child(quote)
	var frame := Control.new()
	frame.custom_minimum_size = Vector2(0, CLIP_HEIGHT)
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.draw.connect(_draw_clip_frame.bind(frame, item))
	col.add_child(frame)
	return panel


## Кадр клипа: заглушка в духе 8-bit (небо, земля), кнопка воспроизведения, штамп бага,
## подпись просмотров. Настоящий кадр демки приходит с галереей.
func _draw_clip_frame(frame: Control, item: FeedContent.Item) -> void:
	var r := Rect2(Vector2.ZERO, frame.size)
	Style.flat(Color("#2F6FB5"), Style.R_CTL, Color.TRANSPARENT, 0).draw(frame.get_canvas_item(), r)
	frame.draw_rect(Rect2(0, r.size.y - 36, r.size.x, 36), Color("#A85A2A"))
	frame.draw_rect(Rect2(0, r.size.y - 40, r.size.x, 4), Color("#2BB37A"))
	var c := r.size / 2.0
	frame.draw_circle(c, 36, Color(1, 1, 1, 0.9))
	frame.draw_colored_polygon(PackedVector2Array([c + Vector2(-10, -16), c + Vector2(18, 0), c + Vector2(-10, 16)]), Style.INK)
	var font := ThemeDB.fallback_font
	frame.draw_string(font, Vector2(20, r.size.y - 12), item.caption, HORIZONTAL_ALIGNMENT_LEFT, -1, Style.FONT_CAPTION, Color(1, 1, 1, 0.85))
	if item.stamp != "":
		var w := font.get_string_size(item.stamp, HORIZONTAL_ALIGNMENT_LEFT, -1, Style.FONT_H2).x + 48
		var pos := Vector2(r.size.x - w - 28, 28)
		frame.draw_set_transform(pos + Vector2(w / 2.0, 24), deg_to_rad(-6.0))
		Style.flat(Style.BUG, Style.R_PILL, Color.TRANSPARENT, 0).draw(frame.get_canvas_item(), Rect2(-w / 2.0, -24, w, 48))
		frame.draw_string(font, Vector2(-w / 2.0 + 24, 11), item.stamp, HORIZONTAL_ALIGNMENT_LEFT, -1, Style.FONT_H2, Style.SURFACE_SOLID)
		frame.draw_set_transform(Vector2.ZERO)


func _make_numbers(item: FeedContent.Item) -> Control:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", Style.GAP_CARDS)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(_number_card("Критики", _score_text(item.score), Style.INK))
	row.add_child(_number_card("Продажи, первый тик", Style.format_money(item.reach), Style.MONEY))
	row.add_child(_number_card("Стримеры", item.text, Style.INK))
	return row


func _number_card(caption: String, value: String, color: Color) -> Control:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.card(true))
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 8)
	panel.add_child(col)
	col.add_child(_label(caption, Style.FONT_CAPTION, Style.INK_2))
	var v := _label(value, 44, color)
	v.add_theme_font_override("font", Style.mono_font())
	col.add_child(v)
	return panel


func _make_buttons() -> Control:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", Style.GAP_CARDS)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for text in ["В демо", "Дальше"]:
		var b := PanelContainer.new()
		b.custom_minimum_size = Vector2(240, Style.BUTTON_HEIGHT)
		b.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var l := _label(text, Style.FONT_H2, Style.INK)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		b.add_child(l)
		row.add_child(b)
		_buttons.append(b)
		_button_labels.append(l)
	return row


## Кнопка в фокусе тёмная, вторая `surface-2` с чернилами (как в конструкторе).
func _refresh_buttons() -> void:
	for i in _buttons.size():
		var on := (i == 0) == focus_demo
		_buttons[i].add_theme_stylebox_override("panel", Style.flat(Style.INK if on else Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 0))
		_button_labels[i].add_theme_color_override("font_color", Style.SURFACE_SOLID if on else Style.INK)


func _score_text(v: float) -> String:
	return "%d" % int(v) if is_equal_approx(v, roundf(v)) else "%.1f" % v


## Лицо-заглушка: круг цвета акцента с буквой.
func _face(color: Color, letter: String, size_px: int) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(size_px, size_px)
	c.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.draw.connect(_draw_face.bind(c, color, letter, size_px))
	return c


func _draw_face(c: Control, color: Color, letter: String, size_px: int) -> void:
	c.draw_circle(Vector2(size_px / 2.0, size_px / 2.0), size_px / 2.0, color)
	if letter != "":
		var font := ThemeDB.fallback_font
		var fs := int(size_px * 0.5)
		var w := font.get_string_size(letter, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		c.draw_string(font, Vector2(size_px / 2.0 - w / 2.0, size_px / 2.0 + fs * 0.36), letter, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Style.SURFACE_SOLID)


func _label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _spacer(h: int) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(0, h)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c
