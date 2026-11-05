class_name PlatformerGenTuning
extends Resource
## Настройки генератора уровня платформера, ресурс `res://resources/demos/platformer_gen.tres`.
## Числа в тайлах. Прыжок героя: до `jump_dx` колонок вперёд и `jump_dy` рядов вверх; генератор
## и проверка проходимости считают с ними.

const PATH := "res://resources/demos/platformer_gen.tres"

@export var width := 200
@export var height := 16
@export var base_height := 3
@export var min_height := 2
@export var max_height := 6
@export var start_flat := 10
@export var end_flat := 12
@export var segment_min := 5
@export var segment_max := 12
@export var pit_chance := 0.35
@export var pit_min := 2
@export var pit_max := 4
@export var landing_min := 4
@export var step_chance := 0.3
@export var step_max := 2
@export var platform_chance := 0.4
@export var platform_min := 3
@export var platform_max := 5
@export var platform_lift_min := 3
@export var platform_lift_max := 4
@export var enemy_chance := 0.5
@export var enemy_min_segment := 6
@export var coin_chance := 0.6
@export var jump_dx := 5
@export var jump_dy := 4


static func load_default() -> PlatformerGenTuning:
	var t := load(PATH) as PlatformerGenTuning
	return t if t != null else PlatformerGenTuning.new()
