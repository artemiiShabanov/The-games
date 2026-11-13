class_name SportLowpolyGenTuning
extends Resource
## Настройки генератора плана бросков спорта × low poly (#115), ресурс
## `res://resources/demos/sport_lowpoly_gen.tres`. Метры, секунды, градусы.

const PATH := "res://resources/demos/sport_lowpoly_gen.tres"

## Расстояние до кольца: ближние и дальние точки; с какого расстояния бросок стоит три очка.
@export var near_min := 3.0
@export var near_max := 4.6
@export var far_min := 5.2
@export var far_max := 7.6
@export var three_from := 5.0
## Точка стоит в стороне от оси кольца не дальше стольких градусов.
@export var angle_max := 48.0
## Под каким углом мяч входит в кольцо (от этого считается подъём броска).
@export var entry := 52.0
## Порядок: сколько первых бросков ближние (дальше дальние), сколько в конце с ветром и за
## ними с ездящим кольцом; сколько стрелок ветра бывает.
@export var near_first := 4
@export var wind_shots := 2
@export var moving_shots := 2
@export var wind_max := 3
## Где на шкале середина зелёной зоны на самой ближней и на самой дальней точке.
@export var zone_at_near := 0.3
@export var zone_at_far := 0.8
## Половина зелёной зоны шкалы и период шкалы: на ближней и на дальней точке.
@export var zone_near := 0.1
@export var zone_far := 0.055
@export var meter_near := 1.6
@export var meter_far := 1.1
## Кольцо ездит: размах в стороны и период.
@export var move_amp := 0.9
@export var move_period := 3.8


static func load_default() -> SportLowpolyGenTuning:
	var t := load(PATH) as SportLowpolyGenTuning
	return t if t != null else SportLowpolyGenTuning.new()
