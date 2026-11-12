class_name ShooterBit16Tuning
extends Resource
## Правила и тюнинг шутера × 16/32-bit «до выхода» (#100), ресурс
## `res://resources/demos/shooter_bit16.tres`. Клетки, секунды, радианы; мир шагает 60 раз в
## секунду.

const PATH := "res://resources/demos/shooter_bit16.tres"

## Герой: здоровье, ход, стрейф, поворот, радиус тела.
@export var health := 100
@export var move_speed := 3.2
@export var strafe_speed := 2.8
@export var turn_speed := 2.6
@export var radius := 0.25
## Выстрел: перезарядка, скорость пули героя, радиус попадания по скелету.
@export var fire_cooldown := 0.45
@export var bullet_speed := 14.0
@export var foe_radius := 0.35
## Аптечка: сколько здоровья.
@export var medkit := 30
## Скелет: здоровье в попаданиях, ход, дальность зрения, держит дистанцию, перезарядка
## выстрела, задержка первого выстрела после того, как заметил.
@export var foe_health := 2
@export var foe_speed := 1.3
@export var foe_sight := 9.0
@export var foe_keep := 2.5
@export var foe_cooldown := 1.9
@export var foe_first_shot := 0.9
## Скелет с саблей: ход быстрее, достаёт на этом расстоянии, удар раз в столько секунд, урон.
@export var melee_speed := 2.1
@export var melee_reach := 0.9
@export var melee_cooldown := 0.9
@export var melee_damage := 12
## Пуля скелета: скорость в клетках в секунду, урон.
@export var shot_speed := 4.5
@export var shot_damage := 14
## Бот WIN: стреляет в врагов ближе этого, уклоняется от пуль ближе этого.
@export var bot_engage := 5.0
## Сабельника бот бьёт раньше: тот бежит быстрее и бьёт вблизи.
@export var bot_engage_melee := 7.5
## Бой без попаданий дольше этого бот бросает на вдвое большее время.
@export var bot_give_up := 2.5
@export var bot_dodge := 2.2
@export var max_seconds := 180.0
@export var music_db := -12.0
@export var sfx_db := -6.0


static func load_default() -> ShooterBit16Tuning:
	var t := load(PATH) as ShooterBit16Tuning
	return t if t != null else ShooterBit16Tuning.new()
