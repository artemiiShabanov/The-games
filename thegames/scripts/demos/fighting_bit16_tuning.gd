class_name FightingBit16Tuning
extends Resource
## Правила битемапа × 16/32-bit (#102, графика по Streets of Rage 2), ресурс
## `res://resources/demos/fighting_bit16.tres`. Пиксели мира (экран ×2), секунды; мир шагает
## 60 раз в секунду. Улица: x вдоль, y вглубь (полоса `depth`), z высота полёта при нокдауне.

const PATH := "res://resources/demos/fighting_bit16.tres"

## Экран (ширина одного «экрана» улицы) и глубина полосы, по которой ходят.
@export var screen_w := 832.0
@export var depth := 100.0
## Герой: жизни, здоровье, ход вдоль и вглубь, тяжесть (полёт при нокдауне).
@export var lives := 3
@export var health := 100
@export var walk_x := 140.0
@export var walk_y := 90.0
@export var gravity := 1300.0
## Комбо: окно для следующего удара, длительность и миг попадания удара, урон, дальность.
@export var combo_window := 0.35
@export var jab_seconds := 0.22
@export var jab_hit := 0.08
@export var jab_damage := 6
@export var jab_reach := 56.0
@export var kick_seconds := 0.36
@export var kick_hit := 0.14
@export var kick_damage := 12
@export var kick_reach := 66.0
## Тяжёлый удар на B (плейтест 2026-11-12, вместо прыжка): долгий замах, удар далеко, валит всех
## перед собой; после него долгое восстановление.
@export var heavy_windup := 0.34
@export var heavy_seconds := 0.7
@export var heavy_damage := 18
@export var heavy_reach := 84.0
## Попадание вглубь не дальше этого.
@export var hit_depth := 16.0
## Стоп-кадр при попадании (весь мир замирает) и белая заливка того, по кому попали.
@export var hitstop := 0.07
@export var hitstop_heavy := 0.13
@export var flash := 0.12
## Захват: вплотную столько секунд; колено, бросок, урон брошенным по другим.
@export var grab_touch := 0.2
@export var grab_reach := 30.0
@export var knee_damage := 5
@export var throw_damage := 14
@export var throw_hit_damage := 8
@export var grab_seconds := 1.2
## Удар по бойцу: оглушение, на земле, встаёт (неуязвим), отлёт при нокдауне.
@export var hurt_seconds := 0.3
@export var down_seconds := 0.8
@export var getup_seconds := 0.5
@export var knock_back := 110.0
## После потери жизни: неуязвимость и взрывная волна, сбивающая врагов рядом.
@export var respawn_invuln := 2.0
@export var respawn_blast := 140.0
## Враги: здоровье, ход, урон, замах, дальность удара (головорез, ножовщик, боцман).
@export var thug_health := 30
@export var thug_speed := 75.0
@export var thug_damage := 8
@export var thug_windup := 0.35
@export var knife_health := 22
@export var knife_speed := 108.0
@export var knife_damage := 10
@export var knife_windup := 0.25
@export var boss_health := 120
@export var boss_speed := 68.0
@export var boss_damage := 14
@export var boss_windup := 0.5
## Рывок боцмана через экран: раз в столько секунд, скорость, урон с нокдауном.
@export var boss_charge_every := 4.0
@export var boss_charge_speed := 330.0
@export var boss_charge_damage := 16
## Врагов одновременно в атаке, остальные ждут поодаль; пауза между ударами врага.
@export var attackers := 2
@export var wait_distance := 140.0
@export var foe_cooldown := 1.1
@export var foe_reach := 50.0
## Бот WIN: встаёт у врага на таком расстоянии.
@export var bot_gap := 44.0
@export var max_seconds := 240.0
@export var music_db := -12.0
@export var sfx_db := -6.0


static func load_default() -> FightingBit16Tuning:
	var t := load(PATH) as FightingBit16Tuning
	return t if t != null else FightingBit16Tuning.new()
