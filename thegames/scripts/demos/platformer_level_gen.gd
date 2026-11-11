class_name PlatformerLevelGen
extends RefCounted
## Генератор уровня платформера из сида: детерминирован, проходим без багов. Раскладка по
## правилам пары платформер × 8-bit (каталог демок): ямы (часть шире прыжка, под рывок),
## ступени, платформы в один-два яруса, враги-ходоки на земле и на платформах, летуны-попугаи
## над землёй, монеты, чекпоинт посередине, флаг в конце. Плотнее
## после плейтеста 2026-11-06: короче отрезки, больше платформ и врагов. После генерации
## `passable()` проверяет, что флаг и каждая платформа достижимы обычным прыжком; если нет,
## генерация повторяется с производным сидом, так что результат всё равно зависит только от сида.

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
			if rng.randf() < t.dash_pit_chance and x - _last_walker_end(level) >= t.dash_pit_gap:
				w = rng.randi_range(t.dash_pit_min, t.dash_pit_max)
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
		e.flying = real_len >= t.flyer_min_segment and rng.randf() < t.flyer_share
		if e.flying:
			e.patrol_from = x + 3
			e.patrol_to = end - 3
		else:
			# Ходок не у краёв отрезка: приземление с прыжка через яму или ступеньку должно быть
			# свободно (плейтест 2026-11-06).
			e.patrol_from = x + 3
			e.patrol_to = end - 2
		e.x = rng.randi_range(e.patrol_from + 1, e.patrol_to - 1) if e.patrol_to - e.patrol_from > 2 else e.patrol_from
		e.y = h + t.flyer_height if e.flying else h
		level.enemies.append(e)
	if real_len >= t.platform_min + 2 and rng.randf() < t.platform_chance:
		var plen := rng.randi_range(t.platform_min, mini(t.platform_max, real_len - 2))
		var px := rng.randi_range(x + 1, end - plen - 1)
		var py := h + rng.randi_range(t.platform_lift_min, t.platform_lift_max)
		_platform(level, rng, t, px, py, plen, false)
		if rng.randf() < t.platform_second_chance and py + 1 + t.jump_dy - 1 + 1 < level.height - 2:
			# Второй ярус: начинается над первым со сдвигом вправо, выше на jump_dy − 1 рядов
			# стояния, так что с первого яруса на него есть прыжок.
			var plen2 := rng.randi_range(t.platform_min, t.platform_max)
			var px2 := px + rng.randi_range(1, plen)
			var py2 := py + t.jump_dy - 1
			_platform(level, rng, t, px2, py2, plen2, true)
	elif not after_pit and real_len >= 4 and rng.randf() < t.coin_chance * 0.6:
		var cx := rng.randi_range(x + 1, end - 3)
		for i in 3:
			level.coins.append(Vector2i(cx + i, h + 1))
	return end


## Правый край патруля последнего ходока на земле; −100, если ходоков ещё нет.
static func _last_walker_end(level: PlatformerLevel) -> int:
	var out := -100
	for e in level.enemies:
		if not e.flying:
			out = maxi(out, e.patrol_to)
	return out


## Платформа с монетами над ней и, если длинная и `with_enemy`, ходоком по ней. Ходоки только на
## втором ярусе: он выше прыжка с земли, иначе прыжок под платформой упирался бы головой во врага.
static func _platform(level: PlatformerLevel, rng: RandomNumberGenerator, t: PlatformerGenTuning,
		px: int, py: int, plen: int, with_enemy: bool) -> void:
	plen = mini(plen, level.width - 1 - px)
	if plen < 2:
		return
	level.platforms.append(Rect2i(px, py, plen, 1))
	if rng.randf() < t.coin_chance:
		for i in plen:
			level.coins.append(Vector2i(px + i, py + 2))
	if with_enemy and plen >= 3 and rng.randf() < t.platform_enemy_chance:
		var e := PlatformerLevel.Enemy.new()
		e.patrol_from = px
		e.patrol_to = px + plen - 1
		e.x = px + plen / 2
		e.y = py + 1
		level.enemies.append(e)


## Проходимость без багов: поиск по поверхностям. Ходьба на соседнюю колонку со ступенью до
## одного ряда вверх, прыжок до `jump_dx` колонок вперёд и `jump_dy` рядов вверх, с дэшем ещё
## `dash_dx` колонок, но не выше двух рядов, падение на любую глубину. Враги не учитываются: их можно перепрыгнуть. Кроме флага достижимой должна
## быть каждая платформа (плейтест 2026-11-06: «не допрыгнуть» это баг только по флагу).
static func passable(level: PlatformerLevel, t: PlatformerGenTuning) -> bool:
	var start := Vector2i(level.spawn.x, level.ground_top(level.spawn.x))
	var seen := {}
	var queue: Array[Vector2i] = [start]
	seen[start] = true
	var flag_reached := false
	while not queue.is_empty():
		var s: Vector2i = queue.pop_front()
		if s.x >= level.flag.x:
			flag_reached = true
			continue
		for d in range(1, t.jump_dx + t.dash_dx + 1):
			var nx := s.x + d
			if nx >= level.width:
				continue
			for sy in level.surfaces_at(nx):
				var ok := false
				if d == 1 and sy <= s.y + 1:
					ok = true
				elif d <= t.jump_dx and sy <= s.y + t.jump_dy:
					ok = true
				elif d > t.jump_dx and sy <= s.y + 2:
					ok = true
				if ok:
					var n := Vector2i(nx, sy)
					if not seen.has(n):
						seen[n] = true
						queue.append(n)
	if not flag_reached:
		return false
	for p in level.platforms:
		var ok := false
		for i in p.size.x:
			if seen.has(Vector2i(p.position.x + i, p.position.y + 1)):
				ok = true
				break
		if not ok:
			return false
	return true
