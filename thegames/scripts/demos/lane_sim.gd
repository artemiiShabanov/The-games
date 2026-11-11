class_name LaneSim
extends RefCounted
## Правила демки гонки × вектор «полосы» (#91) без окна и звука: состояние, шаг, соперники,
## боты. Демка `racing_vector.gd` рисует это состояние и озвучивает события `events`;
## `simulate` гоняет бота по сиду целиком (проверки `demo_test`, `debug/tools/dump_lanes.gd`).
## Правила: дорога из полос едет навстречу, машина перестраивается на соседнюю полосу одним
## шагом и газует, пока держат газ; без газа катится медленнее соперников. Препятствие или
## соперник впереди сбрасывают скорость и на время выключают газ; препятствие при этом
## разбивается. Кто в касании двух машин сзади, тот и уступает. Заезд кончается, когда игрок
## пересёк финиш (первым: цель) или когда первым финишировал соперник (провал).
## Соперники держат свой темп, заранее объезжают препятствия и тех, кто медленнее, а без
## свободной полосы притормаживают. Баги жанра и баланса приходят числами и флагами: `slide`
## лишних полос за перестроение (гололёд), `rival_mult` темп соперников, `walls_open` обочины
## открыты (сквозь стены: за краем дороги нет ни препятствий, ни соперников), `sneeze`
## соперник от касания уходит на обочину и сбрасывает ход.

class Car:
	var rival := false
	## Индекс соперника в `race.rivals`; у игрока −1.
	var index := -1
	## Полоса назначения и положение поперёк дороги сейчас, в полосах.
	var lane := 0
	var x := 0.0
	var dist := 0.0
	var speed := 0.0
	var pace := 0.0
	var phase := 0.0
	## Газ не работает столько секунд (после столкновения).
	var stun := 0.0
	## Соперник на обочине ещё столько секунд (баг «чих»).
	var off := 0.0
	var finished := false
	var crashes := 0


var tuning: RacingVectorTuning
var race: LaneRace
var slide := 0
var rival_mult := 1.0
var walls_open := false
var sneeze := false
var sneeze_off_s := 2.5
var sneeze_throttle := 0.5

var player: Car
var rivals: Array[Car] = []
## Разбитые препятствия, по индексам `race.obstacles`.
var broken: Array[bool] = []
var time := 0.0
var ended := false
var won := false
var rivals_finished := 0
## События шага для звука и эффектов: `[имя, …]`. `shift`, `edge` (упёрся в край дороги),
## `crash` (индекс препятствия), `bump` (удар в соперника), `spin` (индекс соперника, чих),
## `rival_crash` (индекс препятствия), `win`, `lose`. Демка читает и чистит.
var events: Array[Array] = []
## Бот хочет перестроиться на этом шаге: −1, 0 или 1 (`bot`); перестраивает хозяин, чтобы
## залипание кнопки задело и бота.
var bot_shift := 0


static func create(race_: LaneRace, tuning_: RacingVectorTuning) -> LaneSim:
	var s := LaneSim.new()
	s.race = race_
	s.tuning = tuning_
	s.player = Car.new()
	s.player.lane = race_.start_lane
	s.player.x = race_.start_lane
	s.player.speed = tuning_.cruise_speed
	for i in race_.rivals.size():
		var rv := race_.rivals[i]
		var c := Car.new()
		c.rival = true
		c.index = i
		c.lane = rv.lane
		c.x = rv.lane
		c.dist = rv.head
		c.pace = rv.pace
		c.phase = rv.phase
		c.speed = tuning_.cruise_speed
		s.rivals.append(c)
	s.broken.resize(race_.obstacles.size())
	s.broken.fill(false)
	return s


## Прогон бота без окна до конца или до `max_seconds`.
static func simulate(race_: LaneRace, tuning_: RacingVectorTuning, mode: AutoTest.BotMode,
		max_seconds := 240.0, setup := Callable()) -> LaneSim:
	var s := create(race_, tuning_)
	if setup.is_valid():
		setup.call(s)
	var dt := 1.0 / 60.0
	while not s.ended and s.time < max_seconds:
		var gas := s.bot(mode)
		if s.bot_shift != 0:
			s.shift(s.bot_shift)
		s.step(dt, gas)
		s.events.clear()
	return s


func lane_min() -> int:
	return -1 if walls_open else 0


func lane_max() -> int:
	return race.lanes if walls_open else race.lanes - 1


## Куда приведёт перестроение в сторону `dir`: на гололёде машину проносит лишнюю полосу.
func shift_target(dir: int) -> int:
	return clampi(player.lane + dir * (1 + slide), lane_min(), lane_max())


## Перестроение игрока. false, если он упёрся в край дороги.
func shift(dir: int) -> bool:
	if ended or dir == 0:
		return false
	var to := shift_target(dir)
	if to == player.lane:
		events.append([&"edge"])
		return false
	player.lane = to
	events.append([&"shift"])
	return true


## Место игрока: 1 первое.
func place() -> int:
	var n := 1
	for r in rivals:
		if r.dist > player.dist:
			n += 1
	return n


func step(dt: float, gas: bool) -> void:
	if ended:
		return
	time += dt
	_step_player(dt, gas)
	for r in rivals:
		_step_rival(r, dt)
	_resolve_contacts()
	if player.dist >= race.length:
		player.finished = true
		ended = true
		won = rivals_finished == 0
		events.append([&"win" if won else &"lose"])
		return
	for r in rivals:
		if not r.finished and r.dist >= race.length:
			r.finished = true
			rivals_finished += 1
	if rivals_finished > 0:
		ended = true
		won = false
		events.append([&"lose"])


func _step_player(dt: float, gas: bool) -> void:
	var p := player
	p.stun = maxf(p.stun - dt, 0.0)
	var target := tuning.gas_speed if gas and p.stun <= 0.0 else tuning.cruise_speed
	p.speed = move_toward(p.speed, target, (tuning.accel if target > p.speed else tuning.brake) * dt)
	p.x = move_toward(p.x, float(p.lane), dt / tuning.shift_seconds)
	p.dist += p.speed * dt
	var i := _hit_obstacle(p)
	if i >= 0:
		broken[i] = true
		p.speed = minf(p.speed, tuning.crash_speed)
		p.stun = tuning.crash_stun
		p.crashes += 1
		events.append([&"crash", i])


func _step_rival(r: Car, dt: float) -> void:
	var target := r.pace * rival_mult * (1.0 + tuning.rival_wobble * sin(time * 0.7 + r.phase))
	if r.off > 0.0:
		# Чих: едет по обочине вполсилы, потом возвращается на крайнюю полосу.
		r.off -= dt
		target *= sneeze_throttle
		if r.off <= 0.0:
			r.lane = clampi(r.lane, 0, race.lanes - 1)
	else:
		# Помеха своей полосы в обзоре и медленнее: перестроиться туда, где свободнее, шаг за шагом.
		var own := _block_ahead(r)
		if own.x < tuning.rival_look and own.y < target and absf(r.x - r.lane) < 0.15:
			var best := r.lane
			var best_gap := own.x
			for l in race.lanes:
				var g := _lane_block(r, l).x
				if g > best_gap + 40.0 or (is_equal_approx(g, best_gap) and absi(l - r.lane) < absi(best - r.lane)):
					best = l
					best_gap = g
			if best != r.lane:
				var next := r.lane + signi(best - r.lane)
				if _lane_block(r, next).x > tuning.car_len * 0.3:
					r.lane = next
			own = _block_ahead(r)
		# Не въезжать в помеху: чем она ближе, тем ближе к её скорости.
		if own.x < tuning.rival_look and own.y < target:
			target = minf(target, own.y + maxf(own.x, 0.0) * 1.2)
	r.speed = move_toward(r.speed, target, (tuning.rival_accel if target > r.speed else tuning.brake * 2.0) * dt)
	r.x = move_toward(r.x, float(r.lane), dt / tuning.shift_seconds * 0.7)
	r.dist += r.speed * dt
	if r.off <= 0.0:
		var i := _hit_obstacle(r)
		if i >= 0:
			broken[i] = true
			r.speed = minf(r.speed, tuning.crash_speed)
			r.crashes += 1
			events.append([&"rival_crash", i])


## Индекс целого препятствия, в которое въехала машина, или −1.
func _hit_obstacle(c: Car) -> int:
	var reach := (tuning.car_len + tuning.obstacle_len) / 2.0
	for i in race.obstacles.size():
		var o := race.obstacles[i]
		if o.y - c.dist > reach:
			break
		if not broken[i] and absf(o.y - c.dist) < reach and absf(o.x - c.x) < tuning.hit_lanes:
			return i
	return -1


## Ближайшая помеха впереди машины на полосе `lane`: x зазор до неё в пикселях (меньше нуля,
## если она уже рядом), y её скорость. Нет помехи: (INF, INF).
func _lane_block(c: Car, lane: int) -> Vector2:
	var out := Vector2(INF, INF)
	var reach := (tuning.car_len + tuning.obstacle_len) / 2.0
	for i in race.obstacles.size():
		var o := race.obstacles[i]
		if broken[i] or int(o.x) != lane or o.y - c.dist <= -reach:
			continue
		out = Vector2(o.y - c.dist - reach, 0.0)
		break
	for other in _cars():
		if other == c or other.off > 0.0 or not (other.lane == lane or absf(other.x - lane) < 0.6):
			continue
		var gap := other.dist - c.dist - tuning.car_len
		if gap > -tuning.car_len * 2.0 and gap < out.x:
			out = Vector2(gap, other.speed)
	return out


## Помеха впереди там, где машина сейчас: её полоса назначения и та, которую она ещё не покинула.
func _block_ahead(c: Car) -> Vector2:
	var a := _lane_block(c, c.lane)
	var here := roundi(c.x)
	if here != c.lane:
		var b := _lane_block(c, here)
		if b.x < a.x:
			a = b
	return a


func _cars() -> Array[Car]:
	var out: Array[Car] = [player]
	out.append_array(rivals)
	return out


## Касания машин: задняя уступает. Игрок сзади: удар, скорость падает и газ выключен. С багом
## «чих» соперник от касания с игроком уходит на обочину.
func _resolve_contacts() -> void:
	var cars := _cars()
	for i in cars.size():
		for j in range(i + 1, cars.size()):
			var a := cars[i]
			var b := cars[j]
			if a.off > 0.0 or b.off > 0.0:
				continue
			if absf(a.x - b.x) >= tuning.hit_lanes * 1.1 or absf(a.dist - b.dist) >= tuning.car_len:
				continue
			if sneeze and not a.rival:
				b.off = sneeze_off_s
				b.lane = race.lanes if b.x >= a.x else -1
				events.append([&"spin", b.index])
				continue
			var rear := a if a.dist <= b.dist else b
			var front := b if rear == a else a
			rear.dist = front.dist - tuning.car_len
			if rear.rival:
				rear.speed = minf(rear.speed, front.speed)
			else:
				rear.speed = minf(rear.speed, front.speed * tuning.bump_keep)
				rear.stun = tuning.crash_stun
				rear.crashes += 1
				events.append([&"bump"])


# --- Боты ------------------------------------------------------------------------------------

## Бот: возвращает, держит ли газ, и ставит `bot_shift`. WIN газует, смотрит вперёд на
## `bot_look` и уходит на полосу, где до помехи дальше всего, шаг за шагом; без выхода бросает
## газ. LOSE едет без газа и не перестраивается: соперники финишируют раньше.
func bot(mode: AutoTest.BotMode) -> bool:
	bot_shift = 0
	if ended or mode != AutoTest.BotMode.WIN:
		return false
	var p := player
	var own := _block_ahead(p)
	if absf(p.x - p.lane) < 0.15 and _reach(p, own) < tuning.bot_look:
		var best := p.lane
		var best_reach := _reach(p, own)
		for l in range(lane_min(), lane_max() + 1):
			var g := _reach(p, _lane_block(p, l)) - 30.0 * absi(l - p.lane)
			if g > best_reach + 60.0:
				best = l
				best_reach = g
		if best != p.lane:
			var dir := signi(best - p.lane)
			var to := shift_target(dir)
			var clear := to != p.lane
			var l := p.lane + dir
			while clear and l != to + dir:
				if _lane_block(p, l).x < tuning.bot_side_clear:
					clear = false
				l += dir
			if clear:
				bot_shift = dir
	# Газ: бросить, когда до помехи меньше `bot_brake_seconds` и уйти некуда.
	if bot_shift == 0 and own.x < INF:
		var closing := maxf(p.speed - own.y, 1.0)
		if own.x / closing < tuning.bot_brake_seconds * 2.0:
			return false
	return true


## Сколько машина проедет до помехи: до той, что едет медленнее, дальше, чем зазор.
func _reach(c: Car, block: Vector2) -> float:
	if block.x == INF:
		return INF
	if block.y >= c.speed:
		return INF if block.x > 0.0 else block.x
	return block.x * c.speed / maxf(c.speed - block.y, 1.0)
