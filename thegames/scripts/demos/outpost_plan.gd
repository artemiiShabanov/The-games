class_name OutpostPlan
extends RefCounted
## План демки шутер × «продвинутые» «оборона аванпоста» (#123, спека `docs/specs/demos.md`):
## шесть волн врагов, идущих к вышке с трёх сторон, бочки с порохом на поле и место ящика с
## патронами на настиле. Строится `OutpostPlanGen` из сида записи.

enum Kind { RUNNER, SHIELD, THROWER, BRUTE }


class Spawn:
	## Через сколько секунд от начала волны, кто, с какой стороны (номер из `sides`), сдвиг
	## курса внутри стороны (рад) и на каком расстоянии от вышки встанет.
	var at := 0.0
	var kind := Kind.RUNNER
	var side := 0
	var spread := 0.0
	var stop := 8.0


class Wave:
	var spawns: Array[Spawn] = []

	func seconds() -> float:
		var last := 0.0
		for s in spawns:
			last = maxf(last, s.at)
		return last


## Курсы трёх сторон атаки (как `rotation.y`: 0 это −z), в порядке появления.
var sides := PackedFloat32Array()
var waves: Array[Wave] = []
## Бочки: место на земле (x, z).
var kegs := PackedVector2Array()
## Ящик с патронами: место на настиле (x, z).
var crate := Vector2.ZERO
## С какого расстояния враги выходят.
var far := 36.0


static func dir(yaw: float) -> Vector2:
	return Vector2(-sin(yaw), -cos(yaw))


func total() -> int:
	var n := 0
	for w in waves:
		n += w.spawns.size()
	return n


func count(kind: Kind) -> int:
	var n := 0
	for w in waves:
		for s in w.spawns:
			n += 1 if s.kind == kind else 0
	return n


## Сколько сторон занято в волне.
func sides_of(wave: int) -> int:
	var used := {}
	for s in waves[wave].spawns:
		used[s.side] = true
	return used.size()


func signature() -> String:
	var parts: PackedStringArray = []
	for a in sides:
		parts.append("%.2f" % a)
	for w in waves:
		for s in w.spawns:
			parts.append("%.1f,%d,%d,%.2f" % [s.at, s.kind, s.side, s.spread])
	for k in kegs:
		parts.append("k%.1f,%.1f" % [k.x, k.y])
	return "|".join(parts)
