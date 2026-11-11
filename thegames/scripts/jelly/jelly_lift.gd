class_name JellyLift
extends Node2D
## Мармелад (STYLE «Мармелад»): толщина вместо тени и вместо синей рамки фокуса.
## Под хозяином проступает бортик его же цвета, темнее (у белых тёплый серый, у тёмных светлее):
## `resting` постоянная толщина (карточка экрана, смета), плюс подъём в фокусе (`focused`) или
## под курсором (`hover_lift`). В фокусе элемент едва дышит; нажатие (`press`) вдавливает его в
## бортик. Рисуется сдвинутой формой целиком за хозяином: подложка хозяина должна быть
## плотной (затемнённые карточки накрываются вуалью, а не прозрачностью). Обычно ребёнок хозяина позади него; у хозяина,
## который режет содержимое (`clip_contents`), сосед перед ним (`add_under`).

var focused := false
var hover_lift := false
## Бледный нейтральный бортик: фокус на неинтерактивном (пост ленты), не обещает нажатия.
var neutral := false
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
	var moving := Jelly.on()
	var raised := focused if not hover_lift else Jelly.ui().is_hovered(host)
	var target := resting
	if raised:
		target = resting + tu.lift_px
		if focused and moving:
			target += sin(Time.get_ticks_msec() / 1000.0 * 2.2 + _phase) * tu.lift_breathe
	if _press_left > 0.0:
		target = minf(target, tu.lift_press)
	_press_left -= delta
	if moving:
		var k := tu.ui_stiffness * 1.6
		# Вверх с лёгким перелётом, вниз без него: иначе бортик мигает, проходя через ноль.
		var damping := tu.ui_damping * 1.1 if target > spring.value else 2.0 * sqrt(k)
		spring.step(delta, k, damping, target)
	else:
		spring.value = target
		spring.velocity = 0.0
	if target <= 0.0 and spring.value < 0.2:
		spring.value = 0.0
		spring.velocity = 0.0
	var show := spring.value > 0.2 and host.is_visible_in_tree()
	visible = show
	if _sibling and show:
		# Сосед не наследует от хозяина ни места, ни проявления.
		position = host.position
		modulate = host.modulate
	if show and absf(spring.value - _drawn) > 0.01:
		queue_redraw()


func _draw() -> void:
	var k := spring.value
	_drawn = k
	var size := host.size
	var face := host.get_theme_stylebox("panel") as StyleBoxFlat
	var base := face.bg_color if face != null else Style.SURFACE_2
	var tu := Jelly.tuning()
	# Белая подложка: тёплый серый; светлая (surface-2): чуть темнее себя; цветная: заметно
	# темнее; тёмная (кнопка в фокусе): светлее, темнее некуда.
	var lum := base.get_luminance()
	var lip: Color
	if neutral:
		lip = Style.SURFACE_2.darkened(0.1)
	elif lum > 0.95:
		lip = Style.SURFACE_2.darkened(0.08)
	elif lum > 0.75:
		lip = base.darkened(tu.lift_darken * 0.6)
	elif lum > 0.2:
		lip = base.darkened(tu.lift_darken)
	else:
		lip = base.lightened(tu.lift_darken * 1.4)
	lip.a = 1.0
	# Затемнённая (закрытая) карточка накрыта белой вуалью: бортик смешан с белым так же.
	lip = lip.lerp(Style.SURFACE_SOLID, float(host.get_meta(&"jelly_veil", 0.0)))
	var r := minf(radius, minf(size.x, size.y) / 2.0)
	# Серп: та же форма, сдвинутая вниз, минус карточка, поднятая на 2 пикселя. Под карточку
	# он заходит только на эти 2 пикселя: стыка нет, и сквозь растворяющуюся у края карусели
	# карточку ему просвечивать нечем. Бока прямые вровень с карточкой (плейтест 2026-11-11:
	# у поджатого серпа на боку была ступенька, где скругление карточки встречает его бок),
	# поджат только на полпикселя сглаженного края, чтобы не выпирать за карточку.
	var inset := minf(0.5, k * 0.1)
	var squeeze := 1.0 - 2.0 * inset / maxf(size.x, 1.0)
	var cx := size.x / 2.0
	var shape := RunnerJelly.rounded_rect(size, r, 10, 2)
	var shifted := PackedVector2Array()
	for p in shape:
		shifted.append(Vector2(cx + (p.x - cx) * squeeze, p.y + k))
	# Вычитается карточка, поднятая на 2 пикселя (а не поджатая со всех сторон): так серп
	# всегда только снизу. Поджатая форма при низком бортике целиком влезала в сдвинутую,
	# вычитание давало кольцо, и за карточкой рисовалась вся форма.
	var cut := PackedVector2Array()
	for p in shape:
		cut.append(p - Vector2(0.0, 2.0))
	for part in Geometry2D.clip_polygons(shifted, cut):
		if Geometry2D.is_polygon_clockwise(part) or part.size() < 3:
			continue
		var tris := Geometry2D.triangulate_polygon(part)
		if tris.is_empty():
			continue
		var colors := PackedColorArray()
		colors.resize(part.size())
		colors.fill(lip)
		RenderingServer.canvas_item_add_triangle_array(get_canvas_item(), tris, part, colors)
	# Сглаженный край по видимому контуру: точки сдвинутой формы снаружи карточки.
	var edge := PackedVector2Array()
	for p in shifted:
		if not Geometry2D.is_point_in_polygon(p, shape):
			edge.append(p)
		elif edge.size() > 1:
			break
	if edge.size() > 1:
		draw_polyline(edge, lip, 1.0, true)
