class_name EdgeFade
extends Node
## Растворение краёв прокручиваемого списка (плейтест 2026-11-11: лента отзывов и галерея как
## карусель конструктора, без обрезанных карточек). Содержимое `ScrollContainer` рисуется одним
## материалом: у верхнего края списка карточки уходят в прозрачность на `fade_px`, если выше
## что-то есть, у нижнего так же, если есть что-то ниже. В начале и в конце списка край не
## растворяется. Потомки берут материал родителя (`refresh` после перестройки списка); узлы со
## своим материалом не трогаются.

const SHADER := """
shader_type canvas_item;
uniform float top_px = 0.0;
uniform float bottom_px = 1000.0;
uniform float top_fade = 0.0;
uniform float bottom_fade = 0.0;
varying vec2 world_pos;
void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
}
void fragment() {
	float a = top_fade > 0.5 ? smoothstep(0.0, top_fade, world_pos.y - top_px) : 1.0;
	a *= bottom_fade > 0.5 ? smoothstep(0.0, bottom_fade, bottom_px - world_pos.y) : 1.0;
	COLOR.a *= a;
}
"""

var scroll: ScrollContainer
var fade_px := 120.0
var _material: ShaderMaterial


## Растворение краёв `scroll_`; содержимое уже должно быть внутри.
static func attach(scroll_: ScrollContainer, fade := 120.0) -> EdgeFade:
	var f := EdgeFade.new()
	f.scroll = scroll_
	f.fade_px = fade
	var shader := Shader.new()
	shader.code = SHADER
	f._material = ShaderMaterial.new()
	f._material.shader = shader
	# Сосед, а не ребёнок: у `ScrollContainer` должен быть один ребёнок, содержимое.
	scroll_.get_parent().add_child(f)
	f.refresh()
	return f


## Материал на содержимое и его потомков: после перестройки списка.
func refresh() -> void:
	for child in scroll.get_children():
		if child is CanvasItem:
			(child as CanvasItem).material = _material
			_inherit(child)
	_update()


func _inherit(node: Node) -> void:
	for child in node.get_children():
		if child is CanvasItem:
			var ci := child as CanvasItem
			if ci.material == null:
				ci.use_parent_material = true
			_inherit(child)


func _process(_delta: float) -> void:
	_update()


func _update() -> void:
	if scroll == null or _material == null:
		return
	var r := scroll.get_global_rect()
	var bar := scroll.get_v_scroll_bar()
	var max_scroll := maxf(bar.max_value - bar.page, 0.0)
	var at := float(scroll.scroll_vertical)
	_material.set_shader_parameter("top_px", r.position.y)
	_material.set_shader_parameter("bottom_px", r.end.y)
	_material.set_shader_parameter("top_fade", clampf(at, 0.0, fade_px))
	_material.set_shader_parameter("bottom_fade", clampf(max_scroll - at, 0.0, fade_px))
