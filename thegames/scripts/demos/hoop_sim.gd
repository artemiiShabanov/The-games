class_name HoopSim
extends RefCounted
## Правила демки спорт × low poly «броски в кольцо» (#115) без окна: шкала силы, полёт мяча в
## объёме с отскоками от обруча и щита, ветер, ездящее кольцо, очки, серия и боты. Демка
## `sport_lowpoly.gd` рисует это состояние и озвучивает события `events`; `simulate` гоняет
## бота по плану целиком (проверки `demo_test`, `debug/tools/dump_hoop.gd`).
##
## Бросок: прицел это поворот в стороны от линии на кольцо; зажал, шкала силы пошла туда и
## обратно, отпустил, мяч полетел. В зелёной зоне шкалы сила точная: мяч входит чисто, если
## прицел верный. Мимо зоны мяч бьётся об обруч или щит и может всё равно упасть в кольцо.
## Попадание: 2 или 3 очка по расстоянию, чистое (ничего не задел) на очко дороже; после трёх
## попаданий подряд мяч горит и бросок стоит вдвое, пока серия не прервётся.

const DT := 1.0 / 60.0
const SUBSTEPS := 4

enum Phase { COUNTDOWN, AIM, CHARGE, FLIGHT, RESULT, MOVE, DONE }

class Ball:
	var pos := Vector3.ZERO
	var vel := Vector3.ZERO
	var age := 0.0
	var touched := false
	var scored := false
	var done := false
	## Что задел на последнем шаге: `rim`, `board` или пусто.
	var hit := &""


var plan: HoopPlan
var tuning: SportLowpolyTuning
var phase := Phase.COUNTDOWN
var countdown := 0.0
var time := 0.0
var index := 0
## Прицел: радианы вправо от линии на кольцо.
var yaw := 0.0
## Прицел вверх (плюс) и вниз от кольца: меняет подъём броска.
var pitch := 0.0
## Шкала силы 0..1 и сколько секунд зажато.
var power := 0.0
var charge := 0.0
var ball: Ball
var timer := 0.0
var score := 0
var streak := 0
var made := 0
var clean := 0
## Итог каждого сделанного броска: очки (0 мимо).
var results: Array[int] = []
var ended := false
var finished := false
## События шага для звука и эффектов: `[имя, …]`. `go`, `charge`, `throw`, `rim`, `board`,
## `score(очки, чисто, горит)`, `miss`, `next`, `finish`, `fail`. Демка читает и чистит.
var events: Array[Array] = []
## Что бот хочет на этом шаге (`bot`).
var bot_yaw := 0.0
var bot_hold := false

var _held := false
var _bot_wait := 0.0


static func create(plan_: HoopPlan, tuning_: SportLowpolyTuning) -> HoopSim:
	var sim := HoopSim.new()
	sim.plan = plan_
	sim.tuning = tuning_
	sim.countdown = tuning_.countdown
	return sim


## Прогон бота без окна до конца плана.
static func simulate(plan_: HoopPlan, tuning_: SportLowpolyTuning, mode: AutoTest.BotMode) -> HoopSim:
	var sim := create(plan_, tuning_)
	while not sim.ended:
		sim.bot(mode, DT)
		sim.step(DT, sim.bot_yaw, sim.bot_hold)
		sim.events.clear()
	return sim


# --- Геометрия -------------------------------------------------------------------------------

## Середина обруча, когда кольцо стоит.
static func rim_rest(t: SportLowpolyTuning) -> Vector3:
	return Vector3(0.0, t.rim_y * t.hoop_scale - t.hoop_sink, t.rim_z * t.hoop_scale)


## Куда съехало кольцо в момент `at`.
static func hoop_shift(shot: HoopPlan.Shot, at: float) -> float:
	if shot.move_amp <= 0.0:
		return 0.0
	return shot.move_amp * sin(TAU * at / shot.move_period + shot.move_phase)


## Направление от точки на кольцо по земле и вправо от него.
static func forward(shot: HoopPlan.Shot, t: SportLowpolyTuning) -> Vector3:
	var to := rim_rest(t) - shot.pos
	to.y = 0.0
	return to.normalized()


static func right(shot: HoopPlan.Shot, t: SportLowpolyTuning) -> Vector3:
	var f := forward(shot, t)
	return Vector3(-f.z, 0.0, f.x)


## Откуда вылетает мяч.
static func launch_pos(shot: HoopPlan.Shot, t: SportLowpolyTuning) -> Vector3:
	return shot.pos + Vector3(0.0, t.launch_height, 0.0) + forward(shot, t) * t.launch_forward


## Скорость вылета по шкале силы: середина зелёной зоны это середина чистого диапазона.
static func speed_of(shot: HoopPlan.Shot, t: SportLowpolyTuning, power_: float) -> float:
	var mid := (shot.v_lo + shot.v_hi) / 2.0
	var half := (shot.v_hi - shot.v_lo) / 2.0 * t.zone_fill
	var off := power_ - shot.zone
	if absf(off) <= shot.zone_half:
		return mid + off / shot.zone_half * half
	# За краем зоны ошибка растёт быстро: рядом с зоной мяч цепляет обруч, дальше летит мимо.
	return mid + signf(off) * (half + (absf(off) - shot.zone_half) * t.miss_gain * mid)


static func make_ball(shot: HoopPlan.Shot, t: SportLowpolyTuning, yaw_: float, speed: float, pitch_ := 0.0) -> Ball:
	var b := Ball.new()
	b.pos = launch_pos(shot, t)
	# Прицел в стороны добавляет боковую скорость и не отнимает дальность: шкала силы всегда
	# значит одно и то же расстояние вдоль линии на кольцо.
	var flat := forward(shot, t) + right(shot, t) * tan(yaw_)
	# Прицел вверх и вниз меняет подъём броска: шкала силы рассчитана на прицел в кольцо.
	var lift := clampf(shot.lift + pitch_, 0.2, 1.5)
	b.vel = flat * speed * cos(lift) + Vector3.UP * speed * sin(lift)
	return b


## Шаг мяча: тяжесть, ветер, обруч, щит, земля. `shift` это съезд кольца сейчас.
static func step_ball(b: Ball, shot: HoopPlan.Shot, t: SportLowpolyTuning, dt: float, shift: float) -> void:
	b.hit = &""
	var s := t.hoop_scale
	var radius := t.ball_r
	b.vel += (Vector3.DOWN * t.gravity + right(shot, t) * shot.wind * t.wind_unit) * dt
	var prev := b.pos
	b.pos += b.vel * dt
	b.age += dt
	var rim := Vector3(shift, t.rim_y * s - t.hoop_sink, t.rim_z * s)
	var rim_r := t.rim_r * s
	# Щит: доска позади обруча, лицом в −Z.
	var board_z := t.board_z * s
	if prev.z + radius <= board_z and b.pos.z + radius > board_z and absf(b.pos.x - shift) <= t.board_half * s + radius * 0.5 \
			and b.pos.y >= (t.board_y0 * s - t.hoop_sink) - radius * 0.5 and b.pos.y <= (t.board_y1 * s - t.hoop_sink) + radius * 0.5:
		b.pos.z = board_z - radius
		b.vel.z = -b.vel.z * t.bounce_board
		b.touched = true
		b.hit = &"board"
	# Обруч: ближайшая точка окружности.
	var flat := Vector3(b.pos.x - rim.x, 0.0, b.pos.z - rim.z)
	if flat.length() > 0.001:
		var on_rim := rim + flat.normalized() * rim_r
		var off := b.pos - on_rim
		var reach := radius + t.rim_tube * s
		if off.length() < reach and off.length() > 0.0001:
			var n := off.normalized()
			b.pos = on_rim + n * reach
			var into := b.vel.dot(n)
			if into < 0.0:
				b.vel -= n * into * (1.0 + t.bounce_rim)
				b.touched = true
				b.hit = &"rim"
	# В кольцо: середина мяча прошла плоскость обруча сверху вниз внутри него.
	if not b.scored and prev.y > rim.y and b.pos.y <= rim.y and Vector2(b.pos.x - rim.x, b.pos.z - rim.z).length() < rim_r:
		b.scored = true
	# Земля: мяч подпрыгивает и катится; бросок решён, когда он коснулся земли или прошёл кольцо.
	if b.pos.y <= radius:
		b.pos.y = radius
		if b.vel.y < 0.0:
			b.vel.y = -b.vel.y * t.bounce_ground if b.vel.y < -1.0 else 0.0
		b.vel.x *= 1.0 - minf(t.ground_drag * dt, 1.0)
		b.vel.z *= 1.0 - minf(t.ground_drag * dt, 1.0)
		b.done = true
	if b.age > t.flight_limit or (b.scored and b.pos.y < rim.y - 0.5):
		b.done = true


## Пробный бросок без шкалы: попал ли, чисто ли, сколько летел до кольца, куда съехал мяч вбок
## у кольца. `[попал, чисто, секунды, вбок]`.
static func trial(shot: HoopPlan.Shot, t: SportLowpolyTuning, yaw_: float, speed: float, at: float) -> Array:
	var b := make_ball(shot, t, yaw_, speed)
	var dt := DT / SUBSTEPS
	var when := 0.0
	var side := 0.0
	var crossed := false
	var rim_y := t.rim_y * t.hoop_scale - t.hoop_sink
	while not b.done:
		var prev := b.pos
		step_ball(b, shot, t, dt, hoop_shift(shot, at + b.age))
		if not crossed and prev.y > rim_y and b.pos.y <= rim_y:
			crossed = true
			when = b.age
			side = (b.pos - rim_rest(t)).dot(right(shot, t))
	return [b.scored, b.scored and not b.touched, when, side]


# --- Шаг -------------------------------------------------------------------------------------

func shot() -> HoopPlan.Shot:
	return plan.shots[mini(index, plan.shots.size() - 1)]


## Глаза игрока: на точке, в переходе скользят к следующей.
func eye() -> Vector3:
	var here := shot().pos
	if phase == Phase.MOVE and index > 0:
		var k := smoothstep(0.0, 1.0, clampf(timer / tuning.move_seconds, 0.0, 1.0))
		here = plan.shots[index - 1].pos.lerp(here, k)
	return here + Vector3(0.0, tuning.eye, 0.0)


func shift() -> float:
	return hoop_shift(shot(), time)


## Где будет кольцо, когда долетит мяч, брошенный сейчас.
func ghost_shift() -> float:
	return hoop_shift(shot(), time + shot().flight)


func rim_now() -> Vector3:
	return rim_rest(tuning) + Vector3(shift(), 0.0, 0.0)


func fire() -> bool:
	return streak >= tuning.fire_streak


## Шкала силы от времени замаха: туда и обратно.
func meter_of(seconds: float) -> float:
	var k := fposmod(seconds / shot().meter, 1.0)
	return 1.0 - absf(1.0 - 2.0 * k)


## Шаг мира: прицел (радианы вправо от линии на кольцо), зажата ли кнопка броска.
func step(dt: float, yaw_: float, hold: bool, pitch_ := 0.0) -> void:
	if ended:
		return
	if phase == Phase.COUNTDOWN:
		countdown -= dt
		if countdown <= 0.0:
			phase = Phase.AIM
			events.append([&"go"])
		_held = hold
		return
	time += dt
	match phase:
		Phase.AIM:
			yaw = clampf(yaw_, -tuning.aim_limit, tuning.aim_limit)
			pitch = clampf(pitch_, -tuning.aim_limit, tuning.aim_limit)
			if hold and not _held:
				phase = Phase.CHARGE
				charge = 0.0
				power = 0.0
				events.append([&"charge"])
		Phase.CHARGE:
			yaw = clampf(yaw_, -tuning.aim_limit, tuning.aim_limit)
			pitch = clampf(pitch_, -tuning.aim_limit, tuning.aim_limit)
			charge += dt
			power = meter_of(charge)
			if not hold:
				ball = make_ball(shot(), tuning, yaw, speed_of(shot(), tuning, power) * reach_scale(), pitch)
				phase = Phase.FLIGHT
				events.append([&"throw"])
		Phase.FLIGHT:
			for k in SUBSTEPS:
				step_ball(ball, shot(), tuning, dt / SUBSTEPS, hoop_shift(shot(), time - dt + dt * (k + 1) / SUBSTEPS))
				if ball.hit != &"":
					events.append([ball.hit])
			if ball.done:
				_settle()
		Phase.RESULT:
			timer += dt
			# Мяч допадает до земли и катится, пока показан итог.
			if ball != null:
				for k in SUBSTEPS:
					step_ball(ball, shot(), tuning, dt / SUBSTEPS, shift())
			if timer >= tuning.result_seconds:
				ball = null
				index += 1
				if index >= plan.shots.size():
					phase = Phase.DONE
					ended = true
					finished = score >= tuning.goal
					events.append([&"finish" if finished else &"fail"])
				else:
					phase = Phase.MOVE
					timer = 0.0
					yaw = 0.0
					pitch = 0.0
					events.append([&"next"])
		Phase.MOVE:
			timer += dt
			if timer >= tuning.move_seconds:
				phase = Phase.AIM
	_held = hold


func _settle() -> void:
	var points := 0
	if ball.scored:
		var pure := not ball.touched
		points = (shot().points + (tuning.clean_bonus if pure else 0)) * (tuning.fire_mult if fire() else 1)
		events.append([&"score", points, pure, fire()])
		streak += 1
		made += 1
		clean += 1 if pure else 0
	else:
		streak = 0
		events.append([&"miss"])
	score += points
	results.append(points)
	phase = Phase.RESULT
	timer = 0.0


## Поправка скорости на съехавшее кольцо: до места, где оно будет к прилёту, чуть дальше или
## ближе, чем до середины; сила на шкале значит «точно до кольца», где бы оно ни было.
func reach_scale() -> float:
	var s := shot()
	if s.move_amp <= 0.0:
		return 1.0
	var from := launch_pos(s, tuning)
	var rest := rim_rest(tuning)
	return reach_of(s, tuning, ghost_shift())


## То же для съезда `shift_`: отношение скоростей для пути вдоль линии на кольцо.
static func reach_of(s: HoopPlan.Shot, t: SportLowpolyTuning, shift_: float) -> float:
	var from := launch_pos(s, t)
	var rest := rim_rest(t)
	var f := forward(s, t)
	return ideal_speed(s, t, (rest + Vector3(shift_, 0.0, 0.0) - from).dot(f)) / ideal_speed(s, t, (rest - from).dot(f))


## Прицел для кольца, съехавшего на `shift_`, с упреждением на ветер.
static func yaw_for(s: HoopPlan.Shot, t: SportLowpolyTuning, shift_: float) -> float:
	var to := rim_rest(t) + Vector3(shift_, 0.0, 0.0) - launch_pos(s, t)
	return atan(to.dot(right(s, t)) / to.dot(forward(s, t)) - s.wind * tan(s.tick))


## Скорость, с которой мяч под подъёмом броска попадает в середину кольца на расстоянии `d`.
static func ideal_speed(s: HoopPlan.Shot, t: SportLowpolyTuning, d: float) -> float:
	var rise := t.rim_y * t.hoop_scale - t.hoop_sink - t.launch_height
	return sqrt(t.gravity * d * d / (2.0 * pow(cos(s.lift), 2.0) * maxf(d * tan(s.lift) - rise, 0.01)))


## Куда целиться прямо сейчас, чтобы мяч вошёл: на место, где кольцо будет к прилёту, с
## упреждением на ветер.
func ideal_yaw() -> float:
	return yaw_for(shot(), tuning, ghost_shift())


## Бот решает на шаг вперёд. WIN: целится в место, где кольцо будет к прилёту мяча, с поправкой
## на ветер, зажимает и отпускает в середине зелёной зоны. LOSE бросает сразу, без силы.
func bot(mode: AutoTest.BotMode, dt: float) -> void:
	bot_hold = false
	if ended or mode == AutoTest.BotMode.OFF:
		return
	if mode != AutoTest.BotMode.WIN:
		bot_yaw = 0.0
		if phase == Phase.AIM:
			_bot_wait += dt
			bot_hold = _bot_wait >= tuning.bot_wait
		else:
			_bot_wait = 0.0
		return
	match phase:
		Phase.AIM:
			bot_yaw = ideal_yaw()
			_bot_wait += dt
			bot_hold = _bot_wait >= tuning.bot_wait
		Phase.CHARGE:
			bot_yaw = ideal_yaw()
			_bot_wait = 0.0
			# Держит, пока шкала не войдёт в середину зоны.
			bot_hold = absf(meter_of(charge + dt) - shot().zone) > shot().zone_half * tuning.bot_precision
		_:
			_bot_wait = 0.0
