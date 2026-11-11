class_name CardColumns
extends Control
## Вертикальные карусели карточек 260×190 рядом (STYLE, плейтест 2026-11-07): выбранная
## карточка колонки стоит по центру и увеличена так, что выбранные с полями `GAP_CARDS`
## заполняют ширину области; соседи обычного размера раздвинуты на её рост и растворяются к
## верху и низу градиентной маской. Фокус толщиной на выбранной карточке колонки `focus_col`
## (мармелад), при `focus_col = -1` фокуса нет. Содержимое карточек, их блокировки и ввод решает хозяин:
## он даёт готовые `Control` размером `Style.CARD_SIZE`, двигает `index` и зовёт `refresh`.
## Используют конструктор и экран основы (#24).

const COLUMN_TOP := 36
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

var cards: Array[Array] = []
var index: Array[int] = []
var focus_col := -1
var slot := 0.0
var select_scale := 1.0

var _captions: Array[Label] = []
var _clips: Array[Control] = []
var _rows: Array[Control] = []
var _mask: ShaderMaterial
var _column_height := 0.0
var _poked := Vector2i(-1, -1)
var _lifts: Array[Array] = []


## Построить колонки в области `area` (размер этого узла): подписи и карточки по колонкам.
func build(labels: Array[String], cards_: Array[Array], area: Vector2) -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	size = area
	cards = cards_
	index = []
	for c in cards:
		index.append(0)
	var shader := Shader.new()
	shader.code = FADE_SHADER
	_mask = ShaderMaterial.new()
	_mask.shader = shader
	_mask.set_shader_parameter("fade_px", EDGE_FADE)
	_column_height = area.y - COLUMN_TOP
	var n := labels.size()
	slot = (area.x - n * Style.GAP_CARDS) / n
	select_scale = slot / Style.CARD_SIZE.x
	var step_x := slot + Style.GAP_CARDS
	var x0 := float(Style.GAP_CARDS)
	var card_x := 12.0 + (slot - Style.CARD_SIZE.x) / 2.0
	for col in n:
		var caption := Label.new()
		caption.text = labels[col]
		caption.add_theme_font_size_override("font_size", Style.FONT_CAPTION)
		caption.add_theme_color_override("font_color", Style.INK_2)
		caption.mouse_filter = Control.MOUSE_FILTER_IGNORE
		caption.position = Vector2(x0 + col * step_x, 0)
		caption.size = Vector2(slot, 24)
		caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		add_child(caption)
		_captions.append(caption)
		var clip := Control.new()
		clip.position = Vector2(x0 + col * step_x - 12, COLUMN_TOP)
		clip.size = Vector2(slot + 24, _column_height)
		clip.clip_contents = true
		clip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(clip)
		_clips.append(clip)
		var column := Control.new()
		column.mouse_filter = Control.MOUSE_FILTER_IGNORE
		column.material = _mask
		clip.add_child(column)
		_rows.append(column)
		var lifts: Array = []
		_lifts.append(lifts)
		for i in cards[col].size():
			var c: Control = cards[col][i]
			var l := JellyLift.add_to(c, Style.R_CARD)
			# Подбородок толще (#84): добавка в пикселях экрана, карточка в фокусе увеличена.
			l.extra = Jelly.tuning().carousel_chin_px / maxf(select_scale, 0.01)
			lifts.append(l)
			c.pivot_offset = Style.CARD_SIZE / 2.0
			c.position = Vector2(card_x, _card_y(col, i))
			column.add_child(c)
			_inherit_material(c)
			_scaled_font(c)
			# Мармелад: поле меньше половины зазора, соседи не задеваются.
			Jelly.attach(c, Style.R_CARD, Style.GAP_CARDS * 0.45)


func count(col: int) -> int:
	return cards[col].size()


## Колонка под точкой экрана или −1.
func column_at(event: InputEvent) -> int:
	for col in _clips.size():
		if MouseUi.hit(_clips[col], event):
			return col
	return -1


## Карточка под точкой экрана: (колонка, индекс) или (−1, −1). Только внутри своей колонки.
func card_at(event: InputEvent) -> Vector2i:
	var col := column_at(event)
	if col < 0:
		return Vector2i(-1, -1)
	for i in cards[col].size():
		if MouseUi.hit(cards[col][i], event):
			return Vector2i(col, i)
	return Vector2i(col, -1)


func set_caption(col: int, text: String) -> void:
	_captions[col].text = text


## Сдвинуть выбор колонки; true, если выбор изменился.
func step(col: int, dir: int) -> bool:
	var next := clampi(index[col] + dir, 0, count(col) - 1)
	if next == index[col]:
		return false
	index[col] = next
	return true


## Расставить колонки: выбранная по центру и крупнее, соседи раздвинуты, рамка фокуса.
func refresh(animate: bool) -> void:
	# Вздрог карточки, которая стала выбранной в фокусной колонке или получила фокус.
	if animate and focus_col >= 0 and focus_col < cards.size() and not cards[focus_col].is_empty():
		var key := Vector2i(focus_col, index[focus_col])
		if key != _poked:
			Jelly.poke(cards[focus_col][index[focus_col]])
	_poked = Vector2i(focus_col, index[focus_col] if focus_col >= 0 and focus_col < cards.size() else -1)
	for col in cards.size():
		_animate(_rows[col], "position:y", _column_offset(col), animate)
		for i in cards[col].size():
			var c: Control = cards[col][i]
			_animate(c, "scale", Vector2.ONE * (select_scale if i == index[col] else 1.0), animate)
			_animate(c, "position:y", _card_y(col, i), animate)
	_place_focus_ring(animate)


## Фокус толщиной (мармелад, 2026-11-09): выбранная карточка фокусной колонки поднята на
## бортике, синей рамки нет.
func _place_focus_ring(_animate_unused: bool) -> void:
	for col in _lifts.size():
		for i in _lifts[col].size():
			(_lifts[col][i] as JellyLift).focused = col == focus_col and i == index[col]


## Сдвиг колонки, при котором выбранная карточка стоит по центру.
func _column_offset(col: int) -> float:
	return _column_height / 2.0 - Style.CARD_SIZE.y / 2.0 - index[col] * (Style.CARD_SIZE.y + Style.GAP_CARDS)


## Y карточки в колонке: базовый шаг, соседи выбранной сдвинуты на половину её роста, чтобы
## зазор остался `GAP_CARDS`.
func _card_y(col: int, i: int) -> float:
	var y := i * (Style.CARD_SIZE.y + Style.GAP_CARDS)
	var grow := Style.CARD_SIZE.y * (select_scale - 1.0) / 2.0
	if i < index[col]:
		y -= grow
	elif i > index[col]:
		y += grow
		# Под выбранной карточкой фокусной колонки толстый подбородок (#84): соседи ниже
		# уходят на его добавку, зазор остаётся `GAP_CARDS`.
		if col == focus_col:
			y += Jelly.tuning().carousel_chin_px
	return y


func _process(_delta: float) -> void:
	# Границы маски в мировых координатах: карточка двигается при всплытии.
	if _mask != null and not _clips.is_empty():
		var top := _clips[0].global_position.y
		_mask.set_shader_parameter("top_px", top)
		_mask.set_shader_parameter("bottom_px", top + _column_height)


## Карточки увеличиваются масштабом: их подписи растром с запасом (`Jelly.fun_font_scaled`),
## иначе выбранная карточка мылится. Жирность и размер подписей не меняются.
func _scaled_font(node: Node) -> void:
	if node is Label:
		var l := node as Label
		l.add_theme_font_override("font", Jelly.fun_font_scaled(700))
	for child in node.get_children():
		_scaled_font(child)


## Все потомки карточки рисуются материалом колонки, иначе маска краёв на них не действует.
func _inherit_material(node: CanvasItem) -> void:
	node.use_parent_material = true
	for child in node.get_children():
		if child is CanvasItem:
			_inherit_material(child)


func _animate(node: Object, prop: String, value: Variant, animate: bool) -> void:
	if animate and not Debug.skip_cards:
		create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC).tween_property(node, prop, value, Style.FOCUS_MOVE_SECONDS)
	else:
		node.set_indexed(prop, value)


# --- Фабрики карточек для хозяев -----------------------------------------------------------------

## Пустая цветная карточка 260×190 с внутренним `Control` для содержимого.
static func make_card(color: Color) -> PanelContainer:
	var c := PanelContainer.new()
	c.custom_minimum_size = Style.CARD_SIZE
	c.size = Style.CARD_SIZE
	c.pivot_offset = Style.CARD_SIZE / 2.0
	c.add_theme_stylebox_override("panel", Style.flat(color, Style.R_CARD, Color.TRANSPARENT, 0))
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var inner := Control.new()
	inner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.add_child(inner)
	return c


static func inner_of(c: Control) -> Control:
	return c.get_child(0) as Control


## Пилюля по центру карточки, скрытая; хозяин включает по `meta`.
static func center_pill(text: String, meta: StringName) -> Control:
	var pill := HintPill.make(text)
	pill.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	pill.grow_horizontal = Control.GROW_DIRECTION_BOTH
	pill.grow_vertical = Control.GROW_DIRECTION_BOTH
	pill.visible = false
	pill.set_meta(meta, true)
	return pill


## Показать на карточке ровно одну пилюлю по `meta` (или ни одной при пустом) и затемнить.
static func set_card_lock(c: Control, meta: StringName) -> void:
	# Мармелад: прозрачность карточки и бортика наложилась бы ободком на стыке, поэтому
	# затемнение белой вуалью сверху; на белом поле выглядит так же, как `DIM_LOCKED`.
	var veil := _veil_of(c)
	veil.visible = meta != &""
	c.set_meta(&"jelly_veil", (1.0 - Style.DIM_LOCKED) if meta != &"" else 0.0)
	for child in c.get_children():
		if child is JellyLift:
			(child as JellyLift).queue_redraw()
	for child in inner_of(c).get_children():
		if child is HintPill:
			child.visible = meta != &"" and child.has_meta(meta)


static func _veil_of(c: Control) -> Panel:
	for child in c.get_children():
		if child is Panel and child.has_meta(&"veil"):
			return child
	var veil := Panel.new()
	veil.set_meta(&"veil", true)
	veil.add_theme_stylebox_override("panel", Style.flat(Color(Style.SURFACE_SOLID, 1.0 - Style.DIM_LOCKED), Style.R_CARD, Color.TRANSPARENT, 0))
	veil.mouse_filter = Control.MOUSE_FILTER_IGNORE
	veil.size = Style.CARD_SIZE
	veil.use_parent_material = true
	c.add_child(veil)
	# Пилюля причины под вуалью тоже затемнена, как раньше вся карточка.
	return veil


static func label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l
