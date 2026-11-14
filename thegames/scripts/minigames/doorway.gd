extends Minigame
## «Проверни» (doorway, технология low poly), каталог `docs/specs/minigames_catalog.md`. Фигура
## стоит в центре, на неё надвигается стена с вырезом той же фигуры, но повёрнутым: вырез
## сначала большой и сжимается к фигуре. Влево и вправо вращают фигуру свободно, без шагов.
## Стена дошла: если фигура повёрнута под вырез с точностью до зазора, стена проходит сквозь с
## хлопком, иначе бьётся о фигуру. `WALLS` стен, две непройденные это провал.
## Параметры от `t` в `resources/minigames/doorway.tres`: travel (сколько секунд едет стена), gap
## (зазор, градусы в каждую сторону), hard (доля фигур без симметрии: стрелка, уголок, домик).
## Вид как у всех мини-игр, в стиле оболочки: рендера технологии здесь нет (решение
## 2026-11-11). Мармелад: фигура вздрагивает от прохода и трясётся от удара, стена после
## прохода тает, проход брызгает каплями.
## Мышь (#83): колесо крутит фигуру шагами, ведение с зажатой левой кнопкой крутит плавно.

const WALLS := 6
const MAX_MISSES := 2
const FIGURE_R := 150.0
## Вырез на подходе во столько раз больше фигуры и чуть больше неё в момент прохода.
const HOLE_FAR := 2.4
const HOLE_FIT := 1.1
const ROT_SPEED := 210.0
const WHEEL_STEP := 15.0
const DRAG_DEG_PER_PX := 0.45
## Пауза между стенами и сколько стена тает после прохода или удара.
const REST := 0.22
const FADE := 0.3
## Вырез повёрнут от фигуры не меньше чем на столько градусов (по кратчайшему пути).
const MIN_TURN := 40.0
const DOT_R := 9.0
const DOT_GAP := 34.0
## Фигуры: точки в долях радиуса и порядок симметрии (на сколько равных поворотов совпадает).
const SHAPES := {
	&"bar": [[Vector2(-1, -0.4), Vector2(1, -0.4), Vector2(1, 0.4), Vector2(-1, 0.4)], 2],
	&"triangle": [[Vector2(0, -1), Vector2(0.87, 0.5), Vector2(-0.87, 0.5)], 3],
	&"plus": [[Vector2(-0.33, -1), Vector2(0.33, -1), Vector2(0.33, -0.33), Vector2(1, -0.33), Vector2(1, 0.33),
			Vector2(0.33, 0.33), Vector2(0.33, 1), Vector2(-0.33, 1), Vector2(-0.33, 0.33), Vector2(-1, 0.33),
			Vector2(-1, -0.33), Vector2(-0.33, -0.33)], 4],
	&"arrow": [[Vector2(-1, -0.3), Vector2(0.15, -0.3), Vector2(0.15, -0.78), Vector2(1, 0), Vector2(0.15, 0.78),
			Vector2(0.15, 0.3), Vector2(-1, 0.3)], 1],
	&"ell": [[Vector2(-0.8, -0.9), Vector2(-0.15, -0.9), Vector2(-0.15, 0.25), Vector2(0.8, 0.25), Vector2(0.8, 0.9),
			Vector2(-0.8, 0.9)], 1],
	&"house": [[Vector2(-0.72, 0.8), Vector2(-0.72, -0.15), Vector2(0, -0.95), Vector2(0.72, -0.15), Vector2(0.72, 0.8)], 1],
}
const EASY: Array[StringName] = [&"bar", &"triangle", &"plus"]
const HARD: Array[StringName] = [&"arrow", &"ell", &"house"]

var travel := 2.9
var gap := 22.0
var hard_share := 0.0
## Угол фигуры и выреза, градусы.
var angle := 0.0
var hole_angle := 0.0
var shape: StringName = &"bar"
var symmetry := 2
## Сколько стен пришло, сколько пройдено и нет; исходы по порядку.
var wall := 0
var passed := 0
var missed := 0
var results: Array[bool] = []
## Путь стены 0..1; меньше нуля пауза перед следующей.
var progress := -REST

var _points := PackedVector2Array()
var _fade := 0.0
var _fade_scale := 1.0
var _fade_angle := 0.0
var _fade_points := PackedVector2Array()
var _fade_ok := true
var _pop := JellySpring.new()
var _shake := JellySpring.new()
var _dots: Array[JellySpring] = []
var _splash := SplashFx.new()
var _dragging := false
var _pass_sfx: Array[AudioStreamPlayer] = []
var _bump_sfx: AudioStreamPlayer
var _win_sfx: AudioStreamPlayer


func _on_start() -> void:
	travel = clampf(def.param(&"travel", t, 2.9), 1.2, 2.95)
	gap = clampf(def.param(&"gap", t, 22.0), 5.0, 40.0)
	hard_share = clampf(def.param(&"hard", t, 0.0), 0.0, 1.0)
	for i in WALLS:
		_dots.append(JellySpring.new())
		var p := MiniSfx.hit(196.0, 0.0, pow(2.0, i / 6.0))
		add_child(p)
		_pass_sfx.append(p)
	_bump_sfx = MiniSfx.miss()
	_win_sfx = MiniSfx.win()
	add_child(_bump_sfx)
	add_child(_win_sfx)
	_next_wall()
	queue_redraw()


## Новая стена: фигура по сложности, вырез повёрнут от неё заметно в случайную сторону.
func _next_wall() -> void:
	var pool := HARD if rng.randf() < hard_share else EASY
	shape = pool[rng.randi_range(0, pool.size() - 1)]
	var info: Array = SHAPES[shape]
	symmetry = int(info[1])
	_points = PackedVector2Array(info[0])
	var period := 360.0 / symmetry
	var turn := rng.randf_range(minf(MIN_TURN, period * 0.4), period / 2.0) * (1.0 if rng.randf() < 0.5 else -1.0)
	hole_angle = fposmod(angle + turn, 360.0)
	progress = -REST


## Ошибка поворота в градусах с учётом симметрии фигуры: 0 точно в вырез.
func error() -> float:
	var period := 360.0 / symmetry
	return wrapf(angle - hole_angle, -period / 2.0, period / 2.0)


## Повернуть фигуру на `degrees` (плюс по часовой стрелке).
func turn_by(degrees: float) -> void:
	angle = fposmod(angle + degrees, 360.0)


func _on_tick(delta: float) -> void:
	turn_by(Input.get_axis(GameInput.LEFT, GameInput.RIGHT) * ROT_SPEED * delta)
	progress += delta / travel if progress >= 0.0 else delta
	if progress >= 1.0:
		_arrive()
	queue_redraw()


## Стена дошла до фигуры.
func _arrive() -> void:
	var ok := absf(error()) <= gap
	results.append(ok)
	_fade = FADE
	_fade_ok = ok
	_fade_scale = HOLE_FIT
	_fade_angle = hole_angle
	_fade_points = _points
	_dots[wall].kick(9.0)
	if ok:
		passed += 1
		_pass_sfx[clampi(wall, 0, _pass_sfx.size() - 1)].play()
		if Jelly.on():
			_pop.kick(5.0)
			_splash.pop(size / 2.0, Style.accent(wall % 2), 7, 420.0, 0.5)
	else:
		missed += 1
		_bump_sfx.play()
		if Jelly.on():
			_shake.kick(60.0)
	wall += 1
	if missed >= MAX_MISSES:
		finish(false)
	elif wall >= WALLS:
		_win_sfx.play()
		finish(true)
	else:
		_next_wall()


## Время вышло раньше стен: не засчитано.
func _on_timeout() -> bool:
	return false


## Колесо крутит шагами, ведение с зажатой левой кнопкой плавно; клик сам ничего не жмёт.
func _on_mouse(event: InputEventMouse) -> bool:
	var w := MouseUi.wheel(event)
	if w != 0:
		turn_by(w * WHEEL_STEP)
		mouse_last_action = GameInput.RIGHT if w > 0 else GameInput.LEFT
		return true
	var b := event as InputEventMouseButton
	if b != null and b.button_index == MOUSE_BUTTON_LEFT:
		_dragging = b.pressed
		return true
	var m := event as InputEventMouseMotion
	if m != null and _dragging:
		turn_by(m.relative.x * DRAG_DEG_PER_PX)
		mouse_last_action = GameInput.RIGHT if m.relative.x > 0.0 else GameInput.LEFT
		return true
	return false


func _mouse_action(_button: MouseButton, _pos: Vector2) -> StringName:
	return &""


## Бот: WIN крутит кратчайшим путём к вырезу и отпускает в зазоре; LOSE не трогает фигуру.
func _bot_step(_delta: float) -> bool:
	var want := 0
	if AutoTest.bot_mode == AutoTest.BotMode.WIN and progress >= 0.0 and absf(error()) > gap * 0.35:
		want = -1 if error() > 0.0 else 1
	_hold(GameInput.LEFT, want < 0)
	_hold(GameInput.RIGHT, want > 0)
	return false


func _hold(action: StringName, on: bool) -> void:
	if Input.is_action_pressed(action) != on:
		send_action(action, on)


func _on_finish(success: bool) -> void:
	_dragging = false
	for action: StringName in [GameInput.LEFT, GameInput.RIGHT]:
		if AutoTest.bot_active() and Input.is_action_pressed(action):
			Input.action_release(action)
	if success and Jelly.on():
		_pop.kick(8.0)
		_splash.pop(size / 2.0, Style.SUCCESS, 9, 480.0, 0.6)


func _process(delta: float) -> void:
	super(delta)
	if def == null or paused:
		return
	var tu := Jelly.tuning()
	_pop.step(delta, tu.spring_stiffness, tu.spring_damping)
	_shake.step(delta, tu.spring_stiffness, tu.spring_damping)
	for d in _dots:
		d.step(delta, tu.spring_stiffness, tu.spring_damping)
	if _fade > 0.0:
		_fade = maxf(_fade - delta, 0.0)
		# Пройденная стена сжимается дальше, отбитая отскакивает назад.
		_fade_scale += (-1.6 if _fade_ok else 1.2) * delta
	_splash.step(delta, func(_x: float) -> float: return INF)
	if not running:
		queue_redraw()


# --- Рисование --------------------------------------------------------------------------------

## Размер выреза относительно фигуры на пути `p`: издалека большой, у фигуры впритык.
static func hole_scale(p: float) -> float:
	var k := clampf(p, 0.0, 1.0)
	return lerpf(HOLE_FAR, HOLE_FIT, k * k * (3.0 - 2.0 * k))


func _outline(points: PackedVector2Array, degrees: float, scale: float, at: Vector2) -> PackedVector2Array:
	var out := PackedVector2Array()
	var xf := Transform2D(deg_to_rad(degrees), at).scaled_local(Vector2(scale, scale) * FIGURE_R)
	for p in points:
		out.append(xf * p)
	return out


func _draw() -> void:
	if def == null or _points.is_empty():
		return
	var center := size / 2.0
	var field := Rect2(Vector2(Style.PAD_CARD, 96.0), size - Vector2(2 * Style.PAD_CARD, 96.0 + 104.0))
	# Уходящая стена: тает.
	if _fade > 0.0:
		var a := _fade / FADE
		var tint := Style.SUCCESS if _fade_ok else Style.INK_3
		Style.flat(Color(tint, 0.28 * a), Style.R_CARD, Color.TRANSPARENT, 0).draw(get_canvas_item(), field)
		draw_colored_polygon(_outline(_fade_points, _fade_angle, maxf(_fade_scale, 0.05), center), Style.SURFACE_SOLID)
	# Стена на подходе: плотнее с приближением, вырез цветом карточки.
	if running and progress >= 0.0:
		var near := clampf(progress, 0.0, 1.0)
		var color := Style.SURFACE_SOLID.lerp(Style.accent(wall % 2), 0.16 + 0.3 * near)
		Style.flat(color, Style.R_CARD, Color.TRANSPARENT, 0).draw(get_canvas_item(), field)
		var hole := _outline(_points, hole_angle, hole_scale(progress), center)
		draw_colored_polygon(hole, Style.SURFACE_SOLID)
		draw_polyline(_closed(hole), Color(Style.INK, 0.25 + 0.5 * near), 3.0, true)
	# Фигура: текущий элемент, вздрагивает от прохода, трясётся от удара.
	var jelly := Jelly.on()
	var scale := clampf(1.0 + _pop.value * 0.03, 0.8, 1.25) if jelly else 1.0
	var at := center + (Vector2(clampf(_shake.value, -24.0, 24.0), 0.0) if jelly else Vector2.ZERO)
	var body := _outline(_points, angle, scale, at)
	draw_colored_polygon(_outline(_points, angle, scale, at + Vector2(0.0, 8.0)), Color(Style.INK, 0.14))
	draw_colored_polygon(body, Style.INK if running or results.is_empty() or results[results.size() - 1] else Style.INK_3)
	if jelly:
		_splash.draw_air(self, Vector2.ZERO)
	_draw_dots()


static func _closed(points: PackedVector2Array) -> PackedVector2Array:
	var out := points.duplicate()
	if not out.is_empty():
		out.append(out[0])
	return out


## Кружки стен сверху по центру: пройденные `success`, отбитые `danger`.
func _draw_dots() -> void:
	var y := 40.0 + AspectIcon.SIZE / 2.0
	var x0 := size.x / 2.0 - (WALLS - 1) * DOT_GAP / 2.0
	for i in WALLS:
		var c := Color(Style.INK, 0.12)
		if i < results.size():
			c = Style.SUCCESS if results[i] else Style.DANGER
		var r := DOT_R * (1.3 if i == wall and running else 1.0)
		r *= clampf(1.0 + _dots[i].value, 0.5, 1.8)
		draw_circle(Vector2(x0 + i * DOT_GAP, y), r, c)
