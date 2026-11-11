class_name TowerLevelGen
extends RefCounted
## Генератор этажей платформера × вектор из сида (#90): детерминирован. На каждой линии одна
## или две дыры одной скорости и направления (на одной линии они не догоняют друг друга),
## соседние линии чаще едут навстречу и никогда вровень; на каждом этаже, кроме верхнего, один или два врага
## одной скорости; монеты россыпью по этажам; флаг на верхнем. Уровень проходим всегда: дыры
## не стоят и экран замкнут, значит под любую дыру можно встать; `validate` проверяет раскладку.


static func generate(seed_: int, t: PlatformerVectorGenTuning = null) -> TowerLevel:
	if t == null:
		t = PlatformerVectorGenTuning.load_default()
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":tower"))
	var lv := TowerLevel.new()
	lv.width = t.width
	lv.floors = t.floors
	lv.start_x = t.width * rng.randf_range(t.edge_margin * 2.0, 1.0 - t.edge_margin * 2.0)
	lv.flag_x = t.width * rng.randf_range(t.edge_margin, 1.0 - t.edge_margin)
	var dir := 1.0 if rng.randf() < 0.5 else -1.0
	var prev_speed := 0.0
	for line in range(1, t.floors + 1):
		var k := float(line - 1) / maxf(t.floors - 1, 1.0)
		if rng.randf() < t.alternate_chance:
			dir = -dir
		var speed := lerpf(t.hole_speed_low, t.hole_speed_high, k) * dir \
				* rng.randf_range(1.0 - t.hole_speed_jitter, 1.0 + t.hole_speed_jitter)
		# Соседние линии не едут вровень: иначе дыра над дырой висит минутами.
		if absf(speed - prev_speed) < t.hole_speed_gap:
			speed = prev_speed + t.hole_speed_gap * dir
		prev_speed = speed
		var x0 := rng.randf() * t.width
		var count := 2 if rng.randf() < lerpf(t.two_holes_low, t.two_holes_high, k) else 1
		for i in count:
			var h := TowerLevel.Hole.new()
			h.line = line
			h.speed = speed
			h.width = lerpf(t.hole_width_low, t.hole_width_high, k)
			h.x = fposmod(x0 + i * t.width * rng.randf_range(0.42, 0.58), t.width)
			lv.holes.append(h)
	for level in t.floors:
		var speed := rng.randf_range(t.enemy_speed_min, t.enemy_speed_max) * (1.0 if rng.randf() < 0.5 else -1.0)
		var x0 := rng.randf() * t.width
		if level == 0:
			# На земле враг стартует на другой стороне круга от героя.
			x0 = fposmod(lv.start_x + t.width / 2.0 + rng.randf_range(-0.5, 0.5) * (t.width - 2.0 * t.enemy_start_gap), t.width)
		var count := 2 if level >= t.enemy_second_from and rng.randf() < t.enemy_second_chance else 1
		for i in count:
			var e := TowerLevel.Enemy.new()
			e.level = level
			e.speed = speed
			e.x = fposmod(x0 + i * t.width * rng.randf_range(0.42, 0.58), t.width)
			lv.enemies.append(e)
		for i in t.coins_per_level:
			lv.coins.append(Vector2(t.width * (i + rng.randf_range(0.15, 0.85)) / t.coins_per_level, level))
	return lv


## Проверка раскладки: "" или причина. Дыры есть на каждой линии, не стоят и не слипаются,
## враги не на верхнем этаже и не стартуют рядом с героем, всё в пределах экрана.
static func validate(lv: TowerLevel, t: PlatformerVectorGenTuning) -> String:
	if lv.floors != t.floors or lv.floors < 2:
		return "этажей %d" % lv.floors
	for line in range(1, lv.floors + 1):
		var hs := lv.holes_of(line)
		if hs.is_empty() or hs.size() > 2:
			return "на линии %d дыр %d" % [line, hs.size()]
		for h in hs:
			if absf(h.speed) < 10.0:
				return "дыра линии %d стоит" % line
			if h.width < 100.0 or h.width > lv.width / 4.0:
				return "дыра линии %d шириной %.0f" % [line, h.width]
			if h.x < 0.0 or h.x >= lv.width:
				return "дыра линии %d за экраном" % line
		if line > 1 and absf(hs[0].speed - lv.holes_of(line - 1)[0].speed) < t.hole_speed_gap - 0.01:
			return "линии %d и %d едут вровень" % [line - 1, line]
		if hs.size() == 2:
			if not is_equal_approx(hs[0].speed, hs[1].speed):
				return "дыры линии %d едут с разной скоростью" % line
			if absf(TowerLevel.wrap_delta(hs[0].x, hs[1].x, lv.width)) < hs[0].width * 2.0:
				return "дыры линии %d слиплись" % line
	for level in lv.floors:
		if lv.enemies_of(level).is_empty():
			return "на этаже %d нет врага" % level
	for e in lv.enemies:
		if e.level < 0 or e.level >= lv.floors:
			return "враг на этаже %d" % e.level
		if absf(e.speed) < t.enemy_speed_min - 0.01 or absf(e.speed) > t.enemy_speed_max + 0.01:
			return "враг со скоростью %.0f" % e.speed
		if e.level == 0 and absf(TowerLevel.wrap_delta(lv.start_x, e.x, lv.width)) < t.enemy_start_gap - 0.01:
			return "враг стартует у героя"
	if lv.coins.size() != t.coins_per_level * lv.floors:
		return "монет %d" % lv.coins.size()
	for c in lv.coins:
		if c.x < 0.0 or c.x >= lv.width or c.y < 0.0 or c.y >= lv.floors:
			return "монета вне этажей"
	if lv.flag_x < lv.width * t.edge_margin - 0.01 or lv.flag_x > lv.width * (1.0 - t.edge_margin) + 0.01:
		return "флаг у края"
	return ""
