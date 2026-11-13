class_name FightingThreedTuning
extends Resource
## Числа демки файтинг × «продвинутые» «дуэль на саблях» (#125), ресурс
## `res://resources/demos/fighting_threed.tres`: правила и генератор плана соперника. Секунды.

const PATH := "res://resources/demos/fighting_threed.tres"

@export var countdown := 1.5
@export var hero_hp := 100
@export var rival_hp := 150
## Удар героя: замах, после него герой открыт (дольше, если удар отбит), урон.
@export var swing := 0.28
@export var recover := 0.3
@export var recover_blocked := 0.55
@export var damage := 9
## Шаг назад: сколько секунд герой вне досягаемости и сколько потом возвращается с опущенной
## саблей.
@export var step_seconds := 0.42
@export var step_return := 0.38
## После пропущенного удара герой столько секунд не действует.
@export var stun := 0.3
## Соперник: урон удара и выпада, пауза между ударами связки, сколько он открыт после связки и
## сколько после удара героя в цель.
@export var rival_damage := 12
@export var lunge_damage := 22
@export var combo_gap := 0.22
@export var open_seconds := 0.7
@export var flinch := 0.25
## Замах соперника в начале и в конце плана, замах выпада; финт меняет сторону на этой доле
## замаха.
@export var windup := Vector2(0.8, 0.46)
@export var lunge_windup := 0.95
@export var feint_at := 0.55
## Пауза перед связкой в начале и в конце; как часто соперник меняет стойку в паузе; шанс, что
## он успеет закрыться от удара героя.
@export var pause := Vector2(1.3, 0.7)
@export var guard_hold := Vector2(1.7, 0.8)
@export var react := Vector2(0.25, 0.62)
## План: сколько ходов, с какого хода связки из двух и трёх, финты и их доля, как часто выпад.
@export var moves := 44
@export var double_from := 3
@export var triple_from := 10
@export var feint_from := 6
@export var feint_share := 0.32
@export var lunge_from := 5
@export var lunge_every := 5
@export var max_seconds := 110.0
## Бот: задержка реакции на замах и за сколько до выпада он шагает назад.
@export var bot_delay := 0.15
@export var bot_step := 0.3
@export var hit_stop := 0.07
@export var music_db := -11.0
@export var sfx_db := -5.0


static func load_default() -> FightingThreedTuning:
	var t := load(PATH) as FightingThreedTuning
	return t if t != null else FightingThreedTuning.new()
