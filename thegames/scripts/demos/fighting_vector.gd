extends Demo
## Демка файтинг × вектор, каталог `docs/specs/demos_catalog.md`: дуэль на реакцию (#94). Два
## бойца контурами стоят друг против друга, после паузы случайной длины между ними вспыхивает
## звезда лучами и загорается рамка экрана (плейтест 2026-11-12: сигнал там, куда смотришь, а
## не знак наверху). Кто первым нажал A после вспышки, тот бьёт: рывок через противника, и
## проигравший рассыпается на отрезки. Нажал до вспышки: фальстарт, раунд сопернику. Раундов пять, побеждает взявший
## больше; дуэль кончается раньше, когда отставшему уже не догнать. Соперник от раунда к раунду
## бьёт всё раньше.
## План из `DuelPlanGen` по сиду записи: пауза и задержка соперника в каждом раунде. Правила и
## боты живут в `DuelSim` (без окна, им же проверяются сто сидов); демка ведёт его шагами,
## рисует и озвучивает его события. Рисуется на `VectorScreen` в логических пикселях карточки:
## земля, светило, бойцы и реквизит контурами слотов сеттинга, вспышка лучами, счёт раундов
## клетками.
##
## Баги по флагам записи (параметры в `resources/bugs/<id>.tres`). Общие (#44) и баг технологии
## `beam_lag` живут в `Demo` и `VectorScreen`, демка только зовёт хуки: фризы `bug_frame` (в
## ожидании вспышки), заикание пищалки и сигнал с опозданием, удар с опозданием, залипший удар
## (повторяется в начале следующего раунда и даёт фальстарт), розовые заглушки вместо соперника
## или реквизита. Свои проявления: `ghost_hits` (баг жанра) каждый второй удар героя проходит
## мимо, раунд забирает соперник; `wild_physics` невесомость: проигравший не рассыпается, а
## улетает по дуге, соперник быстрее; `unreachable_coins` бессмертный соперник: удар попадает,
## но раунд не засчитан никому; `sneeze_enemies` соперник падает от любого удара после вспышки,
## даже если ударил первым.

const GROUND_Y := 620.0
const HERO_X := 560.0
const RIVAL_X := 1104.0
## Логических пикселей на пиксель спрайта: бойцы 160 в высоту.
const PX := 10.0
const PROP_PX := 6.0
const INK_WORLD := 1
const INK_HERO := 2
const INK_DANGER := 3
const DASH := 240.0
## Вспышка-сигнал между бойцами: лучей, их длина (длинный и короткий) и за сколько секунд она
## раскрывается.
const BURST_RAYS := 16
const BURST_LONG := 170.0
const BURST_SHORT := 96.0
const BURST_OPEN := 0.07
const WHIFF_SECONDS := 0.3
const PLACEHOLDER_SLOTS: Array[String] = ["enemy", "prop_a", "prop_b"]
const MELODY := [0, null, null, null, null, null, 3, null, null, null, null, null, -2, null, null, null,
	0, null, null, null, null, null, 5, null, null, null, 3, null, -2, null, null, null]

var tuning: FightingVectorTuning
var plan: DuelPlan
var sim: DuelSim

var _time := 0.0
## Нажатие удара, которое уйдёт в правила на следующем шаге.
var _pressed := false
## Кто рассыпался или улетел в этом раунде: герой, соперник.
var _gone := [false, false]
## Невесомость: проигравший летит по дуге; сторона (0 герой, 1 соперник, −1 никто) и время полёта.
var _floaty := false
var _fly_side := -1
var _fly_t := 0.0
## Выпад впустую: герой мимо хитбокса, соперник с чихом; остаток секунд.
var _whiff := [0.0, 0.0]
## Залипший удар: проверен ли в этом раунде.
var _stick_checked := false
## Чернила клеток сыгранных раундов по порядку: герой, соперник или ничья.
var _round_marks: Array[int] = []
var _music: AudioStreamPlayer
var _sfx := {}


func _on_start() -> void:
	tuning = FightingVectorTuning.load_default()
	plan = DuelPlanGen.generate(record.seed if record != null else 1)
	sim = DuelSim.create(plan, tuning)
	# Баги жанра и баланса; общие баги в `Demo` (#44).
	if has_bug(&"ghost_hits"):
		sim.pass_every = maxi(int(bug_param(&"ghost_hits", &"pass_every", 2.0)), 1)
	if has_bug(&"wild_physics"):
		sim.rival_mult = bug_param(&"wild_physics", &"duel_rival_mult", 0.75)
		_floaty = true
	sim.immortal = has_bug(&"unreachable_coins")
	sim.frail = has_bug(&"sneeze_enemies")
	vector_screen(_draw_vector)
	_setup_audio()
	sim.events.clear()


func _setup_audio() -> void:
	_music = Sfx.music(Sfx.beeper_loop(MELODY, 120.0), tuning.music_db if not embedded else -80.0)
	add_child(_music)
	bug_music = _music
	if not embedded:
		_music.play()
	_sfx["ready"] = Sfx.player(Sfx.beep(196.0, 0.12, 0.22))
	_sfx["signal"] = Sfx.player(Sfx.beep(1568.0, 0.18, 0.35))
	_sfx["strike"] = Sfx.player(Sfx.beep(1200.0, 0.16, 0.3, 200.0))
	_sfx["whiff"] = Sfx.player(Sfx.beep(600.0, 0.14, 0.2, 300.0))
	_sfx["foul"] = Sfx.player(Sfx.beep(140.0, 0.35, 0.3, 100.0))
	_sfx["won"] = Sfx.player(Sfx.beep(660.0, 0.2, 0.28, 990.0))
	_sfx["lost"] = Sfx.player(Sfx.beep(330.0, 0.3, 0.28, 110.0))
	_sfx["finish"] = Sfx.player(Sfx.beep(660.0, 0.5, 0.3, 1320.0))
	for p in _sfx.values():
		(p as AudioStreamPlayer).volume_db = tuning.sfx_db if not embedded else -80.0
		add_child(p)


func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _play(name: String) -> void:
	bug_play(_sfx[name])


func _on_end(goal: bool) -> void:
	_music.stop()
	if goal:
		_play("finish")
	if AutoTest.enabled and not embedded:
		AutoTest.note("fighting vector: %s %d:%d, ничьих %d, фальстартов %d, лучшая реакция %s, за %.1f с" % [
				_result_title(goal), sim.hero_wins, sim.rival_wins, sim.draws, sim.false_starts, _reaction_text(), elapsed])


func _result_title(goal: bool) -> String:
	if goal:
		return "победа"
	return "ничья" if sim != null and sim.hero_wins == sim.rival_wins else "поражение"


func _result_caption() -> String:
	return "раунды %d:%d · лучшая реакция %s" % [sim.hero_wins, sim.rival_wins, _reaction_text()]


func _reaction_text() -> String:
	return "%.2f с" % sim.best_reaction if sim.best_reaction < INF else "нет"


# --- Ввод и шаг ------------------------------------------------------------------------------

func _game_input(event: InputEvent) -> void:
	if GameInput.is_a(event):
		# С багом управления нажатие уходит в очередь с задержкой (`Demo.bug_press`).
		bug_press(_press)
		get_viewport().set_input_as_handled()


func _press() -> void:
	_pressed = true


func _bot_step(_delta: float) -> void:
	if sim.bot(active_bot_mode()):
		_pressed = true


func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	# Фризы в ожидании вспышки и сразу после неё (`Demo.bug_frame`).
	bug_frame(delta, sim.state == DuelSim.State.WAIT or sim.state == DuelSim.State.SIGNAL, _step)


func _step(dt: float) -> void:
	_time += dt
	for i in 2:
		_whiff[i] = maxf(float(_whiff[i]) - dt, 0.0)
	if _fly_side >= 0:
		_fly_t += dt
	step_shards(dt)
	bug_input_tick()
	# Залипание: удар из прошлого раунда повторяется в начале паузы, это фальстарт.
	if sim.state == DuelSim.State.WAIT and not _stick_checked and sim.t >= 0.5:
		_stick_checked = true
		if bug_take_stick():
			_pressed = true
	sim.step(dt, _pressed)
	_pressed = false
	for ev in sim.events:
		_on_event(ev)
	sim.events.clear()
	# Рывок дошёл до противника: проигравший раунд выбывает.
	if (sim.state == DuelSim.State.STRIKE and _dash_k() > 0.6) or sim.state == DuelSim.State.RESULT:
		if sim.outcome == DuelSim.Outcome.HERO:
			_knock(1)
		elif sim.outcome == DuelSim.Outcome.RIVAL:
			_knock(0)


## Событие правил: звук, эффект, конец демки.
func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"ready":
			_gone = [false, false]
			_fly_side = -1
			_stick_checked = false
			_play("ready")
		&"signal":
			_play("signal")
		&"false_start":
			bug_clear_stick()
			_play("foul")
		&"strike":
			var who := int(ev[1])
			if bool(ev[2]):
				_play("strike")
				if who == 0:
					bug_stick()
			else:
				# Удар не засчитан: выпад впустую (мимо хитбокса, чих) или в бессмертного.
				if int(ev[3]) != DuelSim.How.IMMORTAL:
					_whiff[who] = WHIFF_SECONDS
				_play("whiff")
		&"round":
			match int(ev[1]):
				DuelSim.Outcome.HERO:
					_round_marks.append(INK_HERO)
					_play("won")
				DuelSim.Outcome.RIVAL:
					_round_marks.append(INK_DANGER)
					_play("lost")
				_:
					_round_marks.append(INK_WORLD)
		&"win":
			end_demo(true)
		&"lose":
			end_demo(false)


## Проигравший раунд выбывает: рассыпается на отрезки, а в невесомости улетает по дуге.
func _knock(side: int) -> void:
	if bool(_gone[side]):
		return
	_gone[side] = true
	if _floaty:
		_fly_side = side
		_fly_t = 0.0
		return
	var slot := &"hero" if side == 0 else &"enemy"
	if is_pink(String(slot)):
		return
	shatter_slot(slot, Vector2(HERO_X if side == 0 else RIVAL_X, GROUND_Y - 8.0 * PX), PX, INK_HERO if side == 0 else INK_DANGER)


# --- Рисование -------------------------------------------------------------------------------

## Доля рывка 0..1 в ударе: быстрый старт, плавная остановка.
func _dash_k() -> float:
	var k := clampf(sim.t / (tuning.strike_seconds * 0.45), 0.0, 1.0)
	return 1.0 - (1.0 - k) * (1.0 - k)


func _draw_vector(v: VectorScreen) -> void:
	if sim == null:
		return
	var size := v.logical_size
	var mid := size.x / 2.0
	# Земля со штрихами, светило за бойцами, реквизит по краям.
	v.line(Vector2(0.0, GROUND_Y), Vector2(size.x, GROUND_Y), INK_WORLD, 3.0)
	var gx := 30.0
	while gx < size.x:
		v.line(Vector2(gx, GROUND_Y + 10.0), Vector2(gx - 16.0, GROUND_Y + 30.0), INK_WORLD, 2.0, 0.35)
		gx += 72.0
	var sun := PackedVector2Array()
	for i in 24:
		var a := PI + PI * i / 23.0
		sun.append(Vector2(mid, GROUND_Y) + Vector2.from_angle(a) * 210.0)
	v.poly(sun, INK_WORLD, false, 2.0, 0.4)
	draw_slot(&"prop_a", Vector2(190.0, GROUND_Y - 8.0 * PROP_PX), PROP_PX)
	draw_slot(&"prop_b", Vector2(size.x - 190.0, GROUND_Y - 8.0 * PROP_PX), PROP_PX)
	# Где бойцы: в ударе победитель рывком уходит за противника и остаётся там до конца раунда.
	var hero_x := HERO_X
	var rival_x := RIVAL_X
	var struck := sim.state == DuelSim.State.STRIKE or sim.state == DuelSim.State.RESULT
	var k := _dash_k() if sim.state == DuelSim.State.STRIKE else 1.0
	if struck:
		match sim.outcome:
			DuelSim.Outcome.HERO, DuelSim.Outcome.DRAW:
				hero_x = lerpf(HERO_X, RIVAL_X + DASH, k)
			DuelSim.Outcome.RIVAL:
				rival_x = lerpf(RIVAL_X, HERO_X - DASH, k)
	hero_x += sin(PI * (1.0 - float(_whiff[0]) / WHIFF_SECONDS)) * 150.0 if float(_whiff[0]) > 0.0 else 0.0
	rival_x -= sin(PI * (1.0 - float(_whiff[1]) / WHIFF_SECONDS)) * 150.0 if float(_whiff[1]) > 0.0 else 0.0
	var y := GROUND_Y - 8.0 * PX
	# Росчерк удара: линия от места рывка до бойца; у удара мимо хитбокса он за спиной героя.
	if sim.state == DuelSim.State.STRIKE and sim.outcome != DuelSim.Outcome.NONE:
		var fade := 1.0 - clampf(sim.t / tuning.strike_seconds, 0.0, 1.0)
		if sim.outcome == DuelSim.Outcome.RIVAL:
			v.line(Vector2(RIVAL_X, y - 30.0), Vector2(rival_x, y + 10.0), INK_DANGER, 4.0, fade)
		else:
			v.line(Vector2(HERO_X, y - 30.0), Vector2(hero_x, y + 10.0), INK_HERO, 4.0, fade)
			if sim.outcome == DuelSim.Outcome.DRAW:
				# Бессмертный: искры от удара, а он стоит.
				for i in 6:
					var d := Vector2.from_angle(-PI / 2.0 + (i - 2.5) * 0.5)
					v.line(Vector2(RIVAL_X, y) + d * 40.0, Vector2(RIVAL_X, y) + d * (70.0 + 40.0 * fade), INK_WORLD, 2.5, fade)
	if float(_whiff[0]) > 0.0:
		v.line(Vector2(HERO_X - 190.0, y - 40.0), Vector2(HERO_X - 60.0, y + 20.0), INK_HERO, 3.0, float(_whiff[0]) / WHIFF_SECONDS)
	# Бойцы: в ожидании чуть дышат; выбывший рассыпался или летит по дуге.
	var breath := sin(_time * 3.0) * 2.0 if sim.state == DuelSim.State.WAIT else 0.0
	var enter := clampf(sim.t / 0.4, 0.0, 1.0) if sim.state == DuelSim.State.READY else 1.0
	if not bool(_gone[0]):
		draw_slot(&"hero", Vector2(lerpf(hero_x - 80.0, hero_x, enter), y + breath), PX, hero_x > rival_x)
	if not bool(_gone[1]):
		draw_slot(&"enemy", Vector2(lerpf(rival_x + 80.0, rival_x, enter), y - breath), PX, rival_x < hero_x)
	if _fly_side >= 0:
		var dir := -1.0 if _fly_side == 0 else 1.0
		var from := Vector2(HERO_X if _fly_side == 0 else RIVAL_X, y)
		var at := from + Vector2(dir * 420.0 * _fly_t, -760.0 * _fly_t + 520.0 * _fly_t * _fly_t)
		if at.y < size.y + 120.0 and at.x > -120.0 and at.x < size.x + 120.0:
			draw_slot(&"hero" if _fly_side == 0 else &"enemy", at, PX, false, _fly_t * 7.0 * dir)
	draw_shards()
	# Сигнал: звезда лучами между бойцами на уровне глаз и рамка экрана; в ударе гаснет. На
	# фальстарте там же красный крест.
	var eye := Vector2(mid, y - 16.0)
	if sim.state == DuelSim.State.SIGNAL or (sim.state == DuelSim.State.STRIKE and sim.how != DuelSim.How.FALSE_START):
		var open := clampf(sim.since_signal / BURST_OPEN, 0.3, 1.0)
		var glow := 1.0 - clampf(sim.t / tuning.strike_seconds, 0.0, 1.0) if sim.state == DuelSim.State.STRIKE else 1.0
		var pulse := 1.0 + 0.1 * sin(_time * 34.0)
		for i in BURST_RAYS:
			var d := Vector2.from_angle(TAU * i / BURST_RAYS)
			var reach := (BURST_LONG if i % 2 == 0 else BURST_SHORT) * open * pulse
			v.line(eye + d * 30.0 * open, eye + d * reach, INK_HERO, 5.0 if i % 2 == 0 else 3.0, glow)
		v.poly(PackedVector2Array([eye + Vector2(0, -22), eye + Vector2(22, 0), eye + Vector2(0, 22), eye + Vector2(-22, 0)]),
				INK_HERO, true, 4.0, glow)
		_draw_frame(v, size, INK_HERO, glow * (0.75 + 0.25 * sin(_time * 34.0)))
	elif struck and sim.how == DuelSim.How.FALSE_START:
		var fade := 1.0 - 0.6 * clampf(sim.t / tuning.strike_seconds, 0.0, 1.0) if sim.state == DuelSim.State.STRIKE else 0.4
		v.line(eye + Vector2(-90, -90), eye + Vector2(90, 90), INK_DANGER, 6.0, fade)
		v.line(eye + Vector2(90, -90), eye + Vector2(-90, 90), INK_DANGER, 6.0, fade)
		if sim.state == DuelSim.State.STRIKE:
			_draw_frame(v, size, INK_DANGER, fade)
	# Реакция героя в сотых секунды под ним, пока раунд не сменился.
	if struck and sim.last_reaction < INF:
		var ms := "%d" % int(round(sim.last_reaction * 100.0))
		v.digits(Vector2(HERO_X - VectorScreen.digits_width(ms, 40.0) / 2.0, GROUND_Y + 56.0), ms, 40.0, INK_HERO)
	# Счёт раундов сверху: клетка на раунд, чей он, тем цветом и крест.
	var n := plan.rounds()
	var done := sim.hero_wins + sim.rival_wins + sim.draws
	for i in n:
		var c := Vector2(mid + (i - (n - 1) / 2.0) * 64.0, 52.0)
		var box := PackedVector2Array([c + Vector2(-20, -20), c + Vector2(20, -20), c + Vector2(20, 20), c + Vector2(-20, 20)])
		var ink_i := INK_WORLD
		if i < _round_marks.size():
			ink_i = int(_round_marks[i])
		v.poly(box, ink_i, true, 2.5, 1.0 if i <= done else 0.4)
		if i < _round_marks.size() and ink_i != INK_WORLD:
			v.line(box[0], box[2], ink_i, 2.5)
			v.line(box[1], box[3], ink_i, 2.5)


## Рамка по краю экрана: загорается вместе с сигналом.
func _draw_frame(v: VectorScreen, size: Vector2, ink_i: int, alpha: float) -> void:
	var m := 10.0
	v.poly(PackedVector2Array([Vector2(m, m), Vector2(size.x - m, m), Vector2(size.x - m, size.y - m), Vector2(m, size.y - m)]),
			ink_i, true, 6.0, alpha)
