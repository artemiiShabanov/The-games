class_name SoftBlob
extends RefCounted
## Мягкое тело: кольцо точек на пружинах вокруг центра, который ведёт хозяин (игровая точка
## остаётся главной, тело только рисуется). Точки тянутся к своему месту в форме, форма
## вытягивается по вертикальной скорости центра, давление держит площадь, соседи сглаживают
## контур. Снизу точки держит поверхность: `ground(x)` даёт её высоту или INF над пустотой;
## `walls` твёрдые прямоугольники (столбик при ударе). Координаты мира хозяина.

const SUBSTEP := 1.0 / 240.0

var radius := 28.0
var points := PackedVector2Array()
var velocities := PackedVector2Array()
var center := Vector2.ZERO
var center_velocity := Vector2.ZERO
var collide := true
var walls: Array[Rect2] = []
## Доля точек на поверхности и их разброс по X: под след.
var contact := 0.0
var contact_min := 0.0
var contact_max := 0.0
## Масштаб и поворот формы: хозяин ведёт их, как центр (фигура растёт, покачивается).
var shape_scale := 1.0
var angle := 0.0
## Вытягивание по направлению скорости центра, а не только по вертикали (фигура летит вбок).
var stretch_free := false

## Своя форма покоя (многоугольник) вместо круга; задаётся до `reset`.
var _shape := PackedVector2Array()

var _rest := PackedVector2Array()
var _area0 := 0.0
var _time := 0.0
var _ready := false


func _init(radius_ := 28.0) -> void:
	radius = radius_


## Поставить тело в точку; `scale` меньше единицы: тело надувается из капли.
func reset(at: Vector2, scale := 1.0) -> void:
	var n := _shape.size() if not _shape.is_empty() else maxi(Jelly.tuning().blob_points, 8)
	_rest.resize(n)
	points.resize(n)
	velocities.resize(n)
	for i in n:
		var a := TAU * i / n
		_rest[i] = _shape[i] if not _shape.is_empty() else Vector2(cos(a), sin(a)) * radius
		points[i] = at + _rest[i].rotated(angle) * scale * shape_scale
		velocities[i] = Vector2.ZERO
	_area0 = _area_of(_rest)
	center = at
	center_velocity = Vector2.ZERO
	_ready = true


## Форма покоя: точки по кругу против часовой (в математических осях), центр в нуле.
func set_shape(shape: PackedVector2Array) -> void:
	_shape = shape


## Правильный многоугольник `sides` радиуса `r` в `n` точках по углу, вершина вверх, острия
## чуть притуплены: мармеладка, а не стекло.
static func polygon_shape(sides: int, r: float, n: int, blunt := 0.94) -> PackedVector2Array:
	var out := PackedVector2Array()
	var seg := TAU / sides
	for i in n:
		var a := -PI / 2.0 + TAU * i / n
		var local := fposmod(a + PI / 2.0, seg) - seg / 2.0
		var rr := minf(r * cos(PI / sides) / cos(local), r * blunt)
		out.append(Vector2(cos(a), sin(a)) * rr)
	return out


## Толчок всем точкам от центра (`strength` > 0 раздувает, < 0 сжимает): вздрог.
func pulse(strength: float) -> void:
	for i in points.size():
		velocities[i] += _rest[i].normalized() * strength


## Толкнуть точки скоростью `v`; со `side` только сторону, смотрящую туда, с весом по углу.
func impulse(v: Vector2, side := Vector2.ZERO) -> void:
	for i in points.size():
		var w := 1.0
		if side != Vector2.ZERO:
			w = maxf(0.0, _rest[i].normalized().dot(side.normalized()))
		velocities[i] += v * w


## Тело ведётся центром кинематически: точки живут в его системе, а рывок центра (прыжок,
## приземление) толкает их на долю `blob_inertia` своей скорости, иначе тело схлопывается.
func step(delta: float, target: Vector2, ground: Callable) -> void:
	if delta <= 0.0:
		return
	if not _ready or target.distance_to(center) > radius * 8.0:
		reset(target)
	var tu := Jelly.tuning()
	var from := center
	var cv := (target - from) / delta
	var dv := cv - center_velocity
	center_velocity = cv
	var n := points.size()
	var local := PackedVector2Array()
	local.resize(n)
	for i in n:
		local[i] = points[i] - from
		velocities[i] -= dv * tu.blob_inertia
	var speed := cv.length() if stretch_free else absf(cv.y)
	var s := 1.0 + clampf(speed * tu.blob_stretch, 0.0, tu.blob_stretch_max)
	var dir := cv.angle() if stretch_free and speed > 1.0 else PI / 2.0
	# Вытягивание вдоль `dir`, сжатие поперёк, затем поворот формы и масштаб.
	var form := Transform2D(dir, Vector2.ZERO) * Transform2D(0.0, Vector2(s, 1.0 / sqrt(s)), 0.0, Vector2.ZERO) \
			* Transform2D(-dir, Vector2.ZERO) * Transform2D(angle, Vector2.ZERO).scaled(Vector2.ONE * shape_scale)
	var subs := maxi(1, ceili(delta / SUBSTEP))
	var dt := delta / subs
	var touching := 0
	contact_min = INF
	contact_max = -INF
	for k in subs:
		_time += dt
		var c := from.lerp(target, float(k + 1) / subs)
		var sit := Vector2(0.0, tu.blob_sit * radius)
		var breathe := 1.0 + tu.blob_breathe * sin(_time * TAU * 0.7)
		var area := _area_of(local)
		var area0 := _area0 * shape_scale * shape_scale
		var pressure := tu.blob_pressure * (area0 - area) / area0
		var last_pass := k == subs - 1
		for i in n:
			var q := local[i]
			var prev := local[(i - 1 + n) % n]
			var next := local[(i + 1) % n]
			var goal := sit + form * (_rest[i] * breathe)
			var tangent := next - prev
			var normal := Vector2(tangent.y, -tangent.x).normalized()
			var a := (goal - q) * tu.blob_stiffness - velocities[i] * tu.blob_damping
			a += ((prev + next) * 0.5 - q) * tu.blob_neighbor
			a += normal * pressure
			a.y += tu.blob_gravity
			velocities[i] += a * dt
		for i in n:
			var q := local[i] + velocities[i] * dt
			var v := velocities[i]
			if collide:
				var p := c + q
				var gy: float = ground.call(p.x)
				if p.y > gy:
					q.y = gy - c.y
					# Поверхность неподвижна в мире: вниз точка не идёт, трение тормозит её мировую скорость.
					if v.y + cv.y > 0.0:
						v.y = -cv.y if cv.y < 0.0 else 0.0
					v.x -= (v.x + cv.x) * minf(1.0, tu.blob_friction * dt)
					if last_pass:
						touching += 1
						contact_min = minf(contact_min, p.x)
						contact_max = maxf(contact_max, p.x)
				for w in walls:
					var wp := c + q
					if w.has_point(wp):
						# Выталкивание на ближнюю боковую грань.
						if wp.x - w.position.x < w.end.x - wp.x:
							q.x = w.position.x - c.x
							v.x = minf(v.x, -cv.x)
						else:
							q.x = w.end.x - c.x
							v.x = maxf(v.x, -cv.x)
			local[i] = q
			velocities[i] = v
	for i in n:
		points[i] = target + local[i]
	center = target
	contact = float(touching) / n


## Контур для рисования со сдвигом камеры, сглаженный Catmull-Rom по `smooth` на отрезок.
func polygon(offset: Vector2, smooth := 3) -> PackedVector2Array:
	var n := points.size()
	var out := PackedVector2Array()
	out.resize(n * smooth)
	for i in n:
		var p0 := points[(i - 1 + n) % n]
		var p1 := points[i]
		var p2 := points[(i + 1) % n]
		var p3 := points[(i + 2) % n]
		for j in smooth:
			var t := float(j) / smooth
			var t2 := t * t
			var t3 := t2 * t
			out[i * smooth + j] = offset + 0.5 * ((2.0 * p1) + (p2 - p0) * t
					+ (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2 + (3.0 * p1 - p0 - 3.0 * p2 + p3) * t3)
	return out


static func _area_of(ps: PackedVector2Array) -> float:
	var a := 0.0
	var n := ps.size()
	for i in n:
		var p := ps[i]
		var q := ps[(i + 1) % n]
		a += p.x * q.y - q.x * p.y
	return absf(a) * 0.5
