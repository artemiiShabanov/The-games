extends Minigame
## «Залей» (flood_fill, графика), каталог `docs/specs/minigames_catalog.md`.
## Сетка крупных пикселей трёх-четырёх цветов, внизу палитра. ← → выбирают цвет, A заливает из
## левого верхнего угла: связная область угла перекрашивается и поглощает соседей того же цвета.
## Сделать сетку одноцветной за ограниченное число заливок. Две картинки: первая элементарная,
## вторая настоящая. Провал: ходы кончились или время вышло. Запас ходов считается жадным
## решателем, так что решение в запас гарантировано.
## Параметры от `t` в `resources/minigames/flood_fill.tres`: size, colors, slack.

const FIRST_SIZE := 4
const FIRST_COLORS := 3
const FIRST_MAX_GREEDY := 3
const PICTURES := 2
const GRID_PX := 560.0
const CELL_GAP := 4.0
const WAVE_STEP := 0.035
const SWATCH_R := 34.0
const SWATCH_GAP := 36.0
const DONE_PAUSE := 0.6
const BOT_STEP := 0.4

var size_n := 7
var colors_n := 3
var slack := 2

var picture := 0
var n := 4
var k := 3
var grid: PackedInt32Array = []
## Что показывается: отстаёт от `grid` на время волны.
var shown: PackedInt32Array = []
var change_at: PackedFloat32Array = []
var budget := 0
var used := 0
var sel := 0
var done_left := 0.0
var finished_all := false
var _bot_timer := 0.0
var _fill_sound: AudioStreamPlayer
var _done_sound: AudioStreamPlayer
var _miss_sound: AudioStreamPlayer


func _on_start() -> void:
	size_n = int(round(def.param(&"size", t, 7.0)))
	colors_n = clampi(int(round(def.param(&"colors", t, 3.0))), 3, 4)
	slack = int(round(def.param(&"slack", t, 2.0)))
	_fill_sound = Sfx.player(Sfx.blip(520.0, 0.1, 0.35, 22.0))
	_done_sound = Sfx.player(Sfx.blip(880.0, 0.3, 0.45, 8.0))
	_miss_sound = Sfx.player(Sfx.thud())
	add_child(_fill_sound)
	add_child(_done_sound)
	add_child(_miss_sound)
	_new_picture()
	queue_redraw()


func _new_picture() -> void:
	if picture == 0:
		n = FIRST_SIZE
		k = FIRST_COLORS
		# Элементарная: пара заливок.
		for attempt in 200:
			_random_grid()
			if _greedy_length() <= FIRST_MAX_GREEDY:
				break
		budget = _greedy_length() + 1
	else:
		n = size_n
		k = colors_n
		_random_grid()
		budget = _greedy_length() + slack
	used = 0
	sel = 0
	shown = grid.duplicate()
	change_at.resize(n * n)
	change_at.fill(0.0)


func _random_grid() -> void:
	grid.resize(n * n)
	for i in n * n:
		grid[i] = rng.randi_range(0, k - 1)
	# Угол не должен сразу совпадать со всем: гарантируем хотя бы два цвета.
	if _uniform(grid):
		grid[n * n - 1] = (grid[0] + 1) % k


func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo() or done_left > 0.0:
		return
	if event.is_action_pressed(GameInput.LEFT):
		sel = wrapi(sel - 1, 0, k)
	elif event.is_action_pressed(GameInput.RIGHT):
		sel = wrapi(sel + 1, 0, k)
	elif GameInput.is_a(event):
		_fill(sel)
	else:
		return
	get_viewport().set_input_as_handled()
	queue_redraw()


func _on_tick(delta: float) -> void:
	for i in n * n:
		if shown[i] != grid[i] and elapsed >= change_at[i]:
			shown[i] = grid[i]
	if done_left > 0.0:
		done_left -= delta
		if done_left <= 0.0:
			if finished_all:
				finish(true)
			else:
				picture += 1
				_new_picture()
	queue_redraw()


func _on_timeout() -> bool:
	return finished_all


## Бот: WIN заливает жадно лучшим цветом, LOSE льёт цвет угла, тратя ходы впустую.
func _bot_step(delta: float) -> bool:
	if done_left > 0.0:
		return false
	_bot_timer += delta
	if _bot_timer < BOT_STEP:
		return false
	_bot_timer = 0.0
	if AutoTest.bot_mode == AutoTest.BotMode.WIN:
		sel = _greedy_choice(grid)
	else:
		sel = grid[0]
	_fill(sel)
	return false


func _fill(color: int) -> void:
	if done_left > 0.0 or used >= budget:
		return
	used += 1
	var region := _region(grid)
	if color == grid[0]:
		_miss_sound.play()
	else:
		# Волна от угла: клетки старой области меняют цвет по удалению от (0, 0).
		var dist := _distances(region)
		for cell in region:
			grid[cell] = color
			change_at[cell] = elapsed + dist[cell] * WAVE_STEP
		_fill_sound.play()
	if _uniform(grid):
		_done_sound.play()
		finished_all = picture >= PICTURES - 1
		done_left = DONE_PAUSE + n * WAVE_STEP * 2.0
	elif used >= budget:
		done_left = 0.0
		finish(false)


# --- Решатель и геометрия сетки ------------------------------------------------------------

func _uniform(g: PackedInt32Array) -> bool:
	for i in g.size():
		if g[i] != g[0]:
			return false
	return true


## Клетки, связанные с углом тем же цветом.
func _region(g: PackedInt32Array) -> Array[int]:
	var color := g[0]
	var seen := PackedByteArray()
	seen.resize(n * n)
	var out: Array[int] = []
	var stack: Array[int] = [0]
	seen[0] = 1
	while not stack.is_empty():
		var c: int = stack.pop_back()
		out.append(c)
		for nb in _neighbors(c):
			if seen[nb] == 0 and g[nb] == color:
				seen[nb] = 1
				stack.append(nb)
	return out


## Расстояния по сетке от угла внутри области, для волны.
func _distances(region: Array[int]) -> Dictionary:
	var dist := {}
	var queue: Array[int] = [0]
	dist[0] = 0
	var inside := {}
	for c in region:
		inside[c] = true
	var head := 0
	while head < queue.size():
		var c := queue[head]
		head += 1
		for nb in _neighbors(c):
			if inside.has(nb) and not dist.has(nb):
				dist[nb] = int(dist[c]) + 1
				queue.append(nb)
	return dist


func _neighbors(c: int) -> Array[int]:
	var out: Array[int] = []
	var x := c % n
	var y := c / n
	if x > 0:
		out.append(c - 1)
	if x < n - 1:
		out.append(c + 1)
	if y > 0:
		out.append(c - n)
	if y < n - 1:
		out.append(c + n)
	return out


## Размер области после заливки цветом `color`, без изменения сетки.
func _region_size_after(g: PackedInt32Array, color: int) -> int:
	var copy := g.duplicate()
	for cell in _region(g):
		copy[cell] = color
	return _region(copy).size()


func _greedy_choice(g: PackedInt32Array) -> int:
	var best := -1
	var best_size := -1
	for c in k:
		if c == g[0]:
			continue
		var s := _region_size_after(g, c)
		if s > best_size:
			best_size = s
			best = c
	return best


## Длина жадного решения: верхняя оценка оптимума, в неё решение точно укладывается.
func _greedy_length() -> int:
	var g := grid.duplicate()
	var steps := 0
	while not _uniform(g) and steps < 64:
		var c := _greedy_choice(g)
		for cell in _region(g):
			g[cell] = c
		steps += 1
	return steps


# --- Рисование ----------------------------------------------------------------------------

func _draw() -> void:
	if def == null or grid.is_empty():
		return
	var cell := (GRID_PX - CELL_GAP * (n - 1)) / n
	var origin := Vector2((size.x - GRID_PX) / 2.0, (size.y - GRID_PX) / 2.0 - 40.0)
	var radius := 8 if n <= 5 else 5
	for i in n * n:
		var x := i % n
		var y := i / n
		var rect := Rect2(origin + Vector2(x * (cell + CELL_GAP), y * (cell + CELL_GAP)), Vector2(cell, cell))
		Style.flat(Style.accent(shown[i]), radius, Color.TRANSPARENT, 0).draw(get_canvas_item(), rect)
	# Угол заливки.
	draw_arc(origin + Vector2(cell / 2.0, cell / 2.0), cell * 0.22, 0.0, TAU, 32, Style.SURFACE_SOLID, 4.0, true)
	# Палитра внизу, выбранный цвет в рамке фокуса.
	var total_w := k * SWATCH_R * 2.0 + (k - 1) * SWATCH_GAP
	var px := (size.x - total_w) / 2.0 + SWATCH_R
	var py := origin.y + GRID_PX + 70.0
	for c in k:
		var center := Vector2(px + c * (SWATCH_R * 2.0 + SWATCH_GAP), py)
		draw_circle(center, SWATCH_R, Style.accent(c))
		if c == sel:
			draw_arc(center, SWATCH_R + Style.FOCUS_OFFSET + 1.5, 0.0, TAU, 48, Style.FOCUS, Style.FOCUS_WIDTH, true)
	# Ходы справа сверху: потрачено тёмным, осталось светлым; картинки точками слева от них.
	var r := 7.0
	var gap := 24.0
	var x0 := size.x - 48.0 - (budget - 1) * gap
	for i in budget:
		draw_circle(Vector2(x0 + i * gap, 60.0), r, Style.INK if i < used else Style.SURFACE_2)
	for p in PICTURES:
		var c := Style.SURFACE_2
		if p < picture or (p == picture and done_left > 0.0):
			c = Style.SUCCESS
		elif p == picture:
			c = Style.INK
		draw_circle(Vector2(x0 - 60.0 - (PICTURES - 1 - p) * gap, 60.0), r, c)
