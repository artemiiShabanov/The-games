class_name SplashFx
extends RefCounted
## Брызги, кляксы и след желе. Капли летят по дуге и, коснувшись поверхности (`ground(x)`) или
## стенки (`walls`), становятся кляксами: на земле расплющенными, на стенке стекающими. След:
## полоса по поверхности там, где тело скользит; рвётся в прыжке. Всё в координатах мира
## хозяина, гаснет само. Рисует хозяин в `_draw` через `draw_surface` и `draw_air`.

class Drop:
	var pos := Vector2.ZERO
	var vel := Vector2.ZERO
	var r := 4.0
	var color := Color.WHITE

class Blot:
	var pos := Vector2.ZERO
	var r := 4.0
	var born := 0.0
	var color := Color.WHITE
	var on_wall := false

class TrailPoint:
	var pos := Vector2.ZERO
	var w := 0.0
	var born := 0.0
	var gap := false

const MAX_DROPS := 160
const MAX_BLOTS := 120
## Ниже этой глубины под поверхностью капля пропадает (упала в яму).
const LOST_BELOW := 400.0

var drops: Array[Drop] = []
var blots: Array[Blot] = []
var trail: Array[TrailPoint] = []
var walls: Array[Rect2] = []
var time := 0.0
var rng := RandomNumberGenerator.new()
var _last_trail_x := -INF


## Пучок капель из точки: `count` капель (масштабируется тюнингом), скорость около `speed`,
## направление `angle` (радианы, 0 вправо, −PI/2 вверх) с разбросом `spread`.
func burst(at: Vector2, count: int, speed: float, angle: float, spread: float, color: Color, r_from := 3.0, r_to := 8.0) -> void:
	var n := int(round(count * Jelly.tuning().splash_scale))
	for i in n:
		if drops.size() >= MAX_DROPS:
			drops.pop_front()
		var d := Drop.new()
		var a := angle + rng.randf_range(-spread, spread)
		d.pos = at
		d.vel = Vector2(cos(a), sin(a)) * speed * rng.randf_range(0.45, 1.15)
		d.r = rng.randf_range(r_from, r_to)
		d.color = color
		drops.append(d)


## Точка следа под скользящим телом; `w` ширина.
func add_trail(pos: Vector2, w: float) -> void:
	if absf(pos.x - _last_trail_x) < 5.0:
		return
	_last_trail_x = pos.x
	var p := TrailPoint.new()
	p.pos = pos
	p.w = w
	p.born = time
	trail.append(p)


func break_trail() -> void:
	if trail.is_empty() or trail.back().gap:
		return
	var p := TrailPoint.new()
	p.gap = true
	p.born = time
	trail.append(p)
	_last_trail_x = -INF


## Клякса прямо на поверхности, без полёта (шлепок при приземлении).
func blot(at: Vector2, r: float, color: Color, on_wall := false) -> void:
	if blots.size() >= MAX_BLOTS:
		blots.pop_front()
	var b := Blot.new()
	b.pos = at
	b.r = r
	b.born = time
	b.color = color
	b.on_wall = on_wall
	blots.append(b)


func step(delta: float, ground: Callable) -> void:
	var tu := Jelly.tuning()
	time += delta
	var alive: Array[Drop] = []
	for d in drops:
		d.vel.y += tu.droplet_gravity * delta
		var next := d.pos + d.vel * delta
		var stuck := false
		for w in walls:
			if w.has_point(next):
				blot(Vector2(w.position.x if d.vel.x > 0.0 else w.end.x, next.y), d.r, d.color, true)
				stuck = true
				break
		if not stuck:
			var gy: float = ground.call(next.x)
			if next.y >= gy and d.vel.y > 0.0:
				blot(Vector2(next.x, gy), d.r, d.color)
				stuck = true
			elif gy == INF and next.y > LOST_BELOW + d.pos.y and d.vel.y > 0.0:
				stuck = true
		if not stuck and next.y < 4000.0:
			d.pos = next
			alive.append(d)
	drops = alive
	var keep: Array[Blot] = []
	for b in blots:
		var age := time - b.born
		if age < tu.blot_seconds:
			if b.on_wall:
				b.pos.y += delta * 26.0 * clampf(age, 0.0, 1.0)
			keep.append(b)
	blots = keep
	while not trail.is_empty() and time - trail[0].born > tu.trail_seconds:
		trail.pop_front()


## След и кляксы: поверх поверхности, под телом. Лежат на поверхности `ground(x)`, которая
## сама гуляет волнами, поэтому высота берётся в момент рисования.
func draw_surface(ci: CanvasItem, offset: Vector2, ground: Callable) -> void:
	var tu := Jelly.tuning()
	for i in range(1, trail.size()):
		var a := trail[i - 1]
		var b := trail[i]
		if a.gap or b.gap:
			continue
		var k := 1.0 - (time - b.born) / tu.trail_seconds
		if k <= 0.0:
			continue
		var w := b.w * (0.35 + 0.65 * k) * (0.8 + 0.2 * sin(b.pos.x * 0.07))
		var col := Color(Style.accent(0), tu.trail_alpha * k)
		ci.draw_line(_on_ground(a.pos, ground, a.w * 0.7) + offset, _on_ground(b.pos, ground, b.w * 0.7) + offset, col, w, true)
	for b in blots:
		var age := time - b.born
		var fade := clampf((tu.blot_seconds - age) / (tu.blot_seconds * 0.4), 0.0, 1.0)
		var col := Color(b.color, b.color.a * fade)
		var splat := 1.0 - pow(1.0 - clampf(age / 0.12, 0.0, 1.0), 2.0)
		var scale := Vector2(0.9 + 0.9 * splat, 1.0 - 0.55 * splat)
		if b.on_wall:
			scale = Vector2(0.75, 1.0 + 0.8 * clampf(age, 0.0, 1.0))
		var at := b.pos if b.on_wall else _on_ground(b.pos, ground, 0.0)
		ci.draw_set_transform(at + offset, 0.0, scale)
		ci.draw_circle(Vector2.ZERO, b.r, col)
	ci.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _on_ground(p: Vector2, ground: Callable, lift: float) -> Vector2:
	var gy: float = ground.call(p.x)
	return Vector2(p.x, gy - lift) if gy != INF else p


## Капли в полёте: поверх тела. Вытянуты по скорости.
func draw_air(ci: CanvasItem, offset: Vector2) -> void:
	for d in drops:
		var s := clampf(d.vel.length() / 900.0, 0.0, 0.8)
		ci.draw_set_transform(d.pos + offset, d.vel.angle(), Vector2(1.0 + s, 1.0 / (1.0 + s * 0.5)))
		ci.draw_circle(Vector2.ZERO, d.r, d.color)
	ci.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
