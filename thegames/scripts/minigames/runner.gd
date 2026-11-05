extends Minigame
## «Прыгай» (runner, платформер), каталог `docs/specs/minigames_catalog.md`.
## Точка бежит сама по линии, A прыжок, впереди ямы и столбики. Добежать до конца дорожки,
## провал при двух падениях. С `t` препятствия плотнее, появляются двойные ямы и столбики
## подряд. Абстрактно, в стиле оболочки: линия, круг, прямоугольники.
## Параметры от `t` в `resources/minigames/runner.tres`: speed, gap, combo_share.

enum Kind { PIT, PILLAR }

class Obstacle:
	var kind := Kind.PIT
	var x := 0.0
	var w := 100.0

const RUN_SECONDS := 16.0
const FAIL_AT := 2
const DOT_R := 28.0
const DOT_SCREEN_X := 0.3
const JUMP_DISTANCE := 300.0
const JUMP_HEIGHT := 170.0
const PIT_W := Vector2(90.0, 120.0)
const PIT_LANDING := 80.0
const PILLAR_W := 40.0
const PILLAR_H := 100.0
const PILLAR_ROW_GAP := 260.0
const GROUND_FROM_BOTTOM := 230.0
const FALL_SECONDS := 0.5
const SAFE_SECONDS := 0.7
const SQUASH_SECONDS := 0.12
const BOT_LOOKAHEAD := 140.0

var speed := 420.0
var gap := 480.0
var combo_share := 0.0

var obstacles: Array[Obstacle] = []
var track_length := 0.0
var world_x := 0.0
var dot_y := 0.0
var vel_y := 0.0
var grounded := true
var falls := 0
var fall_left := 0.0
var fall_kind := Kind.PIT
var fall_from := Vector2.ZERO
var safe_left := 0.0
var squash_left := 0.0
var reached := false
var _jump_sound: AudioStreamPlayer
var _fall_sound: AudioStreamPlayer
var _finish_sound: AudioStreamPlayer


func _on_start() -> void:
	speed = def.param(&"speed", t, 420.0)
	gap = def.param(&"gap", t, 480.0)
	combo_share = def.param(&"combo_share", t, 0.0)
	track_length = RUN_SECONDS * speed
	_build_track()
	_jump_sound = Sfx.player(Sfx.blip(560.0, 0.1, 0.3, 24.0))
	_fall_sound = Sfx.player(Sfx.thud(0.18, 0.5))
	_finish_sound = Sfx.player(Sfx.blip(880.0, 0.3, 0.45, 8.0))
	add_child(_jump_sound)
	add_child(_fall_sound)
	add_child(_finish_sound)
	queue_redraw()


## Препятствия по дорожке с промежутком `gap`; с `t` двойные ямы и столбики подряд.
func _build_track() -> void:
	var x := speed * 1.5
	while x < track_length - speed * 1.5:
		var pit := rng.randf() < 0.6
		var combo := rng.randf() < combo_share
		if pit:
			var w := rng.randf_range(PIT_W.x, PIT_W.y)
			_add(Kind.PIT, x, w)
			if combo:
				_add(Kind.PIT, x + w + PIT_LANDING, rng.randf_range(PIT_W.x, PIT_W.y))
				x += w + PIT_LANDING + PIT_W.y
			else:
				x += w
		else:
			_add(Kind.PILLAR, x, PILLAR_W)
			if combo:
				_add(Kind.PILLAR, x + PILLAR_W + PILLAR_ROW_GAP, PILLAR_W)
				x += PILLAR_W * 2.0 + PILLAR_ROW_GAP
			else:
				x += PILLAR_W
		x += gap * rng.randf_range(0.85, 1.15)


func _add(kind: Kind, x: float, w: float) -> void:
	var o := Obstacle.new()
	o.kind = kind
	o.x = x
	o.w = w
	obstacles.append(o)


func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	if GameInput.is_a(event):
		_jump()
		get_viewport().set_input_as_handled()


func _jump() -> void:
	if not grounded or fall_left > 0.0 or reached:
		return
	var airtime := JUMP_DISTANCE / speed
	vel_y = -4.0 * JUMP_HEIGHT / airtime
	grounded = false
	squash_left = SQUASH_SECONDS
	_jump_sound.play()


func _on_tick(delta: float) -> void:
	squash_left = maxf(squash_left - delta, 0.0)
	safe_left = maxf(safe_left - delta, 0.0)
	if reached:
		queue_redraw()
		return
	if fall_left > 0.0:
		fall_left -= delta
		if fall_left <= 0.0:
			_respawn()
		queue_redraw()
		return
	world_x += speed * delta
	if not grounded:
		var airtime := JUMP_DISTANCE / speed
		var g := 8.0 * JUMP_HEIGHT / (airtime * airtime)
		vel_y += g * delta
		dot_y += vel_y * delta
		if dot_y >= 0.0:
			dot_y = 0.0
			vel_y = 0.0
			grounded = true
			squash_left = SQUASH_SECONDS
	if safe_left <= 0.0:
		_check_collisions()
	if world_x >= track_length:
		reached = true
		_finish_sound.play()
		finish(true)
	queue_redraw()


func _on_timeout() -> bool:
	return reached


## Бот: WIN прыгает, когда препятствие близко, LOSE бежит в ямы.
func _bot_step(_delta: float) -> bool:
	if AutoTest.bot_mode != AutoTest.BotMode.WIN or not grounded:
		return false
	for o in obstacles:
		var d := o.x - world_x
		if d > 0.0 and d <= BOT_LOOKAHEAD:
			_jump()
			break
	return false


func _check_collisions() -> void:
	for o in obstacles:
		match o.kind:
			Kind.PIT:
				if grounded and world_x > o.x + DOT_R * 0.5 and world_x < o.x + o.w - DOT_R * 0.5:
					_fall(o)
					return
			Kind.PILLAR:
				var dot_top := -DOT_R * 0.8
				var pillar_top := -PILLAR_H
				if world_x + DOT_R * 0.8 > o.x and world_x - DOT_R * 0.8 < o.x + o.w and dot_y + DOT_R * 0.8 > pillar_top and dot_top < 0.0:
					_fall(o)
					return


func _fall(o: Obstacle) -> void:
	falls += 1
	fall_kind = o.kind
	fall_left = FALL_SECONDS
	fall_from = Vector2(world_x, dot_y)
	_fall_sound.play()
	if falls >= FAIL_AT:
		fall_left = FALL_SECONDS * 0.8
	# Точка возрождается сразу за препятствием (для двойной ямы: за второй).
	var end_x := o.x + o.w
	for other in obstacles:
		if other.x > o.x and other.x <= end_x + PIT_LANDING + 1.0 and other.kind == o.kind:
			end_x = maxf(end_x, other.x + other.w)
	world_x = end_x + 60.0


func _respawn() -> void:
	if falls >= FAIL_AT:
		finish(false)
		return
	dot_y = 0.0
	vel_y = 0.0
	grounded = true
	safe_left = SAFE_SECONDS


# --- Рисование ----------------------------------------------------------------------------

func _draw() -> void:
	if def == null:
		return
	var ground_y := size.y - GROUND_FROM_BOTTOM
	var dot_sx := size.x * DOT_SCREEN_X
	var cam := world_x - dot_sx
	var left := cam
	var right := cam + size.x
	# Земля с ямами: рисуем отрезки между ямами.
	var segments: Array[Vector2] = []
	var cursor := left
	for o in obstacles:
		if o.kind != Kind.PIT or o.x + o.w < left or o.x > right:
			continue
		segments.append(Vector2(cursor, o.x))
		cursor = o.x + o.w
	segments.append(Vector2(cursor, minf(right, track_length + 400.0)))
	for s in segments:
		if s.y <= s.x:
			continue
		draw_line(Vector2(s.x - cam, ground_y), Vector2(s.y - cam, ground_y), Style.INK, 6.0, true)
	# Края ям и тень под ямой.
	for o in obstacles:
		if o.x + o.w < left or o.x > right:
			continue
		var sx := o.x - cam
		if o.kind == Kind.PIT:
			draw_line(Vector2(sx, ground_y), Vector2(sx, ground_y + 24.0), Style.INK, 6.0, true)
			draw_line(Vector2(sx + o.w, ground_y), Vector2(sx + o.w, ground_y + 24.0), Style.INK, 6.0, true)
			draw_rect(Rect2(sx, ground_y + 3.0, o.w, 40.0), Color(Style.INK, 0.06))
		else:
			var rect := Rect2(sx, ground_y - PILLAR_H, o.w, PILLAR_H)
			Style.flat(Style.accent(1), 8, Color.TRANSPARENT, 0).draw(get_canvas_item(), rect)
	# Финиш: столб с флажком.
	var fx := track_length - cam
	if fx > -100.0 and fx < size.x + 100.0:
		draw_line(Vector2(fx, ground_y), Vector2(fx, ground_y - 200.0), Style.accent(2), 6.0, true)
		draw_colored_polygon(PackedVector2Array([Vector2(fx, ground_y - 200.0), Vector2(fx + 70.0, ground_y - 175.0), Vector2(fx, ground_y - 150.0)]), Style.accent(2))
	# Точка: сплюснутая при приземлении, вытянутая в прыжке; падение тонет под землю.
	var pos := Vector2(dot_sx, ground_y - DOT_R + dot_y)
	var col := Style.accent(0)
	var sx_scale := 1.0
	var sy_scale := 1.0
	if fall_left > 0.0:
		var p := 1.0 - fall_left / FALL_SECONDS
		pos = Vector2(fall_from.x - cam + (20.0 if fall_kind == Kind.PIT else -40.0) * p, ground_y - DOT_R + fall_from.y + 120.0 * p * p)
		col = Style.accent(0).lerp(Style.INK_3, p)
		col.a = 1.0 - p
	elif squash_left > 0.0:
		var k := squash_left / SQUASH_SECONDS
		if grounded:
			sx_scale = 1.0 + 0.25 * k
			sy_scale = 1.0 - 0.25 * k
		else:
			sx_scale = 1.0 - 0.15 * k
			sy_scale = 1.0 + 0.15 * k
	elif not grounded:
		sy_scale = 1.0 + clampf(absf(vel_y) / 1500.0, 0.0, 0.15)
		sx_scale = 2.0 - sy_scale
	if safe_left > 0.0 and int(safe_left * 12.0) % 2 == 0:
		col.a *= 0.4
	draw_set_transform(pos, 0.0, Vector2(sx_scale, sy_scale))
	draw_circle(Vector2.ZERO, DOT_R, col)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	# Прогресс дорожки сверху и падения справа.
	var bar_x := size.x * 0.3
	var bar_w := size.x * 0.4
	draw_line(Vector2(bar_x, 60.0), Vector2(bar_x + bar_w, 60.0), Style.SURFACE_2, 4.0, true)
	draw_circle(Vector2(bar_x + bar_w * clampf(world_x / track_length, 0.0, 1.0), 60.0), 7.0, Style.INK)
	var gap2 := 28.0
	var rx := size.x - 48.0 - (FAIL_AT - 1) * gap2
	for i in FAIL_AT:
		draw_circle(Vector2(rx + i * gap2, 60.0), 7.0, Style.DANGER if i < falls else Style.SURFACE_2)
