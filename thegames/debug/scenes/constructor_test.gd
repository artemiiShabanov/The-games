extends Control
## Тестовая сцена конструктора (#23): экран с деньгами и открытыми карточками из раздела
## «Конструктор» дебаг-меню (деньги, релиз, всё открыто, сид). После «В разработку» показывает
## конфигурацию и списание из кошелька, A запускает снова. Под ботом: смета стартовой тройки,
## закрытая карточка держит кнопку, нехватка денег держит кнопку, подтверждение даёт
## конфигурацию с названием и ценой, R меняет название. Флаги: `--no-checks`, `--all-open`, `--cash=N`.

const SECTION: StringName = &"Конструктор"
const SCENE := preload("res://scenes/constructor.tscn")

var economy: EconomyTuning
var cash := 36000
var release := 2
var all_open := false
var seed_value := 1
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
	constructor.setup(genres, techs, settings, wallet.cash, release, seed_value)
	constructor.game_configured.connect(_on_configured)
	add_child(constructor)


func _on_configured(c: GameConfig) -> void:
	wallet.spend(c.total_cost(), &"release")
	constructor.queue_free()
	constructor = null
	_show("В разработку: %s\nкошелёк %s → %s\n\nA снова, F1 меню" % [c, cash, wallet.cash])


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
	constructor.focus(3)
	constructor.confirm()
	_expect(got.is_empty(), "подтверждение прошло с закрытой карточкой")
	constructor.focus(1)
	constructor.move(-1)
	_expect(constructor.selection_open(), "возврат на открытую")
	# Денег не хватает.
	constructor.cash = 5000
	constructor.focus(3)
	_expect(not constructor.estimate.affordable and constructor.estimate.shortfall() == 2000, "нехватка: %s" % constructor.estimate)
	constructor.confirm()
	_expect(got.is_empty(), "подтверждение прошло без денег")
	constructor.cash = cash
	constructor.focus(0)
	constructor.focus(3)
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
	AutoTest.fulfill("constructor checks")
	AutoTest.note("constructor checks done")
