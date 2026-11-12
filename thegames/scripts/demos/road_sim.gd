class_name RoadSim
extends RefCounted
## Правила гонки × 16/32-bit (#99) без окна и звука: герой, одиннадцать соперников, нитро,
## монеты, места, боты. Демка `racing_bit16.gd` рисует это состояние и озвучивает события;
## `simulate` гоняет бота по сиду целиком (проверки `demo_test`, `debug/tools/dump_road.gd`).
## Мир шагает ровно 60 раз в секунду. Правила: газ разгоняет, без газа накат; поворот выносит
## к обочине тем сильнее, чем выше скорость и круче изгиб; обочина тормозит до доли наибольшей
## скорости, проп на ней сбрасывает скорость почти до нуля; догнал соперника в его полосе:
## удар, скорость падает до доли его, герой мигает (`hit`). Нитро три раза за заезд. Старт
## последним из двенадцати; заезд кончается, когда герой доехал до финиша (плейтест
## 2026-11-12: не обрывать, показать место), финиш в тройке это победа.
## Баги приходят числами: `grip` руль на льду (поперёк с инерцией), `rival_mult` скорость
## соперников, `sneeze` соперник от касания крутится и уходит на обочину, `walls_open` пропы
## не держат и обочина не тормозит, `finish_late` настоящий финиш дальше нарисованного.

const DT := 1.0 / 60.0

class Car:
	var x := 0.0
	var z := 0.0
	var speed := 0.0
	## Доля наибольшей скорости, к которой стремится соперник.
	var pace := 0.0
	var target_x := 0.0
	var tint := 0
	var finished := false
	## Секунды на обочине после чиха.
	var spin := 0.0

var tuning: RacingBit16Tuning
var track: RoadTrack
var grip := 1.0
var rival_mult := 1.0
var sneeze := false
var sneeze_seconds := 2.5
var sneeze_throttle := 0.5
var walls_open := false
var finish_late := 0.0

## Герой: поперёк, расстояние, скорость, скорость поперёк (на льду).
var x := 0.0
var z := 0.0
var speed := 0.0
var x_vel := 0.0
var nitros := 3
var nitro_left := 0.0
var rivals: Array[Car] = []
var coin_taken := PackedByteArray()
var coins_got := 0
var bumps := 0
var crashes := 0
## Секунды после удара или аварии: демка мигает повозкой и сыплет искрами.
var hit := 0.0
## Толчок поперёк после аварии, гаснет за полсекунды: герой не прыгает, а съезжает.
var push := 0.0
var time := 0.0
var ended := false
var won := false
## Место на финише или сейчас.
var place := 12
## События шага: `[имя, …]`. `nitro`, `bump`, `crash`, `coin`, `pass` (обогнал), `passed`
## (обогнали), `finish`, `win`, `lose`. Демка читает и чистит.
var events: Array[Array] = []
## Ввод бота на этом шаге.
var bot_gas := false
var bot_nitro := false

var _finishers := 0
## Монеты по порядку расстояния: первая, до которой герой ещё не доехал.
var _next_coin := 0
var _last_place := 12


static func create(track_: RoadTrack, tuning_: RacingBit16Tuning) -> RoadSim:
	var s := RoadSim.new()
	s.track = track_
	s.tuning = tuning_
	s.nitros = tuning_.nitros
	for r in track_.rivals:
		var c := Car.new()
		c.x = r.x
		c.target_x = r.x
		c.z = r.z
		c.pace = r.speed
		c.tint = r.tint
		s.rivals.append(c)
	s.coin_taken.resize(track_.coins.size())
	s.coin_taken.fill(0)
	s.place = s.rivals.size() + 1
	s._last_place = s.place
	return s


static func simulate(track_: RoadTrack, tuning_: RacingBit16Tuning, mode: AutoTest.BotMode, setup := Callable()) -> RoadSim:
	var s := create(track_, tuning_)
	if setup.is_valid():
		setup.call(s)
	while not s.ended:
		var axis := s.bot(mode)
		s.step(axis, s.bot_gas, s.bot_nitro)
		s.events.clear()
	return s


## Финиш, который засчитывается: с багом «финиш на пляже» дальше нарисованного.
func finish_z() -> float:
	return track.finish_z() + finish_late


func max_now() -> float:
	return tuning.max_speed * (tuning.nitro_mult if nitro_left > 0.0 else 1.0)


## Шаг мира в 1/60 секунды: `axis` руль −1..1, `gas` зажат ли газ, `nitro` нажато ли нитро.
func step(axis: float, gas: bool, nitro: bool) -> void:
	if ended:
		return
	time += DT
	if nitro and nitros > 0 and nitro_left <= 0.0:
		nitros -= 1
		nitro_left = tuning.nitro_seconds
		events.append([&"nitro"])
	nitro_left = maxf(nitro_left - DT, 0.0)
	var seg := track.seg_at(z)
	var pct := speed / tuning.max_speed
	# Руль и вынос на повороте. На льду поперечная скорость догоняет руль медленно.
	var want := axis * tuning.steer * pct - pct * pct * track.curve[seg] * tuning.centrifugal * tuning.steer
	x_vel = want if grip >= 1.0 else lerpf(x_vel, want, minf(grip * DT * 6.0, 1.0))
	push = move_toward(push, 0.0, 4.0 * DT)
	hit = maxf(hit - DT, 0.0)
	x = clampf(x + (x_vel + push) * DT, -3.0, 3.0)
	var top := max_now()
	if gas or nitro_left > 0.0:
		speed = minf(speed + tuning.accel * (1.6 if nitro_left > 0.0 else 1.0) * DT, top)
	else:
		speed = maxf(speed - tuning.coast * DT, 0.0)
	if speed > top:
		speed = maxf(speed - tuning.coast * DT, top)
	if absf(x) > 1.0 and not walls_open and speed > tuning.max_speed * tuning.offroad_limit:
		speed = maxf(speed - tuning.offroad_decel * DT, tuning.max_speed * tuning.offroad_limit)
	var z0 := z
	z += speed * DT
	_props(z0)
	_coins(z0)
	_step_rivals()
	_bump()
	_rank()
	if z >= finish_z():
		ended = true
		won = place <= 3
		events.append([&"finish", place])
		events.append([&"win" if won else &"lose"])
	elif time >= tuning.max_seconds:
		ended = true
		events.append([&"lose"])


## Проп на обочине между прошлым и новым `z`: удар, скорость почти до нуля.
func _props(z0: float) -> void:
	if walls_open or absf(x) < 1.1:
		return
	var s0 := int(floor(z0 / RoadTrack.SEG))
	var s1 := int(floor(z / RoadTrack.SEG))
	if s1 == s0:
		return
	for p in track.props_in(s1 % track.count()):
		if absf(p.y - x) < tuning.prop_width:
			speed = tuning.max_speed * tuning.crash_speed
			push = -signf(x) * 1.2
			x_vel = 0.0
			hit = tuning.hit_seconds
			crashes += 1
			events.append([&"crash"])
			return


func _coins(z0: float) -> void:
	for i in range(_next_coin, track.coins.size()):
		var c := track.coins[i]
		if c.y > z:
			break
		_next_coin = i + 1
		if coin_taken[i] == 0 and c.y > z0 and absf(c.x - x) < tuning.coin_width:
			coin_taken[i] = 1
			coins_got += 1
			events.append([&"coin"])


## Соперники держат свою скорость, обходят медленного впереди; финишировавшие стоят.
func _step_rivals() -> void:
	for c in rivals:
		if c.finished:
			continue
		var pace := c.pace * rival_mult * tuning.max_speed
		if c.spin > 0.0:
			c.spin -= DT
			pace *= sneeze_throttle
		# Разгон как у героя, на поворотах без потерь: лидер на пределе едет весь заезд на пределе.
		c.speed = move_toward(c.speed, pace, tuning.accel * DT)
		# Медленный впереди в той же полосе: перестроиться.
		for o in rivals:
			if o != c and not o.finished and o.z > c.z and o.z - c.z < tuning.rival_look * RoadTrack.SEG \
					and absf(o.x - c.x) < tuning.car_width and o.speed < c.speed:
				c.target_x = -0.5 if o.x > 0.0 else 0.5
				if c.target_x == o.x:
					c.target_x = 0.0
				break
		if c.spin <= 0.0:
			c.x = move_toward(c.x, c.target_x, tuning.rival_steer * DT)
		c.z += c.speed * DT
		if c.z >= track.finish_z():
			c.finished = true
			c.z = track.finish_z() + _finishers * RoadTrack.SEG
			_finishers += 1


## Догнал соперника в его полосе: удар. С чихом соперник крутится и уходит на обочину.
func _bump() -> void:
	for c in rivals:
		if c.finished:
			continue
		var gap := c.z - z
		if gap < 0.0 or gap > RoadTrack.SEG or absf(c.x - x) > tuning.car_width:
			continue
		if sneeze:
			if c.spin <= 0.0:
				c.spin = sneeze_seconds
				c.target_x = 1.6 if c.x >= x else -1.6
				events.append([&"spin"])
			continue
		if speed > c.speed and hit <= 0.0:
			speed = c.speed * tuning.bump_keep
			push = 0.8 * (signf(x - c.x) if x != c.x else 1.0)
			hit = tuning.hit_seconds
			bumps += 1
			events.append([&"bump"])


func _rank() -> void:
	var ahead := 0
	for c in rivals:
		if c.finished or c.z > z:
			ahead += 1
	place = ahead + 1
	if place < _last_place:
		events.append([&"pass"])
	elif place > _last_place:
		events.append([&"passed"])
	_last_place = place


# --- Боты --------------------------------------------------------------------------------------

## Бот: возвращает руль и ставит `bot_gas`, `bot_nitro`. WIN держит полосу, свободную от
## соперников на `bot_look` сегментов вперёд (с монетами лучше), рулит с поправкой на вынос,
## сбрасывает газ, если на крутом повороте его выносит за край, жмёт нитро на прямой. LOSE
## едет по краю дороги без нитро и газует пять шестых времени: доезжает, но не в тройке.
func bot(mode: AutoTest.BotMode) -> float:
	bot_nitro = false
	bot_gas = true
	if ended:
		return 0.0
	if mode != AutoTest.BotMode.WIN:
		# Едет по краю дороги без нитро и газует две трети времени: доезжает, но не в тройке.
		bot_gas = fmod(time, 1.5) < 1.25
		return clampf((0.85 - x) * 3.0, -1.0, 1.0)
	var target := _bot_lane()
	var seg := track.seg_at(z)
	var pct := speed / tuning.max_speed
	var curve := track.curve[seg]
	# На крутом повороте держаться внутренней полосы: вынос тянет наружу.
	if absf(curve) > 3.0:
		target = clampf(target + signf(curve) * 0.4, -0.6, 0.6)
	var drift := -pct * pct * curve * tuning.centrifugal * tuning.steer
	# Руль на цель с поправкой на вынос; не хватает руля и уже выносит наружу, отпустить газ.
	var need := ((target - x) * 3.0 - drift / maxf(tuning.steer * pct, 0.3))
	var axis := clampf(need, -1.0, 1.0)
	if absf(drift) > tuning.steer * pct * 0.8 and x * drift > 0.0 and absf(x) > 0.35:
		bot_gas = false
	if nitros > 0 and nitro_left <= 0.0 and speed > tuning.max_speed * 0.9 and absf(x) < 0.7 and _straight_ahead() \
			and z > track.finish_z() * (0.12 + 0.25 * (tuning.nitros - nitros)):
		bot_nitro = true
	return axis


func _bot_lane() -> float:
	var best := x
	var best_score := -INF
	for lane in [-0.6, 0.0, 0.6]:
		var score := -absf(lane - x) * 0.5
		for c in rivals:
			var gap := c.z - z
			if c.finished or gap < -RoadTrack.SEG * 0.5 or gap > tuning.bot_look * RoadTrack.SEG:
				continue
			if absf(c.x - lane) < tuning.car_width + 0.08:
				score -= 10.0 - gap / RoadTrack.SEG * 0.5
		for i in track.coins.size():
			var cz := track.coins[i].y - z
			if coin_taken[i] == 0 and cz > 0.0 and cz < tuning.bot_look * RoadTrack.SEG and absf(track.coins[i].x - lane) < 0.1:
				score += 0.6
		if score > best_score:
			best_score = score
			best = lane
	return best


## Впереди на `bot_nitro_straight` сегментов нет крутого поворота: на нитро (около 160
## сегментов за 2 с) крутой поворот не удержать, пологий удержать можно.
func _straight_ahead() -> bool:
	var s := track.seg_at(z)
	for i in tuning.bot_nitro_straight:
		if absf(track.curve[(s + i) % track.count()]) > tuning.bot_nitro_curve:
			return false
	return true
