class_name RoadTrack
extends RefCounted
## Трасса гонки × 16/32-bit «псевдо-3D» (#99, игра по мотивам Horizon Chase Turbo, графика по
## Outrun): дорога из сегментов длиной `SEG`, у каждого изгиб (`curve`, плюс вправо) и высота
## конца (`y`, плюс вверх). Пропы у обочин, монеты рядами, стартовая решётка соперников.
## Поперёк дороги `x` в полуширинах: −1..1 дорога, дальше обочина. Генерирует `RoadTrackGen`
## по сиду, правила в `RoadSim`.

## Длина сегмента и полуширина дороги в единицах мира.
const SEG := 200.0
const ROAD_W := 2000.0

enum Prop { PALM, ROCK, BARREL, SIGN_LEFT, SIGN_RIGHT, HUT }

## Соперник на старте: x, расстояние от старта, доля наибольшей скорости, оттенок повозки.
class Rival:
	var x := 0.0
	var z := 0.0
	var speed := 0.0
	var tint := 0

var curve := PackedFloat32Array()
var y := PackedFloat32Array()
## Пропы: `[сегмент, x, вид]`.
var props: Array[Vector3] = []
## Монеты: x и расстояние от старта.
var coins := PackedVector2Array()
var rivals: Array[Rival] = []
## Финиш: номер сегмента; трасса тянется дальше, чтобы было что рисовать за ним.
var finish := 0


## Пропы сегмента `i` (пропы отсортированы по сегменту при генерации).
func props_in(i: int) -> Array[Vector3]:
	var out: Array[Vector3] = []
	var lo := 0
	var hi := props.size()
	while lo < hi:
		var mid := (lo + hi) / 2
		if int(props[mid].x) < i:
			lo = mid + 1
		else:
			hi = mid
	while lo < props.size() and int(props[lo].x) == i:
		out.append(props[lo])
		lo += 1
	return out


func count() -> int:
	return curve.size()


## Сегмент под расстоянием `z` (по кругу, если дальше конца).
func seg_at(z: float) -> int:
	return posmod(int(floor(z / SEG)), count())


## Высота дороги под `z`: между концами сегментов по прямой.
func height_at(z: float) -> float:
	var i := seg_at(z)
	var y0 := y[i - 1] if i > 0 else 0.0
	return lerpf(y0, y[i], fposmod(z, SEG) / SEG)


func finish_z() -> float:
	return finish * SEG


func signature() -> String:
	var s := "%d:%d:%d:%d" % [count(), props.size(), coins.size(), rivals.size()]
	for i in range(0, count(), 37):
		s += ",%d/%d" % [int(curve[i] * 10.0), int(y[i])]
	for r in rivals:
		s += ";%d" % int(r.speed * 1000.0)
	return s
