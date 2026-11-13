class_name HookLevelGen
extends RefCounted
## Генератор уровня «крюк-кошки» (#121) из сида. Островки идут друг за другом, на каждом путь
## поворачивает. Сложность растёт по пропастям: сначала одно кольцо, потом цепочки из двух и
## трёх без опоры между ними, перепады высоты островков и колец, под конец кольца ходят
## вверх-вниз, а островки бывают маленькими. Уровень сида это первая попытка, что проходит
## `validate` и которую бот WIN проходит до маяка, потеряв не больше одной жизни.

const ATTEMPTS := 80


static func generate(seed_: int, t: PlatformerThreedGenTuning = null, rules: PlatformerThreedTuning = null) -> HookLevel:
	if t == null:
		t = PlatformerThreedGenTuning.load_default()
	if rules == null:
		rules = PlatformerThreedTuning.load_default()
	var level: HookLevel = null
	for attempt in ATTEMPTS:
		level = _build(seed_, attempt, t)
		if validate(level, t, rules) != "":
			continue
		var bot := HookSim.simulate(level, rules, AutoTest.BotMode.WIN)
		if bot.finished and bot.lives >= rules.lives - 1:
			break
	return level


static func _build(seed_: int, attempt: int, t: PlatformerThreedGenTuning) -> HookLevel:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":hook:", attempt))
	var level := HookLevel.new()
	var first := HookLevel.Islet.new()
	first.radius = t.islet + 0.6
	level.islets.append(first)
	var side := 1.0 if rng.randf() < 0.5 else -1.0
	for g in t.gaps:
		var from := level.islets[g]
		var last := g == t.gaps - 1
		var count := 1
		if g >= t.triple_from and rng.randf() < 0.45:
			count = 3
		elif g >= t.double_from and rng.randf() < 0.7:
			count = 2
		var to := HookLevel.Islet.new()
		to.radius = t.islet + 0.9 if last else (t.islet_small if g >= t.small_from and rng.randf() < t.small_share else t.islet)
		to.y = clampf(from.y + (rng.randf_range(-t.islet_rise, t.islet_rise) if g >= t.height_from else 0.0), 0.0, 5.0)
		var at := from.s + from.radius + t.ring_lead * rng.randf_range(0.9, 1.1)
		var mover := rng.randi_range(0, count - 1) if g >= t.moving_from and rng.randf() < t.moving_share else -1
		for k in count:
			var ring := HookLevel.Ring.new()
			ring.s = at
			ring.gap = g
			ring.y = lerpf(from.y, to.y, (k + 0.5) / count) + rng.randf_range(t.ring_height_min, t.ring_height_max) \
					+ (rng.randf_range(-t.ring_rise, t.ring_rise) if g >= t.height_from and count > 1 else 0.0)
			if k == mover:
				ring.amp = t.moving_amp
				ring.period = t.moving_period * rng.randf_range(0.9, 1.15)
				ring.phase = rng.randf_range(0.0, TAU)
			level.rings.append(ring)
			if k < count - 1:
				at += rng.randf_range(t.ring_step_min, t.ring_step_max)
		to.s = at + t.ring_lead * rng.randf_range(0.95, 1.25) + to.radius
		# Путь поворачивает на островке, чаще в разные стороны.
		from.yaw = clampf((level.islets[g - 1].yaw if g > 0 else 0.0) + side * deg_to_rad(rng.randf_range(t.turn_min, t.turn_max)),
				-deg_to_rad(t.heading_limit), deg_to_rad(t.heading_limit))
		if rng.randf() < 0.7:
			side = -side
		var f := Vector3(-sin(from.yaw), 0.0, -cos(from.yaw))
		to.pos = from.pos + f * (to.s - from.s)
		to.yaw = from.yaw
		level.islets.append(to)
	return level


## Пусто, если уровень годится; иначе что не так.
static func validate(level: HookLevel, t: PlatformerThreedGenTuning = null, rules: PlatformerThreedTuning = null) -> String:
	if t == null:
		t = PlatformerThreedGenTuning.load_default()
	if rules == null:
		rules = PlatformerThreedTuning.load_default()
	if level.gaps() != t.gaps:
		return "пропастей %d" % level.gaps()
	for g in level.gaps():
		var ids := level.rings_of(g)
		if ids.is_empty():
			return "пропасть %d без колец" % g
		# Соседние кольца цепочки достаются одной верёвкой с запасом.
		for k in range(1, ids.size()):
			var a := level.rings[ids[k - 1]]
			var b := level.rings[ids[k]]
			if Vector2(b.s - a.s, b.y - a.y).length() > rules.rope_max * 1.45:
				return "кольца %d и %d слишком далеко" % [ids[k - 1], ids[k]]
	if level.longest_chain() < 3:
		return "нет цепочки из трёх колец"
	if level.moving() < 1:
		return "нет движущихся колец"
	if level.small() < 1:
		return "нет маленьких островков"
	if level.rings_of(0).size() != 1 or level.rings[level.rings_of(0)[0]].amp > 0.0:
		return "первая пропасть не простая"
	return ""
