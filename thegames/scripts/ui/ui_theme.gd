extends Node
## Автолоад `UiTheme`: вешает тему оболочки из `Style.make_theme()` на корневое окно, так
## что каждый Control в проекте наследует её без своих .tres. Перестроить после смены
## палитры: `UiTheme.apply()`.


func _ready() -> void:
	apply()
	# Ручки мармелада общие для всех сцен; Debug готов только после своего `_ready`.
	Jelly.register_debug.call_deferred()


func apply() -> void:
	get_tree().root.theme = Style.make_theme()
