class_name HoopPlan
extends RefCounted
## План бросков демки спорт × low poly «броски в кольцо» (#115, спека `docs/specs/demos.md`):
## десять точек вокруг кольца на мачте. Мачта стоит в начале координат, кольцо смотрит в −Z,
## игрок бросает со стороны −Z. У броска своё расстояние, очки, ветер (стрелки вбок), езда
## кольца и шкала силы: зелёная зона шкалы это скорости, с которыми мяч входит чисто. Строится
## `HoopPlanGen` из сида записи.

class Shot:
	## Точка на земле, расстояние до кольца по земле, очки.
	var pos := Vector3.ZERO
	var dist := 4.0
	var points := 2
	## Подъём броска (радианы) и скорости чистого попадания: от, до.
	var lift := 1.0
	var v_lo := 8.0
	var v_hi := 8.4
	## Сколько секунд мяч летит до кольца.
	var flight := 1.2
	## Ветер в стрелках: плюс дует вправо от игрока. На сколько радиан одна стрелка уводит мяч.
	var wind := 0
	var tick := 0.0
	## Кольцо ездит вдоль X: размах, период, сдвиг (0 размах: стоит).
	var move_amp := 0.0
	var move_period := 4.0
	var move_phase := 0.0
	## Шкала силы: середина и половина зелёной зоны (доли шкалы), период хода туда и обратно.
	var zone := 0.5
	var zone_half := 0.08
	var meter := 1.4


var shots: Array[Shot] = []


func max_points(t: SportLowpolyTuning) -> int:
	var total := 0
	for s in shots:
		total += s.points + t.clean_bonus
	return total


func count_wind() -> int:
	var n := 0
	for s in shots:
		n += 1 if s.wind != 0 else 0
	return n


func count_moving() -> int:
	var n := 0
	for s in shots:
		n += 1 if s.move_amp > 0.0 else 0
	return n


## Подпись для сравнения двух планов: детерминизм генератора.
func signature() -> String:
	var parts: PackedStringArray = []
	for s in shots:
		parts.append("%s,%d,%.3f,%.3f,%.3f,%d,%.2f,%.2f,%.3f,%.3f,%.2f" % [s.pos, s.points, s.lift, s.v_lo, s.v_hi, s.wind, s.move_amp,
				s.move_phase, s.zone, s.zone_half, s.meter])
	return "|".join(parts)
