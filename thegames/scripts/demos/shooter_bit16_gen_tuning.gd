class_name ShooterBit16GenTuning
extends Resource
## Настройки генератора карты шутера × 16/32-bit (#100), ресурс
## `res://resources/demos/shooter_bit16_gen.tres`. Клетки.

const PATH := "res://resources/demos/shooter_bit16_gen.tres"

## Карта: длинная сторона и короткая (сетка залов 3×2 по длинной).
@export var width := 31
@export var height := 21
## Зал не уже этого; шанс слить два соседних в один большой.
@export var room_min := 7
@export var merge_chance := 0.4
## Залов не меньше (после слияния).
@export var rooms_min := 5
## Скелетов в зале: площадь на одного, не меньше и не больше; аптечка в каждом втором зале.
@export var cells_per_foe := 30
@export var foes_min := 1
@export var foes_max := 3
@export var medkit_every := 2
## Колонны в залах не меньше этого по обеим сторонам.
@export var pillar_room := 8


static func load_default() -> ShooterBit16GenTuning:
	var t := load(PATH) as ShooterBit16GenTuning
	return t if t != null else ShooterBit16GenTuning.new()
