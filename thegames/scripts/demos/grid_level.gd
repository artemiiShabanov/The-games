class_name GridLevel
extends RefCounted
## Уровень демки платформер × 16/32-bit «по клеткам» (#98, спека `docs/specs/demos.md`): один
## ряд клеток слева направо. Клетка это пол, яма, шипы, якорь на цепи (падает на клетку и
## поднимается) или плита; по участкам пола
## ходят стражники; над клетками висят монеты; флаг в конце. Ловушки ходят по ритму: у шипов и
## якоря свой период и сдвиг. Строится `GridLevelGen` из сида записи; игру считает `GridSim`.

enum Cell { FLOOR, PIT, SPIKES, ANCHOR, PLATE }

class Guard:
	## Участок патруля, клетки включительно, клетка старта и направление первого шага.
	var from := 0
	var to := 0
	var start := 0
	var dir := -1
	## Секунд на клетку.
	var step := 0.45


var width := 0
var cells: PackedInt32Array = []
## Период и сдвиг ритма ловушки клетки (шипы, якорь); у остальных клеток нули.
var period: PackedFloat32Array = []
var phase: PackedFloat32Array = []
var guards: Array[Guard] = []
## Клетки с монетой над ними.
var coins: PackedInt32Array = []
## Клетки отдыха по возрастанию: с последней пройденной герой начинает после потери жизни.
var checkpoints: PackedInt32Array = []
var start := 1
var flag := 0


func cell(x: int) -> Cell:
	return (cells[x] as Cell) if x >= 0 and x < width else Cell.FLOOR


## Сколько клеток каждого вида, по номеру вида.
func counts() -> PackedInt32Array:
	var out := PackedInt32Array([0, 0, 0, 0, 0])
	for c in cells:
		out[c] += 1
	return out


## Подпись для сравнения двух уровней: детерминизм генератора.
func signature() -> String:
	var parts: PackedStringArray = [str(cells), str(coins), str(checkpoints), str(flag)]
	for i in width:
		if period[i] > 0.0:
			parts.append("%d:%.3f,%.3f" % [i, period[i], phase[i]])
	for g in guards:
		parts.append("g%d,%d,%d,%d,%.3f" % [g.from, g.to, g.start, g.dir, g.step])
	return "|".join(parts)
