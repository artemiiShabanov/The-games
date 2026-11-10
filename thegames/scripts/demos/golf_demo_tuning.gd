class_name GolfDemoTuning
extends Resource
## Физика мяча, удар, темп и боты демки гольф (спорт × 8-bit, #52), ресурс
## `res://resources/demos/sport_bit8.tres`. Пиксели виртуального экрана (×4 в карточке), скорости
## в пикселях в секунду, ускорения в пикселях в секунду за секунду, время в секундах. Физика
## идёт ровным шагом `1 / physics_hz`, так что бот считает траекторию тем же кодом, что и игра.

const PATH := "res://resources/demos/sport_bit8.tres"

## Шаг физики, раз в секунду.
@export var physics_hz := 120
## Мяч (бочонок): радиус, тяжесть, скорость при полной шкале.
@export var ball_radius := 4.0
@export var gravity := 240.0
@export var max_speed := 280.0
## Ветер: ускорение мяча в воздухе на одно деление, вбок.
@export var wind_accel := 12.0
## Отскок от поверхности: доля скорости по нормали (`*_bounce`) и вдоль (`*_keep`); трение
## качения (`*_friction`). Песок вязкий, палуба грина быстрая, корма упругая.
@export var sand_bounce := 0.3
@export var sand_keep := 0.6
@export var sand_friction := 160.0
@export var deck_bounce := 0.45
@export var deck_keep := 0.85
@export var deck_friction := 50.0
@export var hull_bounce := 0.5
@export var hull_keep := 0.7
@export var hull_friction := 80.0
## После отскока скорость по нормали меньше этой: мяч катится. Катится медленнее
## `stop_speed` на склоне, который трение держит: лежит.
@export var roll_threshold := 30.0
@export var stop_speed := 5.0
## Лунка: мяч падает в люк, если над проёмом (полуширина `cup_half`) медленнее
## `cup_capture_roll` качением или `cup_capture_air` с лёта.
@export var cup_half := 5.0
@export var cup_capture_roll := 110.0
@export var cup_capture_air := 160.0
## Мяч летит и катится дольше этого: считается лежащим (страховка).
@export var ball_max_time := 12.0
## Шкала силы: зажатая A гонит шкалу от нуля до полной за `meter_fill` и обратно; отпустил,
## удар с текущей силой. Слабее `min_power`: удара нет и он не засчитан.
@export var meter_fill := 1.0
@export var min_power := 0.03
## Угол целыми градусами: от `angle_min` до `angle_max`, вверх и вниз на `angle_rate` в
## секунду. Новый удар с песка начинается с `angle_start`, с палубы грина с `angle_deck`.
@export var angle_min := 0
@export var angle_max := 80
@export var angle_rate := 40.0
@export var angle_start := 40
@export var angle_deck := 0
## Удары: лимит на лунку `par + max_over_par`, дальше мяч подобран. Штраф за море и аут один
## удар, мяч на прежнее место.
@export var max_over_par := 3
@export var penalty := 1
## Темп: заставка лунки (камера едет от грина к ти), пауза после остановки мяча, пауза после
## моря или аута, пауза после лунки. Страховка всей демки `max_seconds`, итог «не доиграл».
@export var intro_time := 1.6
@export var rest_pause := 0.5
@export var penalty_pause := 1.0
@export var holed_pause := 1.6
@export var max_seconds := 150.0
## Камера: отклик слежения за мячом, 1/с.
@export var cam_follow := 5.0
## Бот WIN перебирает удары симуляцией той же физики: грубо углы через `bot_angle_step` и силы
## через `bot_power_step` делений шкалы (из `meter_fill * physics_hz`), потом точнее вокруг
## лучшего на ±`bot_refine_angle` градусов и ±`bot_refine_power` делений; `bot_sims_per_frame`
## траекторий за кадр. Лучший удар: в лунку, иначе ближе к ней, лёжа не на палубе на
## `bot_off_deck` хуже; море и аут худшие. Думает не меньше `bot_think`, крутит угол не дольше
## `bot_turn_max` (потом бьёт с тем, что вышло).
@export var bot_angle_step := 5
@export var bot_power_step := 6
@export var bot_refine_angle := 3
@export var bot_refine_power := 5
@export var bot_sims_per_frame := 16
@export var bot_off_deck := 30.0
@export var bot_think := 0.5
@export var bot_turn_max := 2.5
## Бот WIN не робот: издалека (до лунки дальше `bot_putt_range`) целит не в люк, а мимо на
## `bot_miss_min`..`bot_miss_max` px в случайную сторону (по сиду), так что подходит к лунке
## и добивает с палубы; ближе целит в люк.
@export var bot_putt_range := 96.0
@export var bot_miss_min := 12.0
@export var bot_miss_max := 36.0
## Бот LOSE: угол и сила слабого удара.
@export var bot_lose_angle := 20
@export var bot_lose_power := 0.15
@export var music_db := -14.0
@export var sfx_db := -8.0


static func load_default() -> GolfDemoTuning:
	var t := load(PATH) as GolfDemoTuning
	return t if t != null else GolfDemoTuning.new()
