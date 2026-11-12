class_name SportBit16Tuning
extends Resource
## Физика и правила футбола × 16/32-bit (#101, два на два с вратарями), ресурс
## `res://resources/demos/sport_bit16.tres`. Пиксели мира, секунды; мир шагает 60 раз в секунду.
## Поле лежит горизонтально: ворота героя слева, соперника справа.

const PATH := "res://resources/demos/sport_bit16.tres"

## Поле, ворота (ширина створа, высота перекладины), штрафная.
@export var pitch_w := 960.0
@export var pitch_h := 560.0
@export var goal_w := 104.0
@export var goal_h := 26.0
@export var box_w := 150.0
@export var box_h := 300.0
## Матч до стольких голов; страховка по времени.
@export var goals_to_win := 3
@export var max_seconds := 300.0
## Игрок: бег, радиус, подкат (скорость, длительность, перезарядка), лежит после подката по нему.
@export var run_speed := 120.0
## С мячом у ноги бег медленнее, доля от обычного (плейтест 2026-11-12).
@export var dribble_speed := 0.8
@export var radius := 6.0
@export var slide_speed := 230.0
@export var slide_seconds := 0.35
@export var slide_cooldown := 0.8
@export var down_seconds := 0.7
## Как часто защитник рядом с владельцем мяча идёт в подкат: доля из плана × это в секунду.
@export var tackle_rate := 1.5
## Мяч: тяжесть, отскок, трение по траве, ведение (на сколько впереди ног, с какой скорости мяч
## уже не берётся, а отскакивает).
@export var gravity := 600.0
@export var bounce := 0.5
@export var friction := 170.0
@export var dribble_ahead := 8.0
@export var control_speed := 260.0
## Удар: зарядка до `charge_max`; скорость и подъём по доле зарядки; подкрутка после удара.
@export var charge_max := 0.7
@export var kick_min := 220.0
@export var kick_max := 520.0
@export var loft_lin := 60.0
@export var loft_sq := 150.0
@export var aftertouch_seconds := 0.35
@export var aftertouch := 260.0
## Вратарь: ход, бросок в прыжке, дальность прыжка, держит мяч перед выбросом.
@export var keeper_speed := 60.0
@export var dive_speed := 170.0
@export var dive_seconds := 0.35
@export var keeper_hold := 0.8
## Прыгает, если мяч долетит до линии ворот быстрее этого (одинаково для обоих вратарей).
@export var dive_window := 1.0
## Ошибка вратаря в угадывании места удара, пиксели в обе стороны.
@export var keeper_error := 52.0
## У вратаря героя ошибка меньше: против живого игрока соперник забивал всё (плейтест).
@export var hero_keeper_error := 26.0
## В прыжке ловит мяч ближе этого.
@export var dive_catch := 10.0
## После гола: пауза перед розыгрышем с центра.
@export var goal_pause := 1.4
## Бот WIN: бьёт с такого расстояния до ворот, с такой зарядкой.
@export var bot_shot_range := 300.0
@export var bot_charge := 0.55
## Пас: короткое нажатие, доля зарядки.
@export var pass_charge := 0.25
@export var bot_tackle := 1.4
@export var music_db := -12.0
@export var sfx_db := -6.0


static func load_default() -> SportBit16Tuning:
	var t := load(PATH) as SportBit16Tuning
	return t if t != null else SportBit16Tuning.new()
