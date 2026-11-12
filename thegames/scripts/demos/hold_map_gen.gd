class_name HoldMapGen
extends RefCounted
## Генератор карты «до выхода» из сида (#100): детерминирован. Залы, а не лабиринт (плейтест
## 2026-11-12): карта режется на сетку крупных залов (3×2 или 2×3, ширины и высоты случайные),
## иногда два соседних сливаются в один большой. Соседние залы соединены проёмами в общей стене
## шириной в две клетки: остов-дерево по соседству плюс один лишний проход для петли. У каждого
## зала своя отделка (доски трюма, камень пещеры, красная каюта, борт с иллюминаторами, склад
## ящиков), свой пол и предмет-ориентир. Старт в угловом зале; выход в наружной стене самого
## дальнего по проходам зала, ключ в самом дальнем из остальных. В больших залах колонны.
## Скелетов по залу 1-3 (кроме стартового), поровну с мушкетами и с саблями; аптечки через зал.

const THEMES: Array[HoldMap.Cell] = [HoldMap.Cell.PLANKS, HoldMap.Cell.STONE, HoldMap.Cell.CABIN, HoldMap.Cell.HULL,
		HoldMap.Cell.CARGO]


static func generate(seed_: int, t: ShooterBit16GenTuning = null) -> HoldMap:
	if t == null:
		t = ShooterBit16GenTuning.load_default()
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":hold"))
	var m := HoldMap.new()
	var wide := rng.randf() < 0.5
	var cols := 3 if wide else 2
	var rows := 2 if wide else 3
	m.width = t.width if wide else t.height
	m.height = t.height if wide else t.width
	m.cells.resize(m.width * m.height)
	m.cells.fill(HoldMap.Cell.PLANKS)
	m.floors.resize(m.width * m.height)
	m.floors.fill(HoldMap.Floor.PLANKS)
	var xs := _cuts(rng, m.width, cols, t.room_min)
	var ys := _cuts(rng, m.height, rows, t.room_min)
	# Сетка залов: индекс по (столбец, ряд); слитые залы делят один индекс.
	var id := {}
	for cy in rows:
		for cx in cols:
			id[Vector2i(cx, cy)] = cy * cols + cx
	if rng.randf() < t.merge_chance:
		var a := Vector2i(rng.randi_range(0, cols - 1), rng.randi_range(0, rows - 1))
		var b := a + (Vector2i(1, 0) if a.x < cols - 1 else Vector2i(-1, 0))
		id[b] = id[a]
	# Залы как прямоугольники: у слитых охватывающий.
	var rects := {}
	for c: Vector2i in id:
		var r := Rect2i(xs[c.x] + 1, ys[c.y] + 1, xs[c.x + 1] - xs[c.x] - 1, ys[c.y + 1] - ys[c.y] - 1)
		var k: int = id[c]
		rects[k] = r if not rects.has(k) else (rects[k] as Rect2i).merge(r)
	var keys := rects.keys()
	keys.sort()
	var index := {}
	for k in keys:
		var room := HoldMap.Room.new()
		room.rect = rects[k]
		index[k] = m.rooms.size()
		m.rooms.append(room)
		_carve(m, room.rect)
	# Отделка залов: темы по кругу в случайном порядке, у стен вокруг зала его тема.
	var themes := THEMES.duplicate()
	_shuffle(rng, themes)
	for i in m.rooms.size():
		_theme(m, m.rooms[i].rect, themes[i % themes.size()])
	# Соседство залов по сетке и проёмы: остов-дерево обходом в глубину плюс один лишний.
	var edges: Array[Vector2i] = []
	for c: Vector2i in id:
		for d: Vector2i in [Vector2i(1, 0), Vector2i(0, 1)]:
			var n := c + d
			if id.has(n) and id[n] != id[c]:
				var e := Vector2i(mini(index[id[c]], index[id[n]]), maxi(index[id[c]], index[id[n]]))
				if not edges.has(e):
					edges.append(e)
	_shuffle(rng, edges)
	var linked := {0: true}
	var used: Array[Vector2i] = []
	var grew := true
	while grew:
		grew = false
		for e in edges:
			if used.has(e) or linked.has(e.x) == linked.has(e.y):
				continue
			used.append(e)
			linked[e.x] = true
			linked[e.y] = true
			grew = true
	for e in edges:
		if not used.has(e):
			used.append(e)
			break
	for e in used:
		_doorway(m, rng, m.rooms[e.x].rect, m.rooms[e.y].rect)
	_pillars(m, rng, t)
	_place(m, rng, t, used)
	return m


## Границы залов по длине `size`: `n` частей, каждая не уже `min_`, лишнее раздаётся случайно;
## стены в границах, первая 0, последняя `size − 1`.
static func _cuts(rng: RandomNumberGenerator, size: int, n: int, min_: int) -> Array[int]:
	var extra: Array[int] = []
	for i in n:
		extra.append(0)
	for k in maxi(size - (n + 1) - n * min_, 0):
		extra[rng.randi_range(0, n - 1)] += 1
	var out: Array[int] = [0]
	for i in n:
		out.append(out[-1] + min_ + extra[i] + 1)
	return out


static func _shuffle(rng: RandomNumberGenerator, a: Array) -> void:
	for i in range(a.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var tmp: Variant = a[i]
		a[i] = a[j]
		a[j] = tmp


static func _carve(m: HoldMap, r: Rect2i) -> void:
	for y in range(r.position.y, r.end.y):
		for x in range(r.position.x, r.end.x):
			m.set_cell(x, y, HoldMap.Cell.FLOOR)


## Стены вокруг зала его отделкой, пол по отделке: камень у пещеры, ковёр у каюты.
static func _theme(m: HoldMap, r: Rect2i, theme: HoldMap.Cell) -> void:
	var fl := HoldMap.Floor.STONE if theme == HoldMap.Cell.STONE else (HoldMap.Floor.CARPET if theme == HoldMap.Cell.CABIN else HoldMap.Floor.PLANKS)
	var g := r.grow(1)
	for y in range(g.position.y, g.end.y):
		for x in range(g.position.x, g.end.x):
			if x < 0 or y < 0 or x >= m.width or y >= m.height:
				continue
			if m.cell(x, y) == HoldMap.Cell.FLOOR:
				m.floors[y * m.width + x] = fl
			elif m.cell(x, y) == HoldMap.Cell.PLANKS:
				m.set_cell(x, y, theme)


## Проём шириной в две клетки в общей стене двух залов (по середине их общего отрезка).
static func _doorway(m: HoldMap, rng: RandomNumberGenerator, a: Rect2i, b: Rect2i) -> void:
	if a.end.x + 1 == b.position.x or b.end.x + 1 == a.position.x:
		var x := a.end.x if a.end.x + 1 == b.position.x else b.end.x
		var lo := maxi(a.position.y, b.position.y) + 1
		var hi := mini(a.end.y, b.end.y) - 3
		var y := rng.randi_range(lo, maxi(lo, hi))
		for k in 2:
			m.set_cell(x, y + k, HoldMap.Cell.FLOOR)
	else:
		var y := a.end.y if a.end.y + 1 == b.position.y else b.end.y
		var lo := maxi(a.position.x, b.position.x) + 1
		var hi := mini(a.end.x, b.end.x) - 3
		var x := rng.randi_range(lo, maxi(lo, hi))
		for k in 2:
			m.set_cell(x + k, y, HoldMap.Cell.FLOOR)


## Колонны в больших залах: квадрат из четырёх в середине или две пары, путь вокруг остаётся.
static func _pillars(m: HoldMap, rng: RandomNumberGenerator, t: ShooterBit16GenTuning) -> void:
	for room in m.rooms:
		var r := room.rect
		if r.size.x < t.pillar_room or r.size.y < t.pillar_room or rng.randf() > 0.7:
			continue
		var c := r.get_center()
		var spots: Array[Vector2i] = [c + Vector2i(-2, -2), c + Vector2i(1, -2), c + Vector2i(-2, 1), c + Vector2i(1, 1)]
		for p in spots:
			if r.has_point(p) and r.grow(-2).has_point(p):
				m.set_cell(p.x, p.y, HoldMap.Cell.PILLAR)


static func _place(m: HoldMap, rng: RandomNumberGenerator, t: ShooterBit16GenTuning, edges: Array[Vector2i]) -> void:
	# Старт в угловом зале (первом по сетке): в середине, лицом к ближнему проёму.
	var first := m.rooms[0]
	m.start = Vector2(first.rect.get_center()) + Vector2(0.5, 0.5)
	if m.solid_at(m.start):
		m.start = _free_spot(m, rng, first.rect)
	# Расстояния по проходам между залами от стартового.
	var dist := {0: 0}
	var queue: Array[int] = [0]
	while not queue.is_empty():
		var a: int = queue.pop_front()
		for e in edges:
			var b := e.y if e.x == a else (e.x if e.y == a else -1)
			if b >= 0 and not dist.has(b):
				dist[b] = dist[a] + 1
				queue.append(b)
	var order := dist.keys()
	order.sort_custom(func(a: int, b: int) -> bool: return dist[a] > dist[b] or (dist[a] == dist[b] and a > b))
	var exit_room: int = order[0]
	var key_room: int = order[1] if order.size() > 1 and order[1] != 0 else exit_room
	m.key = _free_spot(m, rng, m.rooms[key_room].rect)
	m.exit = _exit_wall(m, m.rooms[exit_room].rect)
	m.set_cell(m.exit.x, m.exit.y, HoldMap.Cell.EXIT)
	var to := Vector2(m.rooms[order[order.size() - 2] if order.size() > 1 else 0].rect.get_center()) - m.start
	m.start_angle = atan2(to.y, to.x)
	var musket := rng.randf() < 0.5
	for i in range(1, m.rooms.size()):
		var r := m.rooms[i].rect
		var n := clampi(r.get_area() / t.cells_per_foe, t.foes_min, t.foes_max)
		for k in n:
			m.foes.append(_free_spot(m, rng, r))
			m.foe_kinds.append(HoldMap.Foe.MUSKET if musket else HoldMap.Foe.CUTLASS)
			musket = not musket
		if i % t.medkit_every == 0:
			m.medkits.append(_free_spot(m, rng, r))
	# Ориентир зала: свой предмет у стены, у каждого зала другой.
	var kinds := range(HoldMap.Decor.size())
	_shuffle(rng, kinds)
	for i in m.rooms.size():
		var r := m.rooms[i].rect
		var kind: int = kinds[i % kinds.size()]
		for k in 2:
			var corner := Vector2(r.position) + Vector2(0.7, 0.7) if k == 0 else Vector2(r.end) - Vector2(0.7, 0.7)
			if not m.solid_at(corner):
				m.decor.append(Vector3(corner.x, corner.y, kind))


## Клетка наружной стены зала для двери выхода: дальняя от старта, с полом ровно с одной стороны.
static func _exit_wall(m: HoldMap, r: Rect2i) -> Vector2i:
	var best := Vector2i(-1, -1)
	for x in range(r.position.x + 1, r.end.x - 1):
		for c: Vector2i in [Vector2i(x, r.position.y - 1), Vector2i(x, r.end.y)]:
			best = _better_exit(m, c, best)
	for y in range(r.position.y + 1, r.end.y - 1):
		for c: Vector2i in [Vector2i(r.position.x - 1, y), Vector2i(r.end.x, y)]:
			best = _better_exit(m, c, best)
	return best


static func _better_exit(m: HoldMap, c: Vector2i, best: Vector2i) -> Vector2i:
	var outer := c.x == 0 or c.y == 0 or c.x == m.width - 1 or c.y == m.height - 1
	if not outer or m.open(c.x, c.y):
		return best
	if best.x < 0 or Vector2(c).distance_to(m.start) > Vector2(best).distance_to(m.start):
		return c
	return best


static func _free_spot(m: HoldMap, rng: RandomNumberGenerator, r: Rect2i) -> Vector2:
	for i in 60:
		var x := rng.randi_range(r.position.x + 1, r.end.x - 2)
		var y := rng.randi_range(r.position.y + 1, r.end.y - 2)
		var p := Vector2(x + 0.5, y + 0.5)
		if m.open(x, y) and p.distance_to(m.key) > 0.9 and p.distance_to(m.start) > 0.9:
			return p
	return Vector2(r.get_center()) + Vector2(0.5, 0.5)


## Проверка карты; пустая строка, если всё в порядке.
static func validate(m: HoldMap, t: ShooterBit16GenTuning) -> String:
	if m.rooms.size() < t.rooms_min:
		return "залов %d" % m.rooms.size()
	var s := Vector2i(m.start)
	if not m.open(s.x, s.y):
		return "старт в стене"
	if m.exit.x < 0:
		return "нет двери выхода"
	if m.path(s, Vector2i(m.key)).is_empty():
		return "к ключу нет пути"
	if m.path(s, m.exit).is_empty():
		return "к выходу нет пути"
	for f in m.foes:
		if not m.open(int(f.x), int(f.y)):
			return "враг в стене"
		if f.distance_to(m.start) < 4.0:
			return "враг у старта"
	var musket := 0
	for k in m.foe_kinds:
		musket += 1 if k == HoldMap.Foe.MUSKET else 0
	if absi(musket * 2 - m.foe_kinds.size()) > 1:
		return "мушкетов %d из %d" % [musket, m.foe_kinds.size()]
	return ""
