extends Minigame
## «Бей» (mole, шутер), каталог `docs/specs/minigames_catalog.md`. Четыре лунки по сторонам от
## центра (вверх, вправо, вниз, влево). Кружки выскакивают из лунок и через `up` секунд прячутся;
## стрелка в сторону лунки с кружком бьёт его, пока он снаружи. Кружок спрятался небитым:
## упущен. 5 упущенных провал, иначе успех по таймеру (20 с).
## Стрелка в пустую лунку: промах без штрафа к счёту, но молоток в центре на `STUN_SECONDS`
## сереет и не бьёт (иначе выигрывает долбёжка всеми четырьмя стрелками). Стрелка в лунку, где
## кружок уже прячется (после удара или упущенный), ничего не делает.
## Параметры от `t` в `resources/minigames/mole.tres`: interval (темп: пауза между выскоками),
## up (сколько кружок снаружи), pair (вероятность, что выскочат два сразу).
## Мармелад (STYLE «Мармелад»): кружки мягкие `JellyShape`, выскакивают со вздрагом,
## снаружи стоят на бортике, перед тем как спрятаться, оседают; удар брызгает неяркими каплями
## цвета кружка и расходится кругом, кружок сплющивается обратно в лунку. Упущенный сереет в
## `ink-3` и тонет. Молоток в центре делает выпад в сторону стрелки; промах трясёт его серым.

enum State { EMPTY, UP, HIT, MISSED }

## Направления лунок и стрелки к ним, по часовой от верхней.
const DIRS: Array[Vector2] = [Vector2.UP, Vector2.RIGHT, Vector2.DOWN, Vector2.LEFT]
const KEYS: Array[StringName] = [GameInput.UP, GameInput.RIGHT, GameInput.DOWN, GameInput.LEFT]
const HOLES := 4
const MAX_MISSED := 5
## Первый выскок после старта, с.
const FIRST_POP := 0.6
## После пары следующий выскок позже во столько раз.
const PAIR_GAP := 1.4
## Разброс паузы между выскоками, ±доля.
const JITTER := 0.15
## Без новых выскоков в последние секунды: такой кружок уже не успеть ни ударить, ни упустить.
const QUIET_TAIL := 0.35
## Анимации: выскок, удар (сплющивается в лунку), упущенный (сереет и тонет), оседание перед
## тем как спрятаться, с.
const RISE_SECONDS := 0.14
const HIT_SECONDS := 0.16
const MISS_SECONDS := 0.3
const SINK_SECONDS := 0.25
const SINK_SCALE := 0.86
## Промах в пустую лунку: молоток не бьёт столько, с.
const STUN_SECONDS := 0.3
const JAB_SECONDS := 0.14
const SHAKE_SECONDS := 0.3
const HOLE_R := 84.0
const PIT_R := 72.0
const MOLE_R := 64.0
const HAMMER_R := 46.0
const LIFT := 8.0
const SLOT_R := 12.0
const SLOT_GAP := 40.0
const COUNT_SIZE := 40
## Бот WIN: реакция на выскок, второй кружок пары позже на столько, с.
const BOT_REACTION := 0.35
const BOT_SECOND := 0.14

var interval := 1.0
var up_seconds := 1.2
var pair_chance := 0.0

var state: Array[State] = []
## Время в текущем состоянии лунки, с.
var state_time: Array[float] = []
var next_pop := FIRST_POP
var hits := 0
var missed := 0
var whiffs := 0
var pops := 0
var pairs := 0
var stun := 0.0

var _pop_sound: AudioStreamPlayer
var _hit_sound: AudioStreamPlayer
var _miss_sound: AudioStreamPlayer
var _whiff_sound: AudioStreamPlayer

## Бот: когда реагировать на кружок лунки (от выскока) и отреагировал ли уже.
var _bot_at: Array[float] = []
var _bot_done: Array[bool] = []

# Мармелад: только рисование, на игру не влияет.
var _moles: Array[JellyShape] = []
var _hammer: JellyShape
var _jab_dir := Vector2.ZERO
var _jab := 0.0
var _shake := 0.0
var _slots: Array[JellySpring] = []
var _rings := RingFx.new()
var _splash := SplashFx.new()


func _on_start() -> void:
	interval = def.param(&"interval", t, 1.0)
	up_seconds = def.param(&"up", t, 1.2)
	pair_chance = def.param(&"pair", t, 0.0)
	_pop_sound = Sfx.player(Sfx.blip(440.0, 0.06, 0.25, 40.0))
	_hit_sound = Sfx.player(Sfx.blip(784.0, 0.12, 0.5, 16.0))
	_miss_sound = Sfx.player(Sfx.thud())
	_whiff_sound = Sfx.player(Sfx.thud(0.08, 0.25))
	for p in [_pop_sound, _hit_sound, _miss_sound, _whiff_sound]:
		add_child(p)
	for i in HOLES:
		state.append(State.EMPTY)
		state_time.append(0.0)
		_bot_at.append(0.0)
		_bot_done.append(true)
		_moles.append(JellyShape.circle(MOLE_R, 36))
	for i in MAX_MISSED:
		_slots.append(JellySpring.new())
	_hammer = JellyShape.circle(HAMMER_R, 32)
	queue_redraw()


func _set_state(i: int, s: State) -> void:
	state[i] = s
	state_time[i] = 0.0


## Снаружи ли кружок лунки `i`: по нему можно бить.
func is_up(i: int) -> bool:
	return state[i] == State.UP


func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	var action := GameInput.action_of(event)
	var i := KEYS.find(action)
	if i < 0 or not event.is_action_pressed(action):
		return
	_press(i)
	get_viewport().set_input_as_handled()


func _press(i: int) -> void:
	if stun > 0.0:
		return
	_jab_dir = DIRS[i]
	_jab = JAB_SECONDS
	match state[i]:
		State.UP:
			hits += 1
			_set_state(i, State.HIT)
			_hit_sound.play()
			_jelly_hit(i)
		State.EMPTY:
			whiffs += 1
			stun = STUN_SECONDS
			_shake = SHAKE_SECONDS
			_whiff_sound.play()
			if Jelly.on():
				_hammer.push(DIRS[i] * -220.0, DIRS[i])


func _on_tick(delta: float) -> void:
	stun = maxf(stun - delta, 0.0)
	_jab = maxf(_jab - delta, 0.0)
	_shake = maxf(_shake - delta, 0.0)
	for i in HOLES:
		state_time[i] += delta
		match state[i]:
			State.UP:
				if state_time[i] >= up_seconds:
					_miss(i)
			State.HIT:
				if state_time[i] >= HIT_SECONDS:
					_set_state(i, State.EMPTY)
			State.MISSED:
				if state_time[i] >= MISS_SECONDS:
					_set_state(i, State.EMPTY)
	if not running:
		return
	next_pop -= delta
	if next_pop <= 0.0:
		_pop()
	queue_redraw()


func _miss(i: int) -> void:
	if not running:
		return
	missed += 1
	_set_state(i, State.MISSED)
	_miss_sound.play()
	_slots[missed - 1].kick(14.0)
	if missed >= MAX_MISSED:
		finish(false)


## Выскок: один кружок или с вероятностью `pair` два сразу, в свободные лунки.
func _pop() -> void:
	if time_left <= QUIET_TAIL:
		next_pop = INF
		return
	var free: Array[int] = []
	for i in HOLES:
		if state[i] == State.EMPTY:
			free.append(i)
	if free.is_empty():
		next_pop = 0.05
		return
	var n := 2 if free.size() >= 2 and rng.randf() < pair_chance else 1
	for k in n:
		var i: int = free.pop_at(rng.randi_range(0, free.size() - 1))
		_set_state(i, State.UP)
		_bot_at[i] = BOT_REACTION + k * BOT_SECOND
		_bot_done[i] = false
		_jelly_pop(i)
	pops += n
	if n == 2:
		pairs += 1
	_pop_sound.play()
	next_pop = interval * (PAIR_GAP if n == 2 else 1.0) * rng.randf_range(1.0 - JITTER, 1.0 + JITTER)


func _on_timeout() -> bool:
	return missed < MAX_MISSED


func _on_finish(success: bool) -> void:
	# Кружки, что ещё снаружи, прячутся без счёта (сплющиваются в лунку).
	for i in HOLES:
		if state[i] == State.UP:
			_set_state(i, State.HIT)
	if AutoTest.enabled:
		AutoTest.note("mole: t %.2f, %s, выскоков %d (пар %d), попаданий %d, упущено %d, мимо %d, %.1f с" % [t, "успех" if success else "провал", pops, pairs, hits, missed, whiffs, elapsed])


## Бот: WIN бьёт кружок через `BOT_REACTION` после выскока (второй кружок пары позже на
## `BOT_SECOND`). LOSE в то же время бьёт в пустую лунку (промах, молоток сереет), кружки не
## трогает: пять упущенных.
func _bot_step(_delta: float) -> bool:
	for i in HOLES:
		if _bot_done[i] or not is_up(i) or state_time[i] < _bot_at[i]:
			continue
		_bot_done[i] = true
		if AutoTest.bot_mode == AutoTest.BotMode.WIN:
			_press(i)
		else:
			for k in HOLES:
				if state[k] == State.EMPTY:
					_press(k)
					break
	return false


# --- Мармелад -----------------------------------------------------------------------------

func _jelly_pop(i: int) -> void:
	if not Jelly.on():
		return
	_moles[i].snap(_hole_pos(i))
	_moles[i].poke(160.0)
	_moles[i].push(DIRS[i] * 90.0, DIRS[i])


func _jelly_hit(i: int) -> void:
	if not Jelly.on():
		return
	var col := Style.accent(0)
	_moles[i].poke(-260.0)
	_hammer.poke(200.0)
	_splash.pop(_hole_pos(i) - Vector2(0.0, MOLE_R * 0.6), col, 4, 420.0, 0.55)
	_rings.add(_hole_pos(i), MOLE_R, MOLE_R + 40.0, Color(col, 0.45), 1, 0.45)


## Масштаб кружка лунки `i` сейчас: выскок с перелётом, оседание перед концом окна, удар
## сплющивает в лунку, упущенный тонет.
func _mole_scale(i: int) -> float:
	var st := state_time[i]
	match state[i]:
		State.UP:
			if st < RISE_SECONDS:
				# ease-out без перелёта: перелёт даёт вздрог мармелада.
				var x := 1.0 - st / RISE_SECONDS
				return maxf(1.0 - x * x * x, 0.05)
			var left := up_seconds - st
			if left < SINK_SECONDS:
				return lerpf(SINK_SCALE, 1.0, left / SINK_SECONDS)
			return 1.0
		State.HIT:
			return maxf(1.0 - st / HIT_SECONDS, 0.0)
		State.MISSED:
			return SINK_SCALE * maxf(1.0 - st / MISS_SECONDS, 0.0)
	return 0.0


## Мармелад живёт и после финиша, пока сцена на экране; на паузе стоит.
func _process(delta: float) -> void:
	super(delta)
	if _moles.is_empty() or paused or def == null:
		return
	var tu := Jelly.tuning()
	if not running:
		# После финиша `_on_tick` не идёт: анимации удара и упущенного доигрываются здесь.
		for i in HOLES:
			if state[i] != State.UP:
				state_time[i] += delta
	for i in HOLES:
		_moles[i].follow(delta, _hole_pos(i), 0.0, maxf(_mole_scale(i), 0.05))
	_hammer.follow(delta, _hammer_pos(), 0.0, 1.0)
	for s in _slots:
		s.step(delta, tu.spring_stiffness, tu.spring_damping)
	_rings.step(delta)
	_splash.step(delta, Callable())
	if not running:
		queue_redraw()


# --- Рисование ----------------------------------------------------------------------------

func _center() -> Vector2:
	return Vector2(size.x / 2.0, size.y * 0.5 - 16.0)


## Расстояние от центра до лунки: по высоте поля, чтобы верхняя и нижняя влезли.
func _reach() -> float:
	return clampf(size.y * 0.3, 180.0, 280.0)


func _hole_pos(i: int) -> Vector2:
	return _center() + DIRS[i] * _reach()


func _hammer_pos() -> Vector2:
	var p := _center()
	if _jab > 0.0:
		p += _jab_dir * _reach() * 0.45 * sin(PI * (1.0 - _jab / JAB_SECONDS))
	if _shake > 0.0:
		p.x += sin(_shake * 50.0) * 10.0 * _shake / SHAKE_SECONDS
	return p


func _mole_color(i: int) -> Color:
	if state[i] == State.MISSED:
		return Style.INK_3
	return Style.accent(0)


func _draw() -> void:
	if def == null or _moles.is_empty():
		return
	var jelly := Jelly.on()
	for i in HOLES:
		var p := _hole_pos(i)
		draw_circle(p, HOLE_R, Style.SURFACE_2)
		draw_circle(p, PIT_R, Color(Style.INK, 0.1))
	if jelly:
		_rings.draw(self)
	for i in HOLES:
		var sc := _mole_scale(i)
		if sc < 0.08:
			continue
		var col := _mole_color(i)
		if jelly:
			if is_up(i):
				_moles[i].draw_lifted(self, col, LIFT * sc, Vector2(0.0, -LIFT * sc))
			else:
				_moles[i].draw(self, col)
		else:
			draw_circle(_hole_pos(i), MOLE_R * sc, col)
	var hcol := Style.INK_3 if stun > 0.0 else Style.INK
	if jelly:
		_hammer.draw(self, hcol)
		_splash.draw_air(self, Vector2.ZERO)
	else:
		draw_circle(_hammer_pos(), HAMMER_R, hcol)
	_draw_count()
	_draw_slots()


## Число попаданий на молотке моноширинным белым.
func _draw_count() -> void:
	var mono := Style.mono_font()
	var s := str(hits)
	var sz := mono.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, COUNT_SIZE)
	var p := _hammer_pos() + Vector2(-sz.x / 2.0, COUNT_SIZE * 0.36)
	draw_string(mono, p, s, HORIZONTAL_ALIGNMENT_LEFT, -1, COUNT_SIZE, Style.SURFACE_SOLID)


## Пять кружков упущенных справа сверху, напротив значка: пустые, упущенные `danger`.
func _draw_slots() -> void:
	var y := 40.0 + AspectIcon.SIZE / 2.0
	var x0 := size.x - 48.0 - SLOT_R - (MAX_MISSED - 1) * SLOT_GAP
	for i in MAX_MISSED:
		var c := Style.DANGER if i < missed else Color(Style.INK, 0.12)
		var r := SLOT_R * clampf(1.0 + _slots[i].value, 0.5, 1.8)
		draw_circle(Vector2(x0 + i * SLOT_GAP, y), r, c)
