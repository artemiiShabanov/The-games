class_name MouseUi
extends RefCounted
## Мышь в оболочке (плейтест 2026-11-08, #43): экраны держат все свои Control с
## `MOUSE_FILTER_IGNORE` и разбирают мышь сами в `_unhandled_input`: колесо листает, клик по
## карточке выбирает её, клик по кнопке нажимает. Ховера нет. Здесь общие проверки событий и
## попадание в прямоугольник Control с учётом масштаба карточки.


static func is_click(event: InputEvent) -> bool:
	var m := event as InputEventMouseButton
	return m != null and m.pressed and m.button_index == MOUSE_BUTTON_LEFT


## −1 колесо вверх, 1 вниз, 0 не колесо.
static func wheel(event: InputEvent) -> int:
	var m := event as InputEventMouseButton
	if m == null or not m.pressed:
		return 0
	if m.button_index == MOUSE_BUTTON_WHEEL_UP:
		return -1
	if m.button_index == MOUSE_BUTTON_WHEEL_DOWN:
		return 1
	return 0


static func is_mouse(event: InputEvent) -> bool:
	return event is InputEventMouseButton


## Прямоугольник Control на экране с учётом scale и pivot.
static func rect_of(c: Control) -> Rect2:
	return c.get_global_transform() * Rect2(Vector2.ZERO, c.size)


static func hit(c: Control, event: InputEvent) -> bool:
	var m := event as InputEventMouse
	return m != null and c != null and c.is_visible_in_tree() and rect_of(c).has_point(m.position)


## Все Control под узлом пропускают мышь, чтобы она доходила до `_unhandled_input` экрана.
static func pass_through(node: Node) -> void:
	if node is Control:
		(node as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
	for child in node.get_children():
		pass_through(child)
