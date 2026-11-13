class_name SportThreedTuning
extends Resource
## Числа демки спорт × «продвинутые» «спуск по дюне» (#124), ресурс
## `res://resources/demos/sport_threed.tres`: правила и генератор склона. Метры, секунды,
## радианы.

const PATH := "res://resources/demos/sport_threed.tres"

@export var countdown := 1.5
## Доля ворот, которую надо пройти к финишу.
@export var goal_share := 0.66
## Скольжение: трение, сопротивление воздуха стоя и в приседе (на квадрат скорости), стартовая
## скорость.
@export var friction := 0.45
@export var drag := 0.0021
@export var drag_crouch := 0.0013
@export var start_speed := 14.0
## Кант: как быстро доска ложится на кант (1/с, на скорости медленнее: делится на 1 + v/`edge_speed`),
## скорость поворота курса на полном канте (рад/с на малой скорости, делится на 1 + v/`turn_speed`),
## доля поворота в приседе, предел курса от линии склона.
@export var edge_rate := 5.5
@export var edge_speed := 36.0
@export var turn_rate := 2.4
@export var turn_speed := 44.0
@export var crouch_turn := 0.55
@export var heading_max := 1.05
## Дуга гасит скорость: замедление на полном канте на скорости 20 м/с.
@export var carve_scrub := 1.3
## Срыв канта копится (плейтест 2026-11-13: его должно быть видно заранее): на скорости выше
## `catch_speed` натяг растёт, пока руль дальше `strain_slack` от канта (на `strain_rate` за
## единицу лишнего в секунду) и пока доска лежит на полном канте (`strain_hold` в секунду),
## иначе спадает на `strain_decay`. Полный натяг это срыв: остаётся доля скорости, руля нет
## `catch_seconds`.
@export var catch_speed := 24.0
@export var strain_slack := 0.6
@export var strain_rate := 3.6
@export var strain_hold := 0.35
@export var strain_decay := 1.3
@export var catch_keep := 0.72
@export var catch_seconds := 0.6
## Прыжок заряжается, пока держат кнопку: до `charge_seconds`, полный заряд втрое выше.
## Прыжок без заряда, тяжесть, руление курсом в воздухе (рад/с).
@export var charge_seconds := 0.7
@export var hop := 4.2
@export var gravity := 16.0
@export var air_turn := 1.3
## Трамплин: длина и высота клина, подброс на скорости `ramp_ref` и добавка за полный заряд
## прыжка на кромке (доля).
@export var ramp_length := 9.0
@export var ramp_height := 1.7
@export var ramp_lift := 9.5
@export var ramp_ref := 32.0
@export var ramp_pop := 0.35
## Приземление: курс дальше этого от линии склона это падение.
@export var land_angle := 0.6
## Барьеры поперёк пути: сколько, половина ширины от и до, высота (ниже неё над барьером не
## пролететь).
@export var bars := 7
@export var bar_half := Vector2(4.5, 6.5)
@export var bar_height := 1.3
## Падение: сколько секунд лежит и с какой скоростью встаёт.
@export var fall_seconds := 1.15
@export var fall_speed := 4.0
## Края склона: половина ширины, за ней песок тормозит.
@export var half_width := 15.0
@export var edge_drag := 6.0
@export var body := 0.55
@export var max_seconds := 140.0
## Склон: длина, шаг точек, уклон от и до (градусы), длина волн уклона, изгибы линии склона.
@export var length := 1900.0
@export var step := 4.0
@export var pitch_min := 16.0
@export var pitch_max := 25.0
@export var pitch_wave := 340.0
@export var sway := 9.0
@export var sway_wave := 520.0
## Ворота: первые на этом расстоянии, шаг и половина ширины в начале и в конце, вынос вбок в
## начале и в конце.
@export var gate_first := 120.0
@export var gate_step := Vector2(96.0, 68.0)
@export var gate_half := Vector2(4.6, 2.7)
@export var gate_off := Vector2(3.5, 11.5)
## Трамплины: сколько, ширина; препятствия: сколько в начале и в конце на сотню метров.
@export var ramps := 4
@export var ramp_width := 5.0
@export var rocks_per_100 := Vector2(0.9, 3.0)
## Бот: дальность точки прицеливания по времени и как сильно он рулит на ошибку курса.
@export var bot_look := 1.1
@export var bot_gain := 3.2
@export var cam_distance := 7.6
@export var cam_height := 3.0
@export var cam_fov := 64.0
@export var hit_stop := 0.07
@export var music_db := -11.0
@export var sfx_db := -6.0


static func load_default() -> SportThreedTuning:
	var t := load(PATH) as SportThreedTuning
	return t if t != null else SportThreedTuning.new()
