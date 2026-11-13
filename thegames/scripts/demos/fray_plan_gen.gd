class_name FrayPlanGen
extends RefCounted
## Генератор плана «одного против всех» (#125) из сида. Первая волна это трое простых
## пиратов, которые нападают по одному; со второй выходит щитоносец и бывают атаки вдвоём, с
## третьей пират с ножом; замахи короче, атаки чаще. План сида это первая попытка, что
## проходит `validate`, в которой бот WIN побеждает с запасом здоровья, а бот LOSE проигрывает.

const ATTEMPTS := 30
const T := FrayPlan.Kind.THUG
const S := FrayPlan.Kind.SHIELD
const K := FrayPlan.Kind.KNIFE
const WAVES := [[T, T, T], [T, T, S, T], [T, K, S, T], [T, K, S, K, T], [S, T, K, S, K], [T, S, K, T, K, S]]


static func generate(seed_: int, t: FightingThreedTuning = null) -> FrayPlan:
	if t == null:
		t = FightingThreedTuning.load_default()
	var plan: FrayPlan = null
	for attempt in ATTEMPTS:
		plan = _build(seed_, attempt, t)
		if validate(plan) != "":
			continue
		var win := FraySim.simulate(plan, t, AutoTest.BotMode.WIN)
		var lose := FraySim.simulate(plan, t, AutoTest.BotMode.LOSE)
		if win.won and win.hero_hp >= 30 and not lose.won:
			break
	return plan


static func _build(seed_: int, attempt: int, t: FightingThreedTuning) -> FrayPlan:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":fray:", attempt))
	var plan := FrayPlan.new()
	plan.seed = rng.randi()
	for w in WAVES.size():
		var k := float(w) / (WAVES.size() - 1)
		var wave := FrayPlan.Wave.new()
		var roster: Array = (WAVES[w] as Array).duplicate()
		# Порядок выхода внутри волны случайный, кроме первой.
		if w > 0:
			for i in range(roster.size() - 1, 0, -1):
				var j := rng.randi_range(0, i)
				var keep: int = roster[i]
				roster[i] = roster[j]
				roster[j] = keep
		var start := rng.randf_range(0.0, TAU)
		for i in roster.size():
			wave.kinds.append(roster[i])
			wave.angles.append(start + TAU * i / roster.size() + rng.randf_range(-0.3, 0.3))
		wave.windup = lerpf(t.windup.x, t.windup.y, k)
		wave.gap = lerpf(t.attack_gap.x, t.attack_gap.y, k)
		wave.pair = lerpf(t.pair_chance.x, t.pair_chance.y, k)
		plan.waves.append(wave)
	return plan


## Пусто, если план годится; иначе что не так.
static func validate(plan: FrayPlan) -> String:
	if plan.waves.size() != WAVES.size():
		return "волн %d" % plan.waves.size()
	for k in plan.waves[0].kinds:
		if k != T:
			return "в первой волне не только простые пираты"
	if plan.count(S) < 4 or plan.count(K) < 4:
		return "мало щитоносцев или ножей"
	return ""
