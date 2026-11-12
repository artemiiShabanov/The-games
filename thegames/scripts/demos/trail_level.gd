class_name TrailLevel
extends RefCounted
## Уровень платформера × 16/32-bit «тропа» (#98): земля неровной ломаной со склонами, ямы с
## водой, лианы над широкими ямами, корни-арки, под которыми только в слайде, крабы и попугаи
## на участках. Генерирует `TrailLevelGen` по сиду, правила в `TrailSim`. Пиксели мира, y вниз;
## экран по высоте не едет, поэтому y мира это y экрана.

## Лиана: точка подвеса и длина.
class Vine:
	var anchor := Vector2.ZERO
	var length := 0.0


## Враг ходит или летает туда-сюда по участку `from`..`to` со скоростью `speed` (пикселей в
## секунду); `phase` 0..1 сдвиг по кругу. Положение это функция времени, своего состояния нет.
class Foe:
	var kind := 0
	var from := 0.0
	var to := 0.0
	var speed := 0.0
	var phase := 0.0


## Арка из корней: от `from` до `to` потолок на `gap` пикселей над землёй, выше ствол до верха.
class Arch:
	var from := 0.0
	var to := 0.0
	var gap := 18.0


enum FoeKind { CRAB, PARROT }

## Ломаная поверхности земли по x; в ямах `gaps` земли нет.
var points := PackedVector2Array()
## Ямы: пары `[от, до]` подряд.
var gaps := PackedFloat32Array()
var water_y := 250.0
var width := 0.0
var start_x := 40.0
var flag_x := 0.0
var vines: Array[Vine] = []
var foes: Array[Foe] = []
var arches: Array[Arch] = []
var coins := PackedVector2Array()
## Места возврата после потери жизни, по возрастанию x.
var checkpoints := PackedFloat32Array()
## Украшения переднего плана: `[x, вид]`, вид по `TrailLevelGen.Decor`.
var decor: Array[Vector2i] = []


## Яма ли под точкой x.
func in_gap(x: float) -> bool:
	for i in range(0, gaps.size(), 2):
		if x > gaps[i] and x < gaps[i + 1]:
			return true
	return false


## Высота земли в точке x; в яме и за краями INF.
func height_at(x: float) -> float:
	if x < 0.0 or x > width or in_gap(x):
		return INF
	var i := _segment(x)
	var a := points[i]
	var b := points[i + 1]
	if b.x <= a.x:
		return a.y
	return lerpf(a.y, b.y, (x - a.x) / (b.x - a.x))


## Наклон земли в точке x: dy/dx (минус это подъём вправо).
func slope_at(x: float) -> float:
	var i := _segment(x)
	var a := points[i]
	var b := points[i + 1]
	return (b.y - a.y) / maxf(b.x - a.x, 0.001)


func _segment(x: float) -> int:
	var lo := 0
	var hi := points.size() - 2
	while lo < hi:
		var mid := (lo + hi + 1) / 2
		if points[mid].x <= x:
			lo = mid
		else:
			hi = mid - 1
	return lo


## Арка над точкой x или null.
func arch_at(x: float) -> Arch:
	for a in arches:
		if x >= a.from and x <= a.to:
			return a
	return null


## Положение врага в момент `t` с множителем скорости `mult`: x и направление (+1 вправо).
static func foe_pos(f: Foe, t: float, mult := 1.0) -> Vector2:
	var span := maxf(f.to - f.from, 1.0)
	var d := fposmod(f.phase * 2.0 * span + f.speed * mult * t, 2.0 * span)
	if d < span:
		return Vector2(f.from + d, 1.0)
	return Vector2(f.from + 2.0 * span - d, -1.0)


## Отпечаток уровня для проверки детерминизма.
func signature() -> String:
	var s := "%d:%d:%d:%d:%d:%d" % [points.size(), gaps.size(), vines.size(), foes.size(), arches.size(), coins.size()]
	for p in points:
		s += ",%d" % int(p.y)
	for f in foes:
		s += ";%d,%d" % [int(f.from), int(f.speed)]
	return s
