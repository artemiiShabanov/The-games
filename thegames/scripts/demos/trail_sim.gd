class_name TrailSim
extends RefCounted
## Правила демки платформер × 16/32-bit «тропа» (#98) без окна и звука: герой, физика, враги,
## боты. Демка `platformer_bit16.gd` рисует это состояние и озвучивает события `events`;
## `simulate` гоняет бота по сиду целиком (проверки `demo_test`, `debug/tools/dump_trail.gd`).
## Мир шагает ровно 60 раз в секунду (`step`), поэтому прогон без окна совпадает с демкой.
## Правила: бег с инерцией (разгон, торможение, разворот), склон тянет вниз; прыжок с запасом
## после края и нажатием заранее; B присед: ниже ростом, шаг медленный; B на скорости слайд:
## ещё ниже, по склону вниз разгоняется, на малой скорости переходит в присед; под аркой из
## корней встать нельзя; лиана хватается в прыжке, стрелка раскачивает, A
## отпускает с прибавкой вверх. Краб и попугай убить нельзя: касание стоит жизни и отбрасывает,
## потом неуязвимость. Вода в яме стоит жизни, герой продолжает с последнего места возврата.
## Баги приходят числами: `jump_mult` прыжок выше во столько раз, `enemy_mult` скорость врагов,
## `coins_high` монеты подняты выше любого прыжка, `sneeze` враг падает от касания.

enum State { GROUND, AIR, SLIDE, CROUCH, VINE, HURT, DROWN }

const DT := 1.0 / 60.0
const HALF_W := 6.0
const STAND_H := 26.0
const SLIDE_H := 12.0
const CROUCH_H := 14.0
## Ступенька, которую бег берёт без прыжка; выше это стена.
const STEP_UP := 6.0
## Руки героя над ступнями: этой точкой он висит на лиане.
const HANDS := 22.0
const COIN_RADIUS := 14.0
## Насколько баг «не достать» поднимает монеты.
const COIN_LIFT := 150.0

var tuning: PlatformerBit16Tuning
var level: TrailLevel
var jump_mult := 1.0
var enemy_mult := 1.0
var coins_high := false
var sneeze := false

var state := State.GROUND
## Ступни героя и скорость, пиксели и пиксели в секунду.
var pos := Vector2.ZERO
var vel := Vector2.ZERO
var facing := 1
var state_t := 0.0
## Лиана: индекс, угол от вертикали (плюс вправо), угловая скорость, длина до рук.
var vine := -1
var vine_angle := 0.0
var vine_speed := 0.0
var vine_r := 0.0
var lives := 3
var invuln := 0.0
var coins_got := 0
var deaths := 0
var time := 0.0
var ended := false
var won := false
## Дальше всего, где герой стоял на земле: от этого место возврата.
var max_x := 0.0
var foe_dead: Dictionary[int, float] = {}
var coin_taken := PackedByteArray()
## События шага: `[имя, …]`. `jump`, `land`, `slide`, `grab`, `release`, `fall`, `hurt`
## (причина), `respawn`, `coin`, `foe_down` (индекс), `win`, `lose`. Демка читает и чистит.
var events: Array[Array] = []
## Ввод бота на этом шаге (`bot`).
var bot_jump := false
var bot_slide := false

var _coyote := 0.0
var _buffer := 0.0
var _regrab := -1
var _regrab_t := 0.0
## Прогон варианта ботом: без событий и монет.
var _probe := false
var _bot_t := 0.0
var _plan := {}
var _plan_t := 0.0


static func create(level_: TrailLevel, tuning_: PlatformerBit16Tuning) -> TrailSim:
	var s := TrailSim.new()
	s.level = level_
	s.tuning = tuning_
	s.lives = tuning_.lives
	s.pos = Vector2(level_.start_x, level_.height_at(level_.start_x))
	s.max_x = s.pos.x
	s.coin_taken.resize(level_.coins.size())
	s.coin_taken.fill(0)
	return s


## Прогон бота без окна до конца или до `max_seconds`; `setup` ставит баги.
static func simulate(level_: TrailLevel, tuning_: PlatformerBit16Tuning, mode: AutoTest.BotMode,
		max_seconds := 240.0, setup := Callable()) -> TrailSim:
	var s := create(level_, tuning_)
	if setup.is_valid():
		setup.call(s)
	while not s.ended and s.time < max_seconds:
		var axis := s.bot(mode)
		s.step(axis, s.bot_jump, s.bot_slide)
		s.events.clear()
	return s


func copy() -> TrailSim:
	var s := TrailSim.new()
	s.tuning = tuning
	s.level = level
	s.jump_mult = jump_mult
	s.enemy_mult = enemy_mult
	s.coins_high = coins_high
	s.sneeze = sneeze
	s.state = state
	s.pos = pos
	s.vel = vel
	s.facing = facing
	s.state_t = state_t
	s.vine = vine
	s.vine_angle = vine_angle
	s.vine_speed = vine_speed
	s.vine_r = vine_r
	s.lives = lives
	s.invuln = invuln
	s.deaths = deaths
	s.time = time
	s.ended = ended
	s.won = won
	s.max_x = max_x
	s.foe_dead = foe_dead.duplicate()
	s._coyote = _coyote
	s._buffer = _buffer
	s._regrab = _regrab
	s._regrab_t = _regrab_t
	s._probe = true
	return s


## Рост героя сейчас: в слайде и приседе ниже.
func height() -> float:
	if state == State.SLIDE:
		return SLIDE_H
	return CROUCH_H if state == State.CROUCH else STAND_H


## Низко ли герой: в слайде или приседе, под аркой.
func low() -> bool:
	return state == State.SLIDE or state == State.CROUCH


## Положение врага `i` в момент `at`: x, высота середины тела и направление.
func foe_at(i: int, at: float) -> Vector3:
	var f := level.foes[i]
	var p := TrailLevel.foe_pos(f, at, enemy_mult)
	var ground := level.height_at(p.x)
	if f.kind == TrailLevel.FoeKind.CRAB:
		return Vector3(p.x, ground - 10.0, p.y)
	return Vector3(p.x, ground - 23.0 + roundf(sin(at * 6.0 + f.phase * TAU) * 2.0), p.y)


## Хитбокс героя: ступни в `pos`, ширина `2 * HALF_W`, рост по состоянию.
func hero_box() -> Rect2:
	var h := height()
	return Rect2(pos.x - HALF_W, pos.y - h, 2.0 * HALF_W, h)


## Хитбокс врага `i` в момент `at`: краб с поднятыми клешнями ниже их кончиков, попугай телом.
func foe_box(i: int, at: float) -> Rect2:
	var f := foe_at(i, at)
	var half := Vector2(11.0, 10.0) if level.foes[i].kind == TrailLevel.FoeKind.CRAB else Vector2(9.0, 5.0)
	return Rect2(f.x - half.x, f.y - half.y, 2.0 * half.x, 2.0 * half.y)


## Монета `i` на экране мира: с багом «не достать» выше любого прыжка.
func coin_at(i: int) -> Vector2:
	return level.coins[i] - Vector2(0.0, COIN_LIFT if coins_high else 0.0)


## Шаг мира в 1/60 секунды: `axis` стрелка −1..1, `jump` нажат ли прыжок на этом шаге, `slide`
## зажата ли B.
func step(axis: float, jump: bool, slide: bool) -> void:
	if ended:
		return
	time += DT
	state_t += DT
	invuln = maxf(invuln - DT, 0.0)
	_regrab_t = maxf(_regrab_t - DT, 0.0)
	_buffer = tuning.jump_buffer if jump else maxf(_buffer - DT, 0.0)
	match state:
		State.GROUND, State.SLIDE, State.CROUCH:
			_ground(axis, slide)
		State.AIR:
			_air(axis, true)
		State.HURT:
			_air(0.0, false)
		State.VINE:
			_swing(axis)
		State.DROWN:
			if state_t >= tuning.drown_seconds:
				_respawn()
			return
	if pos.y > level.water_y + 6.0:
		_drown()
		return
	_touch_foes()
	if not _probe:
		_collect()
	if not ended and pos.x >= level.flag_x and (state == State.GROUND or low()):
		ended = true
		won = true
		_emit([&"win"])


func _emit(ev: Array) -> void:
	if not _probe:
		events.append(ev)


func _to(s: State) -> void:
	state = s
	state_t = 0.0


# --- Земля -------------------------------------------------------------------------------------

func _ground(axis: float, slide: bool) -> void:
	var slope := level.slope_at(pos.x)
	# Синус наклона: плюс, когда вправо под гору.
	var sin_a := slope / sqrt(1.0 + slope * slope)
	var pull := tuning.gravity * sin_a
	var ceiling := _under_arch(pos.x)
	if state == State.GROUND and slide:
		# B на скорости это слайд, медленнее присед.
		if absf(vel.x) >= tuning.slide_min:
			vel.x = signf(vel.x) * minf(absf(vel.x) + tuning.slide_boost, tuning.slide_max)
			facing = 1 if vel.x > 0.0 else -1
			_to(State.SLIDE)
			_emit([&"slide"])
		else:
			_to(State.CROUCH)
	if state == State.CROUCH and not slide and not ceiling:
		_to(State.GROUND)
	if state == State.SLIDE:
		vel.x += pull * DT
		vel.x = move_toward(vel.x, 0.0, tuning.slide_friction * DT)
		vel.x = clampf(vel.x, -tuning.slide_max, tuning.slide_max)
		if absf(vel.x) < tuning.slide_to_crouch:
			_to(State.CROUCH if slide or ceiling else State.GROUND)
		elif not slide and not ceiling:
			_to(State.GROUND)
	elif state == State.CROUCH:
		vel.x += pull * tuning.slope_pull * DT
		if axis != 0.0:
			facing = 1 if axis > 0.0 else -1
			var rate := tuning.crouch_accel if absf(vel.x) <= tuning.crouch_max or vel.x * axis < 0.0 else tuning.run_friction
			vel.x = move_toward(vel.x, signf(axis) * tuning.crouch_max, rate * DT)
		else:
			vel.x = move_toward(vel.x, 0.0, tuning.run_friction * DT)
	else:
		vel.x += pull * tuning.slope_pull * DT
		if axis != 0.0:
			facing = 1 if axis > 0.0 else -1
			var cap := tuning.run_max * (1.0 - tuning.uphill_slow * maxf(-sin_a * signf(axis), 0.0))
			# Разворот тормозит сильнее разгона; сверх предела (под гору) скорость сходит мягко.
			var rate := tuning.run_accel
			if vel.x * axis < 0.0:
				rate = tuning.run_turn
			elif absf(vel.x) > cap:
				rate = tuning.run_friction * 0.5
			vel.x = move_toward(vel.x, signf(axis) * cap, rate * DT)
		else:
			vel.x = move_toward(vel.x, 0.0, tuning.run_friction * DT)
	if _buffer > 0.0 and not ceiling:
		_jump()
		_move_air()
		return
	_move_ground()


func _jump() -> void:
	vel.y = -tuning.jump_speed * sqrt(jump_mult)
	_buffer = 0.0
	_coyote = 0.0
	_to(State.AIR)
	_emit([&"jump"])


func _move_ground() -> void:
	var nx := pos.x + vel.x * DT
	if not low() and _arch_wall(nx, pos.y):
		vel.x = 0.0
		return
	var h := level.height_at(nx)
	if h == INF:
		pos.x = nx
		vel.y = 0.0
		_coyote = tuning.coyote
		_to(State.AIR)
		return
	if h < pos.y - STEP_UP:
		vel.x = 0.0
		return
	if h > pos.y + maxf(4.0, absf(vel.x) * DT * 1.3 + 2.0):
		pos.x = nx
		vel.y = 0.0
		_coyote = tuning.coyote
		_to(State.AIR)
		return
	pos = Vector2(nx, h)
	max_x = maxf(max_x, pos.x)


## Над точкой x арка: потолок ниже роста стоя.
func _under_arch(x: float) -> bool:
	for a in level.arches:
		if x + HALF_W > a.from and x - HALF_W < a.to:
			return true
	return false


## Упирается ли герой стоя в ствол арки, встав ступнями в точку (x, feet).
func _arch_wall(x: float, feet: float) -> bool:
	for a in level.arches:
		if x + HALF_W > a.from and x - HALF_W < a.to:
			var ceil := level.height_at(a.from) - a.gap
			if feet - STAND_H < ceil:
				return true
	return false


# --- Воздух ------------------------------------------------------------------------------------

func _air(axis: float, control: bool) -> void:
	if control and axis != 0.0:
		facing = 1 if axis > 0.0 else -1
		var cap := maxf(tuning.run_max, absf(vel.x))
		vel.x = move_toward(vel.x, signf(axis) * cap, tuning.air_accel * DT)
	vel.y += tuning.gravity * DT
	if control:
		_coyote = maxf(_coyote - DT, 0.0)
		if _buffer > 0.0 and _coyote > 0.0:
			_jump()
		if _grab():
			return
	_move_air()


func _move_air() -> void:
	var nx := pos.x + vel.x * DT
	var ny := pos.y + vel.y * DT
	if _arch_wall(nx, ny):
		nx = pos.x
		vel.x = 0.0
	var h := level.height_at(nx)
	# Бок обрыва: ступни уже ниже края земли в новой точке.
	if h != INF and pos.y > h + STEP_UP:
		nx = pos.x
		vel.x = 0.0
		h = level.height_at(nx)
	if vel.y >= 0.0 and h != INF and ny >= h:
		pos = Vector2(nx, h)
		vel.y = 0.0
		_to(State.GROUND)
		max_x = maxf(max_x, pos.x)
		_emit([&"land"])
		return
	pos = Vector2(nx, ny)


# --- Лиана -------------------------------------------------------------------------------------

func _grab() -> bool:
	var hand := pos - Vector2(0.0, HANDS)
	for i in level.vines.size():
		if i == _regrab and _regrab_t > 0.0:
			continue
		var v := level.vines[i]
		var r := hand.distance_to(v.anchor)
		if r < v.length * tuning.vine_grab_from or r > v.length + 2.0:
			continue
		if absf(hand.x - v.anchor.x) > tuning.vine_grab_radius:
			continue
		vine = i
		vine_r = minf(r, v.length)
		vine_angle = asin(clampf((hand.x - v.anchor.x) / vine_r, -1.0, 1.0))
		vine_speed = (vel.x * cos(vine_angle) - vel.y * sin(vine_angle)) / vine_r
		vel = Vector2.ZERO
		_to(State.VINE)
		_emit([&"grab"])
		return true
	return false


func _swing(axis: float) -> void:
	var v := level.vines[vine]
	var acc := -(tuning.gravity / vine_r) * sin(vine_angle)
	if axis != 0.0:
		facing = 1 if axis > 0.0 else -1
		acc += signf(axis) * tuning.vine_pump / vine_r
	vine_speed += acc * DT
	vine_speed *= 1.0 - tuning.vine_damping * DT
	vine_angle += vine_speed * DT
	var lim := deg_to_rad(tuning.vine_max_deg)
	if absf(vine_angle) > lim:
		vine_angle = signf(vine_angle) * lim
		vine_speed = 0.0
	pos = v.anchor + vine_r * Vector2(sin(vine_angle), cos(vine_angle)) + Vector2(0.0, HANDS)
	if _buffer > 0.0:
		vel = vine_r * vine_speed * Vector2(cos(vine_angle), -sin(vine_angle))
		vel.y -= tuning.vine_release_up * sqrt(jump_mult)
		_regrab = vine
		_regrab_t = tuning.vine_regrab
		vine = -1
		_buffer = 0.0
		_to(State.AIR)
		_emit([&"release"])
		return
	# Раскачался над землёй: встал на неё.
	var h := level.height_at(pos.x)
	if h != INF and pos.y >= h:
		pos.y = h
		vel = Vector2.ZERO
		vine = -1
		_to(State.GROUND)
		_emit([&"land"])


# --- Враги, вода, монеты -----------------------------------------------------------------------

func _touch_foes() -> void:
	var me := hero_box()
	for i in level.foes.size():
		if foe_dead.has(i):
			continue
		var box := foe_box(i, time)
		if not me.intersects(box):
			continue
		var f := foe_at(i, time)
		if sneeze:
			foe_dead[i] = time
			_emit([&"foe_down", i])
			continue
		if invuln > 0.0 or state == State.HURT:
			continue
		_hurt(&"краб" if level.foes[i].kind == TrailLevel.FoeKind.CRAB else &"попугай", signf(pos.x - f.x))
		return


func _hurt(why: StringName, away: float) -> void:
	lives -= 1
	deaths += 1
	_emit([&"hurt", why])
	if lives <= 0:
		ended = true
		_emit([&"lose"])
		return
	vine = -1
	vel = Vector2((away if away != 0.0 else -1.0) * tuning.hurt_knock, -tuning.hurt_up)
	invuln = tuning.invulnerable_seconds
	_to(State.HURT)


func _drown() -> void:
	lives -= 1
	deaths += 1
	vine = -1
	vel = Vector2.ZERO
	_to(State.DROWN)
	_emit([&"fall"])
	_emit([&"hurt", &"вода"])
	if lives <= 0:
		ended = true
		_emit([&"lose"])


## Возврат на последнее место возврата, которое герой прошёл по земле.
func _respawn() -> void:
	var cp := level.start_x
	for c in level.checkpoints:
		if c <= max_x + 1.0:
			cp = c
	pos = Vector2(cp, level.height_at(cp))
	vel = Vector2.ZERO
	facing = 1
	invuln = tuning.invulnerable_seconds
	_to(State.GROUND)
	_emit([&"respawn"])


func _collect() -> void:
	if state == State.DROWN:
		return
	var center := pos - Vector2(0.0, height() * 0.5)
	for i in level.coins.size():
		if coin_taken[i] == 0 and center.distance_to(coin_at(i)) < COIN_RADIUS:
			coin_taken[i] = 1
			coins_got += 1
			_emit([&"coin"])


# --- Боты --------------------------------------------------------------------------------------

## Бот: возвращает стрелку и ставит `bot_jump`, `bot_slide`. WIN раз в `bot_every` прогоняет
## варианты на копии мира на `bot_horizon` вперёд (бежать, прыгнуть сейчас или чуть позже,
## слайд, подождать, отступить; на лиане отпустить или качаться) и берёт тот, что дальше всех
## без потери жизни. Если просто бежать безопасно и путь идёт, остальные не считаются. LOSE
## бежит вправо и не прыгает: первая ловушка всегда яма.
func bot(mode: AutoTest.BotMode) -> float:
	bot_jump = false
	bot_slide = false
	if ended:
		return 0.0
	if mode != AutoTest.BotMode.WIN:
		return 1.0
	_bot_t -= DT
	if _bot_t <= 0.0 or _plan.is_empty():
		_bot_t = tuning.bot_every
		_plan = _decide()
		_plan_t = 0.0
	var p := _plan
	bot_jump = bool(p.jump) and absf(_plan_t - float(p.at)) < DT * 0.5
	bot_slide = _plan_t >= float(p.slide_at) and _plan_t < float(p.slide_at) + float(p.slide)
	var axis := float(p.axis) if _plan_t < float(p.hold) else _default_axis()
	_plan_t += DT
	return axis


func _default_axis() -> float:
	if state == State.VINE:
		return 1.0 if vine_speed >= 0.0 else -1.0
	return 1.0


static func _cand(axis: float, hold: float, jump: bool, at: float, slide: float, slide_at := 0.0) -> Dictionary:
	return {axis = axis, hold = hold, jump = jump, at = at, slide = slide, slide_at = slide_at}


func _decide() -> Dictionary:
	var run := _cand(1.0, 0.0, false, 0.0, 0.0)
	if state == State.VINE:
		var hold := _cand(_default_axis(), 0.0, false, 0.0, 0.0)
		var cands: Array[Dictionary] = [hold, _cand(_default_axis(), 0.0, true, 0.0, 0.0)]
		for d in [0.05, 0.1]:
			cands.append(_cand(_default_axis(), 0.0, true, d, 0.0))
		return _best(cands)
	if state == State.DROWN or state == State.HURT:
		return run
	# Просто бежать: если безопасно и герой продвигается, этого хватает.
	var base := _probe_score(run)
	if base > -1.0e5 and base - pos.x > tuning.run_max * tuning.bot_horizon * 0.35:
		return run
	var cands: Array[Dictionary] = [run]
	if state == State.AIR:
		cands.append(_cand(0.0, 0.2, false, 0.0, 0.0))
		cands.append(_cand(-1.0, 0.2, false, 0.0, 0.0))
		cands.append(_cand(-1.0, 0.4, false, 0.0, 0.0))
		return _best(cands)
	for d in [0.0, 0.1, 0.2, 0.3, 0.45, 0.6, 0.8, 1.0]:
		cands.append(_cand(1.0, 0.0, true, d, 0.0))
	for d in [0.0, 0.15, 0.3]:
		cands.append(_cand(1.0, 0.0, false, 0.0, 0.7, d))
	cands.append(_cand(1.0, 0.0, false, 0.0, 1.6, 0.0))
	cands.append(_cand(0.0, 0.3, false, 0.0, 0.0))
	cands.append(_cand(0.0, 0.6, false, 0.0, 0.0))
	cands.append(_cand(-1.0, 0.3, false, 0.0, 0.0))
	cands.append(_cand(0.0, 0.3, true, 0.3, 0.0))
	return _best(cands)


func _best(cands: Array[Dictionary]) -> Dictionary:
	var best := cands[0]
	var best_score := -INF
	for c in cands:
		var s := _probe_score(c)
		if s > best_score + 0.5:
			best_score = s
			best = c
	return best


## Прогон варианта на копии: дальше всех без потери жизни; с потерей чем позже, тем лучше.
func _probe_score(c: Dictionary) -> float:
	var s := copy()
	var t := 0.0
	var limit := tuning.bot_horizon + tuning.bot_land_extra
	var start_lives := lives
	while t < limit:
		var axis := float(c.axis) if t < float(c.hold) else s._default_axis()
		var jump := bool(c.jump) and absf(t - float(c.at)) < DT * 0.5
		var slide := t >= float(c.slide_at) and t < float(c.slide_at) + float(c.slide)
		s.step(axis, jump, slide)
		t += DT
		if s.won:
			return 1.0e6 - t
		if s.lives < start_lives:
			return -1.0e6 + t * 1000.0 + s.pos.x * 0.01
		if t >= tuning.bot_horizon and s.state != State.AIR and s.state != State.HURT:
			break
	return s.pos.x
