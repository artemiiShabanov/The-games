class_name RunnerJelly
extends RefCounted
## Прототип желе для «Прыгай» (ветка proto/jelly). Геймплей и хитбоксы остаются в раннере, здесь
## только вид: точка мягким телом (`SoftBlob`), земля желейной поверхностью с волнами от
## приземлений и прогибом под телом (`JellySurface`), столбики и флажок качаются на пружинах,
## брызги, кляксы и след слизи (`SplashFx`). Раннер шлёт события (прыжок, приземление, падение,
## возрождение, финиш) и каждый кадр центр точки в координатах мира: X по дорожке, Y экранный.

const PILLAR_R := 8.0
const PIT_EDGE := 24.0

var dot_r := 28.0
var pillar_h := 100.0
var ground_y := 800.0
var finish_x := 0.0
## Ямы (начало, конец) и столбики (x, ширина) по дорожке.
var pits: Array[Vector2] = []
var pillars: Array[Vector2] = []
var color := Color.WHITE

var blob: SoftBlob
var fx := SplashFx.new()
var surface := JellySurface.new()
var pillar_shear: Array[JellySpring] = []
var pillar_squash: Array[JellySpring] = []
var pillar_brushed: Array[bool] = []
var flag := JellySpring.new()
var pops: Array[JellySpring] = []
var grounded := true
var falling := false


func setup(pits_: Array[Vector2], pillars_: Array[Vector2], finish_x_: float, dot_r_: float, pillar_h_: float, fail_marks: int, seed_: int) -> void:
	pits = pits_
	pillars = pillars_
	finish_x = finish_x_
	dot_r = dot_r_
	pillar_h = pillar_h_
	color = Style.accent(0)
	blob = SoftBlob.new(dot_r)
	fx.rng.seed = seed_
	for p in pillars:
		pillar_shear.append(JellySpring.new())
		pillar_squash.append(JellySpring.new())
		pillar_brushed.append(false)
	for i in fail_marks:
		pops.append(JellySpring.new())


## Высота поверхности под X в мире, INF над ямой.
func ground(x: float) -> float:
	for p in pits:
		if x > p.x and x < p.y:
			return INF
	return ground_y + surface.height(x)


func pillar_rect(i: int) -> Rect2:
	var p := pillars[i]
	return Rect2(p.x, ground_y - pillar_h, p.y, pillar_h)


# --- События --------------------------------------------------------------------------------

func jump(x: float) -> void:
	grounded = false
	fx.break_trail()
	# Тело отрывается от слизи: пара капель остаётся сзади.
	fx.burst(Vector2(x - dot_r * 0.4, ground_y - 2.0), 4, 260.0, -PI * 0.7, 0.35, color, 2.0, 4.0)


## Приземление со скоростью `speed` вниз: шлепок, кляксы по бокам, волна по земле.
func land(x: float, speed: float) -> void:
	grounded = true
	var k := clampf(speed / 1000.0, 0.3, 1.6)
	surface.impact(x, speed)
	var count := int(3 + 6 * k)
	fx.burst(Vector2(x - dot_r * 0.8, ground_y - 4.0), count, 420.0 * k, -PI * 0.78, 0.3, color, 2.5, 6.0)
	fx.burst(Vector2(x + dot_r * 0.8, ground_y - 4.0), count, 420.0 * k, -PI * 0.22, 0.3, color, 2.5, 6.0)
	fx.blot(Vector2(x - dot_r * 1.1, ground_y), 6.0 * k, color)
	fx.blot(Vector2(x + dot_r * 1.1, ground_y), 5.0 * k, color)


## Падение в яму (`pit` с краями) или удар о столбик `pillar` (индекс или −1).
func fall(at: Vector2, pit: Vector2, pillar: int, fail_index: int) -> void:
	falling = true
	grounded = false
	fx.break_trail()
	if fail_index >= 0 and fail_index < pops.size():
		pops[fail_index].kick(300.0)
	if pillar >= 0:
		var r := pillar_rect(pillar)
		blob.walls = [r]
		fx.walls = [r]
		blob.impulse(Vector2(-900.0, 0.0), Vector2.RIGHT)
		pillar_shear[pillar].kick(520.0)
		pillar_squash[pillar].kick(1.2)
		fx.burst(Vector2(r.position.x - 4.0, at.y), 14, 720.0, PI + 0.25, 0.8, color, 2.5, 7.0)
		for i in 3:
			fx.blot(Vector2(r.position.x, at.y + fx.rng.randf_range(-dot_r * 0.8, dot_r * 0.4)), fx.rng.randf_range(3.0, 6.0), color, true)
		surface.impact(r.position.x, 600.0)
	else:
		# Тело срывается с края ямы: края вздрагивают, с них летят капли.
		surface.impact(pit.x, 700.0)
		surface.impact(pit.y, 700.0)
		fx.burst(Vector2(pit.x, ground_y - 3.0), 5, 360.0, -PI * 0.65, 0.3, color, 2.0, 5.0)
		fx.burst(Vector2(pit.y, ground_y - 3.0), 4, 300.0, -PI * 0.35, 0.3, color, 2.0, 4.0)


func respawn(at: Vector2) -> void:
	falling = false
	grounded = true
	blob.walls = []
	fx.walls = []
	blob.reset(at, 0.4)
	surface.impact(at.x, 500.0)


func finish() -> void:
	flag.kick(380.0)


# --- Кадр -----------------------------------------------------------------------------------

func step(delta: float, center: Vector2) -> void:
	var tu := Jelly.tuning()
	surface.dent_x = center.x
	surface.dent_w = dot_r * 1.2
	surface.dent_depth = tu.dent * clampf(blob.contact * 3.0, 0.0, 1.0) if blob.points.size() > 0 else 0.0
	surface.step(delta)
	blob.collide = not (falling and blob.walls.is_empty())
	blob.step(delta, center, ground)
	fx.step(delta, ground)
	if grounded and not falling and blob.contact > 0.0:
		var x := blob.contact_min + 4.0
		var gy := ground(x)
		if gy != INF:
			fx.add_trail(Vector2(x, gy - 5.0), tu.trail_width)
	elif not grounded:
		fx.break_trail()
	var bottom := center.y + dot_r
	for i in pillars.size():
		var base_x := pillars[i].x + pillars[i].y / 2.0
		# Столбик стоит на желе: наклоняется по склону волны и проседает в её ямке.
		pillar_shear[i].step(delta, tu.spring_stiffness, tu.spring_damping, -surface.slope(base_x) * 260.0)
		pillar_squash[i].step(delta, tu.spring_stiffness * 1.6, tu.spring_damping, surface.height(base_x) * 0.012)
		var r := pillar_rect(i)
		var over := center.x + dot_r > r.position.x and center.x - dot_r < r.end.x
		if over and not pillar_brushed[i] and bottom > r.position.y - 30.0 and bottom < r.position.y + 4.0:
			pillar_brushed[i] = true
			pillar_shear[i].kick(260.0)
			pillar_squash[i].kick(0.6)
		elif not over:
			pillar_brushed[i] = false
	flag.step(delta, tu.spring_stiffness * 0.6, tu.spring_damping * 0.5, -surface.slope(finish_x) * 200.0)
	for p in pops:
		p.step(delta, tu.spring_stiffness * 1.5, tu.spring_damping * 1.2)


# --- Рисование ------------------------------------------------------------------------------

## Вся дорожка от камеры `cam` (X мира у левого края) шириной `width`; `alpha` тела.
func draw(ci: CanvasItem, cam: float, width: float, alpha: float) -> void:
	var time := fx.time
	var off := Vector2(-cam, 0.0)
	var left := cam
	var right := cam + width
	_draw_ground(ci, cam, left, right)
	for i in pillars.size():
		var r := pillar_rect(i)
		if r.end.x < left - 40.0 or r.position.x > right + 40.0:
			continue
		_draw_pillar(ci, i, off)
	_draw_flag(ci, off, time)
	fx.draw_surface(ci, off, ground)
	if blob.points.size() > 0:
		fill(ci, blob.polygon(off), Color(color, color.a * alpha))
	fx.draw_air(ci, off)


func _draw_ground(ci: CanvasItem, cam: float, left: float, right: float) -> void:
	var segments: Array[Vector2] = []
	var cursor := left
	for p in pits:
		if p.y < left or p.x > right:
			continue
		segments.append(Vector2(cursor, p.x))
		cursor = p.y
	segments.append(Vector2(cursor, minf(right, finish_x + 400.0)))
	for s in segments:
		if s.y <= s.x:
			continue
		var line := PackedVector2Array()
		var x := s.x
		while x < s.y:
			line.append(Vector2(x - cam, ground_y + surface.height(x)))
			x += 10.0
		line.append(Vector2(s.y - cam, ground_y + surface.height(s.y)))
		if line.size() >= 2:
			ci.draw_polyline(line, Style.INK, 6.0, true)
	for p in pits:
		if p.y < left or p.x > right:
			continue
		for edge in [p.x, p.y]:
			var ex: float = edge
			ci.draw_line(Vector2(ex - cam, ground_y + surface.height(ex)), Vector2(ex - cam, ground_y + PIT_EDGE), Style.INK, 6.0, true)
		ci.draw_rect(Rect2(p.x - cam, ground_y + 3.0, p.y - p.x, 40.0), Color(Style.INK, 0.06))


## Столбик желе: низ стоит на поверхности, верх гуляет по сдвигу, при проседании раздаётся вширь.
func _draw_pillar(ci: CanvasItem, i: int, off: Vector2) -> void:
	var r := pillar_rect(i)
	var w := r.size.x
	var base := Vector2(r.position.x, ground_y + surface.height(r.position.x + w / 2.0)) + off
	var shear := pillar_shear[i].value
	var squash := clampf(pillar_squash[i].value, -0.4, 0.5)
	var poly := rounded_rect(Vector2(w, pillar_h), PILLAR_R, 6, 10)
	for j in poly.size():
		var p := poly[j]
		var t := clampf((pillar_h - p.y) / pillar_h, 0.0, 1.0)
		var y := -t * pillar_h * (1.0 - squash)
		var x := (p.x - w / 2.0) * (1.0 + squash * 0.7 * (1.0 - t * 0.4)) + w / 2.0 + shear * t * t
		poly[j] = base + Vector2(x, y)
	fill(ci, poly, Style.accent(1))


func _draw_flag(ci: CanvasItem, off: Vector2, time: float) -> void:
	var base := Vector2(finish_x, ground_y + surface.height(finish_x)) + off
	if base.x < -150.0 or base.x > 4000.0:
		return
	var pole := PackedVector2Array()
	for j in 9:
		var t := j / 8.0
		pole.append(base + Vector2(flag.value * t * t, -200.0 * t))
	ci.draw_polyline(pole, Style.accent(2), 6.0, true)
	var top := pole[pole.size() - 1]
	fill(ci, _flag_shape(top, time), Style.accent(2))


func _flag_shape(top: Vector2, time: float) -> PackedVector2Array:
	var out := PackedVector2Array()
	var n := 8
	for j in n + 1:
		var t := float(j) / n
		out.append(top + Vector2(70.0 * t, 25.0 * t + sin(time * 7.0 - t * 4.0) * 5.0 * t))
	for j in range(n, -1, -1):
		var t := float(j) / n
		out.append(top + Vector2(70.0 * t, 50.0 - 25.0 * t + sin(time * 7.0 - t * 4.0) * 5.0 * t))
	return out


# --- Общие помощники ------------------------------------------------------------------------

## Залить многоугольник; если контур сам себя пересёк, рисуется кругом по центру, без ошибки.
static func fill(ci: CanvasItem, poly: PackedVector2Array, col: Color) -> void:
	var idx := Geometry2D.triangulate_polygon(poly)
	if idx.is_empty():
		var c := Vector2.ZERO
		for p in poly:
			c += p
		c /= maxf(poly.size(), 1)
		ci.draw_circle(c, 10.0, col)
		return
	var colors := PackedColorArray()
	colors.resize(poly.size())
	colors.fill(col)
	RenderingServer.canvas_item_add_triangle_array(ci.get_canvas_item(), idx, poly, colors)


## Контур скруглённого прямоугольника от (0, 0) до `size` с частыми точками на сторонах, чтобы
## его можно было гнуть.
static func rounded_rect(size: Vector2, r: float, corner_steps: int, side_steps: int) -> PackedVector2Array:
	var out := PackedVector2Array()
	var corners := [Vector2(size.x - r, r), Vector2(size.x - r, size.y - r), Vector2(r, size.y - r), Vector2(r, r)]
	var starts := [-PI / 2.0, 0.0, PI / 2.0, PI]
	for c in 4:
		var cc: Vector2 = corners[c]
		var a0: float = starts[c]
		for j in corner_steps + 1:
			out.append(cc + Vector2(cos(a0 + PI / 2.0 * j / corner_steps), sin(a0 + PI / 2.0 * j / corner_steps)) * r)
		var nc: Vector2 = corners[(c + 1) % 4]
		var nstart: float = starts[(c + 1) % 4]
		var from := cc + Vector2(cos(a0 + PI / 2.0), sin(a0 + PI / 2.0)) * r
		var to := nc + Vector2(cos(nstart), sin(nstart)) * r
		for j in range(1, side_steps):
			out.append(from.lerp(to, float(j) / side_steps))
	return out
