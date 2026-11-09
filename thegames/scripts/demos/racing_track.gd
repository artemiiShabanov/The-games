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
## перескакивает на соседний участок петли.
func nearest(pos: Vector2, hint: int, window := 12) -> int:
	var n := points.size()
	var best := hint
	var best_d := INF
	for k in range(-window, window + 1):
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
