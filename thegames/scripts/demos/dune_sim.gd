class_name DuneSim
extends RefCounted
## Правила демки спорт × «продвинутые» «спуск по дюне» (#124) без окна. Демка
## `sport_threed.gd` рисует это состояние и озвучивает события `events`; `simulate` гоняет бота
## по сиду целиком (проверки `demo_test`, `debug/tools/dump_dune.gd`).
##
## Райдер едет вниз сам: скорость растёт от уклона и падает от трения, воздуха и дуги. Руль
## кладёт доску на кант, кант поворачивает курс; на скорости доска перекладывается медленнее
## и поворачивает положе, поэтому дугу надо начинать заранее. Руль далеко от канта и долгий
## полный кант на скорости копят натяг `strain` (райдера трясёт и заваливает); полный натяг
## это срыв канта: скорость падает, руль на миг пропадает. В приседе воздух тормозит меньше, но
## доска поворачивает хуже. Ворота засчитываются, если райдер пересёк их линию между флагами.
## Прыжок заряжается, пока держат кнопку, и срабатывает на отпускании: полный заряд втрое
## выше. Трамплин это клин: райдер въезжает по нему и взлетает с кромки (заряд на кромке
## подбрасывает выше). В воздухе курс можно довернуть, а приземлиться надо почти по линии
## склона, иначе падение. Барьер поперёк пути перепрыгивают или объезжают; камень перелетают,
## пальму нет; удар это падение: райдер лежит и встаёт почти без скорости. Цель: доехать до
## низа, пройдя не меньше `goal_share` ворот.

const DT := 1.0 / 60.0
const G := 9.8

var course: DuneCourse
var tuning: SportThreedTuning
var countdown := 0.0
var time := 0.0
var s := 0.0
var x := 0.0
var speed := 0.0
## Курс от линии склона (плюс вправо), кант −1..1 (плюс правый), присед.
var heading := 0.0
var edge := 0.0
var crouch := false
## Высота над склоном и скорость по вертикали; в воздухе ли.
var lift := 0.0
var rise := 0.0
var airborne := false
## Высота клина трамплина под доской (на земле), заряд прыжка в секундах, натяг канта 0..1.
var ride := 0.0
var charge := 0.0
var strain := 0.0
var fallen_left := 0.0
var catch_left := 0.0
var hops := 0
var next_gate := 0
var passed := 0
var missed := 0
var falls := 0
var jumps := 0
var catches := 0
var top := 0.0
var ended := false
var finished := false
var won := false
## Итог ворот по порядку: 1 пройдены, −1 мимо.
var marks := PackedInt32Array()
## События шага: `[имя, …]`. `go`, `gate(номер, пройдены ли)`, `ramp`, `hop`, `land`,
## `catch`, `fall`, `finish`, `timeout`.
var events: Array[Array] = []
var bot_steer := 0.0
var bot_jump := false
var bot_crouch := false

var _held := false


static func create(course_: DuneCourse, tuning_: SportThreedTuning) -> DuneSim:
	var sim := DuneSim.new()
	sim.course = course_
	sim.tuning = tuning_
	sim.countdown = tuning_.countdown
	sim.speed = tuning_.start_speed
	sim.s = 6.0
	return sim


## Прогон бота без окна до конца спуска.
static func simulate(course_: DuneCourse, tuning_: SportThreedTuning, mode: AutoTest.BotMode) -> DuneSim:
	var sim := create(course_, tuning_)
	while not sim.ended:
		sim.bot(mode)
		sim.step(DT, sim.bot_steer, sim.bot_jump, sim.bot_crouch)
		sim.events.clear()
	return sim


## Сколько ворот надо пройти.
func need() -> int:
	return ceili(course.gates.size() * tuning.goal_share)


func progress() -> float:
	return clampf(s / course.length, 0.0, 1.0)


## Шаг мира: руль −1..1 (плюс вправо), держат ли прыжок, держат ли присед.
func step(dt: float, steer: float, jump: bool, crouch_: bool) -> void:
	if ended:
		return
	if countdown > 0.0:
		countdown -= dt
		if countdown <= 0.0:
			events.append([&"go"])
		return
	time += dt
	steer = clampf(steer, -1.0, 1.0)
	crouch = crouch_
	catch_left = maxf(catch_left - dt, 0.0)
	if fallen_left > 0.0:
		fallen_left -= dt
		speed = tuning.fall_speed
		s += speed * dt * 0.3
		charge = 0.0
	elif airborne:
		_air(dt, steer)
	else:
		_ground(dt, steer, jump)
	_held = jump
	_gates()
	top = maxf(top, speed)
	if s >= course.length:
		finished = true
		ended = true
		won = passed >= need()
		events.append([&"finish"])
	elif time > tuning.max_seconds:
		ended = true
		events.append([&"timeout"])


func _ground(dt: float, steer: float, jump: bool) -> void:
	var t := tuning
	if catch_left > 0.0:
		steer = 0.0
		strain = 0.0
	else:
		# Натяг канта: руль далеко от канта или долгий полный кант на скорости.
		var gain := 0.0
		if speed > t.catch_speed:
			gain = t.strain_rate * maxf(absf(steer - edge) - t.strain_slack, 0.0) + (t.strain_hold if absf(edge) > 0.92 else 0.0)
		strain = clampf(strain + (gain if gain > 0.0 else -t.strain_decay) * dt, 0.0, 1.0)
		if strain >= 1.0:
			speed *= t.catch_keep
			catch_left = t.catch_seconds
			strain = 0.0
			edge = 0.0
			steer = 0.0
			catches += 1
			events.append([&"catch"])
	edge = move_toward(edge, steer, t.edge_rate / (1.0 + speed / t.edge_speed) * dt)
	var turn := t.turn_rate / (1.0 + speed / t.turn_speed) * (t.crouch_turn if crouch else 1.0)
	heading = clampf(heading + edge * turn * dt, -t.heading_max, t.heading_max)
	var tilt := atan(course.slope(s))
	var pull := G * sin(tilt) * cos(heading) - t.friction * cos(tilt) - (t.drag_crouch if crouch else t.drag) * speed * speed \
			- t.carve_scrub * absf(edge) * speed / 32.0
	if absf(x) > course.half_width:
		pull -= t.edge_drag
	speed = maxf(speed + pull * dt, 1.5)
	var before := s
	s += speed * cos(heading) * dt
	x += speed * sin(heading) * dt
	# Заряд прыжка копится, пока держат кнопку.
	if jump:
		charge = minf(charge + dt, t.charge_seconds)
	var power := charge / t.charge_seconds
	for r in course.ramps:
		if before < r.s and s >= r.s and absf(x - r.x) <= r.width / 2.0 + 0.3:
			# Кромка трамплина: взлёт с её высоты; заряд прыжка подбрасывает выше.
			airborne = true
			lift = course.ramp_height
			ride = 0.0
			rise = t.ramp_lift * speed / t.ramp_ref * (1.0 + t.ramp_pop * power)
			charge = 0.0
			jumps += 1
			events.append([&"ramp"])
			return
	ride = course.ramp_at(s, x)
	if _held and not jump and charge > 0.0:
		# Отпустил: прыжок по заряду.
		airborne = true
		lift = ride + 0.05
		ride = 0.0
		rise = t.hop * (1.0 + t.charge_gain * power)
		charge = 0.0
		hops += 1
		events.append([&"hop", power])
		return
	_bars(before)
	_rocks()


func _air(dt: float, steer: float) -> void:
	var t := tuning
	heading = clampf(heading + steer * t.air_turn * dt, -1.6, 1.6)
	rise -= t.gravity * dt
	lift += rise * dt
	speed = maxf(speed - t.drag_crouch * speed * speed * dt, 1.5)
	s += speed * cos(heading) * dt
	x += speed * sin(heading) * dt
	_bars(s - speed * cos(heading) * dt)
	_rocks()
	if fallen_left > 0.0:
		return
	if lift <= 0.0:
		lift = 0.0
		airborne = false
		edge = 0.0
		if absf(heading) > t.land_angle:
			_fall()
		else:
			events.append([&"land"])


## Барьер: пересёк его линию в пределах ширины ниже его высоты это падение.
func _bars(before: float) -> void:
	for b in course.bars:
		if before < b.s and s >= b.s and absf(x - b.x) <= b.half and lift < b.height:
			_fall()
			s = b.s + 1.2
			return


## Удар о препятствие: камень перелетают (выше 1,1 м), пальму нет.
func _rocks() -> void:
	for r in course.rocks:
		if absf(r.s - s) > 4.0:
			continue
		if Vector2(r.s - s, r.x - x).length() < r.radius + tuning.body and (r.tall or lift < 1.1):
			_fall()
			# Райдера относит за препятствие, чтобы не упасть о него снова.
			s = r.s + r.radius + tuning.body + 0.6
			return


func _fall() -> void:
	falls += 1
	fallen_left = tuning.fall_seconds
	airborne = false
	lift = 0.0
	rise = 0.0
	charge = 0.0
	strain = 0.0
	ride = 0.0
	heading = 0.0
	edge = 0.0
	speed = tuning.fall_speed
	events.append([&"fall"])


func _gates() -> void:
	while next_gate < course.gates.size() and s >= course.gates[next_gate].s:
		var g := course.gates[next_gate]
		var ok := absf(x - g.x) <= g.half + 0.25
		passed += 1 if ok else 0
		missed += 0 if ok else 1
		marks.append(1 if ok else -1)
		events.append([&"gate", next_gate, ok])
		next_gate += 1


# --- Боты ------------------------------------------------------------------------------------

## Бот: ставит `bot_steer`, `bot_jump`, `bot_crouch`. WIN держит курс на следующие ворота (на
## трамплин, если он стоит перед ними), объезжает препятствия на пути, руль перекладывает
## плавно и отпускает, когда кант натянут, на прямом участке приседает; перед барьером на пути
## заряжает прыжок и отпускает так, чтобы перелететь; перед кромкой трамплина держит заряд, в
## воздухе выравнивает курс. LOSE едет прямо в приседе.
func bot(mode: AutoTest.BotMode) -> void:
	bot_steer = 0.0
	bot_jump = false
	bot_crouch = false
	if ended or mode == AutoTest.BotMode.OFF or countdown > 0.0:
		return
	if mode != AutoTest.BotMode.WIN:
		bot_crouch = true
		return
	if airborne:
		# В воздухе курс держит, пока он годится для приземления.
		bot_steer = clampf(-heading * 3.0, -1.0, 1.0) if absf(heading) > tuning.land_angle - 0.08 else 0.0
		return
	var aim_s := s + 60.0
	var aim_x := 0.0
	if next_gate < course.gates.size():
		var g := course.gates[next_gate]
		aim_s = g.s
		aim_x = g.x
		for r in course.ramps:
			if r.s > s + 0.5 and r.s < g.s:
				aim_s = r.s
				aim_x = r.x
				bot_jump = (r.s - s) / speed < 0.3 and absf(x - r.x) <= r.width / 2.0
	var ahead := maxf(aim_s - s, maxf(speed * tuning.bot_look * 0.35, 5.0))
	var want := clampf(atan2(aim_x - x, ahead), -0.95, 0.95)
	# Барьер на пути: зарядить прыжок и отпустить за полсекунды до него.
	for b in course.bars:
		var gap := b.s - s
		if gap <= 0.0 or gap > speed * 1.3:
			continue
		if absf(x + tan(heading) * gap - b.x) <= b.half + 0.5:
			bot_jump = gap / speed > 0.5
	# Препятствие на пути: довернуть от него.
	var threat := false
	for r in course.rocks:
		var gap := r.s - s
		if gap <= 0.5 or gap > 8.0 + speed * 0.9:
			continue
		# Камни за трамплином, на который бот уже вышел, он перелетит.
		var over := false
		for ramp in course.ramps:
			over = over or (ramp.s > s - 1.0 and r.s > ramp.s and r.s < ramp.s + 16.0 and absf(x - ramp.x) <= ramp.width / 2.0 + 1.5)
		if over:
			continue
		var at := x + tan(heading) * gap
		if absf(at - r.x) < r.radius + tuning.body + 0.9:
			threat = true
			want += (1.0 if at >= r.x else -1.0) * 0.4
	var steer := clampf((want - heading) * tuning.bot_gain, -1.0, 1.0)
	# Руль не уходит далеко от канта и отпускается, когда кант натянут: иначе срыв.
	var reach := tuning.strain_slack + (0.35 if strain < 0.3 else 0.0)
	bot_steer = clampf(steer, edge - reach, edge + reach)
	if strain > 0.6:
		bot_steer = edge * 0.6
	bot_crouch = not threat and absf(want - heading) < 0.1 and absf(heading) < 0.4
