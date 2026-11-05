class_name Main
extends Control
## Главная сцена: фон студии, поверх него появятся экраны петли релиза.
## Пока пустая оболочка; скаффолд, issue #1.

func _ready() -> void:
	($Background as ColorRect).color = Style.BG
	($Title as Label).add_theme_color_override("font_color", Style.STUDIO_INK)
	if AutoTest.enabled:
		AutoTest.note("main scene ready")
