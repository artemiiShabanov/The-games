class_name PlatformerVectorTuning
extends Resource
## Темп и правила демки платформер × вектор «этажи с дырами» (#90), ресурс
## `res://resources/demos/platformer_vector.tres`. Пиксели логического экрана демки.

const PATH := "res://resources/demos/platformer_vector.tres"

## Жизни: одна за каждое падение в дыру.
@export var lives := 3
@export var run_speed := 280.0
## Подъём на этаж сквозь дыру и падение на этаж в дыру, секунды.
@export var jump_seconds := 0.28
@export var fall_seconds := 0.26
## Удар в потолок: вверх и обратно.
@export var bonk_seconds := 0.3
## Оглушение: после падения в дыру, от потолка, от врага, от потолка с дикой физикой.
@export var stun_seconds := 0.45
@export var bonk_stun := 0.7
@export var enemy_stun := 1.0
@export var wild_stun := 1.1
## Враг не трогает героя после потери жизни столько секунд.
@export var invulnerable_seconds := 1.6
## После оглушения врагом и после падения враг проходит сквозь героя ещё столько секунд.
@export var touch_grace := 0.8
## Прощение: дыра над героем считается шире на столько с каждой стороны, дыра под ногами уже.
@export var jump_margin := 12.0
@export var fall_inset := 24.0
## Расстояния касания по горизонтали: враг, монета, флаг.
@export var hit_distance := 42.0
@export var coin_distance := 40.0
@export var flag_distance := 44.0
## Бот WIN: насколько обходит край дыры своего этажа, с каким запасом встаёт под дыру, с какого
## расстояния уходит от врага там, где оглушение опасно.
@export var bot_hole_margin := 46.0
@export var bot_jump_inset := 28.0
@export var bot_enemy_margin := 150.0
@export var music_db := -12.0
@export var sfx_db := -6.0


static func load_default() -> PlatformerVectorTuning:
	var t := load(PATH) as PlatformerVectorTuning
	return t if t != null else PlatformerVectorTuning.new()
