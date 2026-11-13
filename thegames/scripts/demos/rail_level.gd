class_name RailLevel
extends RefCounted
## Маршрут демки шутер × low poly «рельсовый тир» (#114, спека `docs/specs/demos.md`): камера
## едет по острову от остановки к остановке, на каждой перед ней стоят укрытия (бочки и ящики),
## из-за которых группами высовываются враги. Земля это дюны по формуле (`height`), путь идёт с
## поворотами и перепадами высоты. Враг знает, где сидит (`hide`) и куда высовывается (`out`);
## бегуны выбегают сбоку, пока камера едет. Строится `RailLevelGen` из сида записи.

enum Kind { SAILOR, THROWER, CAPTAIN, HOSTAGE, RUNNER }
enum Shape { BARREL, CRATE }

class Stop:
	## Глаза камеры, куда она смотрит (курс и наклон, радианы), сколько секунд ехать сюда с
	## прошлой остановки, групп врагов.
	var pos := Vector3.ZERO
	var yaw := 0.0
	var pitch := 0.0
	var travel := 0.0
	var groups := 0


class Cover:
	## Низ посередине, половина ширины и высота, курс (лицом к камере остановки).
	var stop := 0
	var shape := Shape.BARREL
	var pos := Vector3.ZERO
	var half := 0.5
	var height := 1.2
	var yaw := 0.0

	func box() -> AABB:
		return AABB(pos - Vector3(half, 0.0, half), Vector3(half * 2.0, height, half * 2.0))


class Foe:
	## Остановка и группа (бегун: остановка, к которой едет камера, группа −1), задержка от
	## начала группы (у бегуна доля переезда), укрытие или −1, ступни в укрытии и на виду,
	## сколько секунд целится (пленный: сколько стоит).
	var kind := Kind.SAILOR
	var stop := 0
	var group := 0
	var delay := 0.0
	var cover := -1
	var hide := Vector3.ZERO
	var out := Vector3.ZERO
	var aim := 2.5

	func hostile() -> bool:
		return kind != Kind.HOSTAGE


class Keg:
	var stop := 0
	var pos := Vector3.ZERO
	var radius := 3.0


## Остановки с боем и последняя точка маршрута (финиш, без врагов).
var stops: Array[Stop] = []
var covers: Array[Cover] = []
var foes: Array[Foe] = []
var kegs: Array[Keg] = []
## Дюны: высоты и частоты двух волн, сдвиги, подъём острова и берег.
var dune := PackedFloat32Array([0.9, 0.5, 0.24, 0.31, 0.0, 0.0, 0.0])
var island := 1.3
var shore_from := 17.0
var shore_slope := 0.3
var eye := 1.6


## Высота земли в точке; вода на нуле. Далеко от пути берег уходит под воду.
func height(x: float, z: float) -> float:
	var h := island + dune[0] * sin(x * dune[2] + dune[4]) * cos(z * dune[2] * 0.83 + dune[5]) \
			+ dune[1] * sin((x + z) * dune[3] + dune[6])
	return h - maxf(path_distance(x, z) - shore_from, 0.0) * shore_slope


func ground(p: Vector3) -> Vector3:
	return Vector3(p.x, height(p.x, p.z), p.z)


## Расстояние от точки до пути камеры по земле.
func path_distance(x: float, z: float) -> float:
	var p := Vector2(x, z)
	var best := INF
	for i in range(1, stops.size()):
		var a := Vector2(stops[i - 1].pos.x, stops[i - 1].pos.z)
		var b := Vector2(stops[i].pos.x, stops[i].pos.z)
		best = minf(best, p.distance_to(Geometry2D.get_closest_point_to_segment(p, a, b)))
	return best


## Камера в переезде к остановке `index`, `k` 0..1: положение по земле на высоте глаз, взгляд
## плавно доворачивается.
func pose_pos(index: int, k: float) -> Vector3:
	if index <= 0:
		return stops[0].pos
	var e := smoothstep(0.0, 1.0, clampf(k, 0.0, 1.0))
	var p := stops[index - 1].pos.lerp(stops[index].pos, e)
	return Vector3(p.x, height(p.x, p.z) + eye, p.z)


func pose_look(index: int, k: float) -> Vector2:
	if index <= 0:
		return Vector2(stops[0].yaw, stops[0].pitch)
	var e := smoothstep(0.0, 1.0, clampf(k, 0.0, 1.0))
	return Vector2(lerp_angle(stops[index - 1].yaw, stops[index].yaw, e), lerpf(stops[index - 1].pitch, stops[index].pitch, e))


static func basis_of(look: Vector2) -> Basis:
	return Basis.from_euler(Vector3(look.y, look.x, 0.0))


## Точка мира в кадре камеры: x и y от −1 до 1 (y вниз), z расстояние вперёд (минус: за спиной).
static func project(p: Vector3, cam: Vector3, look: Vector2, tan_half: float, aspect: float) -> Vector3:
	var local := basis_of(look).inverse() * (p - cam)
	var depth := -local.z
	if depth <= 0.01:
		return Vector3(0.0, 0.0, -1.0)
	return Vector3(local.x / depth / (tan_half * aspect), -local.y / depth / tan_half, depth)


## Луч из камеры через точку кадра.
static func ray(aim: Vector2, look: Vector2, tan_half: float, aspect: float) -> Vector3:
	return (basis_of(look) * Vector3(aim.x * tan_half * aspect, -aim.y * tan_half, -1.0)).normalized()


## Где луч входит в шар; −1, если мимо.
static func hit_sphere(from: Vector3, dir: Vector3, center: Vector3, radius: float) -> float:
	var to := center - from
	var along := to.dot(dir)
	if along <= 0.0:
		return -1.0
	var off := to.length_squared() - along * along
	if off > radius * radius:
		return -1.0
	return along - sqrt(radius * radius - off)


## Где луч входит в ящик; −1, если мимо.
static func hit_box(from: Vector3, dir: Vector3, box: AABB) -> float:
	var near := 0.0
	var far := INF
	for axis in 3:
		if absf(dir[axis]) < 0.00001:
			if from[axis] < box.position[axis] or from[axis] > box.end[axis]:
				return -1.0
			continue
		var a := (box.position[axis] - from[axis]) / dir[axis]
		var b := (box.end[axis] - from[axis]) / dir[axis]
		near = maxf(near, minf(a, b))
		far = minf(far, maxf(a, b))
	return near if near <= far else -1.0


## Видно ли точку из камеры: не закрыта укрытиями (кроме `skip`) и дюной.
func sees(cam: Vector3, point: Vector3, skip := -1) -> bool:
	var to := point - cam
	var dist := to.length()
	var dir := to / dist
	for i in covers.size():
		if i == skip:
			continue
		var t := hit_box(cam, dir, covers[i].box())
		if t >= 0.0 and t < dist - 0.05:
			return false
	for k in range(1, 10):
		var p := cam + to * (k / 10.0)
		if height(p.x, p.z) > p.y:
			return false
	return true


func foes_of(stop: int, group: int) -> Array[int]:
	var out: Array[int] = []
	for i in foes.size():
		if foes[i].stop == stop and foes[i].group == group:
			out.append(i)
	return out


func count(kind: Kind) -> int:
	var n := 0
	for f in foes:
		n += 1 if f.kind == kind else 0
	return n


func hostiles() -> int:
	return foes.size() - count(Kind.HOSTAGE)


## Длина пути камеры.
func length() -> float:
	var total := 0.0
	for i in range(1, stops.size()):
		total += stops[i - 1].pos.distance_to(stops[i].pos)
	return total


## Подпись для сравнения двух маршрутов: детерминизм генератора.
func signature() -> String:
	var parts: PackedStringArray = []
	for s in stops:
		parts.append("s%s,%.3f,%.3f,%.2f,%d" % [s.pos, s.yaw, s.pitch, s.travel, s.groups])
	for c in covers:
		parts.append("c%d,%d,%s" % [c.stop, c.shape, c.pos])
	for f in foes:
		parts.append("f%d,%d,%d,%.2f,%d,%s,%s,%.2f" % [f.kind, f.stop, f.group, f.delay, f.cover, f.hide, f.out, f.aim])
	for k in kegs:
		parts.append("k%d,%s" % [k.stop, k.pos])
	return "|".join(parts)
