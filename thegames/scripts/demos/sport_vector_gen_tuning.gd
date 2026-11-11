class_name SportVectorGenTuning
extends Resource
## Настройки генератора матча понга (спорт × вектор, #93), ресурс
## `res://resources/demos/sport_vector_gen.tres`. Пиксели логического экрана демки.

const PATH := "res://resources/demos/sport_vector_gen.tres"

## Скорость ракетки соперника.
@export var ai_speed_min := 340.0
@export var ai_speed_max := 420.0
## Наибольшая ошибка соперника в точке встречи.
@export var ai_error_min := 100.0
@export var ai_error_max := 140.0
## С какой доли поля соперник начинает следить за мячом.
@export var ai_react_min := 0.3
@export var ai_react_max := 0.55
## Подач в списке и их угол от горизонтали, градусы.
@export var serves := 12
@export var serve_angle_min := 12.0
@export var serve_angle_max := 30.0


static func load_default() -> SportVectorGenTuning:
	var t := load(PATH) as SportVectorGenTuning
	return t if t != null else SportVectorGenTuning.new()
