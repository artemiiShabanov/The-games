class_name PlatformerBit16GenTuning
extends Resource
## Настройки генератора уровня платформера × 16/32-bit «тропа» (#98), ресурс
## `res://resources/demos/platformer_bit16_gen.tres`. Пиксели мира и секунды. Пары `_first` и
## `_last` это начало и конец уровня, между ними ровный переход: к концу ямы шире, враги быстрее.

const PATH := "res://resources/demos/platformer_bit16_gen.tres"

## Длина уровня; первые `start_flat` и последние `end_flat` пикселей без ловушек.
@export var width := 4600.0
@export var start_flat := 200.0
@export var end_flat := 240.0
## Уровень земли и вода в ямах (y экрана).
@export var ground_y := 200.0
@export var ground_min_y := 130.0
@export var ground_max_y := 222.0
@export var water_y := 250.0
## Отдых между ловушками.
@export var rest_min := 70.0
@export var rest_max := 140.0
## Холм: высота подъёма. Поверхности ровные, склоны двух наклонов, как плитки 16-битных
## платформеров: пологий 1 к 2 и крутой 1 к 1 (доля крутых `steep_chance`).
@export var hill_rise_min := 24.0
@export var hill_rise_max := 64.0
@export var slope_gentle_deg := 26.57
@export var slope_steep_deg := 45.0
@export var steep_chance := 0.3
## Яма: ширина в начале и в конце уровня, разница высот краёв.
@export var gap_first := 44.0
@export var gap_last := 80.0
@export var gap_step := 14.0
## Широкая яма с лианами: ширина, лиана висит до стольких пикселей над краем.
@export var vine_gap_min := 160.0
@export var vine_gap_max := 210.0
@export var vine_reach := 34.0
## Арка: ширина и просвет под корнями.
@export var arch_min := 64.0
@export var arch_max := 104.0
@export var arch_gap := 18.0
## Краб: участок и скорость.
@export var crab_span_min := 110.0
@export var crab_span_max := 170.0
@export var crab_speed_first := 40.0
@export var crab_speed_last := 64.0
## Попугай: участок и скорость.
@export var parrot_span_min := 120.0
@export var parrot_span_max := 190.0
@export var parrot_speed_first := 56.0
@export var parrot_speed_last := 84.0
## Веса ловушек: холм, яма, лианы, арка, краб, попугай, краб на холме, спуск в арку.
@export var weight_hill := 1.5
@export var weight_gap := 2.0
@export var weight_vines := 1.5
@export var weight_arch := 1.5
@export var weight_crab := 1.5
@export var weight_parrot := 1.5
@export var weight_hill_crab := 1.0
@export var weight_slope_arch := 1.0
## Монеты: шанс над ловушкой и на отдыхе.
@export var coin_trap_chance := 0.85
@export var coin_rest_chance := 0.3
## Украшения: в среднем через столько пикселей.
@export var decor_every := 24.0


static func load_default() -> PlatformerBit16GenTuning:
	var t := load(PATH) as PlatformerBit16GenTuning
	return t if t != null else PlatformerBit16GenTuning.new()
