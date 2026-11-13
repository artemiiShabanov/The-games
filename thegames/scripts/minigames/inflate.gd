extends Minigame
## «Раздуй» (inflate, технология «продвинутые»), каталог `docs/specs/minigames_catalog.md`. Шар
## надувается, пока зажата A, и останавливается, когда её отпустили. Кольцо-метка показывает
## нужный размер, но видна только до начала надувания, а на высокой сложности гаснет ещё
## раньше: размер надо запомнить. Отпустил у метки с точностью до допуска: засчитано. Не додул
## или перешёл за метку: шар лопнул (перейти нельзя и на зажатой кнопке, шар лопается сам).
## `BALLOONS` шаров, два неудачных это провал.
## Параметры от `t` в `resources/minigames/inflate.tres`: speed (как быстро растёт радиус,
## пикселей в секунду), reach (насколько метка бывает дальше от начального размера), show
## (сколько секунд метка видна, пока шар не трогали).
## Вид как у всех мини-игр, в стиле оболочки: рендера технологии здесь нет (решение
## 2026-11-11). Мармелад: шар дрожит, пока растёт, вздрагивает от удачи, лопается брызгами.
## Мышь (#83): левая кнопка это A, держать и отпустить.

const BALLOONS := 5
const MAX_MISSES := 2
## Начальный радиус шара и самый малый радиус метки.
const START_R := 46.0
const MARK_MIN := 110.0
## Допуск: отпустить можно на столько пикселей раньше или позже метки.
const TOLERANCE := 15.0
## Пауза между шарами: итог виден, новый шар ещё не появился.
const REST := 0.45
const DOT_R := 9.0
const DOT_GAP := 34.0

var speed := 120.0
var reach := 70.0
var show := 2.2
## Радиус шара сейчас и радиус метки.
var radius := START_R
var mark := 160.0
## Сколько секунд шар на экране, надувают ли его, начали ли уже.
var age := 0.0
var holding := false
var started := false
## Номер шара, сколько удач и неудач; исходы по порядку.
var balloon := 0
var passed := 0
var missed := 0
var results: Array[bool] = []
## Пауза после итога; больше нуля: шар ждёт смены.
var rest := 0.0

var _last_ok := true
var _popped := false
var _pop := JellySpring.new()
var _wobble := JellySpring.new()
var _dots: Array[JellySpring] = []
var _splash := SplashFx.new()
var _grow_sfx: AudioStreamPlayer
var _ok_sfx: Array[AudioStreamPlayer] = []
var _pop_sfx: AudioStreamPlayer
var _low_sfx: AudioStreamPlayer
var _win_sfx: AudioStreamPlayer


func _on_start() -> void:
	speed = clampf(def.param(&"speed", t, 120.0), 60.0, 320.0)
	reach = clampf(def.param(&"reach", t, 70.0), 20.0, 190.0)
	show = clampf(def.param(&"show", t, 2.2), 0.2, 4.0)
	for i in BALLOONS:
		_dots.append(JellySpring.new())
		var p := Sfx.player(Sfx.blip(392.0 * pow(2.0, i / 6.0), 0.12, 0.32, 20.0))
		add_child(p)
		_ok_sfx.append(p)
	_pop_sfx = Sfx.player(Sfx.thud(0.14, 0.5))
	_low_sfx = Sfx.player(Sfx.blip(180.0, 0.2, 0.35, 9.0))
	_win_sfx = Sfx.player(Sfx.blip(990.0, 0.3, 0.45, 8.0))
	_grow_sfx = Sfx.player(Sfx.hiss(0.2, 0.08))
	for p: AudioStreamPlayer in [_pop_sfx, _low_sfx, _win_sfx, _grow_sfx]:
		add_child(p)
	_next_balloon()
	queue_redraw()


## Новый шар: метка на случайном расстоянии в пределах сложности.
func _next_balloon() -> void:
	radius = START_R
	mark = MARK_MIN + rng.randf_range(0.0, reach)
	age = 0.0
	holding = false
	started = false
	_popped = false
	rest = 0.0


## Видна ли метка: пока шар не трогали и не вышло её время.
func mark_visible() -> bool:
	return not started and age < show and rest <= 0.0


## Насколько шар сейчас от метки, пиксели: минус не додут, плюс перешёл.
func error() -> float:
	return radius - mark


func _on_tick(delta: float) -> void:
	if rest > 0.0:
		rest -= delta
		if rest <= 0.0:
			_advance()
		queue_redraw()
		return
	age += delta
	var down := Input.is_action_pressed(GameInput.A)
	if down and not started:
		started = true
		if _grow_sfx != null:
			_grow_sfx.play()
	if started and down:
		holding = true
		radius += speed * delta
		if Jelly.on():
			_wobble.kick(0.6)
		# Перешёл за метку дальше допуска: лопнул сам, кнопку отпускать поздно.
		if error() > TOLERANCE:
			_settle(false, true)
	elif started and holding:
		# Отпустил: у метки засчитано, раньше не додул.
		_settle(absf(error()) <= TOLERANCE, false)
	queue_redraw()


## Итог шара: удача или нет; `burst` лопнул от перенадува.
func _settle(ok: bool, burst: bool) -> void:
	holding = false
	results.append(ok)
	_last_ok = ok
	_popped = not ok
	_dots[balloon].kick(9.0)
	if ok:
		passed += 1
		_ok_sfx[clampi(balloon, 0, _ok_sfx.size() - 1)].play()
		if Jelly.on():
			_pop.kick(6.0)
			_splash.pop(size / 2.0, Style.SUCCESS, 7, 420.0, 0.5)
	else:
		missed += 1
		(_pop_sfx if burst else _low_sfx).play()
		if Jelly.on():
			_splash.pop(size / 2.0, Style.accent(balloon % 2), 12 if burst else 6, 620.0 if burst else 300.0, 0.6)
	rest = REST


## После паузы: конец игры или следующий шар.
func _advance() -> void:
	balloon += 1
	if missed >= MAX_MISSES:
		finish(false)
	elif balloon >= BALLOONS:
		_win_sfx.play()
		finish(true)
	else:
		_next_balloon()


## Время вышло раньше шаров: не засчитано.
func _on_timeout() -> bool:
	return false


## Бот: WIN зажимает и отпускает точно у метки; LOSE держит, пока шар не лопнет.
func _bot_step(_delta: float) -> bool:
	var want := false
	if rest <= 0.0 and running:
		if AutoTest.bot_mode == AutoTest.BotMode.WIN:
			want = error() < -2.0
		else:
			want = true
	if Input.is_action_pressed(GameInput.A) != want:
		send_action(GameInput.A, want)
	return false


func _on_finish(success: bool) -> void:
	if AutoTest.bot_active() and Input.is_action_pressed(GameInput.A):
		Input.action_release(GameInput.A)
	if success and Jelly.on():
		_pop.kick(8.0)
		_splash.pop(size / 2.0, Style.SUCCESS, 9, 480.0, 0.6)


func _process(delta: float) -> void:
	super(delta)
	if def == null or paused:
		return
	var tu := Jelly.tuning()
	_pop.step(delta, tu.spring_stiffness, tu.spring_damping)
	_wobble.step(delta, tu.spring_stiffness, tu.spring_damping)
	for d in _dots:
		d.step(delta, tu.spring_stiffness, tu.spring_damping)
	_splash.step(delta, func(_x: float) -> float: return INF)
	if not running:
		queue_redraw()


# --- Рисование --------------------------------------------------------------------------------

func _draw() -> void:
	if def == null or _dots.is_empty():
		return
	var center := size / 2.0 + Vector2(0.0, 18.0)
	var jelly := Jelly.on()
	# Метка: пунктирное кольцо нужного размера, пока её видно.
	if mark_visible():
		var fade := clampf((show - age) / 0.35, 0.0, 1.0)
		for k in 24:
			if k % 2 == 0:
				draw_arc(center, mark, TAU * k / 24.0, TAU * (k + 1) / 24.0, 6, Color(Style.INK, 0.55 * fade), 5.0, true)
		draw_arc(center, mark + TOLERANCE, 0.0, TAU, 48, Color(Style.INK, 0.1 * fade), 2.0, true)
		draw_arc(center, mark - TOLERANCE, 0.0, TAU, 48, Color(Style.INK, 0.1 * fade), 2.0, true)
	# После итога метка показывается снова: видно, насколько ошибся.
	if rest > 0.0:
		draw_arc(center, mark, 0.0, TAU, 48, Color(Style.SUCCESS if _last_ok else Style.DANGER, 0.7), 5.0, true)
	if not (_popped and rest > 0.0):
		# Шар: дрожит, пока растёт, вздрагивает от удачи; нитка вниз.
		var r := radius * (clampf(1.0 + _pop.value * 0.03, 0.8, 1.25) if jelly else 1.0)
		var squash := clampf(_wobble.value * 0.012, -0.06, 0.06) if jelly else 0.0
		var color := Style.accent(balloon % 2)
		draw_line(center + Vector2(0.0, r), center + Vector2(sin(age * 3.0) * 10.0, r + 70.0), Color(Style.INK, 0.35), 3.0, true)
		draw_set_transform(center + Vector2(0.0, 8.0), 0.0, Vector2(1.0 + squash, 1.0 - squash))
		draw_circle(Vector2.ZERO, r, Color(Style.INK, 0.12))
		draw_set_transform(center, 0.0, Vector2(1.0 + squash, 1.0 - squash))
		draw_circle(Vector2.ZERO, r, color)
		draw_circle(Vector2(-r * 0.32, -r * 0.34), r * 0.2, Color(1.0, 1.0, 1.0, 0.5))
		draw_colored_polygon(PackedVector2Array([Vector2(-9.0, r - 2.0), Vector2(9.0, r - 2.0), Vector2(0.0, r + 14.0)]), color.darkened(0.15))
		draw_set_transform(Vector2.ZERO)
	if jelly:
		_splash.draw_air(self, Vector2.ZERO)
	_draw_dots()


## Кружки шаров сверху по центру: удачные `success`, лопнувшие `danger`.
func _draw_dots() -> void:
	var y := 40.0 + AspectIcon.SIZE / 2.0
	var x0 := size.x / 2.0 - (BALLOONS - 1) * DOT_GAP / 2.0
	for i in BALLOONS:
		var c := Color(Style.INK, 0.12)
		if i < results.size():
			c = Style.SUCCESS if results[i] else Style.DANGER
		var r := DOT_R * (1.3 if i == balloon and running else 1.0)
		r *= clampf(1.0 + _dots[i].value, 0.5, 1.8)
		draw_circle(Vector2(x0 + i * DOT_GAP, y), r, c)
