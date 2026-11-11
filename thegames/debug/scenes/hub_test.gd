extends Control
## Тестовая сцена главного экрана забега (#77, #78): настоящий `RunState` проходит `--past=N`
## релизов быстрыми конфигурациями (разработка, отклик, лента, фаза студии, покупка первой
## прокачки), затем `RunHub`. Раздел «Главный экран» дебаг-меню: «Заново», окна. Под ботом:
## окно денег сходится с кошельком, окно прокачки по порядку покупки, панель релиза с лентой,
## «Новая игра» шлёт сигнал. `--no-checks [--pop=money|upgrades|release]` держит экран для
## скриншота.

const SECTION: StringName = &"Главный экран"

var run: RunState
var hub: RunHub
var past := 3
var _checks := false
var _pop := ""
var _started := false


func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)
	if AutoTest.enabled:
		var args := AutoTest.parse_args(OS.get_cmdline_user_args())
		past = int(str(args.get("past", past)))
		_pop = str(args.get("pop", ""))
		if args.has("no-checks"):
			AutoTest.bot_mode = AutoTest.BotMode.OFF
		else:
			_checks = true
			Debug.skip_cards = true
			AutoTest.require("hub checks")
	Debug.add_action(SECTION, "Заново", _open)
	Debug.add_action(SECTION, "Окно денег", func() -> void: hub.open_money())
	Debug.add_action(SECTION, "Окно прокачки", func() -> void: hub.open_upgrades())
	Debug.add_action(SECTION, "Последний релиз", func() -> void: hub.open_release(0))
	_open()


func _exit_tree() -> void:
	Debug.clear_section(SECTION)


func _open() -> void:
	if hub != null:
		hub.queue_free()
	run = _make_run(past)
	hub = RunHub.new()
	hub.setup(run)
	hub.new_game.connect(func() -> void: _started = true)
	add_child(hub)
	if _checks:
		_check.call_deferred()
	elif _pop != "":
		_show_pop.call_deferred()


func _show_pop() -> void:
	match _pop:
		"money":
			hub.open_money()
		"upgrades":
			hub.open_upgrades()
		"release":
			hub.open_release(0)


## Забег, прошедший `n` релизов: каждый как в петле, первая прокачка предложения куплена.
static func _make_run(n: int) -> RunState:
	var r := RunState.start(1, true)
	r.studio_name = "Тихая Лампа"
	r.studio_logo = StudioLogo.new()
	r.wallet.cash = 60000
	for i in n:
		r.prepare_release()
		var config := r.first_config()
		var record := r.start_development(config)
		for k in r.last_plan.size():
			record.add_sprint(k != 1)
		r.score_release(record)
		r.build_feed(record)
		var report := r.settle(record)
		if not report.offer.is_empty():
			StudioPhase.buy(report.offer[0], r.wallet, r.upkeep, r.studio, r.economy)
		r.close_release(record, report)
	r.prepare_release()
	return r


func _check() -> void:
	_expect(hub.focus == hub._new_index, "фокус на «Новой игре»")
	# Окно денег: сумма строк истории сходится с изменением кошелька.
	var sum := 0
	for e in run.wallet.history:
		sum += int(e["delta"])
	# Кошелёк поставлен в 60 000 до первого релиза: всё, что после, есть в истории.
	_expect(sum == run.wallet.cash - 60000, "история денег: сумма %d, кошелёк %d" % [sum, run.wallet.cash])
	hub.open_money()
	_expect(hub.window == RunHub.Pop.MONEY and hub._window_node != null, "окно денег открыто")
	hub.open_money()
	_expect(hub.window == RunHub.Pop.NONE, "окно денег закрыто повторным нажатием")
	hub.open_upgrades()
	_expect(hub.window == RunHub.Pop.UPGRADES, "окно прокачки открыто")
	_expect(run.studio.bought_release.size() == run.studio.upgrade_ids.size() and run.studio.release_of(0) == 1,
			"релизы покупки %s" % [run.studio.bought_release])
	hub.open_release(0)
	_expect(hub.window == RunHub.Pop.RELEASE and hub._feed != null, "панель релиза открыта")
	# Лента прошлого релиза собирается заново той же.
	var a := run.build_feed(run.records[-1])
	var b := run.build_feed(run.records[-1])
	_expect(a.items.size() == b.items.size() and a.tag == b.tag, "лента релиза повторяется")
	hub.start_new_game()
	_expect(_started and hub.window == RunHub.Pop.NONE, "«Новая игра» закрыла окно и дала сигнал")
	AutoTest.note("hub: релизов %d, строк истории %d, прокачек %d" % [run.records.size(), run.wallet.history.size(),
			run.studio.upgrade_ids.size()])
	AutoTest.fulfill("hub checks")


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("hub: " + what)
