class_name VectorShapes
extends RefCounted
## Контуры векторных демок (#88) из силуэтов 8-bit спрайтов: так у трёх сеттингов сразу есть
## все слоты без нового рисунка (`demos_catalog.md`, формат слота «Вектор»). Силуэт это
## пиксели с альфой; по границе «залито / пусто» собираются замкнутые обходы по рёбрам
## пикселей, лесенки упрощаются (Рамер — Дуглас — Пекер, `EPSILON`), мелкие обходы (точки,
## дырки в один пиксель) отбрасываются. Внутренние обходы (глаза, окна) остаются: они дают
## контуру деталь. Точки в пикселях спрайта относительно его центра; кэш по пути текстуры.

const EPSILON := 0.75
## Обход короче этого периметра в пикселях (точка, дырка в пиксель) не рисуется.
const MIN_PERIMETER := 6.0

static var _cache: Dictionary[String, Array] = {}


## Контуры спрайта: замкнутые ломаные в пикселях от центра спрайта.
static func of_texture(tex: Texture2D) -> Array[PackedVector2Array]:
	var out: Array[PackedVector2Array] = []
	if tex == null:
		return out
	var key := tex.resource_path
	if key != "" and _cache.has(key):
		out.assign(_cache[key])
		return out
	out = trace(tex.get_image())
	if key != "":
		_cache[key] = out
	return out


## Обходы силуэта картинки, упрощённые и сдвинутые к центру.
static func trace(img: Image) -> Array[PackedVector2Array]:
	var w := img.get_width()
	var h := img.get_height()
	var filled := func(x: int, y: int) -> bool:
		return x >= 0 and y >= 0 and x < w and y < h and img.get_pixel(x, y).a > 0.5
	# Направленные рёбра по часовой (y вниз): залитое всегда справа от ребра.
	var edges: Dictionary[Vector2i, Array] = {}
	var add := func(a: Vector2i, b: Vector2i) -> void:
		if not edges.has(a):
			edges[a] = []
		edges[a].append(b)
	for y in h:
		for x in w:
			if not filled.call(x, y):
				continue
			if not filled.call(x, y - 1):
				add.call(Vector2i(x, y), Vector2i(x + 1, y))
			if not filled.call(x + 1, y):
				add.call(Vector2i(x + 1, y), Vector2i(x + 1, y + 1))
			if not filled.call(x, y + 1):
				add.call(Vector2i(x + 1, y + 1), Vector2i(x, y + 1))
			if not filled.call(x - 1, y):
				add.call(Vector2i(x, y + 1), Vector2i(x, y))
	var center := Vector2(w, h) / 2.0
	var out: Array[PackedVector2Array] = []
	while not edges.is_empty():
		var start: Vector2i = edges.keys()[0]
		var loop: Array[Vector2i] = [start]
		var at := start
		while true:
			var nexts: Array = edges.get(at, [])
			if nexts.is_empty():
				break
			var nxt: Vector2i = nexts.pop_back()
			if nexts.is_empty():
				edges.erase(at)
			if nxt == start:
				break
			loop.append(nxt)
			at = nxt
		if _perimeter(loop) < MIN_PERIMETER:
			continue
		var pts := PackedVector2Array()
		for p in _simplify(_drop_collinear(loop)):
			pts.append(Vector2(p) - center)
		if pts.size() >= 3:
			out.append(pts)
	return out


static func _perimeter(loop: Array[Vector2i]) -> float:
	return float(loop.size())


static func _drop_collinear(loop: Array[Vector2i]) -> Array[Vector2]:
	var out: Array[Vector2] = []
	var n := loop.size()
	for i in n:
		var a := Vector2(loop[(i - 1 + n) % n])
		var b := Vector2(loop[i])
		var c := Vector2(loop[(i + 1) % n])
		if absf((b - a).cross(c - b)) > 0.001:
			out.append(b)
	return out


## Замкнутая ломаная по Рамеру — Дугласу — Пекеру: делится в двух дальних друг от друга
## точках, половины упрощаются как открытые.
static func _simplify(pts: Array[Vector2]) -> Array[Vector2]:
	if pts.size() < 4:
		return pts
	var far := 0
	var best := -1.0
	for i in pts.size():
		var d := pts[0].distance_squared_to(pts[i])
		if d > best:
			best = d
			far = i
	var first: Array[Vector2] = []
	first.assign(pts.slice(0, far + 1))
	var second: Array[Vector2] = []
	second.assign(pts.slice(far))
	second.append(pts[0])
	var a := _rdp(first)
	var b := _rdp(second)
	a.pop_back()
	b.pop_back()
	a.append_array(b)
	return a


static func _rdp(pts: Array[Vector2]) -> Array[Vector2]:
	if pts.size() < 3:
		return pts
	var a := pts[0]
	var b := pts[pts.size() - 1]
	var idx := 0
	var dmax := 0.0
	for i in range(1, pts.size() - 1):
		var d := _dist_to_segment(pts[i], a, b)
		if d > dmax:
			dmax = d
			idx = i
	if dmax <= EPSILON:
		return [a, b]
	var left: Array[Vector2] = []
	left.assign(pts.slice(0, idx + 1))
	var right: Array[Vector2] = []
	right.assign(pts.slice(idx))
	var l := _rdp(left)
	var r := _rdp(right)
	l.pop_back()
	l.append_array(r)
	return l


static func _dist_to_segment(p: Vector2, a: Vector2, b: Vector2) -> float:
	var ab := b - a
	var len2 := ab.length_squared()
	if len2 < 0.0001:
		return p.distance_to(a)
	var t := clampf((p - a).dot(ab) / len2, 0.0, 1.0)
	return p.distance_to(a + ab * t)
