class_name FightPlanGen
extends RefCounted
## Генератор плана соперника файтинга × 8-bit из сида (#54): детерминирован. Раунд делится на
## фазы по `phase_min`..`phase_max` секунд, пока не покроет его; профиль фазы по сиду, соседние
## разные, разных за раунд не меньше `distinct_min`; паттерн ударов фазы из 2-4 знаков, доля
## нижних по профилю. Реакция и шанс промаха соперника, мачта и пропы фона тоже из сида.
## `validate()` проверяет покрытие раунда, профили, паттерны, реакцию и пропы. Не прошёл:
## повтор с производным сидом, после `MAX_ATTEMPTS` запасной план по кругу профилей.

const MAX_ATTEMPTS := 16


static func generate(seed_: int, tuning: FightGenTuning = null, round_seconds := 60.0) -> FightPlan:
	if tuning == null:
		tuning = FightGenTuning.load_default()
	for attempt in MAX_ATTEMPTS:
		var rng := RandomNumberGenerator.new()
		rng.seed = hash(str(seed_, ":fight:", attempt))
		var plan := _build(rng, tuning, round_seconds, false)
		plan.seed = seed_
		if validate(plan, tuning, round_seconds) == "":
			plan.attempts = attempt + 1
			return plan
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":fight:fallback"))
	var plan := _build(rng, tuning, round_seconds, true)
	plan.seed = seed_
	plan.attempts = MAX_ATTEMPTS + 1
	plan.fallback = true
	var why := validate(plan, tuning, round_seconds)
	if why != "":
		push_warning("FightPlanGen: запасной план сида %d не прошёл проверку: %s" % [seed_, why])
	return plan


static func _build(rng: RandomNumberGenerator, t: FightGenTuning, round_seconds: float, plain: bool) -> FightPlan:
	var plan := FightPlan.new()
	var n := maxi(t.profiles.size(), 1)
	var prev := -1
	var start := rng.randi_range(0, n - 1)
	while plan.total_seconds() < round_seconds:
		var ph := FightPlan.Phase.new()
		if plain:
			# Запасной: профили по кругу.
			ph.profile = (start + plan.phases.size()) % n
		else:
			ph.profile = rng.randi_range(0, n - 1)
			if n > 1:
				while ph.profile == prev:
					ph.profile = rng.randi_range(0, n - 1)
		prev = ph.profile
		ph.seconds = roundf(rng.randf_range(t.phase_min, t.phase_max))
		var low_share := t.profiles[ph.profile].low_share if ph.profile < t.profiles.size() else 0.3
		var length := rng.randi_range(t.pattern_min, t.pattern_max)
		var pattern := ""
		for k in length:
			pattern += "L" if rng.randf() < low_share else "H"
		ph.pattern = pattern
		plan.phases.append(ph)
	plan.reaction = rng.randi_range(t.reaction_min, t.reaction_max)
	plan.miss = snappedf(rng.randf_range(t.miss_min, t.miss_max), 0.01)
	plan.mast_x = roundf(rng.randf_range(-t.mast_shift, t.mast_shift))
	# Пушка у одного борта, сундук у другого, сторона по сиду.
	var cannon_left := rng.randf() < 0.5
	for kind in 2:
		var p := FightPlan.Prop.new()
		p.kind = kind
		var side := -1.0 if (kind == 0) == cannon_left else 1.0
		p.x = side * roundf(rng.randf_range(t.prop_from_rail, t.prop_from_rail + t.prop_spread))
		plan.props.append(p)
	return plan


## Пустая строка, если план годится, иначе причина.
static func validate(plan: FightPlan, t: FightGenTuning, round_seconds := 60.0) -> String:
	if plan.total_seconds() < round_seconds:
		return "фазы покрывают %.0f с из %.0f" % [plan.total_seconds(), round_seconds]
	var seen := {}
	for i in plan.phases.size():
		var ph := plan.phases[i]
		if ph.profile < 0 or ph.profile >= t.profiles.size():
			return "профиль %d вне каталога" % ph.profile
		if not plan.fallback and i > 0 and ph.profile == plan.phases[i - 1].profile:
			return "фазы %d и %d одного профиля" % [i - 1, i]
		if ph.seconds < t.phase_min or ph.seconds > t.phase_max:
			return "фаза %d длиной %.0f с" % [i, ph.seconds]
		if ph.pattern.length() < t.pattern_min or ph.pattern.length() > t.pattern_max:
			return "паттерн фазы %d «%s»" % [i, ph.pattern]
		for ch in ph.pattern:
			if ch != "H" and ch != "L":
				return "знак «%s» в паттерне фазы %d" % [ch, i]
		seen[ph.profile] = true
	if seen.size() < mini(t.distinct_min, t.profiles.size()):
		return "разных профилей %d" % seen.size()
	if plan.reaction < t.reaction_min or plan.reaction > t.reaction_max:
		return "реакция %d" % plan.reaction
	if plan.miss < t.miss_min - 0.005 or plan.miss > t.miss_max + 0.005:
		return "промах %.2f" % plan.miss
	if plan.props.size() != 2 or signf(plan.props[0].x) == signf(plan.props[1].x):
		return "пропы не у разных бортов"
	return ""
