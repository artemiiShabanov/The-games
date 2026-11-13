class_name ThreedHud
extends RefCounted
## Рисовалка HUD демок «продвинутых» (плейтест #122: «мыльный и бедный»). Демка задаёт места и
## размеры в виртуальном экране `LowpolyScreen.view`, а рисуется всё в настоящих пикселях
## экрана: слой HUD увеличен в `u` раз, поэтому фигуры со сглаживанием и шрифт, нарисованные в
## виртуальных единицах, расплывались бы. `begin` снимает увеличение, дальше каждая фигура
## умножает свои числа на `u`; в конце `end`. Плашки со скруглением, тенью и кромкой; их цвет
## берётся из палитры сеттинга (плейтест #122): подложка это тёмный тон роли «стена» (у пиратов
## морёное дерево), кромка это цвет бонуса (у пиратов золото).

const WHITE := Color(1.0, 1.0, 1.0, 0.97)
const DIM := Color(1.0, 1.0, 1.0, 0.55)
const FAINT := Color(1.0, 1.0, 1.0, 0.22)
const GOLD := Color(1.0, 0.79, 0.28)
const RED := Color(0.96, 0.3, 0.27)
const GREEN := Color(0.36, 0.86, 0.5)

var canvas: CanvasItem
var u := 1.0
## Подложка плашек, её кромка и самый тёмный тон (середина прибора) от сеттинга.
var glass := Color(0.05, 0.07, 0.11, 0.8)
var edge := Color(1.0, 1.0, 1.0, 0.16)
var deep := Color(0.03, 0.04, 0.07, 0.95)


static func begin(canvas_: CanvasItem, screen: LowpolyScreen) -> ThreedHud:
	var h := ThreedHud.new()
	h.canvas = canvas_
	h.u = maxf(screen.hud.scale.x, 1.0)
	if not screen.palette.is_empty():
		var wall := screen.ink(LowpolyScreen.WALL)
		h.glass = Color(wall.darkened(0.62), 0.86)
		h.deep = Color(wall.darkened(0.8), 0.96)
		h.edge = Color(screen.ink(LowpolyScreen.BONUS), 0.5)
	canvas_.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE / h.u)
	return h


func end() -> void:
	canvas.draw_set_transform(Vector2.ZERO)


## Плашка: тёмное стекло со скруглением `radius`, тенью и кромкой.
func panel(rect: Rect2, radius := 6.0) -> void:
	var box := StyleBoxFlat.new()
	box.bg_color = glass
	box.set_corner_radius_all(int(radius * u))
	box.corner_detail = 12
	box.set_border_width_all(maxi(int(0.4 * u), 1))
	box.border_color = edge
	box.shadow_color = Color(0.0, 0.0, 0.0, 0.3)
	box.shadow_size = int(3.0 * u)
	box.shadow_offset = Vector2(0.0, 1.0 * u)
	box.anti_aliasing = true
	canvas.draw_style_box(box, Rect2(rect.position * u, rect.size * u))


## Строка: `align` −1 от левого края `at`, 0 по середине, 1 от правого. `at.y` это середина
## строки по высоте.
func text(at: Vector2, value: String, size: float, color := WHITE, align := 0, outline := Color(0.0, 0.0, 0.0, 0.0), weight := 800) -> void:
	var font := Jelly.fun_font(weight)
	var px := maxi(int(size * u), 6)
	var box := font.get_string_size(value, HORIZONTAL_ALIGNMENT_LEFT, -1, px)
	var x := at.x * u - (box.x / 2.0 if align == 0 else (box.x if align > 0 else 0.0))
	var pos := Vector2(x, at.y * u + font.get_ascent(px) / 2.0 - font.get_descent(px) / 2.0)
	if outline.a > 0.0:
		canvas.draw_string_outline(font, pos, value, HORIZONTAL_ALIGNMENT_LEFT, -1, px, maxi(int(px * 0.16), 2), outline)
	canvas.draw_string(font, pos, value, HORIZONTAL_ALIGNMENT_LEFT, -1, px, color)


func circle(center: Vector2, radius: float, color: Color) -> void:
	canvas.draw_circle(center * u, radius * u, color, true, -1.0, true)


func arc(center: Vector2, radius: float, from: float, to: float, color: Color, width: float) -> void:
	canvas.draw_arc(center * u, radius * u, from, to, maxi(int(absf(to - from) * 24.0), 6), color, width * u, true)


func line(a: Vector2, b: Vector2, color: Color, width: float) -> void:
	canvas.draw_line(a * u, b * u, color, width * u, true)


## Линия со скруглёнными концами (полосы прогресса).
func bar(a: Vector2, b: Vector2, color: Color, width: float) -> void:
	line(a, b, color, width)
	circle(a, width / 2.0, color)
	circle(b, width / 2.0, color)


func polygon(points: PackedVector2Array, color: Color) -> void:
	var scaled := PackedVector2Array()
	for p in points:
		scaled.append(p * u)
	canvas.draw_colored_polygon(scaled, color)
	scaled.append(scaled[0])
	canvas.draw_polyline(scaled, color, 1.0, true)


func polyline(points: PackedVector2Array, color: Color, width: float) -> void:
	var scaled := PackedVector2Array()
	for p in points:
		scaled.append(p * u)
	canvas.draw_polyline(scaled, color, width * u, true)


func rect(r: Rect2, color: Color) -> void:
	canvas.draw_rect(Rect2(r.position * u, r.size * u), color)


## Сердце с серединой в `center`.
func heart(center: Vector2, size: float, color: Color) -> void:
	var points := PackedVector2Array()
	for k in 48:
		var a := TAU * k / 48.0
		points.append(center + Vector2(16.0 * pow(sin(a), 3.0), -(13.0 * cos(a) - 5.0 * cos(2.0 * a) - 2.0 * cos(3.0 * a) - cos(4.0 * a))) * size / 17.0)
	polygon(points, color)
