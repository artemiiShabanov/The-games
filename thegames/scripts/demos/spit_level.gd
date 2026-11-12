class_name SpitLevel
extends RefCounted
## Уровень демки платформер × low poly «тропа вглубь экрана» (#112, спека
## `docs/specs/demos.md`): песчаная коса из кусков, уходящая от камеры в −Z. Кусок это
## прямоугольник тропы с наклоном по длине; между кусками бывают ямы с водой, сбоку от тропы
## тоже вода. На кусках ряды ящиков и скелеты, что ходят поперёк; дублоны на тропе и дугой над
## ямами. Строится `SpitLevelGen` из сида записи; здесь только раскладка и геометрия для правил
## (`SpitSim`) и для демки.

enum Kind { START, PLAIN, BRIDGE, GUARD, CRATES, END }

class Piece:
	var kind := Kind.PLAIN
	## Яма перед куском: расстояние от дальнего края предыдущего.
	var gap := 0.0
	## Ближний край по z (больше) и длина в сторону −Z, середина по x и ширина.
	var z0 := 0.0
	var length := 10
	var x := 0.0
	var width := 5
	## Высота тропы у ближнего и у дальнего края.
	var h0 := 0.0
	var h1 := 0.0

	func z1() -> float:
		return z0 - length

	func left() -> float:
		return x - width / 2.0

	func right() -> float:
		return x + width / 2.0

	func height(z: float) -> float:
		return lerpf(h0, h1, clampf((z0 - z) / length, 0.0, 1.0))


class Guard:
	## Кусок, линия по z, на сколько ходит в стороны от середины куска, скорость, доля периода.
	var piece := 0
	var z := 0.0
	var reach := 2.0
	var speed := 1.6
	var phase := 0.0


var pieces: Array[Piece] = []
var guards: Array[Guard] = []
## Ящики: середина дна (стоят на тропе).
var crates: Array[Vector3] = []
## Дублоны: середина в воздухе.
var coins: Array[Vector3] = []
var start := Vector3.ZERO


## Кусок под координатой z или −1 (яма, до старта, за финишем).
func piece_at(z: float) -> int:
	for i in pieces.size():
		if z <= pieces[i].z0 and z >= pieces[i].z1():
			return i
	return -1


## Высота тропы под точкой или −INF, если под ней вода.
func ground_at(x: float, z: float) -> float:
	var i := piece_at(z)
	if i < 0 or x < pieces[i].left() or x > pieces[i].right():
		return -INF
	return pieces[i].height(z)


## Где скелет `i` в момент `time` и куда идёт (−1 влево, 1 вправо): ходит туда-сюда ровно.
func guard_x(i: int, time: float) -> float:
	var g := guards[i]
	var u := fposmod(time * g.speed / (4.0 * g.reach) + g.phase, 1.0)
	return pieces[g.piece].x + g.reach * (4.0 * absf(u - 0.5) - 1.0)


func guard_dir(i: int, time: float) -> float:
	var g := guards[i]
	return -1.0 if fposmod(time * g.speed / (4.0 * g.reach) + g.phase, 1.0) < 0.5 else 1.0


func finish_piece() -> Piece:
	return pieces[pieces.size() - 1]


func length() -> float:
	return -finish_piece().z1()


func gaps() -> int:
	var n := 0
	for p in pieces:
		if p.gap > 0.0:
			n += 1
	return n


## Подпись для сравнения двух уровней: детерминизм генератора.
func signature() -> String:
	var parts: PackedStringArray = []
	for p in pieces:
		parts.append("p%d,%.2f,%.2f,%d,%.2f,%d,%.2f,%.2f" % [p.kind, p.gap, p.z0, p.length, p.x, p.width, p.h0, p.h1])
	for g in guards:
		parts.append("g%d,%.2f,%.2f,%.2f,%.2f" % [g.piece, g.z, g.reach, g.speed, g.phase])
	for c in crates:
		parts.append("b%.2f,%.2f,%.2f" % [c.x, c.y, c.z])
	for c in coins:
		parts.append("c%.2f,%.2f,%.2f" % [c.x, c.y, c.z])
	return "|".join(parts)
