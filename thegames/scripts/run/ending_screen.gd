class_name EndingScreen
extends Control
## Экран концовки (#68), спека `docs/specs/run.md`: в большой карточке название концовки,
## оценка крупно (деньги у продажи и корпорации, очки у легенды), подпись, как она считалась,
## число релизов; три лучшие игры забега живыми встроенными демками (`DemoWindow`) с названием
## и оценкой критиков, у легенды кадры крупнее. Банкротство короче: без оценки и демок. Кнопка
## «В галерею» (␣, клик) отдаёт `to_gallery`.

signal to_gallery

const TITLE_FONT := 96
const SCORE_FONT := 88
const BOT_SECONDS := 1.2

var result: Endings.Result
var card: CardFrame
var _button: PanelContainer
var _lift: JellyLift
var _done := false
var _bot_timer := 0.0


func setup(result_: Endings.Result) -> void:
	result = result_


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()
	card.raise_card()
	ShellSounds.play(&"bug" if result.id == Endings.Id.BANKRUPTCY else &"done")


func _unhandled_input(event: InputEvent) -> void:
	# Выбор может синхронно увести экран из дерева, поэтому вьюпорт берётся заранее.
	var viewport := get_viewport()
	if _done:
		return
	if (MouseUi.is_click(event) and MouseUi.hit(_button, event)) or (not event.is_echo() and GameInput.is_a(event)):
		press()
		MouseUi.consume(viewport)


func _process(delta: float) -> void:
	if _done or not AutoTest.bot_active():
		return
	_bot_timer += delta
	if _bot_timer >= BOT_SECONDS:
		press()


func press() -> void:
	if _done:
		return
	_done = true
	_lift.press()
	Jelly.poke(_button, -2.0)
	ShellSounds.play(&"tick")
	to_gallery.emit()


func _build() -> void:
	var header := HintPill.header(ShellHeader.text("Конец забега"))
	header.position = Vector2(Style.EDGE, Style.HEADER_Y - Style.PILL_HEIGHT / 2.0)
	add_child(header)
	card = CardFrame.new()
	add_child(card)
	var inner := CardFrame.inner_size()
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 16)
	column.size = inner
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.content.add_child(column)

	column.add_child(_label("Концовка", Style.FONT_H2, Style.INK_2))
	var title := _label(result.title(), TITLE_FONT, Style.DANGER if result.id == Endings.Id.BANKRUPTCY else Style.INK)
	title.add_theme_font_override("font", Jelly.fun_font(800))
	column.add_child(title)
	if result.score_text() != "":
		var score := _label(result.score_text(), SCORE_FONT, Style.MONEY if result.id != Endings.Id.LEGEND else Style.INK)
		score.add_theme_font_override("font", Style.mono_font())
		column.add_child(score)
	column.add_child(_label(result.caption(), Style.FONT_BODY, Style.INK_2))
	column.add_child(_label("%s · %s" % [_releases_text(result.releases), "студия «%s»" % result.studio if result.studio != "" else ""],
			Style.FONT_BODY, Style.INK_2))

	if result.id != Endings.Id.BANKRUPTCY and not result.top.is_empty():
		var big := result.id == Endings.Id.LEGEND
		var w := floorf((inner.x - 2 * Style.GAP_CARDS) / 3.0) if big else 400.0
		var frame := Vector2(w, roundf(w * 9.0 / 16.0))
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", Style.GAP_CARDS)
		row.mouse_filter = Control.MOUSE_FILTER_IGNORE
		row.size_flags_vertical = Control.SIZE_EXPAND_FILL
		column.add_child(row)
		for g in result.top:
			row.add_child(_game(g, frame))
	else:
		var filler := Control.new()
		filler.size_flags_vertical = Control.SIZE_EXPAND_FILL
		filler.mouse_filter = Control.MOUSE_FILTER_IGNORE
		column.add_child(filler)

	var bottom := HBoxContainer.new()
	bottom.alignment = BoxContainer.ALIGNMENT_END
	bottom.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(bottom)
	_button = PanelContainer.new()
	_button.custom_minimum_size = Vector2(420, Style.BUTTON_HEIGHT)
	_button.add_theme_stylebox_override("panel", Style.flat(Style.INK, Style.R_CTL, Color.TRANSPARENT, 0))
	_button.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var bl := _label("В галерею", Style.FONT_H2, Style.SURFACE_SOLID)
	bl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	bl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_button.add_child(bl)
	bottom.add_child(_button)
	_lift = Jelly.button(_button)
	_lift.focused = true

	var hints := HBoxContainer.new()
	hints.alignment = BoxContainer.ALIGNMENT_CENTER
	hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hints.offset_top = -(Style.PILL_HEIGHT + 16)
	hints.offset_bottom = -16
	hints.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hints.add_child(HintPill.make(GameInput.hint(GameInput.A, "в галерею")))
	add_child(hints)
	MouseUi.pass_through(self)


## Игра: живая демка, под ней название и оценка критиков.
func _game(g: GameRecord, frame: Vector2) -> Control:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 8)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var window := DemoWindow.new()
	window.setup(g, frame)
	box.add_child(window)
	var line := HBoxContainer.new()
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(line)
	var name_label := _label(g.title, Style.FONT_BODY, Style.INK)
	name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	name_label.custom_minimum_size = Vector2(frame.x - 80, 0)
	line.add_child(name_label)
	var c := _label("%.1f" % g.score.critics, Style.FONT_BODY, Style.INK_2)
	c.add_theme_font_override("font", Style.mono_font())
	line.add_child(c)
	return box


static func _releases_text(n: int) -> String:
	var m10 := n % 10
	var m100 := n % 100
	var word := "релизов"
	if m10 == 1 and m100 != 11:
		word = "релиз"
	elif m10 >= 2 and m10 <= 4 and (m100 < 12 or m100 > 14):
		word = "релиза"
	return "%d %s" % [n, word]


func _label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l
