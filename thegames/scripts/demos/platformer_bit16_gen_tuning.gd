class_name PlatformerBit16GenTuning
extends Resource
## Настройки генератора уровня платформера × 16/32-bit «по клеткам» (#98), ресурс
## `res://resources/demos/platformer_bit16_gen.tres`. Клетки и секунды. Значения с суффиксами
## `_first` и `_last` это начало и конец уровня, между ними ровный переход: к концу ритм чаще.

const PATH := "res://resources/demos/platformer_bit16_gen.tres"

## Длина уровня в клетках; первые `start_flat` и последние `end_flat` ровные.
@export var width := 110
@export var start_flat := 4
@export var end_flat := 5
## Отдых между ловушками, клеток.
@export var rest_min := 2
@export var rest_max := 3
## Веса ловушек: яма, шипы, двое шипов через клетку, якорь, плиты, стражник, яма и шипы.
@export var weight_pit := 2.0
@export var weight_spikes := 2.0
@export var weight_spikes_pair := 1.5
@export var weight_anchor := 2.0
@export var weight_plates := 1.5
@export var weight_guard := 2.0
@export var weight_pit_spikes := 1.0
## Ям в уровне не меньше этого.
@export var pits_min := 2
@export var spike_period_first := 2.2
@export var spike_period_last := 1.6
@export var anchor_period_first := 2.4
@export var anchor_period_last := 1.9
## Плит подряд.
@export var plates_min := 2
@export var plates_max := 3
## Участок стражника, клеток, и его шаг, секунд на клетку.
@export var guard_min := 4
@export var guard_max := 6
@export var guard_step_first := 0.5
@export var guard_step_last := 0.4
## Шанс монеты над ловушкой, которую перепрыгивают, и на клетке отдыха.
@export var coin_trap_chance := 0.8
@export var coin_rest_chance := 0.35


static func load_default() -> PlatformerBit16GenTuning:
	var t := load(PATH) as PlatformerBit16GenTuning
	return t if t != null else PlatformerBit16GenTuning.new()
