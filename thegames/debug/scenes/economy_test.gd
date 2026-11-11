extends Control
## Тестовая сцена экономики (#22): таблица цен по технологиям, смета выбранной тройки и план
## покупок модельного забега из `docs/specs/economy_model.md`. Стрелки меняют тройку, A
## покупает следующее из плана, B сбрасывает; то же в дебаг-меню, раздел «Экономика».
## Под ботом сверяет цены, стоимости двенадцати релизов, самую дорогую и дешёвую пары, рост
## содержания по плану и порог банкротства с таблицей модели.

const SECTION: StringName = &"Экономика"
const INK := Style.STUDIO_INK
const G := Game.Genre
const T := Game.Tech
const S := Game.Setting

## План покупок модели: вид, что. Содержание после каждой из таблицы «Хорошие руки».
const PLAN := [
	["genre", G.SHOOTER, 1050], ["cap", &"replay", 1200], ["tech", T.VECTOR, 1500],
	["cap", &"sequels", 1650], ["tech", T.LOWPOLY, 2350], ["genre", G.RACING, 2600], ["tech", T.THREED, 3500]]
## Двенадцать релизов модели: тройка и стоимость из таблицы (округлена до сотен).
const RELEASES := [
	[G.PLATFORMER, T.BIT8, S.PIRATES, 7000], [G.SHOOTER, T.BIT8, S.PIRATES, 7350],
	[G.PLATFORMER, T.BIT8, S.SPACE, 7700], [G.SHOOTER, T.VECTOR, S.SPACE, 4620],
	[G.PLATFORMER, T.BIT8, S.PIRATES, 7000], [G.PLATFORMER, T.VECTOR, S.CASTLES, 4200],
	[G.SHOOTER, T.LOWPOLY, S.CASTLES, 19300], [G.SHOOTER, T.BIT8, S.PIRATES, 7350],
	[G.RACING, T.LOWPOLY, S.SPACE, 21200], [G.PLATFORMER, T.LOWPOLY, S.PIRATES, 17500],
	[G.RACING, T.THREED, S.CASTLES, 29600], [G.SHOOTER, T.THREED, S.SPACE, 29600]]

var tuning: EconomyTuning
var genre := G.PLATFORMER
var tech := T.BIT8
var setting := S.PIRATES
var wallet: Wallet
var upkeep: Upkeep
var bought := 0
var _label: Label
var _checked := false


func _ready() -> void:
	tuning = EconomyTuning.load_default()
	_reset()
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	_label = Label.new()
	_label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_label.offset_left = 48
	_label.offset_top = 40
	_label.offset_right = -48
	_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_label.add_theme_font_size_override("font_size", 24)
	_label.add_theme_color_override("font_color", INK)
	var mono := SystemFont.new()
	mono.font_names = PackedStringArray(["Menlo", "Monaco", "Consolas", "DejaVu Sans Mono", "monospace"])
	_label.add_theme_font_override("font", mono)
	add_child(_label)
	Debug.add_choice(SECTION, "Жанр", Game.GENRE_NAMES,
			func() -> String: return Game.genre_name(genre),
			func(v: String) -> void:
				genre = Game.GENRE_NAMES.find(v) as G
				_refresh())
	Debug.add_choice(SECTION, "Технология", Game.TECH_NAMES,
			func() -> String: return Game.tech_name(tech),
			func(v: String) -> void:
				tech = Game.TECH_NAMES.find(v) as T
				_refresh())
	Debug.add_choice(SECTION, "Сеттинг", Game.SETTING_NAMES,
			func() -> String: return Game.setting_name(setting),
			func(v: String) -> void:
				setting = Game.SETTING_NAMES.find(v) as S
				_refresh())
	Debug.add_action(SECTION, "Купить следующее из плана", _buy_next)
	Debug.add_action(SECTION, "Сброс кошелька", func() -> void:
		_reset()
		_refresh())
	Debug.watch("деньги", func() -> String: return "%s, содержание %s" % [wallet, upkeep] if wallet else "")
	if AutoTest.enabled:
		AutoTest.require("economy checks")
	_refresh()


func _exit_tree() -> void:
	Debug.clear_section(SECTION)


func _reset() -> void:
	wallet = Wallet.new(tuning.start_cash)
	upkeep = Upkeep.new(tuning.upkeep_base)
	bought = 0


## Покупка по плану модели: списывает цену и добавляет надбавку к содержанию.
func _buy_next() -> void:
	if bought >= PLAN.size():
		return
	var item: Array = PLAN[bought]
	match item[0]:
		"genre":
			wallet.spend(tuning.genre_unlock_price, &"upgrade")
			upkeep.add(StringName("genre_%d" % int(item[1])), tuning.genre_unlock_upkeep)
		"tech":
			wallet.spend(tuning.unlock_price_by_tech[item[1]], &"upgrade")
			upkeep.add(StringName("tech_%d" % int(item[1])), tuning.unlock_upkeep_by_tech[item[1]])
		"cap":
			wallet.spend(tuning.capability_price(item[1]), &"upgrade")
			upkeep.add(item[1], tuning.capability_upkeep(item[1]))
	bought += 1
	_refresh()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(GameInput.RIGHT):
		tech = wrapi(tech + 1, 0, T.size()) as T
	elif event.is_action_pressed(GameInput.LEFT):
		tech = wrapi(tech - 1, 0, T.size()) as T
	elif event.is_action_pressed(GameInput.DOWN):
		genre = wrapi(genre + 1, 0, G.size()) as G
	elif event.is_action_pressed(GameInput.UP):
		genre = wrapi(genre - 1, 0, G.size()) as G
	elif event.is_action_pressed(GameInput.A):
		_buy_next()
		return
	elif event.is_action_pressed(GameInput.B):
		setting = wrapi(setting + 1, 0, S.size()) as S
	else:
		return
	_refresh()


func _process(_delta: float) -> void:
	if AutoTest.enabled and not _checked:
		_checked = true
		_run_checks()


func _refresh() -> void:
	var lines: PackedStringArray = []
	lines.append("Экономика   (← → технология, ↑ ↓ жанр, B сеттинг, A купить из плана)")
	lines.append("")
	lines.append("Технология        спринтов   цена спринта   релиз без множителей   открыть   содержание +")
	for t in T.values():
		lines.append("%-16s  %8d   %12d   %21d   %7d   %12d" % [Game.tech_name(t), tuning.sprints(t),
				tuning.sprint_price(G.PLATFORMER, t, S.PIRATES), tuning.release_cost(G.PLATFORMER, t, S.PIRATES),
				tuning.unlock_price_by_tech[t], tuning.unlock_upkeep_by_tech[t]])
	lines.append("")
	lines.append("Смета: %s × %s × %s = %d спринтов × %d = %d  (с менеджером %d)" % [
			Game.genre_name(genre), Game.tech_name(tech), Game.setting_name(setting), tuning.sprints(tech),
			tuning.sprint_price(genre, tech, setting), tuning.release_cost(genre, tech, setting),
			tuning.release_cost(genre, tech, setting, tuning.manager_discount)])
	lines.append("")
	lines.append("Кошелёк %s, содержание %s за релиз, куплено по плану %d из %d" % [wallet, upkeep, bought, PLAN.size()])
	var cheapest := tuning.cheapest_release([G.PLATFORMER], [T.BIT8], [S.PIRATES])
	lines.append("самый дешёвый открытый релиз %d, банкрот: %s" % [cheapest, tuning.is_bankrupt(wallet.cash, cheapest)])
	_label.text = "\n".join(lines)


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("economy: " + what)


func _run_checks() -> void:
	_expect(tuning.start_cash == 36000, "стартовый бюджет %d" % tuning.start_cash)
	var prices := [1000, 1400, 1900, 2500, 3200]
	var costs := [4000, 7000, 11400, 17500, 25600]
	for t in T.values():
		_expect(tuning.sprint_price(G.PLATFORMER, t, S.PIRATES) == prices[t], "цена спринта %s" % Game.tech_name(t))
		_expect(tuning.release_cost(G.PLATFORMER, t, S.PIRATES) == costs[t], "релиз %s" % Game.tech_name(t))
	# Двенадцать релизов модели: таблица округлена до сотен, цена спринта до 10.
	for r in RELEASES:
		var c := tuning.release_cost(r[0], r[1], r[2])
		_expect(absi(c - int(r[3])) <= 50, "релиз %s×%s×%s стоит %d, в модели %d" % [
				Game.genre_name(r[0]), Game.tech_name(r[1]), Game.setting_name(r[2]), c, r[3]])
	_expect(tuning.release_cost(G.FIGHTING, T.THREED, S.SPACE) == 32400, "самая дорогая пара %d" % tuning.release_cost(G.FIGHTING, T.THREED, S.SPACE))
	var all_g: Array[G] = []
	var all_t: Array[T] = []
	var all_s: Array[S] = []
	for g in G.values():
		all_g.append(g)
	for t in T.values():
		all_t.append(t)
	for s in S.values():
		all_s.append(s)
	_expect(tuning.cheapest_release(all_g, all_t, all_s) == 4000, "самый дешёвый релиз")
	_expect(tuning.start_cash > 32400, "бюджета не хватает на самую дорогую пару")
	# Содержание по плану покупок.
	_reset()
	_expect(upkeep.total() == 800, "содержание на старте %d" % upkeep.total())
	for item in PLAN:
		_buy_next()
		_expect(upkeep.total() == int(item[2]), "содержание после %s: %d, в модели %d" % [item[1], upkeep.total(), item[2]])
	_expect(wallet.cash == 36000 - 7000 - 6000 - 3000 - 5000 - 12000 - 7000 - 18000, "списания покупок: %d" % wallet.cash)
	# Банкротство: 1 500 после шестого релиза средних рук меньше 4 000, минус тоже.
	var cheapest := tuning.cheapest_release([G.PLATFORMER, G.SHOOTER], [T.VECTOR, T.BIT8], all_s)
	_expect(cheapest == 4000, "дешёвый релиз средних рук %d" % cheapest)
	_expect(tuning.is_bankrupt(1500, cheapest) and tuning.is_bankrupt(-200, cheapest) and not tuning.is_bankrupt(4000, cheapest),
			"порог банкротства")
	# Сигнал кошелька.
	var got: Array = []
	wallet.money_changed.connect(func(a: int, d: int, r: StringName) -> void: got.append([a, d, r]))
	wallet.earn(500, &"tail")
	wallet.spend(200, &"upkeep")
	_expect(got.size() == 2 and got[1][1] == -200 and got[1][2] == &"upkeep", "сигнал money_changed: %s" % [got])
	_expect(tuning.bugfix_price(G.PLATFORMER, T.BIT8, S.PIRATES) == 1400, "цена багфикса")
	_expect(tuning.sprint_price(G.PLATFORMER, T.BIT8, S.PIRATES, tuning.manager_discount) == 1260, "скидка менеджера")
	_reset()
	_refresh()
	AutoTest.fulfill("economy checks")
	AutoTest.note("economy checks done")
