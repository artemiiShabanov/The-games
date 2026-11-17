extends Node
## Автолоад `UiTheme`: вешает тему оболочки из `Style.make_theme()` на корневое окно, так
## что каждый Control в проекте наследует её без своих .tres. Перестроить после смены
## палитры: `UiTheme.apply()`. Заодно следит, мышь или клавиатура сейчас у игрока
## (`GameInput.note`).


func _ready() -> void:
	# Настройки игры (#81): шины звука, окно, движение, подписи; первым делом на старте.
	Options.boot()
	apply()
	# Последнее устройство ввода для пилюль (#83): сигнал окна видит событие до того, как его
	# съест какой-нибудь экран.
	get_tree().root.window_input.connect(GameInput.note)
	# Ручки мармелада общие для всех сцен; Debug готов только после своего `_ready`.
	Jelly.register_debug.call_deferred()
	_register_debug.call_deferred()


func apply() -> void:
	get_tree().root.theme = Style.make_theme()


## Палитра в дебаг-меню (раздел «Оболочка»): то же, что строка «Палитра» в настройках.
func _register_debug() -> void:
	var ids: Array = []
	for id in Style.PALETTE_IDS:
		ids.append(String(id))
	Debug.add_choice(&"Оболочка", "Палитра", ids, func() -> String: return String(Options.palette),
			_set_palette, true)


func _set_palette(v: String) -> void:
	Options.palette = StringName(v)
	Options.apply()
