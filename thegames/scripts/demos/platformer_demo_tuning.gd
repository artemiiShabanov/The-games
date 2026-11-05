class_name PlatformerDemoTuning
extends Resource
## Физика и темп демки платформер × 8-bit, ресурс `res://resources/demos/platformer_bit8.tres`.
## Пиксели виртуального экрана 480×270, тайл 16. Прыжок должен покрывать `jump_dx` колонок и
## `jump_dy` рядов из тюнинга генератора: дальность = run_speed × jump_time.

const PATH := "res://resources/demos/platformer_bit8.tres"

@export var run_speed := 96.0
@export var jump_height := 72.0
@export var jump_time := 0.95
## Отпустил A в подъёме: вертикальная скорость умножается.
@export var jump_cut := 0.4
@export var enemy_speed := 28.0
@export var stomp_bounce := 120.0
@export var invulnerable_seconds := 1.2
@export var run_fps := 10.0
@export var enemy_fps := 4.0
@export var hero_width := 12.0
@export var hero_height := 15.0


static func load_default() -> PlatformerDemoTuning:
	var t := load(PATH) as PlatformerDemoTuning
	return t if t != null else PlatformerDemoTuning.new()
