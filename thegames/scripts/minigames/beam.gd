extends Minigame
## «Наведи» (beam, графика), каталог `docs/specs/minigames_catalog.md`. Слева платформа, из
## неё бьёт луч, дальше ряд зеркал, в конце мишень. Влево и вправо наклоняют текущий элемент
## (сначала платформу, потом зеркала по очереди), луч перерисовывается в реальном времени и
## отражается от зеркал. Когда луч попал в следующее зеркало, A передаёт управление ему.
## Довести луч до мишени через все зеркала по порядку. 20 с, провал, если луч не дошёл.
## С `t` зеркал больше, мишень меньше и движется, а последнее зеркало это призма: луч
## расщепляется на три, попасть должен любой. Параметры в `resources/minigames/beam.tres`:
## mirrors, target (радиус), move (размах мишени), prism (от 0.5 последнее зеркало призма).

class Mirror:
	var pos := Vector2.ZERO
	var angle := 0.0
	var prism := false

const EMITTER_X := 200.0
const TARGET_X_FROM_RIGHT := 180.0
const MIRROR_LEN := 130.0
const TURN_SPEED := 1.6
const EMITTER_LIMIT := 1.1
const PRISM_SPREAD := 0.26
const HOLD_SECONDS := 0.5
const BEAM_WIDTH := 6.0
const BOT_TURN := 3.2

var mirror_count := 2
var target_r := 60.0
var move_amp := 0.0
var use_prism := false

var mirrors: Array[Mirror] = []
var emitter_angle := 0.0
var target := Vector2.ZERO
var target_base := Vector2.ZERO
var current := 0
var hit_target := false
var hold := 0.0
## Путь луча: список точек каждой ветви (одна ветвь, у призмы три), и сколько зеркал пройдено.
var paths: Array[PackedVector2Array] = []
var reached := 0
var next_hit := false
## Расстояние попадания в следующее зеркало от его центра: бот передаёт управление, когда
## луч идёт через центр, иначе после поворота зеркала луч с него соскользнёт.
var next_hit_dist := INF
var _handoff: AudioStreamPlayer
var _win: AudioStreamPlayer
var _deny: AudioStreamPlayer


func _on_start() -> void:
	mirror_count = clampi(int(round(def.param(&"mirrors", t, 2.0))), 1, 5)
	target_r = def.param(&"target", t, 60.0)
	move_amp = def.param(&"move", t, 0.0)
	use_prism = def.param(&"prism", t, 0.0) >= 0.5
	_handoff = Sfx.player(Sfx.blip(660.0, 0.08, 0.35, 30.0))
	_win = Sfx.player(Sfx.blip(990.0, 0.25, 0.45, 10.0))
	_deny = Sfx.player(Sfx.thud(0.08, 0.3))
	for p in [_handoff, _win, _deny]:
		add_child(p)
	var right := size.x - TARGET_X_FROM_RIGHT
	var mid := size.y * 0.5 + 10.0
	for i in mirror_count:
		var m := Mirror.new()
		var fx := float(i + 1) / (mirror_count + 1)
		m.pos = Vector2(lerpf(EMITTER_X, right, fx), mid + rng.randf_range(-220.0, 220.0))
		m.angle = rng.randf_range(0.0, PI)
		m.prism = use_prism and i == mirror_count - 1
		mirrors.append(m)
	target_base = Vector2(right, mid + rng.randf_range(-160.0, 160.0))
	target = target_base
	emitter_angle = rng.randf_range(-0.6, 0.6)
	_trace()
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	if GameInput.is_a(event):
		_advance()
		get_viewport().set_input_as_handled()


func _advance() -> void:
	if hit_target or current >= mirror_count:
		return
	if next_hit:
		current += 1
		_handoff.play()
	else:
		_deny.play()


func _on_tick(delta: float) -> void:
	if hit_target:
		hold -= delta
		if hold <= 0.0:
			finish(true)
		return
	if move_amp > 0.0:
		target = target_base + Vector2(0, sin(elapsed * 2.1) * move_amp)
	if not AutoTest.bot_active():
		var turn := 0.0
		if Input.is_action_pressed(GameInput.LEFT):
			turn -= 1.0
		if Input.is_action_pressed(GameInput.RIGHT):
			turn += 1.0
		if turn != 0.0:
			_rotate(turn * TURN_SPEED * delta)
	_trace()
	if _target_lit():
		hit_target = true
		hold = HOLD_SECONDS
		_win.play()
	queue_redraw()


func _rotate(da: float) -> void:
	if current == 0:
		emitter_angle = clampf(emitter_angle + da, -EMITTER_LIMIT, EMITTER_LIMIT)
	else:
		mirrors[current - 1].angle = fposmod(mirrors[current - 1].angle + da, PI)


func _on_timeout() -> bool:
	return hit_target


# --- Трассировка ---------------------------------------------------------------------------

func _emitter_pos() -> Vector2:
	return Vector2(EMITTER_X, size.y * 0.5 + 10.0)


static func _segment_hit(o: Vector2, d: Vector2, a: Vector2, b: Vector2) -> float:
	# Параметр t луча до пересечения с отрезком ab, −1 если мимо.
	var v := b - a
	var denom := d.cross(v)
	if absf(denom) < 0.0001:
		return -1.0
	var ao := a - o
	var tt := ao.cross(v) / denom
	var u := ao.cross(d) / denom
	return tt if tt > 1.0 and u >= 0.0 and u <= 1.0 else -1.0


func _mirror_ends(m: Mirror) -> Array[Vector2]:
	var h := Vector2(cos(m.angle), sin(m.angle)) * MIRROR_LEN / 2.0
	return [m.pos - h, m.pos + h]


## Луч от платформы: отражается от зеркал в порядке, какой встретит; `reached` сколько зеркал
## пройдено подряд по порядку, `next_hit` попал ли луч текущего элемента в следующее зеркало.
func _trace() -> void:
	paths.clear()
	reached = 0
	next_hit = false
	next_hit_dist = INF
	var o := _emitter_pos()
	var d := Vector2(cos(emitter_angle), sin(emitter_angle))
	var branch := PackedVector2Array([o])
	var expect := 0
	for bounce in 8:
		var best_t := INF
		var best := -1
		for i in mirrors.size():
			var ends := _mirror_ends(mirrors[i])
			var tt := _segment_hit(o, d, ends[0], ends[1])
			if tt > 0.0 and tt < best_t:
				best_t = tt
				best = i
		var target_t := _circle_hit(o, d)
		if best < 0 or (target_t > 0.0 and target_t < best_t):
			var end := o + d * (target_t if target_t > 0.0 else 3000.0)
			branch.append(end)
			break
		var hit := o + d * best_t
		branch.append(hit)
		if best == expect:
			if expect == current:
				next_hit = true
				next_hit_dist = hit.distance_to(mirrors[best].pos)
			expect += 1
			reached = expect
		var m := mirrors[best]
		var normal := Vector2(-sin(m.angle), cos(m.angle))
		if m.prism and best == mirror_count - 1:
			# Призма: три луча веером, каждый до мишени или в даль.
			var base := d.bounce(normal)
			for k in [-1, 0, 1]:
				var dir := base.rotated(k * PRISM_SPREAD)
				var tt := _circle_hit(hit + dir * 0.01, dir)
				var leg := PackedVector2Array([hit, hit + dir * (tt if tt > 0.0 else 3000.0)])
				paths.append(leg)
			break
		d = d.bounce(normal)
		o = hit + d * 0.01
	paths.push_front(branch)


func _circle_hit(o: Vector2, d: Vector2) -> float:
	var oc := o - target
	var b := oc.dot(d)
	var c := oc.dot(oc) - target_r * target_r
	var disc := b * b - c
	if disc < 0.0:
		return -1.0
	var tt := -b - sqrt(disc)
	return tt if tt > 0.0 else -1.0


## Мишень горит, когда луч прошёл все зеркала по порядку и дошёл до неё.
func _target_lit() -> bool:
	if reached < mirror_count:
		return false
	for p in paths:
		if p.size() >= 2 and p[p.size() - 1].distance_to(target) <= target_r + 0.5:
			return true
	return false


# --- Бот ------------------------------------------------------------------------------------

## Бот: WIN доворачивает текущий элемент так, чтобы луч попал в центр следующего, и жмёт A;
## LOSE ничего не делает.
func _bot_step(delta: float) -> bool:
	if AutoTest.bot_mode != AutoTest.BotMode.WIN or hit_target:
		return false
	if next_hit and next_hit_dist <= 6.0 and current < mirror_count:
		_advance()
		return false
	# Текущий элемент целится в следующее зеркало, последнее зеркало в мишень.
	var goal: Vector2 = mirrors[current].pos if current < mirror_count else target
	var want: float
	if current == 0:
		want = (goal - _emitter_pos()).angle()
		emitter_angle = move_toward(emitter_angle, clampf(want, -EMITTER_LIMIT, EMITTER_LIMIT), BOT_TURN * delta)
	else:
		var m := mirrors[current - 1]
		var incoming := _incoming_dir(current - 1)
		if incoming == Vector2.ZERO:
			return false
		var out := (goal - m.pos).normalized()
		var normal := (out - incoming).normalized()
		want = normal.angle() - PI / 2.0
		m.angle = _toward_angle(m.angle, fposmod(want, PI), BOT_TURN * delta)
	return false


## Направление луча, приходящего в зеркало `i`, из последней трассы.
func _incoming_dir(i: int) -> Vector2:
	var main := paths[0] if not paths.is_empty() else PackedVector2Array()
	if main.size() < i + 2:
		return Vector2.ZERO
	return (main[i + 1] - main[i]).normalized()


static func _toward_angle(a: float, b: float, step: float) -> float:
	var diff := fposmod(b - a + PI / 2.0, PI) - PI / 2.0
	return fposmod(a + clampf(diff, -step, step), PI)


# --- Рисование ----------------------------------------------------------------------------

func _draw() -> void:
	if def == null or mirrors.is_empty():
		return
	var lit := _target_lit()
	# Луч: свечение и ядро.
	for p in paths:
		if p.size() >= 2:
			draw_polyline(p, Color(Style.accent(0), 0.25), BEAM_WIDTH * 3.0, true)
			draw_polyline(p, Style.accent(0), BEAM_WIDTH, true)
	# Платформа.
	var e := _emitter_pos()
	var focus_e := current == 0
	Style.flat(Style.INK if focus_e else Style.INK_3, Style.R_CTL, Color.TRANSPARENT, 0).draw(get_canvas_item(), Rect2(e - Vector2(36, 36), Vector2(72, 72)))
	draw_line(e, e + Vector2(cos(emitter_angle), sin(emitter_angle)) * 44.0, Style.SURFACE_SOLID, 6.0, true)
	# Зеркала и призма.
	for i in mirrors.size():
		var m := mirrors[i]
		var ends := _mirror_ends(m)
		var focused := current == i + 1
		var col := Style.INK if focused or i < reached else Style.INK_3
		if m.prism:
			var n := Vector2(-sin(m.angle), cos(m.angle)) * 34.0
			draw_colored_polygon(PackedVector2Array([ends[0], ends[1], m.pos + n]), Color(col, 0.85))
		else:
			draw_line(ends[0], ends[1], col, 10.0, true)
		draw_circle(m.pos, 7.0, Style.SURFACE_SOLID)
		draw_arc(m.pos, 7.0, 0.0, TAU, 24, col, 3.0, true)
		if focused:
			draw_arc(m.pos, MIRROR_LEN / 2.0 + 16.0, 0.0, TAU, 48, Style.FOCUS, 3.0, true)
	if current == 0:
		Style.focus_ring(Style.R_CTL).draw(get_canvas_item(), Rect2(e - Vector2(36, 36), Vector2(72, 72)))
	# Мишень.
	draw_arc(target, target_r, 0.0, TAU, 64, Style.SUCCESS if lit else Style.accent(1), 8.0, true)
	draw_circle(target, target_r * 0.3, Style.SUCCESS if lit else Color(Style.accent(1), 0.6))
