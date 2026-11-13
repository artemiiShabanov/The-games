class_name PlatformerThreedGenTuning
extends Resource
## Настройки генератора уровня платформера × «продвинутые» (#121), ресурс
## `res://resources/demos/platformer_threed_gen.tres`. Метры, секунды, градусы.

const PATH := "res://resources/demos/platformer_threed_gen.tres"

## Остров: радиус большого (кусок земли) от и до, радиус камня в секции камней, радиус острова
## для посадки после поздних цепочек колец, неровность края (доля радиуса).
@export var land_min := 5.0
@export var land_max := 8.0
@export var stone := 1.5
@export var land_late := 3.6
@export var wobble := 0.09
## Простой прыжок: ширина пропасти от края до края и перепад высоты.
@export var jump_min := 3.9
@export var jump_max := 4.8
@export var jump_drop := 0.8
## Между камнями пропасть короче.
@export var stone_gap_min := 3.0
@export var stone_gap_max := 3.9
## Уступ: до стены и на сколько она выше.
@export var climb_gap_min := 1.2
@export var climb_gap_max := 1.9
@export var climb_rise_min := 2.0
@export var climb_rise_max := 2.25
## Кольца: от края до первого кольца, шаг между кольцами цепочки, от последнего до острова,
## высота кольца над линией между краями.
@export var ring_lead_min := 4.4
@export var ring_lead_max := 5.4
@export var ring_step_min := 8.6
@export var ring_step_max := 10.4
@export var ring_out_min := 6.0
@export var ring_out_max := 7.6
@export var ring_height_min := 5.6
@export var ring_height_max := 6.8
## Перепад высоты островов на пропасти с кольцами и разброс высоты колец в цепочке.
@export var ring_rise := 1.6
@export var ring_scatter := 1.2
## Движущееся кольцо: размах и период хода вверх-вниз.
@export var moving_amp := 1.2
@export var moving_period := 2.6
## Поворот пути на острове и предел курса от начального.
@export var turn_min := 22.0
@export var turn_max := 58.0
@export var heading_limit := 105.0
## Высота островов над начальным: пределы.
@export var height_max := 7.0
## Реквизит на большом острове: сколько вещей и как далеко от пути героя.
@export var props_min := 3
@export var props_max := 6
@export var prop_clear := 1.7


static func load_default() -> PlatformerThreedGenTuning:
	var t := load(PATH) as PlatformerThreedGenTuning
	return t if t != null else PlatformerThreedGenTuning.new()
