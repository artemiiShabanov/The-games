class_name AchievementDef
extends Resource
## Достижение (#139), спека `docs/specs/run.md`: событие внутри игры, которое открывает сеттинг
## на весь профиль. Ресурсы `res://resources/achievements/*.tres`, порог здесь же.

enum Condition {
	CASH,            ## на счету студии не меньше `threshold`
	PERFECT_CRITICS, ## все критики поставили игре не меньше `threshold`
	FRANCHISE_PART,  ## вышла часть франшизы номер `threshold`
	PAID_STREAK,     ## `threshold` релизов подряд окупились первой неделей
	CLEAN_STREAK,    ## `threshold` релизов подряд без багов
	TECHS_IN_RUN,    ## игры на `threshold` разных технологиях за забег
	ENDING,          ## забег закончился концовкой `ending`
	RELEASES,        ## выпущено `threshold` игр за забег
}

@export var id: StringName = &""
@export var title := ""
## Условие словами, одной строкой.
@export var text := ""
@export var setting: Game.Setting = Game.Setting.PIRATES
@export var condition: Condition = Condition.CASH
@export var threshold := 1
@export var ending: StringName = &""
