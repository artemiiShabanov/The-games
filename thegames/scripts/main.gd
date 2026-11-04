class_name Main
extends Control
## Главная сцена: фон студии, поверх него появятся экраны петли релиза.
## Пока пустая оболочка; скаффолд, issue #1.

func _ready() -> void:
	if AutoTest.enabled:
		AutoTest.note("main scene ready")
