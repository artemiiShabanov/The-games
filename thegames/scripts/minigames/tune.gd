extends Minigame
## «Настрой волну» (tune, звук), каталог `docs/specs/minigames_catalog.md`. Две волны наложены
## друг на друга: эталон и своя. Влево и вправо меняют частоту своей, вверх и вниз амплитуду,
## шагами; при совпадении волны сливаются в одну и A фиксирует. A без совпадения трясёт волну
## и блокирует кнопку на миг. Четыре волны за раунд; провал, если к таймеру совпало меньше
## трёх. Обе волны звучат: своя и эталон как два тона, при сближении слышны биения.
## Параметры от `t` в `resources/minigames/tune.tres`: offset (на сколько шагов эталон дальше
## от стартового положения), two_axes (вероятность, что отличается и амплитуда), tolerance
## (допуск в шагах).

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
var _bot_timer := 0.0
var _player: AudioStreamPlayer
var _playback: AudioStreamGeneratorPlayback
var _phase_ref := 0.0
var _phase_own := 0.0
var _ok_sound: AudioStreamPlayer
var _miss_sound: AudioStreamPlayer


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


func _adjust(df: float, da: float) -> void:
	if done_this:
		return
	freq = clampf(snappedf(freq + df, FREQ_STEP), FREQ_MIN, FREQ_MAX)
	amp = clampf(snappedf(amp + da, AMP_STEP), AMP_MIN, AMP_MAX)
	queue_redraw()


func _fix() -> void:
	if done_this or lock > 0.0:
		return
	if matched():
		done_this = true
		matches += 1
		merge = MERGE_SECONDS
		_ok_sound.play()
	else:
		shake = SHAKE_SECONDS
		lock = LOCK_SECONDS
		_miss_sound.play()


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


# --- Рисование ----------------------------------------------------------------------------

func _wave_points(f: float, a: float, phase: float, dx: float) -> PackedVector2Array:
	var pts := PackedVector2Array()
	var left := 96.0
	var width := size.x - 192.0
	var mid := size.y * 0.5 + 10.0
	for i in SEGMENTS + 1:
		var u := float(i) / SEGMENTS
		pts.append(Vector2(left + u * width + dx, mid + sin(u * f * TAU + phase) * a))
	return pts


func _draw() -> void:
	if def == null:
		return
	var is_match := matched()
	var dx := sin(shake * 60.0) * 10.0 * shake / SHAKE_SECONDS if shake > 0.0 else 0.0
	# Эталон: тонкая вторая волна акцентом a2; своя: a1. При совпадении одна толстая success.
	if done_this or is_match:
		var k := clampf(merge / MERGE_SECONDS, 0.0, 1.0) if done_this else 0.0
		var color := Style.SUCCESS if done_this else Style.accent(0)
		draw_polyline(_wave_points(ref_freq, ref_amp, elapsed * 2.0, 0.0), Color(color, 0.35), LINE_WIDTH * (2.0 + 2.0 * k), true)
		draw_polyline(_wave_points(ref_freq, ref_amp, elapsed * 2.0, 0.0), color, LINE_WIDTH, true)
	else:
		draw_polyline(_wave_points(ref_freq, ref_amp, elapsed * 2.0, 0.0), Color(Style.accent(1), 0.8), LINE_WIDTH, true)
		draw_polyline(_wave_points(freq, amp, elapsed * 2.0, dx), Style.accent(0), LINE_WIDTH, true)
	# Подписи осей снизу: частота и амплитуда своей волны против эталона не раскрываются.
	var font := ThemeDB.fallback_font
	var caption := "частота ← →   амплитуда ↑ ↓"
	var w := font.get_string_size(caption, HORIZONTAL_ALIGNMENT_LEFT, -1, Style.FONT_CAPTION).x
	draw_string(font, Vector2(size.x / 2.0 - w / 2.0, size.y - 110.0), caption, HORIZONTAL_ALIGNMENT_LEFT, -1, Style.FONT_CAPTION, Style.INK_3)
	# Волны справа сверху.
	var r := 7.0
	var gap := 28.0
	var x0 := size.x - 48.0 - (WAVES - 1) * gap
	for j in WAVES:
		var c := Style.SURFACE_2
		if j < wave_index:
			c = Style.SUCCESS
		elif j == wave_index:
			c = Style.INK
		draw_circle(Vector2(x0 + j * gap, 60.0), r, c)
