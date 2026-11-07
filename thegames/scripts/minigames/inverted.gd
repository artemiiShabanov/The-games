extends Minigame
## «Выведи» (inverted, управление), каталог `docs/specs/minigames_catalog.md`. Лабиринт 5×5,
## точка в центре, выход в одном из углов. Лабиринты чередуются: в нечётном стрелки двигают
## точку, в чётном точка стоит в центре экрана, а стрелки двигают сам лабиринт под ней (нажал
## вправо: лабиринт уехал вправо, точка оказалась в клетке левее). Стены не пускают в обоих
## режимах; какой режим сейчас, видно по тому, что движется. 2-3 лабиринта за 20 с; провал,
## если не прошёл их до таймера. Параметры от `t` в `resources/minigames/inverted.tres`:
## mazes (число), twist (запутанность: 0 длинные коридоры, 1 частые развилки), flip (через
## сколько ходов режим меняется посреди лабиринта, 0 никогда).

enum Mode { DOT, MAZE }

const N := 5
const CELL := 112.0
const WALL := 8.0
const DOT_R := 26.0
const MOVE_SECONDS := 0.11
const SHAKE_SECONDS := 0.25
const FLASH_SECONDS := 0.4
const BOT_STEP := 0.16
## Стены клетки битами: верх, право, низ, лево.
const DIRS: Array[Vector2i] = [Vector2i(0, -1), Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0)]

var mazes_total := 2
var twist := 0.0
var flip_moves := 0

var walls: Array[int] = []
var cell := Vector2i(2, 2)
var exit_cell := Vector2i(0, 0)
var mode := Mode.DOT
var maze_index := 0
var moves_in_mode := 0
var anim_from := Vector2.ZERO
var anim_to := Vector2.ZERO
var anim := 1.0
var shake := 0.0
var shake_dir := Vector2.ZERO
var flash := 0.0
var _bot_timer := 0.0
var _step_sound: AudioStreamPlayer
var _bump: AudioStreamPlayer
var _done_sound: AudioStreamPlayer
var _flip_sound: AudioStreamPlayer


func _on_start() -> void:
	mazes_total = maxi(int(round(def.param(&"mazes", t, 2.0))), 1)
	twist = clampf(def.param(&"twist", t, 0.0), 0.0, 1.0)
	flip_moves = maxi(int(round(def.param(&"flip", t, 0.0))), 0)
	_step_sound = Sfx.player(Sfx.blip(700.0, 0.04, 0.2, 50.0))
	_bump = Sfx.player(Sfx.thud(0.08, 0.35))
	_done_sound = Sfx.player(Sfx.blip(880.0, 0.18, 0.45, 12.0))
	_flip_sound = Sfx.player(Sfx.blip(440.0, 0.12, 0.3, 18.0))
	for p in [_step_sound, _bump, _done_sound, _flip_sound]:
		add_child(p)
	_new_maze()
	queue_redraw()


# --- Лабиринт -------------------------------------------------------------------------------

func _idx(c: Vector2i) -> int:
	return c.y * N + c.x


func _has_wall(c: Vector2i, d: int) -> bool:
	return walls[_idx(c)] & (1 << d) != 0


## Идеальный лабиринт обходом в глубину; `twist` 0 тянет коридоры прямо, 1 ветвит на каждом шагу.
func _new_maze() -> void:
	walls.clear()
	for i in N * N:
		walls.append(15)
	var visited: Array[bool] = []
	visited.resize(N * N)
	visited.fill(false)
	var stack: Array[Vector2i] = [Vector2i(2, 2)]
	var last_dir := -1
	visited[_idx(Vector2i(2, 2))] = true
	while not stack.is_empty():
		var c: Vector2i = stack.back()
		var options: Array[int] = []
		for d in 4:
			var n := c + DIRS[d]
			if n.x >= 0 and n.x < N and n.y >= 0 and n.y < N and not visited[_idx(n)]:
				options.append(d)
		if options.is_empty():
			stack.pop_back()
			last_dir = -1
			continue
		var d := options[rng.randi_range(0, options.size() - 1)]
		if last_dir >= 0 and options.has(last_dir) and rng.randf() > twist:
			d = last_dir
		var n := c + DIRS[d]
		walls[_idx(c)] &= ~(1 << d)
		walls[_idx(n)] &= ~(1 << ((d + 2) % 4))
		visited[_idx(n)] = true
		stack.append(n)
		last_dir = d
	cell = Vector2i(2, 2)
	var corners: Array[Vector2i] = [Vector2i(0, 0), Vector2i(N - 1, 0), Vector2i(0, N - 1), Vector2i(N - 1, N - 1)]
	exit_cell = corners[rng.randi_range(0, 3)]
	mode = Mode.MAZE if maze_index % 2 == 1 else Mode.DOT
	moves_in_mode = 0
	anim_from = Vector2(cell)
	anim_to = anim_from
	anim = 1.0


func _flip_mode() -> void:
	mode = Mode.MAZE if mode == Mode.DOT else Mode.DOT
	moves_in_mode = 0
	flash = FLASH_SECONDS
	_flip_sound.play()


# --- Ввод и шаг -----------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	var d := -1
	if event.is_action_pressed(GameInput.UP):
		d = 0
	elif event.is_action_pressed(GameInput.RIGHT):
		d = 1
	elif event.is_action_pressed(GameInput.DOWN):
		d = 2
	elif event.is_action_pressed(GameInput.LEFT):
		d = 3
	else:
		return
	_press(d)
	get_viewport().set_input_as_handled()


## Нажатие стрелки: в режиме точки точка идёт туда, в режиме лабиринта лабиринт едет туда,
## то есть точка попадает в клетку напротив.
func _press(d: int) -> void:
	if anim < 1.0:
		return
	var move_dir := d if mode == Mode.DOT else (d + 2) % 4
	if _has_wall(cell, move_dir):
		shake = SHAKE_SECONDS
		shake_dir = Vector2(DIRS[d])
		_bump.play()
		return
	anim_from = Vector2(cell)
	cell += DIRS[move_dir]
	anim_to = Vector2(cell)
	anim = 0.0
	_step_sound.play()


func _on_tick(delta: float) -> void:
	shake = maxf(shake - delta, 0.0)
	flash = maxf(flash - delta, 0.0)
	if anim < 1.0:
		anim = minf(anim + delta / MOVE_SECONDS, 1.0)
		if anim >= 1.0:
			_arrived()
	queue_redraw()


func _arrived() -> void:
	if cell == exit_cell:
		maze_index += 1
		_done_sound.play()
		if maze_index >= mazes_total:
			finish(true)
			return
		_new_maze()
		return
	moves_in_mode += 1
	if flip_moves > 0 and moves_in_mode >= flip_moves:
		_flip_mode()


func _on_timeout() -> bool:
	return maze_index >= mazes_total


## Бот: WIN идёт по кратчайшему пути с учётом режима, LOSE стоит.
func _bot_step(delta: float) -> bool:
	if AutoTest.bot_mode != AutoTest.BotMode.WIN or anim < 1.0:
		return false
	_bot_timer += delta
	if _bot_timer < BOT_STEP:
		return false
	_bot_timer = 0.0
	var d := _next_dir()
	if d >= 0:
		_press(d if mode == Mode.DOT else (d + 2) % 4)
	return false


## Первый шаг кратчайшего пути от текущей клетки к выходу (поиск в ширину).
func _next_dir() -> int:
	var prev := {}
	var queue: Array[Vector2i] = [cell]
	prev[cell] = Vector2i(-1, -1)
	while not queue.is_empty():
		var c: Vector2i = queue.pop_front()
		if c == exit_cell:
			break
		for d in 4:
			if _has_wall(c, d):
				continue
			var n := c + DIRS[d]
			if not prev.has(n):
				prev[n] = c
				queue.append(n)
	if not prev.has(exit_cell):
		return -1
	var step := exit_cell
	while prev[step] != cell:
		step = prev[step]
	for d in 4:
		if cell + DIRS[d] == step:
			return d
	return -1


# --- Рисование ----------------------------------------------------------------------------

func _draw() -> void:
	if def == null or walls.is_empty():
		return
	var center := size / 2.0 + Vector2(0, 10)
	var grid := Vector2(N, N) * CELL
	var pos := anim_from.lerp(anim_to, ease(anim, -1.8))
	var dot_local := (pos + Vector2(0.5, 0.5)) * CELL
	var jolt := shake_dir * sin(shake * 50.0) * 8.0 * shake / SHAKE_SECONDS
	var origin: Vector2
	var dot_screen: Vector2
	if mode == Mode.DOT:
		origin = center - grid / 2.0
		dot_screen = origin + dot_local + jolt
	else:
		# Точка стоит в центре экрана, лабиринт едет под ней.
		dot_screen = center
		origin = center - dot_local - jolt
	# Подложка и клетка выхода.
	Style.flat(Color(Style.INK, 0.04), Style.R_CTL, Color.TRANSPARENT, 0).draw(get_canvas_item(), Rect2(origin - Vector2(WALL, WALL), grid + Vector2(WALL, WALL) * 2.0))
	var exit_rect := Rect2(origin + Vector2(exit_cell) * CELL + Vector2(14, 14), Vector2(CELL - 28, CELL - 28))
	Style.flat(Color(Style.accent(1), 0.9), Style.R_CTL, Color.TRANSPARENT, 0).draw(get_canvas_item(), exit_rect)
	# Стены.
	var ink := Style.INK if flash <= 0.0 else Style.INK.lerp(Style.FOCUS, flash / FLASH_SECONDS)
	for y in N:
		for x in N:
			var c := Vector2i(x, y)
			var p := origin + Vector2(c) * CELL
			if _has_wall(c, 0):
				draw_line(p, p + Vector2(CELL, 0), ink, WALL, true)
			if _has_wall(c, 3):
				draw_line(p, p + Vector2(0, CELL), ink, WALL, true)
			if _has_wall(c, 1):
				draw_line(p + Vector2(CELL, 0), p + Vector2(CELL, CELL), ink, WALL, true)
			if _has_wall(c, 2):
				draw_line(p + Vector2(0, CELL), p + Vector2(CELL, CELL), ink, WALL, true)
	draw_circle(dot_screen, DOT_R, Style.accent(0))
	# Подпись режима снизу: что сейчас двигается.
	var font := ThemeDB.fallback_font
	var caption := "двигается точка" if mode == Mode.DOT else "двигается лабиринт"
	var w := font.get_string_size(caption, HORIZONTAL_ALIGNMENT_LEFT, -1, Style.FONT_H2).x
	draw_string(font, Vector2(size.x / 2.0 - w / 2.0, size.y - 112.0), caption, HORIZONTAL_ALIGNMENT_LEFT, -1, Style.FONT_H2,
			Style.INK if flash <= 0.0 else Style.FOCUS)
	# Лабиринты справа сверху.
	var r := 7.0
	var gap := 28.0
	var x0 := size.x - 48.0 - (mazes_total - 1) * gap
	for j in mazes_total:
		var col := Style.SURFACE_2
		if j < maze_index:
			col = Style.SUCCESS
		elif j == maze_index:
			col = Style.INK
		draw_circle(Vector2(x0 + j * gap, 60.0), r, col)
