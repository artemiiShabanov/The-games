class_name SaberPlan
extends RefCounted
## План соперника в демке файтинг × «продвинутые» «дуэль на саблях» (#125, спека
## `docs/specs/demos.md`): ходы по порядку. Ход это связка из одного-трёх ударов или один
## выпад, который блок не держит. Стороны считаются с места игрока: слева, сверху, справа.
## Строится `SaberPlanGen` из сида записи.

enum Side { LEFT, TOP, RIGHT }


class Strike:
	## Откуда удар придёт, какую сторону показывает замах сначала (при финте другая), длина
	## замаха.
	var side := Side.TOP
	var shown := Side.TOP
	var windup := 0.7

	func feint() -> bool:
		return shown != side


class Move:
	## Пауза перед ходом, удары; выпад (блок не держит, один удар); стойка соперника в паузе и
	## как часто он её меняет; шанс закрыться от удара героя.
	var pause := 1.0
	var strikes: Array[Strike] = []
	var lunge := false
	var guard := Side.TOP
	var guard_hold := 1.5
	var react := 0.3


var moves: Array[Move] = []


func strikes() -> int:
	var n := 0
	for m in moves:
		n += m.strikes.size()
	return n


func feints() -> int:
	var n := 0
	for m in moves:
		for s in m.strikes:
			n += 1 if s.feint() else 0
	return n


func lunges() -> int:
	var n := 0
	for m in moves:
		n += 1 if m.lunge else 0
	return n


func longest() -> int:
	var n := 0
	for m in moves:
		n = maxi(n, m.strikes.size())
	return n


func signature() -> String:
	var parts: PackedStringArray = []
	for m in moves:
		var line := "%.2f%s" % [m.pause, "L" if m.lunge else ""]
		for s in m.strikes:
			line += ",%d%d" % [s.shown, s.side]
		parts.append(line)
	return "|".join(parts)
