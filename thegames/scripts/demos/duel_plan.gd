class_name DuelPlan
extends RefCounted
## План дуэли на реакцию (файтинг × вектор, #94, спека `docs/specs/demos.md`): по раунду пауза
## до вспышки и задержка реакции соперника. Соперник от раунда к раунду всё быстрее. Строится
## `DuelPlanGen` из сида записи; дуэль считает `DuelSim`.

## Пауза до вспышки по раундам, секунды.
var waits: Array[float] = []
## Через сколько после вспышки бьёт соперник, по раундам, секунды.
var delays: Array[float] = []


func rounds() -> int:
	return waits.size()


## Подпись для сравнения двух планов: детерминизм генератора.
func signature() -> String:
	var parts: PackedStringArray = []
	for i in waits.size():
		parts.append("%.3f,%.3f" % [waits[i], delays[i]])
	return "|".join(parts)
