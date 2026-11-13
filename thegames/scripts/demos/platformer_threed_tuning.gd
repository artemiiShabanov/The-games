class_name PlatformerThreedTuning
extends Resource
## Числа правил демки платформер × «продвинутые» «крюк-кошка» (#121), ресурс
## `res://resources/demos/platformer_threed.tres`. Метры и секунды.

const PATH := "res://resources/demos/platformer_threed.tres"

@export var lives := 3
@export var countdown := 1.5
## Бег по островку, прыжок, тяжесть, руление в воздухе вдоль пути и вбок.
@export var run_speed := 6.2
@export var run_accel := 30.0
@export var jump_speed := 6.6
@export var gravity := 15.0
@export var air_accel := 5.0
@export var side_speed := 3.2
## Крюк: с какого расстояния достаёт до кольца, самая короткая верёвка, наименьшая скорость
## качания вперёд (разбег добавляется сам), множитель скорости на отпускании.
@export var rope_max := 7.6
@export var rope_min := 2.6
@export var swing_min := 8.4
@export var release_boost := 1.04
## После отпускания за то же кольцо столько секунд не зацепиться.
@export var rehook := 0.5
## Вода: на сколько ниже самого низкого островка; падение стоит жизни, после него столько
## секунд героя не ранят и он стоит.
@export var water_drop := 4.0
@export var respawn_seconds := 0.9
@export var max_seconds := 150.0
## Бот: запас до края островка при посадке и от дальности верёвки.
@export var bot_margin := 0.45
## Камера за спиной героя.
@export var cam_distance := 8.2
@export var cam_height := 3.6
@export var cam_look := 1.6
@export var cam_turn := 2.6
@export var hit_stop := 0.1
@export var music_db := -10.0
@export var sfx_db := -6.0


static func load_default() -> PlatformerThreedTuning:
	var t := load(PATH) as PlatformerThreedTuning
	return t if t != null else PlatformerThreedTuning.new()
