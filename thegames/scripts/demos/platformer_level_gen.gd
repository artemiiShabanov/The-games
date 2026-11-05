class_name PlatformerLevelGen
extends RefCounted
## Генератор уровня платформера из сида: детерминирован, проходим без багов. Раскладка по
## правилам пары платформер × 8-bit (каталог демок): ямы, ступени, платформы, враги-ходоки,
## монеты, чекпоинт посередине, флаг в конце. После генерации `passable()` проверяет уровень;
## если не прошёл, генерация повторяется с производным сидом, так что результат всё равно
## зависит только от сида.

const MAX_ATTEMPTS := 8


static func generate(seed_: int, tuning: PlatformerGenTuning = null) -> PlatformerLevel:
	if tuning == null:
		tuning = PlatformerGenTuning.load_default()
	var level: PlatformerLevel
	for attempt in MAX_ATTEMPTS:
		var rng := RandomNumberGenerator.new()
		rng.seed = hash(str(seed_, ":", attempt))
		level = _build(rng, tuning)
		if passable(level, tuning):
			return level
	push_warning("PlatformerLevelGen: сид %d не дал проходимого уровня за %d попыток" % [seed_, MAX_ATTEMPTS])
	return level


static func _build(rng: RandomNumberGenerator, t: PlatformerGenTuning) -> PlatformerLevel:
	var level := PlatformerLevel.new()
	level.width = t.width
	level.height = t.height
	level.columns.resize(t.width)
	level.columns.fill(0)
	var x := 0
	var h := t.base_height
	x = _flat(level, x, t.start_flat, h)
	level.spawn = Vector2i(2, h)
	var checkpoint_set := false
	while x < t.width - t.end_flat - 2:
		var r := rng.randf()
		if r < t.pit_chance:
			var w := rng.randi_range(t.pit_min, t.pit_max)
			if rng.randf() < t.coin_chance:
				for i in w:
					level.coins.append(Vector2i(x + i, h + 2 + (1 if i > 0 and i < w - 1 else 0)))
			x += w
			var landing := rng.randi_range(t.landing_min, t.segment_max)
			x = _segment(level, rng, t, x, landing, h, true)
		else:
			if r < t.pit_chance + t.step_chance:
				var dh := rng.randi_range(1, t.step_max) * (1 if rng.randf() < 0.5 else -1)
				h = clampi(h + dh, t.min_height, t.max_height)
			var length := rng.randi_range(t.segment_min, t.segment_max)
			x = _segment(level, rng, t, x, length, h, false)
		if not checkpoint_set and x >= t.width / 2 and not level.is_pit(x - 2):
			level.checkpoint = Vector2i(x - 2, level.ground_top(x - 2))
			checkpoint_set = true
	x = _flat(level, x, t.width - x, h)
	level.flag = Vector2i(t.width - 6, h)
	if not checkpoint_set:
		var cx := t.width / 2
		while level.is_pit(cx):
			cx += 1
		level.checkpoint = Vector2i(cx, level.ground_top(cx))
	return level


static func _flat(level: PlatformerLevel, x: int, length: int, h: int) -> int:
	for i in length:
		if x + i < level.width:
			level.columns[x + i] = h
	return x + length


## Ровный отрезок с украшениями: враг, платформа над ним, монеты.
static func _segment(level: PlatformerLevel, rng: RandomNumberGenerator, t: PlatformerGenTuning,
		x: int, length: int, h: int, after_pit: bool) -> int:
	var end := mini(x + length, level.width)
	_flat(level, x, end - x, h)
	var real_len := end - x
	if real_len >= t.enemy_min_segment and rng.randf() < t.enemy_chance:
		var e := PlatformerLevel.Enemy.new()
		e.patrol_from = x + 1
		e.patrol_to = end - 2
		e.x = rng.randi_range(e.patrol_from + 1, e.patrol_to - 1) if e.patrol_to - e.patrol_from > 2 else e.patrol_from
		e.y = h
		level.enemies.append(e)
	if real_len >= t.platform_min + 2 and rng.randf() < t.platform_chance:
		var plen := rng.randi_range(t.platform_min, mini(t.platform_max, real_len - 2))
		var px := rng.randi_range(x + 1, end - plen - 1)
		var py := h + rng.randi_range(t.platform_lift_min, t.platform_lift_max)
		level.platforms.append(Rect2i(px, py, plen, 1))
		if rng.randf() < t.coin_chance:
			for i in plen:
				level.coins.append(Vector2i(px + i, py + 2))
	elif not after_pit and real_len >= 4 and rng.randf() < t.coin_chance * 0.6:
		var cx := rng.randi_range(x + 1, end - 3)
		for i in 3:
			level.coins.append(Vector2i(cx + i, h + 1))
	return end


## Проходимость без багов: поиск по поверхностям. Ходьба на соседнюю колонку со ступенью до
## одного ряда вверх, прыжок до `jump_dx` колонок вперёд и `jump_dy` рядов вверх, падение на
## любую глубину. Враги не учитываются: их можно перепрыгнуть.
static func passable(level: PlatformerLevel, t: PlatformerGenTuning) -> bool:
	var start := Vector2i(level.spawn.x, level.ground_top(level.spawn.x))
	var seen := {}
	var queue: Array[Vector2i] = [start]
	seen[start] = true
	while not queue.is_empty():
		var s: Vector2i = queue.pop_front()
		if s.x >= level.flag.x:
			return true
		for d in range(1, t.jump_dx + 1):
			var nx := s.x + d
			if nx >= level.width:
				continue
			for sy in level.surfaces_at(nx):
				var ok := false
				if d == 1 and sy <= s.y + 1:
					ok = true
				elif sy <= s.y + t.jump_dy:
					ok = true
				if ok:
					var n := Vector2i(nx, sy)
					if not seen.has(n):
						seen[n] = true
						queue.append(n)
	return false
