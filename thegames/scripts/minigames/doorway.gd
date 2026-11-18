extends Minigame
## «Проверни» (doorway, технология low poly), каталог `docs/specs/minigames_catalog.md`. Фигура
## стоит в центре, на неё надвигается стена с вырезом той же фигуры, но повёрнутым: вырез
## сначала большой и сжимается к фигуре. Влево и вправо вращают фигуру свободно, без шагов.
## Стена дошла: если фигура повёрнута под вырез с точностью до зазора, стена проходит сквозь с
## хлопком, иначе бьётся о фигуру. `WALLS` стен, все доходят до фигуры; предела промахов нет,
## счёт `_score` снижает каждая непройденная стена. Конец без вердикта: ни победного звука, ни
## брызг на финише.
## Параметры от `t` в `resources/minigames/doorway.tres`: travel (сколько секунд едет стена), gap
## (зазор, градусы в каждую сторону), hard (доля фигур без симметрии: стрелка, уголок, домик
## и другие), tricky (доля сложных фигур, плейтест 2026-11-14, #131: обманки, симметричные с
## одной мелкой приметой, и замудрённые, спираль, змея, ключ и подобные; на `t` 1 только они).
## Вид как у всех мини-игр, в стиле оболочки: рендера технологии здесь нет (решение
## 2026-11-11). Мармелад: фигура вздрагивает от прохода и трясётся от удара, стена после
## прохода тает, проход брызгает каплями.
## Мышь (#83): колесо крутит фигуру шагами, ведение с зажатой левой кнопкой крутит плавно.

const WALLS := 6
## Счёт: каждая непройденная стена (отбитая или не дошедшая до конца времени) снимает столько;
## одна из шести (старый порог «еле прошёл») даёт 0,75, четыре и больше 0.
const MISS_COST := 0.25
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
	# Симметричные.
	&"bar": [[Vector2(-1, -0.4), Vector2(1, -0.4), Vector2(1, 0.4), Vector2(-1, 0.4)], 2],
	&"triangle": [[Vector2(0, -1), Vector2(0.87, 0.5), Vector2(-0.87, 0.5)], 3],
	&"plus": [[Vector2(-0.33, -1), Vector2(0.33, -1), Vector2(0.33, -0.33), Vector2(1, -0.33),
			Vector2(1, 0.33), Vector2(0.33, 0.33), Vector2(0.33, 1), Vector2(-0.33, 1),
			Vector2(-0.33, 0.33), Vector2(-1, 0.33), Vector2(-1, -0.33), Vector2(-0.33, -0.33)], 4],
	&"rhombus": [[Vector2(0, -1), Vector2(0.55, 0), Vector2(0, 1), Vector2(-0.55, 0)], 2],
	&"zee": [[Vector2(-0.9, -0.6), Vector2(0.3, -0.6), Vector2(0.3, 0), Vector2(0.9, 0),
			Vector2(0.9, 0.6), Vector2(-0.3, 0.6), Vector2(-0.3, 0), Vector2(-0.9, 0)], 2],
	&"star": [[Vector2(0, -1), Vector2(0.265, -0.364), Vector2(0.951, -0.309), Vector2(0.428, 0.139),
			Vector2(0.588, 0.809), Vector2(0, 0.45), Vector2(-0.588, 0.809), Vector2(-0.428, 0.139),
			Vector2(-0.951, -0.309), Vector2(-0.265, -0.364)], 5],
	&"square": [[Vector2(-0.72, -0.72), Vector2(0.72, -0.72), Vector2(0.72, 0.72), Vector2(-0.72, 0.72)], 4],
	&"bowtie": [[Vector2(-0.9, -0.7), Vector2(0, -0.2), Vector2(0.9, -0.7), Vector2(0.9, 0.7),
			Vector2(0, 0.2), Vector2(-0.9, 0.7)], 2],
	&"star4": [[Vector2(0, -1), Vector2(0.283, -0.283), Vector2(1, 0), Vector2(0.283, 0.283),
			Vector2(0, 1), Vector2(-0.283, 0.283), Vector2(-1, 0), Vector2(-0.283, -0.283)], 4],
	&"aitch": [[Vector2(-0.8, -0.9), Vector2(-0.3, -0.9), Vector2(-0.3, -0.25), Vector2(0.3, -0.25),
			Vector2(0.3, -0.9), Vector2(0.8, -0.9), Vector2(0.8, 0.9), Vector2(0.3, 0.9),
			Vector2(0.3, 0.25), Vector2(-0.3, 0.25), Vector2(-0.3, 0.9), Vector2(-0.8, 0.9)], 2],
	&"tristar": [[Vector2(0, -1), Vector2(0.303, -0.175), Vector2(0.866, 0.5), Vector2(0, 0.35),
			Vector2(-0.866, 0.5), Vector2(-0.303, -0.175)], 3],
	# Без симметрии.
	&"arrow": [[Vector2(-1, -0.3), Vector2(0.15, -0.3), Vector2(0.15, -0.78), Vector2(1, 0),
			Vector2(0.15, 0.78), Vector2(0.15, 0.3), Vector2(-1, 0.3)], 1],
	&"ell": [[Vector2(-0.8, -0.9), Vector2(-0.15, -0.9), Vector2(-0.15, 0.25), Vector2(0.8, 0.25),
			Vector2(0.8, 0.9), Vector2(-0.8, 0.9)], 1],
	&"house": [[Vector2(-0.72, 0.8), Vector2(-0.72, -0.15), Vector2(0, -0.95), Vector2(0.72, -0.15),
			Vector2(0.72, 0.8)], 1],
	&"tee": [[Vector2(-0.9, -0.8), Vector2(0.9, -0.8), Vector2(0.9, -0.2), Vector2(0.3, -0.2),
			Vector2(0.3, 0.9), Vector2(-0.3, 0.9), Vector2(-0.3, -0.2), Vector2(-0.9, -0.2)], 1],
	&"kite": [[Vector2(0, -1), Vector2(0.6, 0.2), Vector2(0, 0.7), Vector2(-0.6, 0.2)], 1],
	&"step": [[Vector2(-0.9, 0.9), Vector2(-0.9, 0.3), Vector2(-0.3, 0.3), Vector2(-0.3, -0.3),
			Vector2(0.3, -0.3), Vector2(0.3, -0.9), Vector2(0.9, -0.9), Vector2(0.9, 0.9)], 1],
	&"trapezoid": [[Vector2(-0.45, -0.6), Vector2(0.45, -0.6), Vector2(0.95, 0.6), Vector2(-0.95, 0.6)], 1],
	&"flag": [[Vector2(-0.6, -0.95), Vector2(0.75, -0.95), Vector2(0.75, -0.05), Vector2(-0.05, -0.05),
			Vector2(-0.05, 0.95), Vector2(-0.6, 0.95)], 1],
	&"cup": [[Vector2(-0.8, -0.8), Vector2(-0.3, -0.8), Vector2(-0.3, 0.3), Vector2(0.3, 0.3),
			Vector2(0.3, -0.8), Vector2(0.8, -0.8), Vector2(0.8, 0.85), Vector2(-0.8, 0.85)], 1],
	&"wedge": [[Vector2(-0.8, -0.8), Vector2(0.9, 0.7), Vector2(-0.8, 0.7)], 1],
	&"drop": [[Vector2(0, -1), Vector2(0.52, 0), Vector2(0.6, 0.3), Vector2(0.52, 0.6),
			Vector2(0.3, 0.82), Vector2(0, 0.9), Vector2(-0.3, 0.82), Vector2(-0.52, 0.6),
			Vector2(-0.6, 0.3), Vector2(-0.52, 0)], 1],
	&"hook": [[Vector2(0.1, -0.9), Vector2(0.65, -0.9), Vector2(0.65, 0.9), Vector2(-0.7, 0.9),
			Vector2(-0.7, 0.1), Vector2(-0.15, 0.1), Vector2(-0.15, 0.35), Vector2(0.1, 0.35)], 1],
	# Обманки: симметричная фигура с одной мелкой приметой (скол, выступ, ступенька).
	&"plus_step": [[Vector2(-0.33, -1), Vector2(0.33, -1), Vector2(0.33, -0.51), Vector2(0.51, -0.51),
			Vector2(0.51, -0.33), Vector2(1, -0.33), Vector2(1, 0.33), Vector2(0.33, 0.33),
			Vector2(0.33, 1), Vector2(-0.33, 1), Vector2(-0.33, 0.33), Vector2(-1, 0.33),
			Vector2(-1, -0.33), Vector2(-0.33, -0.33)], 1],
	&"square_chip": [[Vector2(-0.72, -0.72), Vector2(0.52, -0.72), Vector2(0.72, -0.52), Vector2(0.72, 0.72),
			Vector2(-0.72, 0.72)], 1],
	&"square_nub": [[Vector2(-0.72, -0.72), Vector2(-0.12, -0.72), Vector2(-0.12, -0.86), Vector2(0.12, -0.86),
			Vector2(0.12, -0.72), Vector2(0.72, -0.72), Vector2(0.72, 0.72), Vector2(-0.72, 0.72)], 1],
	&"triangle_chip": [[Vector2(-0.104, -0.82), Vector2(0.104, -0.82), Vector2(0.87, 0.5), Vector2(-0.87, 0.5)], 1],
	&"star_blunt": [[Vector2(0, -0.8), Vector2(0.265, -0.364), Vector2(0.951, -0.309), Vector2(0.428, 0.139),
			Vector2(0.588, 0.809), Vector2(0, 0.45), Vector2(-0.588, 0.809), Vector2(-0.428, 0.139),
			Vector2(-0.951, -0.309), Vector2(-0.265, -0.364)], 1],
	&"bar_notch": [[Vector2(-1, -0.4), Vector2(-0.1, -0.4), Vector2(-0.1, -0.26), Vector2(0.1, -0.26),
			Vector2(0.1, -0.4), Vector2(1, -0.4), Vector2(1, 0.4), Vector2(-1, 0.4)], 1],
	&"rhombus_chip": [[Vector2(-0.138, -0.75), Vector2(0.138, -0.75), Vector2(0.55, 0), Vector2(0, 1),
			Vector2(-0.55, 0)], 1],
	&"aitch_short": [[Vector2(-0.8, -0.9), Vector2(-0.3, -0.9), Vector2(-0.3, -0.25), Vector2(0.3, -0.25),
			Vector2(0.3, -0.9), Vector2(0.8, -0.9), Vector2(0.8, 0.72), Vector2(0.3, 0.72),
			Vector2(0.3, 0.25), Vector2(-0.3, 0.25), Vector2(-0.3, 0.9), Vector2(-0.8, 0.9)], 1],
	&"star4_blunt": [[Vector2(0, -0.78), Vector2(0.283, -0.283), Vector2(1, 0), Vector2(0.283, 0.283),
			Vector2(0, 1), Vector2(-0.283, 0.283), Vector2(-1, 0), Vector2(-0.283, -0.283)], 1],
	&"bowtie_chip": [[Vector2(-0.9, -0.7), Vector2(0, -0.2), Vector2(0.72, -0.6), Vector2(0.9, -0.5),
			Vector2(0.9, 0.7), Vector2(0, 0.2), Vector2(-0.9, 0.7)], 1],
	# Замудрённые: много изгибов и лучей, положение одно.
	&"spiral": [[Vector2(0.11, 0.05), Vector2(0.11, -0.29), Vector2(0.34, -0.29), Vector2(0.34, 0.34),
			Vector2(-0.34, 0.34), Vector2(-0.34, -0.74), Vector2(0.77, -0.74), Vector2(0.77, 0.88),
			Vector2(0.99, 0.88), Vector2(0.99, -0.96), Vector2(-0.56, -0.96), Vector2(-0.56, 0.56),
			Vector2(0.56, 0.56), Vector2(0.56, -0.51), Vector2(-0.11, -0.51), Vector2(-0.11, 0.05)], 1],
	&"snake": [[Vector2(-0.961, 0.057), Vector2(-0.893, 0.11), Vector2(-0.825, 0.167), Vector2(-0.753, 0.224),
			Vector2(-0.677, 0.276), Vector2(-0.594, 0.317), Vector2(-0.502, 0.34), Vector2(-0.405, 0.337),
			Vector2(-0.31, 0.306), Vector2(-0.22, 0.252), Vector2(-0.137, 0.18), Vector2(-0.059, 0.096),
			Vector2(0.017, 0.007), Vector2(0.09, -0.081), Vector2(0.159, -0.159), Vector2(0.221, -0.218),
			Vector2(0.272, -0.25), Vector2(0.302, -0.257), Vector2(0.319, -0.253), Vector2(0.346, -0.235),
			Vector2(0.392, -0.188), Vector2(0.449, -0.108), Vector2(0.511, -0.001), Vector2(0.577, 0.123),
			Vector2(0.645, 0.254), Vector2(0.717, 0.384), Vector2(0.788, 0.495), Vector2(1.052, 0.314),
			Vector2(0.982, 0.217), Vector2(0.912, 0.104), Vector2(0.838, -0.022), Vector2(0.763, -0.15),
			Vector2(0.684, -0.27), Vector2(0.599, -0.376), Vector2(0.503, -0.46), Vector2(0.389, -0.514),
			Vector2(0.264, -0.518), Vector2(0.153, -0.474), Vector2(0.062, -0.403), Vector2(-0.017, -0.318),
			Vector2(-0.09, -0.225), Vector2(-0.158, -0.131), Vector2(-0.224, -0.043), Vector2(-0.287, 0.033),
			Vector2(-0.346, 0.092), Vector2(-0.398, 0.131), Vector2(-0.444, 0.151), Vector2(-0.489, 0.157),
			Vector2(-0.539, 0.15), Vector2(-0.597, 0.128), Vector2(-0.663, 0.091), Vector2(-0.732, 0.044),
			Vector2(-0.805, -0.007), Vector2(-0.879, -0.057)], 1],
	&"wild_star": [[Vector2(0, -1), Vector2(0.109, -0.301), Vector2(0.386, -0.46), Vector2(0.277, -0.16),
			Vector2(0.837, -0.148), Vector2(0.315, 0.056), Vector2(0.476, 0.275), Vector2(0.206, 0.245),
			Vector2(0.325, 0.893), Vector2(0, 0.32), Vector2(-0.239, 0.658), Vector2(-0.206, 0.245),
			Vector2(-0.52, 0.3), Vector2(-0.315, 0.056), Vector2(-0.886, -0.156), Vector2(-0.277, -0.16),
			Vector2(-0.482, -0.575), Vector2(-0.109, -0.301)], 1],
	&"key": [[Vector2(-0.155, 0.144), Vector2(-0.291, 0.331), Vector2(-0.506, 0.418), Vector2(-0.734, 0.377),
			Vector2(-0.906, 0.223), Vector2(-0.97, 0), Vector2(-0.906, -0.223), Vector2(-0.734, -0.377),
			Vector2(-0.506, -0.418), Vector2(-0.291, -0.331), Vector2(-0.155, -0.144), Vector2(0.95, -0.144),
			Vector2(0.95, 0.45), Vector2(0.75, 0.45), Vector2(0.75, 0.144), Vector2(0.55, 0.144),
			Vector2(0.55, 0.35), Vector2(0.4, 0.35), Vector2(0.4, 0.144)], 1],
	&"bolt": [[Vector2(0.1, -1), Vector2(0.6, -1), Vector2(0.2, -0.25), Vector2(0.6, -0.25),
			Vector2(-0.3, 1), Vector2(-0.05, 0.1), Vector2(-0.5, 0.1)], 1],
	&"comb": [[Vector2(-0.9, 0.7), Vector2(-0.9, -0.5), Vector2(-0.6, -0.5), Vector2(-0.6, 0.3),
			Vector2(-0.3, 0.3), Vector2(-0.3, -0.9), Vector2(0, -0.9), Vector2(0, 0.3),
			Vector2(0.3, 0.3), Vector2(0.3, -0.2), Vector2(0.6, -0.2), Vector2(0.6, 0.3),
			Vector2(0.9, 0.3), Vector2(0.9, 0.7)], 1],
	&"maze": [[Vector2(-0.93, -0.8), Vector2(-0.93, 0.23), Vector2(-0.07, 0.23), Vector2(-0.07, -0.47),
			Vector2(0.37, -0.47), Vector2(0.37, 0.67), Vector2(-0.5, 0.67), Vector2(-0.5, 0.93),
			Vector2(0.63, 0.93), Vector2(0.63, -0.73), Vector2(-0.33, -0.73), Vector2(-0.33, -0.03),
			Vector2(-0.67, -0.03), Vector2(-0.67, -0.8)], 1],
}
const EASY: Array[StringName] = [&"bar", &"triangle", &"plus", &"rhombus", &"zee", &"star",
		&"square", &"bowtie", &"star4", &"aitch", &"tristar"]
const HARD: Array[StringName] = [&"arrow", &"ell", &"house", &"tee", &"kite", &"step",
		&"trapezoid", &"flag", &"cup", &"wedge", &"drop", &"hook"]
const TRICKY: Array[StringName] = [&"plus_step", &"square_chip", &"square_nub", &"triangle_chip", &"star_blunt", &"bar_notch",
		&"rhombus_chip", &"aitch_short", &"star4_blunt", &"bowtie_chip"]
const FANCY: Array[StringName] = [&"spiral", &"snake", &"wild_star", &"key", &"bolt", &"comb",
		&"maze"]

var travel := 2.9
var gap := 22.0
var hard_share := 0.0
var tricky_share := 0.0
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


func _on_start() -> void:
	travel = clampf(def.param(&"travel", t, 2.9), 1.2, 2.95)
	gap = clampf(def.param(&"gap", t, 22.0), 5.0, 40.0)
	hard_share = clampf(def.param(&"hard", t, 0.0), 0.0, 1.0)
	tricky_share = clampf(def.param(&"tricky", t, 0.0), 0.0, 1.0)
	for i in WALLS:
		_dots.append(JellySpring.new())
		var p := MiniSfx.hit(196.0, 0.0, pow(2.0, i / 6.0))
		add_child(p)
		_pass_sfx.append(p)
	_bump_sfx = MiniSfx.miss()
	add_child(_bump_sfx)
	_next_wall()
	queue_redraw()


## Новая стена: фигура по сложности, вырез повёрнут от неё заметно в случайную сторону.
func _next_wall() -> void:
	var roll := rng.randf()
	var pool := TRICKY + FANCY if roll < tricky_share else (HARD if rng.randf() < hard_share else EASY)
	# Не та же фигура два раза подряд.
	var prev := shape if wall > 0 else &""
	shape = pool[rng.randi_range(0, pool.size() - 1)]
	if shape == prev:
		shape = pool[(pool.find(shape) + 1) % pool.size()]
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
	if wall >= WALLS:
		finish_score(_score())
	else:
		_next_wall()


## Счёт: 1 за все стены, каждая непройденная (и не дошедшая к концу времени) `MISS_COST`.
## Итог для сцены оценки мини-игр (`minigame_rating_test`).
func summary() -> String:
	return "стен пройдено %d из %d" % [passed, WALLS]  # i18n: skip


func _score() -> float:
	return 1.0 - MISS_COST * (WALLS - passed)


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


func _on_finish(_success: bool) -> void:
	_dragging = false
	for action: StringName in [GameInput.LEFT, GameInput.RIGHT]:
		if AutoTest.bot_active() and Input.is_action_pressed(action):
			Input.action_release(action)


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
	draw_mistakes(missed)
