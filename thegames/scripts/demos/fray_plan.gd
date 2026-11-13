class_name FrayPlan
extends RefCounted
## План демки файтинг × «продвинутые» «один против всех» (#125, спека `docs/specs/demos.md`):
## шесть волн пиратов, которые выходят на палубу вокруг героя. Строится `FrayPlanGen` из сида.

enum Kind { THUG, SHIELD, KNIFE }


class Wave:
	## Кто выходит и с какой стороны палубы (угол), замах врагов, пауза между атаками, шанс
	## атаки вдвоём.
	var kinds: Array[int] = []
	var angles := PackedFloat32Array()
	var windup := 0.9
	var gap := 2.0
	var pair := 0.0


var waves: Array[Wave] = []
## Зерно случайности боя: кто нападает следующим.
var seed := 1


func total() -> int:
	var n := 0
	for w in waves:
		n += w.kinds.size()
	return n


func count(kind: Kind) -> int:
	var n := 0
	for w in waves:
		for k in w.kinds:
			n += 1 if k == kind else 0
	return n


func signature() -> String:
	var parts: PackedStringArray = [str(seed)]
	for w in waves:
		var line := ""
		for i in w.kinds.size():
			line += "%d:%.2f," % [w.kinds[i], w.angles[i]]
		parts.append(line)
	return "|".join(parts)
