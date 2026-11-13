class_name FightingThreedTuning
extends Resource
## Числа демки файтинг × «продвинутые» «один против всех» (#125), ресурс
## `res://resources/demos/fighting_threed.tres`: правила и генератор плана волн. Метры, секунды.

const PATH := "res://resources/demos/fighting_threed.tres"

@export var countdown := 1.5
@export var hero_hp := 100
## Арена: радиус палубы, на которой идёт драка.
@export var arena := 6.2
## Удар героя: с какого расстояния он перелетает к врагу, сколько летит, пауза после удара,
## урон и урон на серии от `strong_combo`.
@export var reach := 7.5
@export var dash := 0.16
@export var after_hit := 0.26
@export var damage := 1
@export var strong_combo := 5
## Сильный удар: сколько держать кнопку, замах после подлёта, на сколько оглушает щитоносца.
@export var heavy_hold := 0.32
@export var heavy_swing := 0.2
@export var shield_stun := 3.2
## Отскок от щита и промах контратаки оставляют героя открытым.
@export var bounce := 0.45
@export var whiff := 0.3
## Контратака: за сколько до удара врага она срабатывает, сколько длится (герой неуязвим).
@export var counter_window := 0.55
@export var counter_seconds := 0.3
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
@export var foe_hp := 6
@export var foe_speed := 2.7
@export var ring := 2.5
@export var ring_far := 3.7
@export var strike_range := 3.1
@export var thug_damage := 8
@export var shield_damage := 10
@export var knife_damage := 14
## Замах врага в первой и в последней волне; после удара или попадания по нему он столько
## стоит; сбитый лежит столько.
@export var windup := Vector2(0.95, 0.62)
@export var foe_recover := 0.7
@export var stagger := 0.6
@export var down_seconds := 1.5
## Атаки: пауза между ними в первой и в последней волне; шанс, что нападут двое с разрывом
## `pair_gap`, в первой и в последней волне.
@export var attack_gap := Vector2(2.1, 1.15)
@export var pair_chance := Vector2(0.0, 0.65)
@export var pair_gap := 0.32
## Следующая волна выходит, когда на ногах осталось не больше стольких врагов.
@export var next_wave_at := 2
@export var max_seconds := 130.0
## Бот: за сколько до удара он жмёт контратаку и уклонение.
@export var bot_counter := 0.3
@export var bot_dodge := 0.28
@export var hit_stop := 0.05
@export var music_db := -11.0
@export var sfx_db := -5.0


static func load_default() -> FightingThreedTuning:
	var t := load(PATH) as FightingThreedTuning
	return t if t != null else FightingThreedTuning.new()
