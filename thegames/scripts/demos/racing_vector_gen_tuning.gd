class_name RacingVectorGenTuning
extends Resource
## Настройки генератора заезда гонок × вектор (#91), ресурс
## `res://resources/demos/racing_vector_gen.tres`. Пиксели логического экрана демки.

const PATH := "res://resources/demos/racing_vector_gen.tres"

@export var lanes := 4
## Длина заезда от старта до финиша.
@export var length := 24000.0
## Первый ряд препятствий не ближе этого к старту, последний не ближе `last_clear` к финишу.
@export var first_row := 1500.0
@export var last_clear := 900.0
## Расстояние между рядами препятствий.
@export var row_gap_min := 520.0
@export var row_gap_max := 980.0
## Шанс двух и трёх препятствий в ряду; одна полоса в ряду всегда свободна.
@export var two_chance := 0.45
@export var three_chance := 0.1
@export var rivals := 3
## Темп соперников: самый медленный и самый быстрый, остальные между ними; разброс в долях.
@export var rival_pace_min := 440.0
@export var rival_pace_max := 510.0
@export var rival_pace_jitter := 0.02
## Фора: ближний соперник и дальний впереди игрока на старте.
@export var rival_head_min := 260.0
@export var rival_head_max := 900.0


static func load_default() -> RacingVectorGenTuning:
	var t := load(PATH) as RacingVectorGenTuning
	return t if t != null else RacingVectorGenTuning.new()
