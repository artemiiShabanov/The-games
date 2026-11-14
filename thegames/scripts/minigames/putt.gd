extends Minigame
## «Натяни» (putt, спорт), каталог `docs/specs/minigames_catalog.md`. Вид сбоку: шар слева на
## земле, лунка (выемка в земле) на расстоянии, которое меняется каждый удар. Держи ␣: от шара
## по земле тянется полоса силы, её конец показывает, куда упадёт шар. Отпустил: шар летит по
## дуге и падает туда, куда показывал конец полосы, плюс снос. Упал в ширину лунки: лунка
## засчитана, иначе промах. 5 лунок за время мини-игры, провал при 2 промахах или по таймеру.
## Полоса доходит до конца шкалы и сжимается обратно (держать дальше можно, это стоит времени).
## Снос (с ростом `t`): шар в полёте сдувает вбок на показанную величину; над лункой стрелка от
## точки, куда целить, до лунки. Шар в полёте на финише засчитывается, если летит в лунку.
## Логика в логических пикселях шкалы `REACH`, поле масштабирует их под ширину карточки.
## Параметры от `t` в `resources/minigames/putt.tres`: speed (скорость полосы, долей шкалы в
## секунду), near и far (разброс расстояний до лунки, доли шкалы), cup (ширина лунки, лог. px),
## drift (снос самое большее, лог. px; у лунки от половины до полного, в случайную сторону).
## Мармелад (STYLE «Мармелад»): шар мягкий `JellyShape`, тянется в полёте и плющится при
## падении; земля `JellySurface` идёт волнами от удара, выемка лунки сглатывает шар и
## переезжает к новой лунке; попадание брызгает неяркими каплями цвета шара, промах сереет в
## `ink-3`, подскакивает прочь от лунки и тонет.

enum Phase { READY, CHARGE, FLIGHT, RESULT }

const HOLES := 5
const MAX_MISSES := 2
## Логическая длина шкалы: сила 1 кладёт шар на `REACH` от старта (без сноса).
const REACH := 1280.0
## Запас поля за концом шкалы под снос и подскок промаха, лог. px.
const TAIL := 170.0
## Соседние лунки не ближе этой доли шкалы друг к другу: расстояние каждый раз разное.
const MIN_STEP := 0.12
## Точка прицела (лунка минус снос) в этих долях шкалы.
const AIM_MIN := 0.14
const AIM_MAX := 0.96
## Снос меньше этого не действует и не показывается, лог. px.
const DRIFT_MIN := 20.0
## Снос лунки от этой доли `drift` до полного.
const DRIFT_LOW := 0.5
## Полёт: время от дальности прицела, с; высота дуги от дальности, px.
const FLIGHT_BASE := 0.45
const FLIGHT_PER_REACH := 0.35
const ARC := 0.34
const ARC_MIN := 70.0
const ARC_MAX := 340.0
## Показ результата удара до следующей лунки, с.
const RESULT_SECONDS := 0.55
## Промах: подскок прочь от лунки, потом тонет до конца показа.
const HOP_SECONDS := 0.28
const HOP_X := 70.0
const HOP_Y := 46.0
## Выемка лунки переезжает к новой за столько (экспоненциально), с.
const CUP_SLIDE := 0.08
const CUP_DEPTH := 46.0
const BALL_R := 34.0
const BALL_X := 160.0
const GROUND_H := 64.0
const BAR_Y := 14.0
const BAR_W := 12.0
const TIP_W := 12.0
const TIP_H := 56.0
const ARROW_Y := 132.0
const ARROW_W := 8.0
const ARROW_HEAD := 22.0
const DOT_R := 12.0
const DOT_GAP := 44.0
const SLOT_R := 12.0
const SLOT_GAP := 40.0
## Бот WIN: жмёт через столько после готовности; ошибка прицела до этой доли полуширины лунки.
const BOT_WAIT := 0.25
const BOT_ERROR := 0.4
## Бот LOSE: целит в эту долю нужной силы, недолёт.
const BOT_SHORT := 0.45

var speed := 0.5
var near := 0.4
var far := 0.7
var cup_w := 160.0
var drift_max := 0.0

var phase := Phase.READY
var phase_time := 0.0
## Лунка и снос текущего удара, лог. px от шара.
var cup := 0.0
var drift := 0.0
var charge_time := 0.0
## Сила 0..1: конец полосы на `power * REACH`.
var power := 0.0
var aim := 0.0
var land := 0.0
var hit := false
var flight_time := 0.5
var holes := 0
var misses := 0
var shots := 0

var _charge_sound: AudioStreamPlayer
var _shot_sound: AudioStreamPlayer
var _hit_sound: AudioStreamPlayer
var _miss_sound: AudioStreamPlayer

var _bot_rng := RandomNumberGenerator.new()
var _bot_target := -1.0

# Мармелад: только рисование, на игру не влияет.
var _ball: JellyShape
var _ground := JellySurface.new()
var _splash := SplashFx.new()
## Выемка лунки на экране догоняет `cup`; `_gulp` раздувает её при попадании.
var _cup_x := -1.0
var _gulp := JellySpring.new()
var _arrow := JellySpring.new()
var _dots: Array[JellySpring] = []
var _slots: Array[JellySpring] = []
var _landed_fx := false


func _on_start() -> void:
	speed = def.param(&"speed", t, 0.5)
	near = def.param(&"near", t, 0.4)
	far = maxf(def.param(&"far", t, 0.7), near)
	cup_w = def.param(&"cup", t, 160.0)
	drift_max = def.param(&"drift", t, 0.0)
	_bot_rng.seed = rng.seed + 7
	_charge_sound = MiniSfx.tap(330.0, -4.0)
	_shot_sound = MiniSfx.tap(520.0)
	_hit_sound = MiniSfx.hit(392.0)
	_miss_sound = MiniSfx.miss()
	for p in [_charge_sound, _shot_sound, _hit_sound, _miss_sound]:
		add_child(p)
	for i in HOLES:
		_dots.append(JellySpring.new())
	for i in MAX_MISSES:
		_slots.append(JellySpring.new())
	_ball = JellyShape.circle(BALL_R, 32)
	_next_cup()
	_enter(Phase.READY)
	queue_redraw()


func _enter(p: Phase) -> void:
	phase = p
	phase_time = 0.0
	if p == Phase.READY:
		power = 0.0
		_bot_target = -1.0
		_landed_fx = false
		if Jelly.on() and _ball != null and size.x > 0.0:
			_ball.snap(_ball_rest())
			_ball.poke(160.0)
			_arrow.kick(10.0)


## Новая лунка: расстояние в [near, far] не ближе `MIN_STEP` к прошлой, снос в случайную
## сторону; точка прицела `cup - drift` остаётся на шкале.
func _next_cup() -> void:
	var d := 0.0
	if drift_max >= DRIFT_MIN:
		d = drift_max * rng.randf_range(DRIFT_LOW, 1.0) * (1.0 if rng.randf() < 0.5 else -1.0)
	var lo := maxf(near, AIM_MIN + d / REACH)
	var hi := maxf(minf(far, AIM_MAX + d / REACH), lo)
	var prev := cup
	var u := rng.randf_range(lo, hi)
	for k in 8:
		if shots == 0 or absf(u * REACH - prev) >= MIN_STEP * REACH:
			break
		u = rng.randf_range(lo, hi)
	cup = u * REACH
	drift = d


func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	if GameInput.is_a(event):
		press()
		get_viewport().set_input_as_handled()
	elif event.is_action_released(GameInput.A):
		release()
		get_viewport().set_input_as_handled()


## Зажал: полоса начинает тянуться. Только когда шар готов.
func press() -> void:
	if phase != Phase.READY:
		return
	charge_time = 0.0
	power = 0.0
	_charge_sound.play()
	_enter(Phase.CHARGE)


## Отпустил: шар летит туда, куда показывал конец полосы, плюс снос.
func release() -> void:
	if phase != Phase.CHARGE:
		return
	aim = power * REACH
	land = aim + drift
	hit = absf(land - cup) <= cup_w / 2.0
	flight_time = FLIGHT_BASE + FLIGHT_PER_REACH * clampf(power, 0.0, 1.0)
	_shot_sound.play()
	if Jelly.on():
		_ball.poke(-180.0)
	_enter(Phase.FLIGHT)


## Куда упадёт шар, если отпустить сейчас, лог. px.
func landing_now() -> float:
	return power * REACH + drift


func _on_tick(delta: float) -> void:
	phase_time += delta
	match phase:
		Phase.CHARGE:
			charge_time += delta
			power = pingpong(charge_time * speed, 1.0)
			# Отпустил на паузе: события не было, клавиша уже не зажата.
			if not AutoTest.bot_active() and not GameInput.a_pressed():
				release()
		Phase.FLIGHT:
			if phase_time >= flight_time:
				_land()
		Phase.RESULT:
			if phase_time >= RESULT_SECONDS:
				_next_cup()
				_enter(Phase.READY)
	queue_redraw()


func _land() -> void:
	shots += 1
	if hit:
		holes += 1
		_hit_sound.play()
		_dots[holes - 1].kick(14.0)
	else:
		misses += 1
		_miss_sound.play()
		_slots[misses - 1].kick(14.0)
	_land_fx()
	_enter(Phase.RESULT)
	if holes >= HOLES:
		finish(true)
	elif misses >= MAX_MISSES:
		finish(false)


## Время вышло: засчитан, если 5 лунок уже есть или последний шар в полёте летит в лунку.
func _on_timeout() -> bool:
	return holes + (1 if phase == Phase.FLIGHT and hit else 0) >= HOLES


func _on_finish(success: bool) -> void:
	if AutoTest.enabled:
		AutoTest.note("putt: t %.2f, %s, лунок %d, промахов %d, ударов %d, %.1f с" % [t, "успех" if success else "провал", holes, misses, shots, elapsed])


## Бот: через `BOT_WAIT` после готовности зажимает; WIN отпускает, когда конец полосы в точке
## «лунка минус снос» с ошибкой до `BOT_ERROR` полуширины лунки (отпускание точно между
## кадрами, иначе на ускоренном времени конец перескакивает лунку). LOSE целит в
## `BOT_SHORT` нужной силы: недолёт, два промаха.
func _bot_step(delta: float) -> bool:
	match phase:
		Phase.READY:
			if phase_time >= BOT_WAIT:
				press()
		Phase.CHARGE:
			if _bot_target < 0.0:
				var want := cup - drift
				if AutoTest.bot_mode == AutoTest.BotMode.WIN:
					want += _bot_rng.randf_range(-1.0, 1.0) * BOT_ERROR * cup_w / 2.0
				else:
					want *= BOT_SHORT
				_bot_target = clampf(want / REACH, 0.0, 1.0)
			var at := _bot_target / speed
			if charge_time + delta >= at:
				charge_time = at
				power = _bot_target
				release()
	return false


# --- Мармелад -----------------------------------------------------------------------------

func _land_fx() -> void:
	_landed_fx = true
	if not Jelly.on():
		return
	var p := Vector2(_sx(land), _gy())
	if hit:
		var col := Style.accent(0)
		_ball.poke(-240.0)
		_gulp.kick(5.0)
		_ground.impact(_sx(cup), 500.0)
		_splash.pop(Vector2(_sx(cup), _gy()), col, 4, 420.0, 0.55)
	else:
		_ball.poke(-300.0)
		_ball.push(Vector2(0.0, 260.0), Vector2.DOWN)
		_ground.impact(p.x, 900.0)


## Мармелад живёт и после финиша, пока сцена на экране; на паузе стоит.
func _process(delta: float) -> void:
	super(delta)
	if _ball == null or paused or def == null or size.x <= 0.0:
		return
	var tu := Jelly.tuning()
	if not running:
		# После финиша `_on_tick` не идёт: полёт и показ результата доигрываются здесь.
		phase_time += delta
		if phase == Phase.FLIGHT and phase_time >= flight_time:
			_land_fx()
			phase = Phase.RESULT
			phase_time = 0.0
	if _cup_x < 0.0:
		_cup_x = cup
	_cup_x = lerpf(_cup_x, cup, 1.0 - exp(-delta / CUP_SLIDE))
	_ball.follow(delta, _ball_pos(), 0.0, maxf(_ball_scale(), 0.05))
	_gulp.step(delta, tu.spring_stiffness, tu.spring_damping)
	_arrow.step(delta, tu.spring_stiffness, tu.spring_damping)
	for s in _dots:
		s.step(delta, tu.spring_stiffness, tu.spring_damping)
	for s in _slots:
		s.step(delta, tu.spring_stiffness, tu.spring_damping)
	_ground.step(delta)
	_splash.step(delta, Callable())
	if not running:
		queue_redraw()


# --- Геометрия ----------------------------------------------------------------------------

## Масштаб логических пикселей шкалы на экран: шкала с запасом во всю ширину поля.
func _k() -> float:
	return maxf((size.x - 80.0 - BALL_X) / (REACH + TAIL), 0.1)


func _sx(lx: float) -> float:
	return BALL_X + lx * _k()


func _gy() -> float:
	return size.y * 0.66


func _ball_rest() -> Vector2:
	return Vector2(BALL_X, _gy() - BALL_R)


## Выемка лунки под экранным `x`: почти отвесные стенки по краям ширины, плоское дно.
func _dip(x: float) -> float:
	var half := cup_w / 2.0 * _k()
	var u := (x - _sx(_cup_x)) / half
	if absf(u) >= 1.0:
		return 0.0
	return CUP_DEPTH * (1.0 + _gulp.value * 0.04) * sqrt(1.0 - u * u * u * u)


func _surface(x: float) -> float:
	return _gy() + _dip(x) + _ground.height(x)


func _ball_pos() -> Vector2:
	match phase:
		Phase.FLIGHT:
			var s := clampf(phase_time / flight_time, 0.0, 1.0)
			var h := clampf(aim * _k() * ARC, ARC_MIN, ARC_MAX)
			var x := _sx(aim * s + drift * s * s)
			return Vector2(x, _gy() - BALL_R - 4.0 * h * s * (1.0 - s))
		Phase.RESULT:
			if not _landed_fx:
				return _ball_rest()
			if hit:
				return Vector2(_sx(cup), _gy() + CUP_DEPTH - BALL_R)
			var dir := signf(land - cup)
			var u := clampf(phase_time / HOP_SECONDS, 0.0, 1.0)
			var x := _sx(land) + dir * HOP_X * u
			return Vector2(x, _surface(x) - BALL_R - 4.0 * HOP_Y * u * (1.0 - u))
	return _ball_rest()


## Масштаб шара: при натяжке чуть поджат, в лунке и после промаха тонет.
func _ball_scale() -> float:
	match phase:
		Phase.CHARGE:
			return 1.0 - 0.08 * power
		Phase.RESULT:
			if hit:
				return clampf(1.0 - phase_time / RESULT_SECONDS, 0.0, 1.0)
			if phase_time > HOP_SECONDS:
				return clampf(1.0 - (phase_time - HOP_SECONDS) / (RESULT_SECONDS - HOP_SECONDS), 0.0, 1.0)
	return 1.0


# --- Рисование ----------------------------------------------------------------------------

func _draw() -> void:
	if def == null or _ball == null:
		return
	var jelly := Jelly.on()
	_draw_ground()
	_draw_bar()
	_draw_arrow()
	var col := Style.INK_3 if phase == Phase.RESULT and not hit and _landed_fx else Style.accent(0)
	if _ball_scale() > 0.06:
		if jelly:
			_ball.draw(self, col)
		else:
			draw_circle(_ball_pos(), BALL_R * _ball_scale(), col)
	if jelly:
		_splash.draw_air(self, Vector2.ZERO)
	_draw_dots()
	_draw_slots()


## Земля плитой `surface-2` с выемкой лунки; выемка подкрашена `a2`.
func _draw_ground() -> void:
	var x0 := 56.0
	var x1 := size.x - 56.0
	var gy := _gy()
	var cap := GROUND_H / 2.0
	draw_circle(Vector2(x0 + cap, gy + cap), cap, Style.SURFACE_2)
	draw_circle(Vector2(x1 - cap, gy + cap), cap, Style.SURFACE_2)
	# Верх плиты: частый шаг, а в ширине лунки точки выемки (у неё почти отвесные стенки).
	var half := cup_w / 2.0 * _k()
	var cx := _sx(_cup_x)
	var pit := PackedVector2Array()
	var n := 32
	for i in n + 1:
		var px := cx - half + 2.0 * half * i / n
		pit.append(Vector2(px, _surface(px)))
	var top := PackedVector2Array()
	var x := x0 + cap
	var pit_done := false
	while x < x1 - cap:
		if x >= cx - half and not pit_done:
			pit_done = true
			for q in pit:
				if q.x > x0 + cap and q.x < x1 - cap:
					top.append(q)
			x = maxf(x, cx + half + 8.0)
			continue
		top.append(Vector2(x, _surface(x)))
		x += 8.0
	top.append(Vector2(x1 - cap, _surface(x1 - cap)))
	var poly := top.duplicate()
	poly.append(Vector2(x1 - cap, gy + GROUND_H))
	poly.append(Vector2(x0 + cap, gy + GROUND_H))
	Jelly.fill(self, poly, Style.SURFACE_2)
	# Подкраска выемки `a2`: между ровной линией земли и дном.
	if pit.size() >= 3:
		Jelly.fill(self, pit, Color(Style.accent(1), 0.35))


## Полоса силы по земле от шара и стойка на её конце: туда упадёт шар без сноса. После
## удара полоса бледнеет и стоит до следующей лунки: видно, куда целил.
func _draw_bar() -> void:
	if phase == Phase.READY:
		return
	var tip := _sx(power * REACH if phase == Phase.CHARGE else aim)
	var col := Style.accent(0) if phase == Phase.CHARGE else Color(Style.accent(0), 0.35)
	var y := _gy() + BAR_Y + BAR_W / 2.0
	draw_line(Vector2(BALL_X, y), Vector2(tip, y), col, BAR_W)
	draw_circle(Vector2(BALL_X, y), BAR_W / 2.0, col)
	var top := Vector2(tip, _gy() - TIP_H + TIP_W / 2.0)
	var bottom := Vector2(tip, y)
	draw_line(top, bottom, col, TIP_W)
	draw_circle(top, TIP_W / 2.0, col)
	draw_circle(bottom, TIP_W / 2.0, col)


## Снос: стрелка над лункой от точки, куда целить, до лунки.
func _draw_arrow() -> void:
	if absf(drift) < DRIFT_MIN:
		return
	var y := _gy() - ARROW_Y + _arrow.value * 4.0
	var to := _sx(_cup_x)
	var from := _sx(_cup_x - drift)
	var dir := signf(to - from)
	var col := Style.INK_2
	var head := minf(ARROW_HEAD, absf(to - from) * 0.5)
	var neck := to - dir * head
	draw_line(Vector2(from, y), Vector2(neck, y), col, ARROW_W)
	draw_circle(Vector2(from, y), ARROW_W / 2.0, col)
	draw_colored_polygon(PackedVector2Array([
		Vector2(to, y),
		Vector2(neck, y - head * 0.75),
		Vector2(neck, y + head * 0.75),
	]), col)


## Пять кружков лунок сверху по центру: забитые `success`, текущая крупнее.
func _draw_dots() -> void:
	var y := 40.0 + AspectIcon.SIZE / 2.0
	var x0 := size.x / 2.0 - (HOLES - 1) * DOT_GAP / 2.0
	for i in HOLES:
		var c := Style.SUCCESS if i < holes else Color(Style.INK, 0.12)
		var r := DOT_R
		if i == holes and running:
			r *= 1.3
		r *= clampf(1.0 + _dots[i].value, 0.5, 1.8)
		draw_circle(Vector2(x0 + i * DOT_GAP, y), r, c)


## Два кружка промахов справа сверху, напротив значка: промахи `danger`.
func _draw_slots() -> void:
	var y := 40.0 + AspectIcon.SIZE / 2.0
	var x0 := size.x - 48.0 - SLOT_R - (MAX_MISSES - 1) * SLOT_GAP
	for i in MAX_MISSES:
		var c := Style.DANGER if i < misses else Color(Style.INK, 0.12)
		var r := SLOT_R * clampf(1.0 + _slots[i].value, 0.5, 1.8)
		draw_circle(Vector2(x0 + i * SLOT_GAP, y), r, c)
