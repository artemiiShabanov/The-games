extends Control
## Тестовая сцена мета-вставок (#63): любая вставка из `resources/events/` карточкой персонажа
## на синтетическом забеге (три жанра, две технологии, две прошлые игры, студия «Тихая Лампа»).
## Раздел «Вставки» дебаг-меню: вставка, настроение персонажа, деньги, сид, «Показать»;
## состояние вставок копится между показами, «Сбросить» обнуляет. Под ботом: для каждой
## вставки и каждого варианта свежий показ, ответ, сверка денег и репутации с пилюлями,
## ограничений, долей, концовки и настроения с `EventState`; настроение +1 даёт +20 % к сумме,
## «хочу X» не совпадает с прошлой игрой. `--no-checks --event=<id> [--mood=N] [--choice=N]`
## показывает одну вставку для скриншота.

const SECTION: StringName = &"Вставки"
const G := Game.Genre
const T := Game.Tech

var defs: Array[EventDef] = []
var event_id := ""
var mood := 0
var cash := 20000
var seed_value := 1
var release := 5

var meta: MetaTuning
var success: SuccessTuning
var state := EventState.new()
var wallet: Wallet
var market: MarketState
var offer: Events.Offer
var card: EventCard
var rng := RandomNumberGenerator.new()
var _label: Label
var _checks := false
## Очередь бота: (вставка, вариант).
var _queue: Array[Vector2i] = []
var _before_cash := 0
var _before_rep := 0.0
var _outcome := ""


func _ready() -> void:
	meta = MetaTuning.load_default()
	success = SuccessTuning.load_default()
	defs = Events.load_all()
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	_label = Label.new()
	_label.position = Vector2(Style.EDGE, 1080 - 40)
	_label.add_theme_font_size_override("font_size", Style.FONT_CAPTION)
	_label.add_theme_color_override("font_color", Style.INK_3)
	add_child(_label)
	var ids: Array[String] = []
	for d in defs:
		ids.append(String(d.id))
	if not ids.is_empty():
		event_id = ids[0]
	Debug.add_choice(SECTION, "Вставка", ids, func() -> String: return event_id, func(v: String) -> void: event_id = v)
	Debug.add_number(SECTION, "Настроение", func() -> int: return mood, func(v: float) -> void: mood = int(v), -1, 1, 1)
	Debug.add_number(SECTION, "Деньги", func() -> int: return cash, func(v: float) -> void: cash = int(v), 0, 100000, 1000)
	Debug.add_number(SECTION, "Сид", func() -> int: return seed_value, func(v: float) -> void: seed_value = int(v), 1, 999, 1)
	Debug.add_action(SECTION, "Показать", _launch)
	Debug.add_action(SECTION, "Сбросить состояние", func() -> void: state = EventState.new())
	Debug.watch("вставки", func() -> String: return str(state))
	if AutoTest.enabled:
		var args := AutoTest.parse_args(OS.get_cmdline_user_args())
		if args.has("no-checks"):
			event_id = str(args.get("event", event_id))
			mood = int(str(args.get("mood", "0")))
		else:
			_checks = true
			Debug.skip_cards = true
			AutoTest.require("event checks")
			_static_checks()
			for e in defs.size():
				for c in defs[e].choices.size():
					_queue.append(Vector2i(e, c))
			_next_check()
			return
	_launch()


func _exit_tree() -> void:
	Debug.clear_section(SECTION)


func _context() -> Events.Context:
	var ctx := Events.Context.new()
	ctx.genres = [G.PLATFORMER, G.SHOOTER, G.RACING]
	ctx.techs = [T.BIT8, T.ASCII]
	ctx.settings = [Game.Setting.PIRATES, Game.Setting.SPACE, Game.Setting.CASTLES]
	ctx.studio = "Тихая Лампа"
	ctx.rng = rng
	var a := GameRecord.create(G.PLATFORMER, T.BIT8, 1, "Пираты на платформах", Game.Setting.PIRATES)
	a.score = ReleaseScore.new()
	a.score.critics = 8.4
	var b := GameRecord.create(G.SHOOTER, T.BIT8, 2, "Корсары в прицеле", Game.Setting.SPACE)
	b.score = ReleaseScore.new()
	b.score.critics = 6.1
	ctx.records = [a, b]
	return ctx


func _launch() -> void:
	if card != null:
		card.queue_free()
		card = null
	var def := Events.find(defs, StringName(event_id))
	if def == null:
		return
	rng.seed = seed_value
	wallet = Wallet.new(cash)
	market = MarketState.create(success, rng, true)
	if not _checks:
		state.moods[def.character.id] = mood
	offer = Events.resolve(def, state.mood(def.character.id), _context(), meta)
	_before_cash = wallet.cash
	_before_rep = market.reputation
	card = EventCard.new()
	card.setup(offer, release, wallet, _apply, meta)
	card.finished.connect(_on_finished)
	add_child(card)
	_label.text = "%s · настроение %+d" % [def.id, state.mood(def.character.id)]


func _apply(i: int) -> String:
	_outcome = Events.apply(offer, i, wallet, market, state, meta, rng, release)
	return _outcome


func _on_finished(i: int) -> void:
	if not _checks:
		_label.text = str(state)
		return
	_check_choice(i)
	_next_check()


# --- Проверки -----------------------------------------------------------------------------------

func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("event: " + what)


## Без экрана: суммы по настроению, «хочу X» не как прошлая игра, пилюли у каждого варианта
## с последствиями, ограничения одной пилюлей.
func _static_checks() -> void:
	var pub := Events.find(defs, &"publisher_offer")
	_expect(pub != null, "нет оффера издателя")
	if pub == null:
		return
	rng.seed = 3
	var calm := Events.resolve(pub, 0, _context(), meta)
	rng.seed = 3
	var warm := Events.resolve(pub, 1, _context(), meta)
	rng.seed = 3
	var cold := Events.resolve(pub, -1, _context(), meta)
	var m0 := calm.choices[0].effects[0].amount
	_expect(warm.choices[0].effects[0].amount == int(roundf(m0 * (1.0 + meta.mood_offer) / 100.0)) * 100,
			"настроение +1: %d при %d" % [warm.choices[0].effects[0].amount, m0])
	_expect(cold.choices[0].effects[0].amount < m0, "настроение −1 уменьшает аванс")
	_expect(warm.line != calm.line and cold.line != calm.line, "реплика по настроению")
	for seed_i in 20:
		rng.seed = seed_i
		var o := Events.resolve(pub, 0, _context(), meta)
		for e in o.choices[0].effects:
			if e.kind == EffectDef.Kind.RESTRICT_GENRE:
				_expect(e.value != G.SHOOTER, "«хочу X» совпал с прошлой игрой")
		var locks := o.choices[0].pills.filter(func(p: Events.Pill) -> bool: return p.tone == Events.Tone.LOCK)
		_expect(locks.size() == 1, "ограничения одной пилюлей: %d" % locks.size())
		_expect(o.line.find("{") < 0, "подстановки в реплике: %s" % o.line)
	for d in defs:
		var o := Events.resolve(d, 0, _context(), meta)
		_expect(o.choices.size() >= 2 and o.choices.size() <= 3, "%s: вариантов %d" % [d.id, o.choices.size()])
		for c in o.choices:
			_expect(c.effects.is_empty() or not c.pills.is_empty(), "%s: «%s» без пилюль" % [d.id, c.text])
			_expect(c.text.find("{") < 0, "%s: подстановки в «%s»" % [d.id, c.text])


func _next_check() -> void:
	if _queue.is_empty():
		AutoTest.note("event: проверено вариантов %d" % (defs.reduce(func(a: int, d: EventDef) -> int: return a + d.choices.size(), 0)))
		AutoTest.fulfill("event checks")
		return
	var q: Vector2i = _queue.pop_front()
	state = EventState.new()
	event_id = String(defs[q.x].id)
	_launch()
	card.index = q.y
	card.confirm()


## После ответа: деньги и репутация как в выпавшей ветке, остальное в состоянии.
func _check_choice(i: int) -> void:
	var c := offer.choices[i]
	var effects := c.effects
	if c.coin and _outcome.find("не повезло") >= 0:
		effects = c.lose_effects
	_expect(not c.coin or _outcome != "", "%s: монетка без исхода" % offer.def.id)
	var money := 0
	var rep := 0.0
	var locks := 0
	var shares := 0
	var ending: StringName = &""
	for e in effects:
		match e.kind:
			EffectDef.Kind.MONEY:
				money += e.amount
			EffectDef.Kind.REPUTATION:
				rep += e.steps * meta.rep_step
			EffectDef.Kind.RESTRICT_GENRE, EffectDef.Kind.RESTRICT_SETTING, EffectDef.Kind.RESTRICT_TECH, EffectDef.Kind.RESTRICT_SEQUEL:
				locks += 1
			EffectDef.Kind.TAIL_SHARE:
				shares += 1
			EffectDef.Kind.ENDING:
				ending = e.id
	var what := "%s/%d" % [offer.def.id, i]
	_expect(wallet.cash - _before_cash == money, "%s: деньги %+d, ждали %+d" % [what, wallet.cash - _before_cash, money])
	_expect(is_equal_approx(market.reputation - _before_rep, rep), "%s: репутация %+.1f, ждали %+.1f" % [what, market.reputation - _before_rep, rep])
	_expect(state.restrictions.size() == locks, "%s: ограничений %d, ждали %d" % [what, state.restrictions.size(), locks])
	_expect(state.tail_shares.size() == shares, "%s: долей %d" % [what, state.tail_shares.size()])
	_expect(state.ending == ending, "%s: концовка %s" % [what, state.ending])
	_expect(state.mood(offer.character.id) == clampi(c.mood_delta, -1, 1), "%s: настроение %d" % [what, state.mood(offer.character.id)])
	_expect(state.shown.get(offer.def.id, 0) == 1, "%s: не отмечена показанной" % what)
	AutoTest.note("event %s: «%s» %s → деньги %+d, R %+.1f, %s" % [what, c.text, _outcome, money, rep, state])
