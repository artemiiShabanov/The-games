extends Minigame
## «Подгони» (fit_frame, оптимизация), каталог `docs/specs/minigames_catalog.md`.
## Вся карточка это поверхность мутной жидкости (тарелки нет). Из глубины по одной всплывают
## правильные многоугольники двух цветов: сначала размытое пятно, потом чёткая фигура; каждая
## всплывает в своём месте около центра и покачивается на волнах. Слева и справа трафареты,
## по одному на цвет; ↑ ↓ меняют число сторон у обоих сразу, ← → отправляют фигуру в трафарет.
## Совпали цвет и стороны: влетает, трафарет пружинит. Нет: фигура и трафарет трясутся, фигура
## тонет. Не успел: тонет. Провал при двух непопавших. (Компоновка и анимации: решения
## 2026-11-05 по плейтесту.)
## Параметры от `t` в `resources/minigames/fit_frame.tres`: shapes, rise, hold, sides_max.

enum State { NONE, RISING, READY, HIT, MISS, SINK }

const MIN_SIDES := 3
const MAX_SIDES := 8
const SHAPE_R := 84.0
const STENCIL_R := 110.0
const STENCIL_WIDTH := 22.0
const STENCIL_OFFSET := 540.0
const SPAWN_SPREAD := 140.0
const HIT_SECONDS := 0.22
const MISS_SECONDS := 0.5
const GAP_SECONDS := 0.3
const FLASH_SECONDS := 0.3
const BOUNCE_SECONDS := 0.45
const SHAKE_SECONDS := 0.35
const FAIL_AT := 2
const BOT_REACTION := 0.25

var shapes_total := 6
var rise_seconds := 1.0
var hold_seconds := 1.5
var sides_max := 6

var stencil_sides := 5
var spawned := 0
var hits := 0
var misses := 0
var results: Array[bool] = []
var gap_left := 0.4

var state := State.NONE
var cur_sides := 3
var cur_color := 0
var cur_age := 0.0
var cur_target := 0
## Своё место всплытия и фаза покачивания у каждой фигуры.
var cur_origin := Vector2.ZERO
var cur_phase := 0.0
var flash: Array[float] = [0.0, 0.0]
var bounce: Array[float] = [0.0, 0.0]
var shake: Array[float] = [0.0, 0.0]

## Прототип мармелада (ветка proto/jelly): вид поверх того же геймплея, `Jelly.on()` выбирает
## рисунок. Фигура мягким телом, трафареты упругими контурами, круги по жидкости.
var jelly_shape: SoftBlob
var jelly_stencils: Array[SoftOutline] = []
var jelly_shake: Array[JellySpring] = []
var jelly_rings := RingFx.new()


func _on_start() -> void:
	shapes_total = int(round(def.param(&"shapes", t, 6.0)))
	rise_seconds = def.param(&"rise", t, 1.0)
	hold_seconds = def.param(&"hold", t, 1.5)
	sides_max = clampi(int(round(def.param(&"sides_max", t, 6.0))), MIN_SIDES + 1, MAX_SIDES)
	stencil_sides = rng.randi_range(MIN_SIDES, sides_max)
	_setup_jelly()
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	if event.is_action_pressed(GameInput.UP):
		_set_stencil_sides(mini(stencil_sides + 1, MAX_SIDES))
	elif event.is_action_pressed(GameInput.DOWN):
		_set_stencil_sides(maxi(stencil_sides - 1, MIN_SIDES))
	elif event.is_action_pressed(GameInput.LEFT):
		_send(0)
	elif event.is_action_pressed(GameInput.RIGHT):
		_send(1)
	else:
		return
	get_viewport().set_input_as_handled()
	queue_redraw()


func _on_tick(delta: float) -> void:
	for i in 2:
		flash[i] = maxf(flash[i] - delta, 0.0)
		bounce[i] = maxf(bounce[i] - delta, 0.0)
		shake[i] = maxf(shake[i] - delta, 0.0)
	cur_age += delta
	match state:
		State.NONE:
			gap_left -= delta
			if gap_left <= 0.0 and spawned < shapes_total:
				_spawn()
		State.RISING:
			if cur_age >= rise_seconds:
				state = State.READY
				cur_age = 0.0
		State.READY:
			if cur_age >= hold_seconds:
				ShellSounds.play(&"miss")
				_miss(State.SINK)
		State.HIT:
			if cur_age >= HIT_SECONDS:
				bounce[cur_target] = BOUNCE_SECONDS
				_jelly_hit(cur_target)
				_resolve()
		State.MISS, State.SINK:
			if cur_age >= MISS_SECONDS:
				_resolve()
	queue_redraw()


func _on_timeout() -> bool:
	return misses < FAIL_AT


## Бот: WIN подгоняет стороны и отправляет в нужный трафарет, LOSE ничего не трогает.
func _bot_step(_delta: float) -> bool:
	if AutoTest.bot_mode == AutoTest.BotMode.WIN and state == State.READY and cur_age >= BOT_REACTION:
		_set_stencil_sides(cur_sides)
		_send(cur_color)
	return false


func _spawn() -> void:
	spawned += 1
	var sides := rng.randi_range(MIN_SIDES, sides_max)
	if sides == cur_sides and sides_max > MIN_SIDES:
		sides = MIN_SIDES + (sides - MIN_SIDES + 1) % (sides_max - MIN_SIDES + 1)
	cur_sides = sides
	cur_color = rng.randi_range(0, 1)
	var a := rng.randf_range(0.0, TAU)
	cur_origin = Vector2(cos(a), sin(a)) * rng.randf_range(0.0, SPAWN_SPREAD)
	cur_phase = rng.randf_range(0.0, TAU)
	state = State.RISING
	cur_age = 0.0
	_jelly_spawn()


func _send(target: int) -> void:
	if state != State.RISING and state != State.READY:
		return
	cur_target = target
	if target == cur_color and stencil_sides == cur_sides:
		hits += 1
		results.append(true)
		flash[target] = FLASH_SECONDS
		state = State.HIT
		cur_age = 0.0
		ShellSounds.play(&"hit")
	else:
		shake[target] = SHAKE_SECONDS
		ShellSounds.play(&"miss")
		jelly_shake[target].kick(900.0 * (1.0 if target == 1 else -1.0))
		_miss(State.MISS)


func _miss(next: State) -> void:
	if next == State.SINK:
		jelly_rings.add(size / 2.0 + cur_origin, SHAPE_R * 0.5, SHAPE_R * 1.6, Color(Style.INK, 0.14), 2, 0.9)
	misses += 1
	results.append(false)
	state = next
	cur_age = 0.0


func _resolve() -> void:
	state = State.NONE
	gap_left = GAP_SECONDS
	if misses >= FAIL_AT:
		finish(false)
	elif spawned >= shapes_total:
		finish(true)


# --- Рисование ----------------------------------------------------------------------------

func _draw() -> void:
	if def == null:
		return
	if Jelly.on() and jelly_shape != null:
		_draw_jelly()
		_draw_dots()
		return
	var center := size / 2.0
	var stencil_pos: Array[Vector2] = [center + Vector2(-STENCIL_OFFSET, 0), center + Vector2(STENCIL_OFFSET, 0)]
	for i in 2:
		var col := Style.accent(i)
		var pos := stencil_pos[i] + Vector2(_shake_offset(shake[i], SHAKE_SECONDS, 12.0), 0)
		var pts := _polygon(pos, STENCIL_R * _bounce_scale(bounce[i]), stencil_sides, 0.0)
		if flash[i] > 0.0:
			draw_colored_polygon(pts, Color(col, 0.35 * flash[i] / FLASH_SECONDS))
		_draw_outline(pts, col, STENCIL_WIDTH)

	var home := center + cur_origin
	match state:
		State.RISING:
			var p := clampf(cur_age / rise_seconds, 0.0, 1.0)
			_draw_shape(home + _float_offset(cur_age), lerpf(0.6, 1.0, p), Style.accent(cur_color), p, 1.0 - p, cur_age)
		State.READY:
			var age := rise_seconds + cur_age
			_draw_shape(home + _float_offset(age), 1.0, Style.accent(cur_color), 1.0, 0.25, age)
		State.HIT:
			var p := clampf(cur_age / HIT_SECONDS, 0.0, 1.0)
			var e := 1.0 - (1.0 - p) * (1.0 - p)
			var pos := home.lerp(stencil_pos[cur_target], e)
			_draw_shape(pos, lerpf(1.0, STENCIL_R / SHAPE_R * 0.8, e), Style.accent(cur_color), 1.0, 0.0, 0.0)
		State.MISS:
			var p := clampf(cur_age / MISS_SECONDS, 0.0, 1.0)
			var pos := home + Vector2(_shake_offset(MISS_SECONDS - cur_age, MISS_SECONDS, 14.0), 0)
			var col := Style.accent(cur_color).lerp(Style.INK_3, p)
			_draw_shape(pos, lerpf(1.0, 0.6, p), col, 1.0 - p * 0.9, p * 0.5, 0.0)
		State.SINK:
			var p := clampf(cur_age / MISS_SECONDS, 0.0, 1.0)
			var col := Style.accent(cur_color).lerp(Style.INK_3, p)
			_draw_shape(home, lerpf(1.0, 0.5, p), col, 1.0 - p, p, 0.0)

	_draw_dots()


func _draw_dots() -> void:
	var r := 7.0
	var gap := 28.0
	var x0 := size.x - 48.0 - (shapes_total - 1) * gap
	for i in shapes_total:
		var c := Style.SURFACE_2
		if i < results.size():
			c = Style.SUCCESS if results[i] else Style.INK_3
		elif i == results.size() and state != State.NONE:
			c = Style.INK
		draw_circle(Vector2(x0 + i * gap, 60.0), r, c)


## Дрейф на волнах: мелкое частое покачивание около места всплытия (плейтест 2026-11-05).
func _float_offset(age: float) -> Vector2:
	return Vector2(sin(age * 2.6 + cur_phase) * 3.0, cos(age * 2.1 + cur_phase) * 4.0)


## Тряска: затухающая синусоида, `left` сколько осталось.
func _shake_offset(left: float, total: float, amp: float) -> float:
	if left <= 0.0:
		return 0.0
	var k := left / total
	return sin(left * 45.0) * amp * k


## Пружина трафарета после попадания: перелёт и короткий второй отскок.
func _bounce_scale(left: float) -> float:
	if left <= 0.0:
		return 1.0
	var p := 1.0 - left / BOUNCE_SECONDS
	return 1.0 + 0.22 * sin(p * PI) * (1.0 - p) + 0.06 * sin(p * TAU) * (1.0 - p)


## Фигура с размытием: `blur` 1 это пятно, 0 чёткий многоугольник. `wobble_age` > 0 даёт
## покачивание на волнах: лёгкий наклон, как у плавающей пластинки (сжатие вдоль плывущей оси).
func _draw_shape(pos: Vector2, scale_: float, col: Color, alpha: float, blur: float, wobble_age: float) -> void:
	var radius := SHAPE_R * scale_
	if blur > 0.0:
		for k in 6:
			draw_circle(pos, radius * (1.6 - k * 0.15), Color(col, 0.07 * blur * alpha))
	if alpha > 0.0 and blur < 1.0:
		var pts := _polygon(Vector2.ZERO, radius, cur_sides, 0.0)
		if wobble_age > 0.0:
			var axis := wobble_age * 1.2 + cur_phase
			var squash := 1.0 - 0.05 * (0.5 + 0.5 * sin(wobble_age * 3.5 + cur_phase))
			var tilt := Transform2D(axis, Vector2.ZERO) * Transform2D(0.0, Vector2(squash, 1.0), 0.0, Vector2.ZERO) * Transform2D(-axis, Vector2.ZERO)
			var rot := Transform2D(sin(wobble_age * 2.4 + cur_phase) * 0.03, Vector2.ZERO)
			pts = (rot * tilt) * pts
		for i in pts.size():
			pts[i] += pos
		draw_colored_polygon(pts, Color(col, alpha * (1.0 - blur * 0.6)))


func _polygon(center: Vector2, radius: float, sides: int, rot: float) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in sides:
		var a := -PI / 2.0 + rot + TAU * i / sides
		pts.append(center + Vector2(cos(a), sin(a)) * radius)
	return pts


func _draw_outline(pts: PackedVector2Array, col: Color, width: float) -> void:
	var closed := PackedVector2Array(pts)
	closed.append(pts[0])
	draw_polyline(closed, col, width, true)
	for p in pts:
		draw_circle(p, width / 2.0, col)


# --- Мармелад (прототип, ветка proto/jelly) -------------------------------------------------

func _setup_jelly() -> void:
	Jelly.register_debug()
	jelly_shape = SoftBlob.new(SHAPE_R)
	jelly_shape.stretch_free = true
	for i in 2:
		var o := SoftOutline.new()
		o.sides = stencil_sides
		o.radius = STENCIL_R
		jelly_stencils.append(o)
		jelly_shake.append(JellySpring.new())


func _stencil_home(i: int) -> Vector2:
	return size / 2.0 + Vector2(-STENCIL_OFFSET if i == 0 else STENCIL_OFFSET, 0.0)


## Смена сторон трафаретов: контуры перетекают сами, а совпавшая фигура радостно вздрагивает.
func _set_stencil_sides(n: int) -> void:
	if n == stencil_sides:
		return
	stencil_sides = n
	if jelly_shape == null:
		return
	for o in jelly_stencils:
		o.pulse(-60.0)
	if (state == State.RISING or state == State.READY) and n == cur_sides:
		jelly_shape.pulse(160.0)


func _jelly_spawn() -> void:
	if jelly_shape == null:
		return
	jelly_shape.set_shape(SoftBlob.polygon_shape(cur_sides, SHAPE_R, 48))
	jelly_shape.shape_scale = 0.6
	jelly_shape.angle = 0.0
	jelly_shape.reset(size / 2.0 + cur_origin, 0.85)
	jelly_rings.add(size / 2.0 + cur_origin, SHAPE_R * 0.4, SHAPE_R * 1.5, Color(Style.INK, 0.12), 2, 1.0)


## Фигура влетела: трафарет раздувается, по жидкости круг.
func _jelly_hit(target: int) -> void:
	if jelly_shape == null:
		return
	jelly_stencils[target].pulse(420.0)
	jelly_rings.add(_stencil_home(target), STENCIL_R * 0.9, STENCIL_R * 1.6, Color(Style.accent(target), 0.35), 1, 0.6)


## Мармелад живёт и после финиша, пока сцена на экране; на паузе стоит.
func _process(delta: float) -> void:
	super(delta)
	if jelly_shape == null or paused:
		return
	var tu := Jelly.tuning()
	jelly_rings.step(delta)
	for i in 2:
		jelly_shake[i].step(delta, tu.spring_stiffness, tu.spring_damping * 0.6)
		jelly_stencils[i].sides = stencil_sides
		jelly_stencils[i].step(delta, _stencil_home(i) + Vector2(jelly_shake[i].value * 0.03, 0.0))
	var pose := _shape_pose()
	if pose.z > 0.0:
		jelly_shape.shape_scale = pose.w
		jelly_shape.angle = sin((cur_age + rise_seconds) * 2.4 + cur_phase) * 0.04 if state == State.READY else 0.0
		jelly_shape.collide = false
		jelly_shape.step(delta, Vector2(pose.x, pose.y), Callable())
	if not running:
		queue_redraw()


## Где фигура сейчас: (x, y, видимость 0..1, масштаб); видимость 0 значит фигуры нет.
func _shape_pose() -> Vector4:
	var home := size / 2.0 + cur_origin
	match state:
		State.RISING:
			var p := clampf(cur_age / rise_seconds, 0.0, 1.0)
			var at := home + _float_offset(cur_age)
			return Vector4(at.x, at.y, p, lerpf(0.6, 1.0, p))
		State.READY:
			var at := home + _float_offset(rise_seconds + cur_age)
			return Vector4(at.x, at.y, 1.0, 1.0)
		State.HIT:
			var p := clampf(cur_age / HIT_SECONDS, 0.0, 1.0)
			var e := 1.0 - (1.0 - p) * (1.0 - p)
			var at := home.lerp(_stencil_home(cur_target), e)
			return Vector4(at.x, at.y, 1.0, lerpf(1.0, STENCIL_R / SHAPE_R * 0.8, e))
		State.MISS:
			var p := clampf(cur_age / MISS_SECONDS, 0.0, 1.0)
			var at := home + Vector2(_shake_offset(MISS_SECONDS - cur_age, MISS_SECONDS, 14.0), 0)
			return Vector4(at.x, at.y, 1.0 - p * 0.9, lerpf(1.0, 0.6, p))
		State.SINK:
			var p := clampf(cur_age / MISS_SECONDS, 0.0, 1.0)
			return Vector4(home.x, home.y, 1.0 - p, lerpf(1.0, 0.5, p))
	return Vector4(0.0, 0.0, 0.0, 1.0)


func _draw_jelly() -> void:
	jelly_rings.draw(self)
	for i in 2:
		var col := Style.accent(i)
		var o := jelly_stencils[i]
		if flash[i] > 0.0:
			RunnerJelly.fill(self, o.points, Color(col, 0.35 * flash[i] / FLASH_SECONDS))
		o.draw(self, col, STENCIL_WIDTH)
	var pose := _shape_pose()
	if pose.z <= 0.0 or jelly_shape.points.is_empty():
		return
	var col := Style.accent(cur_color)
	var alpha := pose.z
	var blur := 0.0
	match state:
		State.RISING:
			blur = 1.0 - pose.z
			alpha = pose.z
		State.READY:
			blur = 0.25
		State.MISS, State.SINK:
			var p := clampf(cur_age / MISS_SECONDS, 0.0, 1.0)
			col = col.lerp(Style.INK_3, p)
			blur = p * (0.5 if state == State.MISS else 1.0)
	var at := Vector2(pose.x, pose.y)
	if blur > 0.0:
		for k in 6:
			draw_circle(at, SHAPE_R * pose.w * (1.6 - k * 0.15), Color(col, 0.07 * blur * alpha))
	if alpha > 0.0 and blur < 1.0:
		RunnerJelly.fill(self, jelly_shape.polygon(Vector2.ZERO, 2), Color(col, alpha * (1.0 - blur * 0.6)))
