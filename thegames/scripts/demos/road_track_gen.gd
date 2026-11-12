class_name RoadTrackGen
extends RefCounted
## Генератор трассы псевдо-3D из сида (#99): детерминирован. Прямая на старте, дальше
## участки: прямая, поворот с плавным въездом и выездом, холм, поворот на холме; к концу
## крутых поворотов больше. Перед крутым поворотом знак со стрелкой. Пальмы по обочинам
## через несколько сегментов, иногда камень, бочка, хижина; монеты рядами по полосе на прямых.
## Соперники стоят решёткой по двое впереди героя, самые быстрые дальше; первые три это
## лидеры на пределе скорости героя (`leader_speeds`). `validate` проверяет.


static func generate(seed_: int, t: RacingBit16GenTuning = null) -> RoadTrack:
	if t == null:
		t = RacingBit16GenTuning.load_default()
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":road"))
	var tr := RoadTrack.new()
	var h := 0.0
	_add(tr, t.start_straight, 0.0, h, h)
	var last_curve := 0.0
	while tr.count() < t.length:
		var k := float(tr.count()) / t.length
		var r := rng.randf()
		if r < 0.25:
			_add(tr, rng.randi_range(t.straight_min, t.straight_max), 0.0, h, h)
			continue
		var hard := rng.randf() < lerpf(t.hard_first, t.hard_last, k)
		var dir := -1.0 if rng.randf() < 0.5 else 1.0
		# Повороты не идут в одну сторону трижды подряд: дорога не закручивается в спираль.
		if last_curve * dir > 0.0 and rng.randf() < 0.5:
			dir = -dir
		last_curve = dir
		var c := dir * (t.curve_hard if hard else rng.randf_range(t.curve_easy, (t.curve_easy + t.curve_hard) * 0.5))
		var hold := rng.randi_range(t.curve_hold_min, t.curve_hold_max)
		var to := h
		if r > 1.0 - t.combo_chance or r < 0.4:
			# Холм вверх или вниз, но не дальше `hill_max` от уровня моря: высота не копится.
			var up := -1.0 if h > 0.0 else 1.0
			if absf(h) < t.hill_max * 0.5 and rng.randf() < 0.5:
				up = -up
			to = clampf(h + rng.randf_range(t.hill_min, t.hill_max) * up, -t.hill_max, t.hill_max)
		if r < 0.4:
			c = 0.0
			hard = false
		if hard:
			var at := tr.count() - t.sign_ahead
			if at > t.start_straight:
				tr.props.append(Vector3(at, -1.35 * dir, RoadTrack.Prop.SIGN_RIGHT if dir > 0.0 else RoadTrack.Prop.SIGN_LEFT))
		_curve(tr, t.curve_enter, hold, t.curve_enter, c, h, to)
		h = to
		if rng.randf() < 0.3:
			# Дорога иногда возвращается на уровень моря: холмы не уводят её в небо.
			var n := maxi(10, int(absf(h) / 120.0))
			_curve(tr, n, 20, n, 0.0, h, 0.0)
			h = 0.0
	tr.finish = tr.count()
	_add(tr, t.after_finish, 0.0, h, h)
	_props(tr, rng, t)
	_coins(tr, rng, t)
	_rivals(tr, rng, t)
	return tr


static func _add(tr: RoadTrack, n: int, c: float, y0: float, y1: float) -> void:
	for i in n:
		tr.curve.append(c)
		tr.y.append(lerpf(y0, y1, float(i + 1) / n))


## Поворот и холм: изгиб и высота плавно нарастают на въезде и спадают на выезде.
static func _curve(tr: RoadTrack, enter: int, hold: int, leave: int, c: float, y0: float, y1: float) -> void:
	var total := float(enter + hold + leave)
	for i in enter + hold + leave:
		var k := float(i + 1) / total
		var ck := 1.0
		if i < enter:
			ck = _ease_in(float(i) / enter)
		elif i >= enter + hold:
			ck = 1.0 - _ease_in(float(i - enter - hold) / leave)
		tr.curve.append(c * ck)
		tr.y.append(lerpf(y0, y1, (1.0 - cos(k * PI)) * 0.5))


static func _ease_in(k: float) -> float:
	return k * k


static func _props(tr: RoadTrack, rng: RandomNumberGenerator, t: RacingBit16GenTuning) -> void:
	for side in [-1.0, 1.0]:
		var i := rng.randi_range(4, 10)
		while i < tr.count() - 4:
			var r := rng.randf()
			var kind := RoadTrack.Prop.PALM
			var x: float = side * rng.randf_range(1.3, 2.2)
			if r < t.rock_chance:
				kind = RoadTrack.Prop.ROCK
				x = side * rng.randf_range(1.25, 1.8)
			elif r < t.rock_chance + t.barrel_chance:
				kind = RoadTrack.Prop.BARREL
				x = side * rng.randf_range(1.2, 1.5)
			elif r < t.rock_chance + t.barrel_chance + t.hut_chance:
				kind = RoadTrack.Prop.HUT
				x = side * rng.randf_range(2.4, 3.0)
			tr.props.append(Vector3(i, x, kind))
			i += rng.randi_range(t.prop_every_min, t.prop_every_max)
	tr.props.sort_custom(func(a: Vector3, b: Vector3) -> bool: return a.x < b.x)


static func _coins(tr: RoadTrack, rng: RandomNumberGenerator, t: RacingBit16GenTuning) -> void:
	var i := 60
	while i < tr.finish - 40:
		var lane: float = [-0.55, 0.0, 0.55][rng.randi_range(0, 2)]
		for k in t.coins_per_row:
			tr.coins.append(Vector2(lane, (i + k * t.coin_step) * RoadTrack.SEG + RoadTrack.SEG * 0.5))
		i += t.coin_row_every + rng.randi_range(-20, 20)


static func _rivals(tr: RoadTrack, rng: RandomNumberGenerator, t: RacingBit16GenTuning) -> void:
	var speeds: Array[float] = []
	var rest := t.rivals - t.leader_speeds.size()
	for i in rest:
		speeds.append(lerpf(t.rival_speed_min, t.rival_speed_max, float(i) / maxf(rest - 1, 1)) + rng.randf_range(-0.01, 0.01))
	# Лидеры впереди всех, первый в самом первом ряду.
	for k in range(t.leader_speeds.size() - 1, -1, -1):
		speeds.append(t.leader_speeds[k])
	# Ближние к герою медленнее, дальние быстрее: обгоны идут по нарастающей.
	for i in t.rivals:
		var r := RoadTrack.Rival.new()
		r.x = -0.45 if i % 2 == 0 else 0.45
		r.z = (i / 2 + 1) * t.grid_gap * RoadTrack.SEG
		r.speed = speeds[i]
		r.tint = i % 4
		tr.rivals.append(r)


## Проверка трассы; пустая строка, если всё в порядке.
static func validate(tr: RoadTrack, t: RacingBit16GenTuning) -> String:
	if tr.finish < t.length:
		return "финиш на сегменте %d раньше длины %d" % [tr.finish, t.length]
	for i in tr.count():
		if absf(tr.curve[i]) > t.curve_hard + 0.01:
			return "изгиб %.1f на сегменте %d" % [tr.curve[i], i]
	for i in range(1, tr.count()):
		if absf(tr.y[i] - tr.y[i - 1]) > RoadTrack.SEG * 0.6:
			return "уклон на сегменте %d круче 0,6" % i
	for p in tr.props:
		if absf(p.y) < 1.15:
			return "проп на дороге у сегмента %d" % int(p.x)
	for c in tr.coins:
		if absf(c.x) > 0.9 or c.y > tr.finish_z():
			return "монета вне дороги у %d" % int(c.y)
	if tr.rivals.size() != t.rivals:
		return "соперников %d" % tr.rivals.size()
	return ""
