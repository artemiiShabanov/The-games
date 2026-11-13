class_name PlatformerThreedTuning
extends Resource
## Числа правил демки платформер × «продвинутые» «крюк-кошка» (#121), ресурс
## `res://resources/demos/platformer_threed.tres`. Метры и секунды.

const PATH := "res://resources/demos/platformer_threed.tres"

@export var lives := 3
@export var countdown := 1.5
## Бег: скорость, разгон и торможение, скорость поворота героя к ходу (рад/с).
@export var run_speed := 7.0
@export var run_accel := 55.0
@export var turn_speed := 14.0
## Прыжок и тяжесть; прыжок ещё столько секунд доступен после схода с края и столько секунд
## помнит нажатие до приземления.
@export var jump_speed := 7.2
@export var gravity := 18.0
@export var coyote := 0.12
@export var jump_buffer := 0.14
## Руление в воздухе: ускорение к стороне хода; быстрее бега оно не разгоняет.
@export var air_accel := 16.0
## Уступ: на сколько выше ступней может быть край, за который герой цепляется руками, и
## сколько секунд он забирается.
@export var climb_reach := 1.9
@export var climb_seconds := 0.5
## Крюк: с какого расстояния достаёт до кольца, самая короткая верёвка, наименьшая скорость
## качания вперёд (разбег добавляется сам), подкачка ходом на верёвке, множитель скорости на
## отпускании.
@export var rope_max := 9.5
@export var rope_min := 3.0
@export var swing_min := 9.0
@export var swing_accel := 4.0
@export var release_boost := 1.04
## После отпускания за то же кольцо столько секунд не зацепиться.
@export var rehook := 0.5
## Вода: на сколько ниже самого низкого острова; падение стоит жизни, после него столько
## секунд героя нет.
@export var water_drop := 5.0
@export var respawn_seconds := 0.9
@export var max_seconds := 200.0
## Бот: запас до края острова при посадке и от дальности верёвки.
@export var bot_margin := 0.5
## Камера: расстояние, высота точки взгляда над ступнями, наклон по умолчанию и его пределы
## (радианы, плюс это сверху), через сколько секунд без мыши камера сама доворачивает за ходом
## и с какой скоростью (1/с).
@export var cam_distance := 8.6
@export var cam_look := 1.7
@export var cam_pitch := 0.3
@export var cam_pitch_min := -0.35
@export var cam_pitch_max := 1.1
@export var cam_auto_delay := 1.2
@export var cam_auto := 1.6
@export var cam_follow := 9.0
@export var hit_stop := 0.1
@export var music_db := -10.0
@export var sfx_db := -6.0


static func load_default() -> PlatformerThreedTuning:
	var t := load(PATH) as PlatformerThreedTuning
	return t if t != null else PlatformerThreedTuning.new()
