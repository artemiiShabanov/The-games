extends Minigame
## «Обведи» (trace, графика): ПРОТОТИП на замену «Наведи» (плейтест 2026-11-14, #131), в общий
## набор мини-игр не входит, лежит в `resources/minigames/proto/` и запускается из дебаг-меню.
## На поле ломаная дорожка с пунктиром по середине. Перо едет само с постоянной скоростью,
## стрелки задают направление, за пером остаётся линия. Довести перо до конца дорожки, не
## выйдя из коридора. Вышел: ошибка, перо возвращается на дорожку и на миг замирает. Две
## ошибки или таймер: провал.
## Параметры от `t` в `resources/minigames/proto/trace.tres`: speed (скорость пера, px/с),
## corridor (полуширина коридора, px), segments (звеньев дорожки), max_len (самое длинное
## звено в клетках).

const CELL := 120.0
const COLS := 12
const ROWS := 5
const MAX_ERRORS := 2
const STUN := 0.45
const PEN_R := 14.0
const TRAIL_WIDTH := 10.0
const TRAIL_STEP := 4.0
const FLASH := 0.35

var speed := 240.0
var corridor := 46.0
var segments := 10
var max_len := 3

## Вершины дорожки в координатах поля.
var path := PackedVector2Array()
## Текущее звено: от `path[seg]` к `path[seg + 1]`.
var seg := 0
var pen := Vector2.ZERO
var dir := Vector2.RIGHT
var errors := 0
var stun := 0.0
var trail := PackedVector2Array()

var _flash := 0.0
var _pop := JellySpring.new()


func _on_start() -> void:
	speed = def.param(&"speed", t, 240.0)
	corridor = def.param(&"corridor", t, 46.0)
	segments = maxi(int(round(def.param(&"segments", t, 10.0))), 3)
	max_len = maxi(int(round(def.param(&"max_len", t, 3.0))), 1)
	_build_path()
	pen = path[0]
	dir = (path[1] - path[0]).normalized()
	trail.append(pen)
	queue_redraw()


## Дорожка: случайный путь по клеткам без самопересечений, каждое звено под прямым углом к
## прошлому. Из нескольких попыток берётся самая длинная.
func _build_path() -> void:
	var origin := Vector2((size.x - (COLS - 1) * CELL) / 2.0, (size.y - (ROWS - 1) * CELL) / 2.0 + 16.0)
	var best: Array[Vector2i] = []
	for attempt in 80:
		var cells := _walk()
		if cells.size() > best.size():
			best = cells
		if best.size() > segments:
			break
	path.clear()
	for c in best:
		path.append(origin + Vector2(c) * CELL)


func _walk() -> Array[Vector2i]:
	var at := Vector2i(0, rng.randi_range(0, ROWS - 1))
	var out: Array[Vector2i] = [at]
	var used: Dictionary[Vector2i, bool] = {at: true}
	var last := Vector2i.ZERO
	for s in segments:
		var dirs: Array[Vector2i] = [Vector2i.RIGHT]
		if s > 0:
			dirs = [Vector2i(last.y, last.x), Vector2i(-last.y, -last.x)]
			if rng.randf() < 0.5:
				dirs.reverse()
		var placed := false
		for d in dirs:
			var lens: Array[int] = []
			for l in range(1, max_len + 1):
				lens.insert(rng.randi_range(0, lens.size()), l)
			for l in lens:
				var ok := true
				for k in range(1, l + 1):
					var c := at + d * k
					if c.x < 0 or c.y < 0 or c.x >= COLS or c.y >= ROWS or used.has(c):
						ok = false
						break
				if not ok:
					continue
				for k in range(1, l + 1):
					used[at + d * k] = true
				at += d * l
				last = d
				out.append(at)
				placed = true
				break
			if placed:
				break
		if not placed:
			break
	return out


func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	if event.is_action_pressed(GameInput.UP):
		_turn(Vector2.UP)
	elif event.is_action_pressed(GameInput.DOWN):
		_turn(Vector2.DOWN)
	elif event.is_action_pressed(GameInput.LEFT):
		_turn(Vector2.LEFT)
	elif event.is_action_pressed(GameInput.RIGHT):
		_turn(Vector2.RIGHT)
	else:
		return
	get_viewport().set_input_as_handled()


## Мышь: клик в сторону от пера поворачивает перо туда.
func _mouse_action(button: MouseButton, pos: Vector2) -> StringName:
	if button != MOUSE_BUTTON_LEFT:
		return &""
	return dir_action(pen, pos)


## Повернуть перо; разворот на месте не считается.
func _turn(to: Vector2) -> void:
	if to == dir or to == -dir or stun > 0.0:
		return
	dir = to
	sfx(MiniSfx.Kind.TAP)


static func _closest(p: Vector2, a: Vector2, b: Vector2) -> Vector2:
	return Geometry2D.get_closest_point_to_segment(p, a, b)


func _on_tick(delta: float) -> void:
	_flash = maxf(_flash - delta, 0.0)
	queue_redraw()
	if stun > 0.0:
		stun -= delta
		return
	pen += dir * speed * delta
	if pen.distance_to(trail[trail.size() - 1]) >= TRAIL_STEP:
		trail.append(pen)
	var a := path[seg]
	var b := path[seg + 1]
	var along := (b - a).normalized()
	var d := pen.distance_to(_closest(pen, a, b))
	var last := seg + 2 >= path.size()
	if not last:
		# Повернул на следующее звено: к нему ближе и перо уже идёт вдоль него.
		var c := path[seg + 2]
		var d2 := pen.distance_to(_closest(pen, b, c))
		if d2 <= d and (pen - b).dot((c - b).normalized()) > 0.0:
			seg += 1
			return
	elif (pen - b).dot(along) >= -PEN_R * 0.5 and d <= corridor:
		_pop.kick(6.0)
		sfx(MiniSfx.Kind.WIN)
		finish(true)
		return
	if d > corridor:
		_error()


## Вышел из коридора: ошибка, перо обратно на дорожку (у самого поворота сразу за него).
func _error() -> void:
	errors += 1
	_flash = FLASH
	sfx(MiniSfx.Kind.MISS)
	if errors >= MAX_ERRORS:
		finish(false)
		return
	var a := path[seg]
	var b := path[seg + 1]
	var at := _closest(pen, a, b)
	if at.distance_to(b) <= corridor and seg + 2 < path.size():
		seg += 1
		at = b
	pen = at
	dir = (path[seg + 1] - path[seg]).normalized()
	trail.append(pen)
	stun = STUN


func _on_timeout() -> bool:
	return false


## Бот: WIN ведёт перо по дорожке и поворачивает у вершин, LOSE сворачивает поперёк.
func _bot_step(delta: float) -> bool:
	if stun > 0.0:
		return false
	var a := path[seg]
	var b := path[seg + 1]
	var along := (b - a).normalized()
	if AutoTest.bot_mode != AutoTest.BotMode.WIN:
		_turn(Vector2(along.y, along.x))
		return false
	var want := along
	if seg + 2 < path.size() and (b - pen).dot(along) <= speed * delta:
		want = (path[seg + 2] - b).normalized()
	_turn(want)
	return false


func _process(delta: float) -> void:
	super(delta)
	if def == null or paused:
		return
	var tu := Jelly.tuning()
	_pop.step(delta, tu.spring_stiffness, tu.spring_damping)
	if not running:
		queue_redraw()


func _draw() -> void:
	if def == null or path.size() < 2:
		return
	# Коридор и пунктир по середине.
	var lane := Style.SURFACE_2 if _flash <= 0.0 else Style.SURFACE_2.lerp(Style.DANGER, 0.35 * _flash / FLASH)
	for i in path.size():
		draw_circle(path[i], corridor, lane)
		if i + 1 < path.size():
			draw_line(path[i], path[i + 1], lane, corridor * 2.0)
	for i in path.size() - 1:
		draw_dashed_line(path[i], path[i + 1], Style.INK_3, 3.0, 14.0)
	# Финиш кольцом, старт точкой.
	var goal := path[path.size() - 1]
	draw_circle(goal, PEN_R + 8.0, Style.SUCCESS)
	draw_circle(goal, PEN_R, lane)
	draw_circle(path[0], 8.0, Style.INK_3)
	# Линия за пером и перо.
	if trail.size() >= 2:
		draw_polyline(trail, Style.accent(0), TRAIL_WIDTH, true)
	for p in [trail[0], pen]:
		draw_circle(p, TRAIL_WIDTH / 2.0, Style.accent(0))
	var r := PEN_R * clampf(1.0 + _pop.value * 0.05, 0.7, 1.6)
	draw_circle(pen + Vector2(0.0, 5.0), r, Color(Style.INK, 0.15))
	draw_circle(pen, r, Style.INK if stun <= 0.0 else Style.DANGER)
	draw_circle(pen + dir * (r * 0.45), r * 0.3, Style.SURFACE_SOLID)
	# Ошибки крестиками справа сверху.
	var cr := 7.0
	for j in MAX_ERRORS:
		var col := Style.DANGER if j < errors else Style.SURFACE_2
		var px := size.x - 48.0 - (MAX_ERRORS - 1 - j) * 28.0
		draw_line(Vector2(px - cr, 60.0 - cr), Vector2(px + cr, 60.0 + cr), col, 3.0, true)
		draw_line(Vector2(px - cr, 60.0 + cr), Vector2(px + cr, 60.0 - cr), col, 3.0, true)
