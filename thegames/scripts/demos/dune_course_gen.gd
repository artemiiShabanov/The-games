class_name DuneCourseGen
extends RefCounted
## Генератор склона «спуска по дюне» (#124) из сида. Ворота идут змейкой: к концу они уже,
## чаще и дальше в стороны. Трамплины стоят перед воротами на пути к ним, за каждым полоса
## камней, которую он перелетает. Препятствий к концу больше; на прямой между воротами их
## нет. Склон сида это первая попытка, что проходит `validate`, на которой бот WIN проходит
## почти все ворота, а едущий прямо не набирает нужной доли.

const ATTEMPTS := 40


static func generate(seed_: int, t: SportThreedTuning = null) -> DuneCourse:
	if t == null:
		t = SportThreedTuning.load_default()
	var course: DuneCourse = null
	for attempt in ATTEMPTS:
		course = _build(seed_, attempt, t)
		if validate(course, t) != "":
			continue
		var win := DuneSim.simulate(course, t, AutoTest.BotMode.WIN)
		var lose := DuneSim.simulate(course, t, AutoTest.BotMode.LOSE)
		if win.won and win.missed <= 2 and win.falls <= 1 and not lose.won:
			break
	return course


static func _build(seed_: int, attempt: int, t: SportThreedTuning) -> DuneCourse:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":dune:", attempt))
	var course := DuneCourse.new()
	course.step = t.step
	course.length = t.length
	course.half_width = t.half_width
	var n := int((t.length + 80.0) / t.step) + 2
	var h := 0.0
	var p1 := rng.randf_range(0.0, TAU)
	var p2 := rng.randf_range(0.0, TAU)
	var w := t.pitch_wave * rng.randf_range(0.85, 1.2)
	var sw := t.sway_wave * rng.randf_range(0.85, 1.2)
	for i in n:
		var s := i * t.step
		course.heights.append(h)
		course.sways.append(t.sway * sin(TAU * s / sw + p2) * smoothstep(0.0, 120.0, s))
		var k := 0.5 + 0.5 * sin(TAU * s / w + p1)
		# За финишем склон выполаживается.
		var pitch := deg_to_rad(lerpf(t.pitch_min, t.pitch_max, k)) * (1.0 - smoothstep(t.length - 10.0, t.length + 50.0, s))
		h -= tan(pitch) * t.step
	# Ворота змейкой.
	var s := t.gate_first
	var side := 1.0 if rng.randf() < 0.5 else -1.0
	while s < t.length - 45.0:
		var k := s / t.length
		var gate := DuneCourse.Gate.new()
		gate.s = s
		gate.half = lerpf(t.gate_half.x, t.gate_half.y, k)
		gate.x = side * lerpf(t.gate_off.x, t.gate_off.y, k) * rng.randf_range(0.75, 1.0)
		course.gates.append(gate)
		# Иногда двое ворот подряд с одной стороны.
		if rng.randf() < 0.82:
			side = -side
		s += lerpf(t.gate_step.x, t.gate_step.y, k) * rng.randf_range(0.9, 1.15)
	# Трамплины: перед воротами из второй половины списка, на прямой к ним; за трамплином
	# полоса камней поперёк пути.
	var picks := range(3, course.gates.size() - 1)
	for i in 12:
		if picks.is_empty() or course.ramps.size() >= t.ramps:
			break
		var pick := int(picks.pop_at(rng.randi_range(0, picks.size() - 1)))
		var gate := course.gates[pick]
		var prev := course.gates[pick - 1]
		# Трамплин стоит на прямой от прошлых ворот к этим, посередине.
		var ramp := DuneCourse.Ramp.new()
		ramp.s = lerpf(prev.s, gate.s, 0.45)
		ramp.x = lerpf(prev.x, gate.x, 0.45)
		ramp.width = t.ramp_width
		var clash := false
		for other in course.ramps:
			clash = clash or absf(other.s - ramp.s) < 70.0
		if clash:
			continue
		course.ramps.append(ramp)
		for row in 3:
			var rock := DuneCourse.Rock.new()
			rock.s = ramp.s + 8.0
			rock.x = lerpf(prev.x, gate.x, 0.45 + 8.0 / maxf(gate.s - prev.s, 1.0)) + (row - 1) * 2.0
			rock.radius = 0.9
			course.rocks.append(rock)
	# Препятствия: в стороне от прямых между соседними воротами.
	var at := 110.0
	while at < t.length - 40.0:
		var k := at / t.length
		var rock := DuneCourse.Rock.new()
		rock.s = at + rng.randf_range(-6.0, 6.0)
		rock.x = rng.randf_range(-t.half_width + 1.5, t.half_width - 1.5)
		rock.tall = rng.randf() < 0.3
		rock.radius = 0.5 if rock.tall else rng.randf_range(0.8, 1.3)
		if _clear(course, rock):
			course.rocks.append(rock)
		at += 100.0 / lerpf(t.rocks_per_100.x, t.rocks_per_100.y, k) * rng.randf_range(0.6, 1.4)
	return course


## Препятствие не стоит на пути между воротами, на трамплине и вплотную к другому.
static func _clear(course: DuneCourse, rock: DuneCourse.Rock) -> bool:
	var before := Vector2(0.0, 0.0)
	for g in course.gates:
		var here := Vector2(g.s, g.x)
		if rock.s >= before.x - 4.0 and rock.s <= here.x + 4.0:
			var k := clampf((rock.s - before.x) / maxf(here.x - before.x, 1.0), 0.0, 1.0)
			if absf(rock.x - lerpf(before.y, here.y, k)) < rock.radius + 3.4:
				return false
		before = here
	for r in course.ramps:
		if absf(rock.s - r.s) < 26.0 and absf(rock.x - r.x) < r.width + 2.0:
			return false
	for other in course.rocks:
		if Vector2(other.s - rock.s, other.x - rock.x).length() < 3.0:
			return false
	return true


## Пусто, если склон годится; иначе что не так.
static func validate(course: DuneCourse, t: SportThreedTuning = null) -> String:
	if t == null:
		t = SportThreedTuning.load_default()
	if course.gates.size() < 16:
		return "ворот %d" % course.gates.size()
	if course.ramps.size() < 2:
		return "трамплинов %d" % course.ramps.size()
	if course.rocks.size() < 18:
		return "препятствий %d" % course.rocks.size()
	if course.gates[course.gates.size() - 1].half >= course.gates[0].half:
		return "ворота не сужаются"
	for g in course.gates:
		if absf(g.x) + g.half > course.half_width - 0.5:
			return "ворота на %.0f м у края" % g.s
	return ""
