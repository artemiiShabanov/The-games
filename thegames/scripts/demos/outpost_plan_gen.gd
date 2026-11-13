class_name OutpostPlanGen
extends RefCounted
## Генератор плана «обороны аванпоста» (#123) из сида. Волны растут: первая идёт с одной
## стороны бегунами, вторая приводит щитоносцев, с третьей враги идут с двух сторон и
## появляются метатели, с пятой с трёх; в шестой выходит великан с охраной. План сида это
## первая попытка, что проходит `validate` и в которой бот WIN выстоял с запасом здоровья.

const ATTEMPTS := 40
const R := OutpostPlan.Kind.RUNNER
const S := OutpostPlan.Kind.SHIELD
const T := OutpostPlan.Kind.THROWER
const B := OutpostPlan.Kind.BRUTE
## Волны: сколько сторон и кто идёт (по порядку выхода).
const WAVES := [
	[1, [R, R, R, R]],
	[1, [R, S, R, R, S]],
	[2, [R, R, T, R, S, R]],
	[2, [S, R, R, T, S, R, R]],
	[3, [R, T, R, S, R, T, R, R]],
	[3, [B, R, R, S, R, T, R, R]],
]


static func generate(seed_: int, rules: ShooterThreedTuning = null) -> OutpostPlan:
	if rules == null:
		rules = ShooterThreedTuning.load_default()
	var plan: OutpostPlan = null
	for attempt in ATTEMPTS:
		plan = _build(seed_, attempt, rules)
		if validate(plan) != "":
			continue
		var bot := OutpostSim.simulate(plan, rules, AutoTest.BotMode.WIN)
		if bot.won and bot.health >= 25:
			break
	return plan


static func _build(seed_: int, attempt: int, rules: ShooterThreedTuning) -> OutpostPlan:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":outpost:", attempt))
	var plan := OutpostPlan.new()
	# Стороны: первая куда-то вперёд, вторая и третья по бокам от неё.
	var front := rng.randf_range(-0.5, 0.5)
	var flip := 1.0 if rng.randf() < 0.5 else -1.0
	plan.sides = PackedFloat32Array([front, front + flip * rng.randf_range(1.5, 2.0), front - flip * rng.randf_range(1.5, 2.0)])
	# Ящик с патронами на настиле со стороны, откуда не идут.
	plan.crate = -OutpostPlan.dir(front) * (rules.deck_radius - 0.75)
	for w in WAVES.size():
		var wave := OutpostPlan.Wave.new()
		var sides_used: int = WAVES[w][0]
		var roster: Array = WAVES[w][1]
		var at := 0.0
		for i in roster.size():
			var spawn := OutpostPlan.Spawn.new()
			spawn.kind = roster[i]
			# Великан идёт с первой стороны, остальные по кругу сторон со случайностью.
			spawn.side = 0 if spawn.kind == B else (i + rng.randi_range(0, 1)) % sides_used
			spawn.spread = rng.randf_range(-0.34, 0.34)
			spawn.stop = rules.thrower_range * rng.randf_range(0.92, 1.1) if spawn.kind == T else rng.randf_range(rules.ring_min, rules.ring_max)
			spawn.at = at
			at += rng.randf_range(0.9, 1.9) * (0.85 if w >= 4 else 1.0)
			wave.spawns.append(spawn)
		plan.waves.append(wave)
	# Бочки: по две на первых сторонах и одна на третьей, на пути врагов.
	for item: Array in [[0, 13.0], [0, 22.0], [1, 12.0], [1, 20.0], [2, 15.0]]:
		var yaw: float = plan.sides[item[0]] + rng.randf_range(-0.22, 0.22)
		plan.kegs.append(OutpostPlan.dir(yaw) * (float(item[1]) + rng.randf_range(-2.0, 2.0)))
	return plan


## Пусто, если план годится; иначе что не так.
static func validate(plan: OutpostPlan) -> String:
	if plan.waves.size() != WAVES.size():
		return "волн %d" % plan.waves.size()
	if plan.sides_of(0) != 1:
		return "первая волна не с одной стороны"
	if plan.sides_of(plan.waves.size() - 1) < 3 or plan.sides_of(2) < 2:
		return "мало сторон атаки"
	if plan.count(B) != 1 or plan.count(S) < 4 or plan.count(T) < 3:
		return "состав волн не тот"
	if plan.kegs.size() < 4:
		return "бочек %d" % plan.kegs.size()
	for i in plan.kegs.size():
		for j in range(i + 1, plan.kegs.size()):
			if plan.kegs[i].distance_to(plan.kegs[j]) < 5.0:
				return "бочки %d и %d рядом" % [i, j]
	return ""
