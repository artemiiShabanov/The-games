class_name ShooterVectorGenTuning
extends Resource
## Настройки генератора волн шутера × вектор (#92), ресурс
## `res://resources/demos/shooter_vector_gen.tres`. Пиксели логического экрана демки, секунды.

const PATH := "res://resources/demos/shooter_vector_gen.tres"

## Появлений в расписании и время первого.
@export var count := 30
@export var first_time := 1.2
## Промежуток между появлениями в начале и в конце расписания, разброс в долях.
@export var interval_start := 2.1
@export var interval_end := 1.2
@export var interval_jitter := 0.2
## Доля глыб и вьюнов; вьюны не раньше этого по счёту появления.
@export var rock_share := 0.25
@export var spinner_share := 0.22
@export var spinner_from := 5
## Доля появлений сбоку (в секторах ±`side_angle` градусов от горизонтали): экран широкий,
## сбоку врага видно дольше. Быстрые враги появляются только сбоку.
@export var side_share := 0.7
@export var side_angle := 35.0
## Соседние по времени появления не ближе этого по направлению, градусы.
@export var min_turn := 25.0
@export var enemy_speed_min := 105.0
@export var enemy_speed_max := 145.0
@export var rock_speed_min := 62.0
@export var rock_speed_max := 82.0
@export var spinner_speed_min := 70.0
@export var spinner_speed_max := 90.0
## Угловая скорость вьюна вокруг башни, градусов в секунду.
@export var spinner_spin_min := 16.0
@export var spinner_spin_max := 28.0


static func load_default() -> ShooterVectorGenTuning:
	var t := load(PATH) as ShooterVectorGenTuning
	return t if t != null else ShooterVectorGenTuning.new()
