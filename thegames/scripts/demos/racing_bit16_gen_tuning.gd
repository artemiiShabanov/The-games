class_name RacingBit16GenTuning
extends Resource
## Настройки генератора трассы гонки × 16/32-bit (#99), ресурс
## `res://resources/demos/racing_bit16_gen.tres`. Длины в сегментах, изгиб в единицах сдвига
## дороги на сегмент (как у классических псевдо-3D), высота в единицах мира.

const PATH := "res://resources/demos/racing_bit16_gen.tres"

## Сегментов до финиша, прямая на старте и после финиша.
@export var length := 2700
@export var start_straight := 40
@export var after_finish := 260
## Участки: прямая, поворот (въезд, дуга, выезд), холм.
@export var straight_min := 20
@export var straight_max := 60
@export var curve_enter := 14
@export var curve_hold_min := 20
@export var curve_hold_max := 55
@export var curve_easy := 2.0
@export var curve_hard := 5.0
## Доля крутых поворотов в начале и в конце трассы.
@export var hard_first := 0.15
@export var hard_last := 0.45
@export var hill_min := 600.0
@export var hill_max := 2600.0
## Поворот и холм вместе.
@export var combo_chance := 0.4
## Пропы: пальма через столько сегментов с каждой стороны, доля камней и бочек.
@export var prop_every_min := 3
@export var prop_every_max := 7
@export var rock_chance := 0.2
@export var barrel_chance := 0.12
@export var hut_chance := 0.04
## Знак перед крутым поворотом за столько сегментов.
@export var sign_ahead := 22
## Монеты: ряд через столько сегментов, монет в ряду, шаг.
@export var coin_row_every := 90
@export var coins_per_row := 5
@export var coin_step := 3
## Соперники: сколько, ряды по двое через столько сегментов, доли наибольшей скорости.
@export var rivals := 11
@export var grid_gap := 4
@export var rival_speed_min := 0.78
@export var rival_speed_max := 0.93


static func load_default() -> RacingBit16GenTuning:
	var t := load(PATH) as RacingBit16GenTuning
	return t if t != null else RacingBit16GenTuning.new()
