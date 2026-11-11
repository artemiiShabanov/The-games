extends Minigame
## «Разгони» (mash, технология ASCII), каталог `docs/specs/minigames_catalog.md`. Бегунок на
## полосе привязан резинкой к столбику на старте: резинка тянет назад тем сильнее, чем дальше он
## ушёл. Каждое нажатие стрелки в другую сторону, чем прошлое (← → ← →), толкает его вперёд;
## та же стрелка дважды не толкает. Дотянуть до финиша до таймера, иначе провал «не дотянул».
## Образ технологии: клавиши ← → крупно под полосой, следующая подсвечена, за бегунком след
## из `»` моноширинным шрифтом. Параметры от `t` в `resources/minigames/mash.tres`: pull
## (жёсткость резинки), finish (финиш долей полосы).
## Мармелад: бегунок мягкое тело, от толчка вздрагивает и наклоняется вперёд, клавиши
## поджимаются от нажатия, резинка толстеет и краснеет от натяжения; на финише брызги, на
## провале резинка утаскивает бегунка к столбику.
## Мышь (#83): левая кнопка ←, правая →, чередовать.

const TRACK_W := 1200.0
const TRACK_H := 72.0
const RUNNER_R := 30.0
## Толчок от нажатия (скорость в долях полосы в секунду) и вязкость.
const IMPULSE := 0.06
const DRAG := 1.6
const KEY_SIZE := Vector2(132, 112)
const TRAIL_STEP := 40.0
## Бот: нажатий в секунду, WIN и LOSE.
const BOT_RATE_WIN := 11.0
const BOT_RATE_LOSE := 4.0
const STEP_PITCHES := 8

var pull := 0.45
var finish_at := 0.6
## Позиция 0..1 вдоль полосы и скорость.
var pos := 0.0
var vel := 0.0
## Последняя стрелка: -1 ←, 1 →, 0 ещё не жали.
var last_dir := 0
var presses := 0

var _steps: Array[AudioStreamPlayer] = []
var _miss: AudioStreamPlayer
var _win: AudioStreamPlayer
var _runner: JellyShape
var _key_springs: Array[JellySpring] = [JellySpring.new(), JellySpring.new()]
var _lean := JellySpring.new()
var _rings := RingFx.new()
var _splash := SplashFx.new()
var _outcome := 0
var _end_age := 0.0
var _end_from := 0.0
var _bot_timer := 0.0
var _bot_dir := -1


func _on_start() -> void:
	pull = maxf(def.param(&"pull", t, 0.45), 0.05)
	finish_at = clampf(def.param(&"finish", t, 0.6), 0.2, 0.95)
	for i in STEP_PITCHES:
		var p := Sfx.player(Sfx.blip(330.0 * pow(2.0, i / 7.0), 0.05, 0.22, 40.0))
		add_child(p)
		_steps.append(p)
	_miss = Sfx.player(Sfx.thud(0.06, 0.2))
	_win = Sfx.player(Sfx.blip(990.0, 0.3, 0.45, 8.0))
	add_child(_miss)
	add_child(_win)
	_runner = JellyShape.circle(RUNNER_R)
	_runner.snap(_runner_pos())
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if not running:
		return
	if event.is_action_pressed(GameInput.LEFT):
		_press(-1)
	elif event.is_action_pressed(GameInput.RIGHT):
		_press(1)


func _mouse_action(button: MouseButton, _pos: Vector2) -> StringName:
	match button:
		MOUSE_BUTTON_LEFT:
			return GameInput.LEFT
		MOUSE_BUTTON_RIGHT:
			return GameInput.RIGHT
	return &""


## Нажатие стрелки: другая, чем прошлая, толкает вперёд; та же дважды только стукает.
func _press(dir: int) -> void:
	_key_springs[0 if dir < 0 else 1].kick(-260.0)
	if dir == last_dir:
		_miss.play()
		if _runner != null:
			_runner.push(Vector2(-40.0, 0.0), Vector2.RIGHT)
		return
	last_dir = dir
	presses += 1
	vel += IMPULSE
	_steps[clampi(int(pos / finish_at * STEP_PITCHES), 0, STEP_PITCHES - 1)].play()
	if _runner != null:
		_runner.push(Vector2(160.0, 0.0), Vector2.LEFT)
		_lean.kick(220.0)


func _on_tick(delta: float) -> void:
	vel += (-pull * pos - DRAG * vel) * delta
	pos += vel * delta
	if pos < 0.0:
		pos = 0.0
		vel = maxf(vel, 0.0)
	if pos >= finish_at:
		pos = finish_at
		_win.play()
		finish(true)
		return
	queue_redraw()


## Время вышло: не дотянул.
func _on_timeout() -> bool:
	return false


## Бот жмёт ← → по очереди с темпом режима: WIN успевает, LOSE нет.
func _bot_step(delta: float) -> bool:
	_bot_timer -= delta
	if _bot_timer <= 0.0:
		_bot_timer += 1.0 / (BOT_RATE_WIN if AutoTest.bot_mode == AutoTest.BotMode.WIN else BOT_RATE_LOSE)
		_bot_dir = -_bot_dir
		tap_action(GameInput.LEFT if _bot_dir < 0 else GameInput.RIGHT)
	return false


func _on_finish(success: bool) -> void:
	_outcome = 1 if success else -1
	_end_age = 0.0
	_end_from = pos
	if _runner == null:
		return
	var at := _runner_pos()
	if success:
		_runner.poke(260.0)
		_rings.add(at, RUNNER_R, RUNNER_R * 2.6, Color(Style.SUCCESS, 0.35), 2, 0.6)
		_splash.burst(at, 10, 560.0, 0.0, 1.2, Color(Style.accent(2), 0.8), 3.0, 7.0)
	else:
		_runner.poke(-200.0)


# --- Геометрия и мармелад ---------------------------------------------------------------------

func _track_rect() -> Rect2:
	return Rect2(size.x / 2.0 - TRACK_W / 2.0, size.y / 2.0 - TRACK_H / 2.0 - 60.0, TRACK_W, TRACK_H)


## Где бегунок по позиции; после провала резинка утаскивает его к столбику.
func _shown_pos() -> float:
	if _outcome < 0:
		var e := 1.0 - pow(1.0 - clampf(_end_age / 0.45, 0.0, 1.0), 3.0)
		return lerpf(_end_from, 0.0, e)
	return pos


func _runner_pos() -> Vector2:
	var r := _track_rect()
	var x0 := r.position.x + RUNNER_R + 12.0
	var x1 := r.end.x - RUNNER_R - 12.0
	return Vector2(lerpf(x0, x1, _shown_pos()), r.get_center().y)


func _post_pos() -> Vector2:
	var r := _track_rect()
	return Vector2(r.position.x + 12.0, r.get_center().y)


func _key_rect(i: int) -> Rect2:
	var r := _track_rect()
	var gap := 32.0
	var x := size.x / 2.0 - KEY_SIZE.x - gap / 2.0 + i * (KEY_SIZE.x + gap)
	return Rect2(Vector2(x, r.end.y + 96.0), KEY_SIZE)


func _process(delta: float) -> void:
	super(delta)
	if _runner == null or paused or def == null:
		return
	if _outcome != 0:
		_end_age += delta
	var tu := Jelly.tuning()
	for s in _key_springs:
		s.step(delta, tu.spring_stiffness, tu.spring_damping)
	_lean.step(delta, tu.spring_stiffness, tu.spring_damping)
	_runner.follow(delta, _runner_pos(), clampf(_lean.value / 1600.0, -0.25, 0.25))
	_rings.step(delta)
	_splash.step(delta, func(_x: float) -> float: return INF)
	if not running:
		queue_redraw()


# --- Рисование --------------------------------------------------------------------------------

func _draw() -> void:
	if def == null:
		return
	var ci := get_canvas_item()
	var r := _track_rect()
	var jelly := Jelly.on() and _runner != null
	Style.flat(Style.SURFACE_2, Style.R_PILL, Color.TRANSPARENT, 0).draw(ci, r)
	var rp := _runner_pos()
	# Пройденное заливкой.
	var filled := Rect2(r.position, Vector2(rp.x - r.position.x + RUNNER_R, r.size.y))
	Style.flat(Color(Style.accent(0), 0.18), Style.R_PILL, Color.TRANSPARENT, 0).draw(ci, filled)
	# Финиш: шашечки поперёк полосы.
	var fx := lerpf(r.position.x + RUNNER_R + 12.0, r.end.x - RUNNER_R - 12.0, finish_at) + RUNNER_R
	var cell := r.size.y / 6.0
	for j in 6:
		for k in 2:
			if (j + k) % 2 == 0:
				draw_rect(Rect2(fx + k * cell, r.position.y + j * cell, cell, cell), Style.INK)
	# Резинка от столбика: толще и краснее с натяжением.
	var stretch := clampf(_shown_pos() / finish_at, 0.0, 1.0)
	var post := _post_pos()
	draw_line(post, rp, Style.INK_3.lerp(Style.DANGER, stretch * 0.8), lerpf(3.0, 9.0, stretch), true)
	draw_circle(post, 10.0, Style.INK)
	# След из «»» моноширинным шрифтом поверх резинки: гуще, чем быстрее бегунок.
	var mono := Style.mono_font()
	var n := int((rp.x - r.position.x - RUNNER_R) / TRAIL_STEP)
	for i in n:
		var x := rp.x - RUNNER_R - (i + 1) * TRAIL_STEP
		var a := clampf(vel * 6.0, 0.0, 0.9) * (1.0 - float(i) / maxf(n, 1.0))
		if a > 0.02:
			draw_string(mono, Vector2(x, r.get_center().y + Style.FONT_H1 * 0.35), "»", HORIZONTAL_ALIGNMENT_LEFT, -1, Style.FONT_H1, Color(Style.INK_2, a))
	# Бегунок.
	var color := Style.accent(0)
	if _outcome < 0:
		color = color.lerp(Style.INK_3, clampf(_end_age / 0.4, 0.0, 1.0))
	if jelly:
		_rings.draw(self)
		_runner.draw(self, color)
		_splash.draw_air(self, Vector2.ZERO)
	else:
		draw_circle(rp, RUNNER_R, color)
	# Клавиши ← →: следующая залита, нажатая поджимается.
	for i in 2:
		var kr := _key_rect(i)
		var squish := clampf(_key_springs[i].value, -40.0, 30.0) if Jelly.on() else 0.0
		kr = kr.grow_individual(0.0, -squish * 0.3, 0.0, 0.0)
		var next := last_dir == 0 or (i == 0) == (last_dir > 0)
		var fill := Style.INK if next and running else Style.SURFACE_2
		Style.flat(fill, Style.R_CTL, Color.TRANSPARENT, 0).draw(ci, kr)
		var glyph := "←" if i == 0 else "→"
		var size_px := Style.FONT_H1
		var w := mono.get_string_size(glyph, HORIZONTAL_ALIGNMENT_LEFT, -1, size_px).x
		draw_string(mono, Vector2(kr.get_center().x - w / 2.0, kr.get_center().y + size_px * 0.35), glyph,
				HORIZONTAL_ALIGNMENT_LEFT, -1, size_px, Style.SURFACE_SOLID if next and running else Style.INK)
