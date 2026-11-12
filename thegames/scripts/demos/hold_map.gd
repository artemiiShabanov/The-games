class_name HoldMap
extends RefCounted
## Карта шутера × 16/32-bit «до выхода» (#100, графика по Doom): сетка клеток, у каждой вид
## (`Cell`). Залы с проёмами в общих стенах (плейтест 2026-11-12: больше локаций, меньше
## коридоров), у каждого зала своя отделка стен и пола и предмет-ориентир; ключ, дверь выхода
## в наружной стене, враги двух видов и аптечки на полу. Клетка
## это квадрат 1×1 в единицах мира; середина клетки (x + 0.5, y + 0.5). Генерирует `HoldMapGen`
## по сиду, правила в `HoldSim`.

enum Cell { FLOOR, PLANKS, STONE, EXIT, PILLAR, CABIN, HULL, CARGO }
## Пол зала: доски, камень, ковёр.
enum Floor { PLANKS, STONE, CARPET }
## Скелет с мушкетом стреляет издали, с саблей бежит и рубит вблизи.
enum Foe { MUSKET, CUTLASS }
## Ориентиры залов: бочки, ящики, фонарь, пушка, сундук, штурвал.
enum Decor { BARRELS, CRATES, LANTERN, CANNON, CHEST, WHEEL }

## Комната: прямоугольник пола в клетках.
class Room:
	var rect := Rect2i()

	func center() -> Vector2:
		return Vector2(rect.position) + Vector2(rect.size) * 0.5

var width := 0
var height := 0
var cells := PackedByteArray()
var rooms: Array[Room] = []
var start := Vector2.ZERO
var start_angle := 0.0
var key := Vector2.ZERO
## Клетка двери выхода (в стене последней комнаты).
var exit := Vector2i.ZERO
## Враги и аптечки: середины клеток.
var foes := PackedVector2Array()
var foe_kinds := PackedByteArray()
var medkits := PackedVector2Array()
## Пол по клеткам (`Floor`) и ориентиры: x, y, вид.
var floors := PackedByteArray()
var decor := PackedVector3Array()


func cell(x: int, y: int) -> Cell:
	if x < 0 or y < 0 or x >= width or y >= height:
		return Cell.STONE
	return cells[y * width + x] as Cell


func set_cell(x: int, y: int, c: Cell) -> void:
	cells[y * width + x] = c


func floor_at(x: int, y: int) -> Floor:
	if x < 0 or y < 0 or x >= width or y >= height:
		return Floor.PLANKS
	return floors[y * width + x] as Floor


## Проходима ли клетка для ходьбы (дверь выхода нет: в неё входят с ключом, это победа).
func open(x: int, y: int) -> bool:
	return cell(x, y) == Cell.FLOOR


func solid_at(p: Vector2) -> bool:
	return not open(int(floor(p.x)), int(floor(p.y)))


## Путь по клеткам от `a` до `b` (обе проходимы или `b` это выход), поиск в ширину; пусто, если
## пути нет. Возвращает клетки без начальной.
func path(a: Vector2i, b: Vector2i) -> Array[Vector2i]:
	var came := {a: a}
	var queue: Array[Vector2i] = [a]
	var head := 0
	while head < queue.size():
		var c := queue[head]
		head += 1
		if c == b:
			break
		for d: Vector2i in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var n := c + d
			if came.has(n) or not (open(n.x, n.y) or n == b):
				continue
			came[n] = c
			queue.append(n)
	if not came.has(b):
		return []
	var out: Array[Vector2i] = []
	var c := b
	while c != a:
		out.push_front(c)
		c = came[c]
	return out


## Видно ли из `a` в `b`: луч не задевает стен (шаг в восьмую клетки, мельче шага пули).
func sight(a: Vector2, b: Vector2) -> bool:
	var d := b - a
	var n := int(ceil(d.length() * 8.0))
	for i in range(1, n):
		if solid_at(a + d * (float(i) / n)):
			return false
	return true


func signature() -> String:
	var s := "%dx%d:%d:%d:%d" % [width, height, rooms.size(), foes.size(), medkits.size()]
	for i in range(0, cells.size(), 13):
		s += str(cells[i])
	return s + ":%d,%d" % [exit.x, exit.y]
