class_name CoverFace
extends Control
## Рисунок одной стороны обложки поверх фона (`docs/specs/cover.md`): стикеры, название, окна
## кадров и копирайт. Живёт в своём прозрачном вьюпорте, `CoverBox` кладёт его текстуру на грань
## коробки поверх фона с эффектом. Координаты предметов в долях лица.

enum Kind { FRONT, BACK, SPINE }

const NONE := -1
const TITLE := -2
const STICKER_SHADER := preload("res://scripts/cover/cover_sticker.gdshader")
## Окна кадров на обороте: центр в долях лица, ширина в долях ширины, поворот в градусах.
const SHOT_SLOTS: Array[Array] = [[Vector2(0.36, 0.2), 0.56, -3.0], [Vector2(0.62, 0.44), 0.56, 2.5]]
const SHOT_BORDER := 6.0
const STRIP_HEIGHT := 70.0
const INK := Color("#1C1B19")

var kind := Kind.FRONT
var record: GameRecord
var studio := ""
var cover: Dictionary = {}
## Выбранный предмет: `NONE`, `TITLE` или номер стикера в `cover.stickers`; рамка только в редакторе.
var selected := NONE

## Предметы стороны: номер стикера (или `TITLE`) и его узел, в порядке рисования.
var _items: Array[Array] = []
var _frame: Control

static var _shot_cache: Dictionary[String, Texture2D] = {}
static var _genres: Catalog


func setup(kind_: Kind, record_: GameRecord, studio_: String) -> void:
	kind = kind_
	record = record_
	studio = studio_
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var t := CoverData.tuning()
	size = Vector2(t.face_px) if kind != Kind.SPINE else Vector2(t.case_depth * t.px_per_unit, t.face_px.y)


func set_cover(cover_: Dictionary) -> void:
	cover = cover_
	rebuild()


func select(index: int) -> void:
	selected = index
	if _frame != null:
		_frame.queue_redraw()


## Собрать сторону заново по словарю обложки.
func rebuild() -> void:
	for child in get_children():
		remove_child(child)
		child.queue_free()
	_items.clear()
	_frame = null
	if record == null:
		return
	match kind:
		Kind.FRONT:
			_add_stickers(CoverData.Side.FRONT)
			_add_title()
		Kind.BACK:
			_add_shots()
			_add_stickers(CoverData.Side.BACK)
			_add_strip()
		Kind.SPINE:
			_add_spine()
	if kind != Kind.SPINE:
		_frame = Control.new()
		_frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_frame.size = size
		_frame.draw.connect(_draw_frame)
		add_child(_frame)


## Предмет под точкой `uv` (доли лица), верхний первым; `NONE`, если пусто.
func object_at(uv: Vector2) -> int:
	var p := uv * size
	for i in range(_items.size() - 1, -1, -1):
		var node: Control = _items[i][1]
		var local := node.get_transform().affine_inverse() * p
		if Rect2(Vector2.ZERO, node.size).grow(6.0).has_point(local):
			return _items[i][0]
	return NONE


func _node_of(index: int) -> Control:
	for item in _items:
		if item[0] == index:
			return item[1]
	return null


# --- Стикеры ------------------------------------------------------------------------------------

func _add_stickers(side: int) -> void:
	var list := CoverData.stickers(cover)
	for i in list.size():
		var s: Dictionary = list[i]
		if int(s.get("side", 0)) != side:
			continue
		var view := StickerView.new()
		view.setup(record, s, size)
		add_child(view)
		_items.append([i, view])


class StickerView:
	extends Control
	## Один стикер: картинка со своим шейдером обводки или контуры примитива.

	var tex: Texture2D
	var lines: Array[PackedVector2Array] = []
	var ink := Color.WHITE
	var style := 0
	var center := Vector2.ZERO
	var long_side := 100.0
	var _bounds := Rect2()

	func setup(record: GameRecord, s: Dictionary, face: Vector2) -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE
		var id := String(s.get("id", ""))
		style = int(s.get("style", 0))
		center = Vector2(float(s.get("x", 0.5)), float(s.get("y", 0.5))) * face
		long_side = CoverData.tuning().sticker_base * face.x * float(s.get("size", 1.0))
		rotation = deg_to_rad(float(s.get("rot", 0.0)))
		if CoverStickers.is_contour(record.tech):
			lines = CoverStickers.contours(record.setting, id)
			ink = CoverStickers.contour_color(record.setting, id)
			var first := true
			for line in lines:
				for p in line:
					_bounds = Rect2(p, Vector2.ZERO) if first else _bounds.expand(p)
					first = false
		else:
			tex = CoverStickers.texture(record.setting, record.tech, id)
			if tex != null:
				tex.changed.connect(_layout)
				texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR if CoverStickers.smooth(record.tech) else CanvasItem.TEXTURE_FILTER_NEAREST
				var mat := ShaderMaterial.new()
				mat.shader = CoverFace.STICKER_SHADER
				mat.set_shader_parameter("mode", style)
				mat.set_shader_parameter("width", CoverStickers.outline_texels(record.tech))
				mat.set_shader_parameter("line", Color.WHITE if style == 1 else CoverFace.INK)
				material = mat
		_layout()

	## Поставить центром в `at` с длинной стороной `long_px` (миниатюра в лотке редактора).
	func place(at: Vector2, long_px: float) -> void:
		center = at
		long_side = long_px
		_layout()

	func _layout() -> void:
		var shape := Vector2.ONE
		if tex != null:
			shape = Vector2(tex.get_size())
		elif _bounds.has_area():
			shape = _bounds.size
		var k := long_side / maxf(maxf(shape.x, shape.y), 1.0)
		size = shape * k
		pivot_offset = size / 2.0
		position = center - size / 2.0
		queue_redraw()

	func _draw() -> void:
		if tex != null:
			draw_texture_rect(tex, Rect2(Vector2.ZERO, size), false)
			return
		if lines.is_empty() or not _bounds.has_area():
			return
		var k := size.x / _bounds.size.x
		var width := clampf(size.x * 0.035, 2.0, 7.0)
		# Обводка и тень ложатся под луч более толстой линией.
		if style == 1 or style == 2:
			_stroke(k, Vector2.ZERO, width * 3.2, Color.WHITE if style == 1 else CoverFace.INK)
		elif style == 3:
			_stroke(k, Vector2(width, width * 1.4), width * 1.4, Color(0, 0, 0, 0.45))
		_stroke(k, Vector2.ZERO, width * 2.6, Color(ink, 0.22))
		_stroke(k, Vector2.ZERO, width, ink)

	func _stroke(k: float, shift: Vector2, width: float, color: Color) -> void:
		for line in lines:
			var pts := PackedVector2Array()
			for p in line:
				pts.append((p - _bounds.position) * k + shift)
			if pts.size() < 2:
				continue
			pts.append(pts[0])
			draw_polyline(pts, color, width, true)
			for p in pts:
				draw_circle(p, width * 0.5, color)


# --- Название ----------------------------------------------------------------------------------

func _title_label(font_index: int, px: int, ink: Color, style: int, max_width: float) -> Label:
	var l := Label.new()
	l.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var text := record.title
	if CoverData.font_caps(font_index):
		text = text.to_upper()
	var font := CoverData.font(font_index)
	l.text = text
	l.add_theme_font_override("font", font)
	l.add_theme_font_size_override("font_size", px)
	l.add_theme_color_override("font_color", ink)
	l.add_theme_constant_override("line_spacing", -roundi(px * 0.12))
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	var outline := maxi(roundi(px * 0.22), 4)
	match style:
		1, 2:
			l.add_theme_constant_override("outline_size", outline)
			l.add_theme_color_override("font_outline_color", Color.WHITE if style == 1 else INK)
		3:
			l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.5))
			l.add_theme_constant_override("shadow_offset_x", maxi(px / 16, 2))
			l.add_theme_constant_override("shadow_offset_y", maxi(px / 10, 3))
	var one_line := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, px).x
	var w := minf(one_line + outline * 2.0, max_width)
	if max_width > 0.0 and one_line + outline * 2.0 > max_width:
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var box := font.get_multiline_string_size(text, HORIZONTAL_ALIGNMENT_CENTER, w if max_width > 0.0 else -1.0, px)
	l.size = Vector2(w if max_width > 0.0 else one_line + outline * 2.0, box.y + outline)
	l.pivot_offset = l.size / 2.0
	return l


func _add_title() -> void:
	var t := CoverData.title(cover)
	var tune := CoverData.tuning()
	var px := roundi(tune.title_px * float(t.get("size", 1.0)))
	var l := _title_label(int(t.get("font", 0)), px, CoverData.color(t, "color"), int(t.get("style", 0)), size.x * 0.94)
	l.position = Vector2(float(t.get("x", 0.5)), float(t.get("y", 0.2))) * size - l.size / 2.0
	l.rotation = deg_to_rad(float(t.get("rot", 0.0)))
	add_child(l)
	_items.append([TITLE, l])


## Корешок: название одной строкой снизу вверх, шрифт и цвет как на лицевой.
func _add_spine() -> void:
	var t := CoverData.title(cover)
	var px := roundi(size.x * 0.5)
	var style := int(t.get("style", 0))
	var l := _title_label(int(t.get("font", 0)), px, CoverData.color(t, "color"), style if style != 3 else 0, 0.0)
	var room := size.y * 0.86
	if l.size.x > room:
		l.scale = Vector2.ONE * room / l.size.x
	l.position = size / 2.0 - l.size / 2.0
	l.rotation = -PI / 2.0
	add_child(l)


# --- Оборот ------------------------------------------------------------------------------------

func _add_shots() -> void:
	var paths := CoverData.shots(cover)
	for i in SHOT_SLOTS.size():
		var slot: Array = SHOT_SLOTS[i]
		var w: float = size.x * slot[1]
		var box := Vector2(w, w * 9.0 / 16.0)
		var holder := Panel.new()
		holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
		holder.add_theme_stylebox_override("panel", Style.flat(Color.WHITE, 4, Color.TRANSPARENT, 0))
		holder.size = box + Vector2.ONE * SHOT_BORDER * 2.0
		holder.pivot_offset = holder.size / 2.0
		holder.position = (slot[0] as Vector2) * size - holder.size / 2.0
		holder.rotation = deg_to_rad(slot[2])
		add_child(holder)
		var tex := _shot(String(paths[i]) if i < paths.size() else "")
		if tex != null:
			var r := TextureRect.new()
			r.texture = tex
			r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			r.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
			r.position = Vector2.ONE * SHOT_BORDER
			r.size = box
			r.clip_contents = true
			r.mouse_filter = Control.MOUSE_FILTER_IGNORE
			holder.add_child(r)
		else:
			# Кадра нет: плашка цвета жанра с технологией, как в галерее.
			var plate := Panel.new()
			plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
			plate.add_theme_stylebox_override("panel", Style.flat(_genre_color(), 0, Color.TRANSPARENT, 0))
			plate.position = Vector2.ONE * SHOT_BORDER
			plate.size = box
			holder.add_child(plate)
			var l := Label.new()
			l.text = Game.tech_name(record.tech)
			l.add_theme_font_override("font", Jelly.fun_font(800))
			l.add_theme_font_size_override("font_size", 28)
			l.add_theme_color_override("font_color", Color(1, 1, 1, 0.7))
			l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			l.size = box
			l.mouse_filter = Control.MOUSE_FILTER_IGNORE
			plate.add_child(l)


## Полоса копирайта внизу оборота: студия, жанр и технология, штрихкод от сида. Не убирается.
func _add_strip() -> void:
	var strip := Control.new()
	strip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	strip.position = Vector2(0.0, size.y - STRIP_HEIGHT)
	strip.size = Vector2(size.x, STRIP_HEIGHT)
	strip.draw.connect(_draw_strip.bind(strip))
	add_child(strip)
	var who := "© " + (studio if studio != "" else "Studio")
	var top := _strip_label(who, 20, Color.WHITE)
	top.position = Vector2(24.0, 10.0)
	strip.add_child(top)
	var what := _strip_label("%s · %s" % [Game.genre_name(record.genre), Game.tech_name(record.tech)], 16, Color(1, 1, 1, 0.6))
	what.position = Vector2(24.0, 38.0)
	strip.add_child(what)


func _strip_label(text: String, px: int, ink: Color) -> Label:
	var l := Label.new()
	l.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	l.text = text
	l.add_theme_font_size_override("font_size", px)
	l.add_theme_color_override("font_color", ink)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.clip_text = true
	l.size = Vector2(size.x - 170.0, px + 8.0)
	return l


func _draw_strip(strip: Control) -> void:
	strip.draw_rect(Rect2(Vector2.ZERO, strip.size), Color(INK, 0.86))
	var code := Rect2(strip.size.x - 132.0, 12.0, 108.0, STRIP_HEIGHT - 24.0)
	strip.draw_rect(code, Color.WHITE)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash([record.seed, "barcode"])
	var x := code.position.x + 6.0
	while x < code.end.x - 8.0:
		var w := float(rng.randi_range(1, 3))
		strip.draw_rect(Rect2(x, code.position.y + 5.0, w, code.size.y - 10.0), INK)
		x += w + float(rng.randi_range(1, 3))


func _genre_color() -> Color:
	if _genres == null:
		_genres = Catalog.load_kind(CatalogEntry.Kind.GENRE)
	var e := _genres.by_value(int(record.genre))
	return e.color if e != null else Style.INK_3


static func _shot(path: String) -> Texture2D:
	if path == "":
		return null
	if _shot_cache.has(path):
		return _shot_cache[path]
	if not FileAccess.file_exists(path):
		return null
	var img := Image.load_from_file(path)
	if img == null or img.is_empty():
		return null
	var tex := ImageTexture.create_from_image(img)
	_shot_cache[path] = tex
	return tex


# --- Рамка выбранного ---------------------------------------------------------------------------

func _draw_frame() -> void:
	var node := _node_of(selected)
	if node == null:
		return
	_frame.draw_set_transform(node.position + node.pivot_offset, node.rotation, node.scale)
	var r := Rect2(-node.size / 2.0, node.size).grow(8.0)
	_frame.draw_rect(r, Color(INK, 0.9), false, 5.0)
	_frame.draw_rect(r, Color.WHITE, false, 2.0)
	for corner: Vector2 in [r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y)]:
		_frame.draw_circle(corner, 7.0, INK)
		_frame.draw_circle(corner, 5.0, Color.WHITE)
