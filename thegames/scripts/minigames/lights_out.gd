extends Minigame
## «Старт» (lights_out, гонки), каталог `docs/specs/minigames_catalog.md`. Ряд из пяти огней
## зажигается по одному, как на старте гонки, после случайной паузы все гаснут: ␣ как можно
## быстрее. Нажал, пока горит хоть один огонь, фальстарт, раунд сгорел. Реакция дольше порога
## `slow` или нет нажатия за `WAIT_MAX` после гашения: медленно. 5 раундов, провал при 2
## фальстартах или 2 медленных. Ложное мигание (с ростом `t`): один огонь на миг гаснет, пока
## остальные горят; нажал в мигание, тоже фальстарт.
## Нажатие между раундами (пока ряд пуст перед зажиганием и на показе результата) не считается.
## Таймер страховочный: раунды идут сами и укладываются в него; если он всё же кончился,
## несыгранные раунды не штрафуются.
## Параметры от `t` в `resources/minigames/lights_out.tres`: hold_min, hold_max (пауза перед
## гашением, разброс растёт), slow (порог медленной реакции, с), blink_chance (вероятность
## ложных миганий в раунде), blinks (сколько миганий самое большее).
## Мармелад (STYLE «Мармелад»): огни мягкие `JellyShape`, зажигаясь, вздрагивают и чуть
## вырастают, гаснут со сжатием; хорошая реакция брызгает неяркими каплями цвета огней и
## расходится кругом, фальстарт красит горящие огни `danger` и трясёт табло, медленная серым
## числом; кружки раундов подпрыгивают.

enum Phase { LEAD, LIGHTING, HOLD, OUT, RESULT, DONE }
enum Outcome { PENDING, OK, SLOW, FALSE_START }

const LIGHTS := 5
const ROUNDS := 5
const MAX_FALSE := 2
const MAX_SLOW := 2
## Пустой ряд перед первым огнём раунда, с.
const LEAD_SECONDS := 0.4
## Шаг зажигания огней, с.
const LIGHT_STEP := 0.3
## Сколько ждать нажатия после гашения, потом раунд медленный.
const WAIT_MAX := 1.0
## Показ результата раунда, с.
const RESULT_SECONDS := 0.6
## Ложное мигание: огонь не горит столько, с.
const BLINK_SECONDS := 0.16
## Мигание не ближе этого к началу паузы и к гашению, с.
const BLINK_MARGIN := 0.25
const BLINK_TAIL := 0.4
const SHAKE_SECONDS := 0.35
const LIGHT_R := 60.0
const LIGHT_GAP := 40.0
const HOUSING_PAD := 28.0
const DOT_R := 12.0
const DOT_GAP := 44.0
const BOT_REACTION := 0.18
const NUMBER_SIZE := 72
const UNIT_SIZE := 44

var hold_min := 0.4
var hold_max := 1.4
var slow := 0.4
var blink_chance := 0.0
var max_blinks := 1

var phase := Phase.LEAD
var phase_time := 0.0
var round_index := 0
var lit := 0
var hold := 1.0
## Время ложных миганий от начала паузы и какой огонь мигает.
var blink_at: Array[float] = []
var blink_light: Array[int] = []
var outcomes: Array[Outcome] = []
var reactions: Array[float] = []
var false_starts := 0
var slows := 0
var out_time := 0.0
var shake := 0.0

var _light_sound: AudioStreamPlayer
var _go_sound: AudioStreamPlayer
var _miss_sound: AudioStreamPlayer

# Мармелад: только рисование, на игру не влияет.
var _lamps: Array[JellyShape] = []
var _was_on: Array[bool] = []
var _dots: Array[JellySpring] = []
var _rings := RingFx.new()
var _splash := SplashFx.new()
var _bot_pressed := false


func _on_start() -> void:
	hold_min = def.param(&"hold_min", t, 0.4)
	hold_max = maxf(def.param(&"hold_max", t, 1.4), hold_min)
	slow = def.param(&"slow", t, 0.4)
	blink_chance = def.param(&"blink_chance", t, 0.0)
	max_blinks = maxi(1, roundi(def.param(&"blinks", t, 1.0)))
	_light_sound = MiniSfx.tap(520.0)
	_go_sound = MiniSfx.hit(440.0)
	_miss_sound = MiniSfx.miss()
	add_child(_light_sound)
	add_child(_go_sound)
	add_child(_miss_sound)
	for i in ROUNDS:
		outcomes.append(Outcome.PENDING)
		reactions.append(-1.0)
		_dots.append(JellySpring.new())
	for i in LIGHTS:
		_lamps.append(JellyShape.circle(LIGHT_R, 40))
		_was_on.append(false)
	_enter(Phase.LEAD)
	queue_redraw()


func _enter(p: Phase) -> void:
	phase = p
	phase_time = 0.0
	match p:
		Phase.LEAD:
			lit = 0
			_bot_pressed = false
		Phase.HOLD:
			hold = rng.randf_range(hold_min, hold_max)
			blink_at.clear()
			blink_light.clear()
			if rng.randf() < blink_chance:
				var n := rng.randi_range(1, max_blinks)
				# Миганию нужно место: пауза растягивается, но не дальше hold_max.
				hold = maxf(hold, minf(BLINK_MARGIN + BLINK_TAIL + BLINK_SECONDS * n * 2.0, maxf(hold_max, 0.9)))
				var room := hold - BLINK_MARGIN - BLINK_TAIL - BLINK_SECONDS
				if room > 0.0:
					for k in n:
						var at := BLINK_MARGIN + room * (k + rng.randf()) / n
						blink_at.append(at)
						blink_light.append(rng.randi_range(0, LIGHTS - 1))
		Phase.OUT:
			lit = 0
			out_time = elapsed


## Горит ли огонь `i` сейчас: зажжён по порядку и не в ложном мигании.
func light_on(i: int) -> bool:
	if phase == Phase.LIGHTING:
		return i < lit
	if phase == Phase.HOLD:
		for k in blink_at.size():
			if blink_light[k] == i and phase_time >= blink_at[k] and phase_time < blink_at[k] + BLINK_SECONDS:
				return false
		return true
	if phase == Phase.RESULT and outcomes[round_index] == Outcome.FALSE_START:
		return i < lit
	return false


func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	if GameInput.is_a(event):
		_press()
		get_viewport().set_input_as_handled()


func _press() -> void:
	match phase:
		Phase.LIGHTING, Phase.HOLD:
			_resolve(Outcome.FALSE_START, -1.0)
		Phase.OUT:
			var r := elapsed - out_time
			_resolve(Outcome.OK if r <= slow else Outcome.SLOW, r)


func _resolve(o: Outcome, reaction: float) -> void:
	outcomes[round_index] = o
	reactions[round_index] = reaction
	match o:
		Outcome.OK:
			_go_sound.play()
		Outcome.SLOW:
			slows += 1
			_miss_sound.play()
		Outcome.FALSE_START:
			false_starts += 1
			shake = SHAKE_SECONDS
			_miss_sound.play()
			if phase == Phase.HOLD:
				lit = LIGHTS
	_jelly_resolve(o)
	_enter(Phase.RESULT)


func _on_tick(delta: float) -> void:
	phase_time += delta
	shake = maxf(shake - delta, 0.0)
	match phase:
		Phase.LEAD:
			if phase_time >= LEAD_SECONDS:
				_enter(Phase.LIGHTING)
		Phase.LIGHTING:
			var want := mini(int(phase_time / LIGHT_STEP) + 1, LIGHTS)
			if want > lit:
				lit = want
				_light_sound.play()
			if phase_time >= LIGHT_STEP * LIGHTS:
				_enter(Phase.HOLD)
		Phase.HOLD:
			if phase_time >= hold:
				_enter(Phase.OUT)
		Phase.OUT:
			if elapsed - out_time > WAIT_MAX:
				_resolve(Outcome.SLOW, -1.0)
		Phase.RESULT:
			if phase_time >= RESULT_SECONDS:
				_next_round()
	queue_redraw()


func _next_round() -> void:
	if false_starts >= MAX_FALSE or slows >= MAX_SLOW:
		finish(false)
		return
	if round_index + 1 >= ROUNDS:
		finish(true)
		return
	round_index += 1
	_enter(Phase.LEAD)


## Страховка: несыгранные раунды не штрафуются.
func _on_timeout() -> bool:
	return false_starts < MAX_FALSE and slows < MAX_SLOW


func _on_finish(_success: bool) -> void:
	phase = Phase.DONE


## Бот: WIN жмёт через `BOT_REACTION` после гашения и не трогает мигания. LOSE в чётных раундах
## срывается на третьем огне (фальстарт), в нечётных не жмёт (медленно): провал за три раунда.
func _bot_step(_delta: float) -> bool:
	if _bot_pressed:
		return false
	if AutoTest.bot_mode == AutoTest.BotMode.WIN:
		if phase == Phase.OUT and elapsed - out_time >= BOT_REACTION:
			_bot_pressed = true
			_press()
	elif round_index % 2 == 0 and phase == Phase.LIGHTING and lit >= 3:
		_bot_pressed = true
		_press()
	return false


# --- Мармелад -----------------------------------------------------------------------------

func _jelly_resolve(o: Outcome) -> void:
	_dots[round_index].kick(14.0)
	if not Jelly.on():
		return
	var col := Style.accent(0)
	match o:
		Outcome.OK:
			for i in LIGHTS:
				_lamps[i].poke(220.0)
				_splash.pop(_light_pos(i) - Vector2(0.0, LIGHT_R - 8.0), col, 2, 420.0, 0.55)
				_rings.add(_light_pos(i), LIGHT_R, LIGHT_R + 34.0, Color(col, 0.45), 1, 0.45)
		Outcome.SLOW:
			for i in LIGHTS:
				_lamps[i].poke(-140.0)
		Outcome.FALSE_START:
			for i in LIGHTS:
				_lamps[i].push(Vector2(260.0, 0.0), Vector2.RIGHT)


## Мармелад живёт и после финиша, пока сцена на экране; на паузе стоит.
func _process(delta: float) -> void:
	super(delta)
	if _lamps.is_empty() or paused or def == null:
		return
	var tu := Jelly.tuning()
	for i in LIGHTS:
		var on := light_on(i)
		if on != _was_on[i]:
			_lamps[i].poke(260.0 if on else -200.0)
		_was_on[i] = on
		_lamps[i].follow(delta, _light_pos(i) + Vector2(_shake_x(), 0.0), 0.0, 1.0 if on else 0.9)
	for d in _dots:
		d.step(delta, tu.spring_stiffness, tu.spring_damping)
	_rings.step(delta)
	_splash.step(delta, Callable())
	if not running:
		queue_redraw()


func _shake_x() -> float:
	if shake <= 0.0:
		return 0.0
	return sin(shake * 45.0) * 14.0 * shake / SHAKE_SECONDS


# --- Рисование ----------------------------------------------------------------------------

func _row_center() -> Vector2:
	return Vector2(size.x / 2.0, size.y * 0.45)


func _light_pos(i: int) -> Vector2:
	var total := LIGHTS * LIGHT_R * 2.0 + (LIGHTS - 1) * LIGHT_GAP
	var c := _row_center()
	return Vector2(c.x - total / 2.0 + LIGHT_R + i * (LIGHT_R * 2.0 + LIGHT_GAP), c.y)


func _housing_rect() -> Rect2:
	var total := LIGHTS * LIGHT_R * 2.0 + (LIGHTS - 1) * LIGHT_GAP + HOUSING_PAD * 2.0
	var h := LIGHT_R * 2.0 + HOUSING_PAD * 2.0
	var c := _row_center()
	return Rect2(c.x - total / 2.0, c.y - h / 2.0, total, h)


func _lamp_color(i: int) -> Color:
	var on := light_on(i)
	if not on:
		return Color(Style.INK, 0.1)
	if phase == Phase.RESULT and outcomes[round_index] == Outcome.FALSE_START:
		return Style.DANGER
	return Style.accent(0)


func _draw() -> void:
	if def == null or _lamps.is_empty():
		return
	var jelly := Jelly.on()
	var housing := _housing_rect()
	housing.position.x += _shake_x()
	Style.flat(Style.SURFACE_2, Style.R_PILL, Color.TRANSPARENT, 0).draw(get_canvas_item(), housing)
	if jelly:
		_rings.draw(self)
	for i in LIGHTS:
		var col := _lamp_color(i)
		var p := _light_pos(i) + Vector2(_shake_x(), 0.0)
		if light_on(i):
			draw_circle(p, LIGHT_R + 14.0, Color(col, 0.16))
		if jelly:
			_lamps[i].draw(self, col)
		else:
			draw_circle(p, LIGHT_R * (1.0 if light_on(i) else 0.9), col)
	if jelly:
		_splash.draw_air(self, Vector2.ZERO)
	_draw_rounds(housing)
	_draw_reaction(housing)


## Кружки раундов над табло: впереди пустые, текущий крупнее, решённые своим цветом.
func _draw_rounds(housing: Rect2) -> void:
	var y := housing.position.y - 64.0
	var x0 := size.x / 2.0 - (ROUNDS - 1) * DOT_GAP / 2.0
	for i in ROUNDS:
		var c := Color(Style.INK, 0.12)
		match outcomes[i]:
			Outcome.OK:
				c = Style.SUCCESS
			Outcome.SLOW:
				c = Style.INK_3
			Outcome.FALSE_START:
				c = Style.DANGER
		var r := DOT_R
		if i == round_index and outcomes[i] == Outcome.PENDING and phase != Phase.DONE:
			r *= 1.3
		r *= clampf(1.0 + _dots[i].value, 0.5, 1.8)
		draw_circle(Vector2(x0 + i * DOT_GAP, y), r, c)


## Реакция раунда под табло: мс зелёным, медленная серым, фальстарт красным словом. Видна от
## решения раунда до первого огня следующего.
func _draw_reaction(housing: Rect2) -> void:
	var k := round_index
	if phase == Phase.LEAD or phase == Phase.LIGHTING:
		k = round_index - 1
		if phase == Phase.LIGHTING and lit > 0:
			return
	if k < 0 or k >= ROUNDS or outcomes[k] == Outcome.PENDING:
		return
	var y := housing.end.y + 112.0
	var font := get_theme_default_font()
	if outcomes[k] == Outcome.FALSE_START:
		_draw_centered(font, "фальстарт", Style.FONT_H1, Style.DANGER, y)
		return
	var col := Style.SUCCESS if outcomes[k] == Outcome.OK else Style.INK_3
	if reactions[k] < 0.0:
		_draw_centered(font, "—", Style.FONT_H1, col, y)
		return
	# Число моноширинным, «мс» основным шрифтом (в Menlo кириллица чужая).
	var mono := Style.mono_font()
	var num := str(roundi(reactions[k] * 1000.0))
	var unit := " мс"
	var nw := mono.get_string_size(num, HORIZONTAL_ALIGNMENT_LEFT, -1, NUMBER_SIZE).x
	var uw := font.get_string_size(unit, HORIZONTAL_ALIGNMENT_LEFT, -1, UNIT_SIZE).x
	var x := size.x / 2.0 - (nw + uw) / 2.0
	draw_string(mono, Vector2(x, y), num, HORIZONTAL_ALIGNMENT_LEFT, -1, NUMBER_SIZE, col)
	draw_string(font, Vector2(x + nw, y), unit, HORIZONTAL_ALIGNMENT_LEFT, -1, UNIT_SIZE, col)


func _draw_centered(font: Font, text: String, fsize: int, col: Color, y: float) -> void:
	var w := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fsize).x
	draw_string(font, Vector2(size.x / 2.0 - w / 2.0, y), text, HORIZONTAL_ALIGNMENT_LEFT, -1, fsize, col)
