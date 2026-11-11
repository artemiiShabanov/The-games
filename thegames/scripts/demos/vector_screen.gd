class_name VectorScreen
extends SubViewportContainer
## Экран векторных демок (#88, `docs/specs/demos_catalog.md`): светящиеся линии на чёрном, как
## векторный монитор аркад. Своё окно `SubViewport`, которое не стирается между кадрами: каждый
## кадр поверх ложится полупрозрачный фон (`persistence`), и всё, что двигалось, оставляет
## гаснущий след люминофора. Линии рисуются сложением цветов в три прохода: широкий тусклый
## ореол, средний и яркое ядро, светлее чернил. Демка рисует в колбэке `draw_fn(screen)` через
## `line`, `poly`, `shape`, `digits`, `cross_box`; координаты в пикселях логического экрана
## `logical_size` (карточка демки), во встроенном режиме окно меньше и всё уменьшено.
## Цвета: `palette[0]` фон, дальше чернила по номеру (`SettingDef.vector_colors`); розовые
## чернила `PINK_INK` для заглушки. Счётчик `segments` (отрезков за прошлый кадр) нужен багу
## технологии «луч не успевает» (#89).

const PINK_INK := 255
## Стрихи цифр и знаков HUD в клетке 0..1 × 0..1 (y вниз), как у сегментного табло: векторные
## аркады рисовали счёт линиями, шрифтом здесь не обойтись.
const STROKES := {
	"0": [[0, 0, 1, 0], [1, 0, 1, 1], [1, 1, 0, 1], [0, 1, 0, 0], [0, 1, 1, 0]],
	"1": [[0.5, 0, 0.5, 1], [0.25, 0.2, 0.5, 0]],
	"2": [[0, 0, 1, 0], [1, 0, 1, 0.5], [1, 0.5, 0, 0.5], [0, 0.5, 0, 1], [0, 1, 1, 1]],
	"3": [[0, 0, 1, 0], [1, 0, 1, 1], [1, 1, 0, 1], [0.2, 0.5, 1, 0.5]],
	"4": [[0, 0, 0, 0.5], [0, 0.5, 1, 0.5], [1, 0, 1, 1]],
	"5": [[1, 0, 0, 0], [0, 0, 0, 0.5], [0, 0.5, 1, 0.5], [1, 0.5, 1, 1], [1, 1, 0, 1]],
	"6": [[1, 0, 0, 0], [0, 0, 0, 1], [0, 1, 1, 1], [1, 1, 1, 0.5], [1, 0.5, 0, 0.5]],
	"7": [[0, 0, 1, 0], [1, 0, 0.4, 1]],
	"8": [[0, 0, 1, 0], [1, 0, 1, 1], [1, 1, 0, 1], [0, 1, 0, 0], [0, 0.5, 1, 0.5]],
	"9": [[1, 0.5, 0, 0.5], [0, 0.5, 0, 0], [0, 0, 1, 0], [1, 0, 1, 1], [1, 1, 0, 1]],
	":": [[0.5, 0.25, 0.5, 0.35], [0.5, 0.65, 0.5, 0.75]],
	"/": [[1, 0, 0, 1]],
	"-": [[0.1, 0.5, 0.9, 0.5]],
	"+": [[0.1, 0.5, 0.9, 0.5], [0.5, 0.15, 0.5, 0.85]],
	"x": [[0.1, 0.3, 0.9, 1], [0.9, 0.3, 0.1, 1]],
	"!": [[0.5, 0, 0.5, 0.65], [0.5, 0.85, 0.5, 1]],
}

var viewport: SubViewport
## Размер логического экрана: в нём демка задаёт координаты.
var logical_size := Vector2(1664, 832)
var palette: Array[Color] = [Color.BLACK, Color.WHITE]
## Доля прошлого кадра, которая остаётся через 1/60 с: след люминофора.
var persistence := 0.55
## Ореол линий; выключатель в дебаг-меню («Вектор»).
var glow := true
var draw_fn := Callable()
## Отрезков за прошлый кадр и розовых заглушек в нём (проверки, баг «луч не успевает»).
var segments := 0
var pink_drawn := 0
var _fade: Node2D
var _world: Node2D
var _counting := 0
var _pinks := 0
var _dt := 1.0 / 60.0
## Первый кадр заливает фон целиком: окно до него не стёрто.
var _first := true


## Экран размером `area` для логического экрана `logical`; встроенный режим это `area` меньше.
static func make(area: Vector2, logical: Vector2, palette_: Array[Color]) -> VectorScreen:
	var s := VectorScreen.new()
	s.logical_size = logical
	s.palette = palette_
	s.size = area
	s.custom_minimum_size = area
	s.stretch = true
	s.mouse_filter = Control.MOUSE_FILTER_IGNORE
	s.viewport = SubViewport.new()
	s.viewport.size = Vector2i(area)
	s.viewport.transparent_bg = false
	# Буфер с плавающей точкой: в 8 битах затухание тусклых следов округляется и не доходит до
	# фона, на экране висят призраки старых кадров.
	s.viewport.use_hdr_2d = true
	s.viewport.render_target_clear_mode = SubViewport.CLEAR_MODE_ONCE
	s.viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	s.add_child(s.viewport)
	s._fade = Node2D.new()
	s._fade.draw.connect(s._draw_fade)
	s.viewport.add_child(s._fade)
	s._world = Node2D.new()
	var add := CanvasItemMaterial.new()
	add.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	s._world.material = add
	s._world.scale = area / logical
	s._world.draw.connect(s._draw_world)
	s.viewport.add_child(s._world)
	return s


func _process(delta: float) -> void:
	_dt = delta
	if _fade != null:
		_fade.queue_redraw()
		_world.queue_redraw()


func _draw_fade() -> void:
	var keep := 0.0 if _first else pow(persistence, _dt * 60.0)
	_first = false
	_fade.draw_rect(Rect2(Vector2.ZERO, Vector2(viewport.size)), Color(palette[0], 1.0 - keep))


func _draw_world() -> void:
	_counting = 0
	_pinks = 0
	if draw_fn.is_valid():
		draw_fn.call(self)
	segments = _counting
	pink_drawn = _pinks


func ink(i: int) -> Color:
	return Demo.PINK if i == PINK_INK else palette[clampi(i, 0, palette.size() - 1)]


## Ломаная со свечением; `closed` замыкает её. Звать только из `draw_fn`.
func poly(points: PackedVector2Array, ink_i: int, closed := false, width := 2.0, alpha := 1.0) -> void:
	if points.size() < 2:
		return
	var pts := points
	if closed:
		pts = points.duplicate()
		pts.append(points[0])
	var c := ink(ink_i)
	_counting += pts.size() - 1
	if ink_i == PINK_INK:
		_pinks += 1
	if glow:
		_world.draw_polyline(pts, Color(c, 0.07 * alpha), width * 5.0, true)
		_world.draw_polyline(pts, Color(c, 0.18 * alpha), width * 2.4, true)
	_world.draw_polyline(pts, Color(c.lerp(Color.WHITE, 0.35), alpha), width, true)


func line(a: Vector2, b: Vector2, ink_i: int, width := 2.0, alpha := 1.0) -> void:
	poly(PackedVector2Array([a, b]), ink_i, false, width, alpha)


## Контуры (`VectorShapes`) в точке `center`: `px` логических пикселей на пиксель спрайта,
## зеркало по x, поворот.
func shape(contours: Array[PackedVector2Array], center: Vector2, px: float, ink_i: int, flip := false,
		angle := 0.0, width := 2.0) -> void:
	var xf := Transform2D(angle, center).scaled_local(Vector2(-px if flip else px, px))
	for c in contours:
		poly(xf * c, ink_i, true, width)


## Розовая заглушка: квадрат с крестом размером `size`.
func cross_box(center: Vector2, size: float, width := 2.0) -> void:
	var h := size / 2.0
	var r := PackedVector2Array([center + Vector2(-h, -h), center + Vector2(h, -h), center + Vector2(h, h), center + Vector2(-h, h)])
	poly(r, PINK_INK, true, width)
	line(r[0], r[2], PINK_INK, width)
	line(r[1], r[3], PINK_INK, width)


## Строка штрихами `STROKES` с верхнего левого угла `pos`, высота знака `h`.
func digits(pos: Vector2, text: String, h: float, ink_i: int, width := 2.0) -> void:
	var w := h * 0.55
	var x := pos.x
	for ch in text:
		var strokes: Array = STROKES.get(ch, [])
		for s: Array in strokes:
			line(Vector2(x + float(s[0]) * w, pos.y + float(s[1]) * h), Vector2(x + float(s[2]) * w, pos.y + float(s[3]) * h), ink_i, width)
		x += w * 1.6


## Ширина строки `digits` высотой `h`.
static func digits_width(text: String, h: float) -> float:
	return maxf(0.0, text.length() * h * 0.55 * 1.6 - h * 0.55 * 0.6)
