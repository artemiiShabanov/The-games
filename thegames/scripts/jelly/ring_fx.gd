class_name RingFx
extends RefCounted
## Круги по поверхности жидкости: расходятся от точки и гаснут. Всплытие, утопление, шлепок.

class Ring:
	var pos := Vector2.ZERO
	var born := 0.0
	var from_r := 0.0
	var to_r := 100.0
	var life := 0.8
	var color := Color.BLACK

var rings: Array[Ring] = []
var time := 0.0


## Круг из `pos` от радиуса `from_r` до `to_r` за `life`; `count` кругов друг за другом.
func add(pos: Vector2, from_r: float, to_r: float, color: Color, count := 1, life := 0.8) -> void:
	for i in count:
		var r := Ring.new()
		r.pos = pos
		r.born = time + i * 0.14
		r.from_r = from_r
		r.to_r = to_r * (1.0 - i * 0.18)
		r.life = life
		r.color = color
		rings.append(r)


func step(delta: float) -> void:
	time += delta
	var keep: Array[Ring] = []
	for r in rings:
		if time - r.born < r.life:
			keep.append(r)
	rings = keep


func draw(ci: CanvasItem) -> void:
	for r in rings:
		var p := (time - r.born) / r.life
		if p < 0.0:
			continue
		var e := 1.0 - (1.0 - p) * (1.0 - p)
		ci.draw_arc(r.pos, lerpf(r.from_r, r.to_r, e), 0.0, TAU, 64, Color(r.color, r.color.a * (1.0 - p)), 3.0 * (1.0 - p * 0.5), true)
