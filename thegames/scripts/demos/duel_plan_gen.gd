class_name DuelPlanGen
extends RefCounted
## Генератор дуэли на реакцию из сида (#94): детерминирован. У каждого раунда своя пауза до
## вспышки (угадать её нельзя) и своя задержка соперника: от раунда к раунду он быстрее.


static func generate(seed_: int, t: FightingVectorGenTuning = null) -> DuelPlan:
	if t == null:
		t = FightingVectorGenTuning.load_default()
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":duel"))
	var plan := DuelPlan.new()
	for i in t.rounds:
		var k := float(i) / maxf(t.rounds - 1, 1.0)
		plan.waits.append(rng.randf_range(t.wait_min, t.wait_max))
		plan.delays.append(lerpf(t.delay_first, t.delay_last, k) + rng.randf_range(-t.delay_jitter, t.delay_jitter))
	return plan


## Проверка плана: "" или причина.
static func validate(plan: DuelPlan, t: FightingVectorGenTuning) -> String:
	if plan.rounds() != t.rounds or plan.delays.size() != t.rounds:
		return "раундов %d" % plan.rounds()
	for i in plan.rounds():
		if plan.waits[i] < t.wait_min - 0.001 or plan.waits[i] > t.wait_max + 0.001:
			return "пауза раунда %d: %.2f с" % [i + 1, plan.waits[i]]
		var k := float(i) / maxf(t.rounds - 1, 1.0)
		if absf(plan.delays[i] - lerpf(t.delay_first, t.delay_last, k)) > t.delay_jitter + 0.001:
			return "задержка соперника в раунде %d: %.2f с" % [i + 1, plan.delays[i]]
	if plan.delays[plan.rounds() - 1] >= plan.delays[0]:
		return "соперник к концу не быстрее"
	return ""
