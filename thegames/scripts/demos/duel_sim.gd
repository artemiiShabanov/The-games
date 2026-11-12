class_name DuelSim
extends RefCounted
## Правила демки файтинг × вектор «дуэль на реакцию» (#94) без окна и звука: состояние, шаг,
## боты. Демка `fighting_vector.gd` рисует это состояние и озвучивает события `events`;
## `simulate` гоняет бота по сиду целиком (проверки `demo_test`, `debug/tools/dump_duel.gd`).
## Правила: в раунде бойцы замирают, после паузы случайной длины вспыхивает сигнал. Кто первым
## ударил после вспышки, взял раунд; соперник бьёт через свою задержку из `DuelPlan`, от
## раунда к раунду всё раньше. Удар до вспышки это фальстарт и проигранный раунд. Раундов
## пять, дуэль кончается раньше, если отставшему уже не догнать; победа у того, кто взял
## больше.
## Баги жанра и баланса приходят числами и флагами: `pass_every` каждый такой удар героя
## проходит мимо, и раунд забирает соперник (мимо хитбокса); `rival_mult` множитель задержки
## соперника (невесомость: враги быстрее); `immortal` удар героя попадает, но раунд не
## засчитан никому (бессмертный соперник); `frail` соперник падает от любого удара после
## вспышки, даже если ударил первым: у героя есть `late_window` на ответ (нокаут от чиха).

enum State { READY, WAIT, SIGNAL, STRIKE, RESULT }
enum Outcome { NONE, HERO, RIVAL, DRAW }
## Как кончился раунд: чистый удар, фальстарт, удар героя мимо, удар в бессмертного, ответ
## после удара соперника.
enum How { CLEAN, FALSE_START, GHOST, IMMORTAL, LATE }

var tuning: FightingVectorTuning
var plan: DuelPlan
var pass_every := 0
var rival_mult := 1.0
var immortal := false
var frail := false

var state := State.READY
## Номер раунда с нуля и время в текущем состоянии.
var round_i := 0
var t := 0.0
## Секунды с момента вспышки.
var since_signal := 0.0
var outcome := Outcome.NONE
var how := How.CLEAN
var hero_wins := 0
var rival_wins := 0
var draws := 0
var false_starts := 0
## Реакция героя на вспышку в последнем раунде и лучшая за дуэль, секунды; INF, если не бил.
var last_reaction := INF
var best_reaction := INF
var time := 0.0
var ended := false
var won := false
## События шага для звука и эффектов: `[имя, …]`. `ready` (раунд), `wait`, `signal`,
## `false_start`, `strike` (0 герой, 1 соперник; попал ли; `How`), `round` (`Outcome`), `win`,
## `lose`. Демка читает и чистит.
var events: Array[Array] = []

var _hero_strikes := 0
## Герой уже ударил в этом раунде и промахнулся; соперник уже ударил и ждёт ответа (чих).
var _hero_missed := false
var _rival_struck := false
var _bot_done := false


static func create(plan_: DuelPlan, tuning_: FightingVectorTuning) -> DuelSim:
	var s := DuelSim.new()
	s.plan = plan_
	s.tuning = tuning_
	s.events.append([&"ready", 0])
	return s


## Прогон бота без окна до конца или до `max_seconds`.
static func simulate(plan_: DuelPlan, tuning_: FightingVectorTuning, mode: AutoTest.BotMode,
		max_seconds := 120.0, setup := Callable()) -> DuelSim:
	var s := create(plan_, tuning_)
	if setup.is_valid():
		setup.call(s)
	var dt := 1.0 / 60.0
	while not s.ended and s.time < max_seconds:
		s.step(dt, s.bot(mode))
		s.events.clear()
	return s


## Задержка соперника в текущем раунде.
func rival_delay() -> float:
	return plan.delays[mini(round_i, plan.rounds() - 1)] * rival_mult


## Шаг мира: `pressed` нажат ли удар на этом шаге.
func step(dt: float, pressed: bool) -> void:
	if ended:
		return
	time += dt
	t += dt
	match state:
		State.READY:
			if t >= tuning.ready_seconds:
				_enter(State.WAIT)
				events.append([&"wait"])
		State.WAIT:
			if pressed:
				# Фальстарт: раунд сопернику.
				false_starts += 1
				last_reaction = INF
				events.append([&"false_start"])
				_finish(Outcome.RIVAL, How.FALSE_START)
				events.append([&"strike", 1, true, How.FALSE_START])
			elif t >= plan.waits[round_i]:
				_enter(State.SIGNAL)
				since_signal = 0.0
				last_reaction = INF
				events.append([&"signal"])
		State.SIGNAL:
			since_signal += dt
			if pressed and not _hero_missed:
				_hero_strike()
			elif since_signal >= rival_delay() and not _rival_struck:
				if frail and not _hero_missed:
					# Чих: соперник ударил первым, но падает и от запоздалого ответа.
					_rival_struck = true
					events.append([&"strike", 1, false, How.LATE])
				else:
					_finish(Outcome.RIVAL, How.GHOST if _hero_missed else How.CLEAN)
					events.append([&"strike", 1, true, how])
			elif _rival_struck and since_signal >= rival_delay() + tuning.late_window:
				_finish(Outcome.RIVAL, How.CLEAN)
		State.STRIKE:
			if t >= tuning.strike_seconds:
				match outcome:
					Outcome.HERO:
						hero_wins += 1
					Outcome.RIVAL:
						rival_wins += 1
					Outcome.DRAW:
						draws += 1
				events.append([&"round", outcome])
				_enter(State.RESULT)
		State.RESULT:
			if t >= tuning.result_seconds:
				_next_round()


func _hero_strike() -> void:
	last_reaction = since_signal
	best_reaction = minf(best_reaction, since_signal)
	_hero_strikes += 1
	if pass_every > 0 and _hero_strikes % pass_every == 0:
		# Мимо хитбокса: удар прошёл сквозь, соперник ещё ударит в ответ.
		_hero_missed = true
		events.append([&"strike", 0, false, How.GHOST])
	elif immortal:
		_finish(Outcome.DRAW, How.IMMORTAL)
		events.append([&"strike", 0, false, How.IMMORTAL])
	else:
		_finish(Outcome.HERO, How.LATE if _rival_struck else How.CLEAN)
		events.append([&"strike", 0, true, how])


func _finish(result: Outcome, how_: How) -> void:
	outcome = result
	how = how_
	_enter(State.STRIKE)


func _enter(next: State) -> void:
	state = next
	t = 0.0


func _next_round() -> void:
	round_i += 1
	var left := plan.rounds() - round_i
	if left <= 0 or hero_wins > rival_wins + left or rival_wins > hero_wins + left:
		ended = true
		won = hero_wins > rival_wins
		round_i = mini(round_i, plan.rounds() - 1)
		events.append([&"win" if won else &"lose"])
		return
	outcome = Outcome.NONE
	how = How.CLEAN
	_hero_missed = false
	_rival_struck = false
	_bot_done = false
	_enter(State.READY)
	events.append([&"ready", round_i])


# --- Боты ------------------------------------------------------------------------------------

## Бот: возвращает, жмёт ли удар на этом шаге. WIN бьёт через `bot_reaction` после вспышки;
## LOSE жмёт раньше вспышки и проигрывает раунды фальстартом.
func bot(mode: AutoTest.BotMode) -> bool:
	if ended or _bot_done:
		return false
	if mode == AutoTest.BotMode.WIN:
		if state == State.SIGNAL and since_signal >= tuning.bot_reaction:
			_bot_done = true
			return true
	elif state == State.WAIT and t >= minf(tuning.bot_lose_press, plan.waits[round_i] * 0.5):
		_bot_done = true
		return true
	return false
