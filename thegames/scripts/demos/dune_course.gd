class_name DuneCourse
extends RefCounted
## Склон демки спорт × «продвинутые» «спуск по дюне» (#124, спека `docs/specs/demos.md`).
## Положение на склоне это `s` метров вниз по линии склона и `x` метров вбок от неё (плюс
## вправо по ходу). Линия склона плавно изгибается, уклон меняется волнами. На склоне стоят
## ворота из двух флагов, трамплины и препятствия (камни ниже роста, пальмы выше). Строится
## `DuneCourseGen` из сида записи.

class Gate:
	var s := 0.0
	var x := 0.0
	var half := 4.0


class Ramp:
	var s := 0.0
	var x := 0.0
	var width := 4.0


class Rock:
	## Препятствие: место, радиус, высокое ли (пальма: не перепрыгнуть).
	var s := 0.0
	var x := 0.0
	var radius := 0.9
	var tall := false


var step := 4.0
var length := 1000.0
var half_width := 15.0
## Высота и сдвиг линии склона вбок в точках через `step`.
var heights := PackedFloat32Array()
var sways := PackedFloat32Array()
var gates: Array[Gate] = []
var ramps: Array[Ramp] = []
var rocks: Array[Rock] = []


func _lerp(values: PackedFloat32Array, s: float) -> float:
	var f := clampf(s, 0.0, length + 60.0) / step
	var i := mini(int(f), values.size() - 2)
	return lerpf(values[i], values[i + 1], f - i)


## Высота склона в `s` на линии склона и с бортами по краям (`x` от линии).
func height(s: float, x := 0.0) -> float:
	var over := maxf(absf(x) - half_width, 0.0)
	return _lerp(heights, s) + over * over * 0.045


func sway(s: float) -> float:
	return _lerp(sways, s)


## Уклон в `s`: тангенс (плюс вниз по ходу).
func slope(s: float) -> float:
	return (_lerp(heights, s - step) - _lerp(heights, s + step)) / (2.0 * step)


## Точка мира: склон идёт в сторону −z.
func world(s: float, x: float, up := 0.0) -> Vector3:
	return Vector3(sway(s) + x, height(s, x) + up, -s)


## Курс линии склона в мире как `rotation.y`.
func yaw(s: float) -> float:
	return atan2(-(sway(s + step) - sway(s - step)), 2.0 * step)


func drop() -> float:
	return heights[0] - _lerp(heights, length)


func tall_rocks() -> int:
	var n := 0
	for r in rocks:
		n += 1 if r.tall else 0
	return n


func signature() -> String:
	var parts: PackedStringArray = ["%.1f" % drop()]
	for g in gates:
		parts.append("g%.1f,%.1f,%.1f" % [g.s, g.x, g.half])
	for r in ramps:
		parts.append("t%.1f,%.1f" % [r.s, r.x])
	for r in rocks:
		parts.append("r%.1f,%.1f" % [r.s, r.x])
	return "|".join(parts)
