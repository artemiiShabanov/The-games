class_name JellyLift
extends Node2D
## Прототип мармелада (ветка proto/jelly): фокус толщиной вместо синей рамки. Элемент в фокусе
## приподнят: под ним проступает бортик его же цвета, темнее, и мягкая тень; в фокусе он едва
## дышит. Нажатие вдавливает его в бортик, отпускание выталкивает с пружиной. Рисуется позади
## хозяина (`show_behind_parent`), цвет берётся из его подложки каждый кадр, поэтому кнопка,
## меняющая цвет, получает бортик своего нового цвета. Хозяин ставит `focused`, зовёт `press`.

var focused := false
var radius := 24.0
var spring := JellySpring.new()
var _press_left := 0.0
var _phase := 0.0


## Подложить подъём под `host` (карточка, кнопка, пилюля: `Control` с подложкой `panel`).
static func add_to(host: Control, radius_ := 24.0) -> JellyLift:
	var l := JellyLift.new()
	l.radius = radius_
	l.show_behind_parent = true
	l.use_parent_material = true
	l._phase = randf() * TAU
	host.add_child(l)
	return l


func press() -> void:
	_press_left = 0.12


func _process(delta: float) -> void:
	var tu := Jelly.tuning()
	var target := 0.0
	if Jelly.on() and Jelly.focus_lift() and focused:
		var t := Time.get_ticks_msec() / 1000.0
		target = tu.lift_px + sin(t * 2.2 + _phase) * tu.lift_breathe
		if _press_left > 0.0:
			target = tu.lift_press
	_press_left -= delta
	var before := spring.value
	spring.step(delta, tu.ui_stiffness * 1.6, tu.ui_damping * 1.1, target)
	visible = spring.value > 0.15
	if visible and absf(spring.value - before) > 0.001:
		queue_redraw()


func _draw() -> void:
	var host := get_parent() as Control
	if host == null:
		return
	var tu := Jelly.tuning()
	var k := spring.value
	var face := host.get_theme_stylebox("panel") as StyleBoxFlat
	var base := face.bg_color if face != null else Style.SURFACE_2
	var sb := StyleBoxFlat.new()
	# У тёмной подложки (кнопка в фокусе) темнее некуда: бортик светлее, иначе его не видно.
	var lip := base.darkened(tu.lift_darken) if base.get_luminance() > 0.2 else base.lightened(tu.lift_darken * 1.4)
	sb.bg_color = Color(lip, 1.0)
	sb.set_corner_radius_all(int(minf(radius, minf(host.size.x, host.size.y) / 2.0)))
	var share := clampf(k / maxf(tu.lift_px, 1.0), 0.0, 1.5)
	sb.shadow_color = Color(0, 0, 0, 0.12 * share)
	sb.shadow_size = int(4.0 + 10.0 * share)
	sb.shadow_offset = Vector2(0, 2.0 + 3.0 * share)
	draw_style_box(sb, Rect2(Vector2(0.0, k), host.size))
