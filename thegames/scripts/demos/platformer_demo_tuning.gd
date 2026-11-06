class_name PlatformerDemoTuning
extends Resource
## Физика и темп демки платформер × 8-bit, ресурс `res://resources/demos/platformer_bit8.tres`.
## Пиксели виртуального экрана (416×208 при ×4 в карточке), тайл 16. Прыжок должен покрывать `jump_dx` колонок и
## `jump_dy` рядов из тюнинга генератора: дальность = run_speed × jump_time.

const PATH := "res://resources/demos/platformer_bit8.tres"

## Жизни вместо таймера: вторая смерть кончает демку.
@export var lives := 2
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
## Попугай: скорость относительно ходока и частота взмахов.
@export var flyer_speed_mult := 1.3
@export var flyer_fps := 8.0
@export var hero_width := 12.0
@export var hero_height := 15.0
## Дэш на B (плейтест 2026-11-06): рывок по горизонтали без гравитации, в воздухе один раз.
@export var dash_speed := 300.0
@export var dash_time := 0.15
@export var dash_cooldown := 0.4
## Громкость музыки и звуков демки в дБ (плейтест 2026-11-06: вдвое тише, чем было).
@export var music_db := -14.0
@export var sfx_db := -6.0
## Вертикальная камера: мёртвая зона от верха и низа экрана в пикселях.
@export var cam_top_margin := 64.0
@export var cam_bottom_margin := 40.0


static func load_default() -> PlatformerDemoTuning:
	var t := load(PATH) as PlatformerDemoTuning
	return t if t != null else PlatformerDemoTuning.new()
