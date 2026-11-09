class_name RacingTrackGen
extends RefCounted
## Генератор трассы гонок × 8-bit из сида: детерминирован. Опорные точки по кругу вокруг
## центра карты с разбросом угла и радиуса, замкнутый сплайн Катмулла-Рома через них,
## средняя линия с равным шагом, старт на почти горизонтальном участке внизу петли. Карта
## тайлов по расстоянию до средней линии: вода, отмель, берег. На воде бочки и рифы у борта,
## средняя линия от них свободна; буи по кромке. `validate()` проверяет замкнутость (линия
## сходится, вода связна, внутри петли остров), длину петли, отступ от краёв, ширину свободной воды, крутизну
## поворотов и что разные участки петли разделены берегом. Не прошла: повтор с производным
## сидом, после `MAX_ATTEMPTS` запасной эллипс без разброса.

const MAX_ATTEMPTS := 16
const TILE := RacingTrack.TILE
## Плотность сэмплов сплайна на отрезок перед пересэмплированием по длине.
const SPLINE_STEPS := 24


static func generate(seed_: int, tuning: RacingGenTuning = null) -> RacingTrack:
	if tuning == null:
		tuning = RacingGenTuning.load_default()
	for attempt in MAX_ATTEMPTS:
		var rng := RandomNumberGenerator.new()
		rng.seed = hash(str(seed_, ":track:", attempt))
		var track := _build(rng, tuning, false)
		if validate(track, tuning) == "":
			track.attempts = attempt + 1
			return track
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":track:fallback"))
	var track := _build(rng, tuning, true)
	track.attempts = MAX_ATTEMPTS + 1
	track.fallback = true
	var why := validate(track, tuning)
	if why != "":
		push_warning("RacingTrackGen: запасная трасса сида %d не прошла проверку: %s" % [seed_, why])
	return track


static func _build(rng: RandomNumberGenerator, t: RacingGenTuning, plain: bool) -> RacingTrack:
	var track := RacingTrack.new()
	track.width = t.width
	track.height = t.height
	track.road_half_px = t.road_half * TILE
	track.side_px = t.side_width * TILE
	var centre := Vector2(t.width, t.height) * TILE / 2.0
	var edge := (t.margin + t.road_half + t.side_width + 1.0) * TILE
	var axes := Vector2(centre.x - edge, centre.y - edge)
	# Опорные точки по кругу; угол растёт, на экране (y вниз) это по часовой.
	var count := 9 if plain else rng.randi_range(t.points_min, t.points_max)
	var ctrl: PackedVector2Array = []
	for i in count:
		var jitter := 0.0 if plain else rng.randf_range(-t.angle_jitter, t.angle_jitter)
		var a := (i + jitter) * TAU / count
		var r := 0.85 if plain else rng.randf_range(t.radius_min, t.radius_max)
		ctrl.append(centre + Vector2(cos(a) * axes.x, sin(a) * axes.y) * r)
	var dense := _spline(ctrl)
	var pts := _resample(dense, t.sample_step)
	# Старт: точка, у которой весь участок решётки и линии финиша (от -12 до +4 точек) почти
	# горизонтален; из таких самая нижняя, иначе самая прямая. Индекс 0 на линии финиша.
	var tang := _tangents(pts)
	var n := pts.size()
	var start := 0
	var best := -INF
	var best_flat := -INF
	var flat_i := 0
	for i in n:
		var flat := INF
		for k in range(-12, 5):
			flat = minf(flat, absf(tang[posmod(i + k, n)].x))
		if flat > best_flat:
			best_flat = flat
			flat_i = i
		if flat >= t.start_straightness - 0.1 and pts[i].y > best:
			best = pts[i].y
			start = i
	if best == -INF:
		start = flat_i
	var rotated: PackedVector2Array = []
	for i in pts.size():
		rotated.append(pts[(start + i) % pts.size()])
	track.points = rotated
	var total := 0.0
	for i in rotated.size():
		total += rotated[i].distance_to(rotated[(i + 1) % rotated.size()])
	track.step_px = total / rotated.size()
	track.tangents = _tangents(rotated)
	for tg in track.tangents:
		track.normals.append(Vector2(-tg.y, tg.x))
	_raster(track, t)
	_place_obstacles(track, rng, t)
	_place_buoys(track, t)
	return track


## Замкнутый сплайн Катмулла-Рома через опорные точки.
static func _spline(ctrl: PackedVector2Array) -> PackedVector2Array:
	var out: PackedVector2Array = []
	var n := ctrl.size()
	for i in n:
		var p0 := ctrl[(i - 1 + n) % n]
		var p1 := ctrl[i]
		var p2 := ctrl[(i + 1) % n]
		var p3 := ctrl[(i + 2) % n]
		for s in SPLINE_STEPS:
			var u := float(s) / SPLINE_STEPS
			var u2 := u * u
			var u3 := u2 * u
			out.append(0.5 * ((2.0 * p1) + (p2 - p0) * u + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * u2
					+ (3.0 * p1 - p0 - 3.0 * p2 + p3) * u3))
	return out


## Точки по замкнутой ломаной с равным шагом по длине.
static func _resample(dense: PackedVector2Array, step: float) -> PackedVector2Array:
	var n := dense.size()
	var total := 0.0
	for i in n:
		total += dense[i].distance_to(dense[(i + 1) % n])
	var count := maxi(int(round(total / step)), 8)
	var spacing := total / count
	var out: PackedVector2Array = [dense[0]]
	var to_next := spacing
	for k in n:
		var a := dense[k]
		var b := dense[(k + 1) % n]
		var seg := a.distance_to(b)
		var at := 0.0
		while seg - at >= to_next and out.size() < count:
			at += to_next
			out.append(a.lerp(b, at / seg))
			to_next = spacing
		to_next -= seg - at
	return out


static func _tangents(pts: PackedVector2Array) -> PackedVector2Array:
	var out: PackedVector2Array = []
	var n := pts.size()
	for i in n:
		out.append((pts[(i + 1) % n] - pts[(i - 1 + n) % n]).normalized())
	return out


## Тайлы по расстоянию центра тайла до ближайшей точки средней линии.
static func _raster(track: RacingTrack, t: RacingGenTuning) -> void:
	var w := track.width
	var h := track.height
	var dist: PackedFloat32Array = []
	dist.resize(w * h)
	dist.fill(INF)
	var reach := int(ceil(t.road_half + t.side_width)) + 1
	for p in track.points:
		var c0 := int(floor(p.x / TILE))
		var r0 := int(floor(p.y / TILE))
		for row in range(maxi(r0 - reach, 0), mini(r0 + reach + 1, h)):
			for col in range(maxi(c0 - reach, 0), mini(c0 + reach + 1, w)):
				var d := p.distance_to(Vector2(col + 0.5, row + 0.5) * TILE)
				var k := row * w + col
				if d < dist[k]:
					dist[k] = d
	track.tiles.resize(w * h)
	for k in w * h:
		var d := dist[k]
		if d <= track.road_half_px:
			track.tiles[k] = RacingTrack.Tile.ROAD
		elif d <= track.road_half_px + track.side_px:
			track.tiles[k] = RacingTrack.Tile.SIDE
		else:
			track.tiles[k] = RacingTrack.Tile.WALL


## Бочки и рифы у борта, по одному на отрезок петли после старта; средняя линия свободна.
static func _place_obstacles(track: RacingTrack, rng: RandomNumberGenerator, t: RacingGenTuning) -> void:
	var n := track.count()
	track.avoid_side.resize(n)
	track.avoid_side.fill(0)
	var from := t.obstacle_clear_start
	var to := n - 16
	if to <= from:
		return
	var count := rng.randi_range(t.obstacles_min, t.obstacles_max)
	var span := float(to - from) / count
	for k in count:
		var o := RacingTrack.Obstacle.new()
		o.index = from + int(span * k + rng.randf_range(0.2, 0.8) * span)
		o.side = 1 if rng.randf() < 0.5 else -1
		o.kind = RacingTrack.Kind.BARREL if rng.randf() < 0.5 else RacingTrack.Kind.ROCK
		o.radius = t.obstacle_radius
		var off := rng.randf_range(t.obstacle_offset_min, t.obstacle_offset_max)
		o.pos = (track.points[o.index] + track.normals[o.index] * off * o.side).round()
		track.obstacles.append(o)
		# Боты за 14 точек до препятствия и чуть после держатся другого борта.
		for i in range(o.index - 14, o.index + 4):
			track.avoid_side[posmod(i, n)] = o.side


## Буи по кромке воды с обеих сторон; только там, где за кромкой отмель, а не чужая вода.
static func _place_buoys(track: RacingTrack, t: RacingGenTuning) -> void:
	var n := track.count()
	for i in range(0, n, maxi(t.buoy_every, 1)):
		if i < 4 or i > n - 12:
			continue
		for s: float in [-1.0, 1.0]:
			var p := (track.points[i] + track.normals[i] * s * (track.road_half_px + 4.0)).round()
			if track.tile_at(p) == RacingTrack.Tile.SIDE:
				track.buoys.append(p)


## Пустая строка, если трасса годится, иначе причина.
static func validate(track: RacingTrack, t: RacingGenTuning) -> String:
	var n := track.count()
	if n * track.step_px < t.min_length_px:
		return "короткая петля: %.0f px" % (n * track.step_px)
	# Замкнутость: последняя точка рядом с первой.
	if track.points[n - 1].distance_to(track.points[0]) > t.sample_step * 1.6:
		return "петля не сходится"
	# Отступ от краёв карты.
	var edge := (t.margin + t.road_half + t.side_width) * TILE
	var size := track.size_px()
	for p in track.points:
		if p.x < edge or p.y < edge or p.x > size.x - edge or p.y > size.y - edge:
			return "трасса у края карты"
	# Старт на почти горизонтальном участке, решётка старта тоже.
	for i in range(-12, 4):
		if absf(track.tangents[posmod(i, n)].x) < t.start_straightness - 0.1:
			return "старт на повороте"
	# Крутизна поворотов.
	var max_turn := deg_to_rad(t.max_turn_deg)
	for i in n:
		if absf(track.tangents[i].angle_to(track.tangents[(i + t.turn_window) % n])) > max_turn:
			return "крутой поворот у точки %d" % i
	# Разные участки петли разделены берегом: срезать нельзя.
	var apart := (2.0 * (t.road_half + t.side_width) + t.min_wall_between) * TILE
	var skip := int(ceil(apart * PI / 2.0 / t.sample_step))
	var apart2 := apart * apart
	for i in n:
		for j in range(i + skip, n):
			if n - (j - i) < skip:
				break
			if track.points[i].distance_squared_to(track.points[j]) < apart2:
				return "участки %d и %d слишком близко" % [i, j]
	# Внутри петли остров: центр карты берег.
	if track.tile_at(size / 2.0) != RacingTrack.Tile.WALL:
		return "внутри петли нет острова"
	# Связность: от финиша по воде и отмели доходим до всех точек средней линии.
	var seen := _flood(track, track.points[0])
	for p in track.points:
		var k := int(floor(p.y / TILE)) * track.width + int(floor(p.x / TILE))
		if not seen[k]:
			return "вода не связна"
	# Ширина: поперёк трассы свободной от препятствий воды не меньше `min_free_width`.
	var need := t.min_free_width * TILE
	for i in n:
		var run := 0.0
		var best := 0.0
		var x := -track.road_half_px
		while x <= track.road_half_px:
			var p := track.points[i] + track.normals[i] * x
			var free := track.tile_at(p) == RacingTrack.Tile.ROAD
			if free:
				for o in track.obstacles:
					if absi(track.wrap_delta(o.index - i)) < 4 and p.distance_to(o.pos) < o.radius + 1.0:
						free = false
						break
			run = run + 2.0 if free else 0.0
			best = maxf(best, run)
			x += 2.0
		if best < need:
			return "узко у точки %d: %.0f px" % [i, best]
	return ""


static func _flood(track: RacingTrack, from: Vector2) -> PackedByteArray:
	var w := track.width
	var seen: PackedByteArray = []
	seen.resize(w * track.height)
	seen.fill(0)
	var start := Vector2i(int(floor(from.x / TILE)), int(floor(from.y / TILE)))
	var stack: Array[Vector2i] = [start]
	seen[start.y * w + start.x] = 1
	while not stack.is_empty():
		var c: Vector2i = stack.pop_back()
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var nb: Vector2i = c + d
			if track.tile(nb.x, nb.y) == RacingTrack.Tile.WALL:
				continue
			var k := nb.y * w + nb.x
			if seen[k]:
				continue
			seen[k] = 1
			stack.append(nb)
	return seen
