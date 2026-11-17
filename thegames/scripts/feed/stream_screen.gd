class_name StreamScreen
extends Control
## Стрим отдельным окном (полировка 2026-11-17: раньше кадр стрима стоял посреди ленты). Поверх
## главного экрана забега по центру карточка: крупный кадр живой записи (`StreamView`) и кнопка
## «Закрыть». Открывается карточкой волны «Стрим» после релиза и кнопкой «Стрим» в карточке игры.
## Esc, ␣, Ctrl, клик по кнопке или мимо карточки закрывают (`finished`); ввод окно разбирает
## само и вниз не пускает.

signal finished

const FRAME := Vector2(1200, 556)
const BUTTON := Vector2(280, 72)

var record: GameRecord
var item: FeedContent.Item

var _panel: PanelContainer
var _button: PanelContainer
var _lift: JellyLift


## `content` лента релиза: из неё берётся клип. Ложь, если клипа нет.
func setup(record_: GameRecord, content: FeedContent) -> bool:
	record = record_
	item = clip_of(content)
	return item != null


static func clip_of(content: FeedContent) -> FeedContent.Item:
	for it in content.items:
		if it.kind == FeedContent.Kind.CLIP:
			return it
	return null


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)
	_panel = PanelContainer.new()
	_panel.add_theme_stylebox_override("panel", Style.card(true))
	center.add_child(_panel)
	Jelly.panel(_panel)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 20)
	_panel.add_child(col)
	var view := StreamView.new()
	view.setup(record, item, FRAME)
	col.add_child(view)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	col.add_child(row)
	_button = PanelContainer.new()
	_button.custom_minimum_size = BUTTON
	_button.add_theme_stylebox_override("panel", Style.flat(Style.INK, Style.R_CTL, Color.TRANSPARENT, 0))
	var l := Label.new()
	l.text = "Закрыть"
	l.add_theme_font_size_override("font_size", Style.FONT_H2)
	l.add_theme_color_override("font_color", Style.SURFACE_SOLID)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_button.add_child(l)
	row.add_child(_button)
	_lift = Jelly.button(_button, Style.R_CTL)
	_lift.focused = true
	MouseUi.pass_through(self)
	if not Debug.skip_cards:
		modulate.a = 0.0
		create_tween().tween_property(self, "modulate:a", 1.0, Style.SWITCH_SECONDS)


func close() -> void:
	_lift.press()
	finished.emit()


func _unhandled_input(event: InputEvent) -> void:
	var viewport := get_viewport()
	if MouseUi.is_motion(event):
		return
	var key := event as InputEventKey
	var esc := key != null and key.pressed and not key.echo and key.keycode == KEY_ESCAPE
	if MouseUi.is_click(event):
		if MouseUi.hit(_button, event) or not MouseUi.hit(_panel, event):
			close()
	elif esc or (not event.is_echo() and (GameInput.is_a(event) or GameInput.is_b(event))):
		close()
	if event is InputEventKey or event is InputEventMouseButton or event is InputEventJoypadButton \
			or event is InputEventJoypadMotion or event is InputEventPanGesture:
		MouseUi.consume(viewport)
