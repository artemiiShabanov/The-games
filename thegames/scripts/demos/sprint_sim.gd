class_name SprintSim
extends RefCounted
## Правила демки гонки × «продвинутые» «спринт» (#122) без окна: заезд из точки в точку против
## трёх соперников. Демка `racing_threed.gd` рисует это состояние и озвучивает события
## `events`; `simulate` гоняет бота по сиду целиком (проверки `demo_test`,
## `debug/tools/dump_sprint.gd`).
##
## Машина игрока считается честно: скорость вектором, курс и угловая скорость отдельно, у
## передней и задней оси свой увод шин и свой предел сцепления. Предел зависит от покрытия,
## от скорости, от нагрузки на ось (на разгоне вес уходит назад, на торможении вперёд, на
## гребне машина легче, в ложбине тяжелее) и от того, сколько сцепления уже занято тягой или
## тормозом. Поэтому в поворот надо входить, оттормозившись; газ в повороте выносит наружу,
## резко брошенный газ или переключение посреди поворота срывают задок. Передачи
## переключаются сами: на переключении тяги нет `shift_seconds`, с отпущенным газом меньше.
## Соперники едут по оси трассы со своей полосой и тормозят перед поворотами заранее.

const DT := 1.0 / 60.0
const SUBSTEPS := 4
const G := 9.8

class Car:
	var rival := false
	var skill := 1.0
	var lane := 0.0
	var pos := Vector2.ZERO
	## Курс как `rotation.y`, скорость вектором и вдоль курса.
	var yaw := 0.0
	var vel := Vector2.ZERO
	var speed := 0.0
	var s := 0.0
	var d := 0.0
	## Только у игрока: угловая скорость (плюс влево), руль −1..1 (плюс вправо) после
	## запаздывания, передача с нуля, обороты 0..1, сколько ещё нет тяги.
	var spin := 0.0
	var steer := 0.0
	var gear := 0
	var rpm := 0.0
	var shift_left := 0.0
	## Продольное и боковое ускорение, сглаженные (перенос веса, крен и клевок кузова).
	var ax := 0.0
	var ay := 0.0
	## Покрытие под машиной и насколько шины скользят, 0..1.
	var surface := 0
	var slide := 0.0
	var scraping := false
	var touching := false
	var finished := -1.0

	func forward() -> Vector2:
		return Vector2(-sin(yaw), -cos(yaw))


var tuning: RacingThreedTuning
var track: SprintTrack
## Машины: игрок первым.
var cars: Array[Car] = []
var time := 0.0
var countdown := 2.0
var ended := false
var finished := false
var crashes := 0
var scrapes := 0
var bumps := 0
var shifts := 0
var top := 0.0
## События шага: `[имя, …]`. `go`, `shift(передача, вверх ли)`, `wall`, `crash`, `hit`,
## `finish`, `timeout`.
var events: Array[Array] = []
## Что бот хочет на этом шаге (`bot`).
var bot_steer := 0.0
var bot_gas := 0.0


static func create(track_: SprintTrack, tuning_: RacingThreedTuning) -> SprintSim:
	var sim := SprintSim.new()
	sim.track = track_
	sim.tuning = tuning_
	sim.countdown = tuning_.countdown
	var half := track_.half(0.0)
	var lanes: Array[float] = [-0.5 * half, 0.5 * half, -0.5 * half]
	for i in tuning_.rival_skills.size() + 1:
		var car := Car.new()
		car.rival = i > 0
		# Сетка: сильный соперник впереди, игрок последним.
		var row := tuning_.rival_skills.size() - i + 1 if i > 0 else tuning_.rival_skills.size() + 1
		car.s = 34.0 - 7.0 * row
		car.d = lanes[(i - 1) % lanes.size()] if i > 0 else 0.5 * half
		car.lane = car.d
		car.skill = tuning_.rival_skills[i - 1] if i > 0 else 1.0
		car.pos = track_.at(car.s, car.d)
		car.yaw = track_.yaw(car.s)
		sim.cars.append(car)
	return sim


## Прогон бота без окна до конца гонки.
static func simulate(track_: SprintTrack, tuning_: RacingThreedTuning, mode: AutoTest.BotMode) -> SprintSim:
	var sim := create(track_, tuning_)
	while not sim.ended:
		sim.bot(mode)
		sim.step(DT, sim.bot_steer, sim.bot_gas)
		sim.events.clear()
	return sim


func player() -> Car:
	return cars[0]


## Место игрока сейчас или на финише: 1 первый.
func place() -> int:
	var me := player()
	var ahead := 0
	for i in range(1, cars.size()):
		var other := cars[i]
		if me.finished >= 0.0:
			ahead += 1 if other.finished >= 0.0 and other.finished < me.finished else 0
		else:
			ahead += 1 if other.finished >= 0.0 or other.s > me.s else 0
	return ahead + 1


func progress() -> float:
	return clampf(player().s / track.length, 0.0, 1.0)


## Сцепление покрытия в точке трассы: доля от плотной дороги.
func grip_at(s: float, d := 0.0) -> float:
	return tuning.surface_grip[surface_at(s, d)]


func surface_at(s: float, d: float) -> int:
	if absf(d) > track.half(s) + 0.5:
		return SprintTrack.Surface.VERGE
	return track.surface(s)


## Нагрузка от рельефа на скорости `v`: на гребне меньше единицы, в ложбине больше.
func load_at(s: float, v: float) -> float:
	return clampf(1.0 - v * v * track.crest(s) / G, 0.35, 1.6)


## Тяга на скорости `v` при полном газе на лучшей передаче (соперники и бот).
func pull_at(v: float) -> float:
	for g in tuning.gear_speeds.size():
		if v < tuning.gear_speeds[g] * tuning.shift_up or g == tuning.gear_speeds.size() - 1:
			return tuning.gear_pulls[g] * _shape(v / tuning.gear_speeds[g])
	return 0.0


## Доля тяги по оборотам: пик в середине, у отсечки тяги нет.
static func _shape(rpm: float) -> float:
	if rpm >= 1.02:
		return 0.0
	return lerpf(0.6, 1.0, sin(PI * clampf(rpm, 0.08, 1.0)))


## Шаг мира: руль −1..1 (плюс вправо), газ −1..1 (минус тормоз и задний ход).
func step(dt: float, steer: float, gas: float) -> void:
	if ended:
		return
	if countdown > 0.0:
		countdown -= dt
		if countdown <= 0.0:
			events.append([&"go"])
		return
	time += dt
	for i in range(1, cars.size()):
		_step_rival(cars[i], dt)
	var me := player()
	for k in SUBSTEPS:
		_step_player(me, dt / SUBSTEPS, clampf(steer, -1.0, 1.0), clampf(gas, -1.0, 1.0))
	_bounds(me)
	_collide(me)
	top = maxf(top, me.speed)
	if me.finished < 0.0 and me.s >= track.length:
		me.finished = time
		finished = true
		ended = true
		events.append([&"finish"])
		return
	var last := 0.0
	var all := true
	for i in range(1, cars.size()):
		all = all and cars[i].finished >= 0.0
		last = maxf(last, cars[i].finished)
	if (all and time > last + tuning.grace_seconds) or time > tuning.max_seconds:
		ended = true
		events.append([&"timeout"])


## Скорость, с которой можно быть в точке `s`, чтобы пройти всё впереди: предел поворота по
## боковому ускорению `lateral` и торможение `braking` до него.
func speed_plan(s: float, v: float, lateral: float, braking: float) -> float:
	var best := INF
	var n := track.count()
	var first := clampi(int(s / track.step), 0, n - 1)
	var steps := int((v * v / (2.0 * braking) + 30.0) / track.step)
	for k in steps + 1:
		var i := mini(first + k, n - 1)
		var mu := tuning.surface_grip[track.surfaces[i]]
		var weight := clampf(1.0 - v * v * track.crests[i] / G, 0.35, 1.6)
		best = minf(best, lateral * mu * weight / maxf(track.bends[i], 0.0005) + 2.0 * braking * mu * k * track.step)
	return sqrt(best)


## Соперник: по оси трассы со своей полосой, разгоняется по тем же передачам, тормозит заранее.
func _step_rival(car: Car, dt: float) -> void:
	var want := minf(speed_plan(car.s, car.speed, tuning.rival_lateral * car.skill, tuning.rival_brake),
			tuning.gear_speeds[tuning.gear_speeds.size() - 1])
	if car.finished >= 0.0:
		want = minf(want, 12.0)
	var mu := grip_at(car.s, car.d)
	var drag := tuning.rolling + tuning.air * car.speed * car.speed + tuning.surface_drag[track.surface(car.s)] + G * track.slope(car.s)
	if car.speed < want:
		car.speed = minf(car.speed + (minf(pull_at(car.speed) * car.skill, mu * tuning.grip * 0.5) - drag) * dt, want)
	else:
		car.speed = maxf(car.speed - tuning.rival_brake * mu * dt, want)
	car.speed = maxf(car.speed, 0.0)
	car.s += car.speed * dt
	var room := track.half(car.s) - 1.3
	car.d = move_toward(car.d, clampf(car.lane, -room, room), 2.5 * dt)
	car.d = clampf(car.d, -room, room)
	car.pos = track.at(car.s, car.d)
	car.yaw = track.yaw(car.s)
	car.vel = car.forward() * car.speed
	if car.finished < 0.0 and car.s >= track.length:
		car.finished = time


func _step_player(car: Car, dt: float, steer: float, gas: float) -> void:
	var t := tuning
	var fwd := car.forward()
	var left := Vector2(-fwd.y, fwd.x) * -1.0
	left = Vector2(fwd.y, -fwd.x)
	var vx := car.vel.dot(fwd)
	var vy := car.vel.dot(left)
	var v := car.vel.length()
	car.surface = surface_at(car.s, car.d)
	var mu := t.surface_grip[car.surface] * maxf(1.0 - t.grip_fade * v, 0.5)
	var hill := track.slope(car.s) * fwd.dot(track.forward(car.s))
	var weight := load_at(car.s, v)
	# Руль запаздывает; чем быстрее, тем меньше угол колёс.
	car.steer = move_toward(car.steer, steer, t.steer_rate * dt)
	var wheel := -car.steer * lerpf(t.steer_low, t.steer_high, clampf(absf(vx) / t.gear_speeds[t.gear_speeds.size() - 1], 0.0, 1.0))
	# Передачи.
	var last := t.gear_speeds.size() - 1
	car.rpm = clampf(absf(vx) / t.gear_speeds[car.gear], 0.0, 1.1)
	if car.shift_left > 0.0:
		car.shift_left -= dt
	elif gas > 0.0 and car.gear < last and car.rpm >= t.shift_up:
		car.gear += 1
		car.shift_left = t.shift_soft if gas < 0.35 else t.shift_seconds
		shifts += 1
		events.append([&"shift", car.gear, true])
	elif car.gear > 0 and absf(vx) < t.gear_speeds[car.gear - 1] * t.shift_down:
		car.gear -= 1
		car.shift_left = t.shift_soft
		events.append([&"shift", car.gear, false])
	# Нагрузка на оси: вес идёт за продольным ускорением.
	var front := clampf(0.5 - car.ax * t.weight_shift, 0.2, 0.8) * weight
	var rear := clampf(0.5 + car.ax * t.weight_shift, 0.2, 0.8) * weight
	var cap_front := mu * t.grip * front * 2.0
	var cap_rear := mu * t.grip * rear * 2.0
	# Продольные силы: тяга на задней оси (не больше её сцепления), тормоз на обеих.
	var drive := 0.0
	var braking := 0.0
	var reverse := gas < 0.0 and vx < 0.6
	if reverse:
		drive = -t.gear_pulls[0] * 0.6 * -gas if vx > -t.reverse_speed else 0.0
	elif gas > 0.0 and car.shift_left <= 0.0:
		drive = t.gear_pulls[car.gear] * _shape(car.rpm) * gas
	elif gas < 0.0:
		braking = t.brake * -gas
	drive = clampf(drive, -cap_rear * 0.5, cap_rear * 0.5)
	braking = minf(braking, mu * t.grip * weight)
	var coast := t.engine_brake if (gas <= 0.0 or car.shift_left > 0.0) and not reverse else 0.0
	var resist := (t.rolling + t.surface_drag[car.surface] + coast + braking) * signf(vx) if absf(vx) > 0.2 else 0.0
	var along := drive - resist - t.air * vx * absf(vx) - G * hill
	if absf(vx) <= 0.2 and drive == 0.0:
		along = -vx / dt * 0.5
	# Занятое продольной силой сцепление уже не держит вбок.
	var used_rear := clampf(absf(drive) / maxf(cap_rear * 0.5, 0.01), 0.0, 1.0)
	var used_brake := clampf(braking / maxf(mu * t.grip * weight, 0.01), 0.0, 1.0)
	cap_rear *= t.rear_bias * sqrt(maxf(1.0 - used_rear * used_rear * 0.45 - used_brake * used_brake * 0.5, 0.2))
	cap_front *= sqrt(maxf(1.0 - used_brake * used_brake * 0.6, 0.12))
	var a := t.wheelbase / 2.0
	if absf(vx) < 3.0:
		# Медленно: колёса не скользят, машина едет по дуге руля.
		car.spin = vx * tan(wheel) / t.wheelbase
		vy = move_toward(vy, 0.0, 12.0 * dt)
		vx += along * dt
		car.slide = 0.0
		car.ay = lerpf(car.ay, 0.0, 1.0 - exp(-t.weight_follow * dt))
	else:
		var slip_front := atan2(vy + a * car.spin, absf(vx)) - wheel * signf(vx)
		var slip_rear := atan2(vy - a * car.spin, absf(vx))
		var side_front := -cap_front * 0.5 * tanh(t.cornering * slip_front)
		var side_rear := -cap_rear * 0.5 * tanh(t.cornering * slip_rear)
		var dvx := along + vy * car.spin - side_front * sin(wheel)
		var dvy := side_front * cos(wheel) + side_rear - vx * car.spin
		var dspin := (a * side_front * cos(wheel) - a * side_rear) / (t.inertia * a * a)
		# Помощь игроку (плейтест 2026-11-13): машину тянет к тому повороту, которого просит
		# руль, и боковое скольжение гаснет само, поэтому занос ловится и не переходит в волчок.
		var asked := clampf(vx * tan(wheel) / t.wheelbase, -mu * t.grip / absf(vx), mu * t.grip / absf(vx))
		dspin -= t.stability * (car.spin - asked)
		vy *= exp(-t.slide_damp * dt)
		vx += dvx * dt
		vy += dvy * dt
		car.spin += dspin * dt
		car.slide = lerpf(car.slide, clampf((maxf(absf(slip_front), absf(slip_rear)) - 0.1) / 0.25, 0.0, 1.0), 1.0 - exp(-10.0 * dt))
		car.ay = lerpf(car.ay, side_front + side_rear, 1.0 - exp(-t.weight_follow * dt))
	car.ax = lerpf(car.ax, along, 1.0 - exp(-t.weight_follow * dt))
	car.yaw = wrapf(car.yaw + car.spin * dt, -PI, PI)
	fwd = car.forward()
	left = Vector2(fwd.y, -fwd.x)
	car.vel = fwd * vx + left * vy
	car.speed = vx
	car.pos += car.vel * dt
	var q := track.locate(car.pos, car.s)
	car.s = q.x
	car.d = q.y


## Борт за обочиной (на сужении сразу за дорогой), камни на плечах, начало трассы.
func _bounds(car: Car) -> void:
	var limit := track.half(car.s) + tuning.verge * track.shoulder(car.s) - 0.9
	var touching := false
	if absf(car.d) > limit or car.s < -6.0:
		touching = true
		var side := signf(car.d)
		var out := track.right(car.s) * side
		if car.s < -6.0:
			out = -track.forward(car.s)
			car.pos = track.at(-6.0, clampf(car.d, -limit, limit))
		else:
			car.pos = track.at(car.s, side * limit)
		var into := car.vel.dot(out)
		if into > 0.0:
			car.vel -= out * into
			if into > 2.0 and not car.scraping:
				car.vel *= tuning.wall_keep
				car.spin *= 0.3
				scrapes += 1
				events.append([&"wall"])
		# Борт доворачивает машину вдоль себя.
		car.yaw = lerp_angle(car.yaw, track.yaw(car.s), 0.12)
		car.spin *= 0.8
	car.scraping = touching
	for rock in track.rocks:
		var at := track.at(rock.x, rock.y)
		var gap := car.pos - at
		var reach := rock.z + 0.9
		if gap.length() < reach:
			var away := gap.normalized() if gap.length() > 0.01 else -car.forward()
			car.pos = at + away * reach
			if car.vel.dot(away) < -1.0:
				car.vel = (car.vel - away * car.vel.dot(away)) * tuning.rock_keep
				car.spin = 0.0
				crashes += 1
				events.append([&"crash"])
	var q := track.locate(car.pos, car.s)
	car.s = q.x
	car.d = q.y
	car.speed = car.vel.dot(car.forward())


## Игрок и соперники не проезжают друг сквозь друга: соперник едет как ехал, игрока отталкивает.
func _collide(car: Car) -> void:
	var any := false
	for i in range(1, cars.size()):
		var other := cars[i]
		var gap := car.pos - other.pos
		var reach := tuning.car_radius * 2.0
		if gap.length() >= reach:
			continue
		any = true
		var away := gap.normalized() if gap.length() > 0.01 else -car.forward()
		car.pos = other.pos + away * reach
		if not car.touching:
			car.vel *= tuning.bump_keep
			bumps += 1
			events.append([&"hit"])
	car.touching = any
	if any:
		var q := track.locate(car.pos, car.s)
		car.s = q.x
		car.d = q.y


# --- Боты ------------------------------------------------------------------------------------

## Бот: ставит `bot_steer` и `bot_gas`. WIN правит на точку впереди по своей полосе (соперника
## обходит сбоку, на сужении держится оси), тормозит заранее под скорость поворота с учётом
## покрытия и рельефа, в повороте газ держит ровно. LOSE не газует.
func bot(mode: AutoTest.BotMode) -> void:
	bot_steer = 0.0
	bot_gas = 0.0
	if ended or mode != AutoTest.BotMode.WIN:
		return
	var car := player()
	var speed := maxf(car.speed, 0.0)
	var lane := 0.0
	var tight := track.is_narrow(car.s) or track.is_narrow(car.s + 30.0 + speed)
	var follow := INF
	for i in range(1, cars.size()):
		var other := cars[i]
		var ahead := other.s - car.s
		if ahead > -2.0 and ahead < 10.0 + speed * 0.6 and other.finished < 0.0:
			if tight:
				# На сужении не обгоняют: держится за соперником.
				if ahead > 0.0 and ahead < 9.0:
					follow = minf(follow, other.speed)
			else:
				var room := track.half(other.s) - 1.5
				lane = clampf(other.d + (3.2 if other.d < 0.0 else -3.2), -room, room)
	var look := tuning.bot_look + speed * tuning.bot_look_time
	var aim := track.at(car.s + look, lane)
	var to := aim - car.pos
	var turn := angle_difference(car.yaw, atan2(-to.x, -to.y))
	bot_steer = clampf(-turn * 2.8 + car.spin * 0.12, -1.0, 1.0)
	var allowed := minf(speed_plan(car.s, speed, tuning.bot_lateral, tuning.bot_brake), follow)
	if speed < allowed - 0.6:
		# Скользит: газ мягче.
		bot_gas = 1.0 if car.slide < 0.35 else 0.4
	elif speed > allowed + 0.4:
		bot_gas = -clampf((speed - allowed) / 3.0, 0.3, 1.0)
	else:
		bot_gas = 0.35
