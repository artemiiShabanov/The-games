class_name RacingThreedTuning
extends Resource
## Числа правил демки гонки × «продвинутые» «спринт» (#122), ресурс
## `res://resources/demos/racing_threed.tres`. Метры, секунды, радианы.

const PATH := "res://resources/demos/racing_threed.tres"

@export var countdown := 2.0
## Передачи: предел скорости каждой и тяга на ней (м/с²). Переключение вверх на доле оборотов
## `shift_up`, вниз на `shift_down` (доля оборотов низшей передачи).
@export var gear_speeds: Array[float] = [11.0, 19.0, 27.0, 34.0, 40.0]
@export var gear_pulls: Array[float] = [9.0, 7.0, 5.2, 3.8, 2.7]
@export var shift_up := 0.93
@export var shift_down := 0.62
## Сколько секунд на переключении нет тяги; с отпущенным газом переключение короче.
@export var shift_seconds := 0.3
@export var shift_soft := 0.12
## Торможение двигателем без газа и на переключении, тормоз, задний ход.
@export var engine_brake := 1.6
@export var brake := 11.0
@export var reverse_speed := 5.0
## Сопротивление: качение и воздух (на квадрат скорости).
@export var rolling := 0.25
@export var air := 0.0009
## База машины, вылет центра масс и момент инерции (в долях m·a²: больше, ленивее поворот).
@export var wheelbase := 2.6
@export var inertia := 1.25
## Шины: жёсткость увода (1/рад в долях веса) и предел бокового ускорения на асфальте.
@export var cornering := 9.0
@export var grip := 10.5
## Сцепление падает с ростом скорости: доля на м/с.
@export var grip_fade := 0.004
## Помощь игроку: задняя ось держит чуть лучше передней, машину доворачивает к повороту руля
## (1/с), боковое скольжение гаснет (1/с).
@export var rear_bias := 1.1
@export var stability := 1.7
@export var slide_damp := 0.8
## Перенос веса: доля веса на ось на 1 м/с² продольного ускорения; как быстро он следует за
## ускорением (1/с).
@export var weight_shift := 0.022
@export var weight_follow := 7.0
## Руль: угол колёс на малой и на предельной скорости, скорость поворота руля (1/с).
@export var steer_low := 0.5
@export var steer_high := 0.1
@export var steer_rate := 3.2
## Покрытия: сцепление и добавка к качению. Плотная дорога, рыхлый песок, мокрый настил,
## обочина.
@export var surface_grip: Array[float] = [1.0, 0.62, 0.5, 0.74]
@export var surface_drag: Array[float] = [0.0, 0.9, 0.0, 0.8]
## Обочина шире дороги на столько; за ней борт: удар оставляет долю скорости.
@export var verge := 3.5
@export var wall_keep := 0.55
@export var rock_keep := 0.3
@export var car_radius := 1.1
@export var bump_keep := 0.85
## Соперники: доля предела бокового ускорения на повороте и тяги; тормозят с таким замедлением.
@export var rival_skills: Array[float] = [0.85, 0.91, 0.97]
@export var rival_lateral := 7.4
@export var rival_brake := 7.5
@export var grace_seconds := 8.0
@export var max_seconds := 150.0
## Бот: боковое ускорение, под которое он входит в поворот, замедление в расчёте тормозного
## пути, дальность точки прицеливания (м и секунд хода).
@export var bot_lateral := 8.4
@export var bot_brake := 8.6
@export var bot_look := 6.0
@export var bot_look_time := 0.42
## Камера: расстояние, высота, точка взгляда, на сколько шире поле зрения на предельной
## скорости, скорость возврата обзора мышью (1/с).
@export var cam_distance := 7.2
@export var cam_height := 2.6
@export var cam_look := 1.1
@export var cam_fov := 62.0
@export var cam_fov_speed := 14.0
@export var cam_return := 2.5
@export var hit_stop := 0.08
@export var music_db := -12.0
@export var sfx_db := -6.0
@export var engine_db := -14.0


static func load_default() -> RacingThreedTuning:
	var t := load(PATH) as RacingThreedTuning
	return t if t != null else RacingThreedTuning.new()
