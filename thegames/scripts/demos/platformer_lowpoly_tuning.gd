class_name PlatformerLowpolyTuning
extends Resource
## Числа правил демки платформер × low poly «тропа вглубь экрана» (#112), ресурс
## `res://resources/demos/platformer_lowpoly.tres`. Метры и секунды.

const PATH := "res://resources/demos/platformer_lowpoly.tres"

@export var lives := 3
@export var run_speed := 6.0
@export var jump_speed := 8.4
@export var gravity := 22.0
## Сколько после схода с края ещё можно прыгнуть.
@export var coyote := 0.15
@export var hero_radius := 0.3
## Неуязвимость после потери жизни.
@export var invulnerable_seconds := 1.5
## Касание скелета и подбор дублона: расстояние по земле.
@export var hit_distance := 0.7
@export var coin_distance := 0.85
## Ящик: половина стороны и скорость отскока вверх после того, как герой его разбил.
@export var crate_half := 0.425
@export var crate_bounce := 6.5
## Бочка на боку: радиус и половина длины. Ядро: радиус и высота полёта над тропой.
@export var barrel_radius := 0.37
@export var barrel_half := 0.43
@export var ball_radius := 0.22
@export var ball_height := 0.9
## Кусок короче этого не точка возврата (камни-ступеньки): возвращает на последний длинный.
@export var safe_length := 6.0
## Маяк засчитан на таком расстоянии от конца тропы.
@export var finish_distance := 1.6
## Возврат после потери жизни: на столько от начала куска тропы.
@export var respawn_inset := 1.2
## Бот: за сколько до края ямы и до ящика прыгать, с какого расстояния ждать скелета, на
## сколько держаться от него и от края тропы.
@export var bot_jump_distance := 0.6
@export var bot_crate_distance := 1.3
@export var bot_wait_distance := 3.2
@export var bot_guard_margin := 1.4
@export var bot_edge_margin := 0.7
## Бот: за сколько до уступа прыгать, запас до ядра и до края плота, окно времени до бочки, в
## которое пора прыгать.
@export var bot_step_distance := 0.9
@export var bot_ball_margin := 1.1
@export var bot_raft_margin := 0.6
@export var bot_barrel_min := 0.2
@export var bot_barrel_max := 0.36
## Как быстро камера разворачивается за поворотом тропы, 1/с.
@export var cam_turn := 2.6
## Камера за спиной: расстояние, высота, высота точки взгляда.
@export var cam_distance := 4.0
@export var cam_height := 2.1
@export var cam_look := 1.2
## Стоп-кадр на потере жизни, секунды.
@export var hit_stop := 0.12
@export var music_db := -10.0
@export var sfx_db := -6.0


static func load_default() -> PlatformerLowpolyTuning:
	var t := load(PATH) as PlatformerLowpolyTuning
	return t if t != null else PlatformerLowpolyTuning.new()
