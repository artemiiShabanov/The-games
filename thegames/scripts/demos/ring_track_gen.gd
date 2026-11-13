class_name RingTrackGen
extends RefCounted
## Генератор трассы гонок × low poly (#113) из сида. Опорные точки стоят по кругу с разбросом
## радиуса и угла, через них идёт замкнутая гладкая кривая: получается извилистое кольцо без
## самопересечений. Кривая режется на точки через равный шаг, старт ставится на самом прямом
## месте. Потом размечаются трамплин (второе по прямоте место, подальше от старта), участки
## без бортов на пологих местах, грязь на внутренней стороне самых крутых поворотов и полосы
## попутного ветра, одна из них у края участка без бортов. Трасса сида это первая попытка, что
## проходит `validate`.

const ATTEMPTS := 300


static func generate(seed_: int, t: RacingLowpolyGenTuning = null) -> RingTrack:
	if t == null:
		t = RacingLowpolyGenTuning.load_default()
	var track: RingTrack = null
	for attempt in ATTEMPTS:
		track = _build(seed_, attempt, t)
		if validate(track, t) == "":
			break
	return track


static func _build(seed_: int, attempt: int, t: RacingLowpolyGenTuning) -> RingTrack:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":ring:", attempt))
	var track := RingTrack.new()
	track.step = t.step
	track.half_width = t.half_width
	track.ramp_gap = t.ramp_gap
	track.ramp_run = t.ramp_run
	# Опорные точки по кругу.
	var control := PackedVector2Array()
	for i in t.points:
		var angle := TAU * (i + rng.randf_range(-t.angle_jitter, t.angle_jitter)) / t.points
		# Точки через одну ближе к центру и дальше от него: кольцо выходит зубчатым, с S-образными связками.
		var swing := (1.0 if i % 2 == 0 else -1.0) * t.zigzag * rng.randf_range(0.35, 1.0)
		var r := t.radius * (1.0 + swing) * rng.randf_range(t.radius_min, t.radius_max)
		control.append(Vector2(cos(angle) * r * t.stretch, sin(angle) * r))
	# Гладкая замкнутая кривая, густо.
	var dense := PackedVector2Array()
	var n := control.size()
	for i in n:
		for k in 16:
			var u := k / 16.0
			dense.append(control[i].cubic_interpolate(control[(i + 1) % n], control[posmod(i - 1, n)], control[(i + 2) % n], u))
	# Точки через равный шаг по длине; углы у опорных точек скругляются, шаг выравнивается снова.
	var even := _resample(dense, t.step)
	for pass_ in t.smooth:
		var next := PackedVector2Array()
		for i in even.size():
			next.append((even[posmod(i - 1, even.size())] + even[i] * 2.0 + even[(i + 1) % even.size()]) / 4.0)
		even = next
	even = _resample(even, t.step)
	var count := even.size()
	var total := 0.0
	for i in count:
		total += even[i].distance_to(even[(i + 1) % count])
	# Старт на самом прямом месте: точки сдвигаются по кругу.
	var bends := _bends(even)
	var start := _straightest(bends, int(40.0 / t.step), [], 0)
	var hill_a := rng.randf_range(0.0, TAU)
	var hill_b := rng.randf_range(0.0, TAU)
	for i in count:
		var p := even[(start + i) % count]
		track.points.append(p)
		var turn := TAU * i / count
		track.heights.append(t.hill_a * sin(turn * 2.0 + hill_a) + t.hill_b * sin(turn * 3.0 + hill_b))
	track.length = total
	track.step = total / count
	for i in count:
		var ahead := track.points[(i + 1) % count] - track.points[posmod(i - 1, count)]
		track.yaws.append(atan2(-ahead.x, -ahead.y))
	for i in count:
		var turn := angle_difference(track.yaws[posmod(i - 2, count)], track.yaws[(i + 2) % count])
		track.curves.append(turn / (4.0 * track.step))
	_mark(track, rng, t)
	return track


## Замкнутая ломаная точками через равный шаг около `step`.
static func _resample(line: PackedVector2Array, step: float) -> PackedVector2Array:
	var total := 0.0
	for i in line.size():
		total += line[i].distance_to(line[(i + 1) % line.size()])
	var count := maxi(int(roundf(total / step)), 8)
	var out := PackedVector2Array()
	var want := 0.0
	var walked := 0.0
	var j := 0
	while out.size() < count:
		var a := line[j % line.size()]
		var b := line[(j + 1) % line.size()]
		var seg := a.distance_to(b)
		if walked + seg >= want:
			out.append(a.lerp(b, (want - walked) / maxf(seg, 0.0001)))
			want += total / count
		else:
			walked += seg
			j += 1
	return out


## Модуль поворота оси в каждой точке (для поиска прямых мест до того, как трасса собрана).
static func _bends(points: PackedVector2Array) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	var n := points.size()
	for i in n:
		var a := points[i] - points[posmod(i - 2, n)]
		var b := points[(i + 2) % n] - points[i]
		out.append(absf(a.angle_to(b)))
	return out


## Начало самого прямого окна из `window` точек, не ближе `keep` точек к занятым местам.
static func _straightest(bends: PackedFloat32Array, window: int, taken: Array, keep: int) -> int:
	var n := bends.size()
	var best := 0
	var best_sum := INF
	for i in n:
		var free := true
		for at: int in taken:
			var gap := absi(posmod(i - at + n / 2, n) - n / 2)
			free = free and gap > keep
		if not free:
			continue
		var sum := 0.0
		for k in window:
			sum += bends[(i + k) % n]
		if sum < best_sum:
			best_sum = sum
			best = i
	return best


## Трамплин, участки без бортов, грязь, ветер.
static func _mark(track: RingTrack, rng: RandomNumberGenerator, t: RacingLowpolyGenTuning) -> void:
	var n := track.count()
	var step := track.step
	var bends := PackedFloat32Array()
	for c in track.curves:
		bends.append(absf(c))
	# Занятые места: старт (точка 0) и всё размеченное; новое не ставится ближе `keep`.
	var taken: Array = [0]
	var ramp_at := _straightest(bends, int((t.ramp_run + t.ramp_gap + 16.0) / step), taken, int(60.0 / step))
	track.ramp_s = ramp_at * step + t.ramp_run + 6.0
	taken.append(ramp_at + int(15.0 / step))
	for k in t.open_count:
		var at := _straightest(bends, int(t.open_length / step), taken, int((t.open_length + 26.0) / step))
		var worst := 0.0
		for i in int(t.open_length / step):
			worst = maxf(worst, bends[(at + i) % n])
		if worst <= t.open_curve:
			track.open.append(Vector2(at * step, track.loop(at * step + t.open_length)))
			taken.append(at + int(t.open_length / step / 2.0))
	# Грязь: самые крутые повороты, не рядом друг с другом, не на участках без бортов и не у трамплина.
	var order: Array[int] = []
	for i in n:
		order.append(i)
	order.sort_custom(func(a: int, b: int) -> bool: return bends[a] > bends[b])
	var mud_at: Array[int] = []
	for i in order:
		if track.muds.size() >= t.mud_count or bends[i] < t.mud_curve:
			break
		var s := i * step
		var clear := not track.is_open(s) and not track.is_open(s - t.mud_length) and not track.is_open(s + t.mud_length) \
				and absf(track.delta(s, track.ramp_s)) > 36.0 and absf(track.delta(s, 0.0)) > 24.0
		for other in mud_at:
			clear = clear and absf(track.delta(s, other * step)) > 34.0
		if not clear:
			continue
		var mud := RingTrack.Mud.new()
		mud.s0 = track.loop(s - t.mud_length / 2.0)
		mud.s1 = track.loop(s + t.mud_length / 2.0)
		# Поворот влево (кривизна плюс): внутренняя сторона слева, `d` минус.
		mud.side = -signf(track.curves[i])
		mud.width = t.mud_width
		track.muds.append(mud)
		mud_at.append(i)
	# Ветер: первая полоса у края участка без бортов (рискованная), остальные на прямых местах.
	var wind_taken: Array = [ramp_at + int(10.0 / step)]
	for k in t.wind_count:
		var wind := RingTrack.Wind.new()
		wind.half = t.wind_half
		if k == 0 and not track.open.is_empty():
			var section := track.open[0]
			wind.s0 = track.loop(section.x + (t.open_length - t.wind_length) / 2.0)
			wind.d = (1.0 if rng.randf() < 0.5 else -1.0) * (track.half_width - t.wind_half - 0.5)
			wind_taken.append(int(section.x / step))
		else:
			var at := _straightest(bends, int(t.wind_length / step), wind_taken, int(46.0 / step))
			wind.s0 = at * step
			wind.d = rng.randf_range(-0.45, 0.45) * track.half_width
			wind_taken.append(at)
		wind.s1 = track.loop(wind.s0 + t.wind_length)
		track.winds.append(wind)


## Пусто, если трасса годится; иначе что не так.
static func validate(track: RingTrack, t: RacingLowpolyGenTuning = null) -> String:
	if t == null:
		t = RacingLowpolyGenTuning.load_default()
	var n := track.count()
	if track.length < t.length_min or track.length > t.length_max:
		return "длина %.0f" % track.length
	var tightest := 0.0
	for c in track.curves:
		tightest = maxf(tightest, absf(c))
	if tightest > 1.0 / t.radius_tightest:
		return "поворот радиусом %.1f" % (1.0 / tightest)
	# Дальние участки не подходят друг к другу ближе зазора: лента не слипается.
	var far := int(t.clearance * 2.0 / track.step)
	for i in range(0, n, 2):
		for j in range(i + far, n, 2):
			if n - (j - i) >= far and track.points[i].distance_to(track.points[j]) < t.clearance:
				return "участки слиплись у точек %d и %d" % [i, j]
	if track.open.is_empty():
		return "нет участков без бортов"
	if track.muds.size() < 2:
		return "грязи %d" % track.muds.size()
	if track.winds.size() < t.wind_count:
		return "ветра %d" % track.winds.size()
	if absf(track.delta(0.0, track.ramp_s)) < 50.0:
		return "трамплин у старта"
	if track.curve_ahead(track.ramp_s - t.ramp_run - 20.0, t.ramp_run + t.ramp_gap + 30.0) > 0.03:
		return "трамплин на повороте"
	if track.is_open(track.ramp_s - 10.0) or track.is_open(track.ramp_s + t.ramp_gap + 6.0):
		return "трамплин на участке без бортов"
	return ""
