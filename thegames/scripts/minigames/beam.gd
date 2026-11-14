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
## Мармелад (STYLE «Мармелад»): зеркала гнутся пружинами (концы отстают при повороте и качаются
## после остановки, при передаче управления вздрагивают дугой), призма перетекает на другую
## сторону вместо скачка, платформа и мишень мягкие тела, мишень тянется на ходу. Текущий
## элемент показан толщиной (бортик темнее под ним), а не синей рамкой; передача управления
## пускает круг от зеркала, зажжённая мишень два круга. Физика луча идёт по точной геометрии.

class Mirror:
	var pos := Vector2.ZERO
	var angle := 0.0
	var start_angle := 0.0
	var prism := false


## Мармелад одного элемента (0 платформа, дальше зеркала): пружины изгиба, дуги, толщины, бортика.
class Wobble:
	var lift := JellySpring.new()
	var press_left := 0.0
	## S-изгиб от вращения: у зеркала пиксели на концах, у платформы отставание ствола в радианах.
	var bend := JellySpring.new()
	## Дуга от вздрога, пиксели на концах (ось держит середину).
	var bow := JellySpring.new()
	## Толщина зеркала, у платформы длина ствола.
	var swell := JellySpring.new()
	## Призма: высота вершины, переходит через ноль при смене стороны.
	var side := JellySpring.new()
	## Непрерывный угол для рисования: игровой берётся по модулю PI и скачет на краю.
	var vis_angle := 0.0

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
# Мармелад: только рисование, геймплей их не читает.
## Мышь: левая кнопка зажата и ведёт луч к точке поля.
var _aim := false
var _aim_at := Vector2.ZERO
var _wob: Array[Wobble] = []
var _body: JellyShape
var _ring_shape: JellyShape
var _dot: JellyShape
var _rings := RingFx.new()
var _beam_pulse := JellySpring.new()
var _jt := 0.0


func _on_start() -> void:
	mirror_count = clampi(int(round(def.param(&"mirrors", t, 2.0))), 1, 5)
	target_r = def.param(&"target", t, 60.0)
	move_amp = def.param(&"move", t, 0.0)
	use_prism = def.param(&"prism", t, 0.0) >= 0.5
	_handoff = MiniSfx.hit(330.0)
	_win = MiniSfx.win()
	_deny = MiniSfx.miss()
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
	_jelly_setup()
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
		_jelly_deny()
		return
	_advance_to(options[rng.randi_range(0, options.size() - 1)])


func _advance_to(i: int) -> void:
	var from := current
	current = i + 1
	activated[i] = true
	_handoff.play()
	_jelly_handoff(from, current)


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
	_jelly_restart()


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
		elif _aim and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
			_turn_toward(_aim_at, TURN_SPEED * delta)
		else:
			_aim = false
	_trace()
	if _target_lit():
		hit_target = true
		hold = HOLD_SECONDS
		_win.play()
		_jelly_lit()
	queue_redraw()


func _rotate(da: float) -> void:
	if current == 0:
		emitter_angle = clampf(emitter_angle + da, -EMITTER_LIMIT, EMITTER_LIMIT)
	else:
		mirrors[current - 1].angle = fposmod(mirrors[current - 1].angle + da, PI)


func _on_timeout() -> bool:
	return hit_target


func _on_finish(success: bool) -> void:
	if not success and _ring_shape != null:
		# Провал: мишень сжимается и качается.
		_ring_shape.poke(-220.0)
		_dot.poke(-260.0)


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
	_turn_toward(goal, BOT_TURN * delta)
	return false


## Доворачивает текущий элемент не больше чем на `step` так, чтобы его луч шёл в `goal`: ствол
## платформы на точку, зеркало отражает входящий луч в неё.
func _turn_toward(goal: Vector2, step: float) -> void:
	if current == 0:
		var want := (goal - _emitter_pos()).angle()
		emitter_angle = move_toward(emitter_angle, clampf(want, -EMITTER_LIMIT, EMITTER_LIMIT), step)
		return
	var m := mirrors[current - 1]
	var incoming := _incoming_dir(current - 1)
	if incoming == Vector2.ZERO:
		return
	var out := (goal - m.pos).normalized()
	var normal := (out - incoming).normalized()
	m.angle = _toward_angle(m.angle, fposmod(normal.angle() - PI / 2.0, PI), step)


## Мышь (#83): зажатая левая кнопка ведёт луч текущего элемента к курсору со скоростью стрелок,
## клик по зеркалу под лучом передаёт ему управление, как ␣ (мимо луча: отказ), правая
## кнопка возвращает к началу, как Ctrl.
func _on_mouse(event: InputEventMouse) -> bool:
	if event is InputEventMouseMotion:
		_aim_at = event.position
		return _aim
	var b := event as InputEventMouseButton
	if b == null or b.button_index != MOUSE_BUTTON_LEFT:
		return false
	_aim = false
	if not b.pressed or hit_target:
		return true
	var i := _mirror_at(b.position)
	if i >= 0 and i + 1 != current:
		if hit_candidates.has(i):
			_advance_to(i)
		else:
			_deny.play()
			_jelly_deny()
		return true
	_aim = true
	_aim_at = b.position
	return true


## Зеркало под точкой поля или −1.
func _mirror_at(pos: Vector2) -> int:
	for i in mirrors.size():
		if pos.distance_to(mirrors[i].pos) <= MIRROR_LEN / 2.0 + 12.0:
			return i
	return -1


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


# --- Мармелад ---------------------------------------------------------------------------------

const PLATFORM_SIZE := 72.0
const BARREL_LEN := 44.0
const MIRROR_WIDTH := 10.0
const PRISM_H := 34.0
const CURVE_POINTS := 12
## Насколько концы зеркала отстают при повороте: секунды запаздывания и потолок в пикселях.
const BEND_LAG := 0.035
const BEND_MAX := 7.0
## То же для ствола платформы, радианы.
const BARREL_LAG := 0.03
const BARREL_MAX := 0.1


func _jelly_setup() -> void:
	_wob.clear()
	for i in mirrors.size() + 1:
		var w := Wobble.new()
		w.vis_angle = emitter_angle if i == 0 else mirrors[i - 1].angle
		w.side.value = PRISM_H
		_wob.append(w)
	_body = JellyShape.rect(Vector2(PLATFORM_SIZE, PLATFORM_SIZE), float(Style.R_CTL), 40)
	_ring_shape = JellyShape.circle(target_r, 40)
	_dot = JellyShape.circle(target_r * 0.3, 24)
	_body.snap(_emitter_pos())
	_ring_shape.snap(target)
	_dot.snap(target)
	_wob[0].lift.value = Jelly.tuning().lift_px


## Управление перешло: прежний элемент сжимается и опускается, новое зеркало вздрагивает
## дугой и толщиной, от его оси круг, луч на миг толстеет.
func _jelly_handoff(from: int, to: int) -> void:
	if _wob.is_empty():
		return
	if from == 0:
		_body.poke(-160.0)
		_wob[0].swell.kick(-120.0)
	else:
		_wob[from].bow.kick(-50.0)
		_wob[from].swell.kick(-30.0)
	var w := _wob[to]
	w.bow.kick(90.0)
	w.swell.kick(55.0)
	_rings.add(mirrors[to - 1].pos, 8.0, MIRROR_LEN * 0.55, Color(Style.SUCCESS, 0.35), 1, 0.6)
	_beam_pulse.kick(45.0)


## A вхолостую: текущий элемент вдавливается в бортик и вздрагивает вбок.
func _jelly_deny() -> void:
	if _wob.is_empty():
		return
	var w := _wob[current]
	w.press_left = 0.12
	if current == 0:
		_body.push(Vector2(240.0, 0.0))
	else:
		w.bow.kick(70.0 if rng.randf() < 0.5 else -70.0)
		w.swell.kick(-35.0)


## B: зеркала встают на старт рывком и качаются, платформа вздрагивает.
func _jelly_restart() -> void:
	if _wob.is_empty():
		return
	_wob[0].vis_angle = emitter_angle
	_body.poke(220.0)
	for i in mirrors.size():
		var w := _wob[i + 1]
		w.vis_angle += _angle_step(mirrors[i].angle, w.vis_angle)
		w.bow.kick(110.0 if i % 2 == 0 else -110.0)
		w.swell.kick(25.0)


## Мишень зажглась: она и зеркала вздрагивают, от мишени два круга.
func _jelly_lit() -> void:
	if _wob.is_empty():
		return
	_ring_shape.poke(300.0)
	_dot.poke(380.0)
	for i in range(1, _wob.size()):
		_wob[i].swell.kick(40.0)
	_rings.add(target, target_r, target_r * 1.8, Color(Style.SUCCESS, 0.4), 2, 0.8)
	_beam_pulse.kick(60.0)


## Кратчайший поворот от непрерывного угла `vis` к игровому `a` (зеркало симметрично, модуль PI).
static func _angle_step(a: float, vis: float) -> float:
	return fposmod(a - vis + PI / 2.0, PI) - PI / 2.0


## Мармелад живёт и после финиша, пока сцена на экране; на паузе стоит.
func _process(delta: float) -> void:
	super(delta)
	if _body == null or paused or delta <= 0.0:
		return
	var tu := Jelly.tuning()
	var k := tu.spring_stiffness
	var c := tu.spring_damping
	_jt += delta
	_rings.step(delta)
	_spring(_beam_pulse, delta, k, c)
	# Платформа: ствол отстаёт от поворота, тело стоит на месте и только вздрагивает.
	var w0 := _wob[0]
	var omega := (emitter_angle - w0.vis_angle) / delta
	w0.vis_angle = emitter_angle
	_spring(w0.bend, delta, k, c, clampf(-omega * BARREL_LAG, -BARREL_MAX, BARREL_MAX))
	_spring(w0.swell, delta, k, c)
	_step_lift(0, delta)
	_follow(_body, delta, _emitter_pos())
	# Зеркала: концы отстают от поворота, после остановки качаются.
	for i in mirrors.size():
		var w := _wob[i + 1]
		var d := _angle_step(mirrors[i].angle, w.vis_angle)
		w.vis_angle += d
		var bend_goal := clampf(-d / delta * BEND_LAG * MIRROR_LEN / 2.0, -BEND_MAX, BEND_MAX)
		_spring(w.bend, delta, k, c * 0.8, bend_goal)
		_spring(w.bow, delta, k, c)
		_spring(w.swell, delta, k, c)
		if mirrors[i].prism:
			_spring(w.side, delta, k * 2.0, c * 1.2, PRISM_H * _prism_sign(i))
		_step_lift(i + 1, delta)
	_follow(_ring_shape, delta, target)
	_follow(_dot, delta, target)
	queue_redraw()


func _spring(s: JellySpring, delta: float, k: float, c: float, goal := 0.0) -> void:
	if Jelly.on():
		s.step(delta, k, c, goal)
	else:
		s.value = goal
		s.velocity = 0.0


## Бортик текущего элемента: поднят и едва дышит, пока им можно управлять (как `JellyLift`).
func _step_lift(idx: int, delta: float) -> void:
	var tu := Jelly.tuning()
	var w := _wob[idx]
	var goal := 0.0
	if running and not hit_target and idx == current:
		goal = tu.lift_px
		if Jelly.on():
			goal += sin(_jt * 2.2 + idx) * tu.lift_breathe
	if w.press_left > 0.0:
		goal = minf(goal, tu.lift_press)
	w.press_left -= delta
	if Jelly.on():
		var k := tu.ui_stiffness * 1.6
		# Вверх с лёгким перелётом, вниз без него: бортик не мигает, проходя через ноль.
		var damping := tu.ui_damping * 1.1 if goal > w.lift.value else 2.0 * sqrt(k)
		w.lift.step(delta, k, damping, goal)
	else:
		w.lift.value = goal
		w.lift.velocity = 0.0
	if goal <= 0.0 and w.lift.value < 0.2:
		w.lift.value = 0.0
		w.lift.velocity = 0.0


## Мягкое тело к игровой точке. Своя тяжесть и посадка тела опускают его на постоянную
## величину, её возвращаем: контур совпадает с точной геометрией.
func _follow(shape: JellyShape, delta: float, center: Vector2) -> void:
	if not Jelly.on():
		shape.snap(center)
		return
	var tu := Jelly.tuning()
	var sag := tu.blob_gravity / tu.blob_stiffness + tu.blob_sit * shape.blob.radius
	shape.follow(delta, center - Vector2(0.0, sag))


## С какой стороны оси вершина призмы в игре: игровой угол отличается от непрерывного на PI.
func _prism_sign(i: int) -> float:
	return 1.0 if cos(mirrors[i].angle - _wob[i + 1].vis_angle) >= 0.0 else -1.0


## Ось зеркала с изгибом: S от поворота и дуга от вздрога, середина на оси.
func _mirror_curve(i: int, offset := Vector2.ZERO) -> PackedVector2Array:
	var w := _wob[i + 1]
	var dir := Vector2(cos(w.vis_angle), sin(w.vis_angle))
	var nrm := Vector2(-dir.y, dir.x)
	var pts := PackedVector2Array()
	for j in CURVE_POINTS + 1:
		var s := -1.0 + 2.0 * j / CURVE_POINTS
		var off := w.bend.value * s * s * s - w.bow.value * s * s
		pts.append(mirrors[i].pos + offset + dir * s * MIRROR_LEN / 2.0 + nrm * off)
	return pts


func _prism_poly(i: int, offset := Vector2.ZERO) -> PackedVector2Array:
	var w := _wob[i + 1]
	var nrm := Vector2(-sin(w.vis_angle), cos(w.vis_angle))
	var pts := _mirror_curve(i, offset)
	pts.append(mirrors[i].pos + offset + nrm * w.side.value)
	return pts


# --- Рисование ----------------------------------------------------------------------------

func _draw() -> void:
	if def == null or mirrors.is_empty() or _body == null:
		return
	var lit := _target_lit()
	var bw := maxf(BEAM_WIDTH + _beam_pulse.value, 2.0)
	# Луч: свечение и ядро отдельными отрезками, чтобы на изломах толщина не менялась.
	for p in paths:
		for i in range(1, p.size()):
			draw_line(p[i - 1], p[i], Color(Style.accent(0), 0.25), bw * 3.0, true)
	for p in paths:
		for i in range(1, p.size()):
			draw_line(p[i - 1], p[i], Style.accent(0), bw, true)
			if i < p.size() - 1:
				draw_circle(p[i], bw / 2.0, Style.accent(0))
	_rings.draw(self)
	# Платформа: текущая стоит на бортике.
	var e := _emitter_pos()
	var w0 := _wob[0]
	_body.draw_lifted(self, Style.INK if current == 0 else Style.INK_3, w0.lift.value)
	var barrel := Vector2.from_angle(emitter_angle + w0.bend.value) * maxf(BARREL_LEN + w0.swell.value, 20.0)
	draw_line(e, e + barrel, Style.SURFACE_SOLID, 6.0, true)
	# Зеркала и призма: текущее на бортике.
	for i in mirrors.size():
		var m := mirrors[i]
		var w := _wob[i + 1]
		var col := Style.SUCCESS if activated[i] else (Style.INK if current == i + 1 else Style.INK_3)
		var lift := w.lift.value
		if m.prism:
			if absf(w.side.value) > 4.0:
				var top := _prism_poly(i)
				if lift > 0.2:
					# Бортик только там, где его не закрывает полупрозрачная призма.
					# Сдвинутая копия дыр не даёт: все куски внешние.
					for part in Geometry2D.clip_polygons(_prism_poly(i, Vector2(0.0, lift)), top):
						Jelly.fill(self, part, Color(Jelly.lip_color(col), 0.85))
				Jelly.fill(self, top, Color(col, 0.85))
			else:
				draw_polyline(_mirror_curve(i), Color(col, 0.85), MIRROR_WIDTH * 0.6, true)
		else:
			var width := maxf(MIRROR_WIDTH + w.swell.value, 4.0)
			if lift > 0.2:
				draw_polyline(_mirror_curve(i, Vector2(0.0, lift)), Jelly.lip_color(col), width - 2.0, true)
			draw_polyline(_mirror_curve(i), col, width, true)
		draw_circle(m.pos, 7.0, Style.SURFACE_SOLID)
		draw_arc(m.pos, 7.0, 0.0, TAU, 24, col, 3.0, true)
	# Мишень: мягкое кольцо и точка, догоняют движение.
	_ring_shape.draw_outline(self, Style.SUCCESS if lit else Style.accent(1), 8.0)
	_dot.draw(self, Style.SUCCESS if lit else Color(Style.accent(1), 0.6))
