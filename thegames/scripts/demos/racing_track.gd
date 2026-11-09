class_name RacingTrack
extends RefCounted
## Трасса гонок × 8-bit, спека `docs/specs/demos.md` и каталог демок. Строится
## `RacingTrackGen` из сида записи игры. Карта тайлов 16×16: вода трассы, отмель-обочина
## (замедляет) и берег-стена. Средняя линия замкнута: точки `points` в пикселях с шагом
## `sample_step`, индекс 0 на линии финиша, движение по возрастанию индекса. Нормаль смотрит
## вправо по ходу (экран, y вниз).

enum Tile { WALL, SIDE, ROAD }
enum Kind { BARREL, ROCK }

class Obstacle:
	var pos := Vector2.ZERO
	var radius := 6.0
	var kind := Kind.BARREL
	## Точка средней линии, у которой стоит, и борт: +1 справа по ходу, -1 слева.
	var index := 0
	var side := 1

const TILE := 16

## Карта в тайлах, строки сверху вниз.
var width := 0
var height := 0
var tiles: PackedByteArray = []
var points: PackedVector2Array = []
var tangents: PackedVector2Array = []
var normals: PackedVector2Array = []
var obstacles: Array[Obstacle] = []
## Буи на кромке воды, украшение без столкновений.
var buoys: PackedVector2Array = []
## Препятствие впереди у точки: его борт (+1, -1) или 0; боты объезжают с другой стороны.
var avoid_side: PackedInt32Array = []
## Полуширина воды и ширина отмели в пикселях.
var road_half_px := 56.0
var side_px := 24.0
## Шаг точек средней линии в пикселях (длина петли / число точек).
var step_px := 8.0
## Сколько попыток понадобилось генератору; `fallback` это запасной эллипс без разброса.
var attempts := 1
var fallback := false


func count() -> int:
	return points.size()


func size_px() -> Vector2:
	return Vector2(width * TILE, height * TILE)


func tile(col: int, row: int) -> Tile:
	if col < 0 or row < 0 or col >= width or row >= height:
		return Tile.WALL
	return tiles[row * width + col] as Tile


func tile_at(pos: Vector2) -> Tile:
	return tile(int(floor(pos.x / TILE)), int(floor(pos.y / TILE)))


## Ближайшая точка средней линии к `pos` в окне ±`window` вокруг прошлой `hint`: машина не
## перескакивает на соседний участок петли. `ahead` больше `window` расширяет окно вперёд
## (срезки по суше с багом «сквозь стены»).
func nearest(pos: Vector2, hint: int, window := 12, ahead := -1) -> int:
	var n := points.size()
	var best := hint
	var best_d := INF
	for k in range(-window, maxi(window, ahead) + 1):
		var i := posmod(hint + k, n)
		var d := pos.distance_squared_to(points[i])
		if d < best_d:
			best_d = d
			best = i
	return best


## Ближайшая точка по всей петле: для старта и проверок.
func nearest_global(pos: Vector2) -> int:
	var best := 0
	var best_d := INF
	for i in points.size():
		var d := pos.distance_squared_to(points[i])
		if d < best_d:
			best_d = d
			best = i
	return best


## Боковое смещение от средней линии у точки `i`: плюс справа по ходу.
func lateral(pos: Vector2, i: int) -> float:
	return (pos - points[i]).dot(normals[i])


## Разность индексов по петле в (-n/2, n/2].
func wrap_delta(d: int) -> int:
	var n := points.size()
	d = posmod(d, n)
	return d - n if d > n / 2 else d


## Срезки через сушу для бага «сквозь стены»: пары точек (откуда, куда), где прямая от одной
## к другой идёт по берегу и со скоростью на суше `land_mult` короче пути по воде хотя бы на
## долю `min_gain`. Прямая не задевает препятствия (запас `clear`) и край карты. Срезки не
## перекрываются: сначала самые выгодные. `from_ahead` и `to_ahead` окно поиска в точках.
func shortcuts(land_mult: float, min_gain: float, clear: float, from_ahead := 20, to_ahead := 120) -> Array[Vector2i]:
	var n := points.size()
	var bounds := Rect2(Vector2.ZERO, size_px()).grow(-clear)
	var found: Array[Vector3] = []
	for i in n:
		var best := -1
		var best_gain := min_gain
		for d in range(from_ahead, mini(to_ahead, n / 2) + 1):
			var j := (i + d) % n
			# Грубо: вся хорда по суше.
			var gain := 1.0 - points[i].distance_to(points[j]) / land_mult / (d * step_px)
			if gain > best_gain and _chord_ok(points[i], points[j], bounds, clear):
				best = d
				best_gain = gain
		if best > 0:
			found.append(Vector3(i, best, best_gain))
	found.sort_custom(func(x: Vector3, y: Vector3) -> bool: return x.z > y.z)
	var taken := PackedByteArray()
	taken.resize(n)
	var out: Array[Vector2i] = []
	for f in found:
		var i := int(f.x)
		var d := int(f.y)
		var free := true
		for k in d + 1:
			if taken[(i + k) % n] != 0:
				free = false
				break
		if not free:
			continue
		for k in d + 1:
			taken[(i + k) % n] = 1
		out.append(Vector2i(i, (i + d) % n))
	out.sort()
	return out


## Хорда проходит по суше и не задевает препятствия и край карты.
func _chord_ok(a: Vector2, b: Vector2, bounds: Rect2, clear: float) -> bool:
	var land := false
	var steps := maxi(int(a.distance_to(b) / 4.0), 1)
	for s in steps + 1:
		var p := a.lerp(b, float(s) / steps)
		if not bounds.has_point(p):
			return false
		if tile_at(p) == Tile.WALL:
			land = true
	if not land:
		return false
	for ob in obstacles:
		if Geometry2D.get_closest_point_to_segment(ob.pos, a, b).distance_to(ob.pos) < ob.radius + clear:
			return false
	return true
