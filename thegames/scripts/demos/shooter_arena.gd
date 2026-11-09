class_name ShooterArena
extends RefCounted
## Арена шутера × 8-bit, спека `docs/specs/demos.md` и каталог демок. Строится
## `ShooterArenaGen` из сида записи игры. Один экран тайлов 16×16: палуба, борт по краю, в
## борту трапы (по ним враги поднимаются на палубу, герою и ядрам туда нельзя), пропы на палубе
## держат и героя, и врагов, и выстрелы. Волны врагов тоже из сида: состав и трап у каждого.

enum Tile { FLOOR, WALL, DOOR, PROP }
enum Kind { BARREL, CHEST, CANNON }
enum Enemy { WALKER, GUNNER }

class Prop:
	var cell := Vector2i.ZERO
	var kind := Kind.BARREL

class Spawn:
	var kind := Enemy.WALKER
	## Индекс трапа в `doors`.
	var door := 0

class Wave:
	var spawns: Array[Spawn] = []

const TILE := 16
const NEIGHBOURS: Array[Vector2i] = [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]

## Арена в тайлах, строки сверху вниз.
var width := 0
var height := 0
var tiles: PackedByteArray = []
## Трапы: клетка в борту и направление внутрь палубы.
var doors: Array[Vector2i] = []
var door_dirs: Array[Vector2i] = []
var props: Array[Prop] = []
var waves: Array[Wave] = []
## Сколько попыток понадобилось генератору; `fallback` это арена без пропов.
var attempts := 1
var fallback := false


func size_px() -> Vector2:
	return Vector2(width * TILE, height * TILE)


func tile(col: int, row: int) -> Tile:
	if col < 0 or row < 0 or col >= width or row >= height:
		return Tile.WALL
	return tiles[row * width + col] as Tile


func set_tile(col: int, row: int, t: Tile) -> void:
	tiles[row * width + col] = t


func cell_of(p: Vector2) -> Vector2i:
	return Vector2i(int(floor(p.x / TILE)), int(floor(p.y / TILE)))


func center_of(cell: Vector2i) -> Vector2:
	return (Vector2(cell) + Vector2(0.5, 0.5)) * TILE


func tile_at(p: Vector2) -> Tile:
	var c := cell_of(p)
	return tile(c.x, c.y)


## Старт героя: середина палубы.
func start_cell() -> Vector2i:
	return Vector2i(width / 2, height / 2)


## Точка закрыта для выстрела: борт, трап или проп.
func blocks_shot(p: Vector2) -> bool:
	return tile_at(p) != Tile.FLOOR


## Прямая от `a` до `b` свободна от борта и пропов (шаг 4 px).
func line_clear(a: Vector2, b: Vector2) -> bool:
	var d := b - a
	var n := maxi(int(ceil(d.length() / 4.0)), 1)
	for i in range(1, n):
		if blocks_shot(a + d * (float(i) / n)):
			return false
	return true


## Расстояния в шагах от клетки `goal` по палубе и трапам (4-связность), -1 недостижимо.
func distances(goal: Vector2i) -> PackedInt32Array:
	var dist: PackedInt32Array = []
	dist.resize(width * height)
	dist.fill(-1)
	if not _walkable(goal):
		return dist
	dist[goal.y * width + goal.x] = 0
	var queue: Array[Vector2i] = [goal]
	var head := 0
	while head < queue.size():
		var c := queue[head]
		head += 1
		var d := dist[c.y * width + c.x]
		for o in NEIGHBOURS:
			var n := c + o
			if _walkable(n) and dist[n.y * width + n.x] < 0:
				dist[n.y * width + n.x] = d + 1
				queue.append(n)
	return dist


func _walkable(c: Vector2i) -> bool:
	var t := tile(c.x, c.y)
	return t == Tile.FLOOR or t == Tile.DOOR


func total_enemies() -> int:
	var n := 0
	for w in waves:
		n += w.spawns.size()
	return n
