class_name Portrait
extends Control
## Пиксельный портрет внешнего персонажа (#140): сетка 24×24, лицо акцентом, чёрный контур.
## Лист `res://assets/portraits/<id>.png` пишет `tools/portraits.py`: столбцы «обычный, моргнул,
## говорит», строки настроений −1, 0, +1. Портрет живой: моргает и говорит в своём ритме.

const GRID := 24
const DIR := "res://assets/portraits/"

var id: StringName = &""
var scale_px := 5
var talking := true
var mood := 0:
	set(value):
		mood = clampi(value, -1, 1)
		queue_redraw()

var _texture: Texture2D
var _mouth_open := false
var _blink := false
var _mouth_timer := 0.0
var _blink_timer := 1.5
var _rng := RandomNumberGenerator.new()


func _init(id_: StringName = &"", scale_ := 5, mood_ := 0) -> void:
	id = id_
	scale_px = scale_
	mood = mood_
	custom_minimum_size = Vector2(GRID, GRID) * scale_px
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_rng.randomize()
	if has(id):
		_texture = load(DIR + id + ".png")


## Есть ли портрет у персонажа с таким id.
static func has(id_: StringName) -> bool:
	return id_ != &"" and ResourceLoader.exists(DIR + id_ + ".png")


func _process(delta: float) -> void:
	_mouth_timer -= delta
	if _mouth_timer <= 0.0:
		_mouth_open = talking and not _mouth_open
		_mouth_timer = _rng.randf_range(0.08, 0.22) if talking else 0.5
		queue_redraw()
	_blink_timer -= delta
	if _blink_timer <= 0.0:
		_blink = not _blink
		_blink_timer = 0.12 if _blink else _rng.randf_range(1.5, 4.0)
		queue_redraw()


func _draw() -> void:
	if _texture == null:
		return
	var column := 2 if _mouth_open else (1 if _blink else 0)
	var src := Rect2(column * GRID, (mood + 1) * GRID, GRID, GRID)
	draw_texture_rect_region(_texture, Rect2(Vector2.ZERO, Vector2(GRID, GRID) * scale_px), src)
