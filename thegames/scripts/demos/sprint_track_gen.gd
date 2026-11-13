class_name SprintTrackGen
extends RefCounted
## Генератор трассы спринта (#122) из сида. Прямые и повороты идут по очереди: к концу трассы
## прямые короче, а повороты круче; со второй трети бывают связки из двух поворотов в разные
## стороны. Рельеф волнами растёт к концу. На пологих местах стоят сужения (мостки с мокрым
## настилом и камнями на плечах), перед частью поворотов лежит рыхлый песок. Трасса сида это
## первая попытка, что проходит `validate` и на которой бот WIN финиширует не ниже второго
## места.

const ATTEMPTS := 60


static func generate(seed_: int, t: RacingThreedGenTuning = null, rules: RacingThreedTuning = null) -> SprintTrack:
	if t == null:
		t = RacingThreedGenTuning.load_default()
	if rules == null:
		rules = RacingThreedTuning.load_default()
	var track: SprintTrack = null
	for attempt in ATTEMPTS:
		track = _build(seed_, attempt, t)
		if validate(track, t) != "":
			continue
		var bot := SprintSim.simulate(track, rules, AutoTest.BotMode.WIN)
		if bot.finished and bot.place() <= 2:
			break
	return track


static func _build(seed_: int, attempt: int, t: RacingThreedGenTuning) -> SprintTrack:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":sprint:", attempt))
	var track := SprintTrack.new()
	track.step = t.step
	track.full_half = t.half_width
	track.narrow_half = t.narrow_half
	var n := int(t.length / t.step) + 1
	track.length = (n - 1) * t.step
	var curves := PackedFloat32Array()
	curves.resize(n)
	# Кривизна: прямая, поворот, иногда сразу второй в другую сторону.
	var s := t.flat_start + rng.randf_range(0.0, 20.0)
	var heading := 0.0
	var side := 1.0 if rng.randf() < 0.5 else -1.0
	while s < track.length - 70.0:
		var k := s / track.length
		var parts := 2 if k > t.link_from and rng.randf() < t.link_chance else 1
		if parts == 2:
			track.links += 1
		for part in parts:
			var radius := lerpf(rng.randf_range(t.radius_start.x, t.radius_start.y), rng.randf_range(t.radius_end.x, t.radius_end.y), k)
			var turn := deg_to_rad(rng.randf_range(t.angle.x, t.angle.y)) * (0.75 if parts == 2 else 1.0)
			# Курс не уходит далеко от начального: трасса не закручивается в себя.
			if part == 0:
				if absf(heading) > 1.2:
					side = -signf(heading)
				elif rng.randf() < 0.6:
					side = -side
			else:
				side = -side
			var span := turn * radius
			var ease := minf(t.ease, span / 3.0)
			if s + span > track.length - 60.0:
				break
			for i in range(int(s / t.step), int((s + span) / t.step) + 1):
				var along := i * t.step - s
				var gain := minf(minf(along / ease, (span - along) / ease), 1.0)
				curves[i] = side / radius * clampf(gain, 0.0, 1.0)
			track.corners.append(Vector3(s + span / 2.0, side * radius, span))
			heading += side * turn
			s += span
			if part == 0 and parts == 2:
				s += rng.randf_range(t.link_gap.x, t.link_gap.y)
		s += lerpf(rng.randf_range(t.straight_start.x, t.straight_start.y), rng.randf_range(t.straight_end.x, t.straight_end.y), k)
	# Ось: курс и точки по кривизне.
	var yaw := 0.0
	var p := Vector2.ZERO
	var w1 := rng.randf_range(t.hill_waves.x, t.hill_waves.y)
	var w2 := rng.randf_range(t.hill_waves.x, t.hill_waves.y) * 0.55
	var p1 := rng.randf_range(0.0, TAU)
	var p2 := rng.randf_range(0.0, TAU)
	for i in n:
		var at := i * t.step
		track.points.append(p)
		track.yaws.append(yaw)
		track.curves.append(curves[i])
		var amp := t.hill * smoothstep(t.flat_start, t.flat_start + 220.0, at) * (0.45 + 0.55 * at / track.length) \
				* smoothstep(0.0, 60.0, track.length - at)
		track.heights.append(amp * (0.6 * sin(TAU * at / w1 + p1) + 0.4 * sin(TAU * at / w2 + p2)))
		track.halves.append(t.half_width)
		track.surfaces.append(SprintTrack.Surface.ROAD)
		p += Vector2(-sin(yaw), -cos(yaw)) * t.step
		yaw += curves[i] * t.step
	track.bake()
	# Сужения: на пологих местах, не у старта и финиша, не вплотную друг к другу.
	for attempt_ in 60:
		if track.narrows.size() >= t.narrows:
			break
		var span := rng.randf_range(t.narrow_min, t.narrow_max)
		var s0 := rng.randf_range(track.length * 0.14, track.length - 120.0 - span)
		var ok := true
		for r in track.narrows:
			if s0 < r.y + 110.0 and s0 + span > r.x - 110.0:
				ok = false
		var at := s0 - t.narrow_ramp - 20.0
		while at <= s0 + span + t.narrow_ramp:
			if absf(track.curve(at)) > 1.0 / 40.0:
				ok = false
			at += t.step
		if not ok:
			continue
		track.narrows.append(Vector2(s0, s0 + span))
		for i in range(int((s0 - t.narrow_ramp) / t.step), int((s0 + span + t.narrow_ramp) / t.step) + 1):
			var here := i * t.step
			var squeeze := clampf(minf((here - (s0 - t.narrow_ramp)) / t.narrow_ramp, (s0 + span + t.narrow_ramp - here) / t.narrow_ramp), 0.0, 1.0)
			track.halves[i] = lerpf(t.half_width, t.narrow_half, smoothstep(0.0, 1.0, squeeze))
			if squeeze >= 1.0:
				track.surfaces[i] = SprintTrack.Surface.PLANKS
		for flank: float in [-1.0, 1.0]:
			track.rocks.append(Vector3(s0 - t.narrow_ramp * 0.45, flank * (lerpf(t.half_width, t.narrow_half, 0.5) + 1.5), 1.3))
	# Рыхлый песок перед поворотами.
	var order := range(track.corners.size())
	for attempt_ in 40:
		if track.sands.size() >= t.sands or order.is_empty():
			break
		var pick: int = order.pop_at(rng.randi_range(0, order.size() - 1))
		var corner := track.corners[pick]
		var span := rng.randf_range(t.sand_length.x, t.sand_length.y)
		var s0 := corner.x - corner.z / 2.0 - span * rng.randf_range(0.3, 0.7)
		if s0 < track.length * 0.12 or s0 + span > track.length - 60.0:
			continue
		var ok := true
		for r in track.narrows:
			if s0 < r.y + 30.0 and s0 + span > r.x - 30.0:
				ok = false
		for r in track.sands:
			if s0 < r.y + 40.0 and s0 + span > r.x - 40.0:
				ok = false
		if not ok:
			continue
		track.sands.append(Vector2(s0, s0 + span))
		for i in range(int(s0 / t.step), int((s0 + span) / t.step) + 1):
			track.surfaces[i] = SprintTrack.Surface.SAND
	return track


## Пусто, если трасса годится; иначе что не так.
static func validate(track: SprintTrack, t: RacingThreedGenTuning = null) -> String:
	if t == null:
		t = RacingThreedGenTuning.load_default()
	if track.corners.size() < 7:
		return "поворотов %d" % track.corners.size()
	if track.links < 1:
		return "нет связки поворотов"
	if track.narrows.size() < 2:
		return "сужений %d" % track.narrows.size()
	if track.sands.size() < 2:
		return "участков песка %d" % track.sands.size()
	if track.climb() < 2.0:
		return "нет рельефа"
	if track.tightest() < 15.0:
		return "поворот радиусом %.0f м" % track.tightest()
	# Дальние витки не сходятся.
	var skip := int(120.0 / track.step)
	for i in range(0, track.count(), 4):
		for j in range(i + skip, track.count(), 4):
			if track.points[i].distance_to(track.points[j]) < t.clearance:
				return "витки сходятся на %.0f и %.0f м" % [i * track.step, j * track.step]
	return ""
