class_name SportVectorTuning
extends Resource
## Темп и правила демки спорт × вектор «понг» (#93), ресурс
## `res://resources/demos/sport_vector.tres`. Пиксели логического экрана демки, секунды.

const PATH := "res://resources/demos/sport_vector.tres"

## До скольких очков идёт матч.
@export var points_to_win := 5
## Поле: стенки сверху и снизу на таком отступе от края экрана, ракетки на таком от боковых.
@export var wall_inset := 24.0
@export var paddle_inset := 72.0
@export var paddle_height := 132.0
@export var paddle_width := 16.0
@export var paddle_speed := 640.0
@export var ball_radius := 12.0
## Скорость мяча на подаче, прибавка за каждый удар ракеткой в долях и потолок.
@export var ball_speed := 820.0
@export var ball_gain := 0.1
@export var ball_speed_cap := 1400.0
## Наибольший угол отскока от ракетки, градусы: у самого края ракетки.
@export var max_angle := 55.0
## Пауза перед подачей.
@export var serve_delay := 0.9
## Соперник без мяча возвращается к середине с этой долей своей скорости.
@export var ai_idle := 0.5
## Усталость соперника: на столько растёт его ошибка с каждым его ударом в розыгрыше, в долях.
@export var ai_tire := 0.18
## Бот WIN: какой долей половины ракетки бьёт, чтобы увести мяч от соперника.
@export var bot_edge := 0.75
@export var music_db := -12.0
@export var sfx_db := -6.0


static func load_default() -> SportVectorTuning:
	var t := load(PATH) as SportVectorTuning
	return t if t != null else SportVectorTuning.new()
