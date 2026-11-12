class_name RacingBit16Tuning
extends Resource
## Физика и правила гонки × 16/32-bit (#99), ресурс `res://resources/demos/racing_bit16.tres`.
## Скорость в единицах мира в секунду, `x` поперёк в полуширинах дороги; мир шагает 60 раз в
## секунду.

const PATH := "res://resources/demos/racing_bit16.tres"

## Наибольшая скорость: сегмент за кадр. Разгон, накат без газа, обочина.
@export var max_speed := 12000.0
@export var accel := 2400.0
@export var coast := 2000.0
@export var offroad_decel := 6000.0
@export var offroad_limit := 0.3
## Руль: сдвиг поперёк за секунду на полной скорости; поворот выносит наружу на долю изгиба.
@export var steer := 2.0
@export var centrifugal := 0.25
## Нитро: зарядов на заезд, длительность, множитель наибольшей скорости и разгона.
@export var nitros := 3
@export var nitro_seconds := 2.0
@export var nitro_mult := 1.35
## Удар: соперник шириной в полуширинах; после удара сзади скорость падает до доли его.
@export var car_width := 0.3
@export var bump_keep := 0.8
## Проп на обочине: ширина, скорость после удара.
@export var prop_width := 0.28
@export var crash_speed := 0.15
## После удара или аварии герой мигает столько секунд (новый удар о соперника в это время не
## считается).
@export var hit_seconds := 0.8
@export var coin_width := 0.25
## Соперники перестраиваются от медленного впереди за столько сегментов, с такой скоростью.
@export var rival_look := 10
@export var rival_steer := 0.8
## Бот WIN: видит соперников на столько сегментов; нитро жмёт, если впереди на столько
## сегментов нет поворота круче `bot_nitro_curve` (за 2 с нитро около 160 сегментов).
@export var bot_look := 20
@export var bot_nitro_straight := 150
@export var bot_nitro_curve := 3.2
@export var max_seconds := 240.0
## Старт: отсчёт 3, 2, 1 после нажатия A, по секунде на цифру.
@export var countdown := 3.0
## Камера: высота над дорогой, угол обзора, сколько сегментов рисуется, длина полосы цвета
## (светлая и тёмная дорога, бордюр) в сегментах; фон сдвигается на поворотах с такой долей.
@export var cam_height := 1000.0
@export var fov := 100.0
@export var draw_distance := 200
@export var band_len := 3
@export var backdrop_shift := 0.004
@export var music_db := -12.0
@export var sfx_db := -6.0


static func load_default() -> RacingBit16Tuning:
	var t := load(PATH) as RacingBit16Tuning
	return t if t != null else RacingBit16Tuning.new()
