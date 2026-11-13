class_name SparPlanGen
extends RefCounted
## Генератор плана соперника файтинга × low poly (#116) из сида. Бой разгоняется: сначала
## одиночные удары с долгим замахом, потом двойные и тройные связки, со второй трети среди них
## сильные удары; паузы между связками и замахи к концу плана короче. Две связки подряд не
## повторяются. План сида это первая попытка, что проходит `validate`.

const ATTEMPTS := 40


static func generate(seed_: int, t: FightingLowpolyGenTuning = null) -> SparPlan:
	if t == null:
		t = FightingLowpolyGenTuning.load_default()
	var plan: SparPlan = null
	for attempt in ATTEMPTS:
		plan = _build(seed_, attempt, t)
		if validate(plan, t) == "":
			break
	return plan


static func _build(seed_: int, attempt: int, t: FightingLowpolyGenTuning) -> SparPlan:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":spar:", attempt))
	var plan := SparPlan.new()
	plan.heavy_windup = t.heavy_windup
	plan.guard_punch = t.guard_punch
	plan.guard_kick = t.guard_kick
	plan.loop_from = t.combos / 2
	var last := ""
	for i in t.combos:
		var late := float(i) / maxf(t.combos - 1, 1.0)
		var combo := SparPlan.Combo.new()
		combo.gap = lerpf(t.gap_first, t.gap_last, late) * rng.randf_range(0.85, 1.15)
		combo.windup = lerpf(t.windup_first, t.windup_last, late)
		for tries in 8:
			combo.moves.clear()
			var size := 1
			if i >= t.triple_from and rng.randf() < 0.4:
				size = 3
			elif i >= t.double_from and rng.randf() < 0.65:
				size = 2
			for k in size:
				combo.moves.append(SparPlan.Move.KICK if rng.randf() < t.kick_share else SparPlan.Move.PUNCH)
			# Сильный удар стоит последним в связке: после него соперник открыт дольше всего.
			if i >= t.heavy_from and rng.randf() < t.heavy_share:
				combo.moves[size - 1] = SparPlan.Move.HEAVY
			if str(combo.moves) != last:
				break
		last = str(combo.moves)
		plan.combos.append(combo)
	for i in t.guard_rolls:
		plan.guard.append(rng.randf())
	return plan


## Пусто, если план годится; иначе что не так.
static func validate(plan: SparPlan, t: FightingLowpolyGenTuning = null) -> String:
	if t == null:
		t = FightingLowpolyGenTuning.load_default()
	if plan.combos.size() != t.combos:
		return "связок %d" % plan.combos.size()
	for i in mini(t.double_from, plan.combos.size()):
		if plan.combos[i].moves.size() != 1 or plan.combos[i].moves[0] == SparPlan.Move.HEAVY:
			return "связка %d в начале не одиночная" % i
	if plan.count(SparPlan.Move.HEAVY) < 3:
		return "сильных ударов %d" % plan.count(SparPlan.Move.HEAVY)
	if plan.count(SparPlan.Move.KICK) < 6 or plan.count(SparPlan.Move.PUNCH) < 6:
		return "мало ударов рукой или ногой"
	if plan.longest() < 3:
		return "нет тройной связки"
	return ""
