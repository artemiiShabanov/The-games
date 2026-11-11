class_name PlatformerVectorGenTuning
extends Resource
## Настройки генератора этажей платформера × вектор (#90), ресурс
## `res://resources/demos/platformer_vector_gen.tres`. Пиксели логического экрана демки
## (1664 в ширину). Значения с суффиксами `_low` и `_high` это нижняя и верхняя линия, между
## ними ровный переход: чем выше, тем дыр меньше, они уже и едут быстрее.

const PATH := "res://resources/demos/platformer_vector_gen.tres"

@export var width := 1664.0
## Линий над землёй; флаг на этаже с этим номером.
@export var floors := 6
@export var hole_width_low := 200.0
@export var hole_width_high := 140.0
@export var hole_speed_low := 50.0
@export var hole_speed_high := 120.0
## Разброс скорости линии в долях.
@export var hole_speed_jitter := 0.15
## Соседние линии различаются по скорости со знаком не меньше чем на столько.
@export var hole_speed_gap := 22.0
## Шанс двух дыр на линии.
@export var two_holes_low := 0.9
@export var two_holes_high := 0.2
## Шанс, что линия едет навстречу предыдущей.
@export var alternate_chance := 0.75
@export var enemy_speed_min := 60.0
@export var enemy_speed_max := 105.0
## Второй враг на этаже: с какого этажа и с каким шансом.
@export var enemy_second_from := 2
@export var enemy_second_chance := 0.35
## Враг нижнего этажа стартует не ближе этого к герою.
@export var enemy_start_gap := 520.0
@export var coins_per_level := 2
## Старт героя и флаг: доля ширины от краёв, ближе которой они не стоят.
@export var edge_margin := 0.15


static func load_default() -> PlatformerVectorGenTuning:
	var t := load(PATH) as PlatformerVectorGenTuning
	return t if t != null else PlatformerVectorGenTuning.new()
