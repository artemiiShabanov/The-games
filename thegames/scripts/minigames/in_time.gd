extends Minigame
## «В такт» (in_time, звук), каталог `docs/specs/minigames_catalog.md`.
## Три дорожки, как в Guitar Hero: ←, ↓, →. Ноты бегут сверху к метке, нужная стрелка в такт.
## Длинные ноты зажать и держать до конца. 16 нот, провал при менее чем 11 попаданиях.
## С `t` быстрее темп, появляются длинные ноты, затем аккорды из двух дорожек.
## Ложное нажатие (нет ноты в окне) это ошибка: метка дрожит, звучит промах (плейтест
## 2026-11-05). Метроном тикает каждую долю с упреждением на задержку вывода звука, метки
## пульсируют в такт; синкопы на полдоли появляются с ростом `t`.
## Параметры от `t` в `resources/minigames/in_time.tres`: beat, travel, window, long_share,
## chord_share, offbeat_share.
## Мармелад (STYLE «Мармелад»): ноты мягкие, вытягиваются на бегу и плющатся о метку при
## попадании, метки упругими кольцами вздрагивают на долю, при попадании (с кругом по полю) и
## при ошибке, зажатая метка чуть вмята; кружки счёта подпрыгивают. Геймплей тот же.

enum NoteState { PENDING, HOLDING, HIT, MISS }

class Note:
	var lane := 0
	var time := 0.0
	var length := 0.0
	var state := NoteState.PENDING
	var resolved_at := 0.0
	## Мармелад: мягкое тело головы и место в счёте нот (только для рисования).
	var body: JellyShape
	var order := 0

const LANES := 3
const LANE_ACTIONS: Array[StringName] = [GameInput.LEFT, GameInput.DOWN, GameInput.RIGHT]
const LANE_GLYPHS: Array[String] = ["←", "↓", "→"]
const TOTAL_NOTES := 16
const NEED_HITS := 11
const COUNT_IN_BEATS := 2
const LANE_W := 150.0
const LANE_GAP := 30.0
const NOTE_R := 44.0
const TOP_Y := 70.0
const HIT_FROM_BOTTOM := 150.0
const POP_SECONDS := 0.25
const SHAKE_SECONDS := 0.35
const PULSE_SECONDS := 0.18
const MAX_ERRORS := TOTAL_NOTES - NEED_HITS
const BOT_PRECISION := 0.03
const RING_R := NOTE_R + 10.0
const MISS_SECONDS := 0.4

var beat := 1.0
var travel := 1.6
var window := 0.14
var long_share := 0.0
var chord_share := 0.0
var offbeat_share := 0.0

var notes: Array[Note] = []
var hits := 0
var misses := 0
## Ложные нажатия: ошибки сверх промахов по нотам.
var false_presses := 0
var held: Array[bool] = [false, false, false]
var lane_flash: Array[float] = [0.0, 0.0, 0.0]
var lane_shake: Array[float] = [0.0, 0.0, 0.0]
var pulse := 0.0
var _next_beat_time := 0.0
var _tick: AudioStreamPlayer
var _hit_sound: AudioStreamPlayer
var _miss_sound: AudioStreamPlayer

# Мармелад: упругие метки, круги по полю, пружины кружков счёта.
var _marks: Array[JellyShape] = []
var _rings := RingFx.new()
var _dots: Array[JellySpring] = []
var _last_pulse := 0.0


func _on_start() -> void:
	beat = def.param(&"beat", t, 1.0)
	travel = def.param(&"travel", t, 1.6)
	window = def.param(&"window", t, 0.14)
	long_share = def.param(&"long_share", t, 0.0)
	chord_share = def.param(&"chord_share", t, 0.0)
	offbeat_share = def.param(&"offbeat_share", t, 0.0)
	_build_chart()
	_tick = Sfx.player(Sfx.blip(1100.0, 0.05, 0.25, 40.0), -6.0)
	_hit_sound = Sfx.player(Sfx.blip(660.0, 0.12, 0.5, 20.0))
	_miss_sound = Sfx.player(Sfx.thud())
	add_child(_tick)
	add_child(_hit_sound)
	add_child(_miss_sound)
	_next_beat_time = notes[0].time - COUNT_IN_BEATS * beat
	_setup_jelly()
	queue_redraw()


## Ноты по сетке долей с синкопами; длинные занимают дорожку на долю, аккорды из двух дорожек.
func _build_chart() -> void:
	var start := COUNT_IN_BEATS * beat + 0.4
	var prev_lane := -1
	var busy_until: Array[float] = [0.0, 0.0, 0.0]
	var k := 0
	var slot := 0
	while k < TOTAL_NOTES:
		var time := start + slot * beat
		if slot > 0 and k < TOTAL_NOTES - 1 and rng.randf() < offbeat_share:
			time += beat * 0.5
		var free: Array[int] = []
		for lane in LANES:
			if busy_until[lane] <= time and lane != prev_lane:
				free.append(lane)
		if free.is_empty():
			for lane in LANES:
				if busy_until[lane] <= time:
					free.append(lane)
		if free.is_empty():
			slot += 1
			continue
		var lane: int = free[rng.randi_range(0, free.size() - 1)]
		var note := Note.new()
		note.lane = lane
		note.time = time
		if rng.randf() < long_share:
			note.length = beat * 0.9
			busy_until[lane] = time + note.length + beat * 0.5
		notes.append(note)
		k += 1
		prev_lane = lane
		if k < TOTAL_NOTES and note.length == 0.0 and free.size() > 1 and rng.randf() < chord_share:
			free.erase(lane)
			var other := Note.new()
			other.lane = free[rng.randi_range(0, free.size() - 1)]
			other.time = time
			notes.append(other)
			k += 1
		slot += 1


func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	for lane in LANES:
		if event.is_action_pressed(LANE_ACTIONS[lane]):
			_press(lane)
			get_viewport().set_input_as_handled()
		elif event.is_action_released(LANE_ACTIONS[lane]):
			_release(lane)


func _on_tick(delta: float) -> void:
	for lane in LANES:
		lane_flash[lane] = maxf(lane_flash[lane] - delta, 0.0)
		lane_shake[lane] = maxf(lane_shake[lane] - delta, 0.0)
	pulse = maxf(pulse - delta, 0.0)
	# Тик уходит в звук с упреждением на задержку вывода, чтобы слышаться ровно на доле.
	var latency := AudioServer.get_output_latency() + AudioServer.get_time_to_next_mix()
	if elapsed + latency >= _next_beat_time and _next_beat_time <= notes[notes.size() - 1].time + 0.01:
		_tick.play()
		_next_beat_time += beat
	if _next_beat_time - beat <= elapsed and elapsed < _next_beat_time - beat + 0.02 and pulse <= 0.0:
		pulse = PULSE_SECONDS
	for n in notes:
		match n.state:
			NoteState.PENDING:
				if elapsed > n.time + window:
					_miss(n)
			NoteState.HOLDING:
				if elapsed >= n.time + n.length:
					_hit(n)
	queue_redraw()
	if misses + false_presses > MAX_ERRORS:
		finish(false)
	elif hits + misses >= TOTAL_NOTES:
		finish(misses + false_presses <= MAX_ERRORS)


func _on_timeout() -> bool:
	return hits >= NEED_HITS and misses + false_presses <= MAX_ERRORS


## Бот: WIN жмёт в такт и держит длинные, LOSE молчит.
func _bot_step(_delta: float) -> bool:
	if AutoTest.bot_mode != AutoTest.BotMode.WIN:
		return false
	for n in notes:
		if n.state == NoteState.PENDING and absf(n.time - elapsed) <= BOT_PRECISION:
			_press(n.lane)
			if n.length == 0.0:
				held[n.lane] = false
		elif n.state == NoteState.HOLDING and elapsed >= n.time + n.length:
			_release(n.lane)
	return false


func _press(lane: int) -> void:
	held[lane] = true
	var best: Note = null
	for n in notes:
		if n.lane == lane and n.state == NoteState.PENDING and absf(n.time - elapsed) <= window:
			if best == null or n.time < best.time:
				best = n
	if best == null:
		# Ложное нажатие: ошибка, метка дрожит.
		false_presses += 1
		lane_shake[lane] = SHAKE_SECONDS
		_miss_sound.play()
		_jelly_mark_poke(lane, -260.0)
		return
	if best.length > 0.0:
		best.state = NoteState.HOLDING
		lane_flash[lane] = POP_SECONDS
		_hit_sound.play()
		_jelly_land(best, 0.6)
	else:
		_hit(best)


func _release(lane: int) -> void:
	held[lane] = false
	for n in notes:
		if n.lane == lane and n.state == NoteState.HOLDING:
			if elapsed < n.time + n.length - window:
				_miss(n)
			else:
				_hit(n)


func _hit(n: Note) -> void:
	if n.state == NoteState.HIT or n.state == NoteState.MISS:
		return
	n.state = NoteState.HIT
	n.resolved_at = elapsed
	hits += 1
	lane_flash[n.lane] = POP_SECONDS
	_hit_sound.play()
	_jelly_land(n, 1.0)


func _miss(n: Note) -> void:
	if n.state == NoteState.HIT or n.state == NoteState.MISS:
		return
	n.state = NoteState.MISS
	n.resolved_at = elapsed
	misses += 1
	_miss_sound.play()
	if n.body != null:
		n.body.poke(-160.0)
	_jelly_mark_poke(n.lane, -140.0)
	_jelly_dot(n)


# --- Мармелад -----------------------------------------------------------------------------

func _setup_jelly() -> void:
	var ordered: Array[Note] = notes.duplicate()
	ordered.sort_custom(func(a: Note, b: Note) -> bool: return a.time < b.time)
	for k in ordered.size():
		ordered[k].order = k
	_dots.clear()
	for k in notes.size():
		_dots.append(JellySpring.new())
	_marks.clear()
	for lane in LANES:
		_marks.append(JellyShape.circle(RING_R, 48))


## Нота села на метку: голова плющится сверху, метка вздрагивает; `k` < 1 начало длинной ноты.
func _jelly_land(n: Note, k: float) -> void:
	if n.body != null:
		# Сверху и снизу внутрь: голова сплющивается, давление раздаёт её вширь.
		n.body.push(Vector2(0.0, 380.0 * k), Vector2.UP)
		n.body.push(Vector2(0.0, -380.0 * k), Vector2.DOWN)
	_jelly_mark_poke(n.lane, 300.0 * k)
	if k >= 1.0:
		_rings.add(Vector2(_lane_x(n.lane), size.y - HIT_FROM_BOTTOM), RING_R, RING_R + 40.0,
				Color(Style.accent(n.lane), 0.6), 1, 0.45)
		_jelly_dot(n)


func _jelly_mark_poke(lane: int, strength: float) -> void:
	if lane < _marks.size():
		_marks[lane].poke(strength)


## Кружок счёта подпрыгивает, когда нота решилась.
func _jelly_dot(n: Note) -> void:
	if Jelly.on() and n.order < _dots.size():
		_dots[n.order].kick(14.0)


## Мармелад живёт и после финиша, пока сцена на экране; на паузе стоит.
func _process(delta: float) -> void:
	super(delta)
	if _marks.is_empty() or paused or not Jelly.on():
		return
	var tu := Jelly.tuning()
	var hit_y := size.y - HIT_FROM_BOTTOM
	_rings.step(delta)
	if pulse > _last_pulse:
		for m in _marks:
			m.poke(90.0)
	_last_pulse = pulse
	for lane in LANES:
		# Зажатая метка чуть вмята.
		_marks[lane].follow(delta, Vector2(_mark_x(lane), hit_y), 0.0, 0.94 if held[lane] else 1.0)
	for d in _dots:
		d.step(delta, tu.spring_stiffness, tu.spring_damping)
	for n in notes:
		var pose := _note_pose(n, hit_y)
		if pose.z <= 0.0:
			continue
		if n.body == null:
			n.body = JellyShape.circle(NOTE_R)
		n.body.follow(delta, Vector2(pose.x, pose.y), 0.0, pose.w)
	if not running:
		queue_redraw()


## Метка по X: при ложном нажатии дрожит.
func _mark_x(lane: int) -> float:
	var x := _lane_x(lane)
	if lane_shake[lane] > 0.0:
		x += sin(lane_shake[lane] * 45.0) * 12.0 * lane_shake[lane] / SHAKE_SECONDS
	return x


## Где голова ноты: (x, y, непрозрачность, масштаб); непрозрачность 0 значит не видна.
func _note_pose(n: Note, hit_y: float) -> Vector4:
	var x := _lane_x(n.lane)
	var y := _note_y(n.time, hit_y)
	var alpha := 1.0
	var scale := 1.0
	match n.state:
		NoteState.MISS:
			var p := clampf((elapsed - n.resolved_at) / MISS_SECONDS, 0.0, 1.0)
			alpha = 1.0 - p
			y += p * 60.0
		NoteState.HIT:
			var p := clampf((elapsed - n.resolved_at) / POP_SECONDS, 0.0, 1.0)
			if p >= 1.0:
				return Vector4(x, hit_y, 0.0, 1.0)
			return Vector4(x, hit_y, 1.0 - p, lerpf(1.0, 0.75, p))
		NoteState.HOLDING:
			y = hit_y
	if y < TOP_Y - NOTE_R - 80.0 or y > size.y or alpha <= 0.0:
		return Vector4(x, y, 0.0, scale)
	return Vector4(x, y, alpha, scale)


# --- Рисование ----------------------------------------------------------------------------

func _lane_x(lane: int) -> float:
	var total := LANES * LANE_W + (LANES - 1) * LANE_GAP
	return (size.x - total) / 2.0 + LANE_W / 2.0 + lane * (LANE_W + LANE_GAP)


func _note_y(time: float, hit_y: float) -> float:
	return hit_y - (time - elapsed) / travel * (hit_y - TOP_Y)


func _draw() -> void:
	if def == null:
		return
	var hit_y := size.y - HIT_FROM_BOTTOM
	var font := get_theme_default_font()
	var jelly := Jelly.on() and not _marks.is_empty()
	for lane in LANES:
		var x := _lane_x(lane)
		var col := Style.accent(lane)
		draw_rect(Rect2(x - LANE_W / 2.0, TOP_Y - 20.0, LANE_W, hit_y - TOP_Y + 20.0 + NOTE_R + 24.0),
				Color(Style.INK, 0.035))
		# Метка: кольцо с глифом, при зажатии и попадании заливается.
		var pop := lane_flash[lane] / POP_SECONDS
		var beat_pulse := pulse / PULSE_SECONDS
		var sx := _mark_x(lane)
		if jelly:
			# Упругое кольцо: пульс доли и попадание вздрагиванием, а не ростом радиуса.
			var m := _marks[lane]
			if held[lane] or pop > 0.0:
				m.draw(self, Color(col, 0.25 + 0.35 * pop))
			m.draw_outline(self, col, 5.0 + 2.0 * beat_pulse)
		else:
			var ring_r := RING_R + 8.0 * pop + 4.0 * beat_pulse
			if held[lane] or pop > 0.0:
				draw_circle(Vector2(sx, hit_y), ring_r, Color(col, 0.25 + 0.35 * pop))
			draw_arc(Vector2(sx, hit_y), ring_r, 0.0, TAU, 64, col, 5.0 + 2.0 * beat_pulse, true)
		var glyph := LANE_GLYPHS[lane]
		var w := font.get_string_size(glyph, HORIZONTAL_ALIGNMENT_CENTER, -1, 40).x
		draw_string(font, Vector2(sx - w / 2.0, hit_y + 14.0), glyph, HORIZONTAL_ALIGNMENT_LEFT, -1, 40, col)
	if jelly:
		_rings.draw(self)
	# Ноты: хвост длинной, затем голова.
	for n in notes:
		var pose := _note_pose(n, hit_y)
		if pose.z <= 0.0:
			continue
		var x := pose.x
		var y := pose.y
		var col := Style.accent(n.lane)
		if n.state == NoteState.MISS:
			col = Style.INK_3
		col.a = pose.z
		if n.state == NoteState.HIT:
			if not jelly:
				var p := 1.0 - pose.z
				draw_arc(Vector2(x, y), NOTE_R + 30.0 * p, 0.0, TAU, 48, col, 6.0, true)
				continue
		elif n.length > 0.0:
			var tail_y := _note_y(n.time + n.length, hit_y)
			if n.state == NoteState.HOLDING:
				tail_y = minf(tail_y, hit_y)
			var top := maxf(tail_y, TOP_Y - NOTE_R)
			draw_rect(Rect2(x - NOTE_R * 0.45, top, NOTE_R * 0.9, maxf(y - top, 0.0)), Color(col, 0.55))
			draw_circle(Vector2(x, top), NOTE_R * 0.45, Color(col, 0.55))
		if jelly and n.body != null:
			n.body.draw(self, col)
		else:
			draw_circle(Vector2(x, y), NOTE_R * pose.w, col)
	# Счёт нот справа сверху: попадания зелёные, промахи серые; решённый кружок подпрыгивает.
	var r := 7.0
	var gap := 24.0
	var x0 := size.x - 48.0 - (TOTAL_NOTES - 1) * gap
	for n in notes:
		var c := Style.SURFACE_2
		if n.state == NoteState.HIT:
			c = Style.SUCCESS
		elif n.state == NoteState.MISS:
			c = Style.INK_3
		var bounce := _dots[n.order].value if n.order < _dots.size() else 0.0
		draw_circle(Vector2(x0 + n.order * gap, 60.0), r * clampf(1.0 + bounce, 0.5, 1.8), c)
