class_name SparSim
extends RefCounted
## Правила демки файтинг × low poly «один на один сбоку в объёме» (#116) без окна: два бойца на
## палубе лицом друг к другу, удары с замахом, блок стоя и в приседе, шаг в глубину, план
## соперника и боты. Демка `fighting_lowpoly.gd` рисует это состояние и озвучивает события
## `events`; `simulate` гоняет бота по плану целиком (проверки `demo_test`,
## `debug/tools/dump_spar.gd`).
##
## Удар: замах, в конце замаха он приходится в цель, потом боец открыт. Верхний удар держит
## блок стоя, нижний блок в приседе, сильный удар соперника блок не держит. Шаг в глубину
## уводит от любого удара; соперник, промахнувшись по шагнувшему, открыт сбоку, и удар по нему
## в это время в полтора раза сильнее. Соперник бьёт связками по плану: пока связка не
## кончилась, он не открыт и его замах не сбить. После последнего удара связки, принятого в
## блок или ушедшего мимо, он открыт: это время для ответа. Удар героя мимо или в блок
## оставляет открытым героя, и соперник отвечает сразу. После нескольких ударов в блок подряд
## соперник выдыхается и какое-то время не нападает. Бой до нокаута.

const DT := 1.0 / 60.0

enum Phase { COUNTDOWN, FIGHT, DONE }
enum State { IDLE, WINDUP, RECOVER, STUN, STEP, KO }

class Fighter:
	var x := 0.0
	## Уход вбок от линии боя (шаг в глубину).
	var z := 0.0
	var hp := 100
	var state := State.IDLE
	## Сколько осталось в состоянии и сколько оно длится всего.
	var timer := 0.0
	var total := 0.0
	var move := SparPlan.Move.PUNCH
	var block := false
	## Какой по счёту удар связки идёт (у героя) и что нажато в запас во время удара.
	var chain := 0
	var queued := -1
	## Открыт: в этом состоянии не закрыться (после промаха, после последнего удара связки).
	var open := false
	## Сколько секунд ещё открыт сбоку.
	var flank := 0.0
	var side := 1
	var step_wait := 0.0
	## Сколько секунд ещё летит по дуге после удара (баг «невесомость»).
	var air := 0.0

	func begin(state_: State, seconds: float) -> void:
		state = state_
		timer = seconds
		total = seconds

	## Доля состояния, 0..1.
	func progress() -> float:
		return 1.0 - timer / total if total > 0.0 else 1.0


class Controls:
	## Ходьба −1..1 (плюс к сопернику), удар рукой и удар ногой (нажатия), блок (держит), шаг в
	## глубину (нажатие: −1 от камеры, 1 к камере).
	var move := 0.0
	var strike := false
	var kick := false
	var block := false
	var step := 0


var plan: SparPlan
var tuning: FightingLowpolyTuning
var phase := Phase.COUNTDOWN
var countdown := 0.0
var time := 0.0
var hero := Fighter.new()
var rival := Fighter.new()
## Какая связка и какой удар в ней; пауза до связки.
var combo_index := 0
var move_index := 0
var wait := 0.0
var guard_index := 0
## Сколько ударов соперника подряд ушло в блок; выдохся ли он (скажется на паузе до связки).
## Баги жанра и баланса (#117), демка ставит их по записи: `ghost_every` каждый такой удар героя
## проходит сквозь соперника (0 выключено), `launch` на сколько метров отбрасывает удар
## (невесомость), `sneeze` соперник падает от любого касания, даже в блок, `immortal` здоровье
## соперника тут же возвращается и бой кончается по времени `immortal_seconds`. Событие `ghost`:
## удар героя прошёл насквозь.
var ghost_every := 0
var launch := 0.0
var sneeze := false
var immortal := false
var immortal_seconds := 40.0
var hero_strikes := 0
var blocked_streak := 0
var tired := false
var tires := 0
var ended := false
var finished := false
var hero_hits := 0
var flank_hits := 0
var blocks := 0
var dodges := 0
var taken := 0
## События шага для звука и эффектов: `[имя, …]`. `go`, `windup(кто, удар)`, `hit(кого, урон,
## сбоку, сильный)`, `block(кто закрылся)`, `whiff(кто промахнулся)`, `step`, `ko(кого)`,
## `tired` (соперник выдохся), `timeout`; кто: 0 герой, 1 соперник. Демка читает и чистит.
var events: Array[Array] = []
## Что бот хочет на этом шаге (`bot`).
var bot_controls := Controls.new()

var _stepped := false


static func create(plan_: SparPlan, tuning_: FightingLowpolyTuning) -> SparSim:
	var sim := SparSim.new()
	sim.plan = plan_
	sim.tuning = tuning_
	sim.countdown = tuning_.countdown
	sim.hero.x = -tuning_.start_gap
	sim.hero.hp = tuning_.hero_hp
	sim.rival.x = tuning_.start_gap
	sim.rival.hp = tuning_.rival_hp
	sim.wait = plan_.combo(0).gap
	return sim


## Прогон бота без окна до конца боя.
static func simulate(plan_: SparPlan, tuning_: FightingLowpolyTuning, mode: AutoTest.BotMode) -> SparSim:
	var sim := create(plan_, tuning_)
	while not sim.ended:
		sim.bot(mode)
		sim.step(DT, sim.bot_controls)
		sim.events.clear()
	return sim


func gap() -> float:
	return rival.x - hero.x


## Удар, который соперник сейчас готовит, и замах этого удара.
func rival_move() -> int:
	var moves := plan.combo(combo_index).moves
	return moves[mini(move_index, moves.size() - 1)]


func windup_of(move: int) -> float:
	if move == SparPlan.Move.HEAVY:
		return plan.heavy_windup
	return plan.combo(combo_index).windup * (tuning.rival_kick_windup if move == SparPlan.Move.KICK else 1.0)


## Может ли соперник сейчас закрыться от удара.
func rival_open() -> bool:
	return rival.flank > 0.0 or rival.state == State.STUN or (rival.state == State.RECOVER and rival.open)


## Шаг мира.
func step(dt: float, inp: Controls) -> void:
	if ended:
		return
	if phase == Phase.COUNTDOWN:
		countdown -= dt
		if countdown <= 0.0:
			phase = Phase.FIGHT
			events.append([&"go"])
		return
	time += dt
	hero.flank = maxf(hero.flank - dt, 0.0)
	rival.flank = maxf(rival.flank - dt, 0.0)
	hero.step_wait = maxf(hero.step_wait - dt, 0.0)
	hero.air = maxf(hero.air - dt, 0.0)
	rival.air = maxf(rival.air - dt, 0.0)
	_step_hero(dt, inp)
	_step_rival(dt)
	if immortal:
		rival.hp = mini(rival.hp + int(ceilf(120.0 * dt)), tuning.rival_hp)
	if hero.hp <= 0 or rival.hp <= 0:
		var down := hero if hero.hp <= 0 else rival
		down.begin(State.KO, 0.0)
		phase = Phase.DONE
		ended = true
		finished = hero.hp > 0
		events.append([&"ko", 0 if hero.hp <= 0 else 1])
	elif time > (immortal_seconds if immortal else tuning.max_seconds):
		phase = Phase.DONE
		ended = true
		events.append([&"timeout"])


func _step_hero(dt: float, inp: Controls) -> void:
	var f := hero
	match f.state:
		State.IDLE:
			f.block = inp.block
			f.chain = 0
			if inp.step != 0 and f.step_wait <= 0.0:
				f.side = inp.step
				f.block = false
				f.begin(State.STEP, tuning.step_seconds)
				events.append([&"step"])
			elif inp.strike or inp.kick:
				f.block = false
				f.move = SparPlan.Move.KICK if inp.kick and not inp.strike else SparPlan.Move.PUNCH
				f.queued = -1
				f.begin(State.WINDUP, tuning.kick_windup if f.move == SparPlan.Move.KICK else tuning.hero_windup)
				events.append([&"windup", 0, f.move])
			elif not f.block and inp.move != 0.0:
				f.x = clampf(f.x + clampf(inp.move, -1.0, 1.0) * tuning.hero_walk * dt, -tuning.arena_half, rival.x - tuning.min_gap)
		State.WINDUP:
			_queue(inp)
			f.timer -= dt
			if f.timer <= 0.0:
				_hero_strikes()
		State.STEP:
			f.timer -= dt
			f.z = f.side * tuning.step_depth * sin(PI * f.progress())
			if f.timer <= 0.0:
				f.z = 0.0
				f.step_wait = tuning.step_cooldown
				f.begin(State.IDLE, 0.0)
		State.RECOVER:
			_queue(inp)
			f.timer -= dt
			# Связка: попавший удар рукой продолжается следующим, если он нажат.
			if not f.open and f.chain > 0 and f.queued >= 0 and f.total - f.timer >= tuning.hero_link:
				f.move = f.queued as SparPlan.Move
				f.queued = -1
				f.begin(State.WINDUP, tuning.kick_chain_windup if f.move == SparPlan.Move.KICK else tuning.hero_chain_windup)
				events.append([&"windup", 0, f.move])
			elif f.timer <= 0.0:
				f.open = false
				f.begin(State.IDLE, 0.0)
		State.STUN:
			f.timer -= dt
			if f.timer <= 0.0:
				f.open = false
				f.begin(State.IDLE, 0.0)


## Нажатие во время удара запоминается: им продолжится связка.
func _queue(inp: Controls) -> void:
	if inp.strike:
		hero.queued = SparPlan.Move.PUNCH
	elif inp.kick:
		hero.queued = SparPlan.Move.KICK


func _hero_strikes() -> void:
	var f := hero
	var kick := f.move == SparPlan.Move.KICK
	var punished := tuning.kick_punished if kick else tuning.hero_punished
	if gap() > (tuning.kick_reach if kick else tuning.hero_reach):
		f.open = true
		f.chain = 0
		f.begin(State.RECOVER, punished)
		events.append([&"whiff", 0])
		return
	var guarded := false
	if not rival_open() and rival.state == State.IDLE:
		var roll := plan.guard[guard_index % plan.guard.size()]
		guard_index += 1
		guarded = roll < (plan.guard_kick if kick else plan.guard_punch)
	hero_strikes += 1
	if sneeze:
		# От чиха: соперник падает от любого касания, даже в блок.
		rival.hp = 0
		hero_hits += 1
		f.begin(State.RECOVER, tuning.hero_recover)
		events.append([&"hit", 1, tuning.rival_hp, false, kick])
		return
	if ghost_every > 0 and hero_strikes % ghost_every == 0:
		# Удар прошёл сквозь соперника.
		f.chain = 0
		f.begin(State.RECOVER, tuning.hero_recover)
		events.append([&"ghost"])
		return
	if guarded:
		# Соперник закрылся: герой открыт, ответ идёт сразу.
		f.open = true
		f.chain = 0
		f.begin(State.RECOVER, punished)
		rival.block = true
		wait = 0.0
		events.append([&"block", 1])
		return
	var side := rival.flank > 0.0
	var base := tuning.kick_damage if kick else tuning.punch_damage[mini(f.chain, tuning.punch_damage.size() - 1)]
	var damage := int(roundf(base * (tuning.flank_mult if side else 1.0)))
	rival.hp -= damage
	hero_hits += 1
	flank_hits += 1 if side else 0
	# Удар ногой и третий удар рукой связку заканчивают.
	f.chain = 0 if kick or f.chain >= tuning.punch_damage.size() - 1 else f.chain + 1
	f.begin(State.RECOVER, tuning.kick_recover if kick else tuning.hero_recover)
	# Связку соперника ударом не сбить (ни замах, ни паузу между ударами): урон проходит, удар
	# всё равно будет. Открытого соперника удар оглушает, его связка на этом кончена.
	var armored := rival.state == State.WINDUP or (rival.state == State.RECOVER and not rival.open)
	if not armored:
		if rival.state == State.RECOVER:
			_next_combo()
		rival.open = false
		rival.begin(State.STUN, tuning.stun)
	if launch > 0.0:
		rival.x = minf(rival.x + launch, tuning.arena_half)
		rival.air = tuning.stun
	events.append([&"hit", 1, damage, side, kick])


func _step_rival(dt: float) -> void:
	var f := rival
	match f.state:
		State.IDLE:
			if wait < -0.3:
				f.block = false
			wait -= dt
			# Подходит на дальность удара и держит её.
			var want := tuning.rival_reach - tuning.rival_lunge * 0.5
			if gap() > want:
				f.x = maxf(f.x - tuning.rival_walk * dt, hero.x + tuning.min_gap)
			if wait <= 0.0 and gap() <= tuning.rival_reach + tuning.rival_lunge * 0.5:
				move_index = 0
				_rival_windup()
		State.WINDUP:
			f.timer -= dt
			if f.timer <= 0.0:
				_rival_strikes()
		State.RECOVER, State.STUN:
			f.timer -= dt
			if f.timer <= 0.0:
				if f.state == State.RECOVER and not _combo_over():
					move_index += 1
					_rival_windup()
				else:
					if f.state == State.RECOVER:
						_next_combo()
					f.open = false
					f.begin(State.IDLE, 0.0)


func _combo_over() -> bool:
	return rival.open or move_index >= plan.combo(combo_index).moves.size() - 1


func _next_combo() -> void:
	combo_index += 1
	move_index = 0
	wait = plan.combo(combo_index).gap
	if tired:
		# Выдохся: переводит дух, прежде чем напасть снова.
		tired = false
		tires += 1
		wait += tuning.tire_seconds
		events.append([&"tired"])


func _rival_windup() -> void:
	rival.block = false
	rival.move = rival_move()
	rival.open = false
	rival.begin(State.WINDUP, windup_of(rival.move))
	events.append([&"windup", 1, rival.move])


func _rival_strikes() -> void:
	var f := rival
	var heavy := f.move == SparPlan.Move.HEAVY
	var last := move_index >= plan.combo(combo_index).moves.size() - 1
	# Выпад: шаг к герою вместе с ударом.
	f.x = maxf(f.x - tuning.rival_lunge, hero.x + tuning.min_gap)
	var dodged := hero.state == State.STEP and hero.total - hero.timer <= tuning.step_safe
	if dodged or gap() > tuning.rival_reach:
		# Мимо: связка обрывается, соперник открыт; от шага ещё и сбоку.
		f.open = true
		f.begin(State.RECOVER, tuning.rival_punished)
		if dodged:
			f.flank = tuning.flank_seconds
			dodges += 1
		events.append([&"whiff", 1])
		return
	if hero.state == State.IDLE and hero.block and not heavy:
		blocks += 1
		blocked_streak += 1
		if blocked_streak >= tuning.tire_blocks:
			blocked_streak = 0
			tired = true
		f.open = last
		f.begin(State.RECOVER, tuning.rival_punished if last else tuning.link)
		events.append([&"block", 0])
		return
	var damage := tuning.heavy_damage if heavy else (tuning.rival_kick_damage if f.move == SparPlan.Move.KICK else tuning.rival_damage)
	hero.hp -= damage
	taken += 1
	blocked_streak = 0
	hero.z = 0.0
	hero.open = false
	hero.block = false
	hero.chain = 0
	hero.begin(State.STUN, tuning.stun)
	if launch > 0.0:
		hero.x = maxf(hero.x - launch, -tuning.arena_half)
		hero.air = tuning.stun
	f.open = false
	f.begin(State.RECOVER, tuning.rival_recover if last else tuning.link)
	events.append([&"hit", 0, damage, false, heavy])


## Бот решает на шаг вперёд. WIN: читает замах соперника (с задержкой реакции), удары рукой и
## ногой берёт в блок, от сильного уходит шагом в глубину под самый удар; бьёт только когда
## соперник открыт на время замаха: два удара рукой и нога. LOSE стоит и не защищается.
func bot(mode: AutoTest.BotMode) -> void:
	var c := Controls.new()
	bot_controls = c
	if ended or mode != AutoTest.BotMode.WIN or phase != Phase.FIGHT:
		return
	# Связка идёт: второй удар рукой, потом нога.
	if (hero.state == State.RECOVER or hero.state == State.WINDUP) and hero.chain > 0 and not hero.open:
		c.strike = hero.chain == 1
		c.kick = hero.chain >= 2
		return
	if rival.state == State.WINDUP:
		var seen := rival.total - rival.timer
		if seen < tuning.bot_react:
			return
		if rival.move == SparPlan.Move.HEAVY:
			c.step = 1 if rival.timer <= tuning.bot_step_lead else 0
		else:
			c.block = true
		return
	var need := tuning.hero_windup + 0.03
	var open_for := maxf(rival.flank, rival.timer if rival_open() and rival.state != State.IDLE else 0.0)
	if open_for >= need:
		if gap() <= tuning.hero_reach - 0.05:
			c.strike = true
		else:
			c.move = 1.0
		return
	# В затишье держится на дальности своего удара.
	if gap() > tuning.hero_reach - 0.15:
		c.move = 1.0
