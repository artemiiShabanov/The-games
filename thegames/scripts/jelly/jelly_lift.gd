class_name JellyLift
extends Node2D
## Прототип мармелада (ветка proto/jelly): толщина вместо тени и вместо синей рамки фокуса.
## Под хозяином проступает бортик его же цвета, темнее (у белых тёплый серый, у тёмных светлее):
## `resting` постоянная толщина (карточка экрана, смета), плюс подъём в фокусе (`focused`) или
## под курсором (`hover_lift`). В фокусе элемент едва дышит; нажатие (`press`) вдавливает его в
## бортик. Рисуется сдвинутой формой целиком за хозяином: подложка хозяина должна быть
## плотной (затемнённые карточки накрываются вуалью, а не прозрачностью). Обычно ребёнок хозяина позади него; у хозяина,
## который режет содержимое (`clip_contents`), сосед перед ним (`add_under`).

var focused := false
var hover_lift := false
var resting := 0.0
var radius := 24.0
var spring := JellySpring.new()
var host: Control
var _sibling := false
var _press_left := 0.0
var _phase := 0.0
var _drawn := -1.0


## Под `host` ребёнком позади него.
static func add_to(host_: Control, radius_ := 24.0, resting_ := 0.0) -> JellyLift:
	var l := _make(host_, radius_, resting_)
	l.show_behind_parent = true
	l.use_parent_material = true
	host_.add_child(l)
	return l


## Под `host` соседом перед ним в том же родителе: для хозяев с `clip_contents`.
static func add_under(host_: Control, radius_ := 24.0, resting_ := 0.0) -> JellyLift:
	var l := _make(host_, radius_, resting_)
	l._sibling = true
	var parent := host_.get_parent()
	parent.add_child(l)
	parent.move_child(l, host_.get_index())
	return l


static func _make(host_: Control, radius_: float, resting_: float) -> JellyLift:
	var l := JellyLift.new()
	l.host = host_
	l.radius = radius_
	l.resting = resting_
	l.spring.value = resting_
	l._phase = randf() * TAU
	Jelly.ui().set_lift(host_, l)
	return l


func press() -> void:
	_press_left = 0.12


func _process(delta: float) -> void:
	if host == null or not is_instance_valid(host):
		queue_free()
		return
	var tu := Jelly.tuning()
	var on := Jelly.on()
	var raised := focused if not hover_lift else Jelly.ui().is_hovered(host)
	var target := resting if on else 0.0
	if on and Jelly.focus_lift() and raised:
		target = resting + tu.lift_px + (sin(Time.get_ticks_msec() / 1000.0 * 2.2 + _phase) * tu.lift_breathe if focused else 0.0)
	if on and _press_left > 0.0:
		target = minf(target, tu.lift_press)
	_press_left -= delta
	var k := tu.ui_stiffness * 1.6
	# Вверх с лёгким перелётом, вниз без него: иначе бортик мигает, проходя через ноль.
	var damping := tu.ui_damping * 1.1 if target > spring.value else 2.0 * sqrt(k)
	spring.step(delta, k, damping, target)
	if target <= 0.0 and spring.value < 0.2:
		spring.value = 0.0
		spring.velocity = 0.0
	var show := spring.value > 0.2 and host.is_visible_in_tree()
	visible = show
	if _sibling and show:
		position = host.position
	if show and absf(spring.value - _drawn) > 0.01:
		queue_redraw()


func _draw() -> void:
	var k := spring.value
	_drawn = k
	var size := host.size
	var face := host.get_theme_stylebox("panel") as StyleBoxFlat
	var base := face.bg_color if face != null else Style.SURFACE_2
	var tu := Jelly.tuning()
	var lip: Color
	if base.get_luminance() > 0.9:
		lip = Style.SURFACE_2.darkened(0.08)
	elif base.get_luminance() > 0.2:
		lip = base.darkened(tu.lift_darken)
	else:
		lip = base.lightened(tu.lift_darken * 1.4)
	lip.a = 1.0
	# Затемнённая (закрытая) карточка накрыта белой вуалью: бортик смешан с белым так же.
	lip = lip.lerp(Style.SURFACE_SOLID, float(host.get_meta(&"jelly_veil", 0.0)))
	var r := minf(radius, minf(size.x, size.y) / 2.0)
	# Та же форма, сдвинутая вниз и чуть уже: целиком за плотной карточкой, видна только
	# нижняя полоса. Без вычитаний: стыка, через который просвечивает фон, нет.
	# Сужение пропорционально высоте: у вдавленного бортика иначе открывается щель в углу.
	var inset := minf(3.0, k * 0.3)
	var sb := StyleBoxFlat.new()
	sb.bg_color = lip
	sb.set_corner_radius_all(int(r))
	sb.anti_aliasing = true
	draw_style_box(sb, Rect2(Vector2(inset, k), Vector2(size.x - 2.0 * inset, size.y)))
