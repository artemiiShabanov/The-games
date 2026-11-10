class_name FightAi
extends RefCounted
## Соперник файтинга × 8-bit (#54): капитан по плану из сида (`FightPlan`). Раунд идёт фазами,
## у фазы профиль поведения (`FightProfile`: напор, стена, подсечка, контра) и паттерн ударов по
## кругу. Пока герой рядом, соперник раз в 20-90 шагов выбирает стойку: блок, присед или
## стоять; её видно, так что человек читает её и выбирает удар (блок бьётся нижним, присед
## ждёт, стоящий верхним). Удары героя соперник видит через `plan.reaction` шагов и с шансом
## `1 − plan.miss` по `punish_chance` бьёт в ответ, пока тот не восстановился. Случайность из
## сида: тот же сид и тот же ввод дают тот же бой.

enum Stance { STAND, BLOCK, CROUCH }

var sim: FightSim
var plan: FightPlan
var gen: FightGenTuning
var t: FightDemoTuning
var me: FightSim.Fighter
var foe: FightSim.Fighter
var rng := RandomNumberGenerator.new()
## Что соперник видел у героя по шагам: состояние, удар, номер удара; читается с задержкой.
var _seen: Array[Vector3i] = []
var _answered := -1
var _phase := -1
var _pattern_i := 0
var _cooldown := 0
var _stance := Stance.STAND
var _stance_left := 0
var _retreat := 0
## Ответ на удар героя: ждёт столько шагов (подходит), потом бьёт; −1 ответа нет.
var _answer_in := -1


func _init(sim_: FightSim, plan_: FightPlan, gen_: FightGenTuning) -> void:
	sim = sim_
	plan = plan_
	gen = gen_
	t = sim.t
	me = sim.rival
	foe = sim.hero
	rng.seed = hash(str(plan.seed, ":fight_ai"))
	_cooldown = rng.randi_range(20, 50)


func profile() -> FightProfile:
	return gen.profiles[plan.phases[maxi(_phase, 0)].profile]


## Название текущего профиля для HUD дебага и заметок.
func profile_title() -> String:
	return profile().title if _phase >= 0 else ""


func think() -> FightSim.Controls:
	var inp := FightSim.Controls.new()
	_seen.append(Vector3i(foe.state, foe.move, foe.move_id))
	var seen := Vector3i(FightSim.State.IDLE, FightSim.Move.NONE, -1)
	if _seen.size() > plan.reaction:
		seen = _seen.pop_front()
	var ph := plan.phase_index(sim.seconds())
	if ph != _phase:
		_phase = ph
		_pattern_i = 0
	var p := profile()
	if not FightSim.actionable(me):
		return inp
	var d := foe.x - me.x
	var toward := 1 if d >= 0.0 else -1
	var dist := absf(d)
	_cooldown -= 1
	# Увидел удар героя: ответить, пока тот не восстановился.
	if seen.x == FightSim.State.STRIKE and seen.z != _answered:
		_answered = seen.z
		_answer_in = -1
		if rng.randf() >= plan.miss and rng.randf() < p.punish_chance:
			_answer_in = 0
	if _answer_in >= 0:
		if foe.state != FightSim.State.STRIKE or foe.move_id != _answered:
			_answer_in = -1
		else:
			var low := FightSim.crouched(foe)
			if dist <= t.reach(low) - 1.0:
				inp.a = true
				inp.down = low
				_answer_in = -1
				return inp
			inp.x = toward
			return inp
	# Отход после своего удара.
	if _retreat > 0:
		_retreat -= 1
		inp.x = -toward
		return inp
	# Свой удар по паттерну фазы.
	var pattern := plan.phases[_phase].pattern
	var low_next := pattern[_pattern_i % pattern.length()] == "L"
	var reach := t.reach(low_next)
	if _cooldown <= 0:
		if dist <= reach - 1.0:
			inp.a = true
			inp.down = low_next
			_pattern_i += 1
			_cooldown = rng.randi_range(p.attack_min, p.attack_max)
			if rng.randf() < p.retreat_chance:
				_retreat = p.retreat_steps
			_stance = Stance.STAND
			_stance_left = 0
			return inp
		inp.x = toward
		return inp
	# Стойка, пока герой близко.
	var near := dist <= t.reach(false) + 10.0
	_stance_left -= 1
	if _stance_left <= 0:
		_stance_left = rng.randi_range(p.stance_min, p.stance_max)
		var roll := rng.randf()
		if not near:
			_stance = Stance.STAND
		elif roll < p.block_chance:
			_stance = Stance.BLOCK
		elif roll < p.block_chance + p.crouch_chance:
			_stance = Stance.CROUCH
		else:
			_stance = Stance.STAND
	if near and _stance == Stance.BLOCK:
		inp.b = true
		return inp
	if near and _stance == Stance.CROUCH:
		inp.down = true
		return inp
	# Держать дистанцию профиля.
	if dist > p.gap + 3.0:
		inp.x = toward
	elif dist < p.gap - 5.0:
		inp.x = -toward
	elif p.crouch_idle:
		inp.down = true
	return inp
