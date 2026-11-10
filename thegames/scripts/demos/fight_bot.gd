class_name FightBot
extends RefCounted
## Бот героя файтинга × 8-bit (#54) для автотеста и стрима ленты. WIN читает состояние
## соперника через `bot_react` шагов: под его верхний приседает, от нижнего отходит, бьёт в
## восстановление (стоящего верхним, присевшего нижним), оглушённого добивает, блок ломает
## нижним, присевшего ждёт `bot_crouch_wait` шагов, стоящего бьёт верхним только с полосы, где
## нижний соперника не достаёт (иначе размен на подсечку). После своего удара выжидает
## `bot_pause_min`..`bot_pause_max` шагов на `bot_gap`; у борта не пятится, бьёт первым.
## LOSE идёт к сопернику и машет верхним издалека, не блокирует: не попадает ни разу.

var sim: FightSim
var mode := AutoTest.BotMode.WIN
var t: FightDemoTuning
var me: FightSim.Fighter
var foe: FightSim.Fighter
## Что бот видел у соперника по шагам: состояние, удар, шаг удара.
var _seen: Array[Vector3i] = []
var _swing := 0
## WIN не бьёт подряд: после своего удара выжидает `bot_pause_min`..`bot_pause_max` шагов
## (защищается и наказывает и в паузе), так что раунд похож на бой, а не на избиение.
var _pause := 0
var rng := RandomNumberGenerator.new()


func _init(sim_: FightSim, mode_: AutoTest.BotMode, seed_: int) -> void:
	sim = sim_
	mode = mode_
	t = sim.t
	me = sim.hero
	foe = sim.rival
	rng.seed = hash(str(seed_, ":fight_bot"))


func think() -> FightSim.Controls:
	var inp := FightSim.Controls.new()
	_seen.append(Vector3i(foe.state, foe.move, foe.t))
	var seen := _seen[0]
	if _seen.size() > t.bot_react:
		seen = _seen.pop_front()
	_pause -= 1
	if not FightSim.actionable(me):
		return inp
	var d := foe.x - me.x
	var toward := 1 if d >= 0.0 else -1
	var dist := absf(d)
	if mode == AutoTest.BotMode.LOSE:
		return _lose(inp, toward, dist)
	var state := seen.x as FightSim.State
	var move := seen.y as FightSim.Move
	# Шаг удара соперника сейчас: увиденный плюс задержка.
	var ft := seen.z + t.bot_react
	if state == FightSim.State.STRIKE:
		var fr := sim.frames(move)
		var low := move == FightSim.Move.LOW
		var threat := ft <= fr.x + fr.y
		if threat and dist <= t.reach(low) + 2.0:
			if low:
				inp.x = -toward
			else:
				inp.down = true
			return inp
		if not threat:
			# Восстановление: успеть ударить, пока он не освободился.
			var left := fr.x + fr.y + fr.z - ft
			var my_low := low
			var startup := t.low_startup if my_low else t.high_startup
			if dist <= t.reach(my_low, true) - 1.0 and left > startup:
				_strike(inp, my_low)
				return inp
			if dist > t.reach(my_low, true) - 1.0 and left > startup + 8:
				inp.x = toward
				return inp
		return inp
	if state == FightSim.State.KO:
		return inp
	# Свои удары героя длиннее (`hero_reach_mult`), нижний соперника обычный.
	var low_reach := t.reach(true)
	var my_low_reach := t.reach(true, true)
	var high_reach := t.reach(false, true)
	var back_room := (me.x - sim.left) if toward > 0 else (sim.right - me.x)
	var ready := _pause <= 0
	match state:
		FightSim.State.HIT:
			# Оглушён: добить верхним, пока не пришёл в себя.
			if dist <= high_reach - 1.0:
				_strike(inp, false)
			else:
				inp.x = toward
			return inp
		FightSim.State.BLOCK, FightSim.State.GUARD:
			# Блок держит только верхний.
			if ready:
				if dist <= my_low_reach - 1.0:
					_strike(inp, true)
				else:
					inp.x = toward
				return inp
		FightSim.State.CROUCH:
			# Присевший ждёт с нижним: бот стоит вне его длины, засиделся: нижний первым.
			if ready and ft > t.bot_crouch_wait:
				if dist <= my_low_reach - 1.0:
					_strike(inp, true)
				else:
					inp.x = toward
				return inp
		_:
			# Стоит или идёт: верхний с полосы, где его нижний не достаёт.
			if ready and dist > low_reach + 0.5 and dist <= high_reach - 1.0:
				_strike(inp, false)
				return inp
	if dist <= low_reach + 0.5:
		if back_room > 24.0:
			inp.x = -toward
		else:
			# У борта не отойти: бить первым.
			_strike(inp, state == FightSim.State.CROUCH or state == FightSim.State.BLOCK or state == FightSim.State.GUARD)
	elif dist > (high_reach - 1.0 if ready and state != FightSim.State.CROUCH else t.bot_gap + 3.0):
		inp.x = toward
	return inp


func _strike(inp: FightSim.Controls, low: bool) -> void:
	inp.a = true
	inp.down = low
	_pause = rng.randi_range(t.bot_pause_min, t.bot_pause_max)


func _lose(inp: FightSim.Controls, toward: int, dist: float) -> FightSim.Controls:
	_swing += 1
	if _swing >= t.bot_lose_every and dist > t.bot_lose_far:
		_swing = 0
		inp.a = true
		return inp
	if dist > t.bot_lose_far - 4.0:
		inp.x = toward
	return inp
