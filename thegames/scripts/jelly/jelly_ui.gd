class_name JellyUi
extends CanvasLayer
## Прототип мармелада для интерфейса (ветка proto/jelly). Один слой поверх кадра: элементы
## регистрируются `Jelly.attach(control)`, слой каждый кадр считает их пружины и одним шейдером
## искажает уже отрисованный кадр в их областях. Поэтому деформируются целиком подложка, текст,
## рамка и тень, а сами `Control` и их раскладка не меняются. Элемент сам реагирует на своё
## движение (отстаёт и гнётся при рывке, качается после остановки), на рост (перелёт масштаба),
## на курсор (линза и наклон к нему), на нажатие мышью (сжатие) и на `Jelly.poke` (вздрог при
## фокусе). Покоящиеся элементы в шейдер не идут; когда двигаться нечему, слой выключен и кадр
## не пересэмплируется.

const LAYER := 90
const MAX_BODIES := 24
const SHADER := """
shader_type canvas_item;
render_mode unshaded;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
uniform vec2 canvas_size = vec2(1920.0, 1080.0);
uniform int count = 0;
uniform vec4 bodies[96];

float rr_sdf(vec2 u, vec2 h, float r) {
	vec2 q = abs(u) - h + vec2(r);
	return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
}

// Обратное отображение тела: из точки кадра в точку, откуда брать цвет.
vec2 warp(vec2 src, vec4 A, vec4 B, vec4 C, vec4 D) {
	vec2 h = A.zw;
	vec2 u = src - A.xy;
	float bl = length(C.xy);
	if (bl > 0.01) {
		vec2 perp = vec2(-C.y, C.x) / bl;
		float ext = abs(perp.x) * h.x + abs(perp.y) * h.y;
		float t = clamp(dot(u, perp) / max(ext, 1.0), -1.0, 1.0);
		u -= C.xy * (1.0 - t * t);
	}
	u = mat2(vec2(B.x, B.z), vec2(B.y, B.w)) * u;
	if (C.w > 0.0001) {
		vec2 v = u - D.xy;
		float sig = 0.7 * min(h.x, h.y);
		u = D.xy + v * (1.0 - C.w * exp(-dot(v, v) / (sig * sig)));
	}
	return A.xy + u;
}

void fragment() {
	vec2 p = UV * canvas_size;
	vec2 src = p;
	for (int i = 0; i < count; i++) {
		vec4 A = bodies[i * 4];
		vec4 B = bodies[i * 4 + 1];
		vec4 C = bodies[i * 4 + 2];
		vec4 D = bodies[i * 4 + 3];
		float m = abs(D.w);
		vec2 du = abs(src - A.xy) - A.zw;
		if (max(du.x, du.y) > m * 2.0 + 24.0) {
			continue;
		}
		// Вес только по самой точке кадра: искажение не выходит за поле элемента на соседей.
		float d0 = rr_sdf(src - A.xy, A.zw, C.z);
		float w = 1.0 - smoothstep(m * 0.35, m, d0);
		if (w > 0.0) {
			src = mix(src, warp(src, A, B, C, D), w);
		}
	}
	vec2 duv = vec2(dFdx(SCREEN_UV.x) / dFdx(UV.x), dFdy(SCREEN_UV.y) / dFdy(UV.y));
	COLOR = texture(screen_tex, SCREEN_UV + (src - p) / canvas_size * duv);
}
"""


class Body:
	var ref: WeakRef
	var radius := 16.0
	var margin := 24.0
	var ring := false
	## Насколько видимый контур выходит за прямоугольник (рамка фокуса рисуется снаружи).
	var expand := 0.0
	## Реагирует ли на курсор линзой: большим контейнерам нельзя, линза на полэкрана кривит всё.
	var hover := true
	var depth := 0
	var clip: WeakRef
	var ready := false
	var center := Vector2.ZERO
	var half := Vector2.ZERO
	var vel := Vector2.ZERO
	var scale := 0.0
	var scale_rate := 0.0
	## Отставание (пиксели), его скорость; пульс масштаба общий и разнонаправленный по осям.
	var lag := Vector2.ZERO
	var lag_v := Vector2.ZERO
	var r := 0.0
	var r_v := 0.0
	var q := 0.0
	var q_v := 0.0
	var lens := 0.0
	var lens_v := 0.0
	var lens_at := Vector2.ZERO
	## Наклон к курсору: цель отставания; изгибает только движение сверх него.
	var lean := Vector2.ZERO

	func control() -> Control:
		return ref.get_ref() as Control

	func energy() -> float:
		return lag.length() + lag_v.length() * 0.05 + (absf(r) + absf(q)) * 200.0 + (absf(r_v) + absf(q_v)) * 10.0 + lens * 200.0


var bodies: Array[Body] = []
var _rect: ColorRect
var _material: ShaderMaterial
var _pressed: Body


func _init() -> void:
	layer = LAYER
	name = "JellyUi"
	_rect = ColorRect.new()
	_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var shader := Shader.new()
	shader.code = SHADER
	_material = ShaderMaterial.new()
	_material.shader = shader
	_rect.material = _material
	_rect.visible = false
	add_child(_rect)


func attach(c: Control, radius: float, margin: float, ring: bool, expand := 0.0, hover := true) -> void:
	for b in bodies:
		if b.control() == c:
			return
	var b := Body.new()
	b.ref = weakref(c)
	b.radius = radius
	b.margin = margin
	b.ring = ring
	b.expand = expand
	b.hover = hover
	bodies.append(b)


func poke(c: Control, strength: float) -> void:
	var b := _find(c)
	if b == null:
		return
	var tu := Jelly.tuning()
	b.r_v += tu.ui_poke * strength
	b.q_v += tu.ui_poke * strength * 1.4


func _find(c: Control) -> Body:
	for b in bodies:
		if b.control() == c:
			return b
	return null


## Нажатие мышью сжимает верхний элемент под курсором, отпускание отпускает его с перелётом.
func _input(event: InputEvent) -> void:
	var mb := event as InputEventMouseButton
	if mb == null or mb.button_index != MOUSE_BUTTON_LEFT or not Jelly.on():
		return
	var tu := Jelly.tuning()
	if mb.pressed:
		_pressed = _top_at(mb.position)
		if _pressed != null:
			_pressed.r_v -= tu.ui_press
			_pressed.q_v += tu.ui_press * 0.5
	elif _pressed != null:
		_pressed.r_v += tu.ui_press * 0.6
		_pressed = null


func _top_at(pos: Vector2) -> Body:
	var best: Body = null
	for b in bodies:
		var c := b.control()
		if c == null or not c.is_visible_in_tree() or b.ring or not b.hover:
			continue
		if Rect2(b.center - b.half, b.half * 2.0).has_point(pos) and (best == null or b.depth >= best.depth):
			best = b
	return best


func _process(delta: float) -> void:
	if delta <= 0.0:
		return
	var alive: Array[Body] = []
	for b in bodies:
		if b.control() != null:
			alive.append(b)
	bodies = alive
	if not Jelly.on():
		_rect.visible = false
		return
	var tu := Jelly.tuning()
	var mouse := get_viewport().get_mouse_position()
	var active: Array[Body] = []
	for b in bodies:
		var c := b.control()
		if not c.is_visible_in_tree():
			b.ready = false
			continue
		_track(b, c, delta, tu, mouse)
		if b.energy() > 0.15 and _inside_clip(b):
			active.append(b)
	active.sort_custom(func(a: Body, b: Body) -> bool: return a.depth < b.depth)
	if active.size() > MAX_BODIES:
		active.resize(MAX_BODIES)
	_upload(active, tu)


func _track(b: Body, c: Control, delta: float, tu: JellyTuning, mouse: Vector2) -> void:
	var xf := c.get_global_transform_with_canvas()
	var rect := xf * Rect2(Vector2.ZERO, c.size)
	var center := rect.get_center()
	var half := rect.size / 2.0 + Vector2.ONE * b.expand
	var scale := maxf(half.length(), 1.0)
	if not b.ready or center.distance_to(b.center) > 600.0:
		b.ready = true
		b.center = center
		b.half = half
		b.scale = scale
		b.vel = Vector2.ZERO
		b.scale_rate = 0.0
		b.depth = _depth(c)
		var clip := _clip_of(c)
		b.clip = weakref(clip) if clip != null else null
		return
	var vel := (center - b.center) / delta
	var rate := (scale - b.scale) / delta / scale
	# Рывок отдаётся телу долей скорости: элемент отстаёт и потом догоняет с качанием.
	b.lag_v -= (vel - b.vel) * tu.ui_inertia
	b.r_v -= (rate - b.scale_rate) * tu.ui_scale_inertia
	b.q_v -= (rate - b.scale_rate) * tu.ui_scale_inertia * 0.6
	b.vel = vel
	b.scale_rate = rate
	b.center = center
	b.half = half
	b.scale = scale
	var hovered := b.hover and not b.ring and Rect2(center - half, half * 2.0).has_point(mouse) and _top_at(mouse) == b
	var lean := Vector2.ZERO
	if hovered:
		lean = (mouse - center) * tu.ui_lean
		b.lens_at = (mouse - center).clamp(-half, half)
	var subs := 2
	var dt := delta / subs
	for i in subs:
		b.lean = lean
		b.lag_v += ((lean - b.lag) * tu.ui_stiffness - b.lag_v * tu.ui_damping) * dt
		b.lag += b.lag_v * dt
		b.r_v += (-b.r * tu.ui_stiffness - b.r_v * tu.ui_damping) * dt
		b.r += b.r_v * dt
		b.q_v += (-b.q * tu.ui_stiffness * 1.3 - b.q_v * tu.ui_damping) * dt
		b.q += b.q_v * dt
		b.lens_v += (((tu.ui_hover_lens if hovered else 0.0) - b.lens) * 200.0 - b.lens_v * 26.0) * dt
		b.lens += b.lens_v * dt
	var cap := 0.2 * minf(half.x, half.y)
	if b.lag.length() > cap:
		b.lag = b.lag.normalized() * cap
	b.r = clampf(b.r, -0.15, 0.15)
	b.q = clampf(b.q, -0.15, 0.15)
	b.lens = maxf(b.lens, 0.0)


func _upload(active: Array[Body], tu: JellyTuning) -> void:
	_rect.visible = not active.is_empty()
	if active.is_empty():
		return
	var data := PackedVector4Array()
	data.resize(MAX_BODIES * 4)
	for i in active.size():
		var b := active[i]
		var forward := Transform2D(Vector2(1.0 + b.q + b.r, 0.0), Vector2(0.0, 1.0 - b.q + b.r), Vector2.ZERO)
		# Вытягивание только по осям, каждое со сжатием поперёк: по диагонали прямоугольник
		# выглядел бы перекошенным, а не мармеладным.
		var ex := absf(b.lag.x) / maxf(b.half.x, 1.0) * tu.ui_stretch
		var ey := absf(b.lag.y) / maxf(b.half.y, 1.0) * tu.ui_stretch
		var sx := (1.0 + ex) / sqrt(1.0 + ey)
		var sy := (1.0 + ey) / sqrt(1.0 + ex)
		forward = Transform2D(Vector2(sx, 0.0), Vector2(0.0, sy), Vector2.ZERO) * forward
		var inv := forward.affine_inverse()
		# Изгиб по главной оси движения.
		var dyn := b.lag - b.lean
		var bend := Vector2(dyn.x, 0.0) if absf(dyn.x) > absf(dyn.y) else Vector2(0.0, dyn.y)
		bend *= tu.ui_bend
		data[i * 4] = Vector4(b.center.x, b.center.y, b.half.x, b.half.y)
		data[i * 4 + 1] = Vector4(inv.x.x, inv.y.x, inv.x.y, inv.y.y)
		data[i * 4 + 2] = Vector4(bend.x, bend.y, minf(b.radius + b.expand, minf(b.half.x, b.half.y)), b.lens)
		data[i * 4 + 3] = Vector4(b.lens_at.x, b.lens_at.y, 1.0 if b.ring else 0.0, b.margin)
	_material.set_shader_parameter("bodies", data)
	_material.set_shader_parameter("count", active.size())
	_material.set_shader_parameter("canvas_size", get_viewport().get_visible_rect().size)


func _inside_clip(b: Body) -> bool:
	var clip := b.clip.get_ref() as Control if b.clip != null else null
	return clip == null or clip.get_global_rect().has_point(b.center)


static func _depth(c: Node) -> int:
	var d := 0
	var n := c.get_parent()
	while n != null:
		d += 1
		n = n.get_parent()
	return d


static func _clip_of(c: Control) -> Control:
	var n := c.get_parent()
	while n != null:
		if n is Control and (n as Control).clip_contents:
			return n as Control
		n = n.get_parent()
	return null
