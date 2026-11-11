class_name LaneRace
extends RefCounted
## Заезд демки гонки × вектор «полосы» (#91, спека `docs/specs/demos.md`): прямая дорога из
## `lanes` полос длиной `length` пикселей логического экрана, на ней препятствия (полоса и
## расстояние от старта) и соперники (полоса старта, фора в пикселях впереди игрока, темп).
## Строится `LaneRaceGen` из сида записи; здесь раскладка на старт, движение считает `LaneSim`.

class Rival:
	var lane := 0
	## Насколько впереди игрока стоит на старте.
	var head := 0.0
	## Своя скорость, пикселей в секунду, и фаза её покачивания.
	var pace := 0.0
	var phase := 0.0


var lanes := 4
var length := 24000.0
var start_lane := 1
## Препятствия: x полоса, y расстояние от старта; по возрастанию расстояния.
var obstacles: Array[Vector2] = []
var rivals: Array[Rival] = []


## Подпись для сравнения двух заездов: детерминизм генератора.
func signature() -> String:
	var parts: PackedStringArray = ["%d|%.1f|%d" % [lanes, length, start_lane]]
	for o in obstacles:
		parts.append("o%d,%.1f" % [int(o.x), o.y])
	for r in rivals:
		parts.append("r%d,%.1f,%.2f,%.3f" % [r.lane, r.head, r.pace, r.phase])
	return "|".join(parts)
