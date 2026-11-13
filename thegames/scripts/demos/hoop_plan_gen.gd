class_name HoopPlanGen
extends RefCounted
## Генератор плана бросков спорта × low poly (#115) из сида. Четыре ближних броска, два дальних,
## потом два с боковым ветром в одну-три стрелки и два с ездящим кольцом, в каждой паре ближний
## и дальний. Зелёная зона шкалы стоит тем выше, чем дальше точка. Для каждой точки подбирается подъём броска (мяч входит
## в кольцо под заданным углом) и пробными бросками ищутся скорости чистого попадания: они
## становятся зелёной зоной шкалы. План сида это первая попытка, что проходит `validate`.

const ATTEMPTS := 60


static func generate(seed_: int, t: SportLowpolyGenTuning = null, rules: SportLowpolyTuning = null) -> HoopPlan:
	if t == null:
		t = SportLowpolyGenTuning.load_default()
	if rules == null:
		rules = SportLowpolyTuning.load_default()
	var plan: HoopPlan = null
	for attempt in ATTEMPTS:
		plan = _build(seed_, attempt, t, rules)
		if validate(plan, t, rules) == "":
			break
	return plan


static func _build(seed_: int, attempt: int, t: SportLowpolyGenTuning, rules: SportLowpolyTuning) -> HoopPlan:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":hoop:", attempt))
	var plan := HoopPlan.new()
	var rim := HoopSim.rim_rest(rules)
	var side := 1.0 if rng.randf() < 0.5 else -1.0
	for i in rules.shots:
		var shot := HoopPlan.Shot.new()
		# Порядок: ближние, потом дальние, затем по паре бросков с ветром и с ездящим кольцом,
		# в каждой паре ближний и дальний.
		var special := i - (rules.shots - t.wind_shots - t.moving_shots)
		var windy := special >= 0 and special < t.wind_shots
		var moving := special >= t.wind_shots
		var far := i >= t.near_first if special < 0 else (special - (0 if windy else t.wind_shots)) % 2 == 1
		shot.dist = rng.randf_range(t.far_min, t.far_max) if far else rng.randf_range(t.near_min, t.near_max)
		# Точки по очереди слева и справа от оси кольца: каждый раз другой вид.
		var angle := side * deg_to_rad(rng.randf_range(8.0, t.angle_max))
		side = -side
		shot.pos = Vector3(rim.x + sin(angle) * shot.dist, 0.0, rim.z - cos(angle) * shot.dist)
		shot.points = 3 if shot.dist >= t.three_from else 2
		var k := clampf(inverse_lerp(t.near_min, t.far_max, shot.dist), 0.0, 1.0)
		shot.zone_half = lerpf(t.zone_near, t.zone_far, k)
		shot.meter = lerpf(t.meter_near, t.meter_far, k)
		# Зелёная зона стоит на шкале по расстоянию: вблизи бросать слабее, издали сильнее.
		shot.zone = lerpf(t.zone_at_near, t.zone_at_far, k)
		if windy:
			shot.wind = rng.randi_range(1, t.wind_max) * (1 if rng.randf() < 0.5 else -1)
		if moving:
			shot.move_amp = t.move_amp
			shot.move_period = t.move_period
			shot.move_phase = rng.randf_range(0.0, TAU)
		_calibrate(shot, t, rules)
		plan.shots.append(shot)
	return plan


## Подъём броска, скорости чистого попадания, время полёта и увод одной стрелкой ветра.
static func _calibrate(shot: HoopPlan.Shot, t: SportLowpolyGenTuning, rules: SportLowpolyTuning) -> void:
	var from := HoopSim.launch_pos(shot, rules)
	var rim := HoopSim.rim_rest(rules)
	var d := Vector2(rim.x - from.x, rim.z - from.z).length()
	var rise := rim.y - from.y
	# Мяч входит в кольцо под углом `entry`: tan(подъёма) = tan(входа) + 2·высота/расстояние.
	shot.lift = atan(tan(deg_to_rad(t.entry)) + 2.0 * rise / d)
	var ideal := sqrt(rules.gravity * d * d / (2.0 * pow(cos(shot.lift), 2.0) * (d * tan(shot.lift) - rise)))
	# Чистый диапазон: от идеальной скорости в обе стороны, пока мяч входит, ничего не задев.
	var calm := HoopPlan.Shot.new()
	calm.pos = shot.pos
	calm.lift = shot.lift
	var step := ideal * 0.001
	shot.v_lo = ideal
	shot.v_hi = ideal
	if not HoopSim.trial(calm, rules, 0.0, ideal, 0.0)[1]:
		shot.v_lo = 0.0
		shot.v_hi = 0.0
		return
	while shot.v_lo > ideal * 0.9 and HoopSim.trial(calm, rules, 0.0, shot.v_lo - step, 0.0)[1]:
		shot.v_lo -= step
	while shot.v_hi < ideal * 1.1 and HoopSim.trial(calm, rules, 0.0, shot.v_hi + step, 0.0)[1]:
		shot.v_hi += step
	var mid := (shot.v_lo + shot.v_hi) / 2.0
	shot.flight = HoopSim.trial(calm, rules, 0.0, mid, 0.0)[2]
	# Одна стрелка ветра: на сколько мяч уходит вбок у кольца, в радианах прицела.
	shot.tick = atan(0.5 * rules.wind_unit * shot.flight * shot.flight / d)


## Пусто, если план годится; иначе что не так.
static func validate(plan: HoopPlan, t: SportLowpolyGenTuning = null, rules: SportLowpolyTuning = null) -> String:
	if t == null:
		t = SportLowpolyGenTuning.load_default()
	if rules == null:
		rules = SportLowpolyTuning.load_default()
	if plan.shots.size() != rules.shots:
		return "бросков %d" % plan.shots.size()
	var near := 0
	for i in plan.shots.size():
		var s := plan.shots[i]
		near += 1 if s.points == 2 else 0
		if s.v_hi - s.v_lo < 0.02:
			return "бросок %d: нет чистого диапазона" % i
		# Точный бросок входит чисто: в середине зоны и у её краёв, с поправкой на ветер, в любой
		# момент езды кольца.
		for at: float in [0.0, 0.9, 1.7, 2.6]:
			var shift := HoopSim.hoop_shift(s, at + s.flight)
			var yaw := HoopSim.yaw_for(s, rules, shift)
			for edge: float in [-0.9, 0.0, 0.9]:
				var scale := HoopSim.reach_of(s, rules, shift)
				var result := HoopSim.trial(s, rules, yaw, HoopSim.speed_of(s, rules, s.zone + edge * s.zone_half) * scale, at)
				if not result[0]:
					return "бросок %d: точный бросок мимо (край зоны %.1f, момент %.1f)" % [i, edge, at]
			if s.move_amp <= 0.0:
				break
	if near < t.near_first:
		return "ближних бросков %d" % near
	if plan.count_wind() != t.wind_shots:
		return "бросков с ветром %d" % plan.count_wind()
	if plan.count_moving() != t.moving_shots:
		return "бросков с ездящим кольцом %d" % plan.count_moving()
	return ""
