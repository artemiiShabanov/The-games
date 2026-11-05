extends Minigame
## «Подгони» (fit_frame, оптимизация), каталог `docs/specs/minigames_catalog.md`, концепт `02b`.
## Тарелка с мутной жидкостью, из глубины по одной всплывают правильные многоугольники двух
## цветов: сначала размытое пятно, потом чёткая фигура. Сверху и снизу трафареты, по одному
## на цвет; ← → меняют число сторон у обоих сразу, ↑ ↓ отправляют фигуру в трафарет. Совпали
## цвет и стороны: вошла. Нет или не успел: тонет. Провал при двух непопавших.
## Параметры от `t` в `resources/minigames/fit_frame.tres`: shapes, rise, hold, sides_max.

enum State { NONE, RISING, READY, HIT, MISS, SINK }

const MIN_SIDES := 3
const MAX_SIDES := 8
const PLATE_R := 260.0
const SHAPE_R := 84.0
const STENCIL_R := 110.0
const STENCIL_WIDTH := 22.0
## Центр трафарета чуть внутри борта: нижняя половина прячется под тарелку, как в концепте.
const STENCIL_INSET := 30.0
## Поле приподнято, чтобы нижний трафарет не лез на пилюлю ввода.
const FIELD_SHIFT := Vector2(0, -30)
const HIT_SECONDS := 0.22
const MISS_SECONDS := 0.45
const GAP_SECONDS := 0.3
const FLASH_SECONDS := 0.3
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
var flash: Array[float] = [0.0, 0.0]


func _on_start() -> void:
	shapes_total = int(round(def.param(&"shapes", t, 6.0)))
	rise_seconds = def.param(&"rise", t, 1.0)
	hold_seconds = def.param(&"hold", t, 1.5)
	sides_max = clampi(int(round(def.param(&"sides_max", t, 6.0))), MIN_SIDES + 1, MAX_SIDES)
	stencil_sides = rng.randi_range(MIN_SIDES, sides_max)
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	if event.is_action_pressed(GameInput.LEFT):
		stencil_sides = maxi(stencil_sides - 1, MIN_SIDES)
	elif event.is_action_pressed(GameInput.RIGHT):
		stencil_sides = mini(stencil_sides + 1, MAX_SIDES)
	elif event.is_action_pressed(GameInput.UP):
		_send(0)
	elif event.is_action_pressed(GameInput.DOWN):
		_send(1)
	else:
		return
	get_viewport().set_input_as_handled()
	queue_redraw()


func _on_tick(delta: float) -> void:
	for i in 2:
		flash[i] = maxf(flash[i] - delta, 0.0)
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
				_miss(State.SINK)
		State.HIT:
			if cur_age >= HIT_SECONDS:
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
		stencil_sides = cur_sides
		_send(cur_color)
	return false


func _spawn() -> void:
	spawned += 1
	var sides := rng.randi_range(MIN_SIDES, sides_max)
	if sides == cur_sides and sides_max > MIN_SIDES:
		sides = MIN_SIDES + (sides - MIN_SIDES + 1) % (sides_max - MIN_SIDES + 1)
	cur_sides = sides
	cur_color = rng.randi_range(0, 1)
	state = State.RISING
	cur_age = 0.0


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
	else:
		_miss(State.MISS)


func _miss(next: State) -> void:
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
	var center := size / 2.0 + FIELD_SHIFT
	var stencil_pos: Array[Vector2] = [center + Vector2(0, -PLATE_R + STENCIL_INSET), center + Vector2(0, PLATE_R - STENCIL_INSET)]
	# Трафареты под тарелкой: их нижняя часть прячется под неё, как в концепте.
	for i in 2:
		var col := Style.accent(i)
		var pts := _polygon(stencil_pos[i], STENCIL_R, stencil_sides, PI if i == 1 else 0.0)
		if flash[i] > 0.0:
			draw_colored_polygon(pts, Color(col, 0.35 * flash[i] / FLASH_SECONDS))
		_draw_outline(pts, col, STENCIL_WIDTH)
	# Тарелка с мутной жидкостью.
	draw_circle(center, PLATE_R + 6.0, Color(Style.INK, 0.05))
	draw_circle(center, PLATE_R, Color(0.91, 0.915, 0.93))
	for k in 5:
		draw_circle(center, PLATE_R * (0.92 - k * 0.17), Color(1, 1, 1, 0.22))
	# Фигура.
	match state:
		State.RISING:
			var p := clampf(cur_age / rise_seconds, 0.0, 1.0)
			_draw_shape(center, lerpf(0.6, 1.0, p), Style.accent(cur_color), p, 1.0 - p)
		State.READY:
			_draw_shape(center, 1.0, Style.accent(cur_color), 1.0, 0.25)
		State.HIT:
			var p := clampf(cur_age / HIT_SECONDS, 0.0, 1.0)
			var e := 1.0 - (1.0 - p) * (1.0 - p)
			var pos := center.lerp(stencil_pos[cur_target], e)
			_draw_shape(pos, lerpf(1.0, STENCIL_R / SHAPE_R * 0.8, e), Style.accent(cur_color), 1.0, 0.0)
		State.MISS:
			var p := clampf(cur_age / MISS_SECONDS, 0.0, 1.0)
			var dir := (stencil_pos[cur_target] - center).normalized()
			var pos := center + dir * sin(p * PI) * 70.0
			var col := Style.accent(cur_color).lerp(Style.INK_3, p)
			_draw_shape(pos, lerpf(1.0, 0.6, p), col, 1.0 - p * 0.9, 0.0)
		State.SINK:
			var p := clampf(cur_age / MISS_SECONDS, 0.0, 1.0)
			var col := Style.accent(cur_color).lerp(Style.INK_3, p)
			_draw_shape(center, lerpf(1.0, 0.5, p), col, 1.0 - p, p)
	# Счёт фигур справа сверху поля.
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


## Фигура с размытием: `blur` 1 это пятно, 0 чёткий многоугольник.
func _draw_shape(pos: Vector2, scale_: float, col: Color, alpha: float, blur: float) -> void:
	var radius := SHAPE_R * scale_
	if blur > 0.0:
		for k in 6:
			draw_circle(pos, radius * (1.6 - k * 0.15), Color(col, 0.07 * blur * alpha))
	if alpha > 0.0 and blur < 1.0:
		var pts := _polygon(pos, radius, cur_sides, 0.0)
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
