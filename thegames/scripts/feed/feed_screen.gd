class_name FeedScreen
extends Control
## Экран ленты отклика, спека `docs/specs/success.md`, концепт `04`, плейтест 2026-11-07: в
## большой карточке `CardFrame` поверх студии колонка 880 по центру, карточки одного размера:
## твиты, карточки критиков с цветной полосой акцента и оценкой справа, стрим как живая запись
## геймплея (встроенная демка с багами записи, бот играет, без звука) с пиксельным лицом
## стримера и онлайном; порядок перемешан, в конце две карточки цифр (критики, просмотры) и
## кнопки «В демо» и «Дальше». Вверх и вниз листают по карточке с центрированием, A до низа
## листает вниз, внизу ставит фокус на «Дальше» и подтверждает, влево-вправо меняют кнопку, B
## это «Дальше». Продажи на этом экране не показываются: они приходят в фазе студии.
## Архив (#78, `setup_archive`): та же лента прошлого релиза панелью на левой половине экрана
## поверх главного экрана забега, выезжает слева; без шапки и подсказок, кнопки «Играть демку»
## и «Закрыть», Esc тоже закрывает.

signal demo_requested
signal finished

const COLUMN_WIDTH := 880
## Запас по бокам колонки, чтобы тени карточек не резались.
const SHADOW_PAD := 32
const ITEM_GAP := 32
const STREAM_HEIGHT := 408
const ACCENT_BAR := 6
const STAGGER_SECONDS := 0.08

var content: FeedContent
var record: GameRecord
var release := 1
var cash := 0
## Индекс карточки по центру; последняя это ряд кнопок.
var index := 0
var focus_demo := false

var card: CardFrame
var _scroll: ScrollContainer
var _column: VBoxContainer
var _buttons: Array[PanelContainer] = []
var _button_labels: Array[Label] = []
var _button_lifts: Array[JellyLift] = []
var _items: Array[Control] = []
var _item_lifts: Array[Array] = []
var _stream_holder: Control
var _demo: Demo
var _revealed := false
var archive := false


func setup(content_: FeedContent, record_: GameRecord, release_: int, cash_: int) -> void:
	content = content_
	record = record_
	release = release_
	cash = cash_


## Лента прошлого релиза панелью слева (#78; справа на главном экране столбик релизов).
func setup_archive(content_: FeedContent, record_: GameRecord) -> void:
	setup(content_, record_, 0, 0)
	archive = true


## Прямоугольник панели архива: колонка с полями карточки, у левого края экрана.
static func archive_rect() -> Rect2:
	var w := COLUMN_WIDTH + 2 * SHADOW_PAD + 2 * Style.PAD_CARD
	return Rect2(Style.EDGE / 2.0, Style.SPRINT_CARD_TOP, w,
			Style.SCREEN.y - Style.SPRINT_CARD_TOP - Style.SPRINT_CARD_BOTTOM)


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()
	await card.raise_card()
	_reveal()


func _exit_tree() -> void:
	_demo = null


func at_end() -> bool:
	return index >= _items.size() - 1


func _unhandled_input(event: InputEvent) -> void:
	if event.is_echo():
		return
	var viewport := get_viewport()
	if MouseUi.is_motion(event):
		# Наведение (#82): кнопки внизу берут фокус; посты не листаются от курсора.
		for i in _buttons.size():
			if at_end() and MouseUi.hit(_buttons[i], event) and focus_demo != (i == 0):
				set_focus_demo(i == 0)
		return
	if MouseUi.is_mouse(event):
		if _mouse(event):
			MouseUi.consume(viewport)
		return
	var key := event as InputEventKey
	if archive and key != null and key.pressed and key.keycode == KEY_ESCAPE:
		ShellSounds.play(&"done")
		finished.emit()
		MouseUi.consume(viewport)
		return
	if event.is_action_pressed(GameInput.DOWN):
		move(1)
	elif event.is_action_pressed(GameInput.UP):
		move(-1)
	elif event.is_action_pressed(GameInput.LEFT):
		if at_end():
			set_focus_demo(true)
	elif event.is_action_pressed(GameInput.RIGHT):
		if at_end():
			set_focus_demo(false)
	elif GameInput.is_a(event):
		if at_end():
			confirm()
		else:
			scroll_to_end()
	elif GameInput.is_b(event):
		ShellSounds.play(&"done")
		finished.emit()
	else:
		return
	get_viewport().set_input_as_handled()


## Мышь: колесо листает по карточке, клик по кнопке нажимает её.
func _mouse(event: InputEvent) -> bool:
	var w := MouseUi.wheel(event)
	if w != 0:
		move(w)
		return true
	if not MouseUi.is_click(event):
		return false
	for i in _buttons.size():
		if MouseUi.hit(_buttons[i], event):
			set_focus_demo(i == 0)
			confirm()
			return true
	return false


## Листание по карточке: выбранная встаёт по центру области.
func move(dir: int) -> void:
	var next := clampi(index + dir, 0, _items.size() - 1)
	if next == index:
		return
	index = next
	ShellSounds.play(&"tick")
	_center_on(index, true)
	_refresh_buttons()
	_refresh_item_focus()


func scroll_to_end() -> void:
	index = _items.size() - 1
	focus_demo = false
	ShellSounds.play(&"tick")
	_center_on(index, true)
	_refresh_buttons()
	_refresh_item_focus()


func set_focus_demo(v: bool) -> void:
	index = _items.size() - 1
	if focus_demo != v:
		focus_demo = v
		ShellSounds.play(&"tick")
	_center_on(index, true)
	_refresh_buttons()


func confirm() -> void:
	if not _button_lifts.is_empty():
		_button_lifts[0 if focus_demo else 1].press()
	ShellSounds.play(&"done")
	if focus_demo:
		demo_requested.emit()
	else:
		finished.emit()


# --- Построение ---------------------------------------------------------------------------------

func _build() -> void:
	if not archive:
		_build_header()
	card = CardFrame.new()
	if archive:
		card.rect_override = archive_rect()
		card.from_left = true
		# Поверх студии и кнопок главного экрана: плотная, сквозь неё ничего не видно.
		card.add_theme_stylebox_override("panel", Style.card(true))
	add_child(card)
	var inner := card.inner()
	_scroll = ScrollContainer.new()
	_scroll.position = Vector2((inner.x - COLUMN_WIDTH) / 2.0 - SHADOW_PAD, 0)
	_scroll.size = Vector2(COLUMN_WIDTH + 2 * SHADOW_PAD, inner.y)
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	_scroll.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.content.add_child(_scroll)
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", SHADOW_PAD)
	margin.add_theme_constant_override("margin_right", SHADOW_PAD)
	margin.add_theme_constant_override("margin_top", SHADOW_PAD)
	margin.add_theme_constant_override("margin_bottom", SHADOW_PAD)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_scroll.add_child(margin)
	_column = VBoxContainer.new()
	_column.custom_minimum_size = Vector2(COLUMN_WIDTH, 0)
	_column.add_theme_constant_override("separation", ITEM_GAP)
	_column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(_column)

	for item in content.items:
		var node: Control
		match item.kind:
			FeedContent.Kind.TWEET:
				node = _make_tweet(item)
			FeedContent.Kind.CRITIC:
				node = _make_critic(item)
			FeedContent.Kind.CLIP:
				node = _make_stream(item)
			FeedContent.Kind.NUMBERS:
				node = _make_numbers(item)
		_column.add_child(node)
		_items.append(node)
		_item_lifts.append(_jelly_item(node))
	var buttons := _make_buttons()
	_column.add_child(buttons)
	_items.append(buttons)
	_item_lifts.append([])
	for n in _items:
		n.modulate.a = 0.0 if not Debug.skip_cards else 1.0
	_refresh_buttons()
	_refresh_item_focus.call_deferred()
	if archive:
		MouseUi.pass_through(self)
		return

	var hints := HBoxContainer.new()
	hints.alignment = BoxContainer.ALIGNMENT_CENTER
	hints.add_theme_constant_override("separation", 16)
	hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hints.offset_top = -(Style.PILL_HEIGHT + 16)
	hints.offset_bottom = -16
	hints.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hints.add_child(HintPill.make("↑ ↓ листать"))
	hints.add_child(HintPill.make(GameInput.hint(GameInput.A, "вниз, внизу выбрать")))
	hints.add_child(HintPill.make(GameInput.hint(GameInput.B, "дальше")))
	MouseUi.pass_through(self)
	add_child(hints)


## Шапка над карточкой: релиз и тег слева, деньги справа.
func _build_header() -> void:
	var header := HintPill.header(ShellHeader.release(release, "Отклик · %s" % content.tag))
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


func _reveal() -> void:
	if _revealed:
		return
	_revealed = true
	if Debug.skip_cards:
		return
	for i in _items.size():
		var n := _items[i]
		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_property(n, "modulate:a", 1.0, Style.SWITCH_SECONDS).set_delay(i * STAGGER_SECONDS)


## Мармелад ленты: посты пружинят при листании и вминаются под курсором; текущий пост на
## бледном нейтральном бортике (фокус виден, но не обещает нажатия). Ряд цифр: обе карточки.
func _jelly_item(node: Control) -> Array:
	var hosts: Array[Control] = []
	if node is PanelContainer:
		hosts.append(node)
	else:
		for child in node.get_children():
			if child is PanelContainer:
				hosts.append(child)
	var lifts: Array = []
	for h in hosts:
		Jelly.attach_container(h, Style.R_CARD, 16.0)
		var l := JellyLift.add_under(h, Style.R_CARD) if h.clip_contents else JellyLift.add_to(h, Style.R_CARD)
		l.neutral = true
		lifts.append(l)
	return lifts


func _refresh_item_focus() -> void:
	for i in _item_lifts.size():
		for l in _item_lifts[i]:
			(l as JellyLift).focused = i == index


## Прокрутка так, чтобы карточка `i` встала по центру области; крайние упираются в края.
func _center_on(i: int, animate: bool) -> void:
	var n := _items[i]
	var center := n.position.y + SHADOW_PAD + n.size.y / 2.0
	var target := clampf(center - _scroll.size.y / 2.0, 0.0, maxf(_column.size.y + 2 * SHADOW_PAD - _scroll.size.y, 0.0))
	if not animate or Debug.skip_cards:
		_scroll.scroll_vertical = int(target)
		return
	create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC).tween_property(_scroll, "scroll_vertical", int(target), Style.SWITCH_SECONDS)


## Карточка-основа одного размера для твитов и критиков: сплошная подложка, слева полоса
## акцента у критиков.
func _post(accent: Color) -> Array:
	var panel := PanelContainer.new()
	# Серые посты на белой карточке экрана: без теней иначе сливаются (мармелад, 2026-11-09).
	var sb := Style.inner_card()
	if accent.a > 0.0:
		# Полоса акцента слева: левая рамка стайлбокса, остальные стороны без рамки.
		sb.border_width_left = ACCENT_BAR
		sb.border_color = accent
		sb.content_margin_left = Style.PAD_CARD - ACCENT_BAR
	panel.add_theme_stylebox_override("panel", sb)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 24)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(row)
	return [panel, row]


func _make_tweet(item: FeedContent.Item) -> Control:
	var parts := _post(Color.TRANSPARENT)
	var panel: PanelContainer = parts[0]
	var row: HBoxContainer = parts[1]
	row.add_child(_face(Style.INK_3, "", 64))
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
	return panel


func _make_critic(item: FeedContent.Item) -> Control:
	var parts := _post(item.person.accent)
	var panel: PanelContainer = parts[0]
	var row: HBoxContainer = parts[1]
	row.add_child(_face(item.person.accent, item.person.name.substr(0, 1), 64))
	var col := VBoxContainer.new()
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.add_theme_constant_override("separation", 4)
	row.add_child(col)
	col.add_child(_label("Критик · " + item.person.subtitle, Style.FONT_CAPTION, Style.INK_3))
	col.add_child(_label(item.person.name, Style.FONT_BODY, item.person.accent))
	var quote := _label(item.text, Style.FONT_BODY, Style.INK)
	quote.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	col.add_child(quote)
	var score_box := HBoxContainer.new()
	score_box.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	score_box.add_theme_constant_override("separation", 2)
	row.add_child(score_box)
	var big := _label(_score_text(item.score), 56, Style.INK)
	big.add_theme_font_override("font", Style.mono_font())
	score_box.add_child(big)
	var denom := _label("/10", Style.FONT_CAPTION, Style.INK_3)
	denom.size_flags_vertical = Control.SIZE_SHRINK_END
	score_box.add_child(denom)
	return panel


## Стрим: живая запись геймплея (встроенная демка с багами записи), сверху имя стримера и
## онлайн, слева снизу говорящее пиксельное лицо, под кадром реплика.
func _make_stream(item: FeedContent.Item) -> Control:
	var panel := PanelContainer.new()
	var sb := Style.inner_card()
	sb.set_content_margin_all(0)
	panel.add_theme_stylebox_override("panel", sb)
	panel.clip_contents = true
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 0)
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(col)
	_stream_holder = Control.new()
	_stream_holder.custom_minimum_size = Vector2(COLUMN_WIDTH, STREAM_HEIGHT)
	_stream_holder.clip_contents = true
	_stream_holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_child(_stream_holder)
	var backdrop := ColorRect.new()
	backdrop.color = Style.STUDIO_INK
	backdrop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stream_holder.add_child(backdrop)
	_start_stream()
	# Шапка стрима поверх кадра: точка «в эфире», имя, онлайн.
	var top := HBoxContainer.new()
	top.position = Vector2(20, 16)
	top.add_theme_constant_override("separation", 12)
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stream_holder.add_child(top)
	var live := HintPill.make("● " + item.person.name)
	(live.get_child(0) as Label).add_theme_color_override("font_color", Style.SURFACE_SOLID)
	var live_sb := Style.flat(Style.DANGER, Style.R_PILL, Color.TRANSPARENT, 0)
	live_sb.content_margin_left = 16
	live_sb.content_margin_right = 16
	live_sb.content_margin_top = 6
	live_sb.content_margin_bottom = 6
	live.add_theme_stylebox_override("panel", live_sb)
	top.add_child(live)
	var online := HintPill.make(item.caption)
	var online_sb := Style.flat(Color(Style.INK, 0.7), Style.R_PILL, Color.TRANSPARENT, 0)
	online_sb.content_margin_left = 16
	online_sb.content_margin_right = 16
	online_sb.content_margin_top = 6
	online_sb.content_margin_bottom = 6
	online.add_theme_stylebox_override("panel", online_sb)
	(online.get_child(0) as Label).add_theme_color_override("font_color", Style.SURFACE_SOLID)
	top.add_child(online)
	# Лицо стримера в левом нижнем углу, на плашке.
	var cam := PanelContainer.new()
	cam.add_theme_stylebox_override("panel", Style.flat(Color(Style.INK, 0.75), Style.R_CTL, Color.TRANSPARENT, 8))
	cam.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cam.add_child(PixelFace.new(item.person.accent, 6))
	_stream_holder.add_child(cam)
	cam.position = Vector2(20, STREAM_HEIGHT - 16 - 96 - 16)
	var quote := _label(item.text, Style.FONT_BODY, Style.INK)
	quote.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var quote_margin := MarginContainer.new()
	for side in ["left", "right", "top", "bottom"]:
		quote_margin.add_theme_constant_override("margin_" + side, 24 if side != "left" and side != "right" else Style.PAD_CARD)
	quote_margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	quote_margin.add_child(quote)
	col.add_child(quote_margin)
	return panel


## Запустить встроенную демку записи; по концу перезапускается, как запись по кругу.
func _start_stream() -> void:
	if record == null or _stream_holder == null:
		return
	# Демка записи из каталога (#45); без неё кадр стрима остаётся фоном.
	_demo = DemoCatalog.create(record)
	if _demo == null:
		return
	_demo.set_anchors_preset(Control.PRESET_TOP_LEFT)
	_demo.setup(record, &"clip")
	_demo.embed(Vector2(COLUMN_WIDTH, STREAM_HEIGHT))
	_demo.demo_finished.connect(_on_stream_finished)
	_stream_holder.add_child(_demo)
	_stream_holder.move_child(_demo, 1)
	_demo.start()


func _on_stream_finished(_r: GameRecord, _reached: bool) -> void:
	if _demo != null:
		_demo.queue_free()
		_demo = null
	if is_inside_tree() and _stream_holder != null:
		_start_stream()


func _make_numbers(item: FeedContent.Item) -> Control:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", Style.GAP_CARDS)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(_number_card("Критики", _score_text(item.score), Style.INK))
	row.add_child(_number_card("Просмотры клипов", item.text, Style.INK))
	return row


func _number_card(caption: String, value: String, color: Color) -> Control:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.inner_card())
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
	for text in (["Играть демку", "Закрыть"] if archive else ["В демо", "Дальше"]):
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
		_button_lifts.append(Jelly.button(b))
	return row


## Фокус на кнопках только внизу ленты: тёмная в фокусе, остальные `surface-2`.
func _refresh_buttons() -> void:
	for i in _buttons.size():
		var on := at_end() and ((i == 0) == focus_demo)
		_buttons[i].add_theme_stylebox_override("panel", Style.flat(Style.INK if on else Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 0))
		_button_lifts[i].focused = on
		_button_labels[i].add_theme_color_override("font_color", Style.SURFACE_SOLID if on else Style.INK)


func _score_text(v: float) -> String:
	return "%d" % int(v) if is_equal_approx(v, roundf(v)) else "%.1f" % v


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
		var font := c.get_theme_default_font()
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


func _spacer_w(w: int) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(w, 0)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c
