class_name RacingLowpolyGenTuning
extends Resource
## Настройки генератора трассы гонок × low poly (#113), ресурс
## `res://resources/demos/racing_lowpoly_gen.tres`. Метры.

const PATH := "res://resources/demos/racing_lowpoly_gen.tres"

## Опорных точек кольца, средний радиус, разброс радиуса и угла, вытянутость по x.
@export var points := 10
@export var radius := 46.0
@export var radius_min := 0.85
@export var radius_max := 1.15
@export var angle_jitter := 0.16
## Насколько точки через одну уходят к центру и от него: извилистость.
@export var zigzag := 0.3
## Сколько раз скругляются углы кривой.
@export var smooth := 24
@export var stretch := 1.25
## Шаг точек трассы и половина её ширины.
@export var step := 2.0
@export var half_width := 4.5
## Длина круга в пределах, самый крутой поворот (радиус) и зазор между дальними участками.
@export var length_min := 320.0
@export var length_max := 520.0
@export var radius_tightest := 6.5
@export var clearance := 14.0
## Холмы: высота двух волн по кругу.
@export var hill_a := 1.3
@export var hill_b := 0.8
## Участки без бортов: сколько, длина, кривизна не больше.
@export var open_count := 2
@export var open_length := 32.0
@export var open_curve := 0.03
## Грязь: сколько поворотов, длина пятна, ширина от внутреннего края, кривизна поворота не меньше.
@export var mud_count := 4
@export var mud_length := 16.0
@export var mud_width := 3.2
@export var mud_curve := 0.04
## Попутный ветер: сколько полос, длина, половина ширины.
@export var wind_count := 3
@export var wind_length := 10.0
@export var wind_half := 1.3
## Трамплин: длина промоины и разбега перед ней.
@export var ramp_gap := 8.0
@export var ramp_run := 6.0


static func load_default() -> RacingLowpolyGenTuning:
	var t := load(PATH) as RacingLowpolyGenTuning
	return t if t != null else RacingLowpolyGenTuning.new()
