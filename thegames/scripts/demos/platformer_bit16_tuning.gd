class_name PlatformerBit16Tuning
extends Resource
## Темп и правила демки платформер × 16/32-bit «по клеткам» (#98), ресурс
## `res://resources/demos/platformer_bit16.tres`. Секунды и клетки.

const PATH := "res://resources/demos/platformer_bit16.tres"

## Жизни: одна за яму, шипы, якорь и стражника.
@export var lives := 3
## Шаг на клетку и прыжок через одну клетку: 12 и 24 кадра при 60 в секунду.
@export var step_seconds := 0.2
@export var jump_seconds := 0.4
## Нажатый заранее прыжок ждёт конца шага столько секунд.
@export var jump_buffer := 0.25
@export var fall_seconds := 0.45
@export var hurt_seconds := 0.7
@export var invulnerable_seconds := 1.2
## Шипы: доля периода, когда они торчат, и доля перед этим, когда показываются кончики.
@export var spike_up := 0.45
@export var spike_warn := 0.12
## Якорь: доля периода, когда он внизу (падает и лежит), и доля перед этим, когда он дрожит.
@export var anchor_down := 0.3
@export var anchor_warn := 0.15
## Плита осыпается через столько после первого шага на неё.
@export var plate_seconds := 0.6
## Стражник стоит на краю участка столько, прежде чем повернуть.
@export var guard_pause := 0.5
## Бот WIN: запас по времени вокруг ловушек, горизонт плана в шагах героя и сколько секунд он
## ждёт без плана, прежде чем пойти наудачу.
@export var bot_margin := 0.09
@export var bot_horizon := 50
@export var bot_patience := 4.0
@export var music_db := -12.0
@export var sfx_db := -6.0


static func load_default() -> PlatformerBit16Tuning:
	var t := load(PATH) as PlatformerBit16Tuning
	return t if t != null else PlatformerBit16Tuning.new()
