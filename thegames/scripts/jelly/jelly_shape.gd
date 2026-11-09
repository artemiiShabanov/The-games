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
	s.blob.set_shape(rect_points(size_, radius, points))
	s.blob.collide = false
	s.blob.stretch_free = true
	return s


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
