class_name FightingVectorGenTuning
extends Resource
## Настройки генератора дуэли на реакцию (файтинг × вектор, #94), ресурс
## `res://resources/demos/fighting_vector_gen.tres`. Секунды.

const PATH := "res://resources/demos/fighting_vector_gen.tres"

@export var rounds := 5
## Пауза до вспышки.
@export var wait_min := 1.4
@export var wait_max := 3.6
## Задержка реакции соперника в первом и в последнем раунде, между ними ровный переход;
## разброс в секундах.
@export var delay_first := 0.62
@export var delay_last := 0.3
@export var delay_jitter := 0.03


static func load_default() -> FightingVectorGenTuning:
	var t := load(PATH) as FightingVectorGenTuning
	return t if t != null else FightingVectorGenTuning.new()
