class_name BugfixOffer
extends Control
## Карточка предложения спринта багфикса после плейтеста (#27): сколько багов, что починит
## успех, цена, кнопки «Купить» и «Отказаться». Влево-вправо фокус, A подтверждает, B и Esc
## отказ. Денег не хватает: кнопка покупки серая с суммой нехватки и трясётся. Деньги не
## списывает: хозяин по сигналу `accepted`.

signal accepted
signal declined

var record: GameRecord
var catalog: BugCatalog
var cost := 0
var cash := 0
var focus_buy := true

var _card: Control
var _buttons: Array[PanelContainer] = []
var _labels: Array[Label] = []


func setup(record_: GameRecord, catalog_: BugCatalog, cost_: int, cash_: int) -> void:
	record = record_
	catalog = catalog_
	cost = cost_
	cash = cash_


func affordable() -> bool:
	return cash >= cost


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	focus_buy = affordable()
	_build()
	if not Debug.skip_cards:
		_card.modulate.a = 0.0
		_card.position.y = Style.SCREEN_SLIDE_PX
		var tw := create_tween().set_parallel(true).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_property(_card, "modulate:a", 1.0, Style.SWITCH_SECONDS)
		tw.tween_property(_card, "position:y", 0.0, Style.SWITCH_SECONDS)
	ShellSounds.play(&"intro")


func _unhandled_input(event: InputEvent) -> void:
	if event.is_echo():
		return
	if MouseUi.is_click(event):
		for i in _buttons.size():
			if MouseUi.hit(_buttons[i], event):
				set_focus_buy(i == 0)
				confirm()
				get_viewport().set_input_as_handled()
				return
		return
	if MouseUi.is_mouse(event):
		return
	if event.is_action_pressed(GameInput.LEFT):
		set_focus_buy(true)
	elif event.is_action_pressed(GameInput.RIGHT):
		set_focus_buy(false)
	elif GameInput.is_a(event):
		confirm()
	elif GameInput.is_b(event):
		decline()
	else:
		return
	get_viewport().set_input_as_handled()


func set_focus_buy(v: bool) -> void:
	if focus_buy == v:
		return
	focus_buy = v
	ShellSounds.play(&"tick")
	_refresh()


func confirm() -> void:
	if focus_buy:
		if not affordable():
			_shake(_buttons[0])
			ShellSounds.play(&"miss")
			return
		ShellSounds.play(&"done")
		accepted.emit()
	else:
		decline()


func decline() -> void:
	ShellSounds.play(&"tick")
	declined.emit()


func _build() -> void:
	_card = Control.new()
	_card.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_card)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.card(true))
	panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	panel.custom_minimum_size = Vector2(Style.FEED_WIDTH, 0)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_card.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 16)
	panel.add_child(column)
	column.add_child(_label("Спринт багфикса", Style.FONT_H1, Style.INK, true))
	var n := record.bug_ids.size()
	var fix := Bugfix.fix_count(record)
	column.add_child(_label("Багов в сборке: %d. Успех чинит %d из них, какие именно, решит QA." % [n, fix],
			Style.FONT_BODY, Style.INK_2, true))
	# Штампы текущих багов.
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 12)
	column.add_child(row)
	for id in record.bug_ids:
		var bug := catalog.by_id(id) if catalog != null else null
		var pill := PanelContainer.new()
		var sb := Style.flat(Style.BUG, Style.R_PILL, Color.TRANSPARENT, 0)
		sb.content_margin_left = 18
		sb.content_margin_right = 18
		sb.content_margin_top = 6
		sb.content_margin_bottom = 6
		pill.add_theme_stylebox_override("panel", sb)
		var l := _label(bug.stamp if bug != null else String(id), Style.FONT_CAPTION + 2, Style.SURFACE_SOLID, false)
		pill.add_child(l)
		row.add_child(pill)
	column.add_child(_label("Цена обычного спринта: %s · у вас %s" % [Style.format_money(cost), Style.format_money(cash)],
			Style.FONT_BODY, Style.INK_2, true))
	var buttons := HBoxContainer.new()
	buttons.alignment = BoxContainer.ALIGNMENT_CENTER
	buttons.add_theme_constant_override("separation", Style.GAP_CARDS)
	column.add_child(buttons)
	for text in ["Купить", "Отказаться"]:
		var b := PanelContainer.new()
		b.custom_minimum_size = Vector2(280, Style.BUTTON_HEIGHT)
		b.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var l := _label(text, Style.FONT_H2, Style.INK, true)
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		b.add_child(l)
		buttons.add_child(b)
		_buttons.append(b)
		_labels.append(l)
	var pill_row := HBoxContainer.new()
	pill_row.alignment = BoxContainer.ALIGNMENT_CENTER
	pill_row.add_child(HintPill.make("← → выбрать · %s подтвердить · %s отказаться" % [GameInput.key(GameInput.A), GameInput.key(GameInput.B)]))
	column.add_child(pill_row)
	MouseUi.pass_through(self)
	_refresh()


func _refresh() -> void:
	for i in _buttons.size():
		var on := (i == 0) == focus_buy
		var active := i != 0 or affordable()
		var bg := Style.INK if on and active else Style.SURFACE_2
		var ink := Style.INK_3
		if active:
			ink = Style.SURFACE_SOLID if on else Style.INK
		_buttons[i].add_theme_stylebox_override("panel", Style.flat(bg, Style.R_CTL, Style.FOCUS if on and not active else Color.TRANSPARENT, 0))
		_labels[i].add_theme_color_override("font_color", ink)
	_labels[0].text = "Купить" if affordable() else "Не хватает " + Style.format_money(cost - cash)


func _shake(node: Control) -> void:
	var x0 := node.position.x
	var tw := create_tween()
	for i in range(4):
		tw.tween_property(node, "position:x", x0 + Style.SHAKE_PX * (1 if i % 2 == 0 else -1), 0.04)
	tw.tween_property(node, "position:x", x0, 0.04)


func _label(text: String, font_size: int, color: Color, center: bool) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if center:
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l
