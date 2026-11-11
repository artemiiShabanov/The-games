class_name MouseUi
extends RefCounted
## Мышь в оболочке (плейтест 2026-11-08, #43): экраны держат все свои Control с
## `MOUSE_FILTER_IGNORE` и разбирают мышь сами в `_unhandled_input`: колесо листает, клик по
## карточке выбирает её, клик по кнопке нажимает. Наведение переносит фокус (плейтест 2026-11-11,
## #82), колесо и тачпад листают (`scroll_px`). Здесь общие проверки событий и попадание в
## прямоугольник Control с учётом масштаба карточки.


static func is_click(event: InputEvent) -> bool:
	var m := event as InputEventMouseButton
	return m != null and m.pressed and m.button_index == MOUSE_BUTTON_LEFT


## Сколько дробных шагов колеса или пикселей жеста тачпада дают один шаг листания.
const PAN_STEP := 3.0

static var _acc := 0.0


## Шаг листания: −1 вверх, 1 вниз, 0 не листание. Колесо мыши шаг на щелчок; тачпад (#82)
## шлёт колесо дробными `factor` или жест панорамирования, они копятся до шага.
static func wheel(event: InputEvent) -> int:
	var pan := event as InputEventPanGesture
	if pan != null:
		return _accumulate(pan.delta.y / PAN_STEP)
	var m := event as InputEventMouseButton
	if m == null or not m.pressed:
		return 0
	var dir := 0
	if m.button_index == MOUSE_BUTTON_WHEEL_UP:
		dir = -1
	elif m.button_index == MOUSE_BUTTON_WHEEL_DOWN:
		dir = 1
	if dir == 0:
		return 0
	if m.factor <= 0.0 or m.factor >= 1.0:
		_acc = 0.0
		return dir
	return _accumulate(dir * m.factor)


static func _accumulate(v: float) -> int:
	if signf(v) != signf(_acc):
		_acc = 0.0
	_acc += v
	if absf(_acc) >= 1.0:
		var step := int(signf(_acc))
		_acc = 0.0
		return step
	return 0


## Прокрутка колесом или тачпадом (#82) в пикселях: колесо с его `factor` (тачпад на macOS
## шлёт колесо дробными шагами), жест панорамирования двумя пальцами. 0, если не прокрутка.
static func scroll_px(event: InputEvent, step := 120.0) -> float:
	var m := event as InputEventMouseButton
	if m != null and m.pressed:
		var f := m.factor if m.factor > 0.0 else 1.0
		if m.button_index == MOUSE_BUTTON_WHEEL_UP:
			return -step * f
		if m.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			return step * f
		return 0.0
	var pan := event as InputEventPanGesture
	if pan != null:
		return pan.delta.y * step / 4.0
	return 0.0


## Наведение (#82): курсор сдвинулся.
static func is_motion(event: InputEvent) -> bool:
	return event is InputEventMouseMotion


## Кнопка мыши, колесо или жест тачпада: экраны разбирают их в своём `_mouse`.
static func is_mouse(event: InputEvent) -> bool:
	return event is InputEventMouseButton or event is InputEventPanGesture


## Прямоугольник Control на экране с учётом scale и pivot.
static func rect_of(c: Control) -> Rect2:
	return c.get_global_transform() * Rect2(Vector2.ZERO, c.size)


## Точка события на экране: мышь или жест тачпада; `null`, если у события её нет.
static func point(event: InputEvent) -> Variant:
	var m := event as InputEventMouse
	if m != null:
		return m.position
	var g := event as InputEventGesture
	if g != null:
		return g.position
	return null


static func hit(c: Control, event: InputEvent) -> bool:
	var p: Variant = point(event)
	return p != null and c != null and c.is_visible_in_tree() and rect_of(c).has_point(p)


## Все Control под узлом пропускают мышь, чтобы она доходила до `_unhandled_input` экрана.
static func pass_through(node: Node) -> void:
	if node is Control:
		(node as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
	for child in node.get_children():
		pass_through(child)


## Ввод съеден. Вьюпорт берётся до выбора: выбор может синхронно увести экран из дерева, и тогда
## `get_viewport()` уже пуст.
static func consume(viewport: Viewport) -> void:
	if viewport != null:
		viewport.set_input_as_handled()
