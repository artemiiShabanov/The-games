class_name StudioLogo
extends RefCounted
## Логотип студии (#61, плейтест 2026-11-10): форма из фигур игры (круг, скруглённый квадрат,
## ромб, шестиугольник), цвет фона из `StudioNames.logo_colors` и абстрактный символ поверх
## белым. Разыгрывается вместе с названием, R на «Новой студии» перегенерирует оба.
## Рисует `StudioLogoView`; здесь только данные и геометрия символа.

enum Shape { CIRCLE, SQUARE, DIAMOND, HEXAGON }

const SYMBOLS := 12

var shape := Shape.CIRCLE
var color := Color("#2F5BFF")
var symbol := 0


static func make(names: StudioNames, rng: RandomNumberGenerator) -> StudioLogo:
	var l := StudioLogo.new()
	l.shape = rng.randi_range(0, Shape.size() - 1) as Shape
	if not names.logo_colors.is_empty():
		l.color = names.logo_colors[rng.randi_range(0, names.logo_colors.size() - 1)]
	l.symbol = rng.randi_range(0, SYMBOLS - 1)
	return l


## Другой логотип: хотя бы форма или символ не те же.
func another(names: StudioNames, rng: RandomNumberGenerator) -> StudioLogo:
	for i in 8:
		var l := make(names, rng)
		if l.shape != shape or l.symbol != symbol:
			return l
	return make(names, rng)


func _to_string() -> String:
	return "%s %s #%d" % [Shape.keys()[shape], color.to_html(false), symbol]


## Символ белым по центру `c`, `r` радиус фигуры фона. `bg` цвет фона: им вырезается
## полумесяц и середина глаза.
static func draw_symbol(ci: CanvasItem, symbol_: int, c: Vector2, r: float, bg: Color) -> void:
	var ink := Color.WHITE
	var s := r * 0.42
	var w := maxf(r * 0.12, 2.0)
	match symbol_:
		0:
			ci.draw_colored_polygon(_star(c, s, s * 0.45, 5), ink)
		1:
			ci.draw_colored_polygon(_ngon(c, s * 1.05, 3, -PI / 2.0, Vector2(0, s * 0.15)), ink)
		2:
			ci.draw_arc(c, s * 0.8, 0.0, TAU, 48, ink, w * 1.3, true)
		3:
			ci.draw_rect(Rect2(c - Vector2(s, w * 0.7), Vector2(s * 2.0, w * 1.4)), ink)
			ci.draw_rect(Rect2(c - Vector2(w * 0.7, s), Vector2(w * 1.4, s * 2.0)), ink)
		4:
			for k in 3:
				var y := (k - 1) * s * 0.65
				ci.draw_line(c + Vector2(-s, y), c + Vector2(s, y), ink, w, true)
		5:
			ci.draw_colored_polygon(PackedVector2Array([
				c + Vector2(0.15, -1.0) * s, c + Vector2(-0.55, 0.15) * s, c + Vector2(-0.05, 0.15) * s,
				c + Vector2(-0.2, 1.0) * s, c + Vector2(0.55, -0.2) * s, c + Vector2(0.05, -0.2) * s,
			]), ink)
		6:
			for k in 3:
				var a := -PI / 2.0 + TAU * k / 3.0
				ci.draw_circle(c + Vector2.from_angle(a) * s * 0.6, s * 0.3, ink)
		7:
			var pts := PackedVector2Array()
			for k in 25:
				var x := -1.0 + 2.0 * k / 24.0
				pts.append(c + Vector2(x * s, sin(x * PI * 1.5) * s * 0.35))
			ci.draw_polyline(pts, ink, w * 1.2, true)
		8:
			for k in 2:
				var y := (k - 0.5) * s * 0.7 + s * 0.2
				ci.draw_polyline(PackedVector2Array([c + Vector2(-s * 0.8, y), c + Vector2(0, y - s * 0.6),
						c + Vector2(s * 0.8, y)]), ink, w * 1.2, true)
		9:
			ci.draw_circle(c, s * 0.9, ink)
			ci.draw_circle(c + Vector2(s * 0.45, -s * 0.3), s * 0.75, bg)
		10:
			ci.draw_arc(c, s * 0.9, 0.0, TAU, 48, ink, w, true)
			ci.draw_circle(c, s * 0.38, ink)
		_:
			for k in 3:
				var a := PI / 2.0 + PI * k / 3.0
				var d := Vector2.from_angle(a) * s
				ci.draw_line(c - d, c + d, ink, w * 1.2, true)


static func _ngon(c: Vector2, r: float, n: int, a0: float, shift := Vector2.ZERO) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in n:
		out.append(c + shift + Vector2.from_angle(a0 + TAU * i / n) * r)
	return out


static func _star(c: Vector2, ro: float, ri: float, n: int) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in n * 2:
		var a := -PI / 2.0 + PI * i / n
		out.append(c + Vector2.from_angle(a) * (ro if i % 2 == 0 else ri))
	return out
