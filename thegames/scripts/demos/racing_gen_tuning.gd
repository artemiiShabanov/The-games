class_name RacingGenTuning
extends Resource
## Настройки генератора трассы гонок, ресурс `res://resources/demos/racing_gen.tres`. Размеры
## в тайлах 16×16, кроме отмеченных пикселей. Трасса: замкнутый сплайн через опорные точки
## вокруг центра карты, растеризованный в воду (трасса), отмель (обочина) и берег (стена).

const PATH := "res://resources/demos/racing_gen.tres"

## Карта в тайлах.
@export var width := 108
@export var height := 70
## Опорные точки петли: столько штук по кругу, радиус по эллипсу карты с разбросом.
@export var points_min := 10
@export var points_max := 13
## Радиус точки как доля полуосей эллипса (полуоси = половина карты минус поля).
@export var radius_min := 0.5
@export var radius_max := 1.0
## Разброс угла точки внутри её сектора, доля сектора.
@export var angle_jitter := 0.3
## Поля от края карты до кромки берега, тайлы.
@export var margin := 2
## Полуширина воды трассы и ширина отмели за ней, тайлы.
@export var road_half := 3.5
@export var side_width := 1.5
## Петля не короче, пиксели (плейтест 2026-11-09: круг в полтора раза длиннее, ~30 с).
@export var min_length_px := 2900.0
## Шаг точек средней линии в пикселях.
@export var sample_step := 8.0
## Проверка ширины: свободной от препятствий воды поперёк трассы не меньше, тайлы.
@export var min_free_width := 4.0
## Между разными участками петли хотя бы столько тайлов берега: срезать нельзя.
@export var min_wall_between := 1.0
## Самый крутой поворот: смена курса на отрезке `turn_window` точек не больше, градусы.
@export var max_turn_deg := 80.0
@export var turn_window := 6
## Старт на почти горизонтальном участке внизу петли: |cos| курса не меньше.
@export var start_straightness := 0.92
## Препятствия на воде (бочки и рифы): штук и отступ от старта в точках средней линии.
@export var obstacles_min := 5
@export var obstacles_max := 8
@export var obstacle_clear_start := 30
## Боковой сдвиг препятствия от средней линии, пиксели; средняя линия остаётся свободной.
@export var obstacle_offset_min := 22.0
@export var obstacle_offset_max := 30.0
@export var obstacle_radius := 6.0
## Буи на кромке воды через столько точек средней линии.
@export var buoy_every := 6


static func load_default() -> RacingGenTuning:
	var t := load(PATH) as RacingGenTuning
	return t if t != null else RacingGenTuning.new()
