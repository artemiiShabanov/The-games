class_name SoftOutline
extends RefCounted
## Упругий контур: кольцо точек на пружинах к правильному многоугольнику вокруг центра. Точки
## разложены по углу, поэтому смена числа сторон перетекает из формы в форму, а не щёлкает.
## Центр ведёт хозяин; рывок центра (тряска) догоняется с запаздыванием и качанием. Жёсткость
## и затухание из материала `Jelly.tuning()`.
## Цель при смене сторон не прыгает, а за `MORPH_SECONDS` плавно переезжает от прежнего
## многоугольника к новому (плейтест 2026-11-14, #131): иначе точки, которым ехать дальше всех
## (бывшие углы, они попадают на середины новых граней), перелетали цель, и грани на миг
## выглядели переломленными пополам. По расчёту на материале игры перелёт при смене квадрата на
## треугольник был 21 px, с переездом за 0,3 с около 2,5 px.

const MORPH_SECONDS := 0.3

var points := PackedVector2Array()
var velocities := PackedVector2Array()
var sides := 5
var radius := 100.0
var center := Vector2.ZERO
var _ready := false
var _target_sides := -1
var _from := PackedVector2Array()
var _to := PackedVector2Array()
var _morph := 1.0


func _init(count := 96) -> void:
	points.resize(count)
	velocities.resize(count)


func reset(at: Vector2) -> void:
	center = at
	var shape := SoftBlob.polygon_shape(sides, radius, points.size(), 0.97)
	for i in points.size():
		points[i] = at + shape[i]
		velocities[i] = Vector2.ZERO
	_target_sides = sides
	_from = shape
	_to = shape
	_morph = 1.0
	_ready = true


## Форма-цель сейчас: на переезде между прежним и новым многоугольником.
func _target() -> PackedVector2Array:
	if _morph >= 1.0:
		return _to
	var k := smoothstep(0.0, 1.0, _morph)
	var out := PackedVector2Array()
	out.resize(_to.size())
	for i in _to.size():
		out[i] = _from[i].lerp(_to[i], k)
	return out


## Толчок от центра: попадание раздувает контур.
func pulse(strength: float) -> void:
	for i in points.size():
		velocities[i] += (points[i] - center).normalized() * strength


func step(delta: float, at: Vector2) -> void:
	if not _ready:
		reset(at)
	center = at
	var tu := Jelly.tuning()
	if sides != _target_sides:
		# Новая цель: переезд начинается с того места, где цель сейчас.
		_from = _target()
		_to = SoftBlob.polygon_shape(sides, radius, points.size(), 0.97)
		_target_sides = sides
		_morph = 0.0
	_morph = minf(_morph + delta / MORPH_SECONDS, 1.0)
	var shape := _target()
	var n := points.size()
	var subs := maxi(1, ceili(delta / SoftBlob.SUBSTEP))
	var dt := delta / subs
	for k in subs:
		for i in n:
			var p := points[i]
			var avg := (points[(i - 1 + n) % n] + points[(i + 1) % n]) * 0.5
			var a := (at + shape[i] - p) * tu.blob_stiffness - velocities[i] * tu.blob_damping
			a += (avg - p) * tu.blob_neighbor * 0.5
			velocities[i] += a * dt
		for i in n:
			points[i] += velocities[i] * dt


## Обводка толщины `width` с круглыми стыками.
func draw(ci: CanvasItem, col: Color, width: float) -> void:
	var closed := PackedVector2Array(points)
	closed.append(points[0])
	ci.draw_polyline(closed, col, width, true)
	for p in points:
		ci.draw_circle(p, width / 2.0, col)
