class_name Constructor
extends Control
## Экран конструктора, спека `docs/specs/constructor.md`, концепты `01`, `01b`: три карусели
## (жанр, технология, сеттинг) слева шириной `CAROUSEL_WIDTH`, смета карточкой справа шириной
## `ESTIMATE_WIDTH`, кнопка «В разработку». Влево и вправо листают, вверх и вниз переводят
## фокус между каруселями и кнопкой, A на карусели переводит фокус на кнопку, A на кнопке
## отдаёт `game_configured`, R другое название. Неоткрытые карточки затемнены с пилюлей «придёт
## с прокачкой», остаются в карусели и получают фокус; с ними кнопка закрыта. Денег не хватает:
## строка остатка `danger`, кнопка серая с суммой нехватки и трясётся. Деньги не списывает:
## это делает хозяин по сигналу. Карточки каруселей пока с крупной буквой вместо иллюстрации.

signal game_configured(config: GameConfig)
signal estimate_changed(estimate: Estimate)

const ROWS := 3
const ROW_BUTTON := 3
const ROW_LABELS: Array[String] = ["Жанр", "Технология", "Сеттинг"]
const ROW_TOP := 232
const ROW_STEP := 270
const CARD_LABEL_SIZE := 30
const TOTAL_FONT := 72
const ESTIMATE_TOP := 200
const ESTIMATE_BOTTOM := 120

var economy: EconomyTuning
var catalogs: Array[Catalog] = []
## Открытые значения по видам: индексы перечислений.
var unlocked: Array[Array] = [[], [], []]
var cash := 0
var discount := 0.0
var release := 1
var rng := RandomNumberGenerator.new()

var focus_row := 0
var index: Array[int] = [0, 0, 0]
var title := ""
var estimate: Estimate

var _rows: Array[Control] = []
var _cards: Array[Array] = [[], [], []]
var _focus_ring: Panel
var _title_label: Label
var _money_label: Label
var _release_label: Label
var _sprints_value: Label
var _price_value: Label
var _total_value: Label
var _remainder_label: Label
var _remainder_value: Label
var _button: PanelContainer
var _button_label: Label
var _ready_done := false


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	if economy == null:
		economy = EconomyTuning.load_default()
	if catalogs.is_empty():
		for k in CatalogEntry.Kind.values():
			catalogs.append(Catalog.load_kind(k))
	_build()
	_ready_done = true
	_refresh(false)


## Хозяин зовёт до добавления в дерево: открытые значения, деньги, скидка, номер релиза, сид.
func setup(unlocked_genres: Array[Game.Genre], unlocked_techs: Array[Game.Tech], unlocked_settings: Array[Game.Setting],
		cash_: int, release_: int, seed_: int, discount_ := 0.0) -> void:
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
	if catalogs.is_empty():
		for k in CatalogEntry.Kind.values():
			catalogs.append(Catalog.load_kind(k))
	# Стартовый выбор: первая открытая карточка каждого вида.
	for kind in ROWS:
		index[kind] = 0
		for i in catalogs[kind].entries.size():
			if is_unlocked(kind, i):
				index[kind] = i
				break
	title = TitleGen.make(selected_entry(2), selected_entry(0), rng)
	if _ready_done:
		_refresh(false)


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


func is_unlocked(kind: int, i: int) -> bool:
	var e := catalogs[kind].entries[i]
	return unlocked[kind].has(e.value)


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
	if event.is_action_pressed(GameInput.LEFT):
		move(-1)
	elif event.is_action_pressed(GameInput.RIGHT):
		move(1)
	elif event.is_action_pressed(GameInput.UP):
		focus(focus_row - 1)
	elif event.is_action_pressed(GameInput.DOWN):
		focus(focus_row + 1)
	elif GameInput.is_a(event):
		if focus_row == ROW_BUTTON:
			confirm()
		else:
			focus(ROW_BUTTON)
	else:
		return
	get_viewport().set_input_as_handled()


## Листание текущей карусели; на кнопке ничего.
func move(dir: int) -> void:
	if focus_row >= ROWS:
		return
	var n := catalogs[focus_row].entries.size()
	var next := clampi(index[focus_row] + dir, 0, n - 1)
	if next == index[focus_row]:
		return
	index[focus_row] = next
	if focus_row != 1:
		title = TitleGen.make(selected_entry(2), selected_entry(0), rng)
	ShellSounds.play(&"switch")
	_refresh(true)


func focus(row: int) -> void:
	row = clampi(row, 0, ROW_BUTTON)
	if row == focus_row:
		return
	focus_row = row
	_refresh(true)


func regenerate_title() -> void:
	title = TitleGen.another(title, selected_entry(2), selected_entry(0), rng)
	_refresh(false)


## Enter на кнопке: конфигурация зафиксирована, назад нельзя. Если нельзя, кнопка трясётся.
func confirm() -> void:
	if estimate == null or not estimate.affordable or not selection_open():
		_shake(_button)
		ShellSounds.play(&"miss")
		return
	ShellSounds.play(&"done")
	game_configured.emit(current_config())


# --- Построение --------------------------------------------------------------------------------

func _build() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_release_label = _label("", Style.FONT_BODY, Style.INK_2)
	_release_label.position = Vector2(Style.EDGE, 48)
	add_child(_release_label)
	var h1 := _label("Следующая игра", Style.FONT_H1, Style.INK)
	h1.position = Vector2(Style.EDGE, 88)
	add_child(h1)
	_money_label = _label("", Style.FONT_H2, Style.MONEY)
	_money_label.add_theme_font_override("font", Style.mono_font())
	_money_label.position = Vector2(Style.SCREEN.x - Style.EDGE - Style.ESTIMATE_WIDTH, 48)
	_money_label.size = Vector2(Style.ESTIMATE_WIDTH, 48)
	_money_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	add_child(_money_label)

	_focus_ring = Panel.new()
	_focus_ring.add_theme_stylebox_override("panel", Style.focus_ring(Style.R_CARD))
	_focus_ring.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_focus_ring.visible = false

	for kind in ROWS:
		var caption := _label(ROW_LABELS[kind], Style.FONT_CAPTION, Style.INK_2)
		caption.position = Vector2(Style.EDGE, ROW_TOP + kind * ROW_STEP - 30)
		add_child(caption)
		var clip := Control.new()
		clip.position = Vector2(Style.EDGE, ROW_TOP + kind * ROW_STEP)
		clip.size = Vector2(Style.CAROUSEL_WIDTH, Style.CARD_SIZE.y + 24)
		clip.clip_contents = true
		clip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(clip)
		var row := Control.new()
		row.mouse_filter = Control.MOUSE_FILTER_IGNORE
		clip.add_child(row)
		_rows.append(row)
		for i in catalogs[kind].entries.size():
			var card := _make_card(catalogs[kind].entries[i], is_unlocked(kind, i))
			card.position = Vector2(i * (Style.CARD_SIZE.x + Style.GAP_CARDS), 12)
			row.add_child(card)
			_cards[kind].append(card)
	add_child(_focus_ring)
	_build_estimate()
	var hints := HBoxContainer.new()
	hints.alignment = BoxContainer.ALIGNMENT_CENTER
	hints.add_theme_constant_override("separation", 16)
	hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hints.offset_top = -(Style.PILL_HEIGHT + 40)
	hints.offset_bottom = -40
	hints.offset_left = Style.EDGE
	hints.offset_right = -(Style.EDGE + Style.ESTIMATE_WIDTH + Style.GAP_CARDS)
	hints.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hints.add_child(HintPill.make("← → листать"))
	hints.add_child(HintPill.make("↑ ↓ карусель"))
	hints.add_child(HintPill.make("A в разработку · R название"))
	add_child(hints)


## Карточка карусели 260×190: цветной фон, крупная буква вместо иллюстрации, название внизу.
func _make_card(e: CatalogEntry, open: bool) -> Control:
	var card := PanelContainer.new()
	card.custom_minimum_size = Style.CARD_SIZE
	card.size = Style.CARD_SIZE
	card.pivot_offset = Style.CARD_SIZE / 2.0
	card.add_theme_stylebox_override("panel", Style.flat(e.color, Style.R_CARD, Color.TRANSPARENT, 0))
	card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var inner := Control.new()
	inner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.add_child(inner)
	var glyph := _label(e.title.substr(0, 1).to_upper(), 96, Color(1, 1, 1, 0.35))
	glyph.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	glyph.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	glyph.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	glyph.offset_bottom = -24
	inner.add_child(glyph)
	var caption := _label(e.title, CARD_LABEL_SIZE, Style.SURFACE_SOLID)
	caption.position = Vector2(24, Style.CARD_SIZE.y - 24 - 44)
	inner.add_child(caption)
	if not open:
		card.modulate.a = Style.DIM_LOCKED
		var pill := HintPill.make("придёт с прокачкой")
		pill.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
		pill.grow_horizontal = Control.GROW_DIRECTION_BOTH
		pill.grow_vertical = Control.GROW_DIRECTION_BOTH
		inner.add_child(pill)
	return card


func _build_estimate() -> void:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.card(true))
	panel.position = Vector2(Style.SCREEN.x - Style.EDGE - Style.ESTIMATE_WIDTH, ESTIMATE_TOP)
	panel.size = Vector2(Style.ESTIMATE_WIDTH, Style.SCREEN.y - ESTIMATE_TOP - ESTIMATE_BOTTOM)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 12)
	panel.add_child(column)
	column.add_child(_label("Смета", Style.FONT_H2, Style.INK_2))
	_title_label = _label("", 44, Style.INK)
	_title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_title_label.custom_minimum_size = Vector2(0, 120)
	column.add_child(_title_label)
	column.add_child(_label("R другое название", Style.FONT_CAPTION, Style.INK_3))
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
	_release_label.text = "Релиз %d" % release
	_money_label.text = Style.format_money(cash)
	_title_label.text = title
	_sprints_value.text = str(estimate.sprints)
	_price_value.text = Style.format_money(estimate.sprint_price)
	_total_value.text = Style.format_money(estimate.total)
	_remainder_value.text = Style.format_money(estimate.remainder)
	var danger := not estimate.affordable
	_remainder_value.add_theme_color_override("font_color", Style.DANGER if danger else Style.MONEY)
	_remainder_label.add_theme_color_override("font_color", Style.DANGER if danger else Style.INK_2)
	var open := selection_open()
	if not open:
		_button_label.text = "Придёт с прокачкой"
	elif danger:
		_button_label.text = "Не хватает " + Style.format_money(estimate.shortfall())
	else:
		_button_label.text = "В разработку"
	var active := open and not danger
	_button.add_theme_stylebox_override("panel", Style.flat(Style.INK if active else Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 0))
	_button_label.add_theme_color_override("font_color", Style.SURFACE_SOLID if active else Style.INK_3)
	# Карусели: выбранная карточка на втором месте, предыдущая выглядывает на PEEK.
	for kind in ROWS:
		var step := Style.CARD_SIZE.x + Style.GAP_CARDS
		var target_x := 0.0
		if index[kind] > 0:
			target_x = -(index[kind] * step) + Style.PEEK + Style.GAP_CARDS
		_animate(_rows[kind], "position:x", target_x, animate)
		for i in _cards[kind].size():
			var card: Control = _cards[kind][i]
			var focused := kind == focus_row and i == index[kind]
			_animate(card, "scale", Vector2.ONE * (Style.FOCUS_SCALE if focused else 1.0), animate)
	_place_focus_ring(animate)


func _place_focus_ring(animate: bool) -> void:
	var target: Control
	var radius := Style.R_CARD
	if focus_row == ROW_BUTTON:
		target = _button
		radius = Style.R_CTL
	else:
		target = _cards[focus_row][index[focus_row]]
	_focus_ring.add_theme_stylebox_override("panel", Style.focus_ring(radius))
	# Позиция после сдвига ряда известна из цели анимации, поэтому считаем сами.
	var rect: Rect2
	if focus_row == ROW_BUTTON:
		rect = Rect2(_button.global_position - global_position, _button.size)
	else:
		var row := _rows[focus_row]
		var clip := row.get_parent() as Control
		var step := Style.CARD_SIZE.x + Style.GAP_CARDS
		var row_x := 0.0
		if index[focus_row] > 0:
			row_x = -(index[focus_row] * step) + Style.PEEK + Style.GAP_CARDS
		var pos := clip.position + Vector2(row_x + target.position.x, target.position.y)
		var grown := Style.CARD_SIZE * Style.FOCUS_SCALE
		rect = Rect2(pos - (grown - Style.CARD_SIZE) / 2.0, grown)
	_focus_ring.visible = true
	_animate(_focus_ring, "position", rect.position, animate)
	_animate(_focus_ring, "size", rect.size, animate)


func _animate(node: Object, prop: String, value: Variant, animate: bool) -> void:
	if animate and not Debug.skip_cards:
		create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC).tween_property(node, prop, value, Style.FOCUS_MOVE_SECONDS)
	else:
		node.set_indexed(prop, value)


func _shake(node: Control) -> void:
	var x0 := node.position.x
	var tw := create_tween()
	for i in range(4):
		tw.tween_property(node, "position:x", x0 + Style.SHAKE_PX * (1 if i % 2 == 0 else -1), 0.04)
	tw.tween_property(node, "position:x", x0, 0.04)


func _label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _spacer(h: int) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(0, h)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c
