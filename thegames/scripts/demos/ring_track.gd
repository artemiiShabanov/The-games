class_name RingTrack
extends RefCounted
## Трасса демки гонки × low poly «кольцо с дрифтом» (#113, спека `docs/specs/demos.md`):
## замкнутая извилистая лента. Осевая задана точками через равный шаг: место, высота, курс,
## кривизна. Положение на трассе это `s` метров от старта по ходу и `d` метров вбок от оси
## (плюс вправо по ходу). Вдоль трассы размечены участки без бортов над водой, пятна грязи на
## внутренней стороне поворотов, полосы попутного ветра и трамплин с промоиной. Строится
## `RingTrackGen` из сида записи.

class Mud:
	## От `s0` до `s1`, у борта `side` (1 правый), шириной `width` от него.
	var s0 := 0.0
	var s1 := 0.0
	var side := 1.0
	var width := 3.0


class Wind:
	## Полоса от `s0` до `s1` с серединой `d` и половиной ширины `half`.
	var s0 := 0.0
	var s1 := 0.0
	var d := 0.0
	var half := 1.3


var step := 2.0
var half_width := 4.5
## Точки оси: x и z, высота, курс как `rotation.y`, кривизна (плюс поворот влево), 1/м.
var points := PackedVector2Array()
var heights := PackedFloat32Array()
var yaws := PackedFloat32Array()
var curves := PackedFloat32Array()
var length := 1.0
## Участки без бортов: от и до, метры от старта.
var open: Array[Vector2] = []
var muds: Array[Mud] = []
var winds: Array[Wind] = []
## Трамплин: где кончается разбег и начинается промоина, её длина, длина разбега.
var ramp_s := 0.0
var ramp_gap := 8.0
var ramp_run := 6.0


func count() -> int:
	return points.size()


func loop(s: float) -> float:
	return fposmod(s, length)


## Кратчайшая разница `b − a` по кругу.
func delta(a: float, b: float) -> float:
	return fposmod(b - a + length / 2.0, length) - length / 2.0


func _index(s: float) -> float:
	return loop(s) / step


## Точка оси на расстоянии `s`.
func center(s: float) -> Vector2:
	var f := _index(s)
	var i := int(f) % count()
	return points[i].lerp(points[(i + 1) % count()], f - int(f))


func height(s: float) -> float:
	var f := _index(s)
	var i := int(f) % count()
	return lerpf(heights[i], heights[(i + 1) % count()], f - int(f))


func yaw(s: float) -> float:
	var f := _index(s)
	var i := int(f) % count()
	return lerp_angle(yaws[i], yaws[(i + 1) % count()], f - int(f))


func curve(s: float) -> float:
	return curves[int(roundf(_index(s))) % count()]


## Самая крутая кривизна (по модулю) на отрезке от `s` на `ahead` метров вперёд.
func curve_ahead(s: float, ahead: float) -> float:
	var worst := 0.0
	var k := 0.0
	while k <= ahead:
		worst = maxf(worst, absf(curve(s + k)))
		k += step
	return worst


func forward(s: float) -> Vector2:
	var a := yaw(s)
	return Vector2(-sin(a), -cos(a))


func right(s: float) -> Vector2:
	var a := yaw(s)
	return Vector2(cos(a), -sin(a))


## Точка мира в `s` и `d`.
func at(s: float, d: float) -> Vector2:
	return center(s) + right(s) * d


func world(s: float, d: float, up := 0.0) -> Vector3:
	var p := at(s, d)
	return Vector3(p.x, height(s) + up, p.y)


## Положение точки на трассе: `x` это `s`, `y` это `d`. `hint` это прошлое `s` этой шлюпки:
## ближайшая точка оси ищется рядом с ним.
func locate(p: Vector2, hint: float) -> Vector2:
	var n := count()
	var base := int(roundf(_index(hint)))
	var best := base
	var best_d := INF
	for k in range(-8, 13):
		var i := posmod(base + k, n)
		var dist := points[i].distance_squared_to(p)
		if dist < best_d:
			best_d = dist
			best = i
	var s := best * step
	var along := (p - points[best]).dot(forward(s))
	s = loop(s + along)
	return Vector2(s, (p - center(s)).dot(right(s)))


static func _inside(s: float, s0: float, s1: float, length_: float) -> bool:
	return fposmod(s - s0, length_) <= fposmod(s1 - s0, length_)


## На этом месте трассы нет бортов.
func is_open(s: float) -> bool:
	for r in open:
		if _inside(loop(s), r.x, r.y, length):
			return true
	return false


## Промоина после трамплина.
func in_gap(s: float) -> bool:
	return _inside(loop(s), ramp_s, ramp_s + ramp_gap, length)


func in_mud(s: float, d: float) -> bool:
	for m in muds:
		if _inside(loop(s), m.s0, m.s1, length) and d * m.side >= half_width - m.width:
			return true
	return false


func in_wind(s: float, d: float) -> bool:
	for w in winds:
		if _inside(loop(s), w.s0, w.s1, length) and absf(d - w.d) <= w.half:
			return true
	return false


## Мест, где игрок рискует временем: участки без бортов, пятна грязи, трамплин.
func risks() -> int:
	return open.size() + muds.size() + 1


## Подпись для сравнения двух трасс: детерминизм генератора.
func signature() -> String:
	var parts: PackedStringArray = ["%d|%.2f|%.2f" % [count(), length, ramp_s]]
	for i in range(0, count(), 7):
		parts.append("%.2f,%.2f,%.2f" % [points[i].x, points[i].y, heights[i]])
	for r in open:
		parts.append("o%.1f,%.1f" % [r.x, r.y])
	for m in muds:
		parts.append("m%.1f,%.1f,%.0f" % [m.s0, m.s1, m.side])
	for w in winds:
		parts.append("w%.1f,%.1f,%.1f" % [w.s0, w.s1, w.d])
	return "|".join(parts)
