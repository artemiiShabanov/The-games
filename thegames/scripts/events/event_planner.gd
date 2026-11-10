class_name EventPlanner
extends RefCounted
## Планировщик мета-вставок (#64), спека `docs/specs/meta.md`: чистые функции, одна вставка за
## фазу студии. Порядок: спасение (банкротство, #67), затем концовка, если её условие выполнено
## (гарантированно, без шанса, не чаще `cooldown` после отказа), затем случайная: с
## `MetaTuning.first_release`, шанс по давности последней вставки (`random_by_gap`: 0, 50 %,
## 100 %), среди подходящих по условию та, что показывалась реже. Вставка недоступна, если
## её персонаж ушёл (отказы подряд), не прошёл `cooldown` или она `once` и уже была.
## Условия по ключу `EventDef.condition` (`met`); неизвестный ключ не выполняется.

## Что планировщик знает о забеге в фазе студии.
class Context:
	var release := 1
	var cap := 12
	var cash := 0
	## Самый дешёвый релиз из открытого.
	var cheapest := 0
	var reputation := 0.0
	## Репутация два релиза назад (до текущего), для «выросла».
	var reputation_before := 0.0
	var records: Array[GameRecord] = []
	var genres := 1
	var sequels := false
	var bankrupt := false
	## Кап −1 и покупателя ещё не было (#62).
	var buyer_due := false


static func plan(defs: Array[EventDef], ctx: Context, state: EventState, meta: MetaTuning,
		rng: RandomNumberGenerator) -> EventDef:
	if ctx.bankrupt:
		return _first(defs, EventDef.Kind.RESCUE, ctx, state, meta)
	if ctx.release < meta.first_release:
		return null
	var ending := _first(defs, EventDef.Kind.ENDING, ctx, state, meta)
	if ending != null:
		return ending
	if rng.randf() >= random_chance(ctx.release - state.last_event_release, meta):
		return null
	var pool: Array[EventDef] = []
	var least := 1 << 30
	for d in defs:
		if d.kind != EventDef.Kind.RANDOM or not available(d, ctx, state, meta):
			continue
		var n: int = state.shown.get(d.id, 0)
		if n < least:
			least = n
			pool.clear()
		if n == least:
			pool.append(d)
	if pool.is_empty():
		return null
	return pool[rng.randi_range(0, pool.size() - 1)]


static func random_chance(gap: int, meta: MetaTuning) -> float:
	if meta.random_by_gap.is_empty():
		return 0.0
	return meta.random_by_gap[clampi(gap, 0, meta.random_by_gap.size() - 1)]


static func _first(defs: Array[EventDef], kind: EventDef.Kind, ctx: Context, state: EventState, meta: MetaTuning) -> EventDef:
	for d in defs:
		if d.kind == kind and available(d, ctx, state, meta):
			return d
	return null


## Может ли вставка прийти сейчас: персонаж на месте, давность, условие.
static func available(d: EventDef, ctx: Context, state: EventState, meta: MetaTuning) -> bool:
	if d.character != null and state.left(d.character.id):
		return false
	if d.once and state.shown.has(d.id):
		return false
	if d.cooldown > 0 and state.last_shown.has(d.id) and ctx.release - state.last_shown[d.id] < d.cooldown:
		return false
	return met(d.condition, ctx, state, meta)


static func met(key: StringName, ctx: Context, state: EventState, meta: MetaTuning) -> bool:
	match key:
		&"always":
			return true
		&"publisher_offer":
			return ctx.genres >= 2
		&"investor_low_cash":
			return ctx.cash < ctx.cheapest * meta.low_cash_releases
		&"reputation_rising":
			return ctx.reputation - ctx.reputation_before >= meta.rep_rising
		&"buyer":
			if state.flags.has(&"buyer_gone") and ctx.release - state.flags[&"buyer_gone"] <= meta.buyer_gone_releases:
				return false
			return ctx.buyer_due or (ctx.release * 2 >= ctx.cap and ctx.reputation >= meta.sale_reputation)
		&"rescue":
			return ctx.bankrupt
	return false
