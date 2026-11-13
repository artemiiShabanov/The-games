class_name HookLevel
extends RefCounted
## Уровень демки платформер × «продвинутые» «крюк-кошка» (#121, спека `docs/specs/demos.md`):
## круглые островки-скалы над водой, между ними пропасти с кольцами на реях. Путь идёт ломаной:
## на каждом островке он поворачивает. Правила считают героя в координатах пути: `s` метров
## вдоль ломаной, `u` вбок, `y` высота; полёт и качание идут в вертикальной плоскости участка.
## Кольцо может ходить вверх-вниз по формуле от времени. Строится `HookLevelGen` из сида.

class Islet:
	## Середина на пути, радиус, высота верха, место в мире и курс пути после островка.
	var s := 0.0
	var radius := 2.6
	var y := 0.0
	var pos := Vector3.ZERO
	var yaw := 0.0


class Ring:
	## Место на пути, высота в покое, размах и период хода вверх-вниз (0: стоит), сдвиг фазы,
	## номер пропасти.
	var s := 0.0
	var y := 5.0
	var amp := 0.0
	var period := 2.6
	var phase := 0.0
	var gap := 0


var islets: Array[Islet] = []
var rings: Array[Ring] = []


func ring_y(i: int, time: float) -> float:
	var r := rings[i]
	return r.y + (r.amp * sin(TAU * time / r.period + r.phase) if r.amp > 0.0 else 0.0)


func forward(index: int) -> Vector3:
	var yaw := islets[clampi(index, 0, islets.size() - 1)].yaw
	return Vector3(-sin(yaw), 0.0, -cos(yaw))


## Точка мира по координатам пути.
func world(s: float, u: float, y: float) -> Vector3:
	var i := 0
	for k in islets.size():
		if s >= islets[k].s:
			i = k
	i = mini(i, islets.size() - 1)
	var f := forward(i)
	var p := islets[i].pos + f * (s - islets[i].s) + Vector3(-f.z, 0.0, f.x) * u
	return Vector3(p.x, y, p.z)


## Курс пути в точке `s` (поворот на островке плавный в пределах его радиуса).
func yaw_at(s: float) -> float:
	var i := 0
	for k in islets.size():
		if s >= islets[k].s - islets[k].radius:
			i = k
	if i == 0:
		return islets[0].yaw
	var here := islets[i]
	var k := clampf((s - (here.s - here.radius)) / (here.radius * 2.0), 0.0, 1.0)
	return lerp_angle(islets[i - 1].yaw, here.yaw, k)


## Островок под точкой или −1.
func islet_at(s: float, u: float) -> int:
	for i in islets.size():
		var d := Vector2(s - islets[i].s, u)
		if d.length() <= islets[i].radius:
			return i
	return -1


func water_y(drop: float) -> float:
	var low := INF
	for it in islets:
		low = minf(low, it.y)
	return low - drop


func length() -> float:
	return islets[islets.size() - 1].s - islets[0].s


func gaps() -> int:
	return islets.size() - 1


func rings_of(gap: int) -> Array[int]:
	var out: Array[int] = []
	for i in rings.size():
		if rings[i].gap == gap:
			out.append(i)
	return out


func longest_chain() -> int:
	var best := 0
	for g in gaps():
		best = maxi(best, rings_of(g).size())
	return best


func moving() -> int:
	var n := 0
	for r in rings:
		n += 1 if r.amp > 0.0 else 0
	return n


func small() -> int:
	var n := 0
	for it in islets:
		n += 1 if it.radius < 1.6 else 0
	return n


## Подпись для сравнения двух уровней: детерминизм генератора.
func signature() -> String:
	var parts: PackedStringArray = []
	for it in islets:
		parts.append("i%.2f,%.2f,%.2f,%.3f" % [it.s, it.radius, it.y, it.yaw])
	for r in rings:
		parts.append("r%.2f,%.2f,%.2f,%.2f,%d" % [r.s, r.y, r.amp, r.phase, r.gap])
	return "|".join(parts)
