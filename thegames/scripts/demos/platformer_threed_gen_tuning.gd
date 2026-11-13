class_name PlatformerThreedGenTuning
extends Resource
## Настройки генератора уровня платформера × «продвинутые» (#121), ресурс
## `res://resources/demos/platformer_threed_gen.tres`. Метры, секунды, градусы.

const PATH := "res://resources/demos/platformer_threed_gen.tres"

## Пропастей на уровне (островков на один больше).
@export var gaps := 15
## Островок: радиус обычного и маленького (бочка, верхушка мачты); с какой пропасти бывают
## маленькие и их доля.
@export var islet := 2.6
@export var islet_small := 1.1
@export var small_from := 9
@export var small_share := 0.5
## Кольцо: высота над островком от и до, шаг между кольцами цепочки от и до, отступ первого
## кольца от края островка.
@export var ring_height_min := 4.6
@export var ring_height_max := 5.8
@export var ring_step_min := 6.4
@export var ring_step_max := 7.8
@export var ring_lead := 3.4
## Перепад высоты соседних островков и колец цепочки: с какой пропасти и до скольких метров.
@export var height_from := 4
@export var islet_rise := 1.6
@export var ring_rise := 1.4
## Цепочки: с какой пропасти два кольца, с какой три.
@export var double_from := 2
@export var triple_from := 8
## Движущиеся кольца: с какой пропасти, доля, размах вверх-вниз, период.
@export var moving_from := 9
@export var moving_share := 0.5
@export var moving_amp := 1.1
@export var moving_period := 2.6
## Поворот пути на островке, градусы, и предел ухода от начального курса.
@export var turn_min := 12.0
@export var turn_max := 38.0
@export var heading_limit := 70.0


static func load_default() -> PlatformerThreedGenTuning:
	var t := load(PATH) as PlatformerThreedGenTuning
	return t if t != null else PlatformerThreedGenTuning.new()
