class_name RacingVectorTuning
extends Resource
## Темп и правила демки гонки × вектор «полосы» (#91), ресурс
## `res://resources/demos/racing_vector.tres`. Пиксели логического экрана демки, скорости в
## пикселях в секунду.

const PATH := "res://resources/demos/racing_vector.tres"

## Скорость без газа и с газом; разгон и сброс, пикселей в секунду за секунду.
@export var cruise_speed := 300.0
@export var gas_speed := 620.0
@export var accel := 520.0
@export var brake := 420.0
## Перестроение на соседнюю полосу, секунды.
@export var shift_seconds := 0.11
## Столкновение: скорость падает до этой, газ не работает столько секунд.
@export var crash_speed := 140.0
@export var crash_stun := 0.7
## Удар в соперника сзади: скорость падает до доли его скорости.
@export var bump_keep := 0.6
## Размеры для столкновений: длина машины и препятствия вдоль дороги, ширина касания в полосах.
@export var car_len := 88.0
@export var obstacle_len := 56.0
@export var hit_lanes := 0.55
## Соперник: как далеко смотрит вперёд, как быстро меняет скорость, покачивание темпа в долях.
@export var rival_look := 420.0
@export var rival_accel := 320.0
@export var rival_wobble := 0.05
## Бот WIN: как далеко смотрит, с каким запасом вдоль дороги перестраивается, за сколько
## секунд до удара бросает газ.
@export var bot_look := 660.0
@export var bot_side_clear := 150.0
@export var bot_brake_seconds := 0.3
@export var music_db := -12.0
@export var sfx_db := -6.0


static func load_default() -> RacingVectorTuning:
	var t := load(PATH) as RacingVectorTuning
	return t if t != null else RacingVectorTuning.new()
