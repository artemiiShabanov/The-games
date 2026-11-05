extends Minigame
## «В такт» (in_time, звук), каталог `docs/specs/minigames_catalog.md`.
## Три дорожки, как в Guitar Hero: ←, ↓, →. Ноты бегут сверху к метке, нужная стрелка в такт.
## Длинные ноты зажать и держать до конца. 16 нот, провал при менее чем 11 попаданиях.
## С `t` быстрее темп, появляются длинные ноты, затем аккорды из двух дорожек.
## Метроном тикает каждую долю, попадание и промах звучат сами.
## Параметры от `t` в `resources/minigames/in_time.tres`: beat, travel, window, long_share,
## chord_share.

enum NoteState { PENDING, HOLDING, HIT, MISS }

class Note:
	var lane := 0
	var time := 0.0
	var length := 0.0
	var state := NoteState.PENDING
	var resolved_at := 0.0

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
const BOT_PRECISION := 0.03

var beat := 1.0
var travel := 1.6
var window := 0.14
var long_share := 0.0
var chord_share := 0.0

var notes: Array[Note] = []
var hits := 0
var misses := 0
var held: Array[bool] = [false, false, false]
var lane_flash: Array[float] = [0.0, 0.0, 0.0]
var _next_beat_time := 0.0
var _tick: AudioStreamPlayer
var _hit_sound: AudioStreamPlayer
var _miss_sound: AudioStreamPlayer


func _on_start() -> void:
	beat = def.param(&"beat", t, 1.0)
	travel = def.param(&"travel", t, 1.6)
	window = def.param(&"window", t, 0.14)
	long_share = def.param(&"long_share", t, 0.0)
	chord_share = def.param(&"chord_share", t, 0.0)
	_build_chart()
	_tick = Sfx.player(Sfx.blip(1100.0, 0.05, 0.25, 40.0), -6.0)
	_hit_sound = Sfx.player(Sfx.blip(660.0, 0.12, 0.5, 20.0))
	_miss_sound = Sfx.player(Sfx.thud())
	add_child(_tick)
	add_child(_hit_sound)
	add_child(_miss_sound)
	_next_beat_time = notes[0].time - COUNT_IN_BEATS * beat
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
		if slot > 0 and k < TOTAL_NOTES - 1 and rng.randf() < 0.3:
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
	if elapsed >= _next_beat_time and _next_beat_time <= notes[notes.size() - 1].time + 0.01:
		_tick.play()
		_next_beat_time += beat
	for n in notes:
		match n.state:
			NoteState.PENDING:
				if elapsed > n.time + window:
					_miss(n)
			NoteState.HOLDING:
				if elapsed >= n.time + n.length:
					_hit(n)
	queue_redraw()
	if misses > TOTAL_NOTES - NEED_HITS:
		finish(false)
	elif hits + misses >= TOTAL_NOTES:
		finish(hits >= NEED_HITS)


func _on_timeout() -> bool:
	return hits >= NEED_HITS


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
		return
	if best.length > 0.0:
		best.state = NoteState.HOLDING
		lane_flash[lane] = POP_SECONDS
		_hit_sound.play()
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


func _miss(n: Note) -> void:
	if n.state == NoteState.HIT or n.state == NoteState.MISS:
		return
	n.state = NoteState.MISS
	n.resolved_at = elapsed
	misses += 1
	_miss_sound.play()


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
	var font := ThemeDB.fallback_font
	for lane in LANES:
		var x := _lane_x(lane)
		var col := Style.accent(lane)
		draw_rect(Rect2(x - LANE_W / 2.0, TOP_Y - 20.0, LANE_W, hit_y - TOP_Y + 20.0 + NOTE_R + 24.0),
				Color(Style.INK, 0.035))
		# Метка: кольцо с глифом, при зажатии и попадании заливается.
		var pop := lane_flash[lane] / POP_SECONDS
		var ring_r := NOTE_R + 10.0 + 8.0 * pop
		if held[lane] or pop > 0.0:
			draw_circle(Vector2(x, hit_y), ring_r, Color(col, 0.25 + 0.35 * pop))
		draw_arc(Vector2(x, hit_y), ring_r, 0.0, TAU, 64, col, 5.0, true)
		var glyph := LANE_GLYPHS[lane]
		var w := font.get_string_size(glyph, HORIZONTAL_ALIGNMENT_CENTER, -1, 40).x
		draw_string(font, Vector2(x - w / 2.0, hit_y + 14.0), glyph, HORIZONTAL_ALIGNMENT_LEFT, -1, 40, col)
	# Ноты: сначала хвосты длинных, потом головы.
	for n in notes:
		var x := _lane_x(n.lane)
		var col := Style.accent(n.lane)
		var y := _note_y(n.time, hit_y)
		match n.state:
			NoteState.MISS:
				var p := clampf((elapsed - n.resolved_at) / 0.4, 0.0, 1.0)
				col = Style.INK_3
				col.a = 1.0 - p
				y += p * 60.0
			NoteState.HIT:
				var p := clampf((elapsed - n.resolved_at) / POP_SECONDS, 0.0, 1.0)
				if p >= 1.0:
					continue
				col.a = 1.0 - p
				y = hit_y
				draw_arc(Vector2(x, y), NOTE_R + 30.0 * p, 0.0, TAU, 48, col, 6.0, true)
				continue
			NoteState.HOLDING:
				y = hit_y
		if y < TOP_Y - NOTE_R - 80.0 or y > size.y:
			continue
		if n.length > 0.0:
			var tail_y := _note_y(n.time + n.length, hit_y)
			if n.state == NoteState.HOLDING:
				tail_y = minf(tail_y, hit_y)
			var top := maxf(tail_y, TOP_Y - NOTE_R)
			draw_rect(Rect2(x - NOTE_R * 0.45, top, NOTE_R * 0.9, maxf(y - top, 0.0)), Color(col, 0.55))
			draw_circle(Vector2(x, top), NOTE_R * 0.45, Color(col, 0.55))
		draw_circle(Vector2(x, y), NOTE_R, col)
	# Счёт нот справа сверху: попадания зелёные, промахи серые.
	var r := 7.0
	var gap := 24.0
	var x0 := size.x - 48.0 - (TOTAL_NOTES - 1) * gap
	var i := 0
	var ordered := notes.duplicate()
	ordered.sort_custom(func(a: Note, b: Note) -> bool: return a.time < b.time)
	for n: Note in ordered:
		var c := Style.SURFACE_2
		if n.state == NoteState.HIT:
			c = Style.SUCCESS
		elif n.state == NoteState.MISS:
			c = Style.INK_3
		draw_circle(Vector2(x0 + i * gap, 60.0), r, c)
		i += 1
