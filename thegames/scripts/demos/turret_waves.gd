class_name TurretWaves
extends RefCounted
## Волны демки шутер × вектор «башня в центре» (#92, спека `docs/specs/demos.md`): расписание
## появлений. Каждый враг появляется у края экрана на своём направлении от башни и летит к
## ней. Строится `TurretWaveGen` из сида записи; движение, выстрелы и повтор расписания по
## кругу считает `TurretSim`.

## Враг летит прямо и быстро; глыба медленная и от выстрела раскалывается на два осколка
## (`SMALL`, в расписании его нет); вьюн приближается по спирали.
enum Kind { ENEMY, ROCK, SMALL, SPINNER }

class Spawn:
	var time := 0.0
	## Направление от башни, радианы: 0 вправо, по часовой на экране.
	var angle := 0.0
	var kind := Kind.ENEMY
	## Скорость к башне, пикселей в секунду, и угловая скорость вокруг неё, радиан в секунду.
	var speed := 0.0
	var spin := 0.0


var spawns: Array[Spawn] = []
## Длина расписания: после неё оно повторяется быстрее.
var seconds := 0.0


## Сколько целей даёт расписание за один проход: глыба это она сама и два осколка.
func targets() -> int:
	var n := 0
	for s in spawns:
		n += 3 if s.kind == Kind.ROCK else 1
	return n


## Подпись для сравнения двух расписаний: детерминизм генератора.
func signature() -> String:
	var parts: PackedStringArray = ["%.2f" % seconds]
	for s in spawns:
		parts.append("%.2f,%.3f,%d,%.1f,%.3f" % [s.time, s.angle, s.kind, s.speed, s.spin])
	return "|".join(parts)
