class_name CardFrame
extends PanelContainer
## Большая карточка поверх студии (STYLE: отступы 96 по бокам, 112 сверху под шапку, 72
## снизу; без тени, с толщиной снизу): в ней идут спринты и демки (решения 2026-11-05 и 2026-11-06). Всплывает снизу за
## `CARD_RISE_SECONDS` с перелётом, уезжает вниз за `CARD_DROP_SECONDS`; `Debug.skip_cards`
## сводит анимации к одному кадру. Содержимое кладётся в `content`, размер которого равен
## внутренней области карточки.

var content: Control
var shown := false


func _init() -> void:
	add_theme_stylebox_override("panel", Style.card())
	clip_contents = true
	visible = false
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	content = Control.new()
	content.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(content)


func _ready() -> void:
	var parent := get_parent_control()
	if parent != null:
		parent.resized.connect(layout)
	layout()
	# Мармелад: карточка тянется и пружинит при всплытии и уходе (на курсор не реагирует), от
	# фона её отделяет толщина. Бортик соседом перед ней: карточка режет содержимое
	# (`clip_contents`) и срезала бы его.
	Jelly.attach_frame(self)
	_add_lip.call_deferred()


## Отложенно: в своём `_ready` родитель ещё занят детьми и не примет соседа.
func _add_lip() -> void:
	if get_parent() != null:
		JellyLift.add_under(self, Style.R_CARD, Style.CARD_THICKNESS)


## Прямоугольник карточки на экране родителя размером `parent_size`.
static func rect_in(parent_size: Vector2) -> Rect2:
	return Rect2(Style.EDGE, Style.SPRINT_CARD_TOP, parent_size.x - 2 * Style.EDGE,
			parent_size.y - Style.SPRINT_CARD_TOP - Style.SPRINT_CARD_BOTTOM)


## Внутренняя область карточки на базовом экране `Style.SCREEN`, без отступов подложки.
static func inner_size() -> Vector2:
	return rect_in(Vector2(Style.SCREEN)).size - Vector2(2 * Style.PAD_CARD, 2 * Style.PAD_CARD)


func layout() -> void:
	var r := rect_in(_parent_size())
	size = r.size
	position = r.position if shown else Vector2(r.position.x, _parent_size().y)


## Всплыть снизу; `sound` звук оболочки `intro`.
func raise_card(sound := true) -> void:
	var r := rect_in(_parent_size())
	size = r.size
	visible = true
	shown = true
	if sound:
		ShellSounds.play(&"intro")
	if Debug.skip_cards:
		position = r.position
		await get_tree().process_frame
		return
	position = Vector2(r.position.x, _parent_size().y)
	var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)
	tw.tween_property(self, "position:y", r.position.y, Style.CARD_RISE_SECONDS)
	await tw.finished


## Уехать вниз и скрыться.
func drop_card() -> void:
	shown = false
	if Debug.skip_cards:
		visible = false
		await get_tree().process_frame
		return
	var tw := create_tween().set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(self, "position:y", _parent_size().y, Style.CARD_DROP_SECONDS)
	await tw.finished
	visible = false


## Тряска по горизонтали на `SHAKE_PX` (STYLE: удар при провале).
func shake_card() -> void:
	var x0 := position.x
	var tw := create_tween()
	for i in range(4):
		tw.tween_property(self, "position:x", x0 + Style.SHAKE_PX * (1 if i % 2 == 0 else -1), 0.04)
	tw.tween_property(self, "position:x", x0, 0.04)


func _parent_size() -> Vector2:
	var parent := get_parent_control()
	return parent.size if parent != null else Vector2(Style.SCREEN)
