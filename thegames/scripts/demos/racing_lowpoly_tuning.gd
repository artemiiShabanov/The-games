class_name RacingLowpolyTuning
extends Resource
## Числа правил демки гонки × low poly «кольцо с дрифтом» (#113), ресурс
## `res://resources/demos/racing_lowpoly.tres`. Метры и секунды.

const PATH := "res://resources/demos/racing_lowpoly.tres"

@export var laps := 2
## Отсчёт перед стартом.
@export var countdown := 2.0
## Шлюпка: предел скорости, разгон, торможение, сопротивление без газа, задний ход.
@export var top_speed := 22.0
@export var accel := 11.0
@export var brake := 22.0
@export var drag := 5.0
@export var reverse_speed := 6.0
## Руль: поворот на малой скорости (рад/с) и скорость, на которой он вдвое слабее.
@export var turn_rate := 3.1
@export var turn_ref := 20.0
## Сцепление: как быстро скорость выравнивается по курсу, обычно и в заносе.
@export var grip := 9.0
@export var drift_grip := 2.4
## Дрифт: с какой скорости начинается, во сколько раз резче руль, сколько скорости съедает в
## секунду, сколько заноса даёт ускорение и сколько нужно на полное.
@export var drift_min_speed := 9.0
@export var drift_turn := 1.6
@export var drift_drag := 0.12
@export var charge_min := 0.45
@export var charge_full := 1.3
## Ускорение (дрифт и ветер): множитель предела скорости, длительность, толчок сразу.
@export var boost_mult := 1.32
@export var boost_seconds := 1.4
@export var boost_kick := 3.5
@export var wind_seconds := 1.1
## Грязь: множитель предела скорости. Борт: сколько скорости остаётся после удара и
## торможение, пока шлюпка трётся.
@export var mud_mult := 0.55
@export var wall_keep := 0.78
@export var wall_drag := 7.0
## Половина ширины шлюпки и радиус столкновения с соперником.
@export var car_half := 0.9
@export var car_radius := 1.0
@export var bump_keep := 0.88
## Вылет в воду: сколько секунд теряется и на сколько метров назад возвращает.
@export var sink_seconds := 2.0
@export var sink_back := 6.0
## Трамплин: доля предела скорости, с которой шлюпка перелетает промоину, высота дуги, на
## сколько до трамплина возвращает после падения.
@export var ramp_speed := 0.62
@export var ramp_height := 1.9
@export var ramp_back := 30.0
## Соперники: доли предела скорости, разгон и поперечное ускорение в поворотах.
@export var rival_skills: Array[float] = [0.95, 1.01, 1.06]
@export var rival_accel := 10.0
@export var rival_lateral := 16.0
## Гонка кончается через столько секунд после финиша последнего соперника, если игрок не доехал.
@export var grace_seconds := 8.0
@export var max_seconds := 150.0
## Бот: поперечное ускорение, под которое он тормозит, кривизна, с которой дрифтует, запас
## взгляда вперёд (метры и секунды хода).
@export var bot_lateral := 11.0
@export var bot_drift_curve := 0.026
@export var bot_look := 5.0
@export var bot_look_time := 0.4
## Камера за шлюпкой.
@export var cam_distance := 6.2
@export var cam_height := 2.5
@export var cam_look := 1.0
@export var cam_turn := 5.0
## Дым в заносе: клубов в запасе, пауза между клубами, сколько живёт, размер, подъём (м/с) и
## цвет, когда заряд уже даёт ускорение.
@export var smoke_count := 24
@export var smoke_every := 0.04
@export var smoke_life := 0.45
@export var smoke_size := 0.6
@export var smoke_rise := 1.1
## Какую долю скорости шлюпки клуб уносит с собой и цвет обычного дыма.
@export var smoke_follow := 0.82
@export var smoke_color := Color(0.92, 0.89, 0.8)
@export var smoke_hot := Color(1.0, 0.62, 0.25)
@export var music_db := -10.0
@export var sfx_db := -6.0


static func load_default() -> RacingLowpolyTuning:
	var t := load(PATH) as RacingLowpolyTuning
	return t if t != null else RacingLowpolyTuning.new()
