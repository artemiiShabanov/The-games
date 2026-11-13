class_name HookLevelGen
extends RefCounted
## Генератор уровня «крюк-кошки» (#121) из сида. Острова идут друг за другом, на каждом путь
## поворачивает. Большая часть пропастей с кольцами, между ними перерывы: простые прыжки,
## уступы и секция маленьких камней. Сложность растёт: одно кольцо, цепочки из двух и трёх,
## перепады высоты, кольца ходят вверх-вниз, остров для посадки мельче. Уровень сида это первая
## попытка, что проходит `validate` и которую бот WIN проходит до маяка, потеряв не больше
## одной жизни.

const ATTEMPTS := 80
## Реквизит: радиус и высота столба коллизии.
const PROPS := {"palm": Vector2(0.25, 4.4), "barrel": Vector2(0.4, 0.86), "crate": Vector2(0.5, 0.85), "rock": Vector2(0.62, 0.7),
		"chest": Vector2(0.42, 0.6), "lighthouse": Vector2(1.5, 9.0)}
const PROP_NAMES := ["palm", "barrel", "crate", "rock", "chest", "palm", "rock"]


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


## План пропастей: вид, сколько колец, движется ли одно, перепад высоты, куда садиться
## (`land` большой остров, `stone` камень, `late` остров поменьше, `last` маяк).
static func _plan(rng: RandomNumberGenerator) -> Array[Dictionary]:
	var J := HookLevel.Kind.JUMP
	var C := HookLevel.Kind.CLIMB
	var R := HookLevel.Kind.RINGS
	var plan: Array[Dictionary] = [
		{"kind": J, "to": "land"},
		{"kind": R, "rings": 1, "to": "land"},
		{"kind": R, "rings": 1 if rng.randf() < 0.6 else 2, "to": "land"},
		{"kind": C, "to": "land"},
		{"kind": R, "rings": 2, "to": "land"},
		{"kind": J, "to": "stone"},
		{"kind": J, "to": "stone"},
	]
	if rng.randf() < 0.5:
		plan.append({"kind": J, "to": "stone"})
	plan.append_array([
		{"kind": J, "to": "land"},
		{"kind": R, "rings": 2, "high": true, "to": "land"},
		{"kind": C, "to": "land"},
		{"kind": R, "rings": 3, "high": true, "to": "late"},
		{"kind": R, "rings": 2, "high": true, "moving": true, "to": "land"},
		{"kind": J, "to": "land"},
		{"kind": R, "rings": 3, "high": true, "moving": true, "to": "last"},
	])
	# Уступ и вторая пропасть с кольцом иногда меняются местами.
	if rng.randf() < 0.5:
		var keep := plan[2]
		plan[2] = plan[3]
		plan[3] = keep
	return plan


static func _islet(rng: RandomNumberGenerator, radius: float, wobble: float) -> HookLevel.Islet:
	var it := HookLevel.Islet.new()
	it.radius = radius
	it.waves = PackedFloat32Array([wobble * rng.randf_range(0.5, 1.0), rng.randf_range(0.0, TAU), wobble * rng.randf_range(0.3, 0.8),
			rng.randf_range(0.0, TAU), wobble * rng.randf_range(0.2, 0.5), rng.randf_range(0.0, TAU)])
	return it


static func _build(seed_: int, attempt: int, t: PlatformerThreedGenTuning) -> HookLevel:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":hook3d:", attempt))
	var level := HookLevel.new()
	level.islets.append(_islet(rng, t.land_min + 0.6, t.wobble))
	var plan := _plan(rng)
	var heading := 0.0
	var side := 1.0 if rng.randf() < 0.5 else -1.0
	for g in plan.size():
		var item := plan[g]
		var kind: HookLevel.Kind = item["kind"]
		var to_kind: String = item["to"]
		var from := level.islets[g]
		# Путь поворачивает на острове, чаще в разные стороны; между камнями почти прямо.
		if g > 0:
			var small := from.radius < 2.2
			heading = clampf(heading + side * (rng.randf_range(8.0, 22.0) if small else rng.randf_range(t.turn_min, t.turn_max)),
					-t.heading_limit, t.heading_limit)
			if rng.randf() < 0.65:
				side = -side
		var yaw := deg_to_rad(heading)
		var dir := Vector2(-sin(yaw), -cos(yaw))
		var radius := rng.randf_range(t.land_min, t.land_max)
		match to_kind:
			"stone":
				radius = t.stone * rng.randf_range(0.9, 1.15)
			"late":
				radius = t.land_late
			"last":
				radius = t.land_min + 1.0
		var to := _islet(rng, radius, t.wobble * (0.5 if radius < 2.2 else 1.0))
		var gap := HookLevel.Gap.new()
		gap.kind = kind
		gap.dir = dir
		var reach := from.edge(dir)
		gap.a = from.pos + Vector3(dir.x, 0.0, dir.y) * reach
		var span := 0.0
		var rise := 0.0
		var marks: Array[float] = []
		match kind:
			HookLevel.Kind.JUMP:
				var stones := to_kind == "stone" or from.radius < 2.2
				span = rng.randf_range(t.stone_gap_min, t.stone_gap_max) if stones else rng.randf_range(t.jump_min, t.jump_max)
				rise = rng.randf_range(-t.jump_drop, 0.2)
			HookLevel.Kind.CLIMB:
				span = rng.randf_range(t.climb_gap_min, t.climb_gap_max)
				rise = rng.randf_range(t.climb_rise_min, t.climb_rise_max)
			HookLevel.Kind.RINGS:
				span = rng.randf_range(t.ring_lead_min, t.ring_lead_max)
				for k in int(item["rings"]):
					marks.append(span)
					if k < int(item["rings"]) - 1:
						span += rng.randf_range(t.ring_step_min, t.ring_step_max)
				span += rng.randf_range(t.ring_out_min, t.ring_out_max)
				rise = rng.randf_range(-t.ring_rise, t.ring_rise) if item.get("high", false) else rng.randf_range(-0.4, 0.4)
				# Высоко забравшись, путь идёт вниз.
				if from.pos.y > t.height_max - 2.5:
					rise = -absf(rise)
		var top := from.pos.y + rise
		if kind != HookLevel.Kind.CLIMB:
			top = clampf(top, 0.0, t.height_max)
		gap.b = gap.a + Vector3(dir.x, 0.0, dir.y) * span
		gap.b.y = top
		to.pos = gap.b + Vector3(dir.x, 0.0, dir.y) * to.edge(-dir)
		var mover := rng.randi_range(0, marks.size() - 1) if item.get("moving", false) else -1
		for k in marks.size():
			var ring := HookLevel.Ring.new()
			var at := gap.a + Vector3(dir.x, 0.0, dir.y) * marks[k]
			ring.pos = Vector3(at.x, lerpf(gap.a.y, gap.b.y, marks[k] / span) + rng.randf_range(t.ring_height_min, t.ring_height_max)
					+ (rng.randf_range(-t.ring_scatter, t.ring_scatter) * 0.5 if item.get("high", false) and marks.size() > 1 else 0.0), at.z)
			ring.gap = g
			if k == mover:
				ring.amp = t.moving_amp
				ring.period = t.moving_period * rng.randf_range(0.9, 1.15)
				ring.phase = rng.randf_range(0.0, TAU)
			level.rings.append(ring)
		level.gaps.append(gap)
		level.islets.append(to)
	_place_props(level, rng, t)
	# Маяк на последнем острове: за серединой по ходу.
	var last := level.islets[level.islets.size() - 1]
	var end_dir := level.gaps[level.gaps.size() - 1].dir
	var tower := HookLevel.Prop.new()
	tower.name = "lighthouse"
	tower.pos = last.pos + Vector3(end_dir.x, 0.0, end_dir.y) * last.radius * 0.3
	tower.radius = PROPS["lighthouse"].x
	tower.height = PROPS["lighthouse"].y
	tower.islet = level.islets.size() - 1
	level.props.append(tower)
	return level


## Точка, с которой бот выходит на прямую к отрыву: на острове, за `back` метров до края.
static func lineup(level: HookLevel, g: int) -> Vector3:
	var gap := level.gaps[g]
	var back := minf(2.5, level.islets[g].radius * 0.9)
	return gap.a - Vector3(gap.dir.x, 0.0, gap.dir.y) * back


## Реквизит на больших островах: в стороне от пути героя (вход, выход на прямую, отрыв).
static func _place_props(level: HookLevel, rng: RandomNumberGenerator, t: PlatformerThreedGenTuning) -> void:
	for i in level.islets.size() - 1:
		var it := level.islets[i]
		if it.radius < t.land_min - 0.1:
			continue
		var path: Array[Vector2] = []
		var start := level.gaps[i - 1].b if i > 0 else it.pos
		path.append(Vector2(start.x, start.z))
		var line := lineup(level, i)
		path.append(Vector2(line.x, line.z))
		path.append(Vector2(level.gaps[i].a.x, level.gaps[i].a.z))
		var placed: Array[Vector2] = []
		var want := rng.randi_range(t.props_min, t.props_max)
		for attempt in 40:
			if placed.size() >= want:
				break
			var angle := rng.randf_range(0.0, TAU)
			var name: String = PROP_NAMES[rng.randi_range(0, PROP_NAMES.size() - 1)]
			var size: Vector2 = PROPS[name]
			var far := it.radius_at(angle) - size.x - 0.35
			var p := Vector2(it.pos.x, it.pos.z) + Vector2(cos(angle), sin(angle)) * far * sqrt(rng.randf_range(0.08, 1.0))
			var ok := true
			for k in path.size() - 1:
				if Geometry2D.get_closest_point_to_segment(p, path[k], path[k + 1]).distance_to(p) < t.prop_clear + size.x:
					ok = false
			for q in placed:
				if q.distance_to(p) < 1.7:
					ok = false
			if not ok:
				continue
			placed.append(p)
			var prop := HookLevel.Prop.new()
			prop.name = name
			prop.pos = Vector3(p.x, it.pos.y, p.y)
			prop.radius = size.x
			prop.height = size.y
			prop.yaw = rng.randf_range(-PI, PI)
			prop.islet = i
			level.props.append(prop)


## Пусто, если уровень годится; иначе что не так.
static func validate(level: HookLevel, t: PlatformerThreedGenTuning = null, rules: PlatformerThreedTuning = null) -> String:
	if t == null:
		t = PlatformerThreedGenTuning.load_default()
	if rules == null:
		rules = PlatformerThreedTuning.load_default()
	if level.gaps.size() < 12 or level.islets.size() != level.gaps.size() + 1:
		return "пропастей %d" % level.gaps.size()
	if level.gaps[0].kind != HookLevel.Kind.JUMP:
		return "первая пропасть не простой прыжок"
	for g in level.gaps.size():
		var ids := level.rings_of(g)
		if (level.gaps[g].kind == HookLevel.Kind.RINGS) != (not ids.is_empty()):
			return "пропасть %d: вид и кольца не сходятся" % g
		# Соседние кольца цепочки достаются одной верёвкой с запасом.
		for k in range(1, ids.size()):
			if level.rings[ids[k - 1]].pos.distance_to(level.rings[ids[k]].pos) > rules.rope_max * 1.3:
				return "кольца %d и %d слишком далеко" % [ids[k - 1], ids[k]]
		if level.gaps[g].kind == HookLevel.Kind.CLIMB:
			var rise := level.gaps[g].b.y - level.gaps[g].a.y
			if rise > rules.climb_reach + rules.jump_speed * rules.jump_speed / (2.0 * rules.gravity) - 0.5:
				return "уступ %d слишком высок" % g
	# Острова не налезают друг на друга, кольца не висят над чужим островом.
	for i in level.islets.size():
		for j in range(i + 2, level.islets.size()):
			var a := level.islets[i]
			var b := level.islets[j]
			if Vector2(a.pos.x - b.pos.x, a.pos.z - b.pos.z).length() < a.radius + b.radius + 4.0:
				return "острова %d и %d слишком близко" % [i, j]
	for r in level.rings:
		for i in level.islets.size():
			if i == r.gap or i == r.gap + 1:
				continue
			var it := level.islets[i]
			if Vector2(it.pos.x - r.pos.x, it.pos.z - r.pos.z).length() < it.radius + 3.0:
				return "кольцо над островом %d" % i
	if level.count(HookLevel.Kind.RINGS) * 2 < level.gaps.size() - 2:
		return "мало пропастей с кольцами"
	if level.count(HookLevel.Kind.CLIMB) < 2:
		return "мало уступов"
	if level.longest_chain() < 3:
		return "нет цепочки из трёх колец"
	if level.moving() < 1:
		return "нет движущихся колец"
	if level.small() < 2:
		return "нет секции камней"
	if level.props.size() < 6:
		return "мало реквизита"
	return ""
