class_name GameInput
extends RefCounted
## Единый набор ввода игры, спека `docs/specs/minigames.md`: стрелки, A, B.
## Клавиатура основная: стрелки или WASD; A = Z, пробел, Enter; B = X, C, Ctrl (Esc с B снят
## плейтестом 2026-11-08: Esc только паузы и отказы оболочки). Мышь в мини-играх (#83):
## левая кнопка = A, правая = B, своё у каждой игры (`Minigame._mouse_action`). Геймпад:
## крестовина и левый стик, кнопка юга A, кнопка востока B. Действия заданы в
## `project.godot` ([input]); код обращается к ним только через эти имена. Подписи в
## интерфейсе реальными клавишами через `key(action)`: «␣» и «Ctrl» на клавиатуре, кнопки
## геймпада, когда он станет устройством.

const LEFT: StringName = &"move_left"
const RIGHT: StringName = &"move_right"
const UP: StringName = &"move_up"
const DOWN: StringName = &"move_down"
const A: StringName = &"action_a"
const B: StringName = &"action_b"

const ALL: Array[StringName] = [LEFT, RIGHT, UP, DOWN, A, B]

enum Device { KEYBOARD, GAMEPAD }

## Подписи клавиатуры: стрелки глифами, A пробел, B Ctrl.
const LABELS := {
	LEFT: "←", RIGHT: "→", UP: "↑", DOWN: "↓", A: "␣", B: "Ctrl",
}
## Подписи геймпада (кнопки юга и востока), для будущего переключения устройства.
const GAMEPAD_LABELS := {
	LEFT: "←", RIGHT: "→", UP: "↑", DOWN: "↓", A: "Ⓐ", B: "Ⓑ",
}

## Текущее устройство подписей; геймпад переключит, когда появится его поддержка в оболочке.
static var device := Device.KEYBOARD
## Игрок сейчас на мыши (#83): последним нажал кнопку мыши или крутил колесо, а не клавишу.
## Пилюли ввода мини-игр показывают тогда подсказку мыши (`HintPill.for_inputs`). Обновляет
## `note`, его зовёт автолоад `UiTheme` на каждое событие окна.
static var mouse := false


## Подпись действия реальной клавишей текущего устройства.
static func key(action: StringName) -> String:
	var table: Dictionary = GAMEPAD_LABELS if device == Device.GAMEPAD else LABELS
	return str(table.get(action, String(action)))


## «␣ дальше»: подпись с глаголом.
static func hint(action: StringName, text: String) -> String:
	return key(action) + " " + text


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


## Последнее устройство ввода: нажатие кнопки мыши включает мышь, клавиша или кнопка геймпада
## возвращают клавиатуру. Движение мыши не в счёт: случайно задетая мышь не меняет подсказки.
static func note(event: InputEvent) -> void:
	if event is InputEventMouseButton and (event as InputEventMouseButton).pressed:
		mouse = true
	elif (event is InputEventKey or event is InputEventJoypadButton) and event.is_pressed():
		mouse = false


## Какое из игровых действий несёт событие, или пустое имя.
static func action_of(event: InputEvent) -> StringName:
	for action in ALL:
		if event.is_action(action):
			return action
	return &""
