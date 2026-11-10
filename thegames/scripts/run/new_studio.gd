class_name NewStudio
extends Control
## Экран «Новая студия» (#61, плейтест 2026-11-10), спека `docs/specs/run.md`. Та же большая
## карточка `CardFrame`, что у конструктора: слева две карусели (`CardColumns`) жанра и
## технологии, справа карточка студии на месте сметы. Пара уже разыграна (`RunState.draw_start`);
## экран её показывает прокруткой: колонки сами крутятся по нескольким кругам карточек и
## замедляются, жанр встаёт первым, технология позже, на остановке карточка вздрагивает,
## подпись «Жанр · выпал». Справа логотип (`StudioLogo`) и название студии (`StudioNames`),
## бюджет и кнопка «Основать студию». Ввод: R другое название и логотип вместе, ␣ основать
## (во время прокрутки ␣ сразу ставит колонки на место). Сеттинга здесь нет: первая игра
## собирается дальше в обычном конструкторе, где открыты только выпавшие жанр и технология.

signal founded(studio_name: String, logo: StudioLogo)

const KINDS: Array[CatalogEntry.Kind] = [CatalogEntry.Kind.GENRE, CatalogEntry.Kind.TECH]
const LABELS: Array[String] = ["Жанр", "Технология"]
const STOPPED: Array[String] = ["Жанр · выпал", "Технология · выпала"]
## Сколько раз карточки каталога повторены в колонке: прокрутка идёт по кругам.
const LAPS := 4
## Пауза до прокрутки (карточка выезжает) и время прокрутки колонок, с.
const SPIN_DELAY := 0.45
const SPIN_SECONDS: Array[float] = [1.8, 2.5]
## С какой доли прокрутки шаги колонки анимируются.
const SMOOTH_FROM := 0.55
## Ширина двух колонок: карточки того же размера, что у конструктора с тремя.
const COLUMNS_WIDTH := 760.0
const LOGO_SIZE := 220.0
const NAME_FONT := 44

var genre := Game.Genre.PLATFORMER
var tech := Game.Tech.BIT8
var cash := 0
var rng := RandomNumberGenerator.new()
var names: StudioNames
var studio_name := ""
var logo: StudioLogo
var spinning := true

var card: CardFrame
var _catalogs: Array[Catalog] = []
var _columns: CardColumns
var _start: Array[int] = []
var _target: Array[int] = []
var _done: Array[bool] = []
var _time := -SPIN_DELAY
var _logo_view: StudioLogoView
var _name_label: Label
var _button: PanelContainer
var _button_label: Label
var _button_lift: JellyLift
var _founded := false


## Хозяин зовёт до добавления в дерево: выпавшая пара, бюджет, сид.
func setup(genre_: Game.Genre, tech_: Game.Tech, cash_: int, seed_: int) -> void:
	genre = genre_
	tech = tech_
	cash = cash_
	rng.seed = seed_
	names = StudioNames.load_default()
	studio_name = names.make(rng)
	logo = StudioLogo.make(names, rng)


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	if names == null:
		setup(genre, tech, cash, 1)
	_build()
	_refresh_studio(false)
	_refresh_button()
	card.raise_card()


# --- Прокрутка --------------------------------------------------------------------------------

func _process(delta: float) -> void:
	if not spinning:
		return
	_time += delta
	for col in KINDS.size():
		if _done[col]:
			continue
		var p := clampf(_time / SPIN_SECONDS[col], 0.0, 1.0)
		# ease-out: быстро в начале, медленно к остановке.
		var eased := 1.0 - pow(1.0 - p, 3.0)
		var k := _start[col] + int(floor(eased * (_target[col] - _start[col])))
		if k != _columns.index[col]:
			_columns.index[col] = k
			# Пока шаги чаще анимации карточек, колонка встаёт сразу: иначе карточки ловятся
			# на полпути разного размера. На замедлении карточки плывут.
			_columns.refresh(p > SMOOTH_FROM)
			ShellSounds.play(&"tick")
		if p >= 1.0:
			_stop(col)
	if _done.all(func(d: bool) -> bool: return d):
		spinning = false
		ShellSounds.play(&"done")
		_refresh_button()


func _stop(col: int) -> void:
	_done[col] = true
	_columns.index[col] = _target[col]
	_columns.set_caption(col, STOPPED[col])
	_columns.refresh(true)
	Jelly.poke(_columns.cards[col][_target[col]] as Control, 3.0)
	ShellSounds.play(&"hit")


## Поставить колонки на выпавшее сразу (␣ во время прокрутки, бот).
func finish_spin() -> void:
	if not spinning:
		return
	for col in KINDS.size():
		if not _done[col]:
			_stop(col)
	spinning = false
	_refresh_button()


# --- Ввод -------------------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if _founded:
		return
	var key := event as InputEventKey
	if key != null and key.pressed and not key.echo and key.keycode == KEY_R:
		regenerate()
		get_viewport().set_input_as_handled()
		return
	if MouseUi.is_click(event):
		if MouseUi.hit(_button, event):
			_press()
			get_viewport().set_input_as_handled()
		return
	if not event.is_echo() and GameInput.is_a(event):
		_press()
		get_viewport().set_input_as_handled()


func _press() -> void:
	if spinning:
		finish_spin()
	else:
		found()


## R: другое название и другой логотип.
func regenerate() -> void:
	studio_name = names.another(studio_name, rng)
	logo = logo.another(names, rng)
	ShellSounds.play(&"tick")
	_refresh_studio(true)


func found() -> void:
	if _founded or spinning:
		return
	_founded = true
	ShellSounds.play(&"done")
	Jelly.poke(_button, -2.0)
	_button_lift.press()
	founded.emit(studio_name, logo)


# --- Построение --------------------------------------------------------------------------------

func _build() -> void:
	var header := HintPill.header("Новая студия")
	header.position = Vector2(Style.EDGE, Style.HEADER_Y - Style.PILL_HEIGHT / 2.0)
	add_child(header)
	var right := HBoxContainer.new()
	right.alignment = BoxContainer.ALIGNMENT_END
	right.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	right.offset_left = Style.EDGE
	right.offset_right = -Style.EDGE
	right.offset_top = Style.HEADER_Y - Style.PILL_HEIGHT / 2.0
	right.offset_bottom = right.offset_top + Style.PILL_HEIGHT
	right.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(right)
	var money := HintPill.header(Style.format_money(cash))
	var money_label := money.get_child(0) as Label
	money_label.add_theme_font_override("font", Style.mono_font())
	money_label.add_theme_color_override("font_color", Style.MONEY)
	right.add_child(money)

	card = CardFrame.new()
	add_child(card)
	var inner := CardFrame.inner_size()
	var left_width := inner.x - Style.ESTIMATE_WIDTH - Style.GAP_CARDS
	var cards: Array[Array] = []
	for col in KINDS.size():
		var cat := Catalog.load_kind(KINDS[col])
		_catalogs.append(cat)
		var column_cards: Array = []
		for lap in LAPS:
			for e in cat.entries:
				column_cards.append(Constructor.entry_card(e))
		cards.append(column_cards)
		var n := cat.entries.size()
		var value := int(genre) if col == 0 else int(tech)
		_start.append(rng.randi_range(0, n - 1))
		_target.append((LAPS - 1) * n + maxi(cat.index_of(value), 0))
		_done.append(false)
	_columns = CardColumns.new()
	_columns.build(LABELS, cards, Vector2(COLUMNS_WIDTH, inner.y))
	_columns.position.x = (left_width - COLUMNS_WIDTH) / 2.0
	_columns.index = _start.duplicate()
	_columns.focus_col = -1
	card.content.add_child(_columns)
	_columns.refresh(false)
	_build_studio(card.content, Vector2(left_width + Style.GAP_CARDS, 0), Vector2(Style.ESTIMATE_WIDTH, inner.y))

	var hints := HBoxContainer.new()
	hints.alignment = BoxContainer.ALIGNMENT_CENTER
	hints.add_theme_constant_override("separation", 16)
	hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hints.offset_top = -(Style.PILL_HEIGHT + 16)
	hints.offset_bottom = -16
	hints.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hints.add_child(HintPill.make("R название и логотип"))
	hints.add_child(HintPill.make(GameInput.hint(GameInput.A, "основать студию")))
	add_child(hints)
	MouseUi.pass_through(self)


## Карточка студии на месте сметы: логотип, название, бюджет, кнопка.
func _build_studio(content: Control, at: Vector2, size_: Vector2) -> void:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.inner_card())
	panel.position = at
	panel.size = size_
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	content.add_child(panel)
	Jelly.attach(panel, Style.R_CARD, 20.0, false, 0.0, true, 0.6)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 12)
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(column)
	column.add_child(_label("Новая студия", Style.FONT_H2, Style.INK_2))
	column.add_child(_spacer(16))
	var logo_row := HBoxContainer.new()
	logo_row.alignment = BoxContainer.ALIGNMENT_CENTER
	logo_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(logo_row)
	_logo_view = StudioLogoView.new()
	_logo_view.custom_minimum_size = Vector2(LOGO_SIZE, LOGO_SIZE)
	logo_row.add_child(_logo_view)
	column.add_child(_spacer(8))
	_name_label = _label("", NAME_FONT, Style.INK)
	_name_label.add_theme_font_override("font", Jelly.fun_font(800))
	_name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_name_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_name_label.max_lines_visible = 2
	_name_label.custom_minimum_size = Vector2(0, int(NAME_FONT * 1.3) * 2)
	_name_label.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	column.add_child(_name_label)
	var hint := _label("R другое название и логотип", Style.FONT_CAPTION, Style.INK_3)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(hint)
	var filler := Control.new()
	filler.size_flags_vertical = Control.SIZE_EXPAND_FILL
	filler.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(filler)
	var budget := HBoxContainer.new()
	budget.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(budget)
	var bc := _label("Бюджет", Style.FONT_H2, Style.INK)
	bc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	budget.add_child(bc)
	var bv := _label(Style.format_money(cash), Style.FONT_H2, Style.MONEY)
	bv.add_theme_font_override("font", Style.mono_font())
	budget.add_child(bv)
	column.add_child(_spacer(8))
	_button = PanelContainer.new()
	_button.custom_minimum_size = Vector2(0, Style.BUTTON_HEIGHT)
	_button.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_button_label = _label("", Style.FONT_H2, Style.SURFACE_SOLID)
	_button_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_button_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_button.add_child(_button_label)
	column.add_child(_button)
	_button_lift = Jelly.button(_button)


func _refresh_studio(animate: bool) -> void:
	_name_label.text = studio_name
	_logo_view.set_logo(logo, animate)
	if animate:
		Jelly.poke(_name_label.get_parent().get_parent() as Control, 1.0)


## Кнопка тёмная и в фокусе, когда колонки встали; пока крутятся, серая «Выпадает…».
func _refresh_button() -> void:
	var active := not spinning
	_button_label.text = "Основать студию" if active else "Выпадает…"
	_button.add_theme_stylebox_override("panel", Style.flat(Style.INK if active else Style.BG, Style.R_CTL, Color.TRANSPARENT, 0))
	_button_label.add_theme_color_override("font_color", Style.SURFACE_SOLID if active else Style.INK_3)
	_button_lift.focused = active
	if active:
		Jelly.poke(_button)


func _label(text: String, font_size: int, color: Color) -> Label:
	return CardColumns.label(text, font_size, color)


func _spacer(h: int) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(0, h)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c
