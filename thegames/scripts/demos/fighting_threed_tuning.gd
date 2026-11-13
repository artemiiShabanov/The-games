class_name FightingThreedTuning
extends Resource
## Числа демки файтинг × «продвинутые» «один против всех» (#125), ресурс
## `res://resources/demos/fighting_threed.tres`: правила и генератор плана волн. Метры, секунды.

const PATH := "res://resources/demos/fighting_threed.tres"

@export var countdown := 1.5
@export var hero_hp := 100
## Арена: радиус палубы, на которой идёт драка; скорость шага героя.
@export var arena := 6.2
@export var walk_speed := 4.4
## Удар героя: с какого расстояния он перелетает к врагу, сколько летит, пауза после удара,
## урон и урон на серии от `strong_combo`.
@export var reach := 7.5
@export var dash := 0.16
@export var after_hit := 0.3
@export var damage := 1
@export var strong_combo := 5
## Сильный удар: сколько держать кнопку, замах после подлёта, на сколько оглушает щитоносца.
@export var heavy_hold := 0.32
@export var heavy_swing := 0.2
@export var shield_stun := 3.2
## Отскок от щита оставляет героя открытым.
@export var bounce := 0.45
## Контратака: удар по врагу, который замахнулся, за столько секунд до его удара или меньше;
## герой кувырком перелетает ему за спину за `counter_seconds` (неуязвим) и бьёт ногой в спину
## на `counter_damage`.
@export var counter_window := 0.6
@export var counter_seconds := 0.34
@export var counter_damage := 2
## Цепочка ударов: с какого расстояния до врага каждый достаёт (левой, правой, ногой, с
## разворота, снизу).
@export var contact: Array[float] = [0.78, 0.78, 1.02, 1.08, 0.72]
## Удар отталкивает врага на столько.
@export var knock := 0.35
## Уклонение: длина переката, сколько длится и сколько из этого герой неуязвим.
@export var dodge_length := 3.2
@export var dodge_seconds := 0.38
@export var dodge_safe := 0.32
## Серия: через сколько секунд без попадания она сгорает, каждые сколько ударов добивание.
@export var combo_seconds := 2.6
@export var special_every := 10
## После пропущенного удара герой столько не действует.
@export var stun := 0.35
## Враги: здоровье, скорость, на каком расстоянии стоят в кругу и с какого бьют, урон.
@export var foe_hp := 12
@export var foe_speed := 2.7
@export var ring := 2.5
@export var ring_far := 3.7
@export var strike_range := 3.1
@export var thug_damage := 8
@export var shield_damage := 10
@export var knife_damage := 14
## Замах врага в первой и в последней волне; после удара или попадания по нему он столько
## стоит; сбитый лежит столько.
@export var windup := Vector2(1.0, 0.75)
@export var foe_recover := 0.7
@export var stagger := 0.6
@export var down_seconds := 1.5
## Атаки: пауза между ними в первой и в последней волне; шанс, что нападут двое с разрывом
## `pair_gap`, в первой и в последней волне.
@export var attack_gap := Vector2(2.5, 1.7)
@export var pair_chance := Vector2(0.0, 0.35)
@export var pair_gap := 0.32
## Следующая волна выходит, когда на ногах осталось не больше стольких врагов.
@export var next_wave_at := 1
@export var max_seconds := 130.0
## Бот: за сколько до удара он жмёт контратаку и уклонение.
@export var bot_counter := 0.3
@export var bot_dodge := 0.28
@export var hit_stop := 0.065
## После стоп-кадра мир столько секунд идёт быстрее во столько раз.
@export var rush_seconds := 0.14
@export var rush := 1.7
@export var music_db := -11.0
@export var sfx_db := -5.0


static func load_default() -> FightingThreedTuning:
	var t := load(PATH) as FightingThreedTuning
	return t if t != null else FightingThreedTuning.new()
