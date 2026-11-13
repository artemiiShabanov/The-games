class_name SportLowpolyTuning
extends Resource
## Числа правил демки спорт × low poly «броски в кольцо» (#115), ресурс
## `res://resources/demos/sport_lowpoly.tres`. Метры и секунды.

const PATH := "res://resources/demos/sport_lowpoly.tres"

## Бросков в демке и сколько очков надо набрать.
@export var shots := 10
@export var goal := 20
@export var countdown := 1.5
## Во сколько раз модель кольца на мачте крупнее исходной; размеры ниже в метрах модели.
@export var hoop_scale := 1.3
## На сколько мачта вкопана в песок: кольцо ниже, смотреть на него не так круто вверх.
@export var hoop_sink := 1.0
@export var rim_y := 3.05
@export var rim_z := -0.42
@export var rim_r := 0.2175
@export var rim_tube := 0.025
@export var board_z := -0.15
@export var board_half := 0.65
@export var board_y0 := 2.925
@export var board_y1 := 3.875
## Мяч: радиус, упругость отскока от обруча и от щита, тяжесть.
@export var ball_r := 0.12
@export var bounce_rim := 0.5
@export var bounce_board := 0.55
## Отскок от земли и как быстро мяч на ней останавливается.
@export var bounce_ground := 0.45
@export var ground_drag := 2.5
@export var gravity := 9.8
## Бросок: высота рук и глаз, на сколько вперёд от точки выпускается мяч.
@export var launch_height := 1.9
@export var launch_forward := 0.3
@export var eye := 1.7
## Прицел: скорость стрелками (рад/с) и предел в стороны.
@export var aim_speed := 0.4
@export var aim_limit := 0.42
## Ветер: ускорение одной стрелки (м/с²).
@export var wind_unit := 0.35
## Какую долю «чистого» диапазона скорости занимает зелёная зона шкалы.
@export var zone_fill := 0.85
## За краем зелёной зоны: доля скорости, что теряется или добавляется на всю длину шкалы.
@export var miss_gain := 0.4
## Очки: за чистый бросок сверху, с какой серии мяч горит и во сколько раз дороже.
@export var clean_bonus := 1
@export var fire_streak := 3
@export var fire_mult := 2
## Паузы: итог броска на экране, переход к следующей точке, сколько летит упавший мяч.
@export var result_seconds := 1.0
@export var move_seconds := 0.8
@export var flight_limit := 5.0
## Бот: пауза перед замахом и насколько точно ловит середину зоны (доля её половины).
@export var bot_wait := 0.35
@export var bot_precision := 0.3
@export var music_db := -10.0
@export var sfx_db := -6.0


static func load_default() -> SportLowpolyTuning:
	var t := load(PATH) as SportLowpolyTuning
	return t if t != null else SportLowpolyTuning.new()
