class_name ShooterLowpolyGenTuning
extends Resource
## Настройки генератора маршрута шутера × low poly «рельсовый тир» (#114), ресурс
## `res://resources/demos/shooter_lowpoly_gen.tres`. Метры, секунды, градусы.

const PATH := "res://resources/demos/shooter_lowpoly_gen.tres"

## Остановок с боем (после последней ещё переезд к финишу).
@export var stops := 5
## Переезд: длина от и до, поворот пути от и до (градусы), предел ухода от начального курса.
@export var leg_min := 10.0
@export var leg_max := 14.0
@export var turn_min := 25.0
@export var turn_max := 60.0
@export var heading_limit := 100.0
## Куда смотрит камера на остановке: отклонение от пути до стольких градусов.
@export var view_turn := 30.0
## Высота глаз над землёй и скорость камеры в переезде.
@export var eye := 1.6
@export var speed := 3.6
## Дюны: высота двух волн, длина волны, подъём острова над водой, с какого расстояния от пути
## берег уходит вниз и как круто.
@export var dune_a := 0.9
@export var dune_b := 0.5
@export var dune_length := 26.0
@export var island_height := 1.3
@export var shore_from := 17.0
@export var shore_slope := 0.3
## Укрытия остановки: сколько от и до, расстояние от и до, разброс по ширине кадра (доля).
@export var covers_min := 4
@export var covers_max := 5
@export var cover_near := 5.5
@export var cover_far := 10.5
@export var cover_spread := 0.74
## Группы врагов на остановке (к концу маршрута больше) и врагов в группе.
@export var groups_first := 2
@export var groups_last := 3
@export var group_min := 1
@export var group_max := 3
## Пауза между появлениями в группе.
@export var stagger := 0.7
## Время прицеливания матроса на первой и на последней остановке, капитана, бегуна в переезде;
## замах метателя.
@export var aim_first := 2.7
@export var aim_last := 1.9
@export var aim_captain := 1.5
@export var aim_runner := 2.1
@export var windup := 1.1
## Метатели: с какой остановки (с нуля) и доля среди матросов. Капитанов на маршрут, пленных на
## маршрут от и до, бочек с порохом.
@export var thrower_from := 1
@export var thrower_share := 0.2
@export var captains := 2
@export var hostages_min := 3
@export var hostages_max := 4
@export var kegs := 2
@export var keg_radius := 3.2
## Сколько секунд пленный стоит с поднятыми руками.
@export var hostage_hold := 1.7
## Бегун в переезде: в какой доле переезда выбегает, расстояние от камеры от и до.
@export var runner_at := 0.12
@export var runner_near := 8.0
@export var runner_far := 11.0


static func load_default() -> ShooterLowpolyGenTuning:
	var t := load(PATH) as ShooterLowpolyGenTuning
	return t if t != null else ShooterLowpolyGenTuning.new()
