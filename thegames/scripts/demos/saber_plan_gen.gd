class_name SaberPlanGen
extends RefCounted
## Генератор плана «дуэли на саблях» (#125) из сида. Первые ходы это одиночные удары с долгим
## замахом; дальше связки из двух, потом из трёх, замах короче, паузы меньше, стойку соперник
## меняет чаще и чаще успевает закрыться. С шестого хода бывают финты, с пятого раз в несколько
## ходов выпад. План сида это первая попытка, что проходит `validate` и в которой бот WIN
## побеждает с запасом здоровья, а бот LOSE проигрывает.

const ATTEMPTS := 30


static func generate(seed_: int, t: FightingThreedTuning = null) -> SaberPlan:
	if t == null:
		t = FightingThreedTuning.load_default()
	var plan: SaberPlan = null
	for attempt in ATTEMPTS:
		plan = _build(seed_, attempt, t)
		if validate(plan, t) != "":
			continue
		var win := SaberSim.simulate(plan, t, AutoTest.BotMode.WIN)
		var lose := SaberSim.simulate(plan, t, AutoTest.BotMode.LOSE)
		if win.won and win.hero_hp >= 30 and not lose.won:
			break
	return plan


static func _build(seed_: int, attempt: int, t: FightingThreedTuning) -> SaberPlan:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":saber:", attempt))
	var plan := SaberPlan.new()
	var last := -1
	for i in t.moves:
		var k := clampf(float(i) / 26.0, 0.0, 1.0)
		var move := SaberPlan.Move.new()
		move.pause = lerpf(t.pause.x, t.pause.y, k) * rng.randf_range(0.85, 1.15)
		move.guard = rng.randi_range(0, 2) as SaberPlan.Side
		move.guard_hold = lerpf(t.guard_hold.x, t.guard_hold.y, k)
		move.react = lerpf(t.react.x, t.react.y, k)
		move.lunge = i >= t.lunge_from and (i - t.lunge_from) % t.lunge_every == 0
		var count := 1
		if not move.lunge:
			if i >= t.triple_from and rng.randf() < 0.45:
				count = 3
			elif i >= t.double_from and rng.randf() < 0.7:
				count = 2
		for n in count:
			var strike := SaberPlan.Strike.new()
			# Сторона не повторяет прошлый удар: блок приходится переставлять.
			var side := rng.randi_range(0, 2)
			if side == last:
				side = (side + 1 + rng.randi_range(0, 1)) % 3
			last = side
			strike.side = side as SaberPlan.Side
			strike.shown = strike.side
			strike.windup = t.lunge_windup if move.lunge else lerpf(t.windup.x, t.windup.y, k) * rng.randf_range(0.92, 1.08)
			if not move.lunge and i >= t.feint_from and rng.randf() < t.feint_share:
				strike.shown = ((side + 1 + rng.randi_range(0, 1)) % 3) as SaberPlan.Side
				# Финту нужен замах подлиннее: после смены стороны её ещё можно прочитать.
				strike.windup = maxf(strike.windup, 0.6)
			move.strikes.append(strike)
		plan.moves.append(move)
	return plan


## Пусто, если план годится; иначе что не так.
static func validate(plan: SaberPlan, t: FightingThreedTuning = null) -> String:
	if t == null:
		t = FightingThreedTuning.load_default()
	if plan.moves.size() != t.moves:
		return "ходов %d" % plan.moves.size()
	if plan.moves[0].strikes.size() != 1 or plan.moves[0].lunge or plan.moves[0].strikes[0].feint():
		return "первый ход не простой удар"
	if plan.longest() < 3:
		return "нет связки из трёх"
	if plan.feints() < 4:
		return "финтов %d" % plan.feints()
	if plan.lunges() < 3:
		return "выпадов %d" % plan.lunges()
	return ""
