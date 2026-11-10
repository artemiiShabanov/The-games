class_name EventCard
extends Control
## Карточка мета-вставки (#63), спека `docs/specs/meta.md`, концепт `06-meta-event`: модальная
## карточка поверх студии. Сверху портрет (живое `PixelFace` ленты в скруглённом квадрате
## `surface-2`, говорит, пока карточка ждёт ответа), над
## именем роль и фирма (и настроение, если не 0), имя, реплика; ниже два-три варианта строками
## `surface-2` с пилюлями последствий справа (`Events.Pill`: плюс зелёным, минус красным,
## ограничение синим, концовка тёмной). Над карточкой пилюли релиза и денег, внизу подсказки.
## ↑ ↓ выбрать, ␣ решить; мышь: наведение выбирает, клик решает. Решение отдаётся хозяину
## (`apply`: применяет и возвращает исход монетки), деньги прокручиваются, исход показывается
## строкой, через `MetaTuning.outcome_seconds` сигнал `finished(index)`.

signal decided(index: int)
signal finished(index: int)

const CARD_WIDTH := 1120
const FACE_BOX := 160.0
const FACE_SCALE := 8
const ROW_HEIGHT := 88
const NAME_FONT := 40
const LINE_FONT := 26
const ROW_FONT := 26

var offer: Events.Offer
var release := 1
var wallet: Wallet
## (index) -> String: применить ответ, вернуть исход (монетка) или пусто.
var apply: Callable
var meta: MetaTuning
var index := 0
var done := false
## Подложка `bg` под карточкой: поверх другого экрана (фаза студии).
var dim := false
var _bot_timer := 0.0

var _panel: PanelContainer
var _face: PixelFace
var _rows: Array[PanelContainer] = []
var _lifts: Array[JellyLift] = []
var _outcome: Label
var _money_label: Label
var _shown_money := 0.0


func setup(offer_: Events.Offer, release_: int, wallet_: Wallet, apply_: Callable, meta_: MetaTuning = null) -> void:
	offer = offer_
	release = release_
	wallet = wallet_
	apply = apply_
	meta = meta_ if meta_ != null else MetaTuning.load_default()


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()
	_refresh_focus()
	ShellSounds.play(&"intro")
	if not Debug.skip_cards:
		_panel.modulate.a = 0.0
		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_property(_panel, "modulate:a", 1.0, Style.SWITCH_SECONDS)


## Бот автотеста: WIN первый вариант, LOSE последний (обычно отказ).
func _process(delta: float) -> void:
	if done or not AutoTest.bot_active():
		return
	_bot_timer += delta
	if _bot_timer < 0.4:
		return
	index = 0 if AutoTest.bot_mode == AutoTest.BotMode.WIN else _rows.size() - 1
	_refresh_focus()
	confirm()


# --- Ввод ---------------------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if done:
		return
	if event is InputEventMouseMotion:
		var over := _row_at(event)
		if over >= 0 and over != index:
			index = over
			ShellSounds.play(&"tick")
			_refresh_focus()
		return
	if MouseUi.is_mouse(event):
		var at := _row_at(event)
		if at >= 0 and MouseUi.is_click(event):
			index = at
			confirm()
			get_viewport().set_input_as_handled()
		return
	if event.is_echo():
		return
	if event.is_action_pressed(GameInput.UP):
		move(-1)
	elif event.is_action_pressed(GameInput.DOWN):
		move(1)
	elif GameInput.is_a(event):
		confirm()
	else:
		return
	get_viewport().set_input_as_handled()


func _row_at(event: InputEvent) -> int:
	for i in _rows.size():
		if MouseUi.hit(_rows[i], event):
			return i
	return -1


func move(dir: int) -> void:
	var next := clampi(index + dir, 0, _rows.size() - 1)
	if next == index:
		ShellSounds.play(&"miss")
		return
	index = next
	ShellSounds.play(&"tick")
	_refresh_focus()


## Решить текущий вариант: хозяин применяет, карточка показывает исход и закрывается.
func confirm() -> void:
	if done:
		return
	done = true
	var i := index
	_lifts[i].press()
	Jelly.poke(_rows[i], -2.0)
	ShellSounds.play(&"done")
	for k in _rows.size():
		if k != i:
			create_tween().tween_property(_rows[k], "modulate:a", 0.35, Style.SWITCH_SECONDS)
	_face.talking = false
	decided.emit(i)
	var outcome := ""
	if apply.is_valid():
		outcome = str(apply.call(i))
	if wallet != null:
		_roll_money(wallet.cash)
	if outcome != "":
		_outcome.text = outcome
		_outcome.visible = true
		Jelly.poke(_panel, 1.0)
	var wait := meta.outcome_seconds if not Debug.skip_cards else 0.05
	await get_tree().create_timer(wait).timeout
	finished.emit(i)


# --- Построение -----------------------------------------------------------------------------------

func _build() -> void:
	if dim:
		var shade := ColorRect.new()
		shade.color = Color(Style.BG, 0.9)
		shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(shade)
	var header := HintPill.header(ShellHeader.release(release, "Вставка"))
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
	var money := HintPill.header("")
	_money_label = money.get_child(0) as Label
	_money_label.add_theme_font_override("font", Style.mono_font())
	_money_label.add_theme_color_override("font_color", Style.MONEY)
	right.add_child(money)
	_shown_money = float(wallet.cash) if wallet != null else 0.0
	_money_label.text = Style.format_money(int(_shown_money))
	money.visible = wallet != null

	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(center)
	_panel = PanelContainer.new()
	_panel.add_theme_stylebox_override("panel", Style.card(true))
	_panel.custom_minimum_size = Vector2(CARD_WIDTH, 0)
	_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	center.add_child(_panel)
	Jelly.panel(_panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 24)
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.add_child(column)

	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 32)
	head.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(head)
	head.add_child(_face_box())
	var text := VBoxContainer.new()
	text.add_theme_constant_override("separation", 8)
	text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	head.add_child(text)
	var who := offer.character
	text.add_child(_label(_who_line(), Style.FONT_CAPTION, Style.INK_3))
	var name_label := _label(who.name if who != null else "", NAME_FONT, Style.INK)
	name_label.add_theme_font_override("font", Jelly.fun_font(800))
	text.add_child(name_label)
	var say := _label("«%s»" % offer.line, LINE_FONT, Style.INK)
	say.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	say.custom_minimum_size = Vector2(CARD_WIDTH - 2 * Style.PAD_CARD - FACE_BOX - 32, 0)
	text.add_child(say)

	var options := VBoxContainer.new()
	options.add_theme_constant_override("separation", 12)
	options.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(options)
	for c in offer.choices:
		options.add_child(_row(c))
	_outcome = _label("", Style.FONT_H2, Style.INK)
	_outcome.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_outcome.visible = false
	column.add_child(_outcome)

	var hints := HBoxContainer.new()
	hints.alignment = BoxContainer.ALIGNMENT_CENTER
	hints.add_theme_constant_override("separation", 16)
	hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hints.offset_top = -(Style.PILL_HEIGHT + 40)
	hints.offset_bottom = -40
	hints.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hints.add_child(HintPill.make("↑ ↓ выбрать"))
	hints.add_child(HintPill.make(GameInput.hint(GameInput.A, "решить")))
	add_child(hints)
	MouseUi.pass_through(self)


## Роль · фирма · настроение (если персонаж помнит прошлые ответы).
func _who_line() -> String:
	var who := offer.character
	if who == null:
		return ""
	var parts: PackedStringArray = [who.role]
	if who.subtitle != "":
		parts.append(who.subtitle)
	if offer.mood > 0:
		parts.append("в хорошем настроении")
	elif offer.mood < 0:
		parts.append("помнит прошлый отказ")
	return " · ".join(parts)


func _face_box() -> Control:
	var box := PanelContainer.new()
	box.add_theme_stylebox_override("panel", Style.flat(Style.SURFACE_2, Style.R_CARD, Color.TRANSPARENT, 0))
	box.custom_minimum_size = Vector2(FACE_BOX, FACE_BOX)
	box.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var center := CenterContainer.new()
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(center)
	_face = PixelFace.new(offer.character.accent if offer.character != null else Style.INK_3, FACE_SCALE)
	center.add_child(_face)
	return box


func _row(c: Events.Choice) -> PanelContainer:
	var row := PanelContainer.new()
	var sb := Style.flat(Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 0)
	sb.content_margin_left = 32
	sb.content_margin_right = 24
	sb.content_margin_top = 16
	sb.content_margin_bottom = 16
	row.add_theme_stylebox_override("panel", sb)
	row.custom_minimum_size = Vector2(0, ROW_HEIGHT)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var line := HBoxContainer.new()
	line.add_theme_constant_override("separation", 12)
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(line)
	var t := _label(c.text, ROW_FONT, Style.INK)
	t.add_theme_font_override("font", Jelly.fun_font(700))
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	t.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	line.add_child(t)
	var pills := HFlowContainer.new()
	pills.alignment = FlowContainer.ALIGNMENT_END
	pills.add_theme_constant_override("h_separation", 8)
	pills.add_theme_constant_override("v_separation", 8)
	pills.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pills.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	pills.mouse_filter = Control.MOUSE_FILTER_IGNORE
	line.add_child(pills)
	for p in c.pills:
		pills.add_child(_pill(p))
	_rows.append(row)
	_lifts.append(Jelly.button(row))
	return row


static func pill_colors(tone: Events.Tone) -> Array[Color]:
	var out: Array[Color] = [Style.SURFACE_SOLID, Style.INK_2]
	match tone:
		Events.Tone.PLUS:
			out = [Style.TINT_PLUS, Style.MONEY]
		Events.Tone.MINUS:
			out = [Style.TINT_MINUS, Style.DANGER]
		Events.Tone.LOCK:
			out = [Style.TINT_LOCK, Style.FOCUS]
		Events.Tone.ENDING:
			out = [Style.INK, Style.SURFACE_SOLID]
	return out


func _pill(p: Events.Pill) -> Control:
	var colors := pill_colors(p.tone)
	if p.text == "или":
		var l := _label("или", Style.FONT_CAPTION, Style.INK_3)
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		l.custom_minimum_size = Vector2(0, 36)
		return l
	var pill := PanelContainer.new()
	var sb := Style.flat(colors[0], Style.R_PILL, Color.TRANSPARENT, 0)
	sb.content_margin_left = 16
	sb.content_margin_right = 16
	sb.content_margin_top = 4
	sb.content_margin_bottom = 4
	pill.add_theme_stylebox_override("panel", sb)
	pill.custom_minimum_size = Vector2(0, 36)
	pill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var l := _label(p.text, Style.FONT_CAPTION, colors[1])
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	pill.add_child(l)
	return pill


func _refresh_focus() -> void:
	for i in _lifts.size():
		_lifts[i].focused = i == index
	if not _rows.is_empty():
		Jelly.poke(_rows[index])


func _roll_money(to: int) -> void:
	var from := _shown_money
	_shown_money = float(to)
	if Debug.skip_cards or is_equal_approx(from, float(to)):
		_money_label.text = Style.format_money(to)
		return
	var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_method(func(v: float) -> void: _money_label.text = Style.format_money(int(roundf(v))),
			from, float(to), Style.SWITCH_SECONDS * 2.0)


func _label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l
