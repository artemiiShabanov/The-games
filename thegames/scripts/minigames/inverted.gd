extends Minigame
## «Выведи» (inverted, управление), каталог `docs/specs/minigames_catalog.md`. Лабиринт 5×5,
## точка в центре, выход в одном из углов. Лабиринты чередуются: в нечётном стрелки двигают
## точку, в чётном точка стоит в центре экрана, а стрелки двигают сам лабиринт под ней (нажал
## вправо: лабиринт уехал вправо, точка оказалась в клетке левее). Стены не пускают в обоих
## режимах, удар о стену блокирует движение на полсекунды. Какой режим сейчас, видно по тому,
## что движется, и по цвету: управляемое синее (акцент), остальное чёрное; выход это кольцо в
## цвете стен, в которое садится точка (плейтест 2026-11-07). 2-3 лабиринта за 20 с;
## провал, если не прошёл их до таймера. Параметры от `t` в `resources/minigames/inverted.tres`:
## mazes (число), twist (запутанность: 0 длинные коридоры, 1 частые развилки), flip (через
## сколько ходов режим меняется посреди лабиринта; от `FLIP_NEVER` и выше не меняется, с `t`
## интервал короче).
## Мармелад (STYLE «Мармелад»): точка мягкое тело, тянется вдоль хода, отстаёт и качается после
## остановки, при ударе плющится о стену, а стена прогибается и дрожит, от удара отлетает пара
## мягких брызг; за точкой тянется склизкий след во всю её ширину (`SlimeTrail`), он лежит на
## лабиринте и тает. Выход пройден: из кольца мягкие брызги цвета точки. Смена режима: лабиринт
## вздрагивает, точка вздрагивает. Геймплей прежний, меняется только рисунок.

enum Mode { DOT, MAZE }

const N := 5
const CELL := 88.0
## Интервал смены режима от этого значения считается «никогда».
const FLIP_NEVER := 10
const WALL := 8.0
const DOT_R := 26.0
const MOVE_SECONDS := 0.11
const SHAKE_SECONDS := 0.25
## После удара о стену движение заблокировано.
const BUMP_LOCK_SECONDS := 0.5
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
var lock := 0.0
var flash := 0.0
var _bot_timer := 0.0
var _step_sound: AudioStreamPlayer
var _bump: AudioStreamPlayer
var _done_sound: AudioStreamPlayer
var _flip_sound: AudioStreamPlayer

## Мармелад: тело точки, прогиб стены после удара, вздрог лабиринта при смене режима, след.
const JELLY_LUNGE := 9.0
const JELLY_SQUASH := 520.0
const JELLY_WALL_KICK := 200.0
const JELLY_FLIP_KICK := 0.4
const JELLY_POKE := 180.0
## След: сколько живёт, с, непрозрачность свежего и ширина в долях диаметра точки.
const TRAIL_SECONDS := 0.8
const TRAIL_ALPHA := 0.2
const TRAIL_WIDTH := 0.9
## Радиус, которым след огибает поворот (не меньше полуширины следа, иначе внутренний край
## ляжет сам на себя); на столько же след не доходит до центра клетки.
const TRAIL_TURN := 28.0
## Шаг отметок следа вдоль хода, пиксели.
const TRAIL_SAMPLE := 5.0
## Брызги: на выходе и от удара о стену (число капель до тюнинга, скорость).
const POP_EXIT := 4
const POP_EXIT_SPEED := 300.0
const POP_BUMP := 2
const POP_BUMP_SPEED := 200.0
var jelly_dot: JellyShape
var jelly_wall := JellySpring.new()
var jelly_flip := JellySpring.new()
## Стена, о которую ударились: клетка и сторона, в координатах лабиринта.
var _hit_rect := Rect2()
var _hit_dir := Vector2.ZERO
## След в координатах лабиринта, брызги в координатах экрана.
var _trail := SlimeTrail.new(Style.INK, TRAIL_SECONDS, TRAIL_ALPHA)
var _fx := SplashFx.new()
## Ход, по которому сейчас идёт след (клетки), и откуда след вошёл в его начало.
var _trail_from := Vector2(-1, -1)
var _trail_to := Vector2(-1, -1)
var _trail_in := Vector2.ZERO
## Докуда по текущему ходу след уже положен, пиксели от центра клетки начала.
var _trail_s := 0.0
var _seen_shake := 0.0
var _seen_flash := 0.0
var _seen_maze := -1
var _seen_mode := Mode.DOT
## Раскладка кадра: угол лабиринта и точка на экране, точка в координатах лабиринта.
var _origin := Vector2.ZERO
var _dot_screen := Vector2.ZERO
var _dot_local := Vector2.ZERO


func _on_start() -> void:
	mazes_total = maxi(int(round(def.param(&"mazes", t, 2.0))), 1)
	twist = clampf(def.param(&"twist", t, 0.0), 0.0, 1.0)
	flip_moves = int(round(def.param(&"flip", t, 12.0)))
	if flip_moves >= FLIP_NEVER:
		flip_moves = 0
	_step_sound = Sfx.player(Sfx.blip(700.0, 0.04, 0.2, 50.0))
	_bump = Sfx.player(Sfx.thud(0.08, 0.35))
	_done_sound = Sfx.player(Sfx.blip(880.0, 0.18, 0.45, 12.0))
	_flip_sound = Sfx.player(Sfx.blip(440.0, 0.12, 0.3, 18.0))
	for p in [_step_sound, _bump, _done_sound, _flip_sound]:
		add_child(p)
	_new_maze()
	jelly_dot = JellyShape.circle(DOT_R)
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


## Мышь (#83): клик со стороны от точки жмёт стрелку в ту сторону, по большей оси; в режиме
## лабиринта, как и стрелка, едет лабиринт.
func _mouse_action(button: MouseButton, pos: Vector2) -> StringName:
	if button != MOUSE_BUTTON_LEFT:
		return &""
	_layout()
	return dir_action(_dot_screen, pos)


## Нажатие стрелки: в режиме точки точка идёт туда, в режиме лабиринта лабиринт едет туда,
## то есть точка попадает в клетку напротив.
func _press(d: int) -> void:
	if anim < 1.0 or lock > 0.0:
		return
	var move_dir := d if mode == Mode.DOT else (d + 2) % 4
	if _has_wall(cell, move_dir):
		shake = SHAKE_SECONDS
		shake_dir = Vector2(DIRS[d])
		lock = BUMP_LOCK_SECONDS
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
	lock = maxf(lock - delta, 0.0)
	if anim < 1.0:
		anim = minf(anim + delta / MOVE_SECONDS, 1.0)
		if anim >= 1.0:
			_arrived()
	queue_redraw()


func _arrived() -> void:
	if cell == exit_cell:
		maze_index += 1
		_done_sound.play()
		if Jelly.on():
			# Брызги из кольца выхода там, где оно на экране сейчас, до смены лабиринта.
			_layout()
			var at := _origin + (Vector2(exit_cell) + Vector2(0.5, 0.5)) * CELL
			_fx.pop(at, _dot_color(), POP_EXIT, POP_EXIT_SPEED)
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
	if AutoTest.bot_mode != AutoTest.BotMode.WIN or anim < 1.0 or lock > 0.0:
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


# --- Мармелад -----------------------------------------------------------------------------

## Где сейчас лабиринт и точка. Без мармелада удар трясёт управляемое, с ним управляемое один
## раз подаётся к стене (тело и стена доигрывают удар сами).
func _layout() -> void:
	var center := size / 2.0 + Vector2(0, 10)
	var grid := Vector2(N, N) * CELL
	var pos := anim_from.lerp(anim_to, ease(anim, -1.8))
	_dot_local = (pos + Vector2(0.5, 0.5)) * CELL
	var jolt := shake_dir * sin(shake * 50.0) * 8.0 * shake / SHAKE_SECONDS
	if Jelly.on():
		var k := clampf((1.0 - shake / SHAKE_SECONDS) / 0.5, 0.0, 1.0)
		jolt = _bump_dir() * sin(PI * k) * JELLY_LUNGE if shake > 0.0 else Vector2.ZERO
		# В режиме лабиринта к точке едет стена, то есть лабиринт против хода точки.
		if mode == Mode.MAZE:
			jolt = -jolt
	if mode == Mode.DOT:
		_origin = center - grid / 2.0
		_dot_screen = _origin + _dot_local + jolt
	else:
		# Точка стоит в центре экрана, лабиринт едет под ней.
		_dot_screen = center
		_origin = center - _dot_local - jolt


## Куда точка упёрлась при последнем ударе: в режиме лабиринта против нажатой стрелки.
func _bump_dir() -> Vector2:
	return shake_dir if mode == Mode.DOT else -shake_dir


## Прямоугольник стены клетки `c` со стороны `d` в координатах лабиринта (общая стена соседей
## даёт один и тот же прямоугольник).
func _wall_rect(c: Vector2i, d: int) -> Rect2:
	var h := WALL / 2.0
	var p := Vector2(c) * CELL
	match d:
		0:
			return Rect2(p + Vector2(-h, -h), Vector2(CELL + WALL, WALL))
		1:
			return Rect2(p + Vector2(CELL - h, -h), Vector2(WALL, CELL + WALL))
		2:
			return Rect2(p + Vector2(-h, CELL - h), Vector2(CELL + WALL, WALL))
	return Rect2(p + Vector2(-h, -h), Vector2(WALL, CELL + WALL))


## Мармелад живёт и после финиша, пока сцена на экране; на паузе стоит.
func _process(delta: float) -> void:
	super(delta)
	if jelly_dot == null or paused or walls.is_empty():
		return
	var tu := Jelly.tuning()
	_layout()
	var new_maze := maze_index != _seen_maze
	if new_maze or mode != _seen_mode:
		# Новый лабиринт или смена режима: точка переставляется без полёта через экран.
		jelly_dot.snap(_dot_screen)
		if _seen_maze >= 0:
			jelly_dot.poke(JELLY_POKE)
		if new_maze:
			jelly_wall.value = 0.0
			jelly_wall.velocity = 0.0
			_trail.clear()
			_trail_from = Vector2(-1, -1)
			_trail_to = Vector2(-1, -1)
			_trail_s = 0.0
		_seen_maze = maze_index
		_seen_mode = mode
	if shake > _seen_shake:
		# Удар: передний край точки плющится о стену, стена прогибается от точки.
		var dir := _bump_dir()
		_hit_dir = dir
		_hit_rect = _wall_rect(cell, DIRS.find(Vector2i(dir)))
		jelly_dot.push(-dir * JELLY_SQUASH, dir)
		jelly_wall.value = 0.0
		jelly_wall.velocity = 0.0
		jelly_wall.kick(JELLY_WALL_KICK)
		_fx.pop(_dot_screen + dir * DOT_R, _dot_color(), POP_BUMP, POP_BUMP_SPEED, 0.4)
	if flash > _seen_flash:
		jelly_flip.kick(JELLY_FLIP_KICK)
	_seen_shake = shake
	_seen_flash = flash
	jelly_wall.step(delta, tu.spring_stiffness * 2.0, tu.spring_damping * 1.5)
	jelly_flip.step(delta, tu.spring_stiffness, tu.spring_damping)
	jelly_dot.follow(delta, _dot_screen)
	# След в координатах лабиринта: в режиме лабиринта он едет вместе со стенами. Пока точка
	# стоит, отметки не добавляются (шаг следа), и след тает.
	_add_trail()
	_trail.step(delta)
	_fx.step(delta, Callable())
	if not running:
		queue_redraw()


## Куда кладётся след в координатах лабиринта. Путь точки ломаный, от центра к центру клетки;
## след не доходит до центра клетки на `TRAIL_TURN` (это под точкой) и огибает поворот дугой
## такого радиуса, так что и внутренний край поворота скруглён. При развороте назад след не
## рвётся: `SlimeTrail` рисует путь одной фигурой, и обратный ход ложится на прямой без
## нахлёста (плейтест 2026-11-11, #86). Смена режима след не рвёт: в координатах лабиринта
## точка не прыгает.
##
## Точка за кадр проходит до трети клетки, и дуга поворота из трёх-четырёх отметок была бы
## гранёной, поэтому путь от прошлого кадра добирается отметками через `TRAIL_SAMPLE`.
func _add_trail() -> void:
	var w := DOT_R * 2.0 * TRAIL_WIDTH
	var d := (anim_to - anim_from).normalized()
	if anim_from != _trail_from or anim_to != _trail_to:
		# Новый ход: откуда след вошёл в клетку, с которой он начинается.
		var last := (_trail_to - _trail_from).normalized()
		_trail_in = last if _trail_to == anim_from else Vector2.ZERO
		if _trail_in != Vector2.ZERO and _trail_in.dot(d) < -0.5:
			_trail_in = Vector2.ZERO
		_trail_from = anim_from
		_trail_to = anim_to
		_trail_s = 0.0
	var c := (anim_from + Vector2(0.5, 0.5)) * CELL
	if d == Vector2.ZERO:
		_trail.add(c, w)
		return
	var s := minf(_dot_local.distance_to(c), CELL - TRAIL_TURN)
	while _trail_s < s:
		_trail_s = minf(_trail_s + TRAIL_SAMPLE, s)
		_trail.add(_trail_point(c, d, _trail_s), w)


## Точка следа на ходе из центра `c` в сторону `d` на расстоянии `s`.
func _trail_point(c: Vector2, d: Vector2, s: float) -> Vector2:
	if _trail_in != Vector2.ZERO and absf(_trail_in.dot(d)) < 0.5 and s < TRAIL_TURN:
		var o := c + (d - _trail_in) * TRAIL_TURN
		var a0 := (-d).angle()
		var turn := wrapf(_trail_in.angle() - a0, -PI, PI)
		return o + Vector2.from_angle(a0 + turn * s / TRAIL_TURN) * TRAIL_TURN
	return c + d * s


## Цвет точки: управляемая синяя, иначе чёрная; во время блокировки после удара тусклее.
func _dot_color() -> Color:
	var col := Style.accent(0) if mode == Mode.DOT else Style.INK
	return col.lerp(Style.INK_3, 0.5) if lock > 0.0 else col


## Стена после удара прогибается дугой от точки: концы на месте, середина качается.
func _draw_bent_wall(rect: Rect2, col: Color) -> void:
	var bow := _hit_dir * jelly_wall.value
	var along := Vector2.RIGHT if rect.size.x > rect.size.y else Vector2.DOWN
	var across := Vector2(along.y, along.x)
	var length := rect.size.dot(along)
	var thick := rect.size.dot(across)
	var a := _origin + rect.position
	var steps := 12
	var poly := PackedVector2Array()
	for k in steps + 1:
		var u := float(k) / steps
		poly.append(a + along * length * u + bow * sin(PI * u))
	for k in range(steps, -1, -1):
		var u := float(k) / steps
		poly.append(a + along * length * u + across * thick + bow * sin(PI * u))
	draw_colored_polygon(poly, col)


# --- Рисование ----------------------------------------------------------------------------

func _draw() -> void:
	if def == null or walls.is_empty():
		return
	_layout()
	var grid := Vector2(N, N) * CELL
	var origin := _origin
	var jelly := Jelly.on() and jelly_dot != null
	# Управляемое синее, остальное чёрное; во время блокировки после удара всё тускнеет.
	var active := Style.accent(0)
	var passive := Style.INK
	var wall_color := passive if mode == Mode.DOT else active
	var dot_color := _dot_color()
	if lock > 0.0:
		wall_color = wall_color.lerp(Style.INK_3, 0.5)
	# Смена режима: лабиринт вздрагивает масштабом вокруг своего центра.
	var wobble := 1.0 + (jelly_flip.value if jelly else 0.0)
	var gc := origin + grid / 2.0
	draw_set_transform(gc * (1.0 - wobble), 0.0, Vector2(wobble, wobble))
	# Подложка и выход: кольцо в цвете управляемого, в которое садится точка.
	Style.flat(Color(Style.INK, 0.04), Style.R_CTL, Color.TRANSPARENT, 0).draw(get_canvas_item(), Rect2(origin - Vector2(WALL, WALL), grid + Vector2(WALL, WALL) * 2.0))
	var exit_center := origin + (Vector2(exit_cell) + Vector2(0.5, 0.5)) * CELL
	var ink := wall_color if flash <= 0.0 else wall_color.lerp(Style.FOCUS, flash / FLASH_SECONDS)
	draw_arc(exit_center, DOT_R + 10.0, 0.0, TAU, 48, ink, 6.0, true)
	# Стены прямоугольниками с нахлёстом на полтолщины, чтобы углы сходились без зазоров.
	# Стена после удара рисуется дугой, пока качается.
	var bent := jelly and absf(jelly_wall.value) > 0.05 and _hit_rect.has_area()
	for y in N:
		for x in N:
			var c := Vector2i(x, y)
			for d: int in [0, 3, 1, 2]:
				if not _has_wall(c, d):
					continue
				var r := _wall_rect(c, d)
				if bent and r.is_equal_approx(_hit_rect):
					continue
				draw_rect(Rect2(origin + r.position, r.size), ink)
	if bent:
		_draw_bent_wall(_hit_rect, ink)
	if jelly:
		# След под точкой, в цвете точки.
		_trail.color = dot_color
		_trail.draw(self, origin)
	draw_set_transform(Vector2.ZERO)
	if jelly and not jelly_dot.blob.points.is_empty():
		jelly_dot.draw(self, dot_color)
	else:
		draw_circle(_dot_screen, DOT_R, dot_color)
	if jelly:
		_fx.draw_air(self, Vector2.ZERO)
	# Лабиринты справа сверху, левее подпись режима: что сейчас двигается (внизу её закрывал
	# бы лабиринт в режиме, где он едет).
	var r := 7.0
	var gap := 28.0
	var x0 := size.x - 48.0 - (mazes_total - 1) * gap
	var font := get_theme_default_font()
	var caption := "двигается точка" if mode == Mode.DOT else "двигается лабиринт"
	var w := font.get_string_size(caption, HORIZONTAL_ALIGNMENT_LEFT, -1, Style.FONT_BODY).x
	draw_string(font, Vector2(x0 - r - 32.0 - w, 69.0), caption, HORIZONTAL_ALIGNMENT_LEFT, -1, Style.FONT_BODY,
			(Style.accent(0) if mode == Mode.MAZE else Style.INK) if flash <= 0.0 else Style.FOCUS)
	for j in mazes_total:
		var col := Style.SURFACE_2
		if j < maze_index:
			col = Style.SUCCESS
		elif j == maze_index:
			col = Style.INK
		draw_circle(Vector2(x0 + j * gap, 60.0), r, col)
