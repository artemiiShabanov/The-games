class_name GalleryScreen
extends Control
## Галерея (#70), спека `docs/specs/run.md`: все выпущенные игры всех забегов из профиля
## (`Profile.gallery`) карточками в большой карточке, по четыре в ряд, с прокруткой. Карточка:
## полоски цветов тройки (жанр, технология, сеттинг), название, критики, баги штампами,
## «Забег N · релиз M». Стрелки и наведение мыши выбирают, колесо листает; ␣ или клик по
## выбранной запускает демку с тем же сидом и багами (полноэкранную, как в ленте), по её концу
## галерея возвращается на ту же карточку. R меняет сортировку: по забегам (новые сверху,
## внутри по релизам) и по критикам. Esc или B закрывают (`closed`). Пустая галерея: одна
## подпись.

signal closed
signal demo_opened(entry: GalleryEntry)

enum Sort { RUNS, CRITICS }

const COLUMNS := 4
const CARD_HEIGHT := 248
const STRIPE := 14
const BOT_SECONDS := 0.6

var entries: Array[GalleryEntry] = []
var sort := Sort.RUNS
var index := 0
var playing := false

var card: CardFrame
var _scroll: ScrollContainer
var _grid: GridContainer
var _cards: Array[PanelContainer] = []
var _lifts: Array[JellyLift] = []
var _sort_label: Label
var _catalogs: Array[Catalog] = []
var _bugs: BugCatalog
var _demo: Demo
var _closing := false
var _bot_timer := 0.0
var _bot_played := false


func setup(entries_: Array[GalleryEntry]) -> void:
	entries = entries_.duplicate()


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	for k in [CatalogEntry.Kind.GENRE, CatalogEntry.Kind.TECH, CatalogEntry.Kind.SETTING]:
		_catalogs.append(Catalog.load_kind(k))
	_bugs = BugCatalog.load_default()
	_sort_entries()
	_build()
	card.raise_card()


func sorted() -> Array[GalleryEntry]:
	return entries


func _sort_entries() -> void:
	if sort == Sort.RUNS:
		entries.sort_custom(func(a: GalleryEntry, b: GalleryEntry) -> bool:
			return a.run_number > b.run_number or (a.run_number == b.run_number and a.release < b.release))
	else:
		entries.sort_custom(func(a: GalleryEntry, b: GalleryEntry) -> bool:
			return a.critics > b.critics or (a.critics == b.critics and a.run_number > b.run_number))


# --- Ввод ------------------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	# Выбор может синхронно увести экран из дерева, поэтому вьюпорт берётся заранее.
	var viewport := get_viewport()
	if playing or _closing:
		return
	if event is InputEventMouseMotion:
		var over := _card_at(event)
		if over >= 0 and over != index:
			focus(over, false)
		return
	if MouseUi.is_mouse(event):
		var w := MouseUi.wheel(event)
		if w != 0:
			_scroll.scroll_vertical += w * (CARD_HEIGHT / 2)
			MouseUi.consume(viewport)
		elif MouseUi.is_click(event):
			var at := _card_at(event)
			if at >= 0:
				focus(at, false)
				play()
				MouseUi.consume(viewport)
		return
	if event.is_echo() and not (event.is_action(GameInput.UP) or event.is_action(GameInput.DOWN)
			or event.is_action(GameInput.LEFT) or event.is_action(GameInput.RIGHT)):
		return
	var key := event as InputEventKey
	if key != null and key.pressed and not key.echo and key.keycode == KEY_R:
		toggle_sort()
	elif key != null and key.pressed and key.keycode == KEY_ESCAPE or GameInput.is_b(event):
		close()
	elif event.is_action_pressed(GameInput.LEFT, true):
		focus(index - 1)
	elif event.is_action_pressed(GameInput.RIGHT, true):
		focus(index + 1)
	elif event.is_action_pressed(GameInput.UP, true):
		focus(index - COLUMNS)
	elif event.is_action_pressed(GameInput.DOWN, true):
		focus(index + COLUMNS)
	elif GameInput.is_a(event):
		play()
	else:
		return
	MouseUi.consume(viewport)


func _card_at(event: InputEvent) -> int:
	for i in _cards.size():
		if MouseUi.hit(_cards[i], event):
			return i
	return -1


func focus(i: int, scroll := true) -> void:
	if entries.is_empty():
		return
	i = clampi(i, 0, entries.size() - 1)
	if i == index:
		return
	index = i
	ShellSounds.play(&"tick")
	_refresh_focus()
	if scroll:
		_scroll_to(i)


func toggle_sort() -> void:
	var current: GalleryEntry = entries[index] if not entries.is_empty() else null
	sort = Sort.CRITICS if sort == Sort.RUNS else Sort.RUNS
	_sort_entries()
	ShellSounds.play(&"tick")
	_fill_grid()
	index = maxi(entries.find(current), 0)
	_refresh_focus()
	_scroll_to(index)


## Демка выбранной игры: тот же сид и те же баги, полноэкранная, по концу назад в галерею.
func play() -> void:
	if entries.is_empty() or playing:
		if entries.is_empty():
			ShellSounds.play(&"miss")
		return
	var e := entries[index]
	var record := e.to_record()
	_demo = DemoCatalog.create(record)
	if _demo == null:
		Jelly.poke(_cards[index], -2.0)
		ShellSounds.play(&"miss")
		return
	playing = true
	_lifts[index].press()
	ShellSounds.play(&"done")
	card.visible = false
	_demo.setup(record, &"gallery")
	_demo.demo_finished.connect(_on_demo_finished)
	add_child(_demo)
	_demo.start()
	demo_opened.emit(e)


func _on_demo_finished(_r: GameRecord, _reached: bool) -> void:
	if _demo != null:
		_demo.queue_free()
		_demo = null
	playing = false
	card.visible = true
	_refresh_focus()


func close() -> void:
	if _closing:
		return
	_closing = true
	ShellSounds.play(&"tick")
	await card.drop_card()
	closed.emit()


## Бот автотеста: открывает демку выбранной игры (если есть), затем закрывает галерею.
func _process(delta: float) -> void:
	if not AutoTest.bot_active() or playing or _closing:
		return
	_bot_timer += delta
	if _bot_timer < BOT_SECONDS:
		return
	_bot_timer = 0.0
	if not _bot_played and not entries.is_empty():
		_bot_played = true
		play()
	else:
		close()


# --- Построение ----------------------------------------------------------------------------

func _build() -> void:
	var header := HintPill.header(ShellHeader.text("Галерея · %s" % _games_text(entries.size())))
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
	var sort_pill := HintPill.header("")
	_sort_label = sort_pill.get_child(0) as Label
	right.add_child(sort_pill)

	card = CardFrame.new()
	add_child(card)
	var inner := CardFrame.inner_size()
	if entries.is_empty():
		var empty := _label("Здесь появятся игры твоих забегов: каждая выпущенная игра попадает в галерею и запускается с теми же багами.",
				Style.FONT_H2, Style.INK_2)
		empty.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		empty.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		empty.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		empty.size = inner
		card.content.add_child(empty)
	else:
		_scroll = ScrollContainer.new()
		_scroll.size = inner
		_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
		_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
		card.content.add_child(_scroll)
		var margin := MarginContainer.new()
		margin.add_theme_constant_override("margin_top", 12)
		margin.add_theme_constant_override("margin_bottom", 12)
		margin.add_theme_constant_override("margin_left", 4)
		margin.add_theme_constant_override("margin_right", 4)
		margin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_scroll.add_child(margin)
		_grid = GridContainer.new()
		_grid.columns = COLUMNS
		_grid.add_theme_constant_override("h_separation", Style.GAP_CARDS)
		_grid.add_theme_constant_override("v_separation", Style.GAP_CARDS)
		_grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		margin.add_child(_grid)
		_fill_grid()

	var hints := HBoxContainer.new()
	hints.alignment = BoxContainer.ALIGNMENT_CENTER
	hints.add_theme_constant_override("separation", 16)
	hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hints.offset_top = -(Style.PILL_HEIGHT + 16)
	hints.offset_bottom = -16
	hints.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if not entries.is_empty():
		hints.add_child(HintPill.make("← → ↑ ↓ выбрать"))
		hints.add_child(HintPill.make(GameInput.hint(GameInput.A, "запустить")))
		hints.add_child(HintPill.make("R сортировка"))
	hints.add_child(HintPill.make("Esc назад"))
	add_child(hints)
	_refresh_focus()
	MouseUi.pass_through(self)


func _fill_grid() -> void:
	_sort_label.text = "по забегам" if sort == Sort.RUNS else "по критикам"
	if _grid == null:
		return
	for c in _grid.get_children():
		c.queue_free()
	_cards.clear()
	_lifts.clear()
	var w := floorf((CardFrame.inner_size().x - 8 - (COLUMNS - 1) * Style.GAP_CARDS) / COLUMNS)
	for e in entries:
		var c := _make_card(e, w)
		_grid.add_child(c)
		_cards.append(c)
		_lifts.append(Jelly.button(c, float(Style.R_CARD)))
	MouseUi.pass_through(_grid)


## Карточка игры: полоски тройки, название, критики, штампы багов, забег и релиз.
func _make_card(e: GalleryEntry, w: float) -> PanelContainer:
	var c := PanelContainer.new()
	c.custom_minimum_size = Vector2(w, CARD_HEIGHT)
	var sb := Style.flat(Style.SURFACE_2, Style.R_CARD, Color.TRANSPARENT, 0)
	sb.content_margin_left = 24
	sb.content_margin_right = 24
	sb.content_margin_top = 20
	sb.content_margin_bottom = 20
	c.add_theme_stylebox_override("panel", sb)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 10)
	c.add_child(col)
	var stripes := HBoxContainer.new()
	stripes.add_theme_constant_override("separation", 6)
	col.add_child(stripes)
	var values := [int(e.genre), int(e.tech), int(e.setting)]
	for k in 3:
		var entry := _catalogs[k].by_value(values[k])
		var bar := Panel.new()
		bar.custom_minimum_size = Vector2(0, STRIPE)
		bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		bar.add_theme_stylebox_override("panel", Style.flat(entry.color if entry != null else Style.INK_3, Style.R_PILL, Color.TRANSPARENT, 0))
		stripes.add_child(bar)
	var names: PackedStringArray = []
	for k in 3:
		var entry := _catalogs[k].by_value(values[k])
		names.append(entry.title if entry != null else "?")
	col.add_child(_label(" × ".join(names), Style.FONT_CAPTION, Style.INK_2))
	var title := _label(e.title, 28, Style.INK)
	title.add_theme_font_override("font", Jelly.fun_font(800))
	title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	title.max_lines_visible = 2
	title.custom_minimum_size = Vector2(w - 48, 0)
	col.add_child(title)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	col.add_child(row)
	var critics := _label("%.1f" % e.critics, Style.FONT_H2, Style.INK)
	critics.add_theme_font_override("font", Style.mono_font())
	row.add_child(critics)
	if e.viral:
		row.add_child(_pill("вирусная", Style.TINT_PLUS, Style.MONEY, 0.0))
	for id in e.bug_ids:
		var bug := _bugs.by_id(id)
		row.add_child(_pill(bug.stamp_for(e.genre) if bug != null else String(id), Style.BUG, Style.SURFACE_SOLID, -6.0))
	var filler := Control.new()
	filler.size_flags_vertical = Control.SIZE_EXPAND_FILL
	col.add_child(filler)
	col.add_child(_label("Забег %d · релиз %d%s" % [e.run_number, e.release, (" · «%s»" % e.studio) if e.studio != "" else ""],
			Style.FONT_CAPTION, Style.INK_3))
	return c


func _pill(text: String, bg: Color, ink: Color, degrees: float) -> Control:
	var p := PanelContainer.new()
	var sb := Style.flat(bg, Style.R_PILL, Color.TRANSPARENT, 0)
	sb.content_margin_left = 12
	sb.content_margin_right = 12
	sb.content_margin_top = 2
	sb.content_margin_bottom = 2
	p.add_theme_stylebox_override("panel", sb)
	p.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var l := _label(text, 14, ink)
	p.add_child(l)
	p.rotation_degrees = degrees
	return p


func _refresh_focus() -> void:
	for i in _lifts.size():
		_lifts[i].focused = i == index
	if index < _cards.size():
		Jelly.poke(_cards[index])


func _scroll_to(i: int) -> void:
	if _scroll == null or i >= _cards.size():
		return
	var row := i / COLUMNS
	var top := row * (CARD_HEIGHT + Style.GAP_CARDS)
	var view := _scroll.size.y
	var target := _scroll.scroll_vertical
	if top < target:
		target = top
	elif top + CARD_HEIGHT + 24 > target + view:
		target = int(top + CARD_HEIGHT + 24 - view)
	create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC).tween_property(_scroll, "scroll_vertical", target, Style.FOCUS_MOVE_SECONDS)


static func _games_text(n: int) -> String:
	var m10 := n % 10
	var m100 := n % 100
	var word := "игр"
	if m10 == 1 and m100 != 11:
		word = "игра"
	elif m10 >= 2 and m10 <= 4 and (m100 < 12 or m100 > 14):
		word = "игры"
	return "%d %s" % [n, word]


func _label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l
