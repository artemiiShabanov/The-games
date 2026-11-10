class_name RunTuning
extends Resource
## Настройки забега, ресурс `res://resources/run.tres`. Стартовая пара разыгрывается (#61):
## жанр из тех, у кого есть демка на стартовой технологии, технология из `start_techs`, не та же
## пара, что в прошлом забеге. `genre` и `tech` стартовая пара автотеста (без розыгрыша, чтобы
## прогоны петли были одинаковыми) и дебага. Кап нужен для сложности `t = (релиз − 1) / (кап − 1)`.

const PATH := "res://resources/run.tres"

@export var genre: Game.Genre = Game.Genre.PLATFORMER
@export var tech: Game.Tech = Game.Tech.BIT8
## Технологии розыгрыша старта: в M2 только 8-bit.
@export var start_techs: Array[Game.Tech] = [Game.Tech.BIT8]
@export var title := "Пираты на платформах"
@export var sprints := 5
@export var cap := 12
## Сколько переигровок в релизе (M0: ноль).
@export var replays := 0


static func load_default() -> RunTuning:
	var t := load(PATH) as RunTuning
	return t if t != null else RunTuning.new()
