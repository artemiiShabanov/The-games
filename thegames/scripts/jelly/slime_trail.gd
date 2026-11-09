class_name SlimeTrail
extends RefCounted
## Склизкий след мармеладной фигуры (STYLE «Мармелад»): полоса во всю ширину протащенной фигуры
## со скруглёнными концами, полупрозрачная, гаснет и сужается за `life`. Хозяин каждый кадр
## зовёт `add(pos, width)` центром фигуры, пока она тащится, `cut()` при прыжке или телепорте,
## `step(delta)` и рисует `draw(ci, offset)` под фигурой. Координаты хозяина (мира или поля).

class Mark:
	var pos := Vector2.ZERO
	var w := 0.0
	var born := 0.0
	var gap := false

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


## Каждая непрерывная полоса одной линией шириной фигуры: прозрачность гаснет от свежего конца
## к старому. Одним вызовом, а не кружками: полупрозрачные кружки внахлёст слились бы в пятно.
## Свежий конец скруглён полукругом без нахлёста.
func draw(ci: CanvasItem, offset := Vector2.ZERO) -> void:
	var run := PackedVector2Array()
	var cols := PackedColorArray()
	var width := 0.0
	for i in marks.size() + 1:
		var m: Mark = marks[i] if i < marks.size() else null
		if m == null or m.gap:
			_flush(ci, run, cols, width)
			run = PackedVector2Array()
			cols = PackedColorArray()
			width = 0.0
			continue
		var k := clampf(1.0 - (time - m.born) / life, 0.0, 1.0)
		run.append(m.pos + offset)
		cols.append(Color(color, alpha * k))
		width = maxf(width, m.w)


func _flush(ci: CanvasItem, run: PackedVector2Array, cols: PackedColorArray, width: float) -> void:
	if run.size() < 2:
		return
	ci.draw_polyline_colors(run, cols, width, true)
	# Полукруг на свежем конце, повёрнутый по ходу: скругление без нахлёста с линией.
	var head := run[run.size() - 1]
	var dir := (head - run[run.size() - 2]).normalized()
	if dir == Vector2.ZERO:
		return
	var cap := PackedVector2Array([head])
	var a0 := dir.angle() - PI / 2.0
	for j in 13:
		cap.append(head + Vector2.from_angle(a0 + PI * j / 12.0) * width / 2.0)
	ci.draw_colored_polygon(cap, cols[cols.size() - 1])
