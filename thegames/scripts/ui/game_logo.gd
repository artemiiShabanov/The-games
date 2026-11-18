class_name GameLogo
extends Control
## Логотип Studio Running (2026-11-17): две строки Nunito 900, в «Running» буква ı без точки, на
## месте точки горит лампа «в эфире» (как `RunningLamp`: цвет `accent`, дышит, с выключенным
## движением интерфейса горит ровно). Точка ставится по ширине глифов, а не на глаз.

const TOP := "Studio"
const BOTTOM := "Runnıng"
## Индекс ı в нижней строке.
const DOT_INDEX := 4
## Шаг строк и положение точки в долях кегля (концепт: кегль 64, шаг 68, центр точки на 43
## выше базовой линии, радиус 7,5 чуть крупнее родной точки).
const LINE_STEP := 1.06
const DOT_RISE := 0.672
const DOT_RADIUS := 0.117
## Сжатие букв в долях кегля (концепт: −2 на кегль 64).
const TRACKING := -0.031

var font_size := 140
## Отступ слева сверх поля карточки: крупные буквы у самого края выглядят прижатыми.
var inset := 40.0
var _font: FontVariation
var _t := 0.0


func _ready() -> void:
	# Копия, а не обёртка: внешний FontVariation сбрасывает ось жирности внутреннего.
	_font = (Jelly.fun_font(900) as FontVariation).duplicate() as FontVariation
	_font.spacing_glyph = roundi(TRACKING * font_size)
	var w := maxf(_width(TOP), _width(BOTTOM))
	custom_minimum_size = Vector2(ceilf(w + inset), ceilf(font_size * (1.0 + LINE_STEP) + font_size * 0.28))
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _process(delta: float) -> void:
	_t += delta
	queue_redraw()


func _width(text: String) -> float:
	return _font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x


func _draw() -> void:
	var ascent := _font.get_ascent(font_size)
	var base1 := ascent
	var base2 := base1 + font_size * LINE_STEP
	draw_string(_font, Vector2(inset, base1), TOP, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, Style.INK)
	draw_string(_font, Vector2(inset, base2), BOTTOM, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, Style.INK)
	var before := _width(BOTTOM.substr(0, DOT_INDEX))
	# Ширина ı разностью строк: так в неё входят кернинг и сжатие букв (сжатие добавлено после
	# глифа, поэтому центр самой буквы без него).
	var glyph := _width(BOTTOM.substr(0, DOT_INDEX + 1)) - before - _font.spacing_glyph
	var c := Vector2(inset + before + glyph * 0.5, base2 - font_size * DOT_RISE)
	var k := 1.0
	if Jelly.enabled:
		k = 0.5 + 0.5 * cos(TAU * _t / Style.LAMP_BREATH_SECONDS)
	var r := font_size * DOT_RADIUS
	var halo := r * 0.8
	draw_circle(c, r + halo * 0.5, Color(Style.ACCENT, 0.22 * k), false, halo * 0.6, true)
	draw_circle(c, r, Color(Style.ACCENT, lerpf(Style.LAMP_DIM, 1.0, k)), true, -1.0, true)
