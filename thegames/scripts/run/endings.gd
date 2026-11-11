class_name Endings
extends RefCounted
## Концовки забега (#68), спека `docs/specs/run.md`: продажа (оценка студии, с уступкой
## покупателя +10 %), корпорация (суммарный тик хвостов × 10, «годовой оборот»), легенда
## (сумма критиков трёх лучших игр × 10 плюс их охват), банкротство (без оценки). Условия
## корпорации и легенды те же, что у вставок (`EventPlanner.corporation`, `legend`), пороги в
## `run.tres`. «Итоги года» на капе: все выполненные концовки и продажа, закрыть карточку
## значит продать (`year_offer`).

enum Id { SALE, CORPORATION, LEGEND, BANKRUPTCY }

const NAMES := ["Продажа", "Корпорация", "Легенда", "Банкротство"]
const KEYS: Array[StringName] = [&"sale", &"corporation", &"legend", &"bankruptcy"]
## Уступка покупателя по флагу вставки «попросить больше».
const BUYER_MORE := 1.1


class Result:
	var id: Id = Id.SALE
	var score := 0
	## Три лучшие игры забега по критикам, от лучшей.
	var top: Array[GameRecord] = []
	var releases := 0
	var studio := ""

	func title() -> String:
		return NAMES[id]

	## Оценка крупно: деньги у продажи и корпорации, очки у легенды, пусто у банкротства.
	func score_text() -> String:
		match id:
			Id.SALE, Id.CORPORATION:
				return Style.format_money(score)
			Id.LEGEND:
				return str(score)
		return ""

	func caption() -> String:
		match id:
			Id.SALE:
				return "Студию купили. Чек с правильным количеством нулей"
			Id.CORPORATION:
				return "Старые игры кормят лучше новых. Теперь вы корпорация"
			Id.LEGEND:
				return "Ушли на пике, пока все ещё хлопают"
		return "Деньги кончились раньше идей"

	func _to_string() -> String:
		return "%s %d, релизов %d, лучшие %s" % [title(), score, releases, top.map(func(r: GameRecord) -> String: return r.title)]


static func from_key(key: StringName) -> Id:
	var i := KEYS.find(key)
	return (i if i >= 0 else Id.SALE) as Id


static func compute(id: Id, records: Array[GameRecord], stats: RunStats, flags: Dictionary) -> Result:
	var r := Result.new()
	r.id = id
	r.releases = records.size()
	r.top = best(records, 3)
	match id:
		Id.SALE:
			var v := float(stats.valuation if stats != null else 0)
			if flags.has(&"buyer_more"):
				v *= BUYER_MORE
			r.score = int(roundf(v))
		Id.CORPORATION:
			r.score = (stats.tail_total if stats != null else 0) * 10
		Id.LEGEND:
			var sum := 0.0
			var reach := 0
			for g in r.top:
				sum += g.score.critics
				reach += g.score.streamers
			r.score = int(roundf(sum * 10.0)) + reach
	return r


## Лучшие игры забега по критикам.
static func best(records: Array[GameRecord], n: int) -> Array[GameRecord]:
	var scored: Array[GameRecord] = []
	for r in records:
		if r.score != null:
			scored.append(r)
	scored.sort_custom(func(a: GameRecord, b: GameRecord) -> bool: return a.score.critics > b.score.critics)
	return scored.slice(0, n)


## Какие концовки выполнены на капе: продажа всегда, корпорация и легенда по условиям.
static func available(records: Array[GameRecord], t: RunTuning) -> Array[Id]:
	var out: Array[Id] = [Id.SALE]
	if EventPlanner.corporation(records, t):
		out.append(Id.CORPORATION)
	if EventPlanner.legend(records, t):
		out.append(Id.LEGEND)
	return out


## Вставка «Итоги года» на капе: журналист подводит итоги, варианты это выполненные концовки с
## оценкой в пилюле; продажа первой и выбирается, если карточку закрыть.
static func year_offer(records: Array[GameRecord], stats: RunStats, flags: Dictionary, t: RunTuning,
		who: CharacterDef, studio: String) -> Events.Offer:
	var def := EventDef.new()
	def.id = &"year_summary"
	def.title = "Итоги года"
	def.kind = EventDef.Kind.ENDING
	def.character = who
	var o := Events.Offer.new()
	o.def = def
	o.character = who
	o.line = "Год закончился, пишу итоги для журнала. Чем студия «%s» его закрывает? Покупатель ждёт ответа, а молчание он тоже примет за «да»." % studio
	var texts := {Id.SALE: "Продать студию", Id.CORPORATION: "Стать корпорацией", Id.LEGEND: "Закрыться легендой"}
	for id in available(records, t):
		var res := compute(id, records, stats, flags)
		var c := Events.Choice.new()
		c.text = texts[id]
		var e := Events.Effect.new()
		e.kind = EffectDef.Kind.ENDING
		e.id = KEYS[id]
		c.effects.append(e)
		var label := "оценка " + res.score_text() if id == Id.SALE else ("оборот " + res.score_text() if id == Id.CORPORATION else "%s очков" % res.score_text())
		c.pills.append(Events.Pill.of("концовка", Events.Tone.ENDING))
		c.pills.append(Events.Pill.of(label, Events.Tone.PLUS))
		o.choices.append(c)
	return o
