class_name GolfBall
extends RefCounted
## Мяч гольфа × 8-bit (#52): полёт с тяжестью и ветром, отскоки от поверхности лунки с потерей
## скорости по виду поверхности, качение по склону с трением, падение в люк, море и аут. Шаг
## ровный (`GolfDemoTuning.physics_hz`), так что бот считает удар этим же кодом, что и игра,
## и попадает туда же.

enum Mode { AIR, ROLL, REST, CUP, WATER, OUT }

## Мяч ушёл в поверхность за шаг глубже этого, px: ударился в отвесную стену сбоку.
const WALL_DEPTH := 6.0

var pos := Vector2.ZERO
var vel := Vector2.ZERO
## Качение: скорость вдоль поверхности, плюс вправо.
var roll := 0.0
var mode := Mode.REST
## Пройдено качением, px: демка крутит бочонок по нему.
var spin := 0.0
var time := 0.0
## Отскоков с последнего удара, для звука.
var bounces := 0


## Удар из точки `from` (центр мяча) под углом `angle_deg` к горизонту в сторону `dir` (±1)
## силой `power` (0..1).
func launch(from: Vector2, angle_deg: float, dir: int, power: float, t: GolfDemoTuning) -> void:
	pos = from
	var a := deg_to_rad(angle_deg)
	vel = Vector2(cos(a) * dir, -sin(a)) * power * t.max_speed
	roll = 0.0
	mode = Mode.AIR
	time = 0.0
	bounces = 0


func moving() -> bool:
	return mode == Mode.AIR or mode == Mode.ROLL


## Один шаг физики `dt`; `wind` делениями ветра лунки.
func step(h: GolfCourse.Hole, t: GolfDemoTuning, sea_y: float, wind: int, dt: float) -> void:
	if not moving():
		return
	time += dt
	if time > t.ball_max_time:
		mode = Mode.REST
		return
	if mode == Mode.AIR:
		_air(h, t, sea_y, wind, dt)
	else:
		_roll(h, t, dt)


func _air(h: GolfCourse.Hole, t: GolfDemoTuning, sea_y: float, wind: int, dt: float) -> void:
	var r := t.ball_radius
	var was_x := pos.x
	vel.y += t.gravity * dt
	vel.x += wind * t.wind_accel * dt
	pos += vel * dt
	if pos.x < 0.0 or pos.x > h.length:
		mode = Mode.OUT
		return
	if h.kind_at(pos.x) == GolfCourse.Kind.WATER:
		if pos.y >= sea_y:
			mode = Mode.WATER
		return
	var ground := h.height_at(pos.x)
	if h.kind_at(was_x) == GolfCourse.Kind.WATER and pos.y > ground + 2.0:
		# Из пролива в отвесный берег: отскок назад, мяч падает в море.
		pos.x = was_x
		vel.x = -vel.x * 0.3
		return
	if pos.y + r < ground:
		return
	if pos.y + r - ground > WALL_DEPTH:
		# Глубоко в поверхности за шаг: это отвесная стена (корма, кромка), отскок вбок.
		pos.x = was_x
		vel.x = -vel.x * t.hull_bounce
		return
	if absf(pos.x - h.cup_x) < t.cup_half and vel.length() < t.cup_capture_air and absf(h.slope_at(pos.x)) <= t.cup_max_slope:
		_holed(h)
		return
	var s := h.slope_at(pos.x)
	var n := Vector2(s, -1.0).normalized()
	var tan := Vector2(1.0, s).normalized()
	var vn := vel.dot(n)
	var vt := vel.dot(tan)
	pos.y = ground - r
	if vn >= 0.0:
		return
	var k := h.kind_at(pos.x)
	var after := -vn * _bounce(k, t)
	vt *= _keep(k, t)
	bounces += 1
	if after < t.roll_threshold:
		mode = Mode.ROLL
		roll = vt
		vel = tan * vt
	else:
		vel = tan * vt + n * after


func _roll(h: GolfCourse.Hole, t: GolfDemoTuning, dt: float) -> void:
	var r := t.ball_radius
	var s := h.slope_at(pos.x)
	var inv := 1.0 / sqrt(1.0 + s * s)
	var pull := t.gravity * s * inv
	var fr := _friction(h.kind_at(pos.x), t)
	if absf(roll) < t.stop_speed and absf(pull) <= fr:
		mode = Mode.REST
		roll = 0.0
		vel = Vector2.ZERO
		return
	roll += pull * dt
	var drag := fr * dt
	roll = 0.0 if absf(roll) <= drag else roll - signf(roll) * drag
	var nx := pos.x + roll * inv * dt
	spin += roll * dt
	if nx < 0.0 or nx > h.length:
		mode = Mode.OUT
		return
	vel = Vector2(roll * inv, roll * s * inv)
	if h.kind_at(nx) == GolfCourse.Kind.WATER:
		# Скатился в пролив: дальше падает.
		pos.x = nx
		mode = Mode.AIR
		return
	pos.x = nx
	pos.y = h.height_at(nx) - r
	if absf(pos.x - h.cup_x) < t.cup_half and absf(roll) < t.cup_capture_roll and absf(h.slope_at(pos.x)) <= t.cup_max_slope:
		_holed(h)


func _holed(h: GolfCourse.Hole) -> void:
	mode = Mode.CUP
	pos = Vector2(h.cup_x, h.height_at(h.cup_x) + 3.0)
	vel = Vector2.ZERO
	roll = 0.0


static func _bounce(k: GolfCourse.Kind, t: GolfDemoTuning) -> float:
	match k:
		GolfCourse.Kind.DECK:
			return t.deck_bounce
		GolfCourse.Kind.HULL:
			return t.hull_bounce
	return t.sand_bounce


static func _keep(k: GolfCourse.Kind, t: GolfDemoTuning) -> float:
	match k:
		GolfCourse.Kind.DECK:
			return t.deck_keep
		GolfCourse.Kind.HULL:
			return t.hull_keep
	return t.sand_keep


static func _friction(k: GolfCourse.Kind, t: GolfDemoTuning) -> float:
	match k:
		GolfCourse.Kind.DECK:
			return t.deck_friction
		GolfCourse.Kind.HULL:
			return t.hull_friction
	return t.sand_friction
