class_name RingSim
extends RefCounted
## Правила демки гонки × low poly «кольцо с дрифтом» (#113) без окна и звука: состояние, шаг,
## боты. Демка `racing_lowpoly.gd` рисует это состояние и озвучивает события `events`;
## `simulate` гоняет бота по сиду целиком (проверки `demo_test`, `debug/tools/dump_ring.gd`).
## Правила: шлюпка на колёсах едет по замкнутой извилистой трассе, `laps` кругов против трёх
## соперников, старт последним. Газ, тормоз, руль; дрифт (держать в повороте) срывает шлюпку
## в занос: руль резче, корму несёт наружу, копится заряд, который на выходе из заноса даёт
## ускорение. Борт отбрасывает и тормозит; где бортов нет, вылет в воду стоит пары секунд и
## возвращает назад на трассу. Грязь у внутреннего края поворота режет предел скорости, полоса
## попутного ветра даёт ускорение, трамплин перебрасывает через промоину, если хватило
## скорости. Соперники едут по оси трассы со своей полосой и силой, без хитростей. Цели нет:
## гонка кончается финишем игрока, итог это место; не доехал, если после финиша последнего
## соперника прошло `grace_seconds`.

const DT := 1.0 / 60.0

class Car:
	var rival := false
	## Соперник: доля предела скорости и полоса вбок от оси.
	var skill := 1.0
	var lane := 0.0
	var pos := Vector2.ZERO
	## Курс как `rotation.y` и скорость вдоль него.
	var yaw := 0.0
	var speed := 0.0
	var vel := Vector2.ZERO
	## Место на круге, вбок от оси и всего метров от линии старта (до старта минус).
	var s := 0.0
	var d := 0.0
	var total := 0.0
	var drifting := false
	var drift_dir := 0.0
	var charge := 0.0
	var boost := 0.0
	## Полёт с трамплина: сколько осталось и сколько всего. В воде: сколько осталось.
	var air := 0.0
	var air_total := 1.0
	var sunk := 0.0
	var scraping := false
	var touching := false
	## Время финиша или −1.
	var finished := -1.0

	func forward() -> Vector2:
		return Vector2(-sin(yaw), -cos(yaw))


var tuning: RacingLowpolyTuning
var track: RingTrack
## Шлюпки: игрок первым, дальше соперники.
var cars: Array[Car] = []
var time := 0.0
var countdown := 2.0
var ended := false
## Игрок доехал до финиша.
var finished := false
var sinks := 0
var bumps := 0
var boosts := 0
## События шага для звука и эффектов: `[имя, …]`. `go`, `drift`, `boost` (от заноса), `wind`,
## `bump` (борт), `hit` (соперник), `splash`, `jump`, `land`, `lap`, `finish`, `timeout`. Демка
## читает и чистит.
var events: Array[Array] = []
## Что бот хочет на этом шаге (`bot`).
var bot_steer := 0.0
var bot_gas := 0.0
var bot_drift := false

var _respawn_s := 0.0
var _in_wind := false


static func create(track_: RingTrack, tuning_: RacingLowpolyTuning) -> RingSim:
	var sim := RingSim.new()
	sim.track = track_
	sim.tuning = tuning_
	sim.countdown = tuning_.countdown
	# Полосы соперников долями половины ширины трассы.
	var lanes: Array[float] = [-0.5 * track_.half_width, 0.5 * track_.half_width, -0.18 * track_.half_width]
	for i in tuning_.rival_skills.size() + 1:
		var car := Car.new()
		car.rival = i > 0
		# Сетка: сильный соперник впереди, игрок последним.
		var row := tuning_.rival_skills.size() - i + 1 if i > 0 else tuning_.rival_skills.size() + 1
		car.total = -4.0 * row
		car.s = track_.loop(car.total)
		car.d = lanes[(i - 1) % lanes.size()] if i > 0 else 0.8
		car.lane = car.d
		car.skill = tuning_.rival_skills[i - 1] if i > 0 else 1.0
		car.pos = track_.at(car.s, car.d)
		car.yaw = track_.yaw(car.s)
		sim.cars.append(car)
	return sim


## Прогон бота без окна до конца гонки.
static func simulate(track_: RingTrack, tuning_: RacingLowpolyTuning, mode: AutoTest.BotMode) -> RingSim:
	var sim := create(track_, tuning_)
	while not sim.ended:
		sim.bot(mode)
		sim.step(DT, sim.bot_steer, sim.bot_gas, sim.bot_drift)
		sim.events.clear()
	return sim


func player() -> Car:
	return cars[0]


func goal() -> float:
	return tuning.laps * track.length


## Круг шлюпки с единицы.
func lap_of(car: Car) -> int:
	return clampi(int(floorf(maxf(car.total, 0.0) / track.length)) + 1, 1, tuning.laps)


## Место игрока сейчас или на финише: 1 первый.
func place() -> int:
	var me := player()
	var ahead := 0
	for i in range(1, cars.size()):
		var other := cars[i]
		if me.finished >= 0.0:
			ahead += 1 if other.finished >= 0.0 and other.finished < me.finished else 0
		else:
			ahead += 1 if other.finished >= 0.0 or other.total > me.total else 0
	return ahead + 1


## Высота шлюпки над трассой в полёте с трамплина.
func air_height(car: Car) -> float:
	if car.air <= 0.0:
		return 0.0
	var k := 1.0 - car.air / car.air_total
	return tuning.ramp_height * 4.0 * k * (1.0 - k)


## Шаг мира: руль −1..1 (плюс вправо), газ −1..1 (минус тормоз), держат ли дрифт.
func step(dt: float, steer: float, gas: float, drift: bool) -> void:
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
	_step_player(player(), dt, clampf(steer, -1.0, 1.0), clampf(gas, -1.0, 1.0), drift)
	_collide(player())
	var me := player()
	if me.finished < 0.0 and me.total >= goal():
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


## Соперник: по оси трассы со своей полосой, тормозит перед поворотом по своей силе.
func _step_rival(car: Car, dt: float) -> void:
	var top := tuning.top_speed * car.skill
	var bend := track.curve_ahead(car.s, 6.0 + car.speed * 0.9)
	var want := minf(top, sqrt(tuning.rival_lateral * car.skill / maxf(bend, 0.001)))
	if car.finished >= 0.0:
		want = top * 0.5
	car.speed = move_toward(car.speed, want, (tuning.rival_accel if want > car.speed else tuning.brake) * dt)
	car.total += car.speed * dt
	car.s = track.loop(car.total)
	car.d = move_toward(car.d, car.lane, 1.5 * dt)
	car.pos = track.at(car.s, car.d)
	car.yaw = track.yaw(car.s)
	car.vel = car.forward() * car.speed
	if car.finished < 0.0 and car.total >= goal():
		car.finished = time


func _step_player(car: Car, dt: float, steer: float, gas: float, drift: bool) -> void:
	if car.sunk > 0.0:
		car.sunk -= dt
		if car.sunk <= 0.0:
			_respawn(car)
		return
	car.boost = maxf(car.boost - dt, 0.0)
	if car.air > 0.0:
		# В полёте: прямо и без руля.
		car.pos += car.vel * dt
		car.air -= dt
		_track(car)
		if car.air <= 0.0:
			events.append([&"land"])
			if track.in_gap(car.s):
				_sink(car, true)
		return
	var top := tuning.top_speed
	if track.in_mud(car.s, car.d):
		top *= tuning.mud_mult
	if car.boost > 0.0:
		top *= tuning.boost_mult
	if gas > 0.0:
		car.speed = minf(car.speed + tuning.accel * gas * dt, maxf(car.speed, top))
	elif gas < 0.0:
		car.speed = maxf(car.speed + tuning.brake * gas * dt, -tuning.reverse_speed)
	else:
		car.speed = move_toward(car.speed, 0.0, tuning.drag * dt)
	if car.speed > top:
		car.speed = move_toward(car.speed, top, tuning.brake * 0.6 * dt)
	# Дрифт: начинается на скорости в повороте, пока держат; на выходе заряд даёт ускорение.
	if not car.drifting and drift and absf(steer) > 0.3 and car.speed > tuning.drift_min_speed:
		car.drifting = true
		car.drift_dir = signf(steer)
		car.charge = 0.0
		events.append([&"drift"])
	elif car.drifting and (not drift or car.speed < tuning.drift_min_speed * 0.6):
		car.drifting = false
		if car.charge >= tuning.charge_min:
			var power := clampf(car.charge / tuning.charge_full, 0.4, 1.0)
			car.boost = maxf(car.boost, tuning.boost_seconds * power)
			car.speed += tuning.boost_kick * power
			boosts += 1
			events.append([&"boost"])
		car.charge = 0.0
	var rate := tuning.turn_rate * steer * clampf(absf(car.speed) / 6.0, 0.0, 1.0) / (1.0 + absf(car.speed) / tuning.turn_ref)
	if car.drifting:
		rate *= tuning.drift_turn
		if signf(steer) == car.drift_dir:
			car.charge += dt * absf(steer)
		car.speed *= 1.0 - tuning.drift_drag * dt
	car.yaw = wrapf(car.yaw - rate * dt * signf(car.speed if absf(car.speed) > 0.2 else 1.0), -PI, PI)
	var hold := tuning.drift_grip if car.drifting else tuning.grip
	car.vel = car.vel.lerp(car.forward() * car.speed, 1.0 - exp(-hold * dt))
	car.pos += car.vel * dt
	var before := car.s
	_track(car)
	# Ветер.
	var wind := track.in_wind(car.s, car.d)
	if wind and not _in_wind:
		car.boost = maxf(car.boost, tuning.wind_seconds)
		car.speed += tuning.boost_kick * 0.6
		events.append([&"wind"])
	_in_wind = wind
	# Трамплин: край разбега пройден вперёд.
	if track.delta(before, track.ramp_s) > 0.0 and track.delta(car.s, track.ramp_s) <= 0.0 and car.speed > 0.0:
		if car.speed >= tuning.top_speed * tuning.ramp_speed:
			car.air_total = (track.ramp_gap + 4.0) / car.speed
			car.air = car.air_total
			car.vel = track.forward(track.ramp_s) * car.speed
			car.yaw = track.yaw(track.ramp_s)
			car.drifting = false
			car.charge = 0.0
			events.append([&"jump"])
			return
		_sink(car, true)
		return
	if track.in_gap(car.s):
		_sink(car, true)
		return
	# Борт или вода.
	var side := signf(car.d)
	if track.is_open(car.s):
		car.scraping = false
		if absf(car.d) > track.half_width + 0.4:
			_sink(car, false)
		return
	var limit := track.half_width - tuning.car_half
	if absf(car.d) > limit:
		var out := track.right(car.s) * side
		car.pos -= out * (absf(car.d) - limit)
		var slip := car.vel.dot(out)
		if slip > 0.0:
			car.vel -= out * slip
		if not car.scraping:
			car.speed *= tuning.wall_keep
			bumps += 1
			events.append([&"bump"])
		car.speed = move_toward(car.speed, 0.0, tuning.wall_drag * dt)
		car.scraping = true
		car.d = side * limit
	else:
		car.scraping = false


## Место шлюпки на трассе и счёт пройденного.
func _track(car: Car) -> void:
	var before := car.s
	var lap := lap_of(car)
	var q := track.locate(car.pos, car.s)
	car.s = q.x
	car.d = q.y
	car.total += track.delta(before, car.s)
	if car.total > 0.0 and lap_of(car) > lap:
		events.append([&"lap"])


func _sink(car: Car, at_ramp: bool) -> void:
	sinks += 1
	car.sunk = tuning.sink_seconds
	car.air = 0.0
	car.drifting = false
	car.charge = 0.0
	car.boost = 0.0
	_respawn_s = track.loop(track.ramp_s - tuning.ramp_back if at_ramp else car.s - tuning.sink_back)
	events.append([&"splash"])


func _respawn(car: Car) -> void:
	car.total += track.delta(car.s, _respawn_s)
	car.s = _respawn_s
	car.d = 0.0
	car.pos = track.at(car.s, 0.0)
	car.yaw = track.yaw(car.s)
	car.speed = 0.0
	car.vel = Vector2.ZERO
	car.sunk = 0.0
	car.scraping = false


## Игрок и соперники не проезжают друг сквозь друга: соперник едет как ехал, игрока отталкивает.
func _collide(car: Car) -> void:
	if car.sunk > 0.0 or car.air > 0.0:
		return
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
			car.speed *= tuning.bump_keep
			events.append([&"hit"])
	car.touching = any
	if any:
		_track(car)


# --- Боты ------------------------------------------------------------------------------------

## Бот: ставит `bot_steer`, `bot_gas`, `bot_drift`. WIN правит на точку впереди по своей полосе
## (от грязи к наружному краю, на полосу ветра, если она не у воды), тормозит перед поворотом
## под своё поперечное ускорение, в крутом повороте дрифтует, перед трамплином не тормозит.
## LOSE не газует: стоит на сетке и не доезжает.
func bot(mode: AutoTest.BotMode) -> void:
	bot_steer = 0.0
	bot_gas = 0.0
	bot_drift = false
	if ended or mode != AutoTest.BotMode.WIN:
		return
	var car := player()
	var speed := maxf(car.speed, 0.0)
	var half := track.half_width
	var open := track.is_open(car.s) or track.is_open(car.s + 12.0)
	var lane := 0.0
	for w in track.winds:
		var ahead := track.delta(car.s, w.s0)
		if ahead > -w.half and ahead < 30.0 and absf(w.d) <= half - 2.2:
			lane = w.d
	for m in track.muds:
		var ahead := track.delta(car.s, m.s0)
		if ahead < 22.0 and track.delta(car.s, m.s1) > 0.0:
			lane = -m.side * 1.4
	if open:
		lane = 0.0
	var look := tuning.bot_look + speed * tuning.bot_look_time
	var aim := track.at(car.s + look, lane)
	var to := aim - car.pos
	var turn := angle_difference(car.yaw, atan2(-to.x, -to.y))
	bot_steer = clampf(-turn * 2.6, -1.0, 1.0)
	var bend := track.curve_ahead(car.s, 8.0 + speed * 0.9)
	var allowed := sqrt(tuning.bot_lateral / maxf(bend, 0.001))
	var to_ramp := track.delta(car.s, track.ramp_s)
	if to_ramp > 0.0 and to_ramp < 45.0:
		allowed = INF
	if open:
		allowed = minf(allowed, tuning.top_speed * 0.85)
	bot_gas = 1.0 if speed < allowed else (-1.0 if speed > allowed * 1.12 else 0.0)
	var here := track.curve(car.s + 5.0)
	bot_drift = not open and absf(here) > tuning.bot_drift_curve and speed > tuning.drift_min_speed + 1.0 \
			and absf(bot_steer) > 0.3 and signf(bot_steer) == -signf(here) and absf(car.d) < half - 1.6
