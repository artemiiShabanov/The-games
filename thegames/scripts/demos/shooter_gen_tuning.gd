class_name ShooterGenTuning
extends Resource
## Настройки генератора арены и волн шутера × 8-bit, ресурс `res://resources/demos/shooter_gen.tres`.
## Размеры в тайлах 16×16. Арена в один экран: палуба внутри борта, по трапу на каждой
## стороне, пропы (бочки, сундуки, пушки) по сиду; волны врагов тоже по сиду.

const PATH := "res://resources/demos/shooter_gen.tres"

## Арена вместе с бортом, тайлы: 26×13 это ровно экран демки в карточке (416×208).
@export var width := 26
@export var height := 13
## Трап на верхнем и нижнем борту не ближе к углу, столько колонок (углы сверху под HUD);
## на боковых бортах не ближе к углу, столько рядов.
@export var door_margin_cols := 5
@export var door_margin_rows := 3
## Пропы на палубе: штук, отступ от борта, свободный квадрат вокруг старта героя (радиус в
## тайлах по Чебышёву) и свободное место перед трапом в тайлах.
@export var props_min := 4
@export var props_max := 7
@export var prop_wall_gap := 2
@export var clear_center := 3
@export var clear_door := 2
## Волны: столько штук, размер первой и прирост на волну, разброс размера.
@export var waves := 9
@export var wave_first := 3
@export var wave_growth := 0.75
@export var wave_jitter := 1
## Доля канониров в первой и последней волне, между ними линейно.
@export var gunner_share_first := 0.15
@export var gunner_share_last := 0.5
## Врагов во всех волнах не меньше: цель демки плюс запас.
@export var enemies_min_total := 40


static func load_default() -> ShooterGenTuning:
	var t := load(PATH) as ShooterGenTuning
	return t if t != null else ShooterGenTuning.new()
