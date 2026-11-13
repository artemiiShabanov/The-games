class_name ShooterLowpolyTuning
extends Resource
## Числа правил демки шутер × low poly «рельсовый тир» (#114), ресурс
## `res://resources/demos/shooter_lowpoly.tres`. Метры и секунды.

const PATH := "res://resources/demos/shooter_lowpoly.tres"

@export var lives := 3
@export var countdown := 2.0
## Угол обзора камеры по вертикали (градусы) и стороны кадра.
@export var fov := 50.0
@export var aspect := 2.0
## Прицел: скорость стрелками (долей полукадра в секунду) и край, дальше которого он не уходит.
@export var aim_speed := 1.5
@export var aim_edge := 0.96
## Пистолет: патронов в обойме, пауза между выстрелами, перезарядка.
@export var clip := 6
@export var fire_gap := 0.18
@export var reload := 1.0
## Враг: сколько высовывается и прячется, сколько сидит за укрытием после выстрела, с какой
## доли подъёма в него можно попасть.
@export var pop := 0.35
@export var duck := 0.3
@export var rest := 1.1
@export var hittable := 0.5
## Бегун в переезде: сколько секунд выбегает в кадр и с какой доли пробежки в него можно попасть.
@export var runner_run := 0.9
@export var runner_hittable := 0.3
## Мишени: середина и радиус туловища и головы над ступнями, запас попадания.
@export var torso_y := 1.08
@export var torso_r := 0.33
@export var head_y := 1.58
@export var head_r := 0.23
@export var hit_pad := 0.07
## Жизней у капитана.
@export var captain_hp := 2
## Бутылка: сколько летит, высота дуги, радиус попадания.
@export var bottle_flight := 1.5
@export var bottle_arc := 1.3
@export var bottle_r := 0.34
## Бочка с порохом: высота середины и радиус попадания.
@export var keg_y := 0.4
@export var keg_r := 0.45
## После попадания по игроку его не ранят столько секунд.
@export var mercy := 1.2
## Пауза между группами врагов и перед переездом.
@export var group_gap := 0.5
@export var leave_gap := 0.6
@export var max_seconds := 150.0
## Бот: реакция на новую цель, скорость прицела (долей полукадра в секунду), точность.
@export var bot_react := 0.22
@export var bot_speed := 2.6
@export var bot_tolerance := 0.02
## Отклик: стоп-кадр и белая заливка при попадании, тряска при ранении.
@export var hit_stop := 0.05
@export var hit_flash := 0.09
@export var shake := 0.35
@export var music_db := -10.0
@export var sfx_db := -6.0


static func load_default() -> ShooterLowpolyTuning:
	var t := load(PATH) as ShooterLowpolyTuning
	return t if t != null else ShooterLowpolyTuning.new()
