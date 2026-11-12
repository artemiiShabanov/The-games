class_name SoccerSim
extends RefCounted
## Правила футбола × 16/32-bit «один на одного» (#101, графика по Sensible Soccer) без окна и
## звука: герой, соперник, два вратаря, мяч, счёт, боты. Демка `sport_bit16.gd` рисует это
## состояние и озвучивает события; `simulate` гоняет бота по сиду целиком (проверки `demo_test`,
## `debug/tools/dump_soccer.gd`). Мир шагает ровно 60 раз в секунду. Поле горизонтально: ворота
## героя слева (x = 0), соперника справа (x = ширина поля).
## Правила: мяч липнет к ноге того, кто его коснулся на земле и не слишком быстрый, и катится
## перед ним; отобрать мяч у соперника можно только подкатом. A держать:
## зарядка удара, отпустить: удар по взгляду, чем дольше, тем сильнее и выше; первые доли
## секунды после удара стрелка поперёк подкручивает мяч. B подкат: рывок, мяч у соперника
## выбивается, соперник падает. Вратарь ходит вдоль створа за мячом, на удар в створ прыгает,
## поймал: держит и выбрасывает своему. Мяч за лицевой мимо створа: от ворот (мяч вратарю), за
## боковой: мяч на линии, ничей. Гол: пауза и розыгрыш с центра пропустившим. Матч до трёх.
## Баги приходят числами: `bounce_mult` мяч скачет, как резиновый; `goal_mult` ворота соперника
## уже (не достать); `sneeze` соперник падает от любого касания; `space_every` мяч раз в столько
## секунд улетает вверх за поле.

const DT := 1.0 / 60.0
const HERO := 0
const RIVAL := 1
const HERO_KEEPER := 2
const RIVAL_KEEPER := 3

class Player:
	var team := 0
	var keeper := false
	var pos := Vector2.ZERO
	var vel := Vector2.ZERO
	var facing := Vector2.RIGHT
	var slide := 0.0
	var slide_dir := Vector2.ZERO
	var slide_cd := 0.0
	var down := 0.0
	var dive := 0.0
	var dive_dir := Vector2.ZERO
	## Куда прыгает: угаданное место удара на линии ворот.
	var dive_to := 0.0
	var hold := 0.0
	var charge := -1.0
	var speed := 120.0
	var reach := 34.0
	var react := 0.2

var tuning: SportBit16Tuning
var plan: SoccerPlan
var bounce_mult := 1.0
var goal_mult := 1.0
var sneeze := false
var space_every := 0.0

var players: Array[Player] = []
## Мяч: место на поле (x, y) и высота (z); скорость так же.
var ball := Vector3.ZERO
var ball_vel := Vector3.ZERO
## У кого мяч у ноги или в руках (индекс игрока), −1 ничей.
var owner := -1
var last_touch := -1
var kicked_by := -1
var kick_t := 9.0
var score: Array[int] = [0, 0]
var time := 0.0
var ended := false
var won := false
var pause := 0.0
var kicks := 0
## События шага: `[имя, …]`. `kick` (игрок), `bounce`, `control` (игрок), `steal` (игрок),
## `slide` (игрок), `tackle` (игрок, кого), `dive` (вратарь), `save` (вратарь), `throw`, `goal`
## (команда), `post`, `out`, `space`, `win`, `lose`. Демка читает и чистит.
var events: Array[Array] = []
## Ввод бота на этом шаге.
var bot_kick := false
var bot_slide := false

var _rng := RandomNumberGenerator.new()
var _steal_cd := 0.0
var _space_t := 0.0
var _conceded := RIVAL
var _rival_aim := 0.0
var _rival_charge := -1.0
var _hero_charge := -1.0
var _keeper_seen: Array[Vector2] = [Vector2.ZERO, Vector2.ZERO]


static func create(plan_: SoccerPlan, tuning_: SportBit16Tuning) -> SoccerSim:
	var s := SoccerSim.new()
	s.plan = plan_
	s.tuning = tuning_
	s._rng.seed = hash(str(plan_.seed, ":match"))
	for i in 4:
		var p := Player.new()
		p.team = HERO if i == HERO or i == HERO_KEEPER else RIVAL
		p.keeper = i >= 2
		p.speed = tuning_.run_speed if i == HERO else (plan_.rival_speed if i == RIVAL else tuning_.keeper_speed)
		p.reach = plan_.keeper_reach if i == HERO_KEEPER else plan_.rival_keeper_reach
		p.react = plan_.keeper_react if i == HERO_KEEPER else (plan_.rival_keeper_react if i == RIVAL_KEEPER else plan_.rival_react)
		s.players.append(p)
	s._kickoff(RIVAL)
	return s


static func simulate(plan_: SoccerPlan, tuning_: SportBit16Tuning, mode: AutoTest.BotMode, setup := Callable()) -> SoccerSim:
	var s := create(plan_, tuning_)
	if setup.is_valid():
		setup.call(s)
	while not s.ended:
		var axis := s.bot(mode)
		s.step(axis, s.bot_kick, s.bot_slide)
		s.events.clear()
	return s


func mid() -> float:
	return tuning.pitch_h * 0.5


## Полуширина створа ворот команды `team` (ворота героя слева, соперника справа).
func half_goal(team: int) -> float:
	return tuning.goal_w * 0.5 * (goal_mult if team == RIVAL else 1.0)


## Шаг мира в 1/60 секунды: `axis` стрелки, `kick` держится ли A, `slide` нажата ли B.
func step(axis: Vector2, kick: bool, slide: bool) -> void:
	if ended:
		return
	time += DT
	if time >= tuning.max_seconds:
		_end(score[HERO] > score[RIVAL])
		return
	if pause > 0.0:
		pause -= DT
		if pause <= 0.0:
			_kickoff(_conceded)
		return
	kick_t += DT
	_steal_cd = maxf(_steal_cd - DT, 0.0)
	_control(HERO, axis, kick, slide)
	var ai := _rival_ai()
	_control(RIVAL, ai[0], ai[1], ai[2])
	_keeper(HERO_KEEPER)
	_keeper(RIVAL_KEEPER)
	_aftertouch(axis)
	_ball_step()
	_touches()
	_space()


## Полевой игрок: бег по `dir`, зарядка и удар, подкат.
func _control(i: int, dir: Vector2, kick: bool, slide: bool) -> void:
	var p := players[i]
	p.slide_cd = maxf(p.slide_cd - DT, 0.0)
	if p.down > 0.0:
		p.down -= DT
		p.vel = Vector2.ZERO
		p.charge = -1.0
		return
	if p.slide > 0.0:
		p.slide -= DT
		p.vel = p.slide_dir * tuning.slide_speed * (p.slide / tuning.slide_seconds * 0.5 + 0.5)
		_move(p)
		return
	if dir.length() > 0.1:
		p.facing = dir.normalized()
	p.vel = dir.limit_length(1.0) * p.speed
	if slide and p.slide_cd <= 0.0:
		p.slide = tuning.slide_seconds
		p.slide_cd = tuning.slide_cooldown
		p.slide_dir = p.facing
		events.append([&"slide", i])
		return
	# Зарядка удара: держит A; отпустил: удар, если мяч у ноги или рядом.
	if kick:
		p.charge = maxf(p.charge, 0.0) + DT
	elif p.charge >= 0.0:
		var k := clampf(p.charge / tuning.charge_max, 0.0, 1.0)
		p.charge = -1.0
		if owner == i or (owner < 0 and Vector2(ball.x, ball.y).distance_to(p.pos) < tuning.radius + 8.0 and ball.z < 12.0):
			_kick(i, p.facing, k)
	_move(p)


func _move(p: Player) -> void:
	p.pos += p.vel * DT
	p.pos.x = clampf(p.pos.x, -14.0, tuning.pitch_w + 14.0)
	p.pos.y = clampf(p.pos.y, -14.0, tuning.pitch_h + 14.0)


## Удар игрока `i` в направлении `dir` с долей зарядки `k`.
func _kick(i: int, dir: Vector2, k: float) -> void:
	var speed := lerpf(tuning.kick_min, tuning.kick_max, k)
	var d := dir.normalized() if dir.length() > 0.01 else players[i].facing
	ball_vel = Vector3(d.x * speed, d.y * speed, tuning.loft_lin * k + tuning.loft_sq * k * k)
	ball.z = maxf(ball.z, 1.0)
	owner = -1
	last_touch = i
	kicked_by = i
	kick_t = 0.0
	kicks += 1
	_steal_cd = 0.25
	events.append([&"kick", i])


## Подкрутка героя: первые доли секунды после его удара стрелка поперёк мяча закручивает его.
func _aftertouch(axis: Vector2) -> void:
	if kicked_by != HERO or kick_t > tuning.aftertouch_seconds or owner >= 0 or axis.length() < 0.1:
		return
	var v := Vector2(ball_vel.x, ball_vel.y)
	if v.length() < 1.0:
		return
	var side := Vector2(-v.y, v.x).normalized()
	var amount := axis.dot(side)
	v += side * amount * tuning.aftertouch * DT
	ball_vel.x = v.x
	ball_vel.y = v.y


func _ball_step() -> void:
	if owner >= 0:
		var p := players[owner]
		if p.keeper:
			ball = Vector3(p.pos.x, p.pos.y, 10.0)
		else:
			var at := p.pos + p.facing * tuning.dribble_ahead
			ball = Vector3(at.x, at.y, 0.0)
		ball_vel = Vector3(p.vel.x, p.vel.y, 0.0)
		return
	ball_vel.z -= tuning.gravity * DT
	ball += ball_vel * DT
	if ball.z <= 0.0:
		ball.z = 0.0
		if ball_vel.z < -40.0:
			ball_vel.z = -ball_vel.z * clampf(tuning.bounce * bounce_mult, 0.0, 0.97)
			events.append([&"bounce"])
		else:
			ball_vel.z = 0.0
		var h := Vector2(ball_vel.x, ball_vel.y)
		h = h.move_toward(Vector2.ZERO, tuning.friction * DT)
		ball_vel.x = h.x
		ball_vel.y = h.y
	_lines()


## Гол, лицевая, боковая.
func _lines() -> void:
	var w := tuning.pitch_w
	for side in 2:
		var crossed := ball.x < 0.0 if side == 0 else ball.x > w
		if not crossed:
			continue
		var team := HERO if side == 0 else RIVAL
		if absf(ball.y - mid()) < half_goal(team) and ball.z < tuning.goal_h:
			_goal(RIVAL if team == HERO else HERO)
			return
		events.append([&"out"])
		# От ворот: мяч вратарю этих ворот.
		var k := HERO_KEEPER if team == HERO else RIVAL_KEEPER
		_give_keeper(k)
		return
	if ball.y < 0.0 or ball.y > tuning.pitch_h:
		events.append([&"out"])
		ball.y = clampf(ball.y, 2.0, tuning.pitch_h - 2.0)
		ball.z = 0.0
		ball_vel = Vector3.ZERO


func _give_keeper(k: int) -> void:
	var p := players[k]
	p.pos = Vector2(_keeper_x(k), mid())
	owner = k
	p.hold = tuning.keeper_hold
	ball = Vector3(p.pos.x, p.pos.y, 10.0)
	ball_vel = Vector3.ZERO


func _keeper_x(k: int) -> float:
	return 12.0 if k == HERO_KEEPER else tuning.pitch_w - 12.0


## Касания: мяч к ноге, отбор, подкат, чих.
func _touches() -> void:
	var b := Vector2(ball.x, ball.y)
	var b_speed := Vector2(ball_vel.x, ball_vel.y).length()
	for i in [HERO, RIVAL]:
		var p := players[i]
		if p.down > 0.0:
			continue
		var near := p.pos.distance_to(b) < tuning.radius + 6.0 and ball.z < 10.0
		if not near:
			continue
		if p.slide > 0.0:
			if owner >= 0 and players[owner].team != p.team and not players[owner].keeper:
				var victim := owner
				players[victim].down = tuning.down_seconds
				owner = -1
				ball_vel = Vector3(p.slide_dir.x * 150.0, p.slide_dir.y * 150.0, 40.0)
				last_touch = i
				events.append([&"tackle", i, victim])
			elif owner < 0:
				ball_vel = Vector3(p.slide_dir.x * 170.0, p.slide_dir.y * 170.0, 20.0)
				last_touch = i
			continue
		# Мяч берётся только ничейный: у соперника его отбирают подкатом, не касанием.
		if owner < 0 and b_speed < tuning.control_speed and _steal_cd <= 0.0 and kick_t > 0.12:
			owner = i
			last_touch = i
			events.append([&"control", i])
	# Чих: соперник падает от любого касания героя.
	if sneeze and players[RIVAL].down <= 0.0 and players[HERO].pos.distance_to(players[RIVAL].pos) < tuning.radius * 2.0:
		players[RIVAL].down = tuning.down_seconds * 2.0
		if owner == RIVAL:
			owner = HERO
		events.append([&"tackle", HERO, RIVAL])


## Вратарь: держит мяч и выбрасывает своему; прыжок; ход вдоль створа за мячом с запозданием.
func _keeper(k: int) -> void:
	var p := players[k]
	var team := p.team
	var gx := _keeper_x(k)
	if owner == k:
		p.hold -= DT
		if p.hold <= 0.0:
			var mate := players[HERO if team == HERO else RIVAL]
			var to := mate.pos - p.pos
			_kick(k, to, clampf(to.length() / 500.0, 0.3, 0.6))
			events.append([&"throw", k])
		return
	if p.dive > 0.0:
		p.dive -= DT
		p.pos.y = move_toward(p.pos.y, p.dive_to, tuning.dive_speed * DT)
		_catch(k, tuning.dive_catch)
		return
	# Запоздалое зрение: вратарь видит мяч с задержкой `react`.
	var seen := _keeper_seen[k - 2].lerp(Vector2(ball.x, ball.y), minf(DT / maxf(p.react, 0.01), 1.0))
	_keeper_seen[k - 2] = seen
	var hg := half_goal(team)
	# Пока мяч далеко, вратарь стоит ближе к центру створа (на треть смещения мяча), за мячом
	# напрямую идёт только вблизи: угол он берёт прыжком, а не ходом.
	var near := absf(seen.x - gx) < 70.0
	var ty := clampf(seen.y if near else mid() + (seen.y - mid()) * 0.35, mid() - hg, mid() + hg)
	if owner < 0 and not near and kick_t < 1.0:
		ty = p.pos.y
	var target := Vector2(gx, ty)
	p.pos = p.pos.move_toward(target, p.speed * DT)
	# Удар в створ: успевает ли мяч к линии, куда, достать ли прыжком.
	var vx := ball_vel.x
	var toward := (vx < -20.0 and team == HERO) or (vx > 20.0 and team == RIVAL)
	if owner < 0 and toward and kick_t > p.react:
		var t := (gx - ball.x) / vx
		if t > 0.0 and t < tuning.dive_window:
			# Вратарь угадывает место с ошибкой (зерно матча): ловит не всё.
			var py := ball.y + ball_vel.y * t + _rng.randf_range(-tuning.keeper_error, tuning.keeper_error)
			if absf(py - mid()) < hg + 6.0 and absf(py - p.pos.y) > 6.0 and absf(py - p.pos.y) < p.reach + 20.0:
				p.dive = tuning.dive_seconds
				p.dive_dir = Vector2(0.0, signf(py - p.pos.y))
				p.dive_to = py
				events.append([&"dive", k])
	_catch(k, 11.0 + (p.reach - 30.0) * 0.2)


func _catch(k: int, r: float) -> void:
	if owner >= 0 or ball.z > tuning.goal_h + 4.0:
		return
	var p := players[k]
	if p.pos.distance_to(Vector2(ball.x, ball.y)) < r and kicked_by != k:
		owner = k
		p.hold = tuning.keeper_hold
		p.dive = 0.0
		last_touch = k
		events.append([&"save", k])


func _goal(team: int) -> void:
	score[team] += 1
	events.append([&"goal", team])
	owner = -1
	if score[team] >= tuning.goals_to_win:
		_end(team == HERO)
		return
	pause = tuning.goal_pause
	_conceded = RIVAL if team == HERO else HERO


## Розыгрыш с центра: мяч в центре, у ноги пропустившего; герой на своей половине, соперник на своей.
func _kickoff(team: int) -> void:
	var c := Vector2(tuning.pitch_w * 0.5, mid())
	players[HERO].pos = c + Vector2(-60.0 if team == RIVAL else -10.0, 0.0)
	players[HERO].facing = Vector2.RIGHT
	players[RIVAL].pos = c + Vector2(60.0 if team == HERO else 10.0, 0.0)
	players[RIVAL].facing = Vector2.LEFT
	for i in [HERO_KEEPER, RIVAL_KEEPER]:
		players[i].pos = Vector2(_keeper_x(i), mid())
		players[i].dive = 0.0
		players[i].hold = 0.0
		_keeper_seen[i - 2] = c
	for p in players:
		p.down = 0.0
		p.slide = 0.0
		p.charge = -1.0
	ball = Vector3(c.x, c.y, 0.0)
	ball_vel = Vector3.ZERO
	owner = team
	last_touch = team
	kicked_by = -1
	kick_t = 9.0
	_rival_charge = -1.0
	_hero_charge = -1.0
	_rival_aim = mid() + (1.0 if _rng.randf() < 0.5 else -1.0) * tuning.goal_w * 0.35


## Мяч в космос: раз в `space_every` секунд мяч на земле взмывает и пропадает, розыгрыш с центра.
func _space() -> void:
	if space_every <= 0.0:
		return
	_space_t += DT
	if _space_t >= space_every and owner < 0 and ball.z <= 0.0:
		_space_t = 0.0
		ball_vel = Vector3(ball_vel.x * 0.2, ball_vel.y * 0.2, 1400.0)
		events.append([&"space"])
	if ball.z > 600.0:
		_kickoff(HERO if last_touch == RIVAL else RIVAL)


func _end(win: bool) -> void:
	ended = true
	won = win
	events.append([&"win" if win else &"lose"])


# --- Соперник и боты ---------------------------------------------------------------------------

## Соперник по плану: с мячом ведёт к воротам героя, обходит героя, с дальности плана бьёт в
## угол с зарядкой плана; герой с мячом: встаёт между ним и воротами и идёт в подкат; мяч ничей:
## бежит к мячу. Возвращает `[направление, A держится, B нажата]`.
func _rival_ai() -> Array:
	# Прицел: угол подальше от вратаря героя, ближе к штанге на долю из плана (сид решает, в какой
	# угол бить, когда вратарь стоит посередине).
	var keeper := players[HERO_KEEPER]
	var side := signf(_rival_aim - mid())
	if absf(keeper.pos.y - mid()) > 4.0:
		side = 1.0 if keeper.pos.y < mid() else -1.0
	var aim := mid() + side * half_goal(HERO) * 0.75
	return _field_ai(RIVAL, 0.0, aim, plan.rival_shot_range, plan.rival_charge, plan.rival_tackle, true)


## Общий разум полевого игрока: атакует ворота с x = `goal_x`, бьёт в `aim_y`.
func _field_ai(i: int, goal_x: float, aim_y: float, shot_range: float, charge: float, tackle: float, rival: bool) -> Array:
	var p := players[i]
	var other := players[RIVAL if i == HERO else HERO]
	var b := Vector2(ball.x, ball.y)
	var holding := rival and _rival_charge >= 0.0 or not rival and _hero_charge >= 0.0
	if owner == i:
		var goal := Vector2(goal_x, aim_y)
		var to := goal - p.pos
		# Бить: держать A `charge` долей зарядки, потом отпустить.
		if to.length() < shot_range or holding:
			var t := (_rival_charge if rival else _hero_charge)
			t = maxf(t, 0.0) + DT
			if rival:
				_rival_charge = t
			else:
				_hero_charge = t
			p.facing = to.normalized()
			if t >= charge * tuning.charge_max:
				if rival:
					_rival_charge = -1.0
				else:
					_hero_charge = -1.0
				return [to.normalized() * 0.01, false, false]
			return [to.normalized() * 0.01, true, false]
		var dir := to.normalized()
		# Обойти: соперник впереди близко, уйти в сторону.
		var ahead := other.pos - p.pos
		if ahead.length() < 46.0 and ahead.dot(dir) > 0.0:
			var side := Vector2(-dir.y, dir.x) * (1.0 if ahead.cross(dir) > 0.0 else -1.0)
			if p.pos.y + side.y * 40.0 < 30.0 or p.pos.y + side.y * 40.0 > tuning.pitch_h - 30.0:
				side = -side
			dir = (dir + side * 1.2).normalized()
		return [dir, false, false]
	if rival:
		_rival_charge = -1.0
	else:
		_hero_charge = -1.0
	if owner == (RIVAL if i == HERO else HERO):
		# Встать между соперником с мячом и своими воротами, вблизи подкат.
		var own_x := tuning.pitch_w if goal_x < tuning.pitch_w * 0.5 else 0.0
		var guard := other.pos + (Vector2(own_x, mid()) - other.pos).normalized() * 14.0
		var to := guard - p.pos
		var d := other.pos.distance_to(p.pos)
		var slide := d < 20.0 and p.slide_cd <= 0.0 and _rng.randf() < tackle * DT * tuning.tackle_rate
		if slide:
			p.facing = (b - p.pos).normalized()
		return [to.normalized() if to.length() > 3.0 else Vector2.ZERO, false, slide]
	# Мяч ничей или у вратаря: к мячу (у своего вратаря отойти вперёд и ждать).
	if owner >= 0 and players[owner].keeper:
		var wait := Vector2(lerpf(goal_x, tuning.pitch_w * 0.5, 0.5), mid())
		if players[owner].team == p.team:
			wait = Vector2(lerpf(tuning.pitch_w - goal_x, tuning.pitch_w * 0.5, 0.4), mid())
		var tw := wait - p.pos
		return [tw.normalized() if tw.length() > 6.0 else Vector2.ZERO, false, false]
	var lead := b + Vector2(ball_vel.x, ball_vel.y) * 0.2
	var tb := lead - p.pos
	return [tb.normalized() if tb.length() > 2.0 else Vector2.ZERO, false, false]


## Бот: возвращает стрелки, ставит `bot_kick`, `bot_slide`. WIN играет за героя как соперник за
## себя: ведёт к воротам справа и бьёт в дальний от вратаря угол с дальности `bot_shot_range`.
## LOSE стоит; мяч у ноги отдаёт слабым ударом сопернику.
func bot(mode: AutoTest.BotMode) -> Vector2:
	bot_kick = false
	bot_slide = false
	if ended:
		return Vector2.ZERO
	if mode != AutoTest.BotMode.WIN:
		# Мяч у ноги отдать слабым ударом к сопернику (отпускание A на следующем шаге), без мяча
		# стоять.
		if owner == HERO:
			bot_kick = players[HERO].charge < 0.0
			var to := players[RIVAL].pos - players[HERO].pos
			players[HERO].facing = to.normalized() if to.length() > 1.0 else Vector2.RIGHT
			return Vector2.ZERO
		return Vector2.ZERO
	var keeper := players[RIVAL_KEEPER]
	var aim := mid() + (1.0 if keeper.pos.y < mid() else -1.0) * half_goal(RIVAL) * 0.75
	var out := _field_ai(HERO, tuning.pitch_w, aim, tuning.bot_shot_range, tuning.bot_charge, tuning.bot_tackle, false)
	bot_kick = out[1]
	bot_slide = out[2]
	return out[0]
