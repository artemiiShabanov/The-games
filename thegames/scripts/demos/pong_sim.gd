class_name PongSim
extends RefCounted
## Правила демки спорт × вектор «понг» (#93) без окна и звука: состояние, шаг, соперник, боты.
## Демка `sport_vector.gd` рисует это состояние и озвучивает события `events`; `simulate`
## гоняет бота по сиду целиком (проверки `demo_test`, `debug/tools/dump_pong.gd`).
## Правила: ракетка игрока слева ходит вверх и вниз, соперника справа ведёт ИИ. Мяч отскакивает
## от стенок сверху и снизу и от ракеток; угол отскока от ракетки зависит от того, каким её
## местом попали (у края круче), и с каждым ударом ракеткой мяч быстрее. Пропустил: очко
## сопернику, подача в сторону пропустившего. Матч до `points_to_win` очков.
## Соперник из `PongMatch`: следит за мячом, когда тот летит к нему и прошёл `ai_react` поля,
## целит в точку встречи с ошибкой до `ai_error` и ходит не быстрее `ai_speed`; без мяча
## возвращается к середине. В долгом розыгрыше он устаёт: с каждым своим ударом ошибка растёт
## на `ai_tire`, так что розыгрыш не тянется бесконечно.
## Баги жанра и баланса приходят числами и флагами: `stick_every` каждый такой отскок от
## стенки мяч залипает в ней, дрожит `stuck_seconds` и улетает за край поля: это аут того, кто
## бил последним, а если после подачи никто не бил, розыгрыш переигрывается (мяч в космос); `bounce_gain` и `kick` мяч-попрыгунчик: быстрее от каждой
## стенки и отскакивает под случайным углом; `ai_wall` соперник непробиваемый: ракетка выше и
## быстрее, без ошибки, а мяч ускоряется без потолка (не достать); `ai_frail` ракетка соперника
## рассыпается от первого касания мяча (чих).

enum State { SERVE, PLAY, STUCK, EJECT }

var tuning: SportVectorTuning
var game: PongMatch
var size := Vector2(1664, 832)
var stick_every := 0
var stuck_seconds := 1.2
var bounce_gain := 0.0
var kick := 0.0
var wild_cap := 2000.0
var ai_wall := false
var ai_height_mult := 1.7
var ai_speed_mult := 3.0
var ai_frail := false

var state := State.SERVE
var ball := Vector2.ZERO
var vel := Vector2.ZERO
var speed := 0.0
## Середины ракеток по вертикали.
var paddle_y := 0.0
var ai_y := 0.0
var ai_alive := true
var score_player := 0
var score_ai := 0
var time := 0.0
var ended := false
var won := false
## Удары ракеток и отскоки от стенок за матч.
var hits := 0
var wall_bounces := 0
## События шага для звука и эффектов: `[имя, …]`. `serve`, `hit` (0 игрок, 1 соперник), `wall`,
## `point` (0 игроку, 1 сопернику), `stuck`, `eject`, `ai_shatter`, `win`, `lose`. Демка читает
## и чистит.
var events: Array[Array] = []

var _serve_left := 0.0
## Куда подача: −1 к игроку, 1 к сопернику.
var _serve_dir := -1.0
var _serve_index := 0
var _stuck_left := 0.0
var _stuck_side := 1.0
var _ai_error := 0.0
## Кто бил последним в розыгрыше (0 игрок, 1 соперник, −1 никто) и сколько раз бил соперник.
var _last_hitter := -1
var _ai_returns := 0
var _rng := RandomNumberGenerator.new()


static func create(game_: PongMatch, tuning_: SportVectorTuning, size_ := Vector2(1664, 832)) -> PongSim:
	var s := PongSim.new()
	s.game = game_
	s.tuning = tuning_
	s.size = size_
	s.paddle_y = size_.y / 2.0
	s.ai_y = size_.y / 2.0
	s._rng.seed = game_.noise_seed
	s._to_serve(-1.0)
	return s


## Прогон бота без окна до конца или до `max_seconds`.
static func simulate(game_: PongMatch, tuning_: SportVectorTuning, mode: AutoTest.BotMode,
		max_seconds := 400.0, setup := Callable()) -> PongSim:
	var s := create(game_, tuning_)
	if setup.is_valid():
		setup.call(s)
	var dt := 1.0 / 60.0
	while not s.ended and s.time < max_seconds:
		s.step(dt, s.bot(mode))
		s.events.clear()
	return s


func top() -> float:
	return tuning.wall_inset


func bottom() -> float:
	return size.y - tuning.wall_inset


## Передняя грань ракетки игрока и соперника по горизонтали.
func player_face() -> float:
	return tuning.paddle_inset + tuning.paddle_width / 2.0


func ai_face() -> float:
	return size.x - tuning.paddle_inset - tuning.paddle_width / 2.0


func ai_height() -> float:
	return tuning.paddle_height * (ai_height_mult if ai_wall else 1.0)


## Где мяч будет по вертикали, когда долетит до `x`, с отскоками от стенок.
func predict_y(x: float) -> float:
	if absf(vel.x) < 1.0:
		return ball.y
	var y := ball.y + vel.y * (x - ball.x) / vel.x
	var lo := top() + tuning.ball_radius
	var span := bottom() - tuning.ball_radius - lo
	var rel := fposmod(y - lo, 2.0 * span)
	return lo + (2.0 * span - rel if rel > span else rel)


## Шаг мира: `axis` ход ракетки игрока −1 вверх, 1 вниз.
func step(dt: float, axis: float) -> void:
	if ended:
		return
	time += dt
	var half := tuning.paddle_height / 2.0
	paddle_y = clampf(paddle_y + clampf(axis, -1.0, 1.0) * tuning.paddle_speed * dt, top() + half, bottom() - half)
	_step_ai(dt)
	match state:
		State.SERVE:
			_serve_left -= dt
			if _serve_left <= 0.0:
				var a := game.serves[_serve_index % game.serves.size()] if not game.serves.is_empty() else 0.3
				_serve_index += 1
				speed = tuning.ball_speed
				vel = Vector2(_serve_dir * cos(a), sin(a)) * speed
				state = State.PLAY
				_roll_ai_error()
				events.append([&"serve"])
		State.PLAY:
			var steps := maxi(int(ceil(speed * dt / tuning.ball_radius)), 1)
			for i in steps:
				_move_ball(dt / steps)
				if state != State.PLAY or ended:
					break
		State.STUCK:
			_stuck_left -= dt
			if _stuck_left <= 0.0:
				state = State.EJECT
				vel = Vector2(0.0, _stuck_side) * maxf(speed, tuning.ball_speed) * 1.5
				events.append([&"eject"])
		State.EJECT:
			ball += vel * dt
			if ball.y < -80.0 or ball.y > size.y + 80.0:
				# Мяч улетел за край: аут того, кто бил последним; никто не бил: переигровка.
				if _last_hitter == 0:
					score_ai += 1
					events.append([&"point", 1])
					_after_point(-1.0)
				elif _last_hitter == 1:
					score_player += 1
					events.append([&"point", 0])
					_after_point(1.0)
				else:
					_to_serve(_serve_dir)


func _move_ball(dt: float) -> void:
	var r := tuning.ball_radius
	ball += vel * dt
	if ball.y - r < top() and vel.y < 0.0:
		ball.y = top() + r
		vel.y = -vel.y
		_on_wall(-1.0)
	elif ball.y + r > bottom() and vel.y > 0.0:
		ball.y = bottom() - r
		vel.y = -vel.y
		_on_wall(1.0)
	if state != State.PLAY:
		return
	var depth := tuning.paddle_width + r
	if vel.x < 0.0 and ball.x - r <= player_face() and ball.x - r >= player_face() - depth \
			and absf(ball.y - paddle_y) <= tuning.paddle_height / 2.0 + r:
		ball.x = player_face() + r
		_bounce(1.0, (ball.y - paddle_y) / (tuning.paddle_height / 2.0))
		_last_hitter = 0
		_roll_ai_error()
		events.append([&"hit", 0])
	elif vel.x > 0.0 and ai_alive and ball.x + r >= ai_face() and ball.x + r <= ai_face() + depth \
			and absf(ball.y - ai_y) <= ai_height() / 2.0 + r:
		ball.x = ai_face() - r
		_bounce(-1.0, (ball.y - ai_y) / (ai_height() / 2.0))
		_last_hitter = 1
		_ai_returns += 1
		events.append([&"hit", 1])
		if ai_frail:
			ai_alive = false
			events.append([&"ai_shatter"])
	if ball.x < -r * 2.0:
		score_ai += 1
		events.append([&"point", 1])
		_after_point(-1.0)
	elif ball.x > size.x + r * 2.0:
		score_player += 1
		events.append([&"point", 0])
		_after_point(1.0)


## Отскок от ракетки в сторону `dir`: угол по месту попадания, мяч быстрее.
func _bounce(dir: float, offset: float) -> void:
	hits += 1
	speed = minf(speed * (1.0 + tuning.ball_gain), INF if ai_wall else (wild_cap if bounce_gain > 0.0 else tuning.ball_speed_cap))
	var a := clampf(offset, -1.0, 1.0) * deg_to_rad(tuning.max_angle)
	vel = Vector2(dir * cos(a), sin(a)) * speed


func _on_wall(side: float) -> void:
	wall_bounces += 1
	events.append([&"wall"])
	if bounce_gain > 0.0:
		# Попрыгунчик: от стенки быстрее и под случайным углом, но всё ещё поперёк поля.
		speed = minf(speed * (1.0 + bounce_gain), wild_cap)
		var a := clampf(absf(atan2(vel.y, absf(vel.x))) + _rng.randf_range(-kick, kick), 0.15, 1.15)
		vel = Vector2(signf(vel.x) * cos(a), signf(vel.y) * sin(a)) * speed
	if stick_every > 0 and wall_bounces % stick_every == 0:
		state = State.STUCK
		_stuck_left = stuck_seconds
		_stuck_side = side
		events.append([&"stuck"])


func _after_point(serve_dir: float) -> void:
	if score_player >= tuning.points_to_win:
		ended = true
		won = true
		events.append([&"win"])
	elif score_ai >= tuning.points_to_win:
		ended = true
		won = false
		events.append([&"lose"])
	else:
		_to_serve(serve_dir)


func _to_serve(dir: float) -> void:
	state = State.SERVE
	_serve_dir = dir
	_serve_left = tuning.serve_delay
	ball = size / 2.0
	vel = Vector2.ZERO
	speed = tuning.ball_speed
	_last_hitter = -1
	_ai_returns = 0


func _roll_ai_error() -> void:
	var reach := game.ai_error * (1.0 + tuning.ai_tire * _ai_returns)
	_ai_error = _rng.randf_range(-reach, reach)


func _step_ai(dt: float) -> void:
	if not ai_alive:
		return
	var s := game.ai_speed * (ai_speed_mult if ai_wall else 1.0)
	var target := size.y / 2.0
	if state == State.PLAY and vel.x > 0.0 and (ai_wall or ball.x > size.x * game.ai_react):
		target = predict_y(ai_face() - tuning.ball_radius) + (0.0 if ai_wall else _ai_error)
	else:
		s *= tuning.ai_idle
	var half := ai_height() / 2.0
	ai_y = move_toward(ai_y, clampf(target, top() + half, bottom() - half), s * dt)


# --- Боты ------------------------------------------------------------------------------------

## Бот: возвращает ход ракетки. WIN встаёт в точку встречи так, чтобы попасть по мячу краем
## ракетки и увести его в ту половину, где соперника нет; LOSE стоит на месте.
func bot(mode: AutoTest.BotMode) -> float:
	if ended or mode != AutoTest.BotMode.WIN:
		return 0.0
	var target := size.y / 2.0
	if state == State.PLAY and vel.x < 0.0:
		var edge := tuning.bot_edge * tuning.paddle_height / 2.0
		target = predict_y(player_face() + tuning.ball_radius)
		if ai_alive:
			# Соперник выше середины: мяч вниз (попасть ниже середины ракетки), и наоборот.
			target += -edge if ai_y < size.y / 2.0 else edge
	return clampf((target - paddle_y) / (tuning.paddle_speed / 60.0), -1.0, 1.0)
