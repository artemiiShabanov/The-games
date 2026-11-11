class_name TowerLevel
extends RefCounted
## Уровень демки платформер × вектор «этажи с дырами» (#90, спека `docs/specs/demos.md`): один
## экран шириной `width`, замкнутый по краям. Этаж 0 это земля, над ней `floors` линий; линия
## `n` служит полом этажа `n` и потолком этажа `n − 1`. По линиям едут дыры, по этажам ходят
## враги, на этажах лежат монеты, флаг на верхнем. Строится `TowerLevelGen` из сида записи;
## здесь только раскладка на момент 0, движение считает демка.

class Hole:
	## Линия 1..floors.
	var line := 1
	## Центр в момент 0 и скорость со знаком, пикселей в секунду.
	var x := 0.0
	var speed := 0.0
	var width := 160.0


class Enemy:
	## Этаж 0..floors − 1: на верхнем врагов нет.
	var level := 0
	var x := 0.0
	var speed := 0.0


var width := 1664.0
var floors := 6
var holes: Array[Hole] = []
var enemies: Array[Enemy] = []
## Монеты: x и этаж.
var coins: Array[Vector2] = []
var start_x := 0.0
var flag_x := 0.0


func holes_of(line: int) -> Array[Hole]:
	var out: Array[Hole] = []
	for h in holes:
		if h.line == line:
			out.append(h)
	return out


func enemies_of(level: int) -> Array[Enemy]:
	var out: Array[Enemy] = []
	for e in enemies:
		if e.level == level:
			out.append(e)
	return out


## Кратчайшая разница `b − a` по кругу шириной `width_`: от −width/2 до width/2.
static func wrap_delta(a: float, b: float, width_: float) -> float:
	return fposmod(b - a + width_ / 2.0, width_) - width_ / 2.0


## Подпись для сравнения двух уровней: детерминизм генератора.
func signature() -> String:
	var parts: PackedStringArray = ["%d|%.2f|%.2f|%.2f" % [floors, width, start_x, flag_x]]
	for h in holes:
		parts.append("h%d,%.2f,%.2f,%.2f" % [h.line, h.x, h.speed, h.width])
	for e in enemies:
		parts.append("e%d,%.2f,%.2f" % [e.level, e.x, e.speed])
	for c in coins:
		parts.append("c%.2f,%d" % [c.x, int(c.y)])
	return "|".join(parts)
