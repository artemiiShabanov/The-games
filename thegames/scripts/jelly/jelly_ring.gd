class_name JellyRing
extends Control
## Прототип мармелада (ветка proto/jelly): рамка фокуса упругим контуром. Хозяин ставит
## `target` (прямоугольник объекта в своих координатах) мгновенно, без твина; точки контура
## сами перетекают к нему на пружинах. Передние по ходу точки жёстче задних, поэтому при
## переходе рамка вытягивается каплей и догоняет себя с качанием. Рисуется по STYLE: снаружи
## объекта с зазором `FOCUS_OFFSET`, толщина `FOCUS_WIDTH`.

const COUNT := 120

var target := Rect2()
var radius := float(Style.R_CARD)
var points := PackedVector2Array()
var velocities := PackedVector2Array()
var _ready_points := false


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	points.resize(COUNT)
	velocities.resize(COUNT)


## Сразу на месте, без перетекания (первое появление).
func snap() -> void:
	var goal := _perimeter()
	for i in COUNT:
		points[i] = goal[i]
		velocities[i] = Vector2.ZERO
	_ready_points = true
	queue_redraw()


## Контур по средней линии рамки: скруглённый прямоугольник, точки по длине дуги.
func _perimeter() -> PackedVector2Array:
	var off := Style.FOCUS_OFFSET + Style.FOCUS_WIDTH / 2.0
	var r := target.grow(off)
	var rad := minf(radius + off, minf(r.size.x, r.size.y) / 2.0)
	var straight_x := r.size.x - 2.0 * rad
	var straight_y := r.size.y - 2.0 * rad
	var arc := PI / 2.0 * rad
	var total := 2.0 * (straight_x + straight_y) + 4.0 * arc
	var out := PackedVector2Array()
	out.resize(COUNT)
	for i in COUNT:
		var s := total * i / COUNT
		out[i] = _along(r, rad, straight_x, straight_y, arc, s)
	return out


func _along(r: Rect2, rad: float, sx: float, sy: float, arc: float, s: float) -> Vector2:
	# Обход по часовой от верхнего левого конца верхней стороны.
	var segs := [sx, arc, sy, arc, sx, arc, sy, arc]
	var k := 0
	while k < 8 and s > segs[k]:
		s -= segs[k]
		k += 1
	k = mini(k, 7)
	var tl := r.position
	match k:
		0: return tl + Vector2(rad + s, 0.0)
		1: return tl + Vector2(r.size.x - rad, rad) + Vector2(sin(s / rad), -cos(s / rad)) * rad
		2: return tl + Vector2(r.size.x, rad + s)
		3: return tl + Vector2(r.size.x - rad, r.size.y - rad) + Vector2(cos(s / rad), sin(s / rad)) * rad
		4: return tl + Vector2(r.size.x - rad - s, r.size.y)
		5: return tl + Vector2(rad, r.size.y - rad) + Vector2(-sin(s / rad), cos(s / rad)) * rad
		6: return tl + Vector2(0.0, r.size.y - rad - s)
	return tl + Vector2(rad, rad) + Vector2(-cos(s / rad), -sin(s / rad)) * rad


func _process(delta: float) -> void:
	if not visible or delta <= 0.0:
		return
	if not _ready_points:
		snap()
	var tu := Jelly.tuning()
	var goal := _perimeter()
	var centroid := Vector2.ZERO
	for p in points:
		centroid += p
	centroid /= COUNT
	var to := target.get_center() - centroid
	var dir := to.normalized() if to.length() > 2.0 else Vector2.ZERO
	var k := tu.ui_stiffness * 5.0
	var d := tu.ui_damping * 3.0
	var subs := maxi(1, ceili(delta / SoftBlob.SUBSTEP))
	var dt := delta / subs
	for step in subs:
		for i in COUNT:
			var p := points[i]
			var prev := points[(i - 1 + COUNT) % COUNT]
			var next := points[(i + 1) % COUNT]
			var normal := (next - prev).orthogonal().normalized() * -1.0
			# Передние по ходу точки тянутся сильнее: рамка течёт, а не едет.
			var lead := 1.0 + 0.6 * normal.dot(dir)
			var a := (goal[i] - p) * k * lead - velocities[i] * d
			a += ((prev + next) * 0.5 - p) * tu.blob_neighbor * 2.0
			velocities[i] += a * dt
		for i in COUNT:
			points[i] += velocities[i] * dt
	queue_redraw()


func _draw() -> void:
	if not _ready_points:
		return
	var closed := PackedVector2Array(points)
	closed.append(points[0])
	draw_polyline(closed, Style.FOCUS, Style.FOCUS_WIDTH, true)
