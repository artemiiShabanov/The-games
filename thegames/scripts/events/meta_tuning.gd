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


static func load_default() -> MetaTuning:
	var t := load(PATH) as MetaTuning
	return t if t != null else MetaTuning.new()
