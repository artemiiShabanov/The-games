class_name ShooterVectorTuning
extends Resource
## Темп и правила демки шутер × вектор «башня в центре» (#92), ресурс
## `res://resources/demos/shooter_vector.tres`. Пиксели логического экрана демки, секунды.

const PATH := "res://resources/demos/shooter_vector.tres"

## Жизни: одна за каждого, кто долетел до башни.
@export var lives := 3
## Сколько уничтожить; глыба и каждый её осколок считаются по одному.
@export var goal := 30
## Поворот ствола, градусов в секунду.
@export var turn_speed := 205.0
## Выстрелы, пока держат кнопку: промежуток и скорость.
@export var fire_every := 0.25
@export var shot_speed := 900.0
## Радиус башни (кто дошёл до него, стоит жизни) и расстояние от центра до дула.
@export var turret_radius := 46.0
@export var muzzle := 78.0
## Радиусы попадания: враг, глыба, осколок, вьюн.
@export var enemy_radius := 34.0
@export var rock_radius := 44.0
@export var small_radius := 26.0
@export var spinner_radius := 32.0
## Осколки глыбы: на сколько пикселей расходятся в стороны и во сколько раз быстрее глыбы.
@export var split_offset := 48.0
@export var small_speed_mult := 1.5
## Потеря жизни сметает всех в этом радиусе от башни (они не засчитываются).
@export var blast_radius := 240.0
## Появления за краем экрана на столько пикселей.
@export var spawn_margin := 40.0
## Расписание повторяется: промежутки умножаются на первое, скорости на второе.
@export var loop_interval_mult := 0.7
@export var loop_speed_mult := 1.2
## Бот WIN: стреляет, когда ствол смотрит в цель с точностью в эту долю её радиуса.
@export var bot_aim := 0.6
## Бот LOSE: крутит ствол с этой долей скорости и не стреляет.
@export var bot_lose_turn := 0.3
@export var music_db := -12.0
@export var sfx_db := -6.0


static func load_default() -> ShooterVectorTuning:
	var t := load(PATH) as ShooterVectorTuning
	return t if t != null else ShooterVectorTuning.new()
