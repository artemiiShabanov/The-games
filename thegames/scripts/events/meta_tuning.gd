class_name MetaTuning
extends Resource
## Числа мета-вставок (#63), ресурс `res://resources/meta.tres`. Суммы конкретных вставок
## лежат в их ресурсах; здесь общее.

const PATH := "res://resources/meta.tres"

## Одна стрелка репутации в карточке, в очках `MarketState.reputation`.
@export var rep_step := 1.5
## Настроение персонажа двигает деньги его предложений на ±эту долю за ступень.
@export var mood_offer := 0.2
## Шанс выигрыша монетки.
@export var coin_chance := 0.5
## Доли с хвоста одной игры суммируются не выше этого.
@export var max_tail_share := 0.5
## Пауза с исходом на карточке после решения, с.
@export var outcome_seconds := 1.0

# Планировщик (#64).
## Вставки с этого релиза.
@export var first_release := 3
## Шанс случайной вставки по числу релизов с последней (индекс; дальше последнее значение):
## на следующем 0, через один 50 %, через два 100 %.
@export var random_by_gap: PackedFloat32Array = PackedFloat32Array([0.0, 0.0, 0.5, 1.0])
## «Репутация выросла за последние два релиза»: на столько очков и больше.
@export var rep_rising := 1.5
## «Денег меньше двух дешёвых релизов».
@export var low_cash_releases := 2.0
## Покупатель с середины забега при репутации от порога (и на капе −1 всегда, #62).
@export var sale_reputation := 10.0
## Покупатель, которому не уступили в цене, уходит на столько релизов.
@export var buyer_gone_releases := 2


static func load_default() -> MetaTuning:
	var t := load(PATH) as MetaTuning
	return t if t != null else MetaTuning.new()
