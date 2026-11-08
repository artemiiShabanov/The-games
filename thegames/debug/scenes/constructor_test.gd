extends Control
## Тестовая сцена конструктора (#23): экран с деньгами и открытыми карточками из раздела
## «Конструктор» дебаг-меню (деньги, релиз, всё открыто, сид). После «В разработку» показывает
## конфигурацию и списание из кошелька, A запускает снова. Под ботом: смета стартовой тройки,
## закрытая карточка держит кнопку, нехватка денег держит кнопку, подтверждение даёт
## конфигурацию с названием и ценой, R меняет название; с сиквелами и ремейками (#24): состав
## колонки «Основа», локи жанра и сеттинга, название по франшизе, технология оригинала у
## ремейка, запись с частью и родителем. Флаги: `--no-checks`, `--all-open`, `--cash=N`,
## `--franchise` (сиквелы и ремейки с двумя прошлыми играми).

const SECTION: StringName = &"Конструктор"
const SCENE := preload("res://scenes/constructor.tscn")

var economy: EconomyTuning
var cash := 36000
var release := 2
var all_open := false
var seed_value := 1
var sequels := false
var remakes := false
var past_count := 2
var constructor: Constructor
var wallet: Wallet
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
			AutoTest.require("constructor checks")
	_launch()


func _exit_tree() -> void:
	Debug.clear_section(SECTION)


func _launch() -> void:
	_label.visible = false
	if constructor != null:
		constructor.queue_free()
	wallet = Wallet.new(cash)
	constructor = SCENE.instantiate() as Constructor
	var genres: Array[Game.Genre] = [Game.Genre.PLATFORMER]
	var techs: Array[Game.Tech] = [Game.Tech.BIT8]
	var settings: Array[Game.Setting] = [Game.Setting.PIRATES]
	if all_open:
		genres.assign(Game.Genre.values())
		techs.assign(Game.Tech.values())
		settings.assign(Game.Setting.values())
	constructor.setup(genres, techs, settings, wallet.cash, release, seed_value, 0.0, _make_past(), sequels, remakes)
	constructor.game_configured.connect(_on_configured)
	add_child(constructor)
	if AutoTest.enabled:
		# `--base=N` под скриншот: выбрать N-ю основу (сиквел или ремейк).
		var args := AutoTest.parse_args(OS.get_cmdline_user_args())
		if args.has("base") and constructor.has_base():
			constructor.focus(Constructor.ROW_BASE)
			constructor.move(int(str(args["base"])))


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
	if constructor == null and GameInput.is_a(event):
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
	_check_franchise()
	AutoTest.fulfill("constructor checks")
	AutoTest.note("constructor checks done")


## Сиквелы и ремейки: одна технология, две прошлые игры (вторая сиквел первой), затем все
## технологии.
func _check_franchise() -> void:
	sequels = true
	remakes = true
	past_count = 2
	_launch()
	var c := constructor
	_expect(c.has_base() and c.base_options.size() == 5, "основ %d" % c.base_options.size())
	_expect(c.base_options[0].kind == GameConfig.Kind.NEW and c.base_options[1].kind == GameConfig.Kind.SEQUEL
			and c.base_options[1].parent == c.past[1], "порядок основ: последняя игра первой")
	for o in c.base_options:
		if o.kind == GameConfig.Kind.REMAKE:
			_expect(not o.open and o.lock_reason == "нужна вторая технология", "ремейк при одной технологии открыт")
	# Сиквел сиквела: номер растёт, жанр и сеттинг залочены, R не работает.
	c.focus(Constructor.ROW_BASE)
	c.move(1)
	_expect(c.title == "Пираты на платформах 3", "название сиквела «%s»" % c.title)
	_expect(c.is_locked_column(0) and c.is_locked_column(2) and not c.is_locked_column(1), "локи сиквела")
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
		_expect(cfg.kind == GameConfig.Kind.SEQUEL and cfg.parent == c.past[1] and rec.part == 3 and rec.parent == c.past[1]
				and not rec.remake and rec.franchise_title() == "Пираты на платформах", "запись сиквела: %s, часть %d" % [rec, rec.part])
	# Ремейк со всеми технологиями: технология оригинала закрыта, выбор уходит на другую.
	all_open = true
	_launch()
	c = constructor
	c.focus(Constructor.ROW_BASE)
	c.move(2)
	_expect(c.base().kind == GameConfig.Kind.REMAKE and c.base().open, "ремейк закрыт при всех технологиях")
	_expect(c.title == "Пираты на платформах 2: ремейк", "название ремейка «%s»" % c.title)
	_expect(c.selected_entry(1).value != int(Game.Tech.BIT8) and c.selection_open(), "технология ремейка %s" % c.selected_entry(1).title)
	_expect(not c.is_unlocked(1, c.catalogs[1].index_of(int(Game.Tech.BIT8))), "технология оригинала открыта у ремейка")
	got.clear()
	c.game_configured.connect(func(cfg: GameConfig) -> void: got.append(cfg))
	c.focus(Constructor.ROW_BUTTON)
	c.confirm()
	_expect(got.size() == 1, "ремейк не ушёл в разработку")
	if got.size() == 1:
		var rec: GameRecord = (got[0] as GameConfig).to_record(6)
		_expect(rec.remake and rec.parent == c.past[1] and rec.part == 2 and rec.genre == Game.Genre.PLATFORMER, "запись ремейка: %s" % rec)
	# Новая игра после ремейка: технология оригинала снова открыта, название своё.
	c.focus(Constructor.ROW_BASE)
	c.move(-2)
	_expect(c.base().kind == GameConfig.Kind.NEW and c.is_unlocked(1, c.catalogs[1].index_of(int(Game.Tech.BIT8)))
			and not c.is_locked_column(0), "возврат к новой игре")
	all_open = false
	sequels = false
	remakes = false
