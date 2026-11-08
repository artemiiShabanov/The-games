class_name Constructor
extends Control
## Экран конструктора, спека `docs/specs/constructor.md`, концепты `01`, `01b`, плейтесты
## 2026-11-07 и 2026-11-08. Весь экран идёт в большой карточке `CardFrame` поверх студии, как
## спринты; над карточкой пилюли «Релиз N · Следующая игра» слева и денег справа. Внутри слева
## три вертикальные карусели (`CardColumns`: жанр, технология, сеттинг), справа карточка сметы
## с заголовком на две строки, числами, которые прокручиваются за 240 мс, и кнопкой «В
## разработку» внизу. Вверх и вниз листают колонку, влево и вправо переводят фокус по колонкам
## и дальше на кнопку, A на колонке переводит фокус на кнопку, A на кнопке отдаёт
## `game_configured`, R другое название. Рамка фокуса только на карточках; на кнопке она
## пропадает, а кнопка становится тёмной. Неоткрытые карточки затемнены с пилюлей «придёт с
## прокачкой», остаются в карусели и получают фокус; с ними кнопка закрыта. Денег не хватает:
## остаток `danger`, кнопка серая с суммой нехватки и трясётся. Деньги не списывает: это
## делает хозяин по сигналу. Основа (#24) выбирается до этого экрана (`BaseChooser`) и
## передаётся в `setup`: сиквел и ремейк держат жанр и сеттинг оригинала выбранными, остальные
## карточки этих колонок серые с пилюлей «недоступно», листание отвечает промахом, название
## задано основой и R не работает; у ремейка карточка технологии оригинала закрыта с пилюлей
## «как у оригинала», выбор сам уходит на другую. Подсказки рынка (#29, `set_market`): метка
## насыщения на карточках жанра и сеттинга («недавно было», «надоело») и, только с
## «Инсайдером», метка «в тренде»; конструктор их не считает, а читает из `MarketState`.
## Карточки каруселей пока с крупной буквой вместо иллюстрации.

signal game_configured(config: GameConfig)
signal estimate_changed(estimate: Estimate)

const ROWS := 3
const ROW_BUTTON := 3
const ROW_LABELS: Array[String] = ["Жанр", "Технология", "Сеттинг"]
const CARD_LABEL_SIZE := 30
const TITLE_FONT := 44
const TITLE_FONT_LONG := 34
const TITLE_LONG := 24
const TOTAL_FONT := 72

var economy: EconomyTuning
var catalogs: Array[Catalog] = []
## Открытые значения по видам: индексы перечислений.
var unlocked: Array[Array] = [[], [], []]
var cash := 0
var discount := 0.0
var release := 1
var rng := RandomNumberGenerator.new()
## Основа следующей игры (#24); null и новая игра равнозначны.
var base: BaseOption
## Подсказки рынка: метки по значениям жанра и сеттинга (#29).
var market_tags: Array[Dictionary] = [{}, {}, {}]

var focus_row := 0
var index: Array[int] = [0, 0, 0]
var title := ""
var estimate: Estimate

var card: CardFrame
var _inner := Vector2.ZERO
var _left_width := 0.0
var _columns: CardColumns
var _cards: Array[Array] = [[], [], []]
var _title_label: Label
var _title_hint: Label
var _money_label: Label
var _header_label: Label
var _sprints_value: Label
var _price_value: Label
var _total_value: Label
var _remainder_label: Label
var _remainder_value: Label
var _button: PanelContainer
var _button_label: Label
var _shown: Dictionary[StringName, float] = {}
var _ready_done := false


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	if economy == null:
		economy = EconomyTuning.load_default()
	if catalogs.is_empty():
		for k in CatalogEntry.Kind.values():
			catalogs.append(Catalog.load_kind(k))
	_build()
	_ready_done = true
	_refresh(false)
	card.raise_card()


## Хозяин зовёт до добавления в дерево: открытые значения, деньги, скидка, номер релиза, сид,
## основа из `BaseChooser` (null: новая игра).
func setup(unlocked_genres: Array[Game.Genre], unlocked_techs: Array[Game.Tech], unlocked_settings: Array[Game.Setting],
		cash_: int, release_: int, seed_: int, discount_ := 0.0, base_: BaseOption = null) -> void:
	unlocked = [[], [], []]
	for g in unlocked_genres:
		unlocked[0].append(int(g))
	for t in unlocked_techs:
		unlocked[1].append(int(t))
	for s in unlocked_settings:
		unlocked[2].append(int(s))
	cash = cash_
	release = release_
	discount = discount_
	rng.seed = seed_
	base = base_
	if catalogs.is_empty():
		for k in CatalogEntry.Kind.values():
			catalogs.append(Catalog.load_kind(k))
	# Стартовый выбор: первая открытая карточка каждого вида, у франшизы жанр и сеттинг оригинала.
	for kind in ROWS:
		index[kind] = 0
		for i in catalogs[kind].entries.size():
			if is_unlocked(kind, i):
				index[kind] = i
				break
	var p := franchise_parent()
	if p != null:
		index[0] = maxi(catalogs[0].index_of(int(p.genre)), 0)
		index[2] = maxi(catalogs[2].index_of(int(p.setting)), 0)
		title = base.title()
	else:
		title = TitleGen.make(selected_entry(2), selected_entry(0), rng)
	if _ready_done:
		_columns.index = index
		_refresh(false)


## Подсказки рынка на карточках: насыщение всегда, тренд только с «Инсайдером». Зовётся до
## или после `setup`, до добавления в дерево или в любой момент.
func set_market(market: MarketState, success: SuccessTuning, insider: bool) -> void:
	market_tags = [{}, {}, {}]
	if market == null:
		if _ready_done:
			_refresh(false)
		return
	for g in market.saturation_genre.size():
		var tag := market.saturation_label(market.saturation_genre[g], success)
		if insider and g == market.trend_genre:
			tag = "в тренде" if tag == "" else "в тренде · " + tag
		if tag != "":
			market_tags[0][g] = tag
	for st in market.saturation_setting.size():
		var tag := market.saturation_label(market.saturation_setting[st], success)
		if insider and st == market.trend_setting:
			tag = "в тренде" if tag == "" else "в тренде · " + tag
		if tag != "":
			market_tags[2][st] = tag
	if _ready_done:
		_refresh(false)


## Метка рынка карточки: пусто, если нет.
func market_tag(kind: int, value: int) -> String:
	return str(market_tags[kind].get(value, ""))


## Конфигурация без экрана: для дебага и бота.
static func quick_config(genre: Game.Genre, tech: Game.Tech, setting: Game.Setting, economy_: EconomyTuning,
		seed_: int, discount_ := 0.0) -> GameConfig:
	var c := GameConfig.new()
	c.genre = genre
	c.tech = tech
	c.setting = setting
	var r := RandomNumberGenerator.new()
	r.seed = seed_
	c.title = TitleGen.make(Catalog.load_kind(CatalogEntry.Kind.SETTING).by_value(setting),
			Catalog.load_kind(CatalogEntry.Kind.GENRE).by_value(genre), r)
	c.sprints = economy_.sprints(tech)
	c.sprint_cost = economy_.sprint_price(genre, tech, setting, discount_)
	return c


## Оригинал, если основа это сиквел или ремейк.
func franchise_parent() -> GameRecord:
	return base.parent if base != null and base.is_franchise() else null


## Технология оригинала закрыта для ремейка.
func _tech_blocked(value: int) -> bool:
	return base != null and base.kind == GameConfig.Kind.REMAKE and base.parent != null and int(base.parent.tech) == value


## Колонка залочена основой: жанр и сеттинг у сиквела и ремейка.
func is_locked_column(kind: int) -> bool:
	return (kind == 0 or kind == 2) and franchise_parent() != null


## Открыта ли карточка: по прокачке, у ремейка технология оригинала закрыта, в залоченной
## колонке только выбранная.
func is_unlocked(kind: int, i: int) -> bool:
	var e := catalogs[kind].entries[i]
	if not unlocked[kind].has(e.value):
		return false
	if kind == 1 and _tech_blocked(e.value):
		return false
	if is_locked_column(kind) and i != index[kind]:
		return false
	return true


func selected_entry(kind: int) -> CatalogEntry:
	return catalogs[kind].entries[index[kind]]


func selection_open() -> bool:
	for kind in ROWS:
		if not is_unlocked(kind, index[kind]):
			return false
	return true


func current_config() -> GameConfig:
	var c := GameConfig.new()
	c.genre = selected_entry(0).value as Game.Genre
	c.tech = selected_entry(1).value as Game.Tech
	c.setting = selected_entry(2).value as Game.Setting
	if base != null:
		c.kind = base.kind
		c.parent = base.parent
	c.title = title
	c.sprints = estimate.sprints
	c.sprint_cost = estimate.sprint_price
	return c


# --- Управление ------------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key != null and key.pressed and not key.echo and key.keycode == KEY_R:
		regenerate_title()
		get_viewport().set_input_as_handled()
		return
	if event.is_echo():
		return
	if event.is_action_pressed(GameInput.UP):
		move(-1)
	elif event.is_action_pressed(GameInput.DOWN):
		move(1)
	elif event.is_action_pressed(GameInput.LEFT):
		focus(focus_row - 1)
	elif event.is_action_pressed(GameInput.RIGHT):
		focus(focus_row + 1)
	elif GameInput.is_a(event):
		if focus_row == ROW_BUTTON:
			confirm()
		else:
			focus(ROW_BUTTON)
	else:
		return
	get_viewport().set_input_as_handled()


## Листание текущей колонки; на кнопке ничего, залоченная колонка отвечает промахом.
func move(dir: int) -> void:
	if focus_row >= ROWS:
		return
	if is_locked_column(focus_row):
		ShellSounds.play(&"miss")
		return
	if not _columns.step(focus_row, dir):
		return
	if focus_row != 1 and franchise_parent() == null:
		title = TitleGen.make(selected_entry(2), selected_entry(0), rng)
	ShellSounds.play(&"tick")
	_refresh(true)


func focus(row: int) -> void:
	row = clampi(row, 0, ROW_BUTTON)
	if row == focus_row:
		return
	focus_row = row
	ShellSounds.play(&"tick")
	_refresh(true)


func regenerate_title() -> void:
	if franchise_parent() != null:
		ShellSounds.play(&"miss")
		return
	title = TitleGen.another(title, selected_entry(2), selected_entry(0), rng)
	ShellSounds.play(&"tick")
	_refresh(false)


## A на кнопке: конфигурация зафиксирована, назад нельзя. Если нельзя, кнопка трясётся.
func confirm() -> void:
	if estimate == null or not estimate.affordable or not selection_open():
		_shake(_button)
		ShellSounds.play(&"miss")
		return
	ShellSounds.play(&"done")
	game_configured.emit(current_config())


# --- Построение --------------------------------------------------------------------------------

func _build() -> void:
	# Шапка над карточкой: релиз слева, деньги справа.
	var header := HintPill.header("")
	header.position = Vector2(Style.EDGE, Style.HEADER_Y - Style.PILL_HEIGHT / 2.0)
	add_child(header)
	_header_label = header.get_child(0) as Label
	var right := HBoxContainer.new()
	right.alignment = BoxContainer.ALIGNMENT_END
	right.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	right.offset_left = Style.EDGE
	right.offset_right = -Style.EDGE
	right.offset_top = Style.HEADER_Y - Style.PILL_HEIGHT / 2.0
	right.offset_bottom = right.offset_top + Style.PILL_HEIGHT
	right.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(right)
	var money_pill := HintPill.header("")
	right.add_child(money_pill)
	_money_label = money_pill.get_child(0) as Label
	_money_label.add_theme_font_override("font", Style.mono_font())
	_money_label.add_theme_color_override("font_color", Style.MONEY)

	card = CardFrame.new()
	add_child(card)
	_inner = CardFrame.inner_size()
	_left_width = _inner.x - Style.ESTIMATE_WIDTH - Style.GAP_CARDS
	var content := card.content
	var cards: Array[Array] = []
	for kind in ROWS:
		var column_cards: Array = []
		for i in catalogs[kind].entries.size():
			column_cards.append(_make_card(catalogs[kind].entries[i], kind == 1))
		_cards[kind] = column_cards
		cards.append(column_cards)
	_columns = CardColumns.new()
	_columns.build(ROW_LABELS, cards, Vector2(_left_width, _inner.y))
	_columns.index = index
	content.add_child(_columns)
	_build_estimate(content)

	var hints := HBoxContainer.new()
	hints.alignment = BoxContainer.ALIGNMENT_CENTER
	hints.add_theme_constant_override("separation", 16)
	hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hints.offset_top = -(Style.PILL_HEIGHT + 16)
	hints.offset_bottom = -16
	hints.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hints.add_child(HintPill.make("↑ ↓ листать"))
	hints.add_child(HintPill.make("← → колонка и кнопка"))
	hints.add_child(HintPill.make(GameInput.hint(GameInput.A, "в разработку")))
	hints.add_child(HintPill.make("R название"))
	add_child(hints)


## Карточка карусели 260×190: цветной фон, крупная буква вместо иллюстрации, название внизу.
## Пилюли «придёт с прокачкой», «недоступно» и (у технологии) «как у оригинала» включаются в
## `_refresh`.
func _make_card(e: CatalogEntry, with_origin_pill: bool) -> Control:
	var c := CardColumns.make_card(e.color)
	var inner := CardColumns.inner_of(c)
	var glyph := CardColumns.label(e.title.substr(0, 1).to_upper(), 96, Color(1, 1, 1, 0.35))
	glyph.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	glyph.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	glyph.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	glyph.offset_bottom = -24
	inner.add_child(glyph)
	var caption := CardColumns.label(e.title, CARD_LABEL_SIZE, Style.SURFACE_SOLID)
	caption.position = Vector2(24, Style.CARD_SIZE.y - 24 - 44)
	inner.add_child(caption)
	inner.add_child(CardColumns.center_pill("придёт с прокачкой", &"upgrade"))
	inner.add_child(CardColumns.center_pill("недоступно", &"franchise"))
	if with_origin_pill:
		inner.add_child(CardColumns.center_pill("как у оригинала", &"origin"))
	# Метка рынка сверху слева (STYLE: метка насыщения без чисел), текст ставит `_refresh`.
	var tag := HintPill.make("")
	tag.position = Vector2(16, 16)
	tag.visible = false
	tag.set_meta(&"market", true)
	inner.add_child(tag)
	return c


func _build_estimate(content: Control) -> void:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.card(true))
	panel.position = Vector2(_left_width + Style.GAP_CARDS, 0)
	panel.size = Vector2(Style.ESTIMATE_WIDTH, _inner.y)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	content.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 12)
	panel.add_child(column)
	column.add_child(_label("Смета", Style.FONT_H2, Style.INK_2))
	_title_label = _label("", TITLE_FONT, Style.INK)
	_title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_title_label.max_lines_visible = 2
	_title_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_title_label.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	# Ровно две строки: заголовок не двигает смету при смене названия.
	_title_label.custom_minimum_size = Vector2(0, int(TITLE_FONT * 1.3) * 2)
	_title_label.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	column.add_child(_title_label)
	_title_hint = _label("R другое название", Style.FONT_CAPTION, Style.INK_3)
	column.add_child(_title_hint)
	column.add_child(_spacer(16))
	_sprints_value = _row(column, "Спринтов")
	_price_value = _row(column, "Цена спринта")
	column.add_child(_spacer(8))
	var total_row := HBoxContainer.new()
	total_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(total_row)
	var total_caption := _label("Итого", Style.FONT_H2, Style.INK)
	total_caption.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	total_caption.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	total_row.add_child(total_caption)
	_total_value = _label("", TOTAL_FONT, Style.INK)
	_total_value.add_theme_font_override("font", Style.mono_font())
	_total_value.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	total_row.add_child(_total_value)
	var rem := HBoxContainer.new()
	rem.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(rem)
	_remainder_label = _label("Останется", Style.FONT_BODY, Style.INK_2)
	_remainder_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rem.add_child(_remainder_label)
	_remainder_value = _label("", Style.FONT_BODY, Style.MONEY)
	_remainder_value.add_theme_font_override("font", Style.mono_font())
	rem.add_child(_remainder_value)
	var filler := Control.new()
	filler.size_flags_vertical = Control.SIZE_EXPAND_FILL
	filler.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(filler)
	_button = PanelContainer.new()
	_button.custom_minimum_size = Vector2(0, Style.BUTTON_HEIGHT)
	_button.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_button_label = _label("В разработку", Style.FONT_H2, Style.SURFACE_SOLID)
	_button_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_button_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_button.add_child(_button_label)
	column.add_child(_button)


func _row(column: VBoxContainer, caption: String) -> Label:
	var row := HBoxContainer.new()
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(row)
	var c := _label(caption, Style.FONT_BODY, Style.INK)
	c.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(c)
	var v := _label("", Style.FONT_BODY, Style.INK)
	v.add_theme_font_override("font", Style.mono_font())
	row.add_child(v)
	return v


# --- Обновление ----------------------------------------------------------------------------------

func _refresh(animate: bool) -> void:
	var g := selected_entry(0).value as Game.Genre
	var t := selected_entry(1).value as Game.Tech
	var s := selected_entry(2).value as Game.Setting
	estimate = Estimate.compute(g, t, s, economy, cash, discount)
	estimate_changed.emit(estimate)
	_header_label.text = "Релиз %d · Следующая игра" % release
	_money_label.text = Style.format_money(cash)
	_title_label.text = title
	# Длинное название (ремейк сиквела) мельче, чтобы уместиться в две строки.
	_title_label.add_theme_font_size_override("font_size", TITLE_FONT if title.length() <= TITLE_LONG else TITLE_FONT_LONG)
	var franchise := franchise_parent() != null
	_title_hint.text = "название по франшизе" if franchise else "R другое название"
	_roll(&"sprints", _sprints_value, estimate.sprints, animate, func(v: float) -> String: return str(int(round(v))))
	_roll(&"price", _price_value, estimate.sprint_price, animate, _money_text)
	_roll(&"total", _total_value, estimate.total, animate, _money_text)
	_roll(&"remainder", _remainder_value, estimate.remainder, animate, _money_text)
	var danger := not estimate.affordable
	_remainder_value.add_theme_color_override("font_color", Style.DANGER if danger else Style.MONEY)
	_remainder_label.add_theme_color_override("font_color", Style.DANGER if danger else Style.INK_2)
	var open := selection_open()
	if not open:
		_button_label.text = "Нужна другая технология" if _tech_blocked(selected_entry(1).value) else "Придёт с прокачкой"
	elif danger:
		_button_label.text = "Не хватает " + Style.format_money(estimate.shortfall())
	else:
		_button_label.text = "В разработку"
	var active := open and not danger
	var on_button := focus_row == ROW_BUTTON
	# Активная: тёмная в фокусе, `surface-2` с чернилами без фокуса; закрытая: `surface-2` с `ink-3`.
	var bg := Style.INK if active and on_button else Style.SURFACE_2
	var ink := Style.INK_3
	if active:
		ink = Style.SURFACE_SOLID if on_button else Style.INK
	_button.add_theme_stylebox_override("panel", Style.flat(bg, Style.R_CTL, Style.FOCUS if on_button and not active else Color.TRANSPARENT, 0))
	_button_label.add_theme_color_override("font_color", ink)
	for kind in ROWS:
		_columns.set_caption(kind, ROW_LABELS[kind] + (" · как у оригинала" if is_locked_column(kind) else ""))
		for i in _cards[kind].size():
			_refresh_card_lock(kind, i, _cards[kind][i])
			_refresh_market_tag(kind, i, _cards[kind][i])
	_columns.focus_col = focus_row if focus_row < ROWS else -1
	_columns.refresh(animate)


func _refresh_market_tag(kind: int, i: int, c: Control) -> void:
	var text := market_tag(kind, catalogs[kind].entries[i].value)
	for child in CardColumns.inner_of(c).get_children():
		if child.has_meta(&"market"):
			child.visible = text != ""
			(child.get_child(0) as Label).text = text


## Закрытая карточка затемнена, пилюля говорит почему: прокачка, франшиза или технология
## оригинала.
func _refresh_card_lock(kind: int, i: int, c: Control) -> void:
	var e := catalogs[kind].entries[i]
	var meta: StringName = &""
	if not unlocked[kind].has(e.value):
		meta = &"upgrade"
	elif is_locked_column(kind) and i != index[kind]:
		meta = &"franchise"
	elif kind == 1 and _tech_blocked(e.value):
		meta = &"origin"
	CardColumns.set_card_lock(c, meta)


## Число прокручивается к новому значению за SWITCH_SECONDS (STYLE: числа не скачут).
func _roll(key: StringName, label: Label, to: int, animate: bool, fmt: Callable) -> void:
	var from: float = _shown.get(key, float(to))
	if not animate or Debug.skip_cards or is_equal_approx(from, float(to)):
		_shown[key] = float(to)
		label.text = fmt.call(float(to))
		return
	var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_method(func(v: float) -> void:
		_shown[key] = v
		label.text = fmt.call(v), from, float(to), Style.SWITCH_SECONDS)


func _money_text(v: float) -> String:
	return Style.format_money(int(round(v)))


func _shake(node: Control) -> void:
	var x0 := node.position.x
	var tw := create_tween()
	for i in range(4):
		tw.tween_property(node, "position:x", x0 + Style.SHAKE_PX * (1 if i % 2 == 0 else -1), 0.04)
	tw.tween_property(node, "position:x", x0, 0.04)


func _label(text: String, font_size: int, color: Color) -> Label:
	return CardColumns.label(text, font_size, color)


func _spacer(h: int) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(0, h)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c
