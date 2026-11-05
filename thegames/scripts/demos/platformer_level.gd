class_name PlatformerLevel
extends RefCounted
## Уровень платформера в тайлах, спека `docs/specs/demos.md`. Строится `PlatformerLevelGen`
## из сида записи игры. Координаты: x колонка слева направо, y ряд снизу вверх (0 у нижнего
## края). `columns[x]` высота земли в рядах, 0 это яма.

class Enemy:
	var x := 0
	var y := 0
	var patrol_from := 0
	var patrol_to := 0

var width := 0
var height := 16
var columns: PackedInt32Array = []
## Платформы: position.x колонка начала, position.y ряд платформы, size.x длина.
var platforms: Array[Rect2i] = []
var enemies: Array[Enemy] = []
var coins: Array[Vector2i] = []
var spawn := Vector2i.ZERO
var checkpoint := Vector2i.ZERO
var flag := Vector2i.ZERO


func ground_top(x: int) -> int:
	return columns[x] if x >= 0 and x < width else 0


func is_pit(x: int) -> bool:
	return ground_top(x) <= 0


## Поверхности, на которых можно стоять в колонке: земля и платформы, ряд стояния.
func surfaces_at(x: int) -> Array[int]:
	var out: Array[int] = []
	if not is_pit(x):
		out.append(ground_top(x))
	for p in platforms:
		if x >= p.position.x and x < p.position.x + p.size.x:
			out.append(p.position.y + 1)
	return out


func pit_count() -> int:
	var n := 0
	var x := 0
	while x < width:
		if is_pit(x):
			n += 1
			while x < width and is_pit(x):
				x += 1
		else:
			x += 1
	return n


## Подпись для сравнения двух уровней: детерминизм генератора.
func signature() -> String:
	var parts: PackedStringArray = [str(columns), str(platforms), str(coins), str(checkpoint), str(flag)]
	for e in enemies:
		parts.append("%d,%d,%d,%d" % [e.x, e.y, e.patrol_from, e.patrol_to])
	return "|".join(parts)
