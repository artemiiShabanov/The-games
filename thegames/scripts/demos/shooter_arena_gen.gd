class_name ShooterArenaGen
extends RefCounted
## Генератор арены и волн шутера × 8-bit из сида: детерминирован. Палуба в борту на весь экран,
## по трапу на каждой стороне (позиция по сиду, сверху мимо углов под HUD), пропы (бочки,
## сундуки, пушки) на палубе не у борта, не у старта героя, не перед трапами и не вплотную
## друг к другу. Волны растут от первой к последней, доля канониров тоже растёт, трап у
## каждого врага по сиду. `validate()` проверяет, что палуба связна (до каждой её клетки и
## каждого трапа дойти от старта), старт и места перед трапами свободны, пропов сколько
## задано, врагов хватает на цель. Не прошла: повтор с производным сидом, после
## `MAX_ATTEMPTS` арена без пропов.

const MAX_ATTEMPTS := 16
const TILE := ShooterArena.TILE


static func generate(seed_: int, tuning: ShooterGenTuning = null) -> ShooterArena:
	if tuning == null:
		tuning = ShooterGenTuning.load_default()
	for attempt in MAX_ATTEMPTS:
		var rng := RandomNumberGenerator.new()
		rng.seed = hash(str(seed_, ":arena:", attempt))
		var arena := _build(rng, tuning, false)
		if validate(arena, tuning) == "":
			arena.attempts = attempt + 1
			return arena
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":arena:fallback"))
	var arena := _build(rng, tuning, true)
	arena.attempts = MAX_ATTEMPTS + 1
	arena.fallback = true
	var why := validate(arena, tuning)
	if why != "":
		push_warning("ShooterArenaGen: запасная арена сида %d не прошла проверку: %s" % [seed_, why])
	return arena


static func _build(rng: RandomNumberGenerator, t: ShooterGenTuning, plain: bool) -> ShooterArena:
	var a := ShooterArena.new()
	a.width = t.width
	a.height = t.height
	a.tiles.resize(a.width * a.height)
	for row in a.height:
		for col in a.width:
			var edge := row == 0 or col == 0 or row == a.height - 1 or col == a.width - 1
			a.set_tile(col, row, ShooterArena.Tile.WALL if edge else ShooterArena.Tile.FLOOR)
	# Трапы: верх, право, низ, лево.
	var top := rng.randi_range(t.door_margin_cols, a.width - 1 - t.door_margin_cols)
	var bottom := rng.randi_range(t.door_margin_cols, a.width - 1 - t.door_margin_cols)
	var right := rng.randi_range(t.door_margin_rows, a.height - 1 - t.door_margin_rows)
	var left := rng.randi_range(t.door_margin_rows, a.height - 1 - t.door_margin_rows)
	a.doors = [Vector2i(top, 0), Vector2i(a.width - 1, right), Vector2i(bottom, a.height - 1), Vector2i(0, left)]
	a.door_dirs = [Vector2i(0, 1), Vector2i(-1, 0), Vector2i(0, -1), Vector2i(1, 0)]
	for d in a.doors:
		a.set_tile(d.x, d.y, ShooterArena.Tile.DOOR)
	if not plain:
		_place_props(a, rng, t)
	_make_waves(a, rng, t)
	return a


static func _place_props(a: ShooterArena, rng: RandomNumberGenerator, t: ShooterGenTuning) -> void:
	var want := rng.randi_range(t.props_min, t.props_max)
	var start := a.start_cell()
	var tries := 0
	while a.props.size() < want and tries < 200:
		tries += 1
		var c := Vector2i(rng.randi_range(t.prop_wall_gap, a.width - 1 - t.prop_wall_gap),
				rng.randi_range(t.prop_wall_gap, a.height - 1 - t.prop_wall_gap))
		if _cheb(c, start) <= t.clear_center or _near_door(a, c, t.clear_door):
			continue
		var crowded := false
		for p in a.props:
			if _cheb(p.cell, c) <= 1:
				crowded = true
				break
		if crowded:
			continue
		var p := ShooterArena.Prop.new()
		p.cell = c
		p.kind = rng.randi_range(0, ShooterArena.Kind.size() - 1) as ShooterArena.Kind
		a.props.append(p)
		a.set_tile(c.x, c.y, ShooterArena.Tile.PROP)


## Волна `i`: размер растёт на `wave_growth` с разбросом, доля канониров от первой к последней.
static func _make_waves(a: ShooterArena, rng: RandomNumberGenerator, t: ShooterGenTuning) -> void:
	for i in t.waves:
		var w := ShooterArena.Wave.new()
		var n := maxi(2, t.wave_first + int(round(i * t.wave_growth)) + rng.randi_range(-t.wave_jitter, t.wave_jitter))
		var k := float(i) / maxf(t.waves - 1, 1)
		var share := lerpf(t.gunner_share_first, t.gunner_share_last, k)
		for j in n:
			var s := ShooterArena.Spawn.new()
			s.kind = ShooterArena.Enemy.GUNNER if rng.randf() < share else ShooterArena.Enemy.WALKER
			s.door = rng.randi_range(0, a.doors.size() - 1)
			w.spawns.append(s)
		a.waves.append(w)


static func _cheb(a: Vector2i, b: Vector2i) -> int:
	return maxi(absi(a.x - b.x), absi(a.y - b.y))


## Клетка `c` ближе `gap` к клетке перед любым трапом.
static func _near_door(a: ShooterArena, c: Vector2i, gap: int) -> bool:
	for i in a.doors.size():
		if _cheb(c, a.doors[i] + a.door_dirs[i]) <= gap:
			return true
	return false


## Пустая строка, если арена годится, иначе причина.
static func validate(a: ShooterArena, t: ShooterGenTuning) -> String:
	if a.width != t.width or a.height != t.height or a.tiles.size() != a.width * a.height:
		return "размер арены"
	var start := a.start_cell()
	if a.tile(start.x, start.y) != ShooterArena.Tile.FLOOR:
		return "старт героя занят"
	for p in a.props:
		if _cheb(p.cell, start) <= t.clear_center:
			return "проп у старта %s" % p.cell
		if _near_door(a, p.cell, t.clear_door):
			return "проп перед трапом %s" % p.cell
	if not a.fallback and (a.props.size() < t.props_min or a.props.size() > t.props_max):
		return "пропов %d" % a.props.size()
	if a.doors.size() != 4:
		return "трапов %d" % a.doors.size()
	var dist := a.distances(start)
	for row in a.height:
		for col in a.width:
			var tt := a.tile(col, row)
			if (tt == ShooterArena.Tile.FLOOR or tt == ShooterArena.Tile.DOOR) and dist[row * a.width + col] < 0:
				return "клетка %d,%d отрезана" % [col, row]
	for i in a.doors.size():
		var inside := a.doors[i] + a.door_dirs[i]
		if a.tile(inside.x, inside.y) != ShooterArena.Tile.FLOOR:
			return "перед трапом %d не палуба" % i
	if a.total_enemies() < t.enemies_min_total:
		return "врагов %d меньше %d" % [a.total_enemies(), t.enemies_min_total]
	return ""
