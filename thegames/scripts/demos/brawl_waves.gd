class_name BrawlWaves
extends RefCounted
## Волны битемапа × 16/32-bit (#102) по сиду (`BrawlWavesGen`): для каждого из трёх экранов
## список врагов: вид, сторона выхода (−1 слева, 1 справа), задержка выхода, глубина. Правила в
## `BrawlSim`.

enum Kind { HERO, THUG, KNIFE, BOSS }

class Spawn:
	var kind := Kind.THUG
	var side := 1.0
	var delay := 0.0
	var y := 0.0

## Экраны: массив массивов `Spawn`.
var screens: Array[Array] = []
## Имена врагов на полоске здоровья (по сиду из списка).
var names: Array[String] = []


func count() -> int:
	var n := 0
	for s in screens:
		n += s.size()
	return n


func signature() -> String:
	var out := ""
	for s in screens:
		out += "|"
		for sp: Spawn in s:
			out += "%d%s%d" % [sp.kind, "L" if sp.side < 0.0 else "R", int(sp.delay * 10.0)]
	return out
