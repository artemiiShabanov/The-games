class_name AsciiGrid
extends Node2D
## Текстовый экран ASCII-демок (#88, `docs/specs/demos_catalog.md`): сетка `cols × rows` клеток
## 8×16, в клетке глиф и номер чернил из палитры. Глифы узкие из атласа GNU Unifont
## (`assets/fonts/unifont/glyphs.png`, `tools/ascii_font.py`): один моноширинный шрифт на все
## ASCII-демки, кириллица для легенды. Палитра маленькая: фон `palette[0]` и чернила 1..N, на
## экран обычно один-два цвета (`SettingDef.ascii_palette`). Демка пишет в клетки (`put`,
## `text`, `fill`, `clear`), сетка перерисовывается сама, если что-то поменялось. Мир и HUD в
## одной сетке: движение по клеткам, никаких субпикселей. Розовая заглушка (`pink_placeholders`)
## это чернила `PINK_INK`, цвет `Demo.PINK`.

const CELL := Vector2i(8, 16)
const ATLAS_PATH := "res://assets/fonts/unifont/glyphs.png"
## Чернила розовой заглушки, вне палитры сеттинга.
const PINK_INK := 255
const SPACE := 32
const UNKNOWN := 63  # «?»

static var _atlas: Texture2D
static var _index: Dictionary[int, int] = {}

var cols := 80
var rows := 30
## Фон и чернила: `palette[0]` фон, дальше чернила по номеру.
var palette: Array[Color] = [Color.BLACK, Color.WHITE]
var _glyphs := PackedInt32Array()
var _inks := PackedByteArray()
var _dirty := true


## Сетка `cols_ × rows_` с палитрой; размер узла в пикселях `cols_ * 8 × rows_ * 16`.
static func make(cols_: int, rows_: int, palette_: Array[Color]) -> AsciiGrid:
	var g := AsciiGrid.new()
	g.cols = cols_
	g.rows = rows_
	g.palette = palette_
	g.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	g.clear()
	return g


static func atlas() -> Texture2D:
	if _atlas == null:
		_atlas = load(ATLAS_PATH) as Texture2D
		for i in AsciiCodepoints.CODES.size():
			_index[AsciiCodepoints.CODES[i]] = i
	return _atlas


## Есть ли глиф в атласе (узкий глиф из взятых блоков).
static func has_glyph(ch: String) -> bool:
	atlas()
	return ch.length() == 1 and _index.has(ch.unicode_at(0))


## Клетка атласа под код; неизвестный код рисуется «?».
static func glyph_rect(code: int) -> Rect2:
	atlas()
	var i: int = _index.get(code, _index.get(UNKNOWN, 0))
	return Rect2(Vector2((i % AsciiCodepoints.PER_ROW) * CELL.x, (i / AsciiCodepoints.PER_ROW) * CELL.y), CELL)


## Битмап глифа 8×16 построчно (для проверок читаемости): true там, где пиксель горит.
static func glyph_bits(ch: String) -> Array[bool]:
	var img := atlas().get_image()
	var r := glyph_rect(ch.unicode_at(0))
	var out: Array[bool] = []
	for y in CELL.y:
		for x in CELL.x:
			out.append(img.get_pixel(int(r.position.x) + x, int(r.position.y) + y).a > 0.5)
	return out


## Размер в пикселях без масштаба.
func pixel_size() -> Vector2:
	return Vector2(cols * CELL.x, rows * CELL.y)


func clear() -> void:
	_glyphs.resize(cols * rows)
	_glyphs.fill(SPACE)
	_inks.resize(cols * rows)
	_inks.fill(1)
	_dirty = true


func inside(x: int, y: int) -> bool:
	return x >= 0 and y >= 0 and x < cols and y < rows


## Глиф в клетку; за краем ничего.
func put(x: int, y: int, ch: String, ink := 1) -> void:
	if not inside(x, y) or ch.is_empty():
		return
	var i := y * cols + x
	var code := ch.unicode_at(0)
	if _glyphs[i] == code and _inks[i] == ink:
		return
	_glyphs[i] = code
	_inks[i] = ink
	_dirty = true


## Строка с клетки `x, y` вправо, обрезается краем.
func text(x: int, y: int, s: String, ink := 1) -> void:
	for i in s.length():
		put(x + i, y, s[i], ink)


## Строка по центру ряда `y`.
func text_center(y: int, s: String, ink := 1) -> void:
	text((cols - s.length()) / 2, y, s, ink)


## Прямоугольник клеток одним глифом.
func fill(r: Rect2i, ch: String, ink := 1) -> void:
	for y in range(r.position.y, r.end.y):
		for x in range(r.position.x, r.end.x):
			put(x, y, ch, ink)


## Глиф в клетке («» за краем).
func at(x: int, y: int) -> String:
	return char(_glyphs[y * cols + x]) if inside(x, y) else ""


func ink_at(x: int, y: int) -> int:
	return _inks[y * cols + x] if inside(x, y) else 0


## Вся сетка строками, для дампов и тестов.
func dump() -> String:
	var lines: Array[String] = []
	for y in rows:
		var s := ""
		for x in cols:
			s += char(_glyphs[y * cols + x])
		lines.append(s)
	return "\n".join(lines)


func _process(_delta: float) -> void:
	if _dirty:
		_dirty = false
		queue_redraw()


func _draw() -> void:
	var tex := atlas()
	draw_rect(Rect2(Vector2.ZERO, pixel_size()), palette[0])
	for y in rows:
		for x in cols:
			var i := y * cols + x
			var code := _glyphs[i]
			if code == SPACE:
				continue
			var ink := int(_inks[i])
			var color := Demo.PINK if ink == PINK_INK else palette[clampi(ink, 0, palette.size() - 1)]
			draw_texture_rect_region(tex, Rect2(Vector2(x * CELL.x, y * CELL.y), CELL), glyph_rect(code), color)
