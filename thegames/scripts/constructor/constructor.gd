class_name Constructor
extends Control
## Экран конструктора, спека `docs/specs/constructor.md`, концепты `01`, `01b`, плейтест
## 2026-11-07. Весь экран идёт в большой карточке `CardFrame` поверх студии, как спринты;
## над карточкой пилюли «Релиз N · Следующая игра» слева и денег справа. Внутри слева три
## карусели (жанр, технология, сеттинг): выбранная карточка по центру ряда, соседние гаснут к
## краям, под ними кнопка «В разработку»; справа карточка сметы с заголовком на две строки и
## числами, которые прокручиваются за 240 мс. Влево и вправо листают, вверх и вниз переводят
## фокус по рядам и на кнопку, A на карусели переводит фокус на кнопку, A на кнопке отдаёт
## `game_configured`, R другое название. Рамка фокуса только на карточках; на кнопке она
## пропадает, а кнопка становится тёмной. Неоткрытые карточки затемнены с пилюлей «придёт с
## прокачкой», остаются в карусели и получают фокус; с ними кнопка закрыта. Денег не хватает:
## остаток `danger`, кнопка серая с суммой нехватки и трясётся. Деньги не списывает: это
## делает хозяин по сигналу. Карточки каруселей пока с крупной буквой вместо иллюстрации.

signal game_configured(config: GameConfig)
signal estimate_changed(estimate: Estimate)

const ROWS := 3
const ROW_BUTTON := 3
const ROW_LABELS: Array[String] = ["Жанр", "Технология", "Сеттинг"]
const ROW_TOP := 40
const ROW_STEP := 234
const ROW_HEIGHT := 214
const CARD_LABEL_SIZE := 30
const TITLE_FONT := 44
const TOTAL_FONT := 72
const BUTTON_WIDTH := 480
const BUTTON_BOTTOM_GAP := 20
## Ширина градиента по краям ряда: карточки растворяются, а не режутся.
const EDGE_FADE := 140.0
## Маска краёв ряда: альфа по мировой X между `left` и `right` с плавными краями `fade`.
const FADE_SHADER := """
shader_type canvas_item;
uniform float left_px = 0.0;
uniform float right_px = 1000.0;
uniform float fade_px = 140.0;
varying vec2 world_pos;
void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
}
void fragment() {
	float a = smoothstep(0.0, fade_px, world_pos.x - left_px) * smoothstep(0.0, fade_px, right_px - world_pos.x);
	COLOR.a *= a;
}
"""

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

var card: CardFrame
var _inner := Vector2.ZERO
var _left_width := 0.0
var _rows: Array[Control] = []
var _clips: Array[Control] = []
var _cards: Array[Array] = [[], [], []]
var _focus_ring: Panel
var _title_label: Label
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
	# Маска краёв рядов: границы ряда в мировых координатах известны из геометрии карточки.
	var shader := Shader.new()
	shader.code = FADE_SHADER
	var mask := ShaderMaterial.new()
	mask.shader = shader
	var row_left := CardFrame.rect_in(Vector2(Style.SCREEN)).position.x + Style.PAD_CARD
	mask.set_shader_parameter("left_px", row_left)
	mask.set_shader_parameter("right_px", row_left + _left_width)
	mask.set_shader_parameter("fade_px", EDGE_FADE)

	_focus_ring = Panel.new()
	_focus_ring.add_theme_stylebox_override("panel", Style.focus_ring(Style.R_CARD))
	_focus_ring.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_focus_ring.visible = false

	for kind in ROWS:
		var caption := _label(ROW_LABELS[kind], Style.FONT_CAPTION, Style.INK_2)
		caption.position = Vector2(0, ROW_TOP + kind * ROW_STEP - 30)
		content.add_child(caption)
		var clip := Control.new()
		clip.position = Vector2(0, ROW_TOP + kind * ROW_STEP)
		clip.size = Vector2(_left_width, ROW_HEIGHT)
		clip.clip_contents = true
		clip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		content.add_child(clip)
		_clips.append(clip)
		var row := Control.new()
		row.mouse_filter = Control.MOUSE_FILTER_IGNORE
		row.material = mask
		clip.add_child(row)
		_rows.append(row)
		for i in catalogs[kind].entries.size():
			var c := _make_card(catalogs[kind].entries[i], is_unlocked(kind, i))
			c.position = Vector2(i * (Style.CARD_SIZE.x + Style.GAP_CARDS), 12)
			row.add_child(c)
			_cards[kind].append(c)
			_inherit_material(c)
	content.add_child(_focus_ring)

	_button = PanelContainer.new()
	_button.custom_minimum_size = Vector2(BUTTON_WIDTH, Style.BUTTON_HEIGHT)
	_button.size = Vector2(BUTTON_WIDTH, Style.BUTTON_HEIGHT)
	_button.position = Vector2((_left_width - BUTTON_WIDTH) / 2.0, _inner.y - Style.BUTTON_HEIGHT - BUTTON_BOTTOM_GAP)
	_button.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_button_label = _label("В разработку", Style.FONT_H2, Style.SURFACE_SOLID)
	_button_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_button_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_button.add_child(_button_label)
	content.add_child(_button)
	_build_estimate(content)

	var hints := HBoxContainer.new()
	hints.alignment = BoxContainer.ALIGNMENT_CENTER
	hints.add_theme_constant_override("separation", 16)
	hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hints.offset_top = -(Style.PILL_HEIGHT + 16)
	hints.offset_bottom = -16
	hints.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hints.add_child(HintPill.make("← → листать"))
	hints.add_child(HintPill.make("↑ ↓ ряд и кнопка"))
	hints.add_child(HintPill.make("A в разработку"))
	hints.add_child(HintPill.make("R название"))
	add_child(hints)


## Карточка карусели 260×190: цветной фон, крупная буква вместо иллюстрации, название внизу.
func _make_card(e: CatalogEntry, open: bool) -> Control:
	var c := PanelContainer.new()
	c.custom_minimum_size = Style.CARD_SIZE
	c.size = Style.CARD_SIZE
	c.pivot_offset = Style.CARD_SIZE / 2.0
	c.add_theme_stylebox_override("panel", Style.flat(e.color, Style.R_CARD, Color.TRANSPARENT, 0))
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.set_meta(&"open", open)
	if not open:
		c.modulate.a = Style.DIM_LOCKED
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
	if not open:
		var pill := HintPill.make("придёт с прокачкой")
		pill.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
		pill.grow_horizontal = Control.GROW_DIRECTION_BOTH
		pill.grow_vertical = Control.GROW_DIRECTION_BOTH
		inner.add_child(pill)
	return c


func _build_estimate(content: Control) -> void:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.card(true))
	panel.position = Vector2(_left_width + Style.GAP_CARDS, 0)
	panel.size = Vector2(Style.ESTIMATE_WIDTH, _inner.y - Style.BUTTON_HEIGHT - BUTTON_BOTTOM_GAP)
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
	_roll(&"sprints", _sprints_value, estimate.sprints, animate, func(v: float) -> String: return str(int(round(v))))
	_roll(&"price", _price_value, estimate.sprint_price, animate, _money_text)
	_roll(&"total", _total_value, estimate.total, animate, _money_text)
	_roll(&"remainder", _remainder_value, estimate.remainder, animate, _money_text)
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
	var on_button := focus_row == ROW_BUTTON
	# Активная: тёмная в фокусе, `surface-2` с чернилами без фокуса; закрытая: `surface-2` с `ink-3`.
	var bg := Style.INK if active and on_button else Style.SURFACE_2
	var ink := Style.INK_3
	if active:
		ink = Style.SURFACE_SOLID if on_button else Style.INK
	_button.add_theme_stylebox_override("panel", Style.flat(bg, Style.R_CTL, Style.FOCUS if on_button and not active else Color.TRANSPARENT, 0))
	_button_label.add_theme_color_override("font_color", ink)
	# Карусели: выбранная карточка по центру ряда.
	var step := Style.CARD_SIZE.x + Style.GAP_CARDS
	for kind in ROWS:
		var target_x := _left_width / 2.0 - Style.CARD_SIZE.x / 2.0 - index[kind] * step
		_animate(_rows[kind], "position:x", target_x, animate)
		for i in _cards[kind].size():
			var c: Control = _cards[kind][i]
			var focused := kind == focus_row and i == index[kind]
			_animate(c, "scale", Vector2.ONE * (Style.FOCUS_SCALE if focused else 1.0), animate)
	_place_focus_ring(animate)


## Рамка фокуса только на карточках; на кнопке пропадает (плейтест 2026-11-07).
func _place_focus_ring(animate: bool) -> void:
	if focus_row == ROW_BUTTON:
		_focus_ring.visible = false
		return
	var step := Style.CARD_SIZE.x + Style.GAP_CARDS
	var target: Control = _cards[focus_row][index[focus_row]]
	var row_x := _left_width / 2.0 - Style.CARD_SIZE.x / 2.0 - index[focus_row] * step
	var pos := _clips[focus_row].position + Vector2(row_x + target.position.x, target.position.y)
	var grown := Style.CARD_SIZE * Style.FOCUS_SCALE
	var rect := Rect2(pos - (grown - Style.CARD_SIZE) / 2.0, grown)
	var was_visible := _focus_ring.visible
	_focus_ring.visible = true
	_animate(_focus_ring, "position", rect.position, animate and was_visible)
	_animate(_focus_ring, "size", rect.size, animate and was_visible)


## Все потомки карточки рисуются материалом ряда, иначе маска краёв на них не действует.
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
