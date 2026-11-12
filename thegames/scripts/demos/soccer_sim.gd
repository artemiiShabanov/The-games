class_name SoccerSim
extends RefCounted
## Правила футбола × 16/32-bit (#101, графика по Sensible Soccer) без окна и звука: две команды
## по двое полевых и вратарю (плейтест 2026-11-12: «один на одного» выглядел странно), мяч,
## счёт, боты. Демка `sport_bit16.gd` рисует это состояние и озвучивает события; `simulate`
## гоняет бота по сиду целиком (проверки `demo_test`, `debug/tools/dump_soccer.gd`). Мир шагает
## ровно 60 раз в секунду. Поле горизонтально: ворота героя слева (x = 0), соперника справа.
## Управление: игрок ведёт того из своих, у кого мяч (в атаке управление переходит к получившему
## мяч), в защите того, кого вёл последним (`ctrl`); остальные полевые по ролям: с мячом ведёт к
## воротам, обходит, отдаёт пас открытому партнёру, бьёт; партнёр открывается впереди сбоку; в
## защите ближний к мячу прессингует и идёт в подкат, второй держит своего.
## Правила: мяч липнет к ноге того, кто его коснулся на земле и не слишком быстрый, с мячом бег
## медленнее (`dribble_speed`); отобрать мяч можно только подкатом. A держать: зарядка удара,
## отпустить: удар по взгляду (короткое нажатие это пас), сразу после удара стрелка поперёк
## подкручивает мяч. B подкат. Вратарь стоит ближе к центру створа, пока мяч далеко, на удар в
## створ прыгает в угаданную точку с ошибкой (у вратаря героя меньше), поймал: держит и
## выбрасывает своему. Лицевая мимо створа: от ворот, боковая: мяч на линии, ничей. Гол: пауза и
## розыгрыш с центра пропустившим. Матч до трёх.
## Баги приходят числами: `bounce_mult` мяч скачет, как резиновый; `goal_mult` ворота соперника
## уже; `sneeze` соперник падает от любого касания; `space_every` мяч раз в столько секунд улетает
## вверх за поле.

const DT := 1.0 / 60.0
## Команды и игроки: 0 и 1 это и номера команд, и первые полевые; 2, 3 вратари; 4, 5 партнёры.
const HERO := 0
const RIVAL := 1
const HERO_KEEPER := 2
const RIVAL_KEEPER := 3
const HERO_MATE := 4
const RIVAL_MATE := 5

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
	var error := 52.0

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
## Кем из своих управляет игрок (или бот за героя).
var ctrl := HERO
var score: Array[int] = [0, 0]
var time := 0.0
var ended := false
var won := false
var pause := 0.0
var kicks := 0
## События шага: `[имя, …]`. `kick` (игрок), `pass` (игрок), `bounce`, `control` (игрок),
## `switch` (игрок), `slide` (игрок), `tackle` (игрок, кого), `dive` (вратарь), `save` (вратарь),
## `throw`, `goal` (команда), `out`, `space`, `win`, `lose`. Демка читает и чистит.
var events: Array[Array] = []
## Ввод бота на этом шаге.
var bot_kick := false
var bot_slide := false

var _rng := RandomNumberGenerator.new()
var _steal_cd := 0.0
var _space_t := 0.0
var _conceded := RIVAL
var _keeper_seen: Array[Vector2] = [Vector2.ZERO, Vector2.ZERO]
## Сколько секунд зарядки держит ИИ игрока, который решил бить (по индексу).
var _ai_charge: Dictionary[int, float] = {}


static func create(plan_: SoccerPlan, tuning_: SportBit16Tuning) -> SoccerSim:
	var s := SoccerSim.new()
	s.plan = plan_
	s.tuning = tuning_
	s._rng.seed = hash(str(plan_.seed, ":match"))
	for i in 6:
		var p := Player.new()
		p.team = HERO if i in [HERO, HERO_KEEPER, HERO_MATE] else RIVAL
		p.keeper = i == HERO_KEEPER or i == RIVAL_KEEPER
		if p.keeper:
			p.speed = tuning_.keeper_speed
			p.reach = plan_.keeper_reach if p.team == HERO else plan_.rival_keeper_reach
			p.react = plan_.keeper_react if p.team == HERO else plan_.rival_keeper_react
			p.error = tuning_.hero_keeper_error if p.team == HERO else tuning_.keeper_error
		else:
			p.speed = tuning_.run_speed if p.team == HERO else plan_.rival_speed
			p.react = plan_.rival_react
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


## Полевые игроки команды.
static func field(team: int) -> Array[int]:
	var out: Array[int] = [HERO, HERO_MATE]
	if team == RIVAL:
		out = [RIVAL, RIVAL_MATE]
	return out


## x ворот, которые команда атакует, и своих.
func attack_x(team: int) -> float:
	return tuning.pitch_w if team == HERO else 0.0


func own_x(team: int) -> float:
	return 0.0 if team == HERO else tuning.pitch_w


## Шаг мира в 1/60 секунды: `axis` стрелки, `kick` держится ли A, `slide` нажата ли B (для
## того, кем управляет игрок).
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
	# Управление переходит к своему, у кого мяч.
	if owner >= 0 and owner != ctrl and players[owner].team == HERO and not players[owner].keeper:
		ctrl = owner
		events.append([&"switch", ctrl])
	for i in [HERO, HERO_MATE, RIVAL, RIVAL_MATE]:
		if i == ctrl:
			_control(i, axis, kick, slide)
		else:
			var ai := _field_ai(i)
			_control(i, ai[0], ai[1], ai[2])
	_keeper(HERO_KEEPER)
	_keeper(RIVAL_KEEPER)
	_aftertouch(axis)
	_ball_step()
	_touches()
	_space()


## Полевой игрок: бег по `dir` (с мячом медленнее), зарядка и удар, подкат.
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
	p.vel = dir.limit_length(1.0) * p.speed * (tuning.dribble_speed if owner == i else 1.0)
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


## Подкрутка героя: сразу после удара того, кем он управляет, стрелка поперёк мяча закручивает.
func _aftertouch(axis: Vector2) -> void:
	if kicked_by != ctrl or kick_t > tuning.aftertouch_seconds or owner >= 0 or axis.length() < 0.1:
		return
	var v := Vector2(ball_vel.x, ball_vel.y)
	if v.length() < 1.0:
		return
	var side := Vector2(-v.y, v.x).normalized()
	v += side * axis.dot(side) * tuning.aftertouch * DT
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
		var h := Vector2(ball_vel.x, ball_vel.y).move_toward(Vector2.ZERO, tuning.friction * DT)
		ball_vel.x = h.x
		ball_vel.y = h.y
	_lines()


## Гол, лицевая, боковая.
func _lines() -> void:
	for side in 2:
		var crossed := ball.x < 0.0 if side == 0 else ball.x > tuning.pitch_w
		if not crossed:
			continue
		var team := HERO if side == 0 else RIVAL
		if absf(ball.y - mid()) < half_goal(team) and ball.z < tuning.goal_h:
			_goal(RIVAL if team == HERO else HERO)
			return
		events.append([&"out"])
		_give_keeper(HERO_KEEPER if team == HERO else RIVAL_KEEPER)
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


## Касания: мяч к ноге, подкат, чих.
func _touches() -> void:
	var b := Vector2(ball.x, ball.y)
	var b_speed := Vector2(ball_vel.x, ball_vel.y).length()
	for i in [HERO, HERO_MATE, RIVAL, RIVAL_MATE]:
		var p := players[i]
		if p.down > 0.0:
			continue
		if p.pos.distance_to(b) >= tuning.radius + 6.0 or ball.z >= 10.0:
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
			_ai_charge.erase(i)
			events.append([&"control", i])
	# Чих: соперник падает от любого касания того, кем управляет игрок.
	if sneeze:
		var me := players[ctrl]
		for i in field(RIVAL):
			var r := players[i]
			if r.down <= 0.0 and me.pos.distance_to(r.pos) < tuning.radius * 2.0:
				r.down = tuning.down_seconds * 2.0
				if owner == i:
					owner = ctrl
				events.append([&"tackle", ctrl, i])


## Вратарь: держит мяч и выбрасывает своему открытому; прыжок; стоит ближе к центру створа, пока
## мяч далеко, вблизи идёт за мячом.
func _keeper(k: int) -> void:
	var p := players[k]
	var team := p.team
	var gx := _keeper_x(k)
	if owner == k:
		p.hold -= DT
		if p.hold <= 0.0:
			var mate := players[_open_mate(team, p.pos)]
			var to := mate.pos - p.pos
			_kick(k, to, clampf(to.length() / 500.0, 0.3, 0.6))
			events.append([&"throw", k])
		return
	if p.dive > 0.0:
		p.dive -= DT
		p.pos.y = move_toward(p.pos.y, p.dive_to, tuning.dive_speed * DT)
		_catch(k, tuning.dive_catch)
		return
	var seen := _keeper_seen[k - 2].lerp(Vector2(ball.x, ball.y), minf(DT / maxf(p.react, 0.01), 1.0))
	_keeper_seen[k - 2] = seen
	var hg := half_goal(team)
	var near := absf(seen.x - gx) < 70.0
	var ty := clampf(seen.y if near else mid() + (seen.y - mid()) * 0.35, mid() - hg, mid() + hg)
	if owner < 0 and not near and kick_t < 1.0:
		ty = p.pos.y
	p.pos = p.pos.move_toward(Vector2(gx, ty), p.speed * DT)
	var vx := ball_vel.x
	var toward := (vx < -20.0 and team == HERO) or (vx > 20.0 and team == RIVAL)
	if owner < 0 and toward and kick_t > p.react:
		var t := (gx - ball.x) / vx
		if t > 0.0 and t < tuning.dive_window:
			var py := ball.y + ball_vel.y * t + _rng.randf_range(-p.error, p.error)
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


## Розыгрыш с центра: мяч у ноги пропустившего, партнёры по своим половинам.
func _kickoff(team: int) -> void:
	var c := Vector2(tuning.pitch_w * 0.5, mid())
	var lay := {
		HERO: c + Vector2(-60.0 if team == RIVAL else -10.0, 0.0),
		HERO_MATE: c + Vector2(-150.0, -110.0),
		RIVAL: c + Vector2(60.0 if team == HERO else 10.0, 0.0),
		RIVAL_MATE: c + Vector2(150.0, 110.0),
	}
	for i: int in lay:
		players[i].pos = lay[i]
		players[i].facing = Vector2.RIGHT if players[i].team == HERO else Vector2.LEFT
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
	ctrl = HERO
	last_touch = team
	kicked_by = -1
	kick_t = 9.0
	_ai_charge.clear()


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
		_kickoff(HERO if last_touch in field(RIVAL) else RIVAL)


func _end(win: bool) -> void:
	ended = true
	won = win
	events.append([&"win" if win else &"lose"])


# --- Разум полевых и боты ----------------------------------------------------------------------

## Партнёр по команде полевого `i`.
static func mate_of(i: int) -> int:
	return {HERO: HERO_MATE, HERO_MATE: HERO, RIVAL: RIVAL_MATE, RIVAL_MATE: RIVAL}[i]


## Самый открытый из своих полевых для выброса или паса: дальше всех от соперников.
func _open_mate(team: int, from: Vector2) -> int:
	var best := field(team)[0]
	var best_gap := -1.0
	for i in field(team):
		var gap := INF
		for o in field(RIVAL if team == HERO else HERO):
			gap = minf(gap, players[o].pos.distance_to(players[i].pos))
		gap -= players[i].pos.distance_to(from) * 0.1
		if gap > best_gap:
			best_gap = gap
			best = i
	return best


## Прицел: угол чужих ворот подальше от вратаря.
func _aim(team: int) -> float:
	var keeper := players[RIVAL_KEEPER if team == HERO else HERO_KEEPER]
	var side := 1.0 if keeper.pos.y < mid() else -1.0
	if absf(keeper.pos.y - mid()) < 4.0:
		side = 1.0 if int(time) % 2 == 0 else -1.0
	return mid() + side * half_goal(RIVAL if team == HERO else HERO) * 0.75


## Параметры разума команды: дальность удара, зарядка, подкат.
func _style(team: int) -> Array:
	if team == HERO:
		return [tuning.bot_shot_range, tuning.bot_charge, tuning.bot_tackle]
	return [plan.rival_shot_range, plan.rival_charge, plan.rival_tackle]


## Разум полевого `i` по роли: `[направление, A держится, B нажата]`.
func _field_ai(i: int) -> Array:
	var p := players[i]
	var team := p.team
	var b := Vector2(ball.x, ball.y)
	var style := _style(team)
	var goal_x := attack_x(team)
	var foes := field(RIVAL if team == HERO else HERO)
	# С мячом: к воротам, обойти, пас открытому партнёру, удар.
	if owner == i:
		var goal := Vector2(goal_x, _aim(team))
		var to := goal - p.pos
		if _ai_charge.has(i):
			p.facing = (Vector2(goal_x, _ai_charge_aim(i)) - p.pos).normalized()
			if p.charge >= float(_ai_charge[i]):
				_ai_charge.erase(i)
				return [Vector2.ZERO, false, false]
			return [Vector2.ZERO, true, false]
		if to.length() < float(style[0]):
			_ai_charge[i] = float(style[1]) * tuning.charge_max
			_ai_aim[i] = goal.y
			return [Vector2.ZERO, true, false]
		var dir := to.normalized()
		var block := _blocker(i, dir, foes)
		if block >= 0:
			# Партнёр впереди и открыт: пас коротким ударом.
			var m := players[mate_of(i)]
			var ahead := (m.pos.x - p.pos.x) * signf(goal_x - p.pos.x)
			if ahead > 30.0 and _lane_open(p.pos, m.pos, foes):
				p.facing = (m.pos + m.vel * 0.3 - p.pos).normalized()
				_ai_charge[i] = tuning.pass_charge * tuning.charge_max
				_ai_aim[i] = -1.0
				events.append([&"pass", i])
				return [Vector2.ZERO, true, false]
			var away := players[block].pos - p.pos
			var side := Vector2(-dir.y, dir.x) * (1.0 if away.cross(dir) > 0.0 else -1.0)
			if p.pos.y + side.y * 40.0 < 30.0 or p.pos.y + side.y * 40.0 > tuning.pitch_h - 30.0:
				side = -side
			dir = (dir + side * 1.2).normalized()
		return [dir, false, false]
	_ai_charge.erase(i)
	var carrier_team := players[owner].team if owner >= 0 else -1
	# Свои с мячом: открыться впереди сбоку от ведущего.
	if carrier_team == team and owner >= 0 and not players[owner].keeper:
		var c := players[owner]
		var fwd := signf(goal_x - c.pos.x)
		var spot := Vector2(c.pos.x + fwd * 120.0, mid() + (mid() - c.pos.y) * 0.6 + (90.0 if c.pos.y < mid() else -90.0))
		spot.x = clampf(spot.x, 60.0, tuning.pitch_w - 60.0)
		spot.y = clampf(spot.y, 40.0, tuning.pitch_h - 40.0)
		return [_toward(p.pos, spot), false, false]
	# Чужие с мячом: ближний к ведущему прессингует, второй держит своего.
	if carrier_team != -1 and carrier_team != team and not players[owner].keeper:
		var c := players[owner]
		var presser := field(team)[0]
		for j in field(team):
			if players[j].pos.distance_to(c.pos) < players[presser].pos.distance_to(c.pos):
				presser = j
		if presser == i:
			var guard := c.pos + (Vector2(own_x(team), mid()) - c.pos).normalized() * 14.0
			var slide := c.pos.distance_to(p.pos) < 20.0 and p.slide_cd <= 0.0 and _rng.randf() < float(style[2]) * DT * tuning.tackle_rate
			if slide:
				p.facing = (b - p.pos).normalized()
			return [_toward(p.pos, guard), false, slide]
		var mark := players[mate_of(owner)].pos
		var cover := mark + (Vector2(own_x(team), mid()) - mark).normalized() * 30.0
		return [_toward(p.pos, cover), false, false]
	# Мяч у вратаря: встать на свою позицию.
	if owner >= 0 and players[owner].keeper:
		var mine := players[owner].team == team
		var depth := 0.4 if mine else 0.55
		var x := lerpf(own_x(team), tuning.pitch_w * 0.5, depth if i in [HERO, RIVAL] else depth * 0.7)
		var y := mid() + (-80.0 if i in [HERO, RIVAL] else 80.0)
		return [_toward(p.pos, Vector2(x, y)), false, false]
	# Мяч ничей: ближний из своих к мячу, второй держит позицию между мячом и своими воротами.
	var chaser := field(team)[0]
	for j in field(team):
		if players[j].pos.distance_to(b) < players[chaser].pos.distance_to(b):
			chaser = j
	if chaser == i:
		return [_toward(p.pos, b + Vector2(ball_vel.x, ball_vel.y) * 0.2), false, false]
	var hold := b.lerp(Vector2(own_x(team), mid()), 0.45)
	return [_toward(p.pos, hold), false, false]


var _ai_aim: Dictionary[int, float] = {}


func _ai_charge_aim(i: int) -> float:
	var a := float(_ai_aim.get(i, -1.0))
	return a if a >= 0.0 else players[i].pos.y + players[i].facing.y * 100.0


func _toward(from: Vector2, to: Vector2) -> Vector2:
	var d := to - from
	return d.normalized() if d.length() > 4.0 else Vector2.ZERO


## Соперник впереди близко по ходу `dir` или −1.
func _blocker(i: int, dir: Vector2, foes: Array[int]) -> int:
	for o in foes:
		var ahead := players[o].pos - players[i].pos
		if ahead.length() < 46.0 and ahead.dot(dir) > 0.0:
			return o
	return -1


## Свободна ли линия паса: никто из соперников не ближе 18 к отрезку.
func _lane_open(a: Vector2, b: Vector2, foes: Array[int]) -> bool:
	for o in foes:
		var q := Geometry2D.get_closest_point_to_segment(players[o].pos, a, b)
		if q.distance_to(players[o].pos) < 18.0:
			return false
	return true


## Бот: возвращает стрелки, ставит `bot_kick`, `bot_slide` для того, кем управляет. WIN играет
## за управляемого тем же разумом, что и остальные полевые; LOSE стоит и отдаёт мяч сопернику
## слабым ударом.
func bot(mode: AutoTest.BotMode) -> Vector2:
	bot_kick = false
	bot_slide = false
	if ended:
		return Vector2.ZERO
	if mode != AutoTest.BotMode.WIN:
		if owner == ctrl:
			bot_kick = players[ctrl].charge < 0.0
			var to := players[RIVAL].pos - players[ctrl].pos
			players[ctrl].facing = to.normalized() if to.length() > 1.0 else Vector2.RIGHT
		return Vector2.ZERO
	var out := _field_ai(ctrl)
	bot_kick = out[1]
	bot_slide = out[2]
	return out[0]
