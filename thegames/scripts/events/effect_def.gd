class_name EffectDef
extends Resource
## Последствие варианта мета-вставки (#63), спека `docs/specs/meta.md`. Деньги и репутация
## применяются сразу (`Events.apply`), остальное копится в `EventState` и читается следующим
## релизом (ограничения и бонусы #66), экономикой (доли с хвоста #66) и забегом (концовка #68).
## У каждого последствия пилюля на карточке; `text` её переписывает, пустая у флага скрыта.
## Продажа хвоста (`SELL_TAIL`, спасение): деньги за `MetaTuning.sell_tail_ticks` тиков лучшего
## хвоста, игра перестаёт платить (`EventState.sold_tails`, экономика в #66/#67).

enum Kind { MONEY, REPUTATION, RESTRICT_GENRE, RESTRICT_SETTING, RESTRICT_TECH, RESTRICT_SEQUEL, TAIL_SHARE, NEXT_BONUS, ENDING, FLAG, SELL_TAIL }
enum Stat { CRITICS, STREAMERS, SALES }

## Значение ограничения «выбрать при показе» и «как у прошлой игры».
const PICK := -1
const LAST := -2

@export var kind: Kind = Kind.MONEY
## Деньги, со знаком. С `mood_scaled` двигается настроением персонажа на ±`MetaTuning.mood_offer`.
@export var amount := 0
@export var mood_scaled := true
## Репутация ступенями со знаком (стрелки без числа), ступень `MetaTuning.rep_step`.
@export var steps := 0
## Ограничение: значение перечисления жанра, сеттинга или технологии, `PICK` или `LAST`; у
## сиквела индекс игры забега, `PICK` лучшая по критикам.
@export var value := PICK
## Доля с хвоста (0.3 это 30 %) на `games` следующих игр.
@export var share := 0.0
@export var games := 1
## Бонус следующей игре: что и насколько (стримеры +15, критики +0.5, продажи +0.2).
@export var stat: Stat = Stat.SALES
@export var bonus := 0.0
## Концовка (sale, corporation, legend) или флаг.
@export var id: StringName = &""
## Текст пилюли вместо собранного.
@export var text := ""
## Число из `MetaTuning` по имени свойства (#65): деньги (знак берётся из `amount`, по
## умолчанию плюс), доля или бонус (знак из `bonus`). Так суммы вставок живут в `meta.tres`.
@export var key: StringName = &""


static func money(amount_: int, scaled := true) -> EffectDef:
	var e := EffectDef.new()
	e.kind = Kind.MONEY
	e.amount = amount_
	e.mood_scaled = scaled
	return e


static func reputation(steps_: int) -> EffectDef:
	var e := EffectDef.new()
	e.kind = Kind.REPUTATION
	e.steps = steps_
	return e
