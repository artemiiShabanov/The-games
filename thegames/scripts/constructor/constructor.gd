class_name Constructor
extends Control
## Экран конструктора, спека `docs/specs/constructor.md`, концепты `01`, `01b`, плейтест
## 2026-11-07. Весь экран идёт в большой карточке `CardFrame` поверх студии, как спринты;
## над карточкой пилюли «Релиз N · Следующая игра» слева и денег справа. Внутри слева
## вертикальные карусели: жанр, технология, сеттинг, а когда открыты сиквелы или ремейки (#24),
## перед ними четвёртая, «Основа»: новая игра, сиквел каждой прошлой игры, ремейк каждой
## прошлой игры. Сиквел и ремейк лочат жанр и сеттинг под оригинал и задают название
## («Пираты на платформах 2», «Пираты на платформах: ремейк»); ремейку нужна другая
## технология, карточка технологии оригинала закрыта с пилюлей «как у оригинала», при одной
## открытой технологии ремейки закрыты с пилюлей «нужна вторая технология», ремейк ремейка
## закрыт. Выбранная карточка по центру колонки и увеличена так, что выбранные с полями
## `GAP_CARDS` заполняют ширину до сметы, соседние обычного размера раздвинуты на её рост и
## растворяются к верху и низу; справа карточка сметы с заголовком на две строки, числами,
## которые прокручиваются за 240 мс, и кнопкой «В разработку» внизу. Вверх и вниз листают
## колонку, влево и вправо переводят фокус по колонкам и дальше на кнопку, A на колонке
## переводит фокус на кнопку, A на кнопке отдаёт `game_configured`, R другое название (только у
## новой игры). Рамка фокуса только на карточках; на кнопке она пропадает, а кнопка становится
## тёмной. Неоткрытые карточки затемнены с пилюлей «придёт с прокачкой», остаются в карусели и
## получают фокус; с ними кнопка закрыта. Денег не хватает: остаток `danger`, кнопка серая с
## суммой нехватки и трясётся. Деньги не списывает: это делает хозяин по сигналу. Карточки
## каруселей пока с крупной буквой вместо иллюстрации.

signal game_configured(config: GameConfig)
signal estimate_changed(estimate: Estimate)

## Колонки каталогов 0..2 (как `CatalogEntry.Kind`), основа 3, кнопка 4.
const ROWS := 3
const ROW_BASE := 3
const ROW_BUTTON := 4
const ROW_LABELS: Array[String] = ["Жанр", "Технология", "Сеттинг", "Основа"]
const COLUMN_TOP := 36
const CARD_LABEL_SIZE := 30
const BASE_TITLE_SIZE := 26
const TITLE_FONT := 44
const TITLE_FONT_LONG := 34
const TITLE_LONG := 24
const TOTAL_FONT := 72
const BASE_COLOR := Color("#1E2A4A")
## Ширина градиента по верху и низу колонки: карточки растворяются, а не режутся.
const EDGE_FADE := 120.0
## Маска краёв колонки: альфа по мировой Y между `top` и `bottom` с плавными краями `fade`.
## Границы обновляются каждый кадр, потому что карточка всплывает и уезжает.
const FADE_SHADER := """
shader_type canvas_item;
uniform float top_px = 0.0;
uniform float bottom_px = 1000.0;
uniform float fade_px = 120.0;
varying vec2 world_pos;
void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
}
void fragment() {
	float a = smoothstep(0.0, fade_px, world_pos.y - top_px) * smoothstep(0.0, fade_px, bottom_px - world_pos.y);
	COLOR.a *= a;
}
"""


## Карточка колонки «Основа»: новая игра или сиквел / ремейк прошлой игры.
class BaseOption:
	var kind: GameConfig.Kind = GameConfig.Kind.NEW
	var parent: GameRecord
	var open := true
	## Почему закрыта: пилюля на карточке.
	var lock_reason := ""

	func title() -> String:
		match kind:
			GameConfig.Kind.SEQUEL:
				return "%s %d" % [parent.franchise_title(), parent.part + 1]
			GameConfig.Kind.REMAKE:
				return "%s: ремейк" % parent.title
		return ""


var economy: EconomyTuning
var catalogs: Array[Catalog] = []
## Открытые значения по видам: индексы перечислений.
var unlocked: Array[Array] = [[], [], []]
var cash := 0
var discount := 0.0
var release := 1
var rng := RandomNumberGenerator.new()
## Прошлые игры забега и флаги возможностей (#24).
var past: Array[GameRecord] = []
var sequels_unlocked := false
var remakes_unlocked := false
var base_options: Array[BaseOption] = []

var focus_row := 0
var index: Array[int] = [0, 0, 0, 0]
var title := ""
var estimate: Estimate

var card: CardFrame
var _inner := Vector2.ZERO
var _left_width := 0.0
## Порядок колонок слева направо: [3, 0, 1, 2] с основой, [0, 1, 2] без.
var _order: Array[int] = [0, 1, 2]
var _rows: Array[Control] = [null, null, null, null]
var _clips: Array[Control] = [null, null, null, null]
var _captions: Array[Label] = [null, null, null, null]
var _mask: ShaderMaterial
var _column_height := 0.0
## Ширина слота колонки и масштаб выбранной карточки, чтобы слоты с полями заполнили ширину.
var _slot := 0.0
var _select_scale := 1.0
var _cards: Array[Array] = [[], [], [], []]
var _focus_ring: Panel
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
	if base_options.is_empty():
		_build_base_options()
	_build()
	_ready_done = true
	_refresh(false)
	card.raise_card()


## Хозяин зовёт до добавления в дерево: открытые значения, деньги, скидка, номер релиза, сид,
## прошлые игры забега и флаги сиквелов и ремейков из студии.
func setup(unlocked_genres: Array[Game.Genre], unlocked_techs: Array[Game.Tech], unlocked_settings: Array[Game.Setting],
		cash_: int, release_: int, seed_: int, discount_ := 0.0, past_: Array[GameRecord] = [],
		sequels_ := false, remakes_ := false) -> void:
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
	past = past_
	sequels_unlocked = sequels_
	remakes_unlocked = remakes_
	if catalogs.is_empty():
		for k in CatalogEntry.Kind.values():
			catalogs.append(Catalog.load_kind(k))
	_build_base_options()
	# Стартовый выбор: новая игра, первая открытая карточка каждого вида.
	for kind in ROWS:
		index[kind] = 0
		for i in catalogs[kind].entries.size():
			if is_unlocked(kind, i):
				index[kind] = i
				break
	index[ROW_BASE] = 0
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


## Колонка «Основа» есть, когда открыты сиквелы или ремейки.
func has_base() -> bool:
	return sequels_unlocked or remakes_unlocked


func base() -> BaseOption:
	return base_options[index[ROW_BASE]] if not base_options.is_empty() else null


## Основа это сиквел или ремейк: жанр и сеттинг под оригинал.
func franchise_parent() -> GameRecord:
	var b := base()
	return b.parent if b != null and b.kind != GameConfig.Kind.NEW else null


## Список основ: новая игра, затем по прошлым играм от последней сиквел и ремейк. Ремейк
## закрыт для ремейка и когда нет другой открытой технологии.
func _build_base_options() -> void:
	base_options.clear()
	var fresh := BaseOption.new()
	base_options.append(fresh)
	if not has_base():
		return
	for k in range(past.size() - 1, -1, -1):
		var p := past[k]
		if sequels_unlocked:
			var s := BaseOption.new()
			s.kind = GameConfig.Kind.SEQUEL
			s.parent = p
			base_options.append(s)
		if remakes_unlocked:
			var r := BaseOption.new()
			r.kind = GameConfig.Kind.REMAKE
			r.parent = p
			if p.remake:
				r.open = false
				r.lock_reason = "ремейк ремейка нельзя"
			elif not _other_tech_open(p.tech):
				r.open = false
				r.lock_reason = "нужна вторая технология"
			base_options.append(r)


func _other_tech_open(tech: Game.Tech) -> bool:
	for t in unlocked[1]:
		if t != int(tech):
			return true
	return false


func _count(kind: int) -> int:
	return base_options.size() if kind == ROW_BASE else catalogs[kind].entries.size()


## Открыта ли карточка: каталожная по прокачке, у ремейка технология оригинала закрыта,
## основа по своему флагу.
func is_unlocked(kind: int, i: int) -> bool:
	if kind == ROW_BASE:
		return base_options[i].open
	var e := catalogs[kind].entries[i]
	if not unlocked[kind].has(e.value):
		return false
	if kind == 1 and _tech_blocked(e.value):
		return false
	return true


## Технология оригинала закрыта для ремейка.
func _tech_blocked(value: int) -> bool:
	var b := base()
	return b != null and b.kind == GameConfig.Kind.REMAKE and int(b.parent.tech) == value


## Колонка залочена основой: жанр и сеттинг у сиквела и ремейка.
func is_locked_column(kind: int) -> bool:
	return (kind == 0 or kind == 2) and franchise_parent() != null


func selected_entry(kind: int) -> CatalogEntry:
	return catalogs[kind].entries[index[kind]]


func selection_open() -> bool:
	for kind in ROWS:
		if not is_unlocked(kind, index[kind]):
			return false
	var b := base()
	return b == null or b.open


func current_config() -> GameConfig:
	var c := GameConfig.new()
	c.genre = selected_entry(0).value as Game.Genre
	c.tech = selected_entry(1).value as Game.Tech
	c.setting = selected_entry(2).value as Game.Setting
	var b := base()
	if b != null:
		c.kind = b.kind
		c.parent = b.parent
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
		focus_step(-1)
	elif event.is_action_pressed(GameInput.RIGHT):
		focus_step(1)
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
	if focus_row == ROW_BUTTON:
		return
	if is_locked_column(focus_row):
		ShellSounds.play(&"miss")
		return
	var n := _count(focus_row)
	var next := clampi(index[focus_row] + dir, 0, n - 1)
	if next == index[focus_row]:
		return
	index[focus_row] = next
	if focus_row == ROW_BASE:
		_apply_base()
	elif focus_row != 1:
		title = TitleGen.make(selected_entry(2), selected_entry(0), rng)
	ShellSounds.play(&"tick")
	_refresh(true)


## Выбор основы: сиквел и ремейк ставят жанр и сеттинг оригинала, ремейк уводит технологию с
## технологии оригинала, название задано; новая игра получает название заново.
func _apply_base() -> void:
	var b := base()
	var p := franchise_parent()
	if p != null:
		index[0] = maxi(catalogs[0].index_of(int(p.genre)), 0)
		index[2] = maxi(catalogs[2].index_of(int(p.setting)), 0)
		if b.kind == GameConfig.Kind.REMAKE and _tech_blocked(selected_entry(1).value):
			for i in catalogs[1].entries.size():
				if is_unlocked(1, i):
					index[1] = i
					break
		title = b.title()
	else:
		title = TitleGen.make(selected_entry(2), selected_entry(0), rng)


## Фокус по порядку колонок и дальше на кнопку.
func focus_step(dir: int) -> void:
	var chain: Array[int] = _order.duplicate()
	chain.append(ROW_BUTTON)
	var pos := chain.find(focus_row)
	focus(chain[clampi(pos + dir, 0, chain.size() - 1)])


func focus(row: int) -> void:
	if row == focus_row or (row == ROW_BASE and not has_base()):
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
	var shader := Shader.new()
	shader.code = FADE_SHADER
	_mask = ShaderMaterial.new()
	_mask.shader = shader
	_mask.set_shader_parameter("fade_px", EDGE_FADE)
	_column_height = _inner.y - COLUMN_TOP
	if has_base():
		_order.assign([ROW_BASE, 0, 1, 2])
	else:
		_order.assign([0, 1, 2])
	var columns := _order.size()
	# Слева поле GAP, между слотами GAP, справа до сметы сам GAP между областями.
	_slot = (_left_width - columns * Style.GAP_CARDS) / columns
	_select_scale = _slot / Style.CARD_SIZE.x
	var step_x := _slot + Style.GAP_CARDS
	var x0 := float(Style.GAP_CARDS)
	var card_x := 12.0 + (_slot - Style.CARD_SIZE.x) / 2.0

	_focus_ring = Panel.new()
	_focus_ring.add_theme_stylebox_override("panel", Style.focus_ring(Style.R_CARD))
	_focus_ring.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_focus_ring.visible = false

	for pos in columns:
		var kind: int = _order[pos]
		var caption := _label(ROW_LABELS[kind], Style.FONT_CAPTION, Style.INK_2)
		caption.position = Vector2(x0 + pos * step_x, 0)
		caption.size = Vector2(_slot, 24)
		caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		content.add_child(caption)
		_captions[kind] = caption
		var clip := Control.new()
		clip.position = Vector2(x0 + pos * step_x - 12, COLUMN_TOP)
		clip.size = Vector2(_slot + 24, _column_height)
		clip.clip_contents = true
		clip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		content.add_child(clip)
		_clips[kind] = clip
		var column := Control.new()
		column.mouse_filter = Control.MOUSE_FILTER_IGNORE
		column.material = _mask
		clip.add_child(column)
		_rows[kind] = column
		for i in _count(kind):
			var c: Control
			if kind == ROW_BASE:
				c = _make_base_card(base_options[i])
			else:
				c = _make_card(catalogs[kind].entries[i], kind == 1)
			c.position = Vector2(card_x, _card_y(kind, i))
			column.add_child(c)
			_cards[kind].append(c)
			_inherit_material(c)
	content.add_child(_focus_ring)
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
	hints.add_child(HintPill.make("A в разработку"))
	hints.add_child(HintPill.make("R название"))
	add_child(hints)


## Карточка карусели 260×190: цветной фон, крупная буква вместо иллюстрации, название внизу.
## Пилюли «придёт с прокачкой» и (у технологии) «как у оригинала» включаются в `_refresh`.
func _make_card(e: CatalogEntry, with_origin_pill: bool) -> Control:
	var c := PanelContainer.new()
	c.custom_minimum_size = Style.CARD_SIZE
	c.size = Style.CARD_SIZE
	c.pivot_offset = Style.CARD_SIZE / 2.0
	c.add_theme_stylebox_override("panel", Style.flat(e.color, Style.R_CARD, Color.TRANSPARENT, 0))
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var inner := Control.new()
	inner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.add_child(inner)
	var glyph := _label(e.title.substr(0, 1).to_upper(), 96, Color(1, 1, 1, 0.35))
	glyph.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	glyph.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	glyph.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	glyph.offset_bottom = -24
	inner.add_child(glyph)
	var caption := _label(e.title, CARD_LABEL_SIZE, Style.SURFACE_SOLID)
	caption.position = Vector2(24, Style.CARD_SIZE.y - 24 - 44)
	inner.add_child(caption)
	inner.add_child(_center_pill("придёт с прокачкой", &"locked_pill"))
	if with_origin_pill:
		inner.add_child(_center_pill("как у оригинала", &"origin_pill"))
	return c


## Карточка основы: новая игра или сиквел / ремейк прошлой игры в цвете её жанра.
func _make_base_card(o: BaseOption) -> Control:
	var c := PanelContainer.new()
	c.custom_minimum_size = Style.CARD_SIZE
	c.size = Style.CARD_SIZE
	c.pivot_offset = Style.CARD_SIZE / 2.0
	var color := BASE_COLOR
	if o.parent != null:
		var ge := catalogs[0].by_value(int(o.parent.genre))
		if ge != null:
			color = ge.color
	c.add_theme_stylebox_override("panel", Style.flat(color, Style.R_CARD, Color.TRANSPARENT, 0))
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var inner := Control.new()
	inner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.add_child(inner)
	if o.kind == GameConfig.Kind.NEW:
		var glyph := _label("+", 96, Color(1, 1, 1, 0.35))
		glyph.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		glyph.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		glyph.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		glyph.offset_bottom = -24
		inner.add_child(glyph)
		var caption := _label("Новая игра", CARD_LABEL_SIZE, Style.SURFACE_SOLID)
		caption.position = Vector2(24, Style.CARD_SIZE.y - 24 - 44)
		inner.add_child(caption)
	else:
		var kind_label := _label("сиквел" if o.kind == GameConfig.Kind.SEQUEL else "ремейк", Style.FONT_CAPTION, Color(1, 1, 1, 0.75))
		kind_label.position = Vector2(24, 20)
		inner.add_child(kind_label)
		var name_label := _label(o.parent.title, BASE_TITLE_SIZE, Style.SURFACE_SOLID)
		name_label.position = Vector2(24, 50)
		name_label.size = Vector2(Style.CARD_SIZE.x - 48, 70)
		name_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		name_label.max_lines_visible = 2
		name_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		inner.add_child(name_label)
		var sub := "%s · часть %d" % [Game.tech_name(o.parent.tech), o.parent.part]
		if o.parent.score != null:
			sub = "%s · критики %.1f" % [Game.tech_name(o.parent.tech), o.parent.score.critics]
		var sub_label := _label(sub, Style.FONT_CAPTION, Color(1, 1, 1, 0.75))
		sub_label.position = Vector2(24, Style.CARD_SIZE.y - 24 - 26)
		inner.add_child(sub_label)
		if not o.open:
			var pill := _center_pill(o.lock_reason, &"locked_pill")
			pill.visible = true
			inner.add_child(pill)
	return c


func _center_pill(text: String, meta: StringName) -> Control:
	var pill := HintPill.make(text)
	pill.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	pill.grow_horizontal = Control.GROW_DIRECTION_BOTH
	pill.grow_vertical = Control.GROW_DIRECTION_BOTH
	pill.visible = false
	pill.set_meta(meta, true)
	return pill


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
		if _tech_blocked(selected_entry(1).value):
			_button_label.text = "Нужна другая технология"
		elif base() != null and not base().open:
			_button_label.text = base().lock_reason.capitalize()
		else:
			_button_label.text = "Придёт с прокачкой"
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
	# Колонки: выбранная карточка по центру колонки и крупнее, соседи раздвинуты на её рост.
	for kind in _order:
		if kind != ROW_BASE:
			_captions[kind].text = ROW_LABELS[kind] + (" · как у оригинала" if is_locked_column(kind) else "")
		_animate(_rows[kind], "position:y", _column_offset(kind), animate)
		for i in _cards[kind].size():
			var c: Control = _cards[kind][i]
			_animate(c, "scale", Vector2.ONE * (_select_scale if i == index[kind] else 1.0), animate)
			_animate(c, "position:y", _card_y(kind, i), animate)
			if kind != ROW_BASE:
				_refresh_card_lock(kind, i, c)
	_place_focus_ring(animate)


## Закрытая карточка затемнена, пилюля говорит почему: прокачка или технология оригинала.
func _refresh_card_lock(kind: int, i: int, c: Control) -> void:
	var e := catalogs[kind].entries[i]
	var by_upgrade := not unlocked[kind].has(e.value)
	var by_origin := kind == 1 and not by_upgrade and _tech_blocked(e.value)
	c.modulate.a = Style.DIM_LOCKED if by_upgrade or by_origin else 1.0
	var inner := c.get_child(0)
	for child in inner.get_children():
		if child.has_meta(&"locked_pill"):
			child.visible = by_upgrade
		elif child.has_meta(&"origin_pill"):
			child.visible = by_origin


## Рамка фокуса только на карточках; на кнопке пропадает (плейтест 2026-11-07).
func _place_focus_ring(animate: bool) -> void:
	if focus_row == ROW_BUTTON:
		_focus_ring.visible = false
		return
	var target: Control = _cards[focus_row][index[focus_row]]
	var base_pos := _clips[focus_row].position + Vector2(target.position.x, _column_offset(focus_row) + index[focus_row] * (Style.CARD_SIZE.y + Style.GAP_CARDS))
	var grown := Style.CARD_SIZE * _select_scale
	var rect := Rect2(base_pos - (grown - Style.CARD_SIZE) / 2.0, grown)
	var was_visible := _focus_ring.visible
	_focus_ring.visible = true
	_animate(_focus_ring, "position", rect.position, animate and was_visible)
	_animate(_focus_ring, "size", rect.size, animate and was_visible)


## Сдвиг колонки, при котором выбранная карточка стоит по центру.
func _column_offset(kind: int) -> float:
	return _column_height / 2.0 - Style.CARD_SIZE.y / 2.0 - index[kind] * (Style.CARD_SIZE.y + Style.GAP_CARDS)


## Y карточки в колонке: базовый шаг, соседи выбранной сдвинуты на половину её роста, чтобы
## зазор остался `GAP_CARDS`.
func _card_y(kind: int, i: int) -> float:
	var y := i * (Style.CARD_SIZE.y + Style.GAP_CARDS)
	var grow := Style.CARD_SIZE.y * (_select_scale - 1.0) / 2.0
	if i < index[kind]:
		y -= grow
	elif i > index[kind]:
		y += grow
	return y


func _process(_delta: float) -> void:
	# Границы маски в мировых координатах: карточка двигается при всплытии.
	if _mask != null and _clips[0] != null:
		var top := _clips[0].global_position.y
		_mask.set_shader_parameter("top_px", top)
		_mask.set_shader_parameter("bottom_px", top + _column_height)


## Все потомки карточки рисуются материалом колонки, иначе маска краёв на них не действует.
func _inherit_material(node: CanvasItem) -> void:
	node.use_parent_material = true
	for child in node.get_children():
		if child is CanvasItem:
			_inherit_material(child)


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
