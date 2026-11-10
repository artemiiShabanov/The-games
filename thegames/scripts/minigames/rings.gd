extends Minigame
## «Выстрой» (rings, файтинг), каталог `docs/specs/minigames_catalog.md`. Замок: три
## концентрических кольца с вырезом крутятся с разной скоростью вокруг сердцевины с замочной
## скважиной. Сверху стрелка и от сердцевины к ней канал. ␣ останавливает подсвеченное кольцо,
## по очереди внешнее, среднее, внутреннее. Стрелка внутри выреза: кольцо встало, вырез
## доворачивается точно под стрелку, подсветка переходит на следующее. Мимо: замок клинит на
## `JAM_SECONDS` (все кольца красные, трясутся), потом все крутятся снова и начинать с внешнего:
## промах стоит времени, а при узких вырезах и таймера. Все три
## выреза под стрелкой: засов выезжает по каналу, замок щёлкает, следующий замок с новыми
## кольцами. 3 замка за 20 с, иначе провал по таймеру.
## Параметры от `t` в `resources/minigames/rings.tres`: speed (скорость вращения, °/с; у колец
## множители `SPEED_MULTS` в случайном порядке), gap (ширина выреза, °), reverse (вероятность,
## что кольцо крутится против часовой).
## Мармелад (STYLE «Мармелад»): кольца на пружине толщины и радиуса: вставшее вздрагивает,
## заклинившее трясётся, новый замок выскакивает кольцами; сердцевина мягкая `JellyShape`,
## засов выстреливает в стрелку и брызгает неяркими каплями `a1`, от замка расходится круг.

enum Phase { PLAY, OPEN }
enum RingState { SPIN, SET, JAM }

const RINGS := 3
const LOCKS := 3
## Множители скорости колец, раздаются кольцам замка в случайном порядке.
const SPEED_MULTS: Array[float] = [0.8, 1.05, 1.35]
## Вырез нового замка не ближе этого к стрелке, °.
const START_AWAY := 70.0
## Клин после промаха, с.
const JAM_SECONDS := 0.5
## Замок открывается: засов едет столько, показ всего столько, с.
const BOLT_SECONDS := 0.16
const OPEN_SECONDS := 0.6
## Вставшее кольцо доворачивает вырез под стрелку за такое время (экспонента), с.
const SNAP_SECONDS := 0.04
## Размеры при высоте поля 1080: радиусы осей колец снаружи внутрь, толщина, сердцевина.
const RADII: Array[float] = [270.0, 200.0, 130.0]
const WIDTH := 50.0
const HUB_R := 72.0
const CHANNEL_W := 8.0
const BOLT_W := 20.0
const DOT_R := 12.0
const DOT_GAP := 44.0
## Бот WIN: не раньше этого после подсветки кольца; ошибка до такой доли полувыреза.
const BOT_READY := 0.25
const BOT_ERROR := 0.5

var speed := 180.0
var gap := 50.0
var reverse := 0.0

var phase := Phase.PLAY
var phase_time := 0.0
## Угол середины выреза от верха по часовой, °.
var angle: Array[float] = []
## Скорость вращения со знаком (плюс по часовой), °/с.
var spin: Array[float] = []
var ring_state: Array[RingState] = []
var jam_time: Array[float] = []
var active := 0
var active_time := 0.0
var locks := 0
var stops := 0
var jams := 0
var reversed := 0

var _set_sound: AudioStreamPlayer
var _jam_sound: AudioStreamPlayer
var _open_sound: AudioStreamPlayer
var _bot_rng := RandomNumberGenerator.new()
var _bot_err := 0.0

# Мармелад: только рисование, на игру не влияет.
var _snap: Array[float] = []
var _wob: Array[JellySpring] = []
var _dots: Array[JellySpring] = []
var _hub: JellyShape
var _bolt_hit := false
var _rings := RingFx.new()
var _splash := SplashFx.new()


func _on_start() -> void:
	speed = def.param(&"speed", t, 180.0)
	gap = def.param(&"gap", t, 50.0)
	reverse = def.param(&"reverse", t, 0.0)
	_bot_rng.seed = hash(str(rng.seed, ":rings_bot"))
	_set_sound = Sfx.player(Sfx.blip(660.0, 0.08, 0.4, 30.0))
	_jam_sound = Sfx.player(Sfx.thud())
	_open_sound = Sfx.player(Sfx.blip(988.0, 0.2, 0.5, 10.0))
	for p in [_set_sound, _jam_sound, _open_sound]:
		add_child(p)
	for i in RINGS:
		angle.append(0.0)
		spin.append(0.0)
		ring_state.append(RingState.SPIN)
		jam_time.append(0.0)
		_snap.append(0.0)
		_wob.append(JellySpring.new())
	for i in LOCKS:
		_dots.append(JellySpring.new())
	_hub = JellyShape.circle(HUB_R, 36)
	_new_lock()
	queue_redraw()


## Новый замок: вырезы вдали от стрелки, скорости колец перемешаны, направления по `reverse`.
func _new_lock() -> void:
	phase = Phase.PLAY
	phase_time = 0.0
	active = 0
	active_time = 0.0
	var mults := SPEED_MULTS.duplicate()
	for i in range(mults.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var tmp: float = mults[i]
		mults[i] = mults[j]
		mults[j] = tmp
	for i in RINGS:
		angle[i] = rng.randf_range(START_AWAY, 360.0 - START_AWAY)
		var dir := 1.0
		if rng.randf() < reverse:
			dir = -1.0
			reversed += 1
		spin[i] = speed * mults[i] * dir
		ring_state[i] = RingState.SPIN
		jam_time[i] = 0.0
		_snap[i] = 0.0
		if Jelly.on():
			_wob[i].value = -0.5 - 0.15 * i
	_bot_err = _bot_rng.randf_range(-BOT_ERROR, BOT_ERROR) * gap / 2.0
	_bolt_hit = false


## Смещение выреза кольца `i` от стрелки, −180..180°.
func offset(i: int) -> float:
	return wrapf(angle[i], -180.0, 180.0)


## Стрелка внутри выреза кольца `i`.
func aligned(i: int) -> bool:
	return absf(offset(i)) <= gap / 2.0


func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	if GameInput.is_a(event):
		_press()
		get_viewport().set_input_as_handled()


func _press() -> void:
	if phase != Phase.PLAY or ring_state[active] != RingState.SPIN:
		return
	_stop(active, angle[active])


## Остановить подсвеченное кольцо `i` на угле `at`: встало или заклинило.
func _stop(i: int, at: float) -> void:
	angle[i] = wrapf(at, 0.0, 360.0)
	stops += 1
	if aligned(i):
		ring_state[i] = RingState.SET
		_snap[i] = offset(i)
		angle[i] = 0.0
		_set_sound.play()
		if Jelly.on():
			_wob[i].kick(5.0)
			_hub.poke(80.0)
		active += 1
		active_time = 0.0
		_bot_err = _bot_rng.randf_range(-BOT_ERROR, BOT_ERROR) * gap / 2.0
		if active >= RINGS:
			_open()
	else:
		# Клин: весь замок, вставшие кольца снова крутятся, начинать с внешнего.
		jams += 1
		for k in RINGS:
			ring_state[k] = RingState.JAM
			jam_time[k] = 0.0
			if Jelly.on():
				_wob[k].kick(-4.0 if k == i else -2.0)
		active = 0
		active_time = 0.0
		_jam_sound.play()


func _open() -> void:
	phase = Phase.OPEN
	phase_time = 0.0
	locks += 1
	_open_sound.play()
	if Jelly.on():
		_hub.poke(-220.0)
		_dots[locks - 1].kick(14.0)
	if locks >= LOCKS:
		finish(true)


func _on_tick(delta: float) -> void:
	phase_time += delta
	active_time += delta
	for i in RINGS:
		match ring_state[i]:
			RingState.SPIN:
				angle[i] = wrapf(angle[i] + spin[i] * delta, 0.0, 360.0)
			RingState.JAM:
				jam_time[i] += delta
				if jam_time[i] >= JAM_SECONDS:
					ring_state[i] = RingState.SPIN
	if phase == Phase.OPEN and phase_time >= OPEN_SECONDS:
		_new_lock()
	queue_redraw()


func _on_timeout() -> bool:
	return locks >= LOCKS


func _on_finish(success: bool) -> void:
	if AutoTest.enabled:
		AutoTest.note("rings: t %.2f, %s, замков %d, остановок %d, клинов %d, против часовой %d, %.1f с" % [t, "успех" if success else "провал", locks, stops, jams, reversed, elapsed])


## Бот: WIN останавливает кольцо, когда середина выреза проходит стрелку (с ошибкой до
## `BOT_ERROR` полувыреза), не раньше `BOT_READY` после подсветки; момент между кадрами, чтобы
## на ускоренном времени не перескочить. LOSE жмёт, когда вырез напротив стрелки: каждое
## нажатие клин, ни одного замка, провал по таймеру.
func _bot_step(delta: float) -> bool:
	if phase != Phase.PLAY or ring_state[active] != RingState.SPIN or active_time < BOT_READY:
		return false
	var i := active
	if AutoTest.bot_mode == AutoTest.BotMode.WIN:
		var d := wrapf(angle[i] - _bot_err, -180.0, 180.0)
		var step := spin[i] * delta
		if absf(d) < 90.0 and (d <= 0.0) != (d + step <= 0.0):
			_stop(i, _bot_err)
	elif absf(offset(i)) > 150.0:
		_press()
	return false


# --- Мармелад -----------------------------------------------------------------------------

## Мармелад живёт и после финиша, пока сцена на экране; на паузе стоит.
func _process(delta: float) -> void:
	super(delta)
	if _hub == null or paused or def == null:
		return
	var tu := Jelly.tuning()
	if not running and phase == Phase.OPEN:
		phase_time += delta
	if phase == Phase.OPEN and not _bolt_hit and phase_time >= BOLT_SECONDS:
		_bolt_hit = true
		if Jelly.on():
			var col := Style.accent(0)
			_splash.pop(_marker_tip(), col, 6, 420.0, 0.55)
			_rings.add(_center(), HUB_R * _k(), (RADII[0] + WIDTH) * _k(), Color(col, 0.35), 1, 0.5)
			for s in _wob:
				s.kick(3.0)
	for i in RINGS:
		_snap[i] *= exp(-delta / SNAP_SECONDS)
		_wob[i].step(delta, tu.spring_stiffness, tu.spring_damping)
	for s in _dots:
		s.step(delta, tu.spring_stiffness, tu.spring_damping)
	_hub.follow(delta, _center(), 0.0, 1.0)
	_rings.step(delta)
	_splash.step(delta, Callable())
	if not running:
		queue_redraw()


# --- Рисование ----------------------------------------------------------------------------

## Масштаб поля: размеры заданы для высоты 1080.
func _k() -> float:
	return clampf(size.y / 1080.0, 0.5, 1.5)


func _center() -> Vector2:
	return Vector2(size.x / 2.0, size.y * 0.5 + 8.0)


## Кончик стрелки над внешним кольцом.
func _marker_tip() -> Vector2:
	return _center() + Vector2.UP * (RADII[0] + WIDTH / 2.0 + 12.0) * _k()


func _ring_color(i: int) -> Color:
	match ring_state[i]:
		RingState.SET:
			return Style.INK
		RingState.JAM:
			return Style.DANGER
	if i == active and phase == Phase.PLAY and running:
		return Style.accent(0)
	return Style.BG.lerp(Style.INK, 0.16)


## Видимый угол выреза: доворот вставшего и тряска заклинившего.
func _shown_angle(i: int) -> float:
	var a := angle[i] + _snap[i]
	if ring_state[i] == RingState.JAM:
		var left := 1.0 - jam_time[i] / JAM_SECONDS
		a += sin(jam_time[i] * 70.0) * 5.0 * left
	return a


func _draw() -> void:
	if def == null or _hub == null:
		return
	var k := _k()
	var c := _center()
	# Канал от сердцевины к стрелке: просвечивает в вырезах.
	draw_line(c, _marker_tip(), Color(Style.INK, 0.12), CHANNEL_W * k)
	for i in RINGS:
		_draw_ring(i, k)
	_draw_bolt(k)
	if Jelly.on():
		_rings.draw(self)
		_hub.draw(self, Style.INK)
	else:
		draw_circle(c, HUB_R * k, Style.INK)
	_draw_keyhole(c, k)
	_draw_marker(k)
	if Jelly.on():
		_splash.draw_air(self, Vector2.ZERO)
	_draw_dots()


## Кольцо дугой без выреза; концы скруглены внутрь дуги, так что видимый вырез равен
## настоящему.
func _draw_ring(i: int, k: float) -> void:
	var wob := clampf(_wob[i].value, -0.8, 0.8)
	var r := RADII[i] * k * (1.0 + wob * 0.06)
	var w := WIDTH * k * maxf(1.0 + wob * 0.3, 0.2)
	var cap := rad_to_deg(w / 2.0 / r)
	var a := _shown_angle(i)
	var from := deg_to_rad(a + gap / 2.0 + cap - 90.0)
	var to := deg_to_rad(a + 360.0 - gap / 2.0 - cap - 90.0)
	if to <= from:
		return
	var col := _ring_color(i)
	var c := _center()
	draw_arc(c, r, from, to, 96, col, w, true)
	draw_circle(c + Vector2.from_angle(from) * r, w / 2.0, col)
	draw_circle(c + Vector2.from_angle(to) * r, w / 2.0, col)


## Засов: из сердцевины по каналу до стрелки, пока замок открывается.
func _draw_bolt(k: float) -> void:
	if phase != Phase.OPEN:
		return
	var f := clampf(phase_time / BOLT_SECONDS, 0.0, 1.0)
	f = 1.0 - (1.0 - f) * (1.0 - f)
	var c := _center()
	var tip := c.lerp(_marker_tip(), f)
	var col := Style.accent(0)
	draw_line(c, tip, col, BOLT_W * k)
	draw_circle(tip, BOLT_W * k / 2.0, col)


## Замочная скважина на сердцевине: кружок и клин книзу.
func _draw_keyhole(c: Vector2, k: float) -> void:
	var hole := Style.BG
	var top := c + Vector2(0.0, -10.0) * k
	draw_circle(top, 13.0 * k, hole)
	draw_colored_polygon(PackedVector2Array([
		top + Vector2(-7.0, 4.0) * k, top + Vector2(7.0, 4.0) * k,
		top + Vector2(12.0, 34.0) * k, top + Vector2(-12.0, 34.0) * k,
	]), hole)


## Стрелка над внешним кольцом остриём к центру.
func _draw_marker(k: float) -> void:
	var tip := _marker_tip()
	draw_colored_polygon(PackedVector2Array([
		tip, tip + Vector2(-16.0, -24.0) * k, tip + Vector2(16.0, -24.0) * k,
	]), Style.INK)


## Три кружка замков сверху по центру: открытые `success`, текущий крупнее.
func _draw_dots() -> void:
	var y := 40.0 + AspectIcon.SIZE / 2.0
	var x0 := size.x / 2.0 - (LOCKS - 1) * DOT_GAP / 2.0
	for i in LOCKS:
		var col := Style.SUCCESS if i < locks else Color(Style.INK, 0.12)
		var r := DOT_R
		if i == locks and running:
			r *= 1.3
		r *= clampf(1.0 + _dots[i].value, 0.5, 1.8)
		draw_circle(Vector2(x0 + i * DOT_GAP, y), r, col)
