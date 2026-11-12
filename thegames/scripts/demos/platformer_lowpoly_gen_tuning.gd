class_name PlatformerLowpolyGenTuning
extends Resource
## Настройки генератора тропы платформера × low poly (#112), ресурс
## `res://resources/demos/platformer_lowpoly_gen.tres`. Метры и секунды. Значения с суффиксами
## `_first` и `_last` это начало и конец косы, между ними ровный переход: дальше ямы шире,
## скелеты, бочки и плоты быстрее, пушки стреляют чаще.

const PATH := "res://resources/demos/platformer_lowpoly_gen.tres"

## Кусков тропы между стартом и финишем (россыпь камней-ступенек считается за один).
@export var pieces := 18
@export var start_length := 8
@export var end_length := 12
@export var end_width := 7
## Обычный кусок: длина и ширина, целые метры.
@export var plain_length_min := 8
@export var plain_length_max := 11
@export var width_min := 4
@export var width_max := 5
## Мостик: узкий настил.
@export var bridge_length_min := 6
@export var bridge_length_max := 9
@export var bridge_width := 2
## Кусок со скелетами: длина, скорость, с какой доли косы скелеты ходят парой в противофазе.
@export var guard_length_min := 12
@export var guard_length_max := 14
@export var guard_speed_first := 1.7
@export var guard_speed_last := 2.7
@export var guard_pair_from := 0.35
## Кусок с рядом ящиков.
@export var crates_length_min := 11
@export var crates_length_max := 13
## Каток: по куску навстречу катятся бочки. Длина, ширина, скорость бочек, период.
@export var roll_length_min := 14
@export var roll_length_max := 18
@export var roll_width := 4
@export var roll_speed_first := 5.0
@export var roll_speed_last := 7.0
@export var roll_period_first := 2.4
@export var roll_period_last := 1.7
## Обстрел: пушки с островков бьют поперёк куска. Длина, число пушек, период, скорость ядра.
@export var fire_length_min := 12
@export var fire_length_max := 14
@export var fire_cannons_first := 2
@export var fire_cannons_last := 3
@export var fire_period_first := 2.7
@export var fire_period_last := 2.0
@export var fire_speed := 9.0
## Камни-ступеньки: сколько, сторона камня, яма между ними, сдвиг вбок.
@export var stone_count_min := 3
@export var stone_count_max := 4
@export var stone_size := 2
@export var stone_gap_min := 1.6
@export var stone_gap_max := 2.3
@export var stone_jitter := 0.5
## Яма перед куском: ширина, шанс, сколько ям в уровне самое малое.
@export var gap_min := 1.8
@export var gap_first := 2.6
@export var gap_last := 3.5
@export var gap_chance := 0.5
@export var gaps_min := 4
## Плот над широкой водой: шанс вместо обычной ямы (не в начале косы), прыжок до плота и с
## него, половина стороны плота, размах и скорость хода, сколько плотов самое малое.
@export var raft_chance := 0.45
@export var raft_from := 0.2
@export var raft_hop := 2.3
@export var raft_half := 1.25
@export var raft_reach := 2.2
@export var raft_speed_first := 1.6
@export var raft_speed_last := 2.6
@export var rafts_min := 1
## Уступ на стыке без ямы: шанс и высота. Перепад через яму и наклон куска на всю длину.
@export var step_chance := 0.4
@export var step_min := 0.8
@export var step_max := 1.1
@export var steps_min := 2
@export var gap_step := 0.5
@export var slope := 1.0
@export var height_min := -1.0
@export var height_max := 4.5
## Поворот под прямым углом после куска: шанс и сколько поворотов самое малое.
@export var turn_chance := 0.3
@export var turns_min := 2
## На сколько середина следующего куска уходит вбок, не больше; через яму куски перекрываются
## по ширине не меньше чем на столько.
@export var drift := 1.5
@export var overlap_min := 2.0
## Дублонов на обычный кусок и над ямой.
@export var coins_plain := 3
@export var coins_gap := 2
## Доли видов кусков.
@export var share_plain := 0.14
@export var share_bridge := 0.1
@export var share_guard := 0.17
@export var share_crates := 0.13
@export var share_roll := 0.17
@export var share_fire := 0.15
@export var share_stone := 0.14


static func load_default() -> PlatformerLowpolyGenTuning:
	var t := load(PATH) as PlatformerLowpolyGenTuning
	return t if t != null else PlatformerLowpolyGenTuning.new()
