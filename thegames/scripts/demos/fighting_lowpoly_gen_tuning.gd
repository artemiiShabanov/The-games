class_name FightingLowpolyGenTuning
extends Resource
## Настройки генератора плана соперника файтинга × low poly (#116), ресурс
## `res://resources/demos/fighting_lowpoly_gen.tres`. Секунды и доли.

const PATH := "res://resources/demos/fighting_lowpoly_gen.tres"

## Связок в плане (после последней план идёт по кругу с самых трудных).
@export var combos := 30
## Первые связки одиночные; с какой связки бывают двойные, тройные и сильный удар.
@export var double_from := 2
@export var triple_from := 6
@export var heavy_from := 4
## Доля связок с сильным ударом после `heavy_from` и доля ударов ногой.
@export var heavy_share := 0.4
@export var kick_share := 0.45
## Пауза перед связкой и замах обычного удара: в начале боя и к концу плана.
@export var gap_first := 1.5
@export var gap_last := 0.75
@export var windup_first := 0.52
@export var windup_last := 0.36
## Замах сильного удара.
@export var heavy_windup := 0.85
## Как часто соперник успевает закрыться от удара героя: от руки и от ноги.
@export var guard_punch := 0.62
@export var guard_kick := 0.45
## Сколько бросков жребия блока заготовлено.
@export var guard_rolls := 160


static func load_default() -> FightingLowpolyGenTuning:
	var t := load(PATH) as FightingLowpolyGenTuning
	return t if t != null else FightingLowpolyGenTuning.new()
