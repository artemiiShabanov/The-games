class_name JellyShape
extends RefCounted
## Мармеладная фигура для мини-игр (STYLE «Мармелад»): мягкое тело `SoftBlob` любой формы
## (скруглённый прямоугольник, круг, многоугольник), которое хозяин ведёт центром, поворотом и
## масштабом из своего `_on_tick`/`_process`, а рисует в `_draw`. Резкий сдвиг центра тело
## догоняет с запаздыванием и качанием, `poke` вздрагивает (попадание, выбор), `push` толкает
## точки (удар сбоку). `draw_lifted` рисует фигуру на бортике темнее себя: так в мини-играх
## показывается выделенный объект вместо синей рамки. Числа из материала `Jelly.tuning()`.

var blob: SoftBlob
var size := Vector2.ZERO
var _started := false


## Скруглённый прямоугольник `size` с радиусом `radius`.
static func rect(size_: Vector2, radius: float, points := 40) -> JellyShape:
	var s := JellyShape.new()
	s.size = size_
	s.blob = SoftBlob.new(minf(size_.x, size_.y) / 2.0)
	s.blob.set_shape(rect_outline(size_, radius, points))
	s.blob.collide = false
	s.blob.stretch_free = true
	return s


## Контур скруглённого прямоугольника по периметру, а не по углу из центра: у каждого угла
## своя дуга из `CORNER_SEGMENTS` отрезков, поэтому скругление одинаково круглое при любой
## длине (плейтест 2026-11-14, #131: у длинных блоков углы выходили гранёными). Остаток
## `points` идёт на прямые стороны по их длине. Порядок тот же, против часовой в
## математических осях.
const CORNER_SEGMENTS := 8

static func rect_outline(size_: Vector2, radius: float, points := 40) -> PackedVector2Array:
	var half := size_ / 2.0
	var r := minf(radius, minf(half.x, half.y))
	var straight: Array[float] = [size_.y - 2.0 * r, size_.x - 2.0 * r, size_.y - 2.0 * r, size_.x - 2.0 * r]
	var total := 2.0 * (straight[0] + straight[1])
	var spare := maxi(points - 4 * (CORNER_SEGMENTS + 1), 4)
	var corners: Array[Vector2] = [Vector2(1, 1), Vector2(-1, 1), Vector2(-1, -1), Vector2(1, -1)]
	var out := PackedVector2Array()
	for k in 4:
		var c := corners[k] * (half - Vector2(r, r))
		for j in CORNER_SEGMENTS + 1:
			var a := (k + float(j) / CORNER_SEGMENTS) * PI / 2.0
			out.append(c + Vector2(cos(a), sin(a)) * r)
		# Прямая сторона от конца этой дуги до начала следующей: точки внутри, без концов.
		var from := out[out.size() - 1]
		var next_c := corners[(k + 1) % 4] * (half - Vector2(r, r))
		var a_next := (k + 1) * PI / 2.0
		var to := next_c + Vector2(cos(a_next), sin(a_next)) * r
		var inner := int(round(spare * straight[(k + 1) % 4] / total)) if total > 0.0 else 0
		for j in inner:
			out.append(from.lerp(to, float(j + 1) / (inner + 1)))
	return out


static func circle(r: float, points := 32) -> JellyShape:
	var s := JellyShape.new()
	s.size = Vector2(r, r) * 2.0
	s.blob = SoftBlob.new(r)
	var pts := PackedVector2Array()
	for i in points:
		var a := TAU * i / points
		pts.append(Vector2(cos(a), sin(a)) * r)
	s.blob.set_shape(pts)
	s.blob.collide = false
	s.blob.stretch_free = true
	return s


## Правильный многоугольник вершиной вверх, острия чуть притуплены.
static func polygon(sides: int, r: float, points := 48) -> JellyShape:
	var s := JellyShape.new()
	s.size = Vector2(r, r) * 2.0
	s.blob = SoftBlob.new(r)
	s.blob.set_shape(SoftBlob.polygon_shape(sides, r, points))
	s.blob.collide = false
	s.blob.stretch_free = true
	return s


## Точки контура скруглённого прямоугольника вокруг нуля по углу, против часовой (в
## математических осях), как ждёт `SoftBlob`.
static func rect_points(size_: Vector2, radius: float, n: int) -> PackedVector2Array:
	var half := size_ / 2.0
	var r := minf(radius, minf(half.x, half.y))
	var out := PackedVector2Array()
	for i in n:
		var a := TAU * i / n
		var d := Vector2(cos(a), sin(a))
		# Луч из центра до контура: пересечение со скруглённым прямоугольником бинарным поиском.
		var lo := 0.0
		var hi := half.length() + 1.0
		for k in 18:
			var mid := (lo + hi) / 2.0
			var p := d * mid
			var q := (p.abs() - half + Vector2(r, r))
			var sd := Vector2(maxf(q.x, 0.0), maxf(q.y, 0.0)).length() + minf(maxf(q.x, q.y), 0.0) - r
			if sd < 0.0:
				lo = mid
			else:
				hi = mid
		out.append(d * lo)
	return out


## Вести фигуру: центр, поворот, масштаб. Первый вызов ставит тело на место без качания.
func follow(delta: float, center: Vector2, angle := 0.0, scale := 1.0) -> void:
	blob.angle = angle
	blob.shape_scale = scale
	if not _started:
		_started = true
		blob.reset(center)
		return
	blob.step(delta, center, Callable())


## Поставить без качания (телепорт, новый объект).
func snap(center: Vector2) -> void:
	_started = true
	blob.reset(center)


## Вздрог: `strength` > 0 раздувает, < 0 сжимает; 150-400 заметно, мармелад гасит быстро.
func poke(strength := 250.0) -> void:
	blob.pulse(strength)


## Толчок точкам скоростью `v`; со `side` только той стороне, что смотрит туда.
func push(v: Vector2, side := Vector2.ZERO) -> void:
	blob.impulse(v, side)


func contour(offset := Vector2.ZERO) -> PackedVector2Array:
	return blob.polygon(offset, 2)


func draw(ci: CanvasItem, color: Color, offset := Vector2.ZERO) -> void:
	if blob.points.is_empty():
		return
	Jelly.fill(ci, contour(offset), color)


## Обводка контура толщины `width` (трафареты, рамки внутри поля).
func draw_outline(ci: CanvasItem, color: Color, width: float, offset := Vector2.ZERO) -> void:
	if blob.points.is_empty():
		return
	var c := contour(offset)
	c.append(c[0])
	ci.draw_polyline(c, color, width, true)


## Фигура на бортике высотой `lift` (выделение вместо синей рамки): снизу та же форма темнее.
func draw_lifted(ci: CanvasItem, color: Color, lift: float, offset := Vector2.ZERO) -> void:
	if blob.points.is_empty():
		return
	if lift > 0.2:
		Jelly.fill(ci, contour(offset + Vector2(0.0, lift)), Jelly.lip_color(color))
	Jelly.fill(ci, contour(offset), color)
