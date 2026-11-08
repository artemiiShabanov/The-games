extends Control
## Тестовая сцена конструктора (#23): экран с деньгами и открытыми карточками из раздела
## «Конструктор» дебаг-меню (деньги, релиз, всё открыто, сид). После «В разработку» показывает
## конфигурацию и списание из кошелька, A запускает снова. Под ботом: смета стартовой тройки,
## закрытая карточка держит кнопку, нехватка денег держит кнопку, подтверждение даёт
## конфигурацию с названием и ценой, R меняет название; с сиквелами и ремейками (#24) сначала
## экран основы `BaseChooser`: состав колонок, закрытые ремейки, затем конструктор с локами
## жанра и сеттинга, названием по франшизе, технологией оригинала у ремейка, запись с частью
## и родителем. Флаги: `--no-checks`, `--all-open`, `--cash=N`, `--franchise` (сиквелы и
## ремейки с двумя прошлыми играми), `--base=K,I` (под скриншот: колонка и карточка основы;
## без него экран основы стоит).

const SECTION: StringName = &"Конструктор"
const SCENE := preload("res://scenes/constructor.tscn")
const CHOOSER_PATH := "res://scenes/base_chooser.tscn"

var economy: EconomyTuning
var cash := 36000
var release := 2
var all_open := false
var seed_value := 1
var sequels := false
var remakes := false
var past_count := 2
var manager := false
var insider := false
var constructor: Constructor
var chooser: BaseChooser
var wallet: Wallet
var past: Array[GameRecord] = []
var _label: Label
var _checked := false


func _ready() -> void:
	economy = EconomyTuning.load_default()
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
	Debug.add_number(SECTION, "Деньги", func() -> int: return cash, func(v: float) -> void: cash = int(v), -10000, 200000, 1000)
	Debug.add_number(SECTION, "Релиз", func() -> int: return release, func(v: float) -> void: release = int(v), 1, 13, 1)
	Debug.add_toggle(SECTION, "Всё открыто", func() -> bool: return all_open, func(v: bool) -> void: all_open = v)
	Debug.add_number(SECTION, "Сид", func() -> int: return seed_value, func(v: float) -> void: seed_value = int(v), 1, 999, 1)
	Debug.add_toggle(SECTION, "Сиквелы открыты", func() -> bool: return sequels, func(v: bool) -> void: sequels = v)
	Debug.add_toggle(SECTION, "Ремейки открыты", func() -> bool: return remakes, func(v: bool) -> void: remakes = v)
	Debug.add_number(SECTION, "Прошлых игр", func() -> int: return past_count, func(v: float) -> void: past_count = int(v), 0, 6, 1)
	Debug.add_toggle(SECTION, "Менеджер (−10 %)", func() -> bool: return manager, func(v: bool) -> void: manager = v)
	Debug.add_toggle(SECTION, "Инсайдер (тренд)", func() -> bool: return insider, func(v: bool) -> void: insider = v)
	Debug.add_action(SECTION, "Открыть конструктор", _launch)
	Debug.add_action(SECTION, "Собрать без экрана", func() -> void:
		var c := Constructor.quick_config(Game.Genre.PLATFORMER, Game.Tech.BIT8, Game.Setting.PIRATES, economy, seed_value)
		AutoTest.note("quick config: %s" % c)
		_show("Без экрана: %s" % c))
	Debug.watch("смета", func() -> String: return str(constructor.estimate) if constructor and constructor.estimate else "")
	if AutoTest.enabled:
		# `--no-checks` для скриншотов, `--all-open` открывает все карточки, `--cash=N` деньги.
		var args := AutoTest.parse_args(OS.get_cmdline_user_args())
		all_open = args.has("all-open")
		if args.has("cash"):
			cash = int(args["cash"])
		if args.has("franchise"):
			sequels = true
			remakes = true
		if args.has("no-checks"):
			_checked = true
		else:
			Debug.skip_cards = true
			AutoTest.require("constructor checks")
	_launch()


func _exit_tree() -> void:
	Debug.clear_section(SECTION)


func _unlocked() -> Array:
	var genres: Array[Game.Genre] = [Game.Genre.PLATFORMER]
	var techs: Array[Game.Tech] = [Game.Tech.BIT8]
	var settings: Array[Game.Setting] = [Game.Setting.PIRATES]
	if all_open:
		genres.assign(Game.Genre.values())
		techs.assign(Game.Tech.values())
		settings.assign(Game.Setting.values())
	return [genres, techs, settings]


## С открытыми сиквелами или ремейками сначала экран основы, иначе сразу конструктор.
func _launch() -> void:
	_clear()
	wallet = Wallet.new(cash)
	past = _make_past()
	if sequels or remakes:
		chooser = (load(CHOOSER_PATH) as PackedScene).instantiate() as BaseChooser
		chooser.setup(past, _unlocked()[1], sequels, remakes, wallet.cash, release)
		chooser.base_chosen.connect(_on_base_chosen)
		add_child(chooser)
		if AutoTest.enabled:
			var args := AutoTest.parse_args(OS.get_cmdline_user_args())
			if args.has("base"):
				var parts := str(args["base"]).split(",")
				chooser.focus(int(parts[0]))
				chooser.move(int(parts[1]) if parts.size() > 1 else 0)
				chooser.confirm()
	else:
		_open_constructor(null)


func _on_base_chosen(o: BaseOption) -> void:
	if chooser != null:
		chooser.queue_free()
		chooser = null
	_open_constructor(o)


## Рынок для подсказок: тренд платформер и космос, платформер недавно был, пираты надоели.
func _make_market() -> MarketState:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var m := MarketState.create(SuccessTuning.load_default(), rng, true)
	m.trend_genre = Game.Genre.PLATFORMER
	m.trend_setting = Game.Setting.SPACE
	m.saturation_genre[Game.Genre.PLATFORMER] = 0.4
	m.saturation_setting[Game.Setting.PIRATES] = 0.7
	return m


func _open_constructor(o: BaseOption) -> void:
	constructor = SCENE.instantiate() as Constructor
	var u := _unlocked()
	constructor.setup(u[0], u[1], u[2], wallet.cash, release, seed_value, economy.manager_discount if manager else 0.0, o)
	constructor.set_market(_make_market(), SuccessTuning.load_default(), insider)
	constructor.game_configured.connect(_on_configured)
	add_child(constructor)


func _clear() -> void:
	_label.visible = false
	if constructor != null:
		constructor.queue_free()
		constructor = null
	if chooser != null:
		chooser.queue_free()
		chooser = null


## Прошлые игры забега: платформер 8-bit пираты и его сиквел, затем шутер, с оценками критиков.
func _make_past() -> Array[GameRecord]:
	var out: Array[GameRecord] = []
	for i in past_count:
		var genre := Game.Genre.PLATFORMER if i % 3 != 2 else Game.Genre.SHOOTER
		var r := GameRecord.create(genre, Game.Tech.BIT8, 100 + i, "Пираты на платформах" if genre == Game.Genre.PLATFORMER else "Корсары под огнём", Game.Setting.PIRATES)
		if i % 3 == 1 and not out.is_empty():
			r.parent = out[i - 1]
			r.part = out[i - 1].part + 1
			r.title = "%s %d" % [r.parent.franchise_title(), r.part]
		r.score = ReleaseScore.new()
		r.score.critics = 6.0 + i * 0.7
		out.append(r)
	return out


func _on_configured(c: GameConfig) -> void:
	wallet.spend(c.total_cost(), &"release")
	constructor.queue_free()
	constructor = null
	_show("В разработку: %s\nзапись: %s\nкошелёк %s → %s\n\nA снова, F1 меню" % [c, c.to_record(1), cash, wallet.cash])


func _show(text: String) -> void:
	_label.text = text
	_label.visible = true


func _unhandled_input(event: InputEvent) -> void:
	if constructor == null and chooser == null and GameInput.is_a(event):
		_launch()


func _process(_delta: float) -> void:
	if AutoTest.enabled and not _checked and constructor != null:
		_checked = true
		_run_checks()


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("constructor: " + what)


func _run_checks() -> void:
	var e := constructor.estimate
	_expect(e != null and e.sprints == 5 and e.sprint_price == 1400 and e.total == 7000 and e.remainder == cash - 7000,
			"смета стартовой тройки: %s" % e)
	_expect(constructor.title != "", "название пустое")
	var t0 := constructor.title
	constructor.regenerate_title()
	_expect(constructor.title != t0, "R не поменял название")
	# Закрытая карточка: фокус на неё встаёт, кнопка закрыта.
	constructor.focus(1)
	constructor.move(1)
	_expect(constructor.index[1] == 2 and not constructor.selection_open(), "закрытая технология не выбрана")
	var got: Array = []
	constructor.game_configured.connect(func(c: GameConfig) -> void: got.append(c))
	constructor.focus(Constructor.ROW_BUTTON)
	constructor.confirm()
	_expect(got.is_empty(), "подтверждение прошло с закрытой карточкой")
	constructor.focus(1)
	constructor.move(-1)
	_expect(constructor.selection_open(), "возврат на открытую")
	# Денег не хватает.
	constructor.cash = 5000
	constructor.focus(Constructor.ROW_BUTTON)
	_expect(not constructor.estimate.affordable and constructor.estimate.shortfall() == 2000, "нехватка: %s" % constructor.estimate)
	constructor.confirm()
	_expect(got.is_empty(), "подтверждение прошло без денег")
	constructor.cash = cash
	constructor.focus(0)
	constructor.focus(Constructor.ROW_BUTTON)
	constructor.confirm()
	_expect(got.size() == 1, "подтверждение не отдало конфигурацию")
	if got.size() == 1:
		var c: GameConfig = got[0]
		_expect(c.sprints == 5 and c.sprint_cost == 1400 and c.title == constructor.title if constructor else true,
				"конфигурация: %s" % c)
		_expect(wallet.cash == cash - 7000, "кошелёк после старта %d" % wallet.cash)
	var q := Constructor.quick_config(Game.Genre.SHOOTER, Game.Tech.ASCII, Game.Setting.SPACE, economy, 7)
	_expect(q.sprints == 4 and q.sprint_cost == 1160 and q.title != "", "quick_config: %s" % q)
	_expect(Style.format_money(12000) == "$ 12 000" and Style.format_money(-2600) == "− $ 2 600" and Style.format_money(900) == "$ 900",
			"формат денег: %s / %s" % [Style.format_money(12000), Style.format_money(-2600)])
	await _check_franchise()
	_check_effects()
	_check_mouse()
	AutoTest.fulfill("constructor checks")
	AutoTest.note("constructor checks done")


## Сиквелы и ремейки: одна технология, две прошлые игры (вторая сиквел первой), затем все
## технологии. Экран основы ведётся методами, выбор сразу через `confirm(option)`.
func _check_franchise() -> void:
	sequels = true
	remakes = true
	past_count = 2
	_launch()
	_expect(chooser != null and constructor == null, "экран основы не открылся")
	_expect(chooser.kinds.size() == 3 and chooser.options[0].size() == 1 and chooser.options[1].size() == 2
			and chooser.options[2].size() == 2, "колонки основы: %s" % [chooser.options])
	_expect((chooser.options[1][0] as BaseOption).parent == past[1], "порядок основ: последняя игра первой")
	for o in chooser.options[2]:
		_expect(not (o as BaseOption).open and (o as BaseOption).lock_reason == "нужна вторая технология", "ремейк при одной технологии открыт")
	# Закрытый ремейк не выбирается, сиквел сиквела выбирается.
	chooser.focus(2)
	chooser.confirm()
	_expect(constructor == null, "закрытый ремейк прошёл")
	chooser.focus(1)
	chooser.confirm()
	await get_tree().process_frame
	await get_tree().process_frame
	var c := constructor
	_expect(c != null and chooser == null, "конструктор после выбора сиквела не открылся")
	_expect(c.title == "Пираты на платформах 3", "название сиквела «%s»" % c.title)
	_expect(c.is_locked_column(0) and c.is_locked_column(2) and not c.is_locked_column(1), "локи сиквела")
	_expect(c.index[0] == 0 and c.index[2] == 0 and c.selection_open(), "жанр и сеттинг оригинала не выбраны")
	var t0 := c.title
	c.regenerate_title()
	_expect(c.title == t0, "R поменял название сиквела")
	c.focus(0)
	c.move(1)
	_expect(c.index[0] == 0, "залоченный жанр сдвинулся")
	var got: Array = []
	c.game_configured.connect(func(cfg: GameConfig) -> void: got.append(cfg))
	c.focus(Constructor.ROW_BUTTON)
	c.confirm()
	_expect(got.size() == 1, "сиквел не ушёл в разработку")
	if got.size() == 1:
		var cfg: GameConfig = got[0]
		var rec := cfg.to_record(5)
		_expect(cfg.kind == GameConfig.Kind.SEQUEL and cfg.parent == past[1] and rec.part == 3 and rec.parent == past[1]
				and not rec.remake and rec.franchise_title() == "Пираты на платформах", "запись сиквела: %s, часть %d" % [rec, rec.part])
	# Ремейк со всеми технологиями: технология оригинала закрыта, выбор уходит на другую.
	all_open = true
	_launch()
	_expect((chooser.options[2][0] as BaseOption).open, "ремейк закрыт при всех технологиях")
	chooser.confirm(chooser.options[2][0])
	await get_tree().process_frame
	await get_tree().process_frame
	c = constructor
	_expect(c != null and c.title == "Пираты на платформах 2: ремейк", "название ремейка «%s»" % (c.title if c else ""))
	_expect(c.selected_entry(1).value != int(Game.Tech.BIT8) and c.selection_open(), "технология ремейка %s" % c.selected_entry(1).title)
	_expect(not c.is_unlocked(1, c.catalogs[1].index_of(int(Game.Tech.BIT8))), "технология оригинала открыта у ремейка")
	got.clear()
	c.game_configured.connect(func(cfg: GameConfig) -> void: got.append(cfg))
	c.focus(Constructor.ROW_BUTTON)
	c.confirm()
	_expect(got.size() == 1, "ремейк не ушёл в разработку")
	if got.size() == 1:
		var rec: GameRecord = (got[0] as GameConfig).to_record(6)
		_expect(rec.remake and rec.parent == past[1] and rec.part == 2 and rec.genre == Game.Genre.PLATFORMER, "запись ремейка: %s" % rec)
	# Новая игра через экран основы: ничего не залочено, название своё.
	_launch()
	chooser.confirm(chooser.options[0][0])
	await get_tree().process_frame
	await get_tree().process_frame
	c = constructor
	_expect(c != null and c.base != null and c.base.kind == GameConfig.Kind.NEW and not c.is_locked_column(0)
			and c.is_unlocked(1, c.catalogs[1].index_of(int(Game.Tech.BIT8))), "новая игра после основы")
	all_open = false
	sequels = false
	remakes = false


## Менеджер и инсайдер (#29): скидка в смете, метки рынка на карточках.
func _check_effects() -> void:
	_expect(constructor.market_tag(0, Game.Genre.PLATFORMER) == "недавно было"
			and constructor.market_tag(2, Game.Setting.PIRATES) == "надоело"
			and constructor.market_tag(2, Game.Setting.SPACE) == "", "метки без инсайдера: %s" % [constructor.market_tags])
	manager = true
	insider = true
	_launch()
	var e := constructor.estimate
	_expect(e.sprint_price == 1260 and e.total == 6300, "смета с менеджером: %s" % e)
	_expect(constructor.market_tag(0, Game.Genre.PLATFORMER) == "в тренде · недавно было"
			and constructor.market_tag(2, Game.Setting.SPACE) == "в тренде", "метки с инсайдером: %s" % [constructor.market_tags])
	manager = false
	insider = false


## Мышь (#43): клик по карточке выбирает её и колонку, колесо листает колонку под курсором,
## клик по кнопке отдаёт конфигурацию. События синтетические, координаты из прямоугольников.
func _check_mouse() -> void:
	all_open = true
	_launch()
	var c := constructor
	var card: Control = c._cards[2][1]
	var ev := InputEventMouseButton.new()
	ev.button_index = MOUSE_BUTTON_LEFT
	ev.pressed = true
	ev.position = MouseUi.rect_of(card).get_center()
	c._unhandled_input(ev)
	_expect(c.focus_row == 2 and c.index[2] == 1, "клик по карточке: колонка %d, индекс %d" % [c.focus_row, c.index[2]])
	var wheel := InputEventMouseButton.new()
	wheel.button_index = MOUSE_BUTTON_WHEEL_DOWN
	wheel.pressed = true
	wheel.position = MouseUi.rect_of(c._cards[1][0]).get_center()
	c._unhandled_input(wheel)
	_expect(c.focus_row == 1 and c.index[1] == 1, "колесо над технологией: индекс %d" % c.index[1])
	var got: Array = []
	c.game_configured.connect(func(cfg: GameConfig) -> void: got.append(cfg))
	var click := InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	click.pressed = true
	click.position = MouseUi.rect_of(c._button).get_center()
	c._unhandled_input(click)
	_expect(got.size() == 1, "клик по кнопке не отдал конфигурацию")
	all_open = false
