class_name LowpolyTuning
extends Resource
## Числа основы low poly (#108): экран, приметы эпохи первой PlayStation, свет, туман, камера
## за спиной и вид от первого лица. Один ресурс `res://resources/demos/lowpoly.tres` на все пять
## демок технологии.

const PATH := "res://resources/demos/lowpoly.tres"

## Увеличение экрана ближайшим соседом: 3D рисуется в карточку, уменьшенную во столько раз.
@export var screen_scale := 3
## Дрожание вершин: шаг сетки, к которой прилипают вершины, в пикселях экрана демки.
@export var vertex_snap := 2.0
## Плывущие текстуры: 1 полностью аффинное наложение, 0 правильная перспектива.
@export var affine := 0.85
## Глубина цвета: ступеней на канал (31 это 15-битный цвет) и сила дизеринга, 0 выключает.
@export var color_levels := 31.0
@export var dither := 1.0
## Угол обзора камеры по вертикали, градусы.
@export var fov := 60.0
## Дальняя плоскость камеры, метры.
@export var far := 140.0
## Солнце: наклон вниз и поворот, градусы; сила света по вершинам.
@export var sun_pitch := -52.0
@export var sun_yaw := 38.0
@export var sun_energy := 0.75
## Рассеянный свет: сколько видно на гранях, отвёрнутых от солнца.
@export var ambient_energy := 0.5
## Туман цветом неба: с какого расстояния начинается и где закрывает всё, метры.
@export var fog_begin := 30.0
@export var fog_end := 90.0
## Тень-блин под героями: непрозрачность.
@export var shadow_alpha := 0.4
## Камера за спиной: расстояние до цели, высота над ней, высота точки взгляда над целью.
@export var follow_distance := 5.5
@export var follow_height := 2.6
@export var follow_look_height := 1.2
## Как быстро камера догоняет цель и доворачивает за её курсом, 1/с.
@export var follow_lag := 7.0
@export var follow_turn := 2.2
## Вид от первого лица: высота глаз, скорость поворота стрелками (рад/с), предел наклона (рад).
@export var eye_height := 1.55
@export var look_speed := 2.4
@export var pitch_limit := 1.2

static var _default: LowpolyTuning


static func load_default() -> LowpolyTuning:
	if _default == null:
		_default = load(PATH) as LowpolyTuning if ResourceLoader.exists(PATH) else LowpolyTuning.new()
	return _default
