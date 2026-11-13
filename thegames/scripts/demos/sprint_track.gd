class_name SprintTrack
extends RefCounted
## Трасса демки гонки × «продвинутые» «спринт» (#122, спека `docs/specs/demos.md`): дорога из
## точки в точку по острову. Осевая задана точками через равный шаг: место, высота, курс,
## кривизна, половина ширины и покрытие. Положение на трассе это `s` метров от старта и `d`
## метров вбок от оси (плюс вправо по ходу). По бокам дороги обочина, за ней борт; на
## сужениях (мостки) обочины нет, перед ними на плечах стоят камни. Строится `SprintTrackGen`.

enum Surface { ROAD, SAND, PLANKS, VERGE }

var step := 2.0
var points := PackedVector2Array()
var heights := PackedFloat32Array()
## Курс как `rotation.y`, кривизна (плюс поворот влево), 1/м.
var yaws := PackedFloat32Array()
var curves := PackedFloat32Array()
var halves := PackedFloat32Array()
var surfaces := PackedByteArray()
var length := 1.0
## Половина ширины дороги обычная и на сужении.
var full_half := 6.5
var narrow_half := 3.4
## Сужения и участки рыхлого песка: от и до, метры от старта.
var narrows: Array[Vector2] = []
var sands: Array[Vector2] = []
## Камни на плечах сужений: `x` это `s`, `y` это `d`, `z` радиус.
var rocks: Array[Vector3] = []
## Повороты: `x` середина, `y` радиус со знаком (плюс влево), `z` длина. Для дампа и проверок.
var corners: Array[Vector3] = []
## Заготовки для расчёта скорости: модуль кривизны и выпуклость в каждой точке (`bake`).
var bends := PackedFloat32Array()
var crests := PackedFloat32Array()
var links := 0


## Посчитать заготовки: зовёт генератор, когда ось готова.
func bake() -> void:
	bends.resize(count())
	crests.resize(count())
	for i in count():
		bends[i] = absf(curves[i])
		crests[i] = crest(i * step)


func count() -> int:
	return points.size()


func _index(s: float) -> float:
	return clampf(s, 0.0, length) / step


func _lerp(values: PackedFloat32Array, s: float) -> float:
	var f := _index(s)
	var i := mini(int(f), count() - 2)
	return lerpf(values[i], values[i + 1], f - i)


func center(s: float) -> Vector2:
	var f := _index(s)
	var i := mini(int(f), count() - 2)
	var p := points[i].lerp(points[i + 1], f - i)
	# За финишем и до старта дорога продолжается прямо.
	if s > length:
		p += forward(length) * (s - length)
	elif s < 0.0:
		p += forward(0.0) * s
	return p


func height(s: float) -> float:
	return _lerp(heights, s)


func half(s: float) -> float:
	return _lerp(halves, s)


func yaw(s: float) -> float:
	var f := _index(s)
	var i := mini(int(f), count() - 2)
	return lerp_angle(yaws[i], yaws[i + 1], f - i)


func curve(s: float) -> float:
	return curves[clampi(int(roundf(_index(s))), 0, count() - 1)]


func surface(s: float) -> int:
	return surfaces[clampi(int(roundf(_index(s))), 0, count() - 1)]


## Уклон вдоль хода (плюс в гору) и выпуклость (плюс на гребне), 1/м.
func slope(s: float) -> float:
	return (height(s + step) - height(s - step)) / (2.0 * step)


func crest(s: float) -> float:
	return -(height(s + step * 2.0) - 2.0 * height(s) + height(s - step * 2.0)) / (4.0 * step * step)


func forward(s: float) -> Vector2:
	var a := yaw(s)
	return Vector2(-sin(a), -cos(a))


func right(s: float) -> Vector2:
	var a := yaw(s)
	return Vector2(cos(a), -sin(a))


func at(s: float, d: float) -> Vector2:
	return center(s) + right(s) * d


func world(s: float, d: float, up := 0.0) -> Vector3:
	var p := at(s, d)
	return Vector3(p.x, height(s) + up, p.y)


## Положение точки на трассе: `x` это `s`, `y` это `d`. `hint` это прошлое `s` машины.
func locate(p: Vector2, hint: float) -> Vector2:
	var n := count()
	var base := clampi(int(roundf(_index(hint))), 0, n - 1)
	var best := base
	var best_d := INF
	for k in range(-8, 13):
		var i := clampi(base + k, 0, n - 1)
		var dist := points[i].distance_squared_to(p)
		if dist < best_d:
			best_d = dist
			best = i
	var s := best * step
	s += (p - points[best]).dot(forward(s))
	return Vector2(s, (p - center(s)).dot(right(s)))


## Доля обочины в этом месте: 1 на обычной дороге, 0 на сужении (там за дорогой сразу борт).
func shoulder(s: float) -> float:
	return clampf((half(s) - narrow_half) / maxf(full_half - narrow_half, 0.01), 0.0, 1.0)


func is_narrow(s: float) -> bool:
	for r in narrows:
		if s >= r.x and s <= r.y:
			return true
	return false


## Самый крутой поворот на трассе: радиус, м.
func tightest() -> float:
	var worst := 0.0
	for c in curves:
		worst = maxf(worst, absf(c))
	return 1.0 / maxf(worst, 0.0001)


func climb() -> float:
	var low := INF
	var high := -INF
	for h in heights:
		low = minf(low, h)
		high = maxf(high, h)
	return high - low


## Подпись для сравнения двух трасс: детерминизм генератора.
func signature() -> String:
	var parts: PackedStringArray = ["%d|%.2f" % [count(), length]]
	for i in range(0, count(), 9):
		parts.append("%.2f,%.2f,%.2f,%.1f,%d" % [points[i].x, points[i].y, heights[i], halves[i], surfaces[i]])
	for r in rocks:
		parts.append("r%.1f,%.1f" % [r.x, r.y])
	return "|".join(parts)
