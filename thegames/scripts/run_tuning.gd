class_name RunTuning
extends Resource
## Настройки забега, ресурс `res://resources/run.tres`. В M0 экономики нет: одна пара, число
## спринтов фиксировано, кап нужен только для сложности `t = (релиз − 1) / (кап − 1)`.

const PATH := "res://resources/run.tres"

@export var genre: Game.Genre = Game.Genre.PLATFORMER
@export var tech: Game.Tech = Game.Tech.BIT8
@export var title := "Пираты на платформах"
@export var sprints := 5
@export var cap := 12
## Сколько переигровок в релизе (M0: ноль).
@export var replays := 0


static func load_default() -> RunTuning:
	var t := load(PATH) as RunTuning
	return t if t != null else RunTuning.new()
