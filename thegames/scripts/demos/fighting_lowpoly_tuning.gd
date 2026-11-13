class_name FightingLowpolyTuning
extends Resource
## Числа правил демки файтинг × low poly «один на один сбоку в объёме» (#116), ресурс
## `res://resources/demos/fighting_lowpoly.tres`. Метры и секунды.

const PATH := "res://resources/demos/fighting_lowpoly.tres"

@export var countdown := 1.5
## Здоровье бойцов.
@export var hero_hp := 100
@export var rival_hp := 300
## Палуба: половина длины; бойцы стартуют на таком расстоянии от середины и не сходятся ближе.
@export var arena_half := 4.6
@export var start_gap := 1.3
@export var min_gap := 0.85
## Ходьба героя и соперника.
@export var hero_walk := 2.3
@export var rival_walk := 1.7
## Удар рукой: замах, сколько герой открыт после попадания и после промаха или блока,
## дальность. Связка до трёх ударов рукой: следующий выходит через `hero_link` после попадания
## с замахом `hero_chain_windup`; урон по ударам связки.
@export var hero_windup := 0.2
@export var hero_recover := 0.28
@export var hero_punished := 0.5
@export var hero_reach := 1.55
@export var hero_link := 0.08
@export var hero_chain_windup := 0.15
@export var punch_damage: Array[int] = [5, 5, 7]
## Удар ногой: замах сам по себе и в конце связки, дальность, урон, сколько герой открыт после
## попадания и после промаха или блока.
@export var kick_windup := 0.32
@export var kick_chain_windup := 0.2
@export var kick_reach := 1.9
@export var kick_damage := 12
@export var kick_recover := 0.36
@export var kick_punished := 0.62
## Удар сбоку во столько раз сильнее.
@export var flank_mult := 1.5
## Удар соперника: дальность с выпадом, сколько он открыт после последнего удара связки (в блок
## или мимо) и после попадания, пауза между ударами связки.
@export var rival_reach := 1.75
@export var rival_lunge := 0.35
@export var rival_punished := 0.6
@export var rival_recover := 0.35
@export var link := 0.16
## Урон соперника: рукой, ногой и сильный удар (пробивает блок); замах ноги во столько раз дольше.
@export var rival_damage := 8
@export var rival_kick_damage := 12
@export var rival_kick_windup := 1.3
@export var heavy_damage := 18
## Оглушение после пропущенного удара и после блока.
@export var stun := 0.38
@export var block_stun := 0.1
## Шаг в глубину: сколько длится, сколько из этого боец неуязвим, пауза до следующего шага, на
## сколько уходит вбок, сколько секунд после ухода соперник открыт сбоку.
@export var step_seconds := 0.42
@export var step_safe := 0.3
@export var step_cooldown := 0.25
@export var step_depth := 0.95
@export var flank_seconds := 0.75
@export var max_seconds := 150.0
## Бот: реакция на замах и за сколько до удара уходит шагом.
@export var bot_react := 0.12
@export var bot_step_lead := 0.18
## Отклик: стоп-кадр и белая заливка на попадании.
@export var hit_stop := 0.07
@export var hit_flash := 0.1
@export var music_db := -10.0
@export var sfx_db := -6.0


static func load_default() -> FightingLowpolyTuning:
	var t := load(PATH) as FightingLowpolyTuning
	return t if t != null else FightingLowpolyTuning.new()
