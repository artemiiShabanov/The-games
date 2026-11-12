class_name Bit16Screen
extends SubViewportContainer
## Экран демок 16/32-bit (#95, `docs/specs/demos_catalog.md`): виртуальный экран вдвое мельче
## карточки (832×416 при карточке 1664×832), увеличение ×2 ближайшим соседом; у 8-bit было ×4.
## Спрайт 32×32 на экране того же размера, что 16×16 у 8-bit, но вчетверо подробнее. Три слоя
## `Node2D`: `backdrop` (фон, параллакс), `world` (мир со сдвигом камеры, на него ложится чужая
## палитра), `hud`; демка рисует в колбэках `draw_backdrop`, `draw_world`, `draw_hud`.
## Спрайт это лента кадров 32 пикселя шириной (`frames`, `sprite`). Палитра сеттинга из 16
## цветов, индекс это роль (`K` обводка … `PINE` тень зелени, как в `tools/pixel_sprites16.py`).
## Во встроенном режиме (стрим ленты) увеличение ×1 и экран размером с рамку.

const FRAME := 32
const SCALE := 2
const EMBED_SCALE := 1
## Роли цветов палитры 16/32.
enum { K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, WOOD, BARK, RED, LEAF, PINE }

## Виртуальный экран в пикселях демки.
var view := Vector2(832, 416)
var viewport: SubViewport
var backdrop: Node2D
var world: Node2D
var hud: Node2D
var palette: Array[Color] = []
var draw_backdrop := Callable()
var draw_world := Callable()
var draw_hud := Callable()
## Розовых заглушек нарисовано за прошлый кадр (проверки).
var pink_drawn := 0
var _pinks := 0


## Экран в области `area`: во встроенном режиме мельче и без увеличения.
static func make(area: Vector2, embedded: bool, palette_: Array[Color]) -> Bit16Screen:
	var s := Bit16Screen.new()
	var shrink := EMBED_SCALE if embedded else SCALE
	s.palette = palette_
	s.view = (area / shrink).floor()
	s.position = ((area - s.view * shrink) / 2.0).floor()
	s.size = s.view * shrink
	s.custom_minimum_size = s.size
	s.stretch = true
	s.stretch_shrink = shrink
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	s.mouse_filter = Control.MOUSE_FILTER_IGNORE
	s.viewport = SubViewport.new()
	s.viewport.size = Vector2i(s.view)
	s.viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	s.viewport.snap_2d_transforms_to_pixel = true
	s.add_child(s.viewport)
	s.backdrop = Node2D.new()
	s.backdrop.draw.connect(s._draw_layer.bind(0))
	s.viewport.add_child(s.backdrop)
	s.world = Node2D.new()
	s.world.draw.connect(s._draw_layer.bind(1))
	s.viewport.add_child(s.world)
	s.hud = Node2D.new()
	s.hud.draw.connect(s._draw_layer.bind(2))
	s.viewport.add_child(s.hud)
	return s


func _process(_delta: float) -> void:
	if backdrop != null:
		backdrop.queue_redraw()
		world.queue_redraw()
		hud.queue_redraw()


func _draw_layer(layer: int) -> void:
	if layer == 0:
		_pinks = 0
	var fn: Callable = [draw_backdrop, draw_world, draw_hud][layer]
	if fn.is_valid():
		fn.call([backdrop, world, hud][layer])
	if layer == 2:
		pink_drawn = _pinks


func ink(i: int) -> Color:
	return palette[clampi(i, 0, palette.size() - 1)] if not palette.is_empty() else Color.WHITE


## Кадров в ленте: ширина на 32.
static func frames(tex: Texture2D) -> int:
	return maxi(tex.get_width() / FRAME, 1) if tex != null else 1


## Кадр `frame` ленты `tex` низом по центру в точке `feet`; `scale` увеличение (вид вглубь),
## `flip` зеркало. Высота кадра это высота текстуры: 32, у бойца 64.
func sprite(canvas: CanvasItem, tex: Texture2D, frame: int, feet: Vector2, flip := false, scale := 1.0,
		tint := Color.WHITE) -> void:
	if tex == null:
		return
	var h := float(tex.get_height())
	var src := Rect2((frame % frames(tex)) * FRAME, 0, FRAME, h)
	var w := roundf(FRAME * scale)
	var dst := Rect2(roundf(feet.x - w / 2.0), roundf(feet.y - h * scale), w, roundf(h * scale))
	if flip:
		# Отрицательная ширина отражает текстуру, позиция прямоугольника при этом не сдвигается.
		dst = Rect2(dst.position.x + dst.size.x, dst.position.y, -dst.size.x, dst.size.y)
	canvas.draw_texture_rect_region(tex, dst, src, tint)


## Розовая заглушка вместо спрайта: блок в шашку, чтобы не спутать с вещью из игры.
func pink(canvas: CanvasItem, feet: Vector2, scale := 1.0, height := float(FRAME)) -> void:
	_pinks += 1
	var w := roundf(FRAME * scale * 0.75)
	var h := roundf(height * scale * 0.75)
	var at := Vector2(roundf(feet.x - w / 2.0), roundf(feet.y - h))
	canvas.draw_rect(Rect2(at, Vector2(w, h)), Demo.PINK)
	var cell := maxf(roundf(4.0 * scale), 2.0)
	var y := 0.0
	var row := 0
	while y < h:
		var x := cell if row % 2 == 0 else 0.0
		while x < w:
			canvas.draw_rect(Rect2(at + Vector2(x, y), Vector2(minf(cell, w - x), minf(cell, h - y))), Demo.PINK.darkened(0.25))
			x += cell * 2.0
		y += cell
		row += 1
