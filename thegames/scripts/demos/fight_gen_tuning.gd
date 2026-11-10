class_name FightGenTuning
extends Resource
## Настройки генератора плана соперника файтинга × 8-bit (#54), ресурс
## `res://resources/demos/fighting_gen.tres`: профили поведения, из которых сид собирает
## раунд фазами, паттерны ударов, реакция, пропы фона.

const PATH := "res://resources/demos/fighting_gen.tres"

## Профили соперника: напор, стена, подсечка, контра.
@export var profiles: Array[FightProfile] = []
## Фазы раунда: длина каждой, секунд; разных профилей за раунд не меньше.
@export var phase_min := 8.0
@export var phase_max := 16.0
@export var distinct_min := 3
## Паттерн ударов фазы: столько знаков, H верхний, L нижний; соперник бьёт по кругу.
@export var pattern_min := 2
@export var pattern_max := 4
## Реакция соперника на удары героя, шагов, и шанс не ответить совсем.
@export var reaction_min := 12
@export var reaction_max := 20
@export var miss_min := 0.25
@export var miss_max := 0.45
## Мачта со смещением от середины арены, px; пропы фона у бортов (пушка, сундук) от борта.
@export var mast_shift := 40.0
@export var prop_from_rail := 12.0
@export var prop_spread := 40.0


static func load_default() -> FightGenTuning:
	var t := load(PATH) as FightGenTuning
	return t if t != null else FightGenTuning.new()
