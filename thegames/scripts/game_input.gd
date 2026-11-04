class_name GameInput
extends RefCounted
## Единый набор ввода игры, спека `docs/specs/minigames.md`: стрелки, A, B.
## Клавиатура основная: стрелки; A = Z, пробел, Enter; B = X, Esc.
## Геймпад: крестовина и левый стик, кнопка юга A, кнопка востока B.
## Действия заданы в `project.godot` ([input]); код обращается к ним только через эти имена.

const LEFT: StringName = &"move_left"
const RIGHT: StringName = &"move_right"
const UP: StringName = &"move_up"
const DOWN: StringName = &"move_down"
const A: StringName = &"action_a"
const B: StringName = &"action_b"

const ALL: Array[StringName] = [LEFT, RIGHT, UP, DOWN, A, B]
## Подписи для интро мини-игр и тестовых сцен.
const LABELS := {
	LEFT: "←", RIGHT: "→", UP: "↑", DOWN: "↓", A: "A", B: "B",
}


## Направление стрелок или стика, длина до 1.
static func axis() -> Vector2:
	return Input.get_vector(LEFT, RIGHT, UP, DOWN)


static func a_pressed() -> bool:
	return Input.is_action_pressed(A)


static func b_pressed() -> bool:
	return Input.is_action_pressed(B)


static func a_just_pressed() -> bool:
	return Input.is_action_just_pressed(A)


static func b_just_pressed() -> bool:
	return Input.is_action_just_pressed(B)


static func is_a(event: InputEvent) -> bool:
	return event.is_action_pressed(A)


static func is_b(event: InputEvent) -> bool:
	return event.is_action_pressed(B)


## Нажатие любого игрового действия: для «пропускается любой клавишей».
static func is_any_press(event: InputEvent) -> bool:
	if event.is_echo():
		return false
	for action in ALL:
		if event.is_action_pressed(action):
			return true
	return false


## Какое из игровых действий несёт событие, или пустое имя.
static func action_of(event: InputEvent) -> StringName:
	for action in ALL:
		if event.is_action(action):
			return action
	return &""
