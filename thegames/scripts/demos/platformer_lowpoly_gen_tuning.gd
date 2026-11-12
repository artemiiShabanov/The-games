class_name PlatformerLowpolyGenTuning
extends Resource
## Настройки генератора тропы платформера × low poly (#112), ресурс
## `res://resources/demos/platformer_lowpoly_gen.tres`. Метры. Значения с суффиксами `_first` и
## `_last` это первый и последний кусок, между ними ровный переход: дальше ямы шире, скелеты
## быстрее.

const PATH := "res://resources/demos/platformer_lowpoly_gen.tres"

## Кусков тропы между стартом и финишем.
@export var pieces := 20
@export var start_length := 8
@export var end_length := 12
@export var end_width := 7
## Обычный кусок: длина и ширина, целые метры.
@export var plain_length_min := 8
@export var plain_length_max := 12
@export var width_min := 4
@export var width_max := 5
## Мостик: узкий настил.
@export var bridge_length_min := 6
@export var bridge_length_max := 9
@export var bridge_width := 2
## Кусок со скелетом: длина, скорость скелета.
@export var guard_length_min := 11
@export var guard_length_max := 13
@export var guard_speed_first := 1.4
@export var guard_speed_last := 2.4
## Кусок с рядом ящиков.
@export var crates_length_min := 11
@export var crates_length_max := 13
## Яма перед куском: ширина.
@export var gap_min := 1.8
@export var gap_first := 2.4
@export var gap_last := 3.2
## Шанс ямы перед куском и сколько ям в уровне самое малое.
@export var gap_chance := 0.55
@export var gaps_min := 4
## Перепад высоты через яму и наклон куска на всю длину, не больше.
@export var gap_step := 0.4
@export var slope := 0.6
## На сколько середина следующего куска уходит вбок, не больше.
@export var drift := 1.5
## Через яму куски перекрываются по ширине не меньше чем на столько.
@export var overlap_min := 2.0
## Дублонов на обычный кусок и над ямой.
@export var coins_plain := 3
@export var coins_gap := 2
## Доли видов кусков: обычный, мостик, скелет, ящики.
@export var share_plain := 0.3
@export var share_bridge := 0.2
@export var share_guard := 0.25
@export var share_crates := 0.25


static func load_default() -> PlatformerLowpolyGenTuning:
	var t := load(PATH) as PlatformerLowpolyGenTuning
	return t if t != null else PlatformerLowpolyGenTuning.new()
