class_name FightingVectorTuning
extends Resource
## Темп и правила демки файтинг × вектор «дуэль на реакцию» (#94), ресурс
## `res://resources/demos/fighting_vector.tres`. Секунды.

const PATH := "res://resources/demos/fighting_vector.tres"

## Бойцы выходят и замирают; удар; итог раунда на экране.
@export var ready_seconds := 1.2
@export var strike_seconds := 0.55
@export var result_seconds := 1.2
## Баг «чих»: после удара соперника у игрока есть ещё столько секунд, чтобы ударить и победить.
@export var late_window := 0.8
## Бот WIN: реакция на вспышку. Бот LOSE жмёт раньше вспышки, через столько после начала паузы.
@export var bot_reaction := 0.2
@export var bot_lose_press := 0.6
@export var music_db := -14.0
@export var sfx_db := -6.0


static func load_default() -> FightingVectorTuning:
	var t := load(PATH) as FightingVectorTuning
	return t if t != null else FightingVectorTuning.new()
