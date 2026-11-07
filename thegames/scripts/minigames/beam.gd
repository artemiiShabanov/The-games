extends Minigame
## «Наведи» (beam, графика), каталог `docs/specs/minigames_catalog.md`. Слева платформа, из
## неё бьёт луч, дальше ряд зеркал, в конце мишень. Влево и вправо наклоняют текущий элемент
## (сначала платформу, потом зеркала), луч перерисовывается в реальном времени и отражается
## от зеркал. A передаёт управление тому зеркалу, в которое сейчас попадает луч от текущего
## элемента (у призмы считаются все три луча, из зеркал под ними берётся случайное), B
## возвращает расстановку к началу. Зеркало, получившее управление, становится зелёным;
## мишень горит, когда зелёными стали все зеркала и луч дошёл до неё (плейтест 2026-11-07).
## 20 с, провал, если не дошёл.
## С `t` зеркал больше, мишень меньше и движется, а последнее зеркало это призма: луч
## расщепляется на три, попасть должен любой. Параметры в `resources/minigames/beam.tres`:
## mirrors, target (радиус), move (размах мишени), prism (от 0.5 последнее зеркало призма).

class Mirror:
	var pos := Vector2.ZERO
	var angle := 0.0
	var start_angle := 0.0
	var prism := false

const EMITTER_X := 200.0
const TARGET_X_FROM_RIGHT := 180.0
const MIRROR_LEN := 130.0
const TURN_SPEED := 1.6
const EMITTER_LIMIT := 1.1
const PRISM_SPREAD := 0.26
const HOLD_SECONDS := 0.5
const BEAM_WIDTH := 6.0
## Луч упирается в поверхность зеркала, а не в его ось: отступ на половину толщины.
const MIRROR_HALF := 5.0
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
## Точные точки отражений основной ветви (для физики и бота); в `paths` они отступают до
## поверхности зеркала ради рисования.
var exact: PackedVector2Array = PackedVector2Array()
## Зеркала, в которые попадает луч от текущего элемента, и расстояние попадания от центра
## каждого (ключ индекс): бот передаёт управление, когда луч идёт через центр, иначе после
## поворота зеркала луч с него соскользнёт. У призмы кандидатов может быть несколько.
var hit_candidates: Dictionary[int, float] = {}
## Зеркала, получившие управление по A: зелёные, для победы нужны все.
var activated: Array[bool] = []
var start_emitter := 0.0
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
		m.start_angle = m.angle
		m.prism = use_prism and i == mirror_count - 1
		mirrors.append(m)
		activated.append(false)
	target_base = Vector2(right, mid + rng.randf_range(-160.0, 160.0))
	target = target_base
	emitter_angle = rng.randf_range(-0.6, 0.6)
	start_emitter = emitter_angle
	_trace()
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	if GameInput.is_a(event):
		_advance()
	elif GameInput.is_b(event):
		_restart()
	else:
		return
	get_viewport().set_input_as_handled()


## A: управление зеркалу, в которое сейчас попадает луч от текущего элемента; из нескольких
## (лучи призмы) случайное.
func _advance() -> void:
	if hit_target:
		return
	var options: Array[int] = []
	for i in hit_candidates:
		if i + 1 != current:
			options.append(i)
	if options.is_empty():
		_deny.play()
		return
	_advance_to(options[rng.randi_range(0, options.size() - 1)])


func _advance_to(i: int) -> void:
	current = i + 1
	activated[i] = true
	_handoff.play()


## B: платформа и зеркала как в начале, управление снова у платформы.
func _restart() -> void:
	if hit_target:
		return
	emitter_angle = start_emitter
	for m in mirrors:
		m.angle = m.start_angle
	for i in activated.size():
		activated[i] = false
	current = 0
	_deny.play()
	_trace()


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


## Луч от платформы: отражается от зеркал в порядке, какой встретит; у призмы расходится на
## три ветви, каждая трассируется дальше. `hit_candidates` зеркала, в которые попадает луч от
## текущего элемента.
func _trace() -> void:
	paths.clear()
	exact = PackedVector2Array()
	hit_candidates.clear()
	var o := _emitter_pos()
	exact.append(o)
	_trace_ray(o, Vector2(cos(emitter_angle), sin(emitter_angle)), 0, false, o)


func _trace_ray(o: Vector2, d: Vector2, from_element: int, split: bool, first: Vector2) -> void:
	var branch := PackedVector2Array([first])
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
			branch.append(o + d * (target_t if target_t > 0.0 else 3000.0))
			break
		var m := mirrors[best]
		var normal := Vector2(-sin(m.angle), cos(m.angle))
		# Отступ до поверхности зеркала вдоль луча: луч не проходит сквозь его толщину.
		var cos_in := absf(d.dot(normal))
		var back := MIRROR_HALF / maxf(cos_in, 0.2)
		var hit_exact := o + d * best_t
		var hit := o + d * maxf(best_t - back, 0.0)
		branch.append(hit)
		exact.append(hit_exact)
		if from_element == current:
			var dist := hit_exact.distance_to(m.pos)
			if dist < hit_candidates.get(best, INF):
				hit_candidates[best] = dist
		from_element = best + 1
		if m.prism and not split:
			# Призма: три луча веером, каждый трассируется дальше сам.
			paths.append(branch)
			var base := d.bounce(normal)
			for k in [-1, 0, 1]:
				var dir := base.rotated(k * PRISM_SPREAD)
				_trace_ray(hit_exact + dir * 0.01, dir, from_element, true, hit)
			return
		d = d.bounce(normal)
		o = hit_exact + d * 0.01
	paths.append(branch)


func _circle_hit(o: Vector2, d: Vector2) -> float:
	var oc := o - target
	var b := oc.dot(d)
	var c := oc.dot(oc) - target_r * target_r
	var disc := b * b - c
	if disc < 0.0:
		return -1.0
	var tt := -b - sqrt(disc)
	return tt if tt > 0.0 else -1.0


## Мишень горит, когда все зеркала получили управление и луч дошёл до неё.
func _target_lit() -> bool:
	for a in activated:
		if not a:
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
	# Бот идёт по зеркалам по порядку: передаёт управление только следующему и только при
	# попадании у центра.
	if hit_candidates.has(current) and hit_candidates[current] <= 6.0:
		_advance_to(current)
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


## Направление луча, приходящего в зеркало `i`: точный отрезок трассы, который кончается у него.
func _incoming_dir(i: int) -> Vector2:
	var main := exact
	var best := -1
	var best_d := 40.0
	for j in range(1, main.size()):
		var d := main[j].distance_to(mirrors[i].pos)
		if d < best_d:
			best_d = d
			best = j
	if best < 1:
		return Vector2.ZERO
	return (main[best] - main[best - 1]).normalized()


static func _toward_angle(a: float, b: float, step: float) -> float:
	var diff := fposmod(b - a + PI / 2.0, PI) - PI / 2.0
	return fposmod(a + clampf(diff, -step, step), PI)


# --- Рисование ----------------------------------------------------------------------------

func _draw() -> void:
	if def == null or mirrors.is_empty():
		return
	var lit := _target_lit()
	# Луч: свечение и ядро отдельными отрезками, чтобы на изломах толщина не менялась.
	for p in paths:
		for i in range(1, p.size()):
			draw_line(p[i - 1], p[i], Color(Style.accent(0), 0.25), BEAM_WIDTH * 3.0, true)
	for p in paths:
		for i in range(1, p.size()):
			draw_line(p[i - 1], p[i], Style.accent(0), BEAM_WIDTH, true)
			if i < p.size() - 1:
				draw_circle(p[i], BEAM_WIDTH / 2.0, Style.accent(0))
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
		var col := Style.SUCCESS if activated[i] else (Style.INK if focused else Style.INK_3)
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
