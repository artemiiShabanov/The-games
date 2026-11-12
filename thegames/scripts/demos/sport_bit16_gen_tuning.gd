class_name SportBit16GenTuning
extends Resource
## Разброс плана соперника футбола × 16/32-bit (#101) по сиду, ресурс
## `res://resources/demos/sport_bit16_gen.tres`.

const PATH := "res://resources/demos/sport_bit16_gen.tres"

@export var rival_speed_min := 100.0
@export var rival_speed_max := 118.0
@export var shot_range_min := 200.0
@export var shot_range_max := 300.0
@export var charge_min := 0.5
@export var charge_max := 0.8
@export var tackle_min := 0.3
@export var tackle_max := 0.8
@export var react_min := 0.1
@export var react_max := 0.3
@export var keeper_reach_min := 28.0
@export var keeper_reach_max := 40.0
@export var keeper_react_min := 0.12
@export var keeper_react_max := 0.3


static func load_default() -> SportBit16GenTuning:
	var t := load(PATH) as SportBit16GenTuning
	return t if t != null else SportBit16GenTuning.new()
