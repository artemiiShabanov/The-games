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
@export var segment_max := 10
@export var pit_chance := 0.35
@export var pit_min := 2
@export var pit_max := 4
## Яма под рывок: шире обычного прыжка, перелетается прыжком с дэшем в воздухе.
@export var dash_pit_chance := 0.3
@export var dash_pit_min := 6
@export var dash_pit_max := 7
## Яма под рывок не раньше чем через столько колонок после последнего ходока: к обрыву надо
## подойти по земле, а не прилететь с прыжка через врага.
@export var dash_pit_gap := 8
@export var landing_min := 4
@export var step_chance := 0.3
@export var step_max := 2
@export var platform_chance := 0.4
@export var platform_min := 3
@export var platform_max := 5
@export var platform_lift_min := 2
@export var platform_lift_max := 3
## Второй ярус: платформа над первой, ряд стояния выше не больше чем на `jump_dy`.
@export var platform_second_chance := 0.5
## Насколько второй ярус выше первого в рядах; 0 значит `jump_dy − 1` (8-bit). ASCII: 2, иначе
## при прыжке на две клетки второй ярус лёг бы на голову стоящему на первом.
@export var platform_second_lift := 0
## Ходок на платформе второго яруса длиной от трёх.
@export var platform_enemy_chance := 0.4
@export var enemy_chance := 0.9
@export var enemy_min_segment := 8
## Доля летунов среди врагов отрезка и высота их нижнего края над землёй в рядах.
@export var flyer_share := 0.4
@export var flyer_height := 2
## Летун только на отрезке от такой длины и патрулирует его середину: прыжки на входе и
## выходе отрезка должны быть свободны.
@export var flyer_min_segment := 8
@export var coin_chance := 0.7
## Ряд монет над платформой (от ряда платформы). ASCII: 1, монеты лежат на ней, иначе ряд монет
## совпал бы с рядом второго яруса.
@export var platform_coin_lift := 2
@export var jump_dx := 5
@export var jump_dy := 4
## Сколько колонок добавляет дэш в воздухе; приземление при этом не выше двух рядов.
@export var dash_dx := 3
## Дальность прыжка на поверхность выше старта; 0 значит `jump_dx` (8-bit). ASCII (#90): прыжок
## по клеткам на высоте держится недолго, вверх он короче, чем вровень или вниз.
@export var jump_dx_up := 0


static func load_default() -> PlatformerGenTuning:
	var t := load(PATH) as PlatformerGenTuning
	return t if t != null else PlatformerGenTuning.new()
