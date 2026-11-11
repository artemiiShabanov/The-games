extends Node
## Автолоад `UiTheme`: вешает тему оболочки из `Style.make_theme()` на корневое окно, так
## что каждый Control в проекте наследует её без своих .tres. Перестроить после смены
## палитры: `UiTheme.apply()`. Заодно следит, мышь или клавиатура сейчас у игрока
## (`GameInput.note`).


func _ready() -> void:
	apply()
	# Последнее устройство ввода для пилюль (#83): сигнал окна видит событие до того, как его
	# съест какой-нибудь экран.
	get_tree().root.window_input.connect(GameInput.note)
	# Ручки мармелада общие для всех сцен; Debug готов только после своего `_ready`.
	Jelly.register_debug.call_deferred()


func apply() -> void:
	get_tree().root.theme = Style.make_theme()
