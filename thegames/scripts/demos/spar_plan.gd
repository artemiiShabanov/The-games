class_name SparPlan
extends RefCounted
## План соперника демки файтинг × low poly (#116, спека `docs/specs/demos.md`): связки ударов
## по порядку и жребий, закроется ли он от очередного удара героя. Удар связки: рукой, ногой
## (замах дольше, бьёт больнее) или сильный (блок не держит, только шаг в глубину).
## Строится `SparPlanGen` из сида записи.

enum Move { PUNCH, KICK, HEAVY }

class Combo:
	## Пауза перед связкой, удары по порядку, замах обычного удара.
	var gap := 1.2
	var moves: Array[int] = []
	var windup := 0.45


var combos: Array[Combo] = []
## Замах сильного удара.
var heavy_windup := 0.85
## Жребий блока соперника по порядку ударов героя: число 0..1, блок, если меньше порога.
var guard := PackedFloat32Array()
var guard_punch := 0.6
var guard_kick := 0.45
## С какой связки план идёт по кругу, когда кончился.
var loop_from := 0


func combo(index: int) -> Combo:
	if index < combos.size():
		return combos[index]
	return combos[loop_from + (index - combos.size()) % (combos.size() - loop_from)]


func count(move: Move) -> int:
	var n := 0
	for c in combos:
		for m in c.moves:
			n += 1 if m == move else 0
	return n


func longest() -> int:
	var n := 0
	for c in combos:
		n = maxi(n, c.moves.size())
	return n


## Подпись для сравнения двух планов: детерминизм генератора.
func signature() -> String:
	var parts: PackedStringArray = []
	for c in combos:
		parts.append("%.2f,%s,%.2f" % [c.gap, c.moves, c.windup])
	return "|".join(parts) + "#" + str(guard.slice(0, 12))
