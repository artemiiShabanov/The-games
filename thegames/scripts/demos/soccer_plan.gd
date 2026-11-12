class_name SoccerPlan
extends RefCounted
## План соперника в футболе × 16/32-bit (#101) по сиду (`SoccerPlanGen`): характер соперника и
## вратарей и цвет формы. Правила в `SoccerSim`.

## Соперник: скорость бега, с какого расстояния бьёт, зарядка удара, как часто идёт в подкат
## (доля секунды, когда рядом с героем с мячом), реакция (с запозданием видит мяч).
var rival_speed := 110.0
var rival_shot_range := 260.0
var rival_charge := 0.5
var rival_tackle := 0.5
var rival_react := 0.15
## Вратари: реакция и дальность прыжка у своего и у чужого.
var keeper_reach := 34.0
var keeper_react := 0.2
var rival_keeper_reach := 34.0
var rival_keeper_react := 0.2
## Цвет формы соперника: индекс роли палитры.
var rival_kit := 0
## Зерно случайных решений матча (куда бьёт соперник).
var seed := 1


func signature() -> String:
	return "%d:%d:%d:%d:%d:%d" % [int(rival_speed), int(rival_shot_range), int(rival_charge * 100.0),
			int(rival_tackle * 100.0), int(keeper_reach), rival_kit]
