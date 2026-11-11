class_name Events
extends RefCounted
## Мета-вставки без экрана (#63), спека `docs/specs/meta.md`. `resolve` превращает `EventDef`
## в конкретное предложение: реплика по настроению, суммы с поправкой на настроение (±20 % за
## ступень, по сотням), выбранные жанр, сеттинг, технология или игра для сиквела (`PICK` и
## `LAST`), тексты пилюль. `apply` применяет ответ: деньги и репутация сразу, ограничения, доли
## с хвоста, бонусы, флаги и концовка в `EventState`; монетка решается здесь. Экран
## (`EventCard`) только показывает предложение и отдаёт номер ответа.

enum Tone { PLUS, MINUS, LOCK, ENDING, NEUTRAL }

const DIR := "res://resources/events/"

## Что вставка знает о забеге при показе.
class Context:
	var genres: Array[int] = []
	var techs: Array[int] = []
	var settings: Array[int] = []
	var records: Array[GameRecord] = []
	var studio := ""
	var rng: RandomNumberGenerator


## Последствие с конкретными значениями.
class Effect:
	var kind: EffectDef.Kind
	var amount := 0
	var steps := 0
	var value := 0
	var share := 0.0
	var games := 1
	var stat: EffectDef.Stat
	var bonus := 0.0
	var id: StringName = &""
	var text := ""


class Pill:
	var text := ""
	var tone: Tone = Tone.NEUTRAL

	static func of(text_: String, tone_: Tone) -> Pill:
		var p := Pill.new()
		p.text = text_
		p.tone = tone_
		return p


class Choice:
	var text := ""
	var effects: Array[Effect] = []
	var coin := false
	var lose_effects: Array[Effect] = []
	var mood_delta := 0
	var pills: Array[Pill] = []


class Offer:
	var def: EventDef
	var character: CharacterDef
	var mood := 0
	var line := ""
	var choices: Array[Choice] = []


## Все вставки из `resources/events/`, по имени файла.
static func load_all() -> Array[EventDef]:
	var out: Array[EventDef] = []
	var dir := DirAccess.open(DIR)
	if dir == null:
		return out
	var names: PackedStringArray = []
	for f in dir.get_files():
		if f.ends_with(".tres") or f.ends_with(".res"):
			names.append(f)
	names.sort()
	for f in names:
		var d := load(DIR + f) as EventDef
		if d != null:
			out.append(d)
	return out


static func find(defs: Array[EventDef], id: StringName) -> EventDef:
	for d in defs:
		if d.id == id:
			return d
	return null


## `who`: кто приходит, если не основной персонаж (`EventPlanner.who`).
static func resolve(def: EventDef, mood: int, ctx: Context, meta: MetaTuning, who: CharacterDef = null) -> Offer:
	var o := Offer.new()
	o.def = def
	o.character = who if who != null else def.character
	o.mood = mood
	# Выбор при показе один на вставку: «гонки» в реплике и во всех вариантах одни и те же.
	var picks: Dictionary = {}
	var vars := {"studio": ctx.studio}
	# Игры для реплик по умолчанию: лучшая по критикам и с самым большим хвостом.
	var best := _best_game(ctx.records)
	if best >= 0:
		vars["game"] = ctx.records[best].title
	var tail := _best_tail(ctx.records)
	if tail >= 0:
		vars["tail_game"] = ctx.records[tail].title
	var texts: Array[String] = []
	for c in def.choices:
		var oc := Choice.new()
		oc.coin = c.coin
		oc.mood_delta = c.mood_delta
		for e in c.effects:
			var r := _resolve_effect(e, mood, ctx, meta, picks, vars)
			if r != null:
				oc.effects.append(r)
		for e in c.lose_effects:
			var r := _resolve_effect(e, mood, ctx, meta, picks, vars)
			if r != null:
				oc.lose_effects.append(r)
		# Вариант, чьи последствия некуда применить (нет хвоста на продажу), не предлагается.
		if not c.effects.is_empty() and oc.effects.is_empty() and not c.coin:
			continue
		o.choices.append(oc)
		texts.append(c.text)
	for i in o.choices.size():
		o.choices[i].text = _fill(texts[i], vars)
		o.choices[i].pills = _pills(o.choices[i], o.character)
	o.line = _fill(def.line_for(mood), vars)
	return o


static func _resolve_effect(e: EffectDef, mood: int, ctx: Context, meta: MetaTuning, picks: Dictionary,
		vars: Dictionary) -> Effect:
	var r := Effect.new()
	r.kind = e.kind
	r.text = e.text
	r.steps = e.steps
	r.share = e.share
	r.games = e.games
	r.stat = e.stat
	r.bonus = e.bonus
	r.id = e.id
	# Число из `meta.tres` по ключу: деньги со знаком `amount`, доля, бонус со знаком `bonus`.
	var amount := e.amount
	if e.key != &"" and e.key in meta:
		var v := float(meta.get(e.key))
		match e.kind:
			EffectDef.Kind.MONEY:
				amount = int(v) * (-1 if e.amount < 0 else 1)
			EffectDef.Kind.TAIL_SHARE:
				r.share = v
			EffectDef.Kind.NEXT_BONUS:
				r.bonus = v * (-1.0 if e.bonus < 0.0 else 1.0)
	match e.kind:
		EffectDef.Kind.MONEY:
			var a := float(amount)
			if e.mood_scaled and amount > 0:
				a *= 1.0 + mood * meta.mood_offer
			r.amount = int(roundf(a / 100.0)) * 100
			if not vars.has("money") and r.amount > 0:
				vars["money"] = Style.format_money(r.amount)
		EffectDef.Kind.RESTRICT_GENRE, EffectDef.Kind.RESTRICT_SETTING, EffectDef.Kind.RESTRICT_TECH:
			var key := "%d:%d" % [e.kind, e.value]
			if not picks.has(key):
				picks[key] = _pick_value(e.kind, e.value, ctx)
			r.value = picks[key]
			if r.value < 0:
				return null
			var name := _value_name(e.kind, r.value)
			var var_key: String = {EffectDef.Kind.RESTRICT_GENRE: "genre", EffectDef.Kind.RESTRICT_SETTING: "setting",
					EffectDef.Kind.RESTRICT_TECH: "tech"}[e.kind]
			if not vars.has(var_key):
				vars[var_key] = name
		EffectDef.Kind.RESTRICT_SEQUEL:
			r.value = e.value if e.value >= 0 else _best_game(ctx.records)
			if r.value < 0 or r.value >= ctx.records.size():
				return null
			vars["game"] = ctx.records[r.value].title
		EffectDef.Kind.SELL_TAIL:
			r.value = _best_tail(ctx.records)
			if r.value < 0:
				return null
			r.amount = ctx.records[r.value].score.last_tick * meta.sell_tail_ticks
			vars["tail_game"] = ctx.records[r.value].title
	return r


static func _pick_value(kind: EffectDef.Kind, value: int, ctx: Context) -> int:
	var last: GameRecord = ctx.records.back() if not ctx.records.is_empty() else null
	var pool: Array[int] = ctx.genres
	var last_value := -1
	match kind:
		EffectDef.Kind.RESTRICT_SETTING:
			pool = ctx.settings
			last_value = int(last.setting) if last != null else -1
		EffectDef.Kind.RESTRICT_TECH:
			pool = ctx.techs
			last_value = int(last.tech) if last != null else -1
		_:
			last_value = int(last.genre) if last != null else -1
	if value >= 0:
		return value if pool.has(value) else -1
	if value == EffectDef.LAST and last_value >= 0:
		return last_value
	if pool.is_empty():
		return -1
	# «Хочу X»: другое, чем прошлая игра, если есть из чего.
	var other: Array[int] = []
	for v in pool:
		if v != last_value:
			other.append(v)
	var from := other if not other.is_empty() else pool
	return from[ctx.rng.randi_range(0, from.size() - 1)]


static func _best_game(records: Array[GameRecord]) -> int:
	var best := -1
	var best_c := -INF
	for i in records.size():
		var c := records[i].score.critics if records[i].score != null else 0.0
		if c > best_c:
			best_c = c
			best = i
	return best


## Игра с самым большим тиком хвоста, −1 если хвостов нет.
static func _best_tail(records: Array[GameRecord]) -> int:
	var best := -1
	var best_tick := 0
	for i in records.size():
		var tick := records[i].score.last_tick if records[i].score != null else 0
		if tick > best_tick:
			best_tick = tick
			best = i
	return best


static func _value_name(kind: EffectDef.Kind, value: int) -> String:
	match kind:
		EffectDef.Kind.RESTRICT_SETTING:
			return Game.setting_name(value as Game.Setting)
		EffectDef.Kind.RESTRICT_TECH:
			return Game.tech_name(value as Game.Tech)
	return Game.genre_name(value as Game.Genre)


# --- Пилюли --------------------------------------------------------------------------------

## Пилюли варианта: ограничения следующей игры одной пилюлей, монетка с обеими ветками через
## «или», настроение персонажа последней.
static func _pills(c: Choice, who: CharacterDef) -> Array[Pill]:
	var out: Array[Pill] = []
	if c.coin:
		out.append(Pill.of("монетка", Tone.NEUTRAL))
	out.append_array(_effect_pills(c.effects))
	if c.coin and not c.lose_effects.is_empty():
		out.append(Pill.of("или", Tone.NEUTRAL))
		out.append_array(_effect_pills(c.lose_effects))
	if c.mood_delta < 0:
		out.append(Pill.of("%s обидится" % who.short(), Tone.MINUS))
	elif c.mood_delta > 0:
		out.append(Pill.of("%s запомнит" % who.short(), Tone.PLUS))
	return out


static func _effect_pills(effects: Array[Effect]) -> Array[Pill]:
	var out: Array[Pill] = []
	var next: PackedStringArray = []
	for e in effects:
		if e.text != "":
			out.append(Pill.of(e.text, _tone(e)))
			continue
		match e.kind:
			EffectDef.Kind.MONEY:
				out.append(Pill.of(("+" if e.amount > 0 else "−") + Style.format_money(absi(e.amount)), _tone(e)))
			EffectDef.Kind.REPUTATION:
				var arrow := ("↑" if e.steps > 0 else "↓").repeat(absi(e.steps))
				out.append(Pill.of("репутация " + arrow, _tone(e)))
			EffectDef.Kind.RESTRICT_GENRE, EffectDef.Kind.RESTRICT_SETTING, EffectDef.Kind.RESTRICT_TECH:
				next.append(_value_name(e.kind, e.value).to_lower())
			EffectDef.Kind.RESTRICT_SEQUEL:
				next.append("сиквел")
			EffectDef.Kind.TAIL_SHARE:
				var games := "" if e.games <= 1 else " %s игр" % (["двух", "трёх", "четырёх"][e.games - 2] if e.games <= 4 else str(e.games))
				out.append(Pill.of("−%d %% с хвоста%s" % [roundi(e.share * 100.0), games], Tone.MINUS))
			EffectDef.Kind.NEXT_BONUS:
				var what: String = ["критики", "стримеры", "продажи"][e.stat]
				var v := ("%+.1f" % e.bonus) if e.stat == EffectDef.Stat.CRITICS else ("%+d %%" % roundi(e.bonus * 100.0) if e.stat == EffectDef.Stat.SALES else "%+d" % roundi(e.bonus))
				out.append(Pill.of("%s следующей игры %s" % [what, v.replace("-", "−")], _tone(e)))
			EffectDef.Kind.ENDING:
				out.append(Pill.of("концовка", Tone.ENDING))
			EffectDef.Kind.SELL_TAIL:
				out.append(Pill.of("+" + Style.format_money(e.amount), Tone.PLUS))
				out.append(Pill.of("хвост перестанет платить", Tone.MINUS))
	if not next.is_empty():
		out.insert(mini(1, out.size()), Pill.of("следующая игра: " + " · ".join(next), Tone.LOCK))
	return out


static func _tone(e: Effect) -> Tone:
	match e.kind:
		EffectDef.Kind.MONEY:
			return Tone.PLUS if e.amount > 0 else Tone.MINUS
		EffectDef.Kind.REPUTATION:
			return Tone.PLUS if e.steps > 0 else Tone.MINUS
		EffectDef.Kind.NEXT_BONUS:
			return Tone.PLUS if e.bonus > 0 else Tone.MINUS
		EffectDef.Kind.TAIL_SHARE:
			return Tone.MINUS
		EffectDef.Kind.ENDING:
			return Tone.ENDING
		EffectDef.Kind.FLAG:
			return Tone.NEUTRAL
	return Tone.LOCK


# --- Применение ----------------------------------------------------------------------------

## Ответ `index` на предложение: что применилось и исход монетки (пусто без монетки).
static func apply(offer: Offer, index: int, wallet: Wallet, market: MarketState, state: EventState,
		meta: MetaTuning, rng: RandomNumberGenerator, release: int) -> String:
	var c := offer.choices[index]
	var effects := c.effects
	var outcome := ""
	if c.coin:
		var win := rng.randf() < meta.coin_chance
		outcome = "Монетка: повезло" if win else "Монетка: не повезло"
		if not win:
			effects = c.lose_effects
	var who := offer.character.with_name() if offer.character != null else ""
	var payer := offer.character.name if offer.character != null else ""
	for e in effects:
		match e.kind:
			EffectDef.Kind.MONEY:
				if e.amount > 0:
					wallet.earn(e.amount, &"event", payer)
				else:
					wallet.spend(-e.amount, &"event", payer)
			EffectDef.Kind.REPUTATION:
				market.reputation += e.steps * meta.rep_step
			EffectDef.Kind.RESTRICT_GENRE, EffectDef.Kind.RESTRICT_SETTING, EffectDef.Kind.RESTRICT_TECH, EffectDef.Kind.RESTRICT_SEQUEL:
				var r := EventState.Restriction.new()
				r.kind = e.kind
				r.value = e.value
				r.by = who
				state.restrictions.append(r)
			EffectDef.Kind.TAIL_SHARE:
				var t := EventState.TailShare.new()
				t.share = e.share
				t.games = e.games
				t.by = who
				state.tail_shares.append(t)
			EffectDef.Kind.NEXT_BONUS:
				var b := EventState.Bonus.new()
				b.stat = e.stat
				b.value = e.bonus
				state.bonuses.append(b)
			EffectDef.Kind.ENDING:
				state.ending = e.id
			EffectDef.Kind.FLAG:
				state.flags[e.id] = release
			EffectDef.Kind.SELL_TAIL:
				wallet.earn(e.amount, &"event", payer)
				if not state.sold_tails.has(e.value):
					state.sold_tails.append(e.value)
	if offer.character != null:
		var ch := offer.character
		state.shift_mood(ch.id, c.mood_delta)
		# Отказы подряд: персонаж с лимитом уходит до конца забега.
		state.refusals[ch.id] = state.refusals.get(ch.id, 0) + 1 if c.mood_delta < 0 else 0
		if ch.leaves_after_refusals > 0 and state.refusals[ch.id] >= ch.leaves_after_refusals:
			state.flags[StringName("left_" + String(ch.id))] = release
	state.mark_shown(offer.def.id, release)
	return outcome


static func _fill(template: String, vars: Dictionary) -> String:
	var out := template
	for k in vars:
		out = out.replace("{" + k + "}", str(vars[k]))
	return out
