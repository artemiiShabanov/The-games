class_name HookSim
extends RefCounted
## Правила демки платформер × «продвинутые» «крюк-кошка» (#121) без окна: бег по островкам,
## прыжок, крюк за кольцо, качание маятником, полёт, жизни и боты. Демка `platformer_threed.gd`
## рисует это состояние и озвучивает события `events`; `simulate` гоняет бота по сиду целиком
## (проверки `demo_test`, `debug/tools/dump_hook.gd`).
##
## Герой живёт в координатах пути: `s` вдоль, `u` вбок, `y` высота. Зажатый крюк цепляется за
## ближайшее кольцо, до которого достаёт верёвка; герой качается маятником (если разбега мало,
## качание добирает скорость само), отпущенный крюк отпускает его по касательной. Отпустил
## рано: недолёт, поздно: взлетел и упал назад. Приземлиться надо на островок; вода стоит жизни
## и возвращает на последний островок. Цель: островок с маяком в конце.

const DT := 1.0 / 60.0

enum Phase { COUNTDOWN, PLAY, DONE }
enum Mode { GROUND, AIR, SWING, DOWN }

var level: HookLevel
var tuning: PlatformerThreedTuning
var phase := Phase.COUNTDOWN
var countdown := 0.0
var time := 0.0
var mode := Mode.GROUND
var s := 0.0
var u := 0.0
var y := 0.0
var vs := 0.0
var vy := 0.0
## Кольцо, на котором висит герой, длина верёвки, угол от отвеса (плюс вперёд) и его скорость.
var ring := -1
var rope := 5.0
var theta := 0.0
var omega := 0.0
## Последнее кольцо и сколько секунд за него ещё не зацепиться; последний островок.
var last_ring := -1
var rehook_left := 0.0
var islet := 0
var lives := 3
var down_left := 0.0
var ended := false
var finished := false
var hooks := 0
var falls := 0
var water := -4.0
## События шага для звука и эффектов: `[имя, …]`. `go`, `jump`, `hook(кольцо)`, `release`,
## `land(островок)`, `splash`, `respawn`, `finish`, `dead`, `timeout`. Демка читает и чистит.
var events: Array[Array] = []
## Что бот хочет на этом шаге (`bot`).
var bot_forward := 0.0
var bot_side := 0.0
var bot_jump := false
var bot_hook := false

var _armed := true
var _bot_wait := false


static func create(level_: HookLevel, tuning_: PlatformerThreedTuning) -> HookSim:
	var sim := HookSim.new()
	sim.level = level_
	sim.tuning = tuning_
	sim.countdown = tuning_.countdown
	sim.lives = tuning_.lives
	sim.water = level_.water_y(tuning_.water_drop)
	sim.s = level_.islets[0].s - level_.islets[0].radius * 0.5
	sim.y = level_.islets[0].y
	return sim


## Прогон бота без окна до конца уровня.
static func simulate(level_: HookLevel, tuning_: PlatformerThreedTuning, mode_: AutoTest.BotMode) -> HookSim:
	var sim := create(level_, tuning_)
	while not sim.ended:
		sim.bot(mode_)
		sim.step(DT, sim.bot_forward, sim.bot_side, sim.bot_jump, sim.bot_hook)
		sim.events.clear()
	return sim


func progress() -> float:
	return clampf((s - level.islets[0].s) / maxf(level.length(), 1.0), 0.0, 1.0)


## Место кольца сейчас: вдоль пути и по высоте.
func ring_pos(i: int, at := -1.0) -> Vector2:
	return Vector2(level.rings[i].s, level.ring_y(i, time if at < 0.0 else at))


## Кольцо, за которое крюк зацепится сейчас, или −1.
func target() -> int:
	var best := -1
	var best_d := INF
	for i in level.rings.size():
		if i == last_ring and rehook_left > 0.0:
			continue
		var p := ring_pos(i)
		if p.x < s - 1.0:
			continue
		var d := Vector2(p.x - s, p.y - y).length()
		if d <= tuning.rope_max and d < best_d and p.y > y + 0.8:
			best = i
			best_d = d
	return best


## Шаг мира: ход вперёд и вбок (−1..1), нажат ли прыжок, зажат ли крюк.
func step(dt: float, forward: float, side: float, jump: bool, hook: bool) -> void:
	if ended:
		return
	if phase == Phase.COUNTDOWN:
		countdown -= dt
		if countdown <= 0.0:
			phase = Phase.PLAY
			events.append([&"go"])
		return
	time += dt
	rehook_left = maxf(rehook_left - dt, 0.0)
	if not hook:
		_armed = true
	match mode:
		Mode.GROUND:
			_ground(dt, clampf(forward, -1.0, 1.0), clampf(side, -1.0, 1.0), jump, hook)
		Mode.AIR:
			_air(dt, clampf(forward, -1.0, 1.0), clampf(side, -1.0, 1.0), hook)
		Mode.SWING:
			_swing(dt, clampf(side, -1.0, 1.0), hook)
		Mode.DOWN:
			down_left -= dt
			if down_left <= 0.0:
				var it := level.islets[islet]
				s = it.s - it.radius * 0.4
				u = 0.0
				y = it.y
				vs = 0.0
				vy = 0.0
				mode = Mode.GROUND
				events.append([&"respawn"])
	if not ended and time > tuning.max_seconds:
		ended = true
		phase = Phase.DONE
		events.append([&"timeout"])


func _ground(dt: float, forward: float, side: float, jump: bool, hook: bool) -> void:
	vs = move_toward(vs, forward * tuning.run_speed, tuning.run_accel * dt)
	s += vs * dt
	u += side * tuning.side_speed * dt
	var it := level.islets[islet]
	y = it.y
	if Vector2(s - it.s, u).length() > it.radius:
		# Сошёл с края.
		mode = Mode.AIR
		vy = 0.0
	if jump:
		mode = Mode.AIR
		vy = tuning.jump_speed
		events.append([&"jump"])
	if hook and _armed and mode == Mode.AIR:
		_try_hook()


func _air(dt: float, forward: float, side: float, hook: bool) -> void:
	var before := y
	var was_inside := level.islet_at(s, u)
	vy -= tuning.gravity * dt
	vs = clampf(vs + forward * tuning.air_accel * dt, -maxf(absf(vs), tuning.run_speed), maxf(absf(vs), tuning.run_speed))
	s += vs * dt
	y += vy * dt
	u += side * tuning.side_speed * 0.6 * dt
	var i := level.islet_at(s, u)
	if i >= 0:
		var top := level.islets[i].y
		if vy <= 0.0 and before >= top - 0.05 and y <= top:
			_land(i)
			return
		if y < top - 0.05 and was_inside < 0:
			# Врезался в бок островка: назад к краю, дальше вниз.
			var it := level.islets[i]
			var edge := sqrt(maxf(it.radius * it.radius - u * u, 0.0))
			s = it.s - edge - 0.02 if s < it.s else it.s + edge + 0.02
			vs = 0.0
	if y < water:
		_fall()
		return
	if hook and _armed:
		_try_hook()


func _try_hook() -> void:
	var i := target()
	if i < 0:
		return
	var p := ring_pos(i)
	var d := Vector2(s - p.x, y - p.y)
	ring = i
	rope = clampf(d.length(), tuning.rope_min, tuning.rope_max)
	theta = atan2(d.x, -d.y)
	# Скорость вдоль дуги; если разбега мало, качание добирает её само.
	var along := vs * cos(theta) + vy * sin(theta)
	omega = maxf(along, tuning.swing_min) / rope
	mode = Mode.SWING
	_armed = false
	hooks += 1
	events.append([&"hook", i])


func _swing(dt: float, side: float, hook: bool) -> void:
	omega -= tuning.gravity / rope * sin(theta) * dt
	theta += omega * dt
	var p := ring_pos(ring)
	s = p.x + rope * sin(theta)
	y = p.y - rope * cos(theta)
	u = move_toward(u, 0.0, 1.5 * dt) + side * tuning.side_speed * 0.4 * dt
	vs = rope * omega * cos(theta)
	vy = rope * omega * sin(theta)
	var i := level.islet_at(s, u)
	if i >= 0 and y <= level.islets[i].y:
		last_ring = ring
		ring = -1
		_land(i)
		return
	if not hook or absf(theta) > 1.95:
		# Отпустил: летит по касательной.
		last_ring = ring
		rehook_left = tuning.rehook
		ring = -1
		vs *= tuning.release_boost
		vy *= tuning.release_boost
		mode = Mode.AIR
		events.append([&"release"])
	if y < water:
		ring = -1
		_fall()


func _land(i: int) -> void:
	mode = Mode.GROUND
	y = level.islets[i].y
	vy = 0.0
	vs = clampf(vs, -tuning.run_speed, tuning.run_speed)
	if i != islet:
		events.append([&"land", i])
	islet = maxi(islet, i)
	last_ring = -1
	if i >= level.islets.size() - 1:
		finished = true
		ended = true
		phase = Phase.DONE
		events.append([&"finish"])


func _fall() -> void:
	falls += 1
	lives -= 1
	events.append([&"splash"])
	if lives <= 0:
		ended = true
		phase = Phase.DONE
		events.append([&"dead"])
		return
	mode = Mode.DOWN
	down_left = tuning.respawn_seconds
	vs = 0.0
	vy = 0.0


# --- Боты ------------------------------------------------------------------------------------

## Что будет, если лететь без крюка из точки с такой скоростью: островок, на который герой
## сядет с запасом (номер ≥ 0), или кольцо, до которого дотянется верёвка (−2 − номер), или −1.
func flight(s0: float, y0: float, vs0: float, vy0: float, from_ring: int) -> int:
	var ps := s0
	var py := y0
	var pvy := vy0
	var at := time
	var h := DT * 2.0
	for k in 120:
		var before := py
		pvy -= tuning.gravity * h
		ps += vs0 * h
		py += pvy * h
		at += h
		if py < water:
			return -1
		for i in level.rings.size():
			if i <= from_ring or level.rings[i].gap != level.rings[maxi(from_ring, 0)].gap:
				continue
			var p := ring_pos(i, at)
			# До кольца достаёт верёвка, герой ниже него и ещё не пролетел.
			if p.x - ps > -0.6 and p.y - py > 1.6 and Vector2(p.x - ps, p.y - py).length() <= tuning.rope_max - tuning.bot_margin and at - time > tuning.rehook * 0.3:
				return -2 - i
		var j := level.islet_at(ps, 0.0)
		if j > islet:
			var it := level.islets[j]
			if pvy <= 0.0 and before >= it.y and py <= it.y:
				return j if absf(ps - it.s) <= it.radius - tuning.bot_margin else -1
			if py < it.y:
				return -1
	return -1


## Бот решает на шаг вперёд. WIN: бежит к краю, прыгает, цепляется за кольцо и отпускает в тот
## миг, когда полёт без крюка приведёт на следующий островок или к следующему кольцу цепочки.
## LOSE бежит вперёд без крюка и падает.
func bot(mode_: AutoTest.BotMode) -> void:
	bot_forward = 0.0
	bot_side = 0.0
	bot_jump = false
	bot_hook = false
	if ended or mode_ == AutoTest.BotMode.OFF or phase != Phase.PLAY:
		return
	bot_side = clampf(-u * 2.0, -1.0, 1.0)
	if mode_ != AutoTest.BotMode.WIN:
		bot_forward = 1.0
		return
	match mode:
		Mode.GROUND:
			var it := level.islets[islet]
			bot_forward = 1.0
			bot_jump = s >= it.s + it.radius - 0.35
		Mode.AIR:
			bot_forward = 0.0
			# После отпускания кнопка один шаг отпущена, потом снова зажата: крюк берёт кольцо.
			bot_hook = not _bot_wait and target() >= 0
			_bot_wait = false
			# Если полёт и так приведёт на островок, крюк не нужен.
			if bot_hook and flight(s, y, vs, vy, 9999) >= 0:
				bot_hook = false
		Mode.SWING:
			bot_hook = true
			if theta > 0.15 and omega > 0.0:
				var k := tuning.release_boost
				var out := flight(s, y, vs * k, vy * k, ring)
				if out >= 0 or out <= -2:
					bot_hook = false
					_bot_wait = true
