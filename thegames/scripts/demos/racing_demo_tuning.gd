class_name RacingDemoTuning
extends Resource
## Физика и темп демки гонки × 8-bit, ресурс `res://resources/demos/racing_bit8.tres`. Пиксели
## виртуального экрана (×4 в карточке), тайл 16, скорости в пикселях в секунду, углы в радианах.

const PATH := "res://resources/demos/racing_bit8.tres"

## Шлюпка игрока: предельная скорость, разгон на A, торможение на B, задний ход, выбег.
@export var max_speed := 125.0
@export var accel := 110.0
@export var brake := 220.0
@export var reverse_speed := 40.0
@export var coast_drag := 45.0
## Поворот: рад/с на полной управляемости; управляемость растёт со скоростью до `turn_full_speed`.
@export var turn_rate := 3.2
@export var turn_full_speed := 40.0
## Сцепление: как быстро скорость догоняет курс (дикая физика делит его, выходит лёд).
@export var grip := 12.0
## Отмель: доля предельной скорости и сброс лишней скорости в секунду.
@export var side_speed_mult := 0.45
@export var side_drag := 180.0
## Берег и препятствия: отскок скорости по оси удара и доля скорости после удара.
@export var wall_bounce := 0.35
@export var wall_speed_keep := 0.5
@export var car_radius := 5.0
## Соперники: предельная скорость как доля игрока, разброс по сиду; смотрят вперёд на столько
## точек средней линии плюс по точке на `bot_look_speed` пикселей в секунду.
@export var bot_speed_min := 0.8
@export var bot_speed_max := 0.9
@export var bot_lookahead := 4
@export var bot_look_speed := 40.0
## Перед поворотом соперник сбрасывает скорость до этой доли на развороте в 90°, окно в точках.
@export var bot_corner_slow := 0.55
@export var bot_brake_window := 14
## Ряды соперников по бокам от средней линии и сдвиг, которым объезжают препятствия.
@export var bot_lane := 14.0
@export var avoid_offset := 22.0
## Бот автотеста за игрока: LOSE держит такую долю газа.
@export var lose_throttle := 0.4
## Застрял (скорость ниже порога столько секунд): задний ход; ещё дольше: на среднюю линию.
@export var stuck_speed := 8.0
@export var stuck_seconds := 1.2
@export var reverse_seconds := 0.7
@export var respawn_seconds := 3.5
## Отсчёт 3-2-1 перед стартом.
@export var countdown := 1.5
## Страховка: столько секунд гонки, и итог «не добрался».
@export var max_seconds := 90.0
## Решётка старта: ряды за линией финиша в точках средней линии, шаг рядов.
@export var grid_back := 3
@export var grid_row_gap := 3
## Чих (`sneeze_enemies`): соперник от касания крутится волчком столько секунд.
@export var spin_seconds := 1.0
@export var spin_rate := 14.0
## Залипание газа (`sticky_input`): отпущенный газ сам включается рывком такой длины.
@export var stick_burst := 0.35
@export var stick_gap := 0.2
## Камера смотрит вперёд по скорости на столько секунд.
@export var camera_lead := 0.35
## Пена за кормой: раз в столько секунд на скорости выше `wake_speed`.
@export var wake_every := 0.06
@export var wake_speed := 30.0
@export var music_db := -14.0
@export var sfx_db := -6.0


static func load_default() -> RacingDemoTuning:
	var t := load(PATH) as RacingDemoTuning
	return t if t != null else RacingDemoTuning.new()
