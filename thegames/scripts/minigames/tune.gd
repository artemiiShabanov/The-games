extends Minigame
## «Настрой волну» (tune, звук), каталог `docs/specs/minigames_catalog.md`. Две волны наложены
## друг на друга: эталон и своя. Влево и вправо меняют частоту своей, вверх и вниз амплитуду,
## шагами; при совпадении волны сливаются в одну и A фиксирует. A без совпадения трясёт волну
## и блокирует кнопку на миг. Четыре волны за раунд; провал, если к таймеру совпало меньше
## трёх. Обе волны звучат: своя и эталон как два тона, при сближении слышны биения.
## Параметры от `t` в `resources/minigames/tune.tres`: offset (на сколько шагов эталон дальше
## от стартового положения), two_axes (вероятность, что отличается и амплитуда), tolerance
## (допуск в шагах).
## Мармелад: своя волна как мармеладная струна, рисуется по частоте и амплитуде на пружинах, так
## что после шага догоняет новую форму с недолётом и коротким качанием и чуть выгибается
## серединой; промах сплющивает и толкает её вбок, совпадение раздувает слитую волну и брызгает
## мягкими каплями цвета успеха с нескольких гребней. Точки волн мягкие, текущая стоит на бортике,
## засчитанная вздрагивает с кругом и каплей-другой. Геймплей на настоящих числах.

const WAVES := 4
const NEED := 3
const FREQ_MIN := 2.0
const FREQ_MAX := 10.0
const FREQ_STEP := 0.5
const AMP_MIN := 32.0
const AMP_MAX := 192.0
const AMP_STEP := 16.0
const LINE_WIDTH := 6.0
const SEGMENTS := 160
const SHAKE_SECONDS := 0.3
const LOCK_SECONDS := 0.4
const MERGE_SECONDS := 0.35
const BOT_STEP := 0.14
const HZ_BASE := 180.0
const HZ_PER_CYCLE := 36.0
const TONE_VOLUME := 0.18
const DOT_R := 7.0
const DOT_GAP := 28.0
const SPLASH_CRESTS := 5

## Мышь: сколько пикселей ведения на шаг частоты и амплитуды, и сдвиг, после которого клик уже
## ведение, а не фиксация.
const DRAG_FREQ_PX := 36.0
const DRAG_AMP_PX := 24.0
const CLICK_SLOP := 10.0

var offset_steps := 3
var two_axes := 0.0
var tolerance := 1

var wave_index := 0
var matches := 0
var ref_freq := 4.0
var ref_amp := 96.0
var freq := 4.0
var amp := 96.0
var shake := 0.0
var lock := 0.0
var merge := 0.0
var done_this := false
var _drag := false
var _drag_acc := Vector2.ZERO
var _drag_moved := false
var _bot_timer := 0.0
var _player: AudioStreamPlayer
var _playback: AudioStreamGeneratorPlayback
var _phase_ref := 0.0
var _phase_own := 0.0
var _ok_sound: AudioStreamPlayer
var _miss_sound: AudioStreamPlayer
# Мармелад: только рисование, геймплей на freq и amp.
var _jelly_freq := JellySpring.new()
var _jelly_amp := JellySpring.new()
var _jelly_bend := JellySpring.new()
var _jelly_swell := JellySpring.new()
var _jelly_side := JellySpring.new()
var _jelly_dots: Array[JellyShape] = []
var _jelly_rings := RingFx.new()
var _jelly_splash := SplashFx.new()
var _jelly_side_dir := 1.0


func _on_start() -> void:
	offset_steps = maxi(int(round(def.param(&"offset", t, 3.0))), 1)
	two_axes = def.param(&"two_axes", t, 0.0)
	tolerance = maxi(int(round(def.param(&"tolerance", t, 1.0))), 0)
	_ok_sound = Sfx.player(Sfx.blip(880.0, 0.18, 0.45, 12.0))
	_miss_sound = Sfx.player(Sfx.thud(0.14, 0.45))
	add_child(_ok_sound)
	add_child(_miss_sound)
	var gen := AudioStreamGenerator.new()
	gen.mix_rate = 22050.0
	gen.buffer_length = 0.12
	_player = AudioStreamPlayer.new()
	_player.stream = gen
	_player.volume_db = -6.0
	add_child(_player)
	_player.play()
	_playback = _player.get_stream_playback() as AudioStreamGeneratorPlayback
	_new_wave()
	for j in WAVES:
		_jelly_dots.append(JellyShape.circle(DOT_R, 20))
	queue_redraw()


func _new_wave() -> void:
	done_this = false
	merge = 0.0
	# Своя волна стартует в середине диапазонов, эталон на offset шагов в сторону.
	freq = snappedf((FREQ_MIN + FREQ_MAX) / 2.0 + rng.randi_range(-2, 2) * FREQ_STEP, FREQ_STEP)
	amp = snappedf((AMP_MIN + AMP_MAX) / 2.0 + rng.randi_range(-2, 2) * AMP_STEP, AMP_STEP)
	var dir := 1 if rng.randf() < 0.5 else -1
	ref_freq = clampf(freq + dir * offset_steps * FREQ_STEP, FREQ_MIN, FREQ_MAX)
	if is_equal_approx(ref_freq, freq):
		ref_freq = clampf(freq - dir * offset_steps * FREQ_STEP, FREQ_MIN, FREQ_MAX)
	ref_amp = amp
	if rng.randf() < two_axes:
		var adir := 1 if rng.randf() < 0.5 else -1
		ref_amp = clampf(amp + adir * maxi(offset_steps - 1, 1) * AMP_STEP, AMP_MIN, AMP_MAX)
		if is_equal_approx(ref_amp, amp):
			ref_amp = clampf(amp - adir * maxi(offset_steps - 1, 1) * AMP_STEP, AMP_MIN, AMP_MAX)
	# Новая волна не перетекает из прошлой, а встаёт сразу.
	_jelly_freq.value = freq
	_jelly_freq.velocity = 0.0
	_jelly_amp.value = amp
	_jelly_amp.velocity = 0.0
	_jelly_bend.value = 0.0
	_jelly_bend.velocity = 0.0


func matched() -> bool:
	return absf(freq - ref_freq) <= tolerance * FREQ_STEP + 0.001 and absf(amp - ref_amp) <= tolerance * AMP_STEP + 0.001


func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	if event.is_action_pressed(GameInput.LEFT):
		_adjust(-FREQ_STEP, 0.0)
	elif event.is_action_pressed(GameInput.RIGHT):
		_adjust(FREQ_STEP, 0.0)
	elif event.is_action_pressed(GameInput.UP):
		_adjust(0.0, AMP_STEP)
	elif event.is_action_pressed(GameInput.DOWN):
		_adjust(0.0, -AMP_STEP)
	elif GameInput.is_a(event):
		_fix()
	else:
		return
	get_viewport().set_input_as_handled()


## Мышь (#83): ведёшь с зажатой кнопкой, как крутишь ручку: вбок частота, вверх-вниз амплитуда,
## шаг на каждые `DRAG_FREQ_PX` и `DRAG_AMP_PX`; клик без ведения фиксирует, как ␣; колесо
## амплитуда.
func _on_mouse(event: InputEventMouse) -> bool:
	var w := MouseUi.wheel(event)
	if w != 0:
		tap_action(GameInput.UP if w < 0 else GameInput.DOWN)
		return true
	var b := event as InputEventMouseButton
	if b != null and b.button_index == MOUSE_BUTTON_LEFT:
		if b.pressed:
			_drag = true
			_drag_acc = Vector2.ZERO
			_drag_moved = false
		elif _drag:
			_drag = false
			if not _drag_moved:
				tap_action(GameInput.A)
		return true
	var m := event as InputEventMouseMotion
	if m == null or not _drag:
		return false
	_drag_acc += m.relative
	if _drag_acc.length() > CLICK_SLOP:
		_drag_moved = true
	while absf(_drag_acc.x) >= DRAG_FREQ_PX:
		tap_action(GameInput.RIGHT if _drag_acc.x > 0.0 else GameInput.LEFT)
		_drag_acc.x -= signf(_drag_acc.x) * DRAG_FREQ_PX
	while absf(_drag_acc.y) >= DRAG_AMP_PX:
		tap_action(GameInput.DOWN if _drag_acc.y > 0.0 else GameInput.UP)
		_drag_acc.y -= signf(_drag_acc.y) * DRAG_AMP_PX
	return true


func _adjust(df: float, da: float) -> void:
	if done_this:
		return
	var was_freq := freq
	var was_amp := amp
	freq = clampf(snappedf(freq + df, FREQ_STEP), FREQ_MIN, FREQ_MAX)
	amp = clampf(snappedf(amp + da, AMP_STEP), AMP_MIN, AMP_MAX)
	# Струна выгибается серединой в сторону шага; упёрлась в край — лёгкий вздрог.
	if not is_equal_approx(was_freq, freq) or not is_equal_approx(was_amp, amp):
		_jelly_bend.kick(140.0 * (signf(df) if df != 0.0 else -signf(da)))
	else:
		_jelly_swell.kick(-1.2)
	queue_redraw()


func _fix() -> void:
	if done_this or lock > 0.0:
		return
	if matched():
		done_this = true
		matches += 1
		merge = MERGE_SECONDS
		_ok_sound.play()
		_jelly_swell.kick(4.0)
		if wave_index < _jelly_dots.size():
			_jelly_dots[wave_index].poke(260.0)
			_jelly_rings.add(_dot_pos(wave_index), DOT_R, DOT_R * 3.2, Color(Style.SUCCESS, 0.5), 1, 0.6)
			if Jelly.on():
				_jelly_splash.pop(_dot_pos(wave_index), Color(Style.SUCCESS, 0.7), 1, 170.0, 0.35)
		if Jelly.on():
			_splash_crests()
	else:
		shake = SHAKE_SECONDS
		lock = LOCK_SECONDS
		_miss_sound.play()
		# Сторона толчка чередуется: общий rng не трогаем, он геймплейный.
		_jelly_side_dir = -_jelly_side_dir
		_jelly_side.kick(320.0 * _jelly_side_dir)
		_jelly_swell.kick(-3.0)


func _on_tick(delta: float) -> void:
	shake = maxf(shake - delta, 0.0)
	lock = maxf(lock - delta, 0.0)
	if done_this:
		merge -= delta
		if merge <= 0.0:
			wave_index += 1
			if wave_index >= WAVES:
				finish(matches >= NEED)
				return
			_new_wave()
			_jelly_dots[wave_index].poke(180.0)
	_push_audio()
	queue_redraw()


func _on_timeout() -> bool:
	return matches >= NEED


func _on_finish(_success: bool) -> void:
	if _player != null:
		_player.stop()


## Два тона: эталон и свой, громкость по амплитуде; при близких частотах слышны биения.
func _push_audio() -> void:
	if _playback == null:
		return
	var rate := 22050.0
	var f_ref := HZ_BASE + ref_freq * HZ_PER_CYCLE
	var f_own := HZ_BASE + freq * HZ_PER_CYCLE
	var v_ref := TONE_VOLUME * ref_amp / AMP_MAX
	var v_own := TONE_VOLUME * amp / AMP_MAX
	var frames := _playback.get_frames_available()
	for i in frames:
		_phase_ref = fmod(_phase_ref + f_ref / rate, 1.0)
		_phase_own = fmod(_phase_own + f_own / rate, 1.0)
		var s := v_ref * sin(_phase_ref * TAU) + v_own * sin(_phase_own * TAU)
		_playback.push_frame(Vector2(s, s))


## Бот: WIN шагает к эталону по частоте, потом по амплитуде, затем A; LOSE ничего не делает.
func _bot_step(delta: float) -> bool:
	if AutoTest.bot_mode != AutoTest.BotMode.WIN or done_this:
		return false
	_bot_timer += delta
	if _bot_timer < BOT_STEP:
		return false
	_bot_timer = 0.0
	if absf(freq - ref_freq) > 0.001:
		_adjust(FREQ_STEP * signf(ref_freq - freq), 0.0)
	elif absf(amp - ref_amp) > 0.001:
		_adjust(0.0, AMP_STEP * signf(ref_amp - amp))
	else:
		_fix()
	return false


# --- Мармелад ----------------------------------------------------------------------------

## Пружины рисования догоняют настоящие числа; живут и после финиша, на паузе стоят. Без
## движения мармелада рисуются настоящие числа.
func _process(delta: float) -> void:
	super(delta)
	if paused or _jelly_dots.is_empty():
		return
	var tu := Jelly.tuning()
	# Плотнее предметов: шаг частоты сдвигает весь хвост волны, недолёт должен быть коротким.
	var k := tu.spring_stiffness
	var d := tu.spring_damping * 2.0
	if Jelly.on():
		_jelly_freq.step(delta, k, d, freq)
		_jelly_amp.step(delta, k, d, amp)
		_jelly_bend.step(delta, k, d)
		_jelly_swell.step(delta, k, d)
		_jelly_side.step(delta, k, d)
	else:
		for sp: JellySpring in [_jelly_freq, _jelly_amp, _jelly_bend, _jelly_swell, _jelly_side]:
			sp.velocity = 0.0
			sp.value = 0.0
		_jelly_freq.value = freq
		_jelly_amp.value = amp
	_jelly_rings.step(delta)
	_jelly_splash.step(delta, Callable())
	for j in _jelly_dots.size():
		_jelly_dots[j].follow(delta, _dot_pos(j))
	if not running:
		queue_redraw()


## Слитая волна брызгает с гребней: до SPLASH_CRESTS верхушек, равномерно по ширине, по 2–3
## мягкие капли с каждой. Фаза та же, что у рисования, чтобы капли срывались с самого гребня.
func _splash_crests() -> void:
	var phase := elapsed * 2.0
	var crests: Array[float] = []
	# Верхушка там, где sin = −1 (y вниз): u·f·TAU + phase = −PI/2 + TAU·n.
	var n := ceili((phase + PI / 2.0) / TAU)
	while true:
		var u := (-PI / 2.0 - phase + TAU * n) / (ref_freq * TAU)
		if u > 0.97:
			break
		if u >= 0.03:
			crests.append(u)
		n += 1
	if crests.is_empty():
		return
	var count := mini(crests.size(), SPLASH_CRESTS)
	var pts := _wave_points(ref_freq, ref_amp, phase, 0.0)
	for i in count:
		var idx := int(round(float(i) * (crests.size() - 1) / maxf(count - 1, 1.0))) if count > 1 else crests.size() >> 1
		var at := pts[clampi(int(round(crests[idx] * SEGMENTS)), 0, SEGMENTS)]
		_jelly_splash.pop(at, Color(Style.SUCCESS, 0.9), 4, 300.0, 0.55)


func _dot_pos(j: int) -> Vector2:
	return Vector2(size.x - 48.0 - (WAVES - 1) * DOT_GAP + j * DOT_GAP, 60.0)


# --- Рисование ----------------------------------------------------------------------------

## Точки волны; `bend` выгибает середину (концы на месте), как дёрнутую струну.
func _wave_points(f: float, a: float, phase: float, dx: float, bend := 0.0) -> PackedVector2Array:
	var pts := PackedVector2Array()
	var left := 96.0
	var width := size.x - 192.0
	var mid := size.y * 0.5 + 10.0
	for i in SEGMENTS + 1:
		var u := float(i) / SEGMENTS
		pts.append(Vector2(left + u * width + dx, mid + sin(u * f * TAU + phase) * a + sin(u * PI) * bend))
	return pts


func _draw() -> void:
	if def == null:
		return
	var is_match := matched()
	var dx := sin(shake * 60.0) * 10.0 * shake / SHAKE_SECONDS if shake > 0.0 else 0.0
	# Мармелад: своя волна по частоте и амплитуде на пружинах, промах толкает её пружиной вбок.
	var swell := 1.0
	var own_freq := freq
	var own_amp := amp
	var bend := 0.0
	if Jelly.on() and not _jelly_dots.is_empty():
		dx = _jelly_side.value
		swell = maxf(1.0 + _jelly_swell.value, 0.3)
		own_freq = _jelly_freq.value
		own_amp = _jelly_amp.value
		bend = _jelly_bend.value
	# Эталон: тонкая вторая волна акцентом a2; своя: a1. При совпадении одна толстая success.
	if done_this or is_match:
		var k := clampf(merge / MERGE_SECONDS, 0.0, 1.0) if done_this else 0.0
		var color := Style.SUCCESS if done_this else Style.accent(0)
		var merged := _wave_points(ref_freq, ref_amp * swell, elapsed * 2.0, 0.0)
		draw_polyline(merged, Color(color, 0.35), LINE_WIDTH * (2.0 + 2.0 * k), true)
		draw_polyline(merged, color, LINE_WIDTH, true)
	else:
		draw_polyline(_wave_points(ref_freq, ref_amp, elapsed * 2.0, 0.0), Color(Style.accent(1), 0.8), LINE_WIDTH, true)
		draw_polyline(_wave_points(own_freq, own_amp * swell, elapsed * 2.0, dx, bend), Style.accent(0), LINE_WIDTH, true)
	_jelly_splash.draw_air(self, Vector2.ZERO)
	# Подписи осей снизу: частота и амплитуда своей волны против эталона не раскрываются.
	var font := get_theme_default_font()
	var caption := "частота ← →   амплитуда ↑ ↓"
	var w := font.get_string_size(caption, HORIZONTAL_ALIGNMENT_LEFT, -1, Style.FONT_CAPTION).x
	draw_string(font, Vector2(size.x / 2.0 - w / 2.0, size.y - 110.0), caption, HORIZONTAL_ALIGNMENT_LEFT, -1, Style.FONT_CAPTION, Style.INK_3)
	# Волны справа сверху: мягкие точки, текущая на бортике.
	_jelly_rings.draw(self)
	var lift := Jelly.tuning().lift_px * 0.4
	for j in WAVES:
		var c := Style.SURFACE_2
		if j < wave_index or (j == wave_index and done_this):
			c = Style.SUCCESS
		elif j == wave_index:
			c = Style.INK
		if j < _jelly_dots.size():
			_jelly_dots[j].draw_lifted(self, c, lift if j == wave_index and not done_this else 0.0)
		else:
			draw_circle(_dot_pos(j), DOT_R, c)
