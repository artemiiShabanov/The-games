class_name ShooterThreedTuning
extends Resource
## Числа правил демки шутер × «продвинутые» «оборона аванпоста» (#123), ресурс
## `res://resources/demos/shooter_threed.tres`. Метры, секунды, радианы.

const PATH := "res://resources/demos/shooter_threed.tres"

@export var countdown := 1.5
## Вышка: высота настила, его радиус, высота глаз героя, скорость шага, как близко к краю
## можно подойти.
@export var deck_height := 3.0
@export var deck_radius := 3.4
@export var eye := 1.6
@export var walk_speed := 4.2
@export var deck_margin := 0.35
@export var health := 100
## Револьвер: барабан, запас при себе и его предел, перезарядка, пауза между выстрелами.
@export var clip := 6
@export var reserve := 18
@export var reserve_max := 24
@export var reload_seconds := 1.25
@export var fire_gap := 0.2
## Ящик с патронами: как близко подойти и сколько секунд он пополняет запас.
@export var crate_reach := 1.3
@export var crate_seconds := 0.7
## Где враги встают и начинают бить: расстояние от вышки (от и до).
@export var ring_min := 7.4
@export var ring_max := 9.2
## Бегун: скорость, здоровье, пауза между бросками ножа и урон.
@export var runner_speed := 5.6
@export var runner_hp := 1
@export var runner_gap := 1.7
@export var runner_damage := 5
## Щитоносец: скорость, здоровье, пауза и замах (щит открыт), урон.
@export var shield_speed := 2.7
@export var shield_hp := 3
@export var shield_gap := 2.6
@export var shield_windup := 0.8
@export var shield_damage := 9
## Метатель: встаёт на этом расстоянии, пауза между бутылками, полёт, урон и радиус разлёта.
@export var thrower_speed := 3.6
@export var thrower_hp := 2
@export var thrower_range := 21.0
@export var thrower_gap := 3.0
@export var bottle_seconds := 1.9
@export var bottle_damage := 12
@export var bottle_blast := 1.9
@export var bottle_radius := 0.55
## Великан: скорость, здоровье, пауза и замах (голова уязвима), урон; урон по нему: в тело, в
## голову и в голову на замахе.
@export var brute_speed := 2.1
@export var brute_hp := 16
@export var brute_gap := 3.2
@export var brute_windup := 1.1
@export var brute_damage := 18
@export var brute_head := 2
@export var brute_weak := 5
## Бочка с порохом: радиус взрыва и урон.
@export var keg_blast := 5.5
@export var keg_damage := 5
## Тела для попадания: радиус и высота середины тела и головы обычного врага; великан во
## столько раз крупнее.
@export var body_radius := 0.55
@export var body_height := 0.95
@export var head_radius := 0.33
@export var head_height := 1.66
@export var brute_scale := 1.7
## Следующая волна выходит через столько секунд после того, как эта перебита, или через
## столько после её последнего врага, даже если он ещё жив.
@export var wave_lull := 1.0
@export var wave_overlap := 4.0
@export var max_seconds := 150.0
## Бот: скорость поворота прицела (рад/с), пауза между выстрелами, запас точности (доля
## радиуса цели).
@export var bot_turn := 2.8
@export var bot_gap := 0.5
## Дальше этого бот не стреляет.
@export var bot_range := 27.0
@export var bot_tight := 0.55
@export var fov := 60.0
@export var hit_stop := 0.05
@export var music_db := -11.0
@export var sfx_db := -5.0


static func load_default() -> ShooterThreedTuning:
	var t := load(PATH) as ShooterThreedTuning
	return t if t != null else ShooterThreedTuning.new()
