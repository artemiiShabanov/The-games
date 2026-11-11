class_name SlimeTrail
extends RefCounted
## Склизкий след мармеладной фигуры (STYLE «Мармелад»): полоса во всю ширину протащенной фигуры
## со скруглёнными концами и поворотами, полупрозрачная одной заливкой, гаснет за `life`. Хозяин каждый кадр
## зовёт `add(pos, width)` центром фигуры, пока она тащится, `cut()` при прыжке или телепорте,
## `step(delta)` и рисует `draw(ci, offset)` под фигурой. Координаты хозяина (мира или поля).

class Mark:
	var pos := Vector2.ZERO
	var w := 0.0
	var born := 0.0
	var gap := false

## Шаг пути, по которому считается свежесть вершин контура, пиксели.
const FRESH_STEP := 16.0

var marks: Array[Mark] = []
var color := Color.WHITE
## Сколько живёт след, с, и непрозрачность свежего.
var life := 0.9
var alpha := 0.22
## Шаг между отметками, пиксели.
var spacing := 4.0
var time := 0.0


func _init(color_ := Color.WHITE, life_ := 0.9, alpha_ := 0.22) -> void:
	color = color_
	life = life_
	alpha = alpha_


func add(pos: Vector2, width: float) -> void:
	if not marks.is_empty() and not marks.back().gap and marks.back().pos.distance_to(pos) < spacing:
		return
	var m := Mark.new()
	m.pos = pos
	m.w = width
	m.born = time
	marks.append(m)


## Разрыв: следующий `add` начнёт новую полосу.
func cut() -> void:
	if marks.is_empty() or marks.back().gap:
		return
	var m := Mark.new()
	m.gap = true
	m.born = time
	marks.append(m)


func clear() -> void:
	marks.clear()


func step(delta: float) -> void:
	time += delta
	while not marks.is_empty() and time - marks[0].born > life:
		marks.pop_front()


## Каждая непрерывная полоса одной фигурой (плейтест 2026-11-11, #86): контур вокруг пути на
## полширины со скруглёнными стыками и концами (`Geometry2D.offset_polyline`, это объединение,
## путь может ложиться сам на себя), и фигура заливается одним вызовом. Полупрозрачные куски
## внахлёст не темнеют: их нет. Прозрачность гаснет от свежего конца к старому цветом вершин:
## у каждой вершины контура свежесть ближайшей точки пути.
func draw(ci: CanvasItem, offset := Vector2.ZERO) -> void:
	var run := PackedVector2Array()
	var fresh := PackedFloat32Array()
	var width := 0.0
	for i in marks.size() + 1:
		var m: Mark = marks[i] if i < marks.size() else null
		if m == null or m.gap:
			_flush(ci, run, fresh, width)
			run = PackedVector2Array()
			fresh = PackedFloat32Array()
			width = 0.0
			continue
		run.append(m.pos + offset)
		fresh.append(clampf(1.0 - (time - m.born) / life, 0.0, 1.0))
		width = maxf(width, m.w)


func _flush(ci: CanvasItem, run: PackedVector2Array, fresh: PackedFloat32Array, width: float) -> void:
	if run.size() < 2 or width <= 0.0:
		return
	# Путь для свежести реже отметок: вершин контура сотни, сверять каждую с каждой отметкой дорого.
	var path := PackedVector2Array([run[0]])
	var path_k := PackedFloat32Array([fresh[0]])
	for i in range(1, run.size()):
		if i == run.size() - 1 or run[i].distance_to(path[path.size() - 1]) >= FRESH_STEP:
			path.append(run[i])
			path_k.append(fresh[i])
	for poly in Geometry2D.offset_polyline(run, width / 2.0, Geometry2D.JOIN_ROUND, Geometry2D.END_ROUND):
		# Дыра (путь замкнулся в петлю) остаётся залитой: петля в следе редкость.
		if Geometry2D.is_polygon_clockwise(poly) or poly.size() < 3:
			continue
		var tris := Geometry2D.triangulate_polygon(poly)
		if tris.is_empty():
			continue
		var cols := PackedColorArray()
		for p in poly:
			cols.append(Color(color, alpha * _freshness(p, path, path_k)))
		RenderingServer.canvas_item_add_triangle_array(ci.get_canvas_item(), tris, poly, cols)


## Свежесть точки контура: по ближайшему отрезку пути, между его концами линейно; на нахлёсте
## пути берётся свежий.
static func _freshness(p: Vector2, path: PackedVector2Array, path_k: PackedFloat32Array) -> float:
	var best := INF
	var k := 0.0
	for i in range(1, path.size()):
		var a := path[i - 1]
		var ab := path[i] - a
		var len2 := ab.length_squared()
		var u := clampf((p - a).dot(ab) / len2, 0.0, 1.0) if len2 > 0.0 else 0.0
		var d := p.distance_squared_to(a + ab * u)
		var ki := lerpf(path_k[i - 1], path_k[i], u)
		if d < best - 1.0 or (d < best + 1.0 and ki > k):
			best = minf(d, best)
			k = ki
	return k
