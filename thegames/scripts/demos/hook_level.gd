class_name HookLevel
extends RefCounted
## Уровень демки платформер × «продвинутые» «крюк-кошка» (#121, спека `docs/specs/demos.md`):
## острова над водой и пропасти между ними. Остров это кусок земли с неровным краем и плоским
## верхом (большой) или камень (маленький); на больших стоит реквизит, сквозь который не
## пройти. Пропасть бывает трёх видов: простой прыжок, уступ (стена выше прыжка, герой
## цепляется руками за край и забирается) и кольца на реях для крюка, одно или цепочкой.
## Путь поворачивает на островах. Всё в координатах мира, метры. Строится `HookLevelGen`.

enum Kind { JUMP, CLIMB, RINGS }


class Islet:
	## Середина верха в мире, средний радиус, неровность края (три волны: доля и фаза).
	var pos := Vector3.ZERO
	var radius := 6.0
	var waves := PackedFloat32Array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

	## Радиус в сторону `angle` (угол в плоскости xz от оси x).
	func radius_at(angle: float) -> float:
		return radius * (1.0 + waves[0] * sin(2.0 * angle + waves[1]) + waves[2] * sin(3.0 * angle + waves[3])
				+ waves[4] * sin(5.0 * angle + waves[5]))

	## Край в сторону единичного `dir` (x, z).
	func edge(dir: Vector2) -> float:
		return radius_at(atan2(dir.y, dir.x))

	func holds(x: float, z: float, pad := 0.0) -> bool:
		var d := Vector2(x - pos.x, z - pos.z)
		return d.length() <= radius_at(atan2(d.y, d.x)) + pad


class Ring:
	## Место в покое, размах и период хода вверх-вниз (0: стоит), сдвиг фазы, номер пропасти.
	var pos := Vector3.ZERO
	var amp := 0.0
	var period := 2.6
	var phase := 0.0
	var gap := 0


class Prop:
	## Вещь на острове: имя модели, место основания, радиус и высота столба коллизии, поворот.
	var name := "barrel"
	var pos := Vector3.ZERO
	var radius := 0.5
	var height := 1.0
	var yaw := 0.0
	var islet := 0


class Gap:
	## Пропасть от острова `index` к следующему: вид, точка отрыва на краю, точка края
	## следующего острова, единичный курс (x, z).
	var kind := Kind.JUMP
	var a := Vector3.ZERO
	var b := Vector3.ZERO
	var dir := Vector2(0.0, -1.0)

	func length() -> float:
		return Vector2(b.x - a.x, b.z - a.z).length()


var islets: Array[Islet] = []
var gaps: Array[Gap] = []
var rings: Array[Ring] = []
var props: Array[Prop] = []


func ring_pos(i: int, time: float) -> Vector3:
	var r := rings[i]
	return r.pos + Vector3(0.0, r.amp * sin(TAU * time / r.period + r.phase) if r.amp > 0.0 else 0.0, 0.0)


## Остров под точкой или −1.
func islet_at(x: float, z: float, pad := 0.0) -> int:
	for i in islets.size():
		if islets[i].holds(x, z, pad):
			return i
	return -1


func water_y(drop: float) -> float:
	var low := INF
	for it in islets:
		low = minf(low, it.pos.y)
	return low - drop


## Длина пути по серединам островов.
func length() -> float:
	var sum := 0.0
	for i in range(1, islets.size()):
		sum += Vector2(islets[i].pos.x - islets[i - 1].pos.x, islets[i].pos.z - islets[i - 1].pos.z).length()
	return sum


func rings_of(gap: int) -> Array[int]:
	var out: Array[int] = []
	for i in rings.size():
		if rings[i].gap == gap:
			out.append(i)
	return out


func count(kind: Kind) -> int:
	var n := 0
	for g in gaps:
		n += 1 if g.kind == kind else 0
	return n


func longest_chain() -> int:
	var best := 0
	for g in gaps.size():
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
		n += 1 if it.radius < 2.2 else 0
	return n


## Подпись для сравнения двух уровней: детерминизм генератора.
func signature() -> String:
	var parts: PackedStringArray = []
	for it in islets:
		parts.append("i%.2f,%.2f,%.2f,%.2f" % [it.pos.x, it.pos.y, it.pos.z, it.radius])
	for g in gaps:
		parts.append("g%d" % g.kind)
	for r in rings:
		parts.append("r%.2f,%.2f,%.2f,%.2f,%d" % [r.pos.x, r.pos.y, r.pos.z, r.amp, r.gap])
	for p in props:
		parts.append("p%s,%.2f,%.2f" % [p.name, p.pos.x, p.pos.z])
	return "|".join(parts)
