class_name AspectIcon
extends Control
## Значок аспекта, жанра или технологии в круге 96 px (STYLE: линия 4 px). До появления
## настоящих пиктограмм (M5) рисует первую букву владельца.

const SIZE := 96.0

var text := "?"
var color: Color = Style.INK


static func for_def(def: MinigameDef) -> AspectIcon:
	var icon := AspectIcon.new()
	icon.text = def.owner_name().substr(0, 1).to_upper()
	return icon


func _init() -> void:
	custom_minimum_size = Vector2(SIZE, SIZE)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _draw() -> void:
	var center := size / 2.0
	draw_arc(center, SIZE / 2.0 - 2.0, 0.0, TAU, 64, color, 4.0, true)
	# Шрифт темы (Nunito), а не встроенный.
	var font := get_theme_default_font()
	var font_size := 40
	var w := font.get_string_size(text, HORIZONTAL_ALIGNMENT_CENTER, -1, font_size).x
	draw_string(font, Vector2(center.x - w / 2.0, center.y + font_size * 0.36), text,
			HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)
