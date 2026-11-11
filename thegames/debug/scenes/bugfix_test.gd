extends Control
## Тестовая сцена спринта багфикса (#27): запись с багами из раздела «Багфикс» дебаг-меню
## (число багов, деньги, сид), предложение, при согласии списание и случайная аспектная
## мини-игра через раннер, затем карточка «починено». Под ботом: отказ, покупка с WIN чинит
## половину багов, покупка с LOSE не чинит и не добавляет, нехватка денег держит кнопку, с
## «Отделом QA» (#29) второе предложение после первого спринта, есть баги или нет.

const SECTION: StringName = &"Багфикс"
const OFFER_PATH := "res://scenes/bugfix_offer.tscn"

var bugs := 3
var cash := 20000
var seed_value := 1
var qa := false
var state: StudioState
var offers_shown := 0
var economy: EconomyTuning
var catalog: BugCatalog
var pool: Array[MinigameDef] = []
var record: GameRecord
var wallet: Wallet
var offer: BugfixOffer
var runner: SprintRunner
var rng := RandomNumberGenerator.new()
var _label: Label
var _phase := 0
var _fixed: Array[StringName] = []
var _before := 0


func _ready() -> void:
	economy = EconomyTuning.load_default()
	catalog = BugCatalog.load_default()
	for d in MinigamePool.load_all():
		if d.scene != null:
			pool.append(d)
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	_label = Label.new()
	_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	_label.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_label.grow_vertical = Control.GROW_DIRECTION_BOTH
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.add_theme_font_size_override("font_size", Style.FONT_H2)
	_label.visible = false
	add_child(_label)
	Debug.add_number(SECTION, "Багов", func() -> int: return bugs, func(v: float) -> void: bugs = int(v), 0, 6, 1)
	Debug.add_number(SECTION, "Деньги", func() -> int: return cash, func(v: float) -> void: cash = int(v), 0, 100000, 1000)
	Debug.add_number(SECTION, "Сид", func() -> int: return seed_value, func(v: float) -> void: seed_value = int(v), 1, 999, 1)
	Debug.add_toggle(SECTION, "Отдел QA", func() -> bool: return qa, func(v: bool) -> void: qa = v)
	Debug.add_action(SECTION, "Новое предложение", _launch)
	Debug.watch("багфикс", func() -> String: return "%s, деньги %s" % [record.bug_ids, wallet] if record else "")
	if AutoTest.enabled:
		Debug.skip_cards = true
		if AutoTest.parse_args(OS.get_cmdline_user_args()).has("no-checks"):
			_phase = -1
			Debug.skip_cards = false
		else:
			AutoTest.require("bugfix checks")
	_launch()


func _exit_tree() -> void:
	Debug.clear_section(SECTION)


func _make_record() -> GameRecord:
	var rec := GameRecord.create(Game.Genre.PLATFORMER, Game.Tech.BIT8, seed_value, "Пираты на платформах", Game.Setting.PIRATES)
	for k in mini(bugs, catalog.bugs.size()):
		rec.add_bug(catalog.bugs[k].id)
	return rec


func _launch() -> void:
	_clear()
	rng.seed = seed_value
	record = _make_record()
	wallet = Wallet.new(cash)
	state = StudioState.new()
	if qa:
		state.buy(UpgradePool.find(UpgradePool.load_all(), &"qa"))
	offers_shown = 0
	_show_offer()


func _show_offer() -> void:
	offers_shown += 1
	offer = (load(OFFER_PATH) as PackedScene).instantiate() as BugfixOffer
	offer.setup(record, catalog, Bugfix.price(record, economy), wallet.cash)
	offer.accepted.connect(_on_accepted)
	offer.declined.connect(_on_declined)
	add_child(offer)


func _on_declined() -> void:
	_clear()
	_show("Отказались. Баги: %s\n\nA снова, F1 меню" % [record.bug_ids])


func _on_accepted() -> void:
	wallet.spend(Bugfix.price(record, economy), &"bugfix")
	_clear()
	var def := Bugfix.pick_minigame(pool, rng)
	runner = SprintRunner.new()
	runner.sprint_finished.connect(_on_sprint_finished)
	add_child(runner)
	runner.run(Bugfix.plan_for(def), 0.3, false, seed_value * 1000, "Багфикс")


func _on_sprint_finished(_def: MinigameDef, success: bool) -> void:
	_before = record.bug_ids.size()
	_fixed.clear()
	if success:
		_fixed = Bugfix.apply_fix(record, rng)
	await get_tree().process_frame
	if runner != null:
		runner.queue_free()
		runner = null
	var names: PackedStringArray = []
	for id in _fixed:
		var b := catalog.by_id(id)
		names.append(b.stamp_for(record.genre) if b != null else String(id))
	_show(("Починено: %s" % ", ".join(names) if success else "Провал: ничего не починено") +
			"\nОсталось багов: %d · деньги %s\n\nA снова, F1 меню" % [record.bug_ids.size(), wallet])
	# «Отдел QA»: второе предложение, есть баги или нет.
	if offers_shown < Bugfix.offers(state) and offer == null:
		_show_offer()
	if AutoTest.enabled and _phase > 0:
		await _check(success)


func _clear() -> void:
	_label.visible = false
	if offer != null:
		offer.queue_free()
		offer = null
	if runner != null:
		runner.queue_free()
		runner = null


func _show(text: String) -> void:
	_label.text = text
	_label.visible = true


func _unhandled_input(event: InputEvent) -> void:
	if offer == null and runner == null and GameInput.is_a(event):
		_launch()


func _process(_delta: float) -> void:
	if AutoTest.enabled and _phase == 0 and offer != null:
		_phase = 1
		_run_checks()


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("bugfix: " + what)


## Фаза 1: функции и отказ; затем покупка с WIN, потом с LOSE.
func _run_checks() -> void:
	_expect(Bugfix.price(record, economy) == 1400, "цена %d" % Bugfix.price(record, economy))
	_expect(Bugfix.fix_count(record) == 2, "починит %d из 3" % Bugfix.fix_count(record))
	var one := GameRecord.create(Game.Genre.PLATFORMER, Game.Tech.BIT8, 1)
	one.add_bug(catalog.bugs[0].id)
	_expect(Bugfix.fix_count(one) == 1, "один баг чинится")
	var d := Bugfix.pick_minigame(pool, rng)
	_expect(d != null and d.kind == MinigameDef.Kind.ASPECT and d.scene != null, "выбор мини-игры %s" % (d.id if d else ""))
	# Нехватка денег держит кнопку.
	var poor := (load(OFFER_PATH) as PackedScene).instantiate() as BugfixOffer
	poor.setup(record, catalog, 1400, 500)
	var got: Array[String] = []
	poor.accepted.connect(func() -> void: got.append("acc"))
	poor.declined.connect(func() -> void: got.append("dec"))
	add_child(poor)
	poor.set_focus_buy(true)
	poor.confirm()
	_expect(got.is_empty() and not poor.affordable(), "покупка без денег прошла")
	poor.decline()
	_expect(got == ["dec"], "отказ без денег")
	poor.queue_free()
	# Отказ в обычном предложении.
	var declined := [false]
	offer.declined.connect(func() -> void: declined[0] = true)
	offer.set_focus_buy(false)
	offer.confirm()
	_expect(declined[0], "отказ по кнопке")
	# Покупка с WIN.
	_phase = 2
	AutoTest.bot_mode = AutoTest.BotMode.WIN
	_launch()
	offer.confirm()
	_expect(wallet.cash == cash - 1400, "списание %d" % wallet.cash)


func _check(success: bool) -> void:
	match _phase:
		2:
			_expect(success, "WIN: мини-игра провалена")
			_expect(_fixed.size() == 2 and record.bug_ids.size() == 1, "WIN: починено %d, осталось %d" % [_fixed.size(), record.bug_ids.size()])
			_phase = 3
			AutoTest.bot_mode = AutoTest.BotMode.LOSE
			_launch()
			offer.confirm()
		3:
			_expect(not success, "LOSE: мини-игра выиграна")
			_expect(_fixed.is_empty() and record.bug_ids.size() == 3, "LOSE: починено %d, осталось %d" % [_fixed.size(), record.bug_ids.size()])
			# QA: два предложения, второе чинит оставшийся баг.
			_phase = 4
			qa = true
			AutoTest.bot_mode = AutoTest.BotMode.WIN
			_launch()
			offer.confirm()
		4:
			_expect(success and record.bug_ids.size() == 1, "QA первый: осталось %d" % record.bug_ids.size())
			_phase = 5
			_expect(offer != null and offers_shown == 2, "QA: второго предложения нет")
			if offer != null:
				offer.confirm()
		5:
			_expect(success and record.bug_ids.is_empty() and wallet.cash == cash - 2 * 1400, "QA второй: осталось %d, деньги %s" % [record.bug_ids.size(), wallet])
			_phase = 6
			await get_tree().process_frame
			_expect(offer == null, "QA: третье предложение")
			qa = false
			AutoTest.fulfill("bugfix checks")
			AutoTest.note("bugfix checks done")
