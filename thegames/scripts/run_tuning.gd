class_name RunTuning
extends Resource
## Настройки забега, ресурс `res://resources/run.tres`. Стартовая пара разыгрывается (#61):
## жанр из тех, у кого есть демка на стартовой технологии, технология из `start_techs`, не та же
## пара, что в прошлом забеге. `genre` и `tech` стартовая пара автотеста (без розыгрыша, чтобы
## прогоны петли были одинаковыми) и дебага. Кап и его сигналы ниже; от капа и сложность
## мини-игр `t = (релиз − 1) / (кап − 1)`.

const PATH := "res://resources/run.tres"

@export var genre: Game.Genre = Game.Genre.PLATFORMER
@export var tech: Game.Tech = Game.Tech.BIT8
## Технологии розыгрыша старта: в M2 только 8-bit.
@export var start_techs: Array[Game.Tech] = [Game.Tech.BIT8]
@export var title := "Пираты на платформах"
@export var sprints := 5
## Кап забега (#62): разыгрывается на забег в `cap_min`..`cap_max` релизов, игроку не
## показывается. Сигналы капа считаются от него: «студия-ветеран» у критиков с капа −
## `veteran_left`, реплики «сколько ещё» во вставках с капа − `how_long_left`, покупатель на
## капе − `buyer_left`; все не раньше релиза `signals_from`.
@export var cap_min := 11
@export var cap_max := 13
@export var signals_from := 3
@export var veteran_left := 3
@export var how_long_left := 2
@export var buyer_left := 1
## Сколько переигровок в релизе (M0: ноль).
@export var replays := 0


static func load_default() -> RunTuning:
	var t := load(PATH) as RunTuning
	return t if t != null else RunTuning.new()
