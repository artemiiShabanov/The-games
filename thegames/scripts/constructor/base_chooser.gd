class_name BaseChooser
extends Control
## Экран основы следующей игры (#24, плейтест 2026-11-08): отдельный шаг перед конструктором,
## когда открыты сиквелы или ремейки. В большой карточке `CardFrame` до трёх вертикальных
## каруселей (`CardColumns`): «Новая игра» из одной карточки, «Сиквел» и «Ремейк» с карточкой
## на каждую прошлую игру от последней, в цвете её жанра, с технологией и оценкой критиков.
## Вверх и вниз листают колонку, влево и вправо переводят фокус, A выбирает и отдаёт
## `base_chosen`; закрытая карточка (ремейк ремейка, одна технология) затемнена с пилюлей
## причины, A на ней трясёт карточку. Назад нет: «Новая игра» это обычный путь.

signal base_chosen(option: BaseOption)

const COLUMNS_WIDTH := 1140
const CARD_TITLE_SIZE := 26
const NEW_COLOR := Color("#1E2A4A")

var past: Array[GameRecord] = []
var unlocked_techs: Array[Game.Tech] = []
var sequels_unlocked := false
var remakes_unlocked := false
var cash := 0
var release := 1
## Колонки: вид и его основы.
var kinds: Array[GameConfig.Kind] = []
var options: Array[Array] = []
var focus_col := 0

var card: CardFrame
var _columns: CardColumns
var _genres: Catalog
var _closing := false


func setup(past_: Array[GameRecord], unlocked_techs_: Array[Game.Tech], sequels_: bool, remakes_: bool,
		cash_: int, release_: int) -> void:
	past = past_
	unlocked_techs = unlocked_techs_
	sequels_unlocked = sequels_
	remakes_unlocked = remakes_
	cash = cash_
	release = release_


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_genres = Catalog.load_kind(CatalogEntry.Kind.GENRE)
	kinds = [GameConfig.Kind.NEW]
	if sequels_unlocked and not past.is_empty():
		kinds.append(GameConfig.Kind.SEQUEL)
	if remakes_unlocked and not past.is_empty():
		kinds.append(GameConfig.Kind.REMAKE)
	options = []
	for k in kinds:
		options.append(BaseOption.list(k, past, unlocked_techs))
	_build()
	_refresh(false)
	card.raise_card()


func selected() -> BaseOption:
	return options[focus_col][_columns.index[focus_col]]


func _unhandled_input(event: InputEvent) -> void:
	if event.is_echo() or _closing:
		return
	if MouseUi.is_motion(event):
		# Наведение (#82): колонка под курсором берёт фокус.
		var col := _columns.column_at(event)
		if col >= 0:
			focus(col)
		return
	if MouseUi.is_mouse(event):
		if _mouse(event):
			get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed(GameInput.UP):
		move(-1)
	elif event.is_action_pressed(GameInput.DOWN):
		move(1)
	elif event.is_action_pressed(GameInput.LEFT):
		focus(focus_col - 1)
	elif event.is_action_pressed(GameInput.RIGHT):
		focus(focus_col + 1)
	elif GameInput.is_a(event):
		confirm()
	else:
		return
	get_viewport().set_input_as_handled()


## Мышь: колесо листает колонку под курсором, клик по карточке выбирает её, по выбранной
## подтверждает.
func _mouse(event: InputEvent) -> bool:
	var w := MouseUi.wheel(event)
	if w != 0:
		var col := _columns.column_at(event)
		if col < 0:
			return false
		focus(col)
		move(w)
		return true
	if not MouseUi.is_click(event):
		return false
	var at := _columns.card_at(event)
	if at.x < 0:
		return false
	focus(at.x)
	if at.y < 0:
		return true
	if at.y == _columns.index[at.x]:
		confirm()
	else:
		_columns.index[at.x] = at.y
		ShellSounds.play(&"tick")
		_refresh(true)
	return true


func move(dir: int) -> void:
	if _columns.step(focus_col, dir):
		ShellSounds.play(&"tick")
		_refresh(true)


func focus(col: int) -> void:
	col = clampi(col, 0, kinds.size() - 1)
	if col == focus_col:
		return
	focus_col = col
	ShellSounds.play(&"tick")
	_refresh(true)


## Выбрать текущую основу в фокусе; если указан `option`, его (для бота и тестов).
func confirm(option: BaseOption = null) -> void:
	if _closing:
		return
	var o := option if option != null else selected()
	if not o.open:
		_shake(_columns.cards[focus_col][_columns.index[focus_col]])
		ShellSounds.play(&"miss")
		return
	_closing = true
	ShellSounds.play(&"done")
	await card.drop_card()
	base_chosen.emit(o)


# --- Построение --------------------------------------------------------------------------------

func _build() -> void:
	var header := HintPill.header(ShellHeader.release(release, "Основа"))
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
	var labels: Array[String] = []
	var cards: Array[Array] = []
	for col in kinds.size():
		labels.append(["Новая игра", "Сиквел", "Ремейк"][kinds[col]])
		var column_cards: Array = []
		for o in options[col]:
			column_cards.append(_make_card(o))
		cards.append(column_cards)
	_columns = CardColumns.new()
	# Область как у каруселей конструктора, по центру карточки.
	var width := minf(COLUMNS_WIDTH, inner.x)
	_columns.position = Vector2((inner.x - width) / 2.0, 0)
	_columns.build(labels, cards, Vector2(width, inner.y))
	card.content.add_child(_columns)

	var hints := HBoxContainer.new()
	hints.alignment = BoxContainer.ALIGNMENT_CENTER
	hints.add_theme_constant_override("separation", 16)
	hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hints.offset_top = -(Style.PILL_HEIGHT + 16)
	hints.offset_bottom = -16
	hints.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hints.add_child(HintPill.make("↑ ↓ листать"))
	hints.add_child(HintPill.make("← → колонка"))
	hints.add_child(HintPill.make(GameInput.hint(GameInput.A, "выбрать")))
	hints.add_child(HintPill.make("Esc назад"))
	add_child(hints)
	MouseUi.pass_through(self)


## Карточка основы: новая игра тёмная с плюсом; сиквел и ремейк в цвете жанра оригинала с его
## названием, технологией и оценкой критиков.
func _make_card(o: BaseOption) -> Control:
	var color := NEW_COLOR
	if o.parent != null:
		var ge := _genres.by_value(int(o.parent.genre))
		if ge != null:
			color = ge.color
	var c := CardColumns.make_card(color)
	var inner := CardColumns.inner_of(c)
	if o.kind == GameConfig.Kind.NEW:
		var glyph := CardColumns.label("+", 96, Color(1, 1, 1, 0.35))
		glyph.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		glyph.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		glyph.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		glyph.offset_bottom = -24
		inner.add_child(glyph)
		var caption := CardColumns.label("С нуля", 30, Style.SURFACE_SOLID)
		caption.position = Vector2(24, Style.CARD_SIZE.y - 24 - 44)
		inner.add_child(caption)
		return c
	var kind_label := CardColumns.label(o.kind_name(), Style.FONT_CAPTION, Color(1, 1, 1, 0.75))
	kind_label.position = Vector2(24, 20)
	inner.add_child(kind_label)
	var name_label := CardColumns.label(o.parent.title, CARD_TITLE_SIZE, Style.SURFACE_SOLID)
	name_label.position = Vector2(24, 50)
	name_label.size = Vector2(Style.CARD_SIZE.x - 48, 70)
	name_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	name_label.max_lines_visible = 2
	name_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	inner.add_child(name_label)
	var sub := "%s · часть %d" % [Game.tech_name(o.parent.tech), o.parent.part]
	if o.parent.score != null:
		sub = "%s · критики %.1f" % [Game.tech_name(o.parent.tech), o.parent.score.critics]
	var sub_label := CardColumns.label(sub, Style.FONT_CAPTION, Color(1, 1, 1, 0.75))
	sub_label.position = Vector2(24, Style.CARD_SIZE.y - 24 - 26)
	inner.add_child(sub_label)
	if not o.open:
		inner.add_child(CardColumns.center_pill(o.lock_reason, &"locked"))
		CardColumns.set_card_lock(c, &"locked")
	return c


func _refresh(animate: bool) -> void:
	_columns.focus_col = focus_col
	_columns.refresh(animate)


func _shake(node: Control) -> void:
	var x0 := node.position.x
	var tw := create_tween()
	for i in range(4):
		tw.tween_property(node, "position:x", x0 + Style.SHAKE_PX * (1 if i % 2 == 0 else -1), 0.04)
	tw.tween_property(node, "position:x", x0, 0.04)
