class_name ShooterDemoTuning
extends Resource
## Бой и темп демки шутер × 8-bit, ресурс `res://resources/demos/shooter_bit8.tres`. Пиксели
## виртуального экрана (×4 в карточке), тайл 16, скорости в пикселях в секунду, время в секундах.

const PATH := "res://resources/demos/shooter_bit8.tres"

## Цель: уничтожить столько врагов. Страховка: столько секунд боя, и итог «не отбился».
@export var kills_goal := 30
@export var max_seconds := 120.0
## Отсчёт 3-2-1 перед стартом.
@export var countdown := 1.5
## Герой: скорость, радиус тела, жизни, неуязвимость после удара и отброс от врага.
@export var hero_speed := 72.0
@export var hero_radius := 5.0
@export var hero_hp := 5
@export var hurt_invuln := 1.2
@export var knockback := 10.0
## Ядро героя: скорость, пауза между выстрелами при зажатой A, вылет от центра героя.
@export var ball_speed := 210.0
@export var fire_cooldown := 0.22
@export var muzzle := 7.0
## Попадание: ядро и пуля ближе этого к центру цели (радиус цели плюс радиус снаряда).
@export var hit_radius := 7.0
## Ходок (скелет): скорость, жизни; идёт к герою по палубе в обход пропов.
@export var walker_speed := 36.0
@export var walker_hp := 2
## Канонир: скорость, жизни, держится от героя на расстоянии от `keep_min` до `keep_max`,
## ходит вбок и меняет сторону раз в `strafe_flip` секунд (±40 % по сиду), стреляет медленной
## пулей раз в `fire_every` (±20 %), первый выстрел через `first_shot` после выхода на палубу.
@export var gunner_speed := 28.0
@export var gunner_hp := 1
@export var keep_min := 70.0
@export var keep_max := 120.0
@export var strafe_flip := 2.0
@export var fire_every := 1.8
@export var first_shot := 1.2
@export var shot_speed := 80.0
@export var enemy_radius := 5.0
## Волны: враг выходит из трапа раз в `spawn_gap`; следующая волна, когда на палубе осталось
## не больше `next_wave_alive` врагов или волна идёт дольше `wave_max`, после паузы
## `wave_pause`. На палубе не больше `max_alive` врагов разом.
@export var spawn_gap := 1.0
@export var next_wave_alive := 1
@export var wave_max := 12.0
@export var wave_pause := 3.0
@export var max_alive := 8
## Ром (аптечка): раз в `rum_every` секунд на свободной палубе, если прежний не подобран;
## лечит `rum_heal` жизней.
@export var rum_every := 20.0
@export var rum_heal := 2
## Бот WIN: стреляет, когда враг на одной из 8 линий не дальше `bot_align` px от неё (с
## упреждением); ходок ближе `bot_danger` px гонит его назад; пуля, что пройдёт ближе
## `bot_dodge` px в ближайшие `bot_dodge_time` секунд, уводит вбок; держит дистанцию от цели
## от `bot_range_min` до `bot_range_max`; за ромом идёт, когда жизней меньше `bot_rum_hp`.
@export var bot_align := 4.0
@export var bot_danger := 30.0
@export var bot_dodge := 11.0
@export var bot_dodge_time := 0.6
@export var bot_range_min := 40.0
@export var bot_range_max := 130.0
@export var bot_rum_hp := 4
@export var music_db := -14.0
@export var sfx_db := -8.0


static func load_default() -> ShooterDemoTuning:
	var t := load(PATH) as ShooterDemoTuning
	return t if t != null else ShooterDemoTuning.new()
