class_name StudioLogoView
extends Control
## Логотип студии на экране (#61): мармеладная фигура цвета логотипа, символ поверх. Смена
## логотипа вздрагивает фигурой (`set_logo`). Размер задаёт хозяин (`custom_minimum_size`).

var logo: StudioLogo
var _shape: JellyShape
var _shape_kind := -1


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func set_logo(l: StudioLogo, animate := true) -> void:
	logo = l
	if _shape_kind != int(l.shape):
		_shape = null
	if animate and _shape != null and Jelly.on():
		_shape.poke(260.0)
	queue_redraw()


func _radius() -> float:
	return minf(size.x, size.y) / 2.0 * 0.92


func _make_shape() -> void:
	var r := _radius()
	match logo.shape:
		StudioLogo.Shape.CIRCLE:
			_shape = JellyShape.circle(r, 40)
		StudioLogo.Shape.SQUARE:
			_shape = JellyShape.rect(Vector2(r, r) * 1.7, r * 0.36, 48)
		StudioLogo.Shape.DIAMOND:
			_shape = JellyShape.polygon(4, r * 1.08, 48)
		_:
			_shape = JellyShape.polygon(6, r, 48)
	_shape_kind = int(logo.shape)
	if Jelly.on():
		_shape.snap(size / 2.0)
		_shape.poke(260.0)


func _process(delta: float) -> void:
	if logo == null or size.x <= 0.0:
		return
	if _shape == null:
		_make_shape()
	_shape.follow(delta, size / 2.0, 0.0, 1.0)
	queue_redraw()


func _draw() -> void:
	if logo == null or _shape == null:
		return
	if Jelly.on():
		_shape.draw(self, logo.color)
	else:
		draw_circle(size / 2.0, _radius(), logo.color)
	StudioLogo.draw_symbol(self, logo.symbol, size / 2.0, _radius(), logo.color)
