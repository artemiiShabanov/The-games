class_name SaberSim
extends RefCounted
## Правила демки файтинг × «продвинутые» «дуэль на саблях» (#125) без окна. Демка
## `fighting_threed.gd` рисует это состояние и озвучивает события `events`; `simulate` гоняет
## бота по сиду целиком (проверки `demo_test`, `debug/tools/dump_saber.gd`).
##
## У каждого бойца стойка: сабля слева, сверху или справа (стороны с места игрока). Стойка
## героя это и его блок, и сторона его удара. Удар соперника блок держит, только если стойка
## героя с той же стороны в миг удара и герой не занят своим ударом. Замах соперника виден:
## он показывает сторону; при финте на `feint_at` замаха сторона меняется. Связку из двух-трёх
## ударов надо отбить целиком, после неё соперник открыт: это время для ответа. Выпад блок не
## держит: от него уходят шагом назад (после шага герой миг возвращается с опущенной саблей).
## В паузе соперник держит стойку и меняет её: удар героя в закрытую сторону отбит и оставляет
## героя открытым, в открытую попадает, если соперник не успел закрыться.

const DT := 1.0 / 60.0

enum Phase { COUNTDOWN, PLAY, DONE }
enum Hero { READY, SWING, RECOVER, STEP, RETURN, STUN }
enum Rival { PAUSE, WINDUP, GAP, OPEN, FLINCH }

var plan: SaberPlan
var tuning: FightingThreedTuning
var phase := Phase.COUNTDOWN
var countdown := 0.0
var time := 0.0
var hero_hp := 100
var rival_hp := 150
## Герой: что делает, сколько осталось, стойка, сторона идущего удара.
var hero := Hero.READY
var hero_left := 0.0
var guard := SaberPlan.Side.TOP
var swing_side := SaberPlan.Side.TOP
## Соперник: что делает, сколько осталось, номер хода и удара в нём, стойка.
var rival := Rival.PAUSE
var rival_left := 0.0
var rival_total := 1.0
var move := 0
var strike := 0
var rival_guard := SaberPlan.Side.TOP
var _guard_left := 0.0
var _resume := 0.0
var ended := false
var won := false
var landed := 0
var parried := 0
var blocks := 0
var taken := 0
var dodges := 0
var steps := 0
## События шага: `[имя, …]`. `go`, `guard(сторона)`, `swing(сторона)`, `land(сторона)`,
## `parried(сторона)`, `step`, `windup(сторона, выпад ли)`, `feint(сторона)`, `block(сторона)`,
## `hurt(сторона, урон)`, `dodge`, `open`, `win`, `dead`, `timeout`.
var events: Array[Array] = []
var bot_side := -1
var bot_strike := false
var bot_back := false

var _rng := RandomNumberGenerator.new()
var _bot_seen := -1
var _bot_wait := 0.0
var _bot_shown := -1


static func create(plan_: SaberPlan, tuning_: FightingThreedTuning) -> SaberSim:
	var sim := SaberSim.new()
	sim.plan = plan_
	sim.tuning = tuning_
	sim.countdown = tuning_.countdown
	sim.hero_hp = tuning_.hero_hp
	sim.rival_hp = tuning_.rival_hp
	sim._rng.seed = hash(plan_.signature())
	sim._enter_pause()
	return sim


## Прогон бота без окна до конца боя.
static func simulate(plan_: SaberPlan, tuning_: FightingThreedTuning, mode: AutoTest.BotMode) -> SaberSim:
	var sim := create(plan_, tuning_)
	while not sim.ended:
		sim.bot(mode, DT)
		sim.step(DT, sim.bot_side, sim.bot_strike, sim.bot_back)
		sim.events.clear()
	return sim


func now() -> SaberPlan.Move:
	return plan.moves[move % plan.moves.size()]


func blow() -> SaberPlan.Strike:
	return now().strikes[mini(strike, now().strikes.size() - 1)]


## Доля замаха соперника 0..1 (вне замаха 0).
func windup_k() -> float:
	return clampf(1.0 - rival_left / rival_total, 0.0, 1.0) if rival == Rival.WINDUP else 0.0


## Сторона, которую сейчас показывает сабля соперника: стойка, а на замахе сторона удара (до
## смены финта ложная).
func shown() -> SaberPlan.Side:
	if rival != Rival.WINDUP:
		return rival_guard
	var b := blow()
	return b.shown if windup_k() < tuning.feint_at else b.side


func lunging() -> bool:
	return rival == Rival.WINDUP and now().lunge


## Герой вне досягаемости (шаг назад).
func away() -> bool:
	return hero == Hero.STEP


## Блок героя сейчас работает.
func guarding() -> bool:
	return hero == Hero.READY


## Шаг мира: сторона стойки (−1 не менять), нажат ли удар, нажат ли шаг назад.
func step(dt: float, side: int, strike_: bool, back: bool) -> void:
	if ended:
		return
	if phase == Phase.COUNTDOWN:
		countdown -= dt
		if countdown <= 0.0:
			phase = Phase.PLAY
			events.append([&"go"])
		return
	time += dt
	if side >= 0 and side != guard and hero != Hero.SWING:
		guard = side as SaberPlan.Side
		events.append([&"guard", guard])
	_step_hero(dt, strike_, back)
	_step_rival(dt)
	if rival_hp <= 0:
		won = true
		ended = true
		phase = Phase.DONE
		events.append([&"win"])
	elif hero_hp <= 0:
		ended = true
		phase = Phase.DONE
		events.append([&"dead"])
	elif time > tuning.max_seconds:
		ended = true
		phase = Phase.DONE
		events.append([&"timeout"])


func _step_hero(dt: float, strike_: bool, back: bool) -> void:
	var t := tuning
	if hero != Hero.READY:
		hero_left -= dt
		if hero_left <= 0.0:
			match hero:
				Hero.SWING:
					_hero_hits()
				Hero.STEP:
					hero = Hero.RETURN
					hero_left = t.step_return
				_:
					hero = Hero.READY
	if back and (hero == Hero.READY or hero == Hero.RECOVER):
		hero = Hero.STEP
		hero_left = t.step_seconds
		steps += 1
		events.append([&"step"])
	elif strike_ and hero == Hero.READY:
		hero = Hero.SWING
		hero_left = t.swing
		swing_side = guard
		events.append([&"swing", swing_side])
		# Соперник в паузе может успеть закрыться.
		if rival == Rival.PAUSE and rival_guard != swing_side and _rng.randf() < now().react:
			rival_guard = swing_side
			_guard_left = now().guard_hold


## Удар героя дошёл: в закрытую сторону отбит, иначе попал.
func _hero_hits() -> void:
	var t := tuning
	var closed := (rival == Rival.PAUSE or rival == Rival.FLINCH) and rival_guard == swing_side
	if closed:
		parried += 1
		hero = Hero.RECOVER
		hero_left = t.recover_blocked
		events.append([&"parried", swing_side])
		return
	landed += 1
	rival_hp = maxi(rival_hp - t.damage, 0)
	hero = Hero.RECOVER
	hero_left = t.recover
	events.append([&"land", swing_side])
	if rival == Rival.PAUSE:
		# Пропустив удар в паузе, соперник вздрагивает и закрывает эту сторону.
		_resume = rival_left
		rival = Rival.FLINCH
		rival_left = t.flinch
		rival_guard = swing_side


func _enter_pause() -> void:
	rival = Rival.PAUSE
	rival_left = now().pause
	rival_total = rival_left
	rival_guard = now().guard
	_guard_left = now().guard_hold
	strike = 0


func _start_windup() -> void:
	rival = Rival.WINDUP
	rival_left = blow().windup
	rival_total = rival_left
	events.append([&"windup", blow().shown, now().lunge])


func _step_rival(dt: float) -> void:
	var t := tuning
	var was := windup_k()
	rival_left -= dt
	match rival:
		Rival.PAUSE:
			_guard_left -= dt
			if _guard_left <= 0.0:
				# Меняет стойку: всегда на другую сторону.
				rival_guard = ((rival_guard + 1 + _rng.randi_range(0, 1)) % 3) as SaberPlan.Side
				_guard_left = now().guard_hold
			if rival_left <= 0.0:
				_start_windup()
		Rival.FLINCH:
			if rival_left <= 0.0:
				rival = Rival.PAUSE
				rival_left = maxf(_resume, 0.25)
		Rival.WINDUP:
			if blow().feint() and was < t.feint_at and windup_k() >= t.feint_at:
				events.append([&"feint", blow().side])
			if rival_left <= 0.0:
				_rival_hits()
				if strike < now().strikes.size() - 1:
					strike += 1
					rival = Rival.GAP
					rival_left = t.combo_gap
				else:
					rival = Rival.OPEN
					rival_left = t.open_seconds
					rival_guard = blow().side
					events.append([&"open"])
		Rival.GAP:
			if rival_left <= 0.0:
				_start_windup()
		Rival.OPEN:
			if rival_left <= 0.0:
				move += 1
				_enter_pause()


## Удар соперника дошёл.
func _rival_hits() -> void:
	var t := tuning
	var b := blow()
	if away():
		dodges += 1
		events.append([&"dodge"])
		return
	if not now().lunge and guarding() and guard == b.side:
		blocks += 1
		events.append([&"block", b.side])
		return
	var amount := t.lunge_damage if now().lunge else t.rival_damage
	taken += 1
	hero_hp = maxi(hero_hp - amount, 0)
	hero = Hero.STUN
	hero_left = t.stun
	events.append([&"hurt", b.side, amount])


# --- Боты ------------------------------------------------------------------------------------

## Бот: ставит `bot_side`, `bot_strike`, `bot_back`. WIN читает саблю соперника с задержкой
## `bot_delay` и ставит стойку туда же, от выпада шагает назад, после связки бьёт открытого
## соперника. LOSE стоит в стойке сверху и не бьёт.
func bot(mode: AutoTest.BotMode, dt: float) -> void:
	bot_side = -1
	bot_strike = false
	bot_back = false
	if ended or mode != AutoTest.BotMode.WIN or phase != Phase.PLAY:
		return
	# Увиденная сторона доходит до рук не сразу.
	var see := int(shown())
	if see != _bot_shown:
		_bot_shown = see
		_bot_wait = tuning.bot_delay
	_bot_wait -= dt
	if _bot_wait <= 0.0:
		_bot_seen = _bot_shown
	if rival == Rival.WINDUP or rival == Rival.GAP:
		if lunging():
			bot_back = rival_left <= tuning.bot_step
		elif _bot_seen >= 0:
			bot_side = _bot_seen
	elif rival == Rival.OPEN and hero == Hero.READY and rival_left >= tuning.swing + 0.03:
		bot_strike = true
