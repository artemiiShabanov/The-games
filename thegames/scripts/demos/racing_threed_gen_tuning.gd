class_name RacingThreedGenTuning
extends Resource
## Настройки генератора трассы спринта (#122), ресурс
## `res://resources/demos/racing_threed_gen.tres`. Метры, градусы.

const PATH := "res://resources/demos/racing_threed_gen.tres"

## Длина трассы и шаг точек оси.
@export var length := 1300.0
@export var step := 2.0
## Половина ширины дороги и сужения; сужение: длина и переход.
@export var half_width := 6.5
@export var narrow_half := 3.4
@export var narrow_min := 26.0
@export var narrow_max := 38.0
@export var narrow_ramp := 12.0
@export var narrows := 3
## Прямые: длина в начале и в конце трассы (от и до).
@export var straight_start := Vector2(90.0, 140.0)
@export var straight_end := Vector2(45.0, 85.0)
## Повороты: радиус в начале и в конце трассы, угол.
@export var radius_start := Vector2(42.0, 60.0)
@export var radius_end := Vector2(17.0, 30.0)
@export var angle := Vector2(38.0, 105.0)
## Связки: с какой доли трассы бывают, шанс и прямая между поворотами.
@export var link_from := 0.35
@export var link_chance := 0.6
@export var link_gap := Vector2(6.0, 14.0)
## Вход и выход поворота: длина плавного набора кривизны.
@export var ease := 14.0
## Рельеф: высота волн в конце трассы, их длины; первые метры ровные.
@export var hill := 4.5
@export var hill_waves := Vector2(150.0, 260.0)
@export var flat_start := 80.0
## Рыхлый песок: сколько участков, длина.
@export var sands := 4
@export var sand_length := Vector2(26.0, 44.0)
## Соседние витки трассы не ближе этого.
@export var clearance := 34.0


static func load_default() -> RacingThreedGenTuning:
	var t := load(PATH) as RacingThreedGenTuning
	return t if t != null else RacingThreedGenTuning.new()
