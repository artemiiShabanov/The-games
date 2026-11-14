extends Minigame
## «Прыгай» (runner, платформер), каталог `docs/specs/minigames_catalog.md`.
## Точка бежит сама по линии, A прыжок, высота по длине нажатия (отпустил раньше: короче),
## впереди ямы и столбики. Добежать до конца дорожки, провал при двух падениях. Хитбоксы
## меньше картинки, чтобы прощать касания (плейтест 2026-11-05). С `t` препятствия плотнее, появляются широкие ямы и столбики
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
const WIDE_PIT := 0.8
const PILLAR_W := 40.0
const PILLAR_H := 100.0
const PILLAR_ROW_GAP := 260.0
const GROUND_FROM_BOTTOM := 230.0
const FALL_SECONDS := 0.5
const SAFE_SECONDS := 0.91
## Отпустил A в подъёме: вертикальная скорость режется, прыжок короче.
const JUMP_CUT := 0.45
const STRETCH_SECONDS := 0.25
const SQUASH_SECONDS := 0.18
## Доля радиуса, которая считается телом: меньше картинки, касания прощаются.
const HIT_R := 0.495
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
var air_time := 0.0
var land_time := 1.0
var reached := false
var _jump_sound: AudioStreamPlayer
var _fall_sound: AudioStreamPlayer
var _finish_sound: AudioStreamPlayer
## Прототип желе (ветка proto/jelly): вид поверх того же геймплея, `Jelly.on()` выбирает рисунок.
var jelly: RunnerJelly


func _on_start() -> void:
	speed = def.param(&"speed", t, 420.0)
	gap = def.param(&"gap", t, 480.0)
	combo_share = def.param(&"combo_share", t, 0.0)
	track_length = RUN_SECONDS * speed
	_build_track()
	# Прыжок и приземление упругие: один шлёп, приземление тяжелее и тише.
	_jump_sound = MiniSfx.squish(150.0)
	_fall_sound = MiniSfx.miss()
	_finish_sound = MiniSfx.win()
	add_child(_jump_sound)
	add_child(_fall_sound)
	add_child(_finish_sound)
	_setup_jelly()
	queue_redraw()


func _setup_jelly() -> void:
	Jelly.register_debug()
	var pits: Array[Vector2] = []
	var pillars: Array[Vector2] = []
	for o in obstacles:
		if o.kind == Kind.PIT:
			pits.append(Vector2(o.x, o.x + o.w))
		else:
			pillars.append(Vector2(o.x, o.w))
	jelly = RunnerJelly.new()
	jelly.setup(pits, pillars, track_length, DOT_R, PILLAR_H, FAIL_AT, rng.randi())
	jelly.ground_y = size.y - GROUND_FROM_BOTTOM


## Центр точки в координатах мира желе: X по дорожке, Y экранный.
func _dot_world() -> Vector2:
	var ground_y := size.y - GROUND_FROM_BOTTOM
	if fall_left > 0.0:
		var p := 1.0 - fall_left / FALL_SECONDS
		return Vector2(fall_from.x + (20.0 if fall_kind == Kind.PIT else -40.0) * p, ground_y - DOT_R + fall_from.y + 120.0 * p * p)
	return Vector2(world_x, ground_y - DOT_R + dot_y)


## Желе живёт и после финиша, пока сцена на экране; на паузе стоит.
func _process(delta: float) -> void:
	super(delta)
	if jelly == null or paused:
		return
	jelly.ground_y = size.y - GROUND_FROM_BOTTOM
	jelly.step(delta, _dot_world())
	if not running:
		queue_redraw()


## Препятствия по дорожке с промежутком `gap`; с `t` широкие ямы и столбики подряд.
func _build_track() -> void:
	var x := speed * 1.5
	while x < track_length - speed * 1.5:
		var pit := rng.randf() < 0.6
		var combo := rng.randf() < combo_share
		if pit:
			var w := rng.randf_range(PIT_W.x, PIT_W.y)
			if combo:
				# Вместо двух ям подряд одна широкая: `WIDE_PIT` от их общей длины с площадкой
				# между ними (плейтест 2026-11-14, #131).
				w = WIDE_PIT * (w + PIT_LANDING + rng.randf_range(PIT_W.x, PIT_W.y))
			_add(Kind.PIT, x, w)
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
	elif event.is_action_released(GameInput.A) and not grounded and vel_y < 0.0:
		vel_y *= JUMP_CUT


func _jump() -> void:
	if not grounded or fall_left > 0.0 or reached:
		return
	var airtime := JUMP_DISTANCE / speed
	vel_y = -4.0 * JUMP_HEIGHT / airtime
	grounded = false
	air_time = 0.0
	_jump_sound.play()
	jelly.jump(world_x)


func _on_tick(delta: float) -> void:
	safe_left = maxf(safe_left - delta, 0.0)
	land_time += delta
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
		air_time += delta
		if dot_y >= 0.0:
			jelly.land(world_x, vel_y)
			sfx(MiniSfx.Kind.SQUISH, 80.0, 1.0, -5.0)
			dot_y = 0.0
			vel_y = 0.0
			grounded = true
			land_time = 0.0
	if safe_left <= 0.0:
		_check_collisions()
	if world_x >= track_length:
		reached = true
		_finish_sound.play()
		jelly.finish()
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
		# Широкую яму прыжок перекрывает впритык: отталкиваться ближе к краю.
		if d > 0.0 and d <= minf(BOT_LOOKAHEAD, JUMP_DISTANCE - o.w - 20.0):
			_jump()
			break
	return false


func _check_collisions() -> void:
	for o in obstacles:
		match o.kind:
			Kind.PIT:
				# Падает, только когда почти вся точка над пустотой.
				if grounded and world_x > o.x + DOT_R * (1.0 - HIT_R) and world_x < o.x + o.w - DOT_R * (1.0 - HIT_R):
					_fall(o)
					return
			Kind.PILLAR:
				var hit := DOT_R * HIT_R
				var pillar_top := -PILLAR_H + 8.0
				if world_x + hit > o.x + 4.0 and world_x - hit < o.x + o.w - 4.0 and dot_y + hit > pillar_top:
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
	var pillar := -1
	if o.kind == Kind.PILLAR:
		pillar = jelly.pillars.find(Vector2(o.x, o.w))
	jelly.fall(_dot_world(), Vector2(o.x, o.x + o.w), pillar, falls - 1)
	# Точка возрождается сразу за препятствием (для двойной ямы: за второй).
	var end_x := o.x + o.w
	for other in obstacles:
		if other.x > o.x and other.x <= end_x + PIT_LANDING + 1.0 and other.kind == o.kind:
			end_x = maxf(end_x, other.x + other.w)
	world_x = end_x + 60.0


func _respawn() -> void:
	jelly.respawn(Vector2(world_x, size.y - GROUND_FROM_BOTTOM - DOT_R))
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
	if Jelly.on() and jelly != null:
		_draw_jelly()
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
	elif not grounded and air_time < STRETCH_SECONDS:
		# Одно плавное вытягивание при отрыве, к вершине форма круглая.
		var k := sin(air_time / STRETCH_SECONDS * PI)
		sy_scale = 1.0 + 0.22 * k
		sx_scale = 1.0 - 0.14 * k
	elif grounded and land_time < SQUASH_SECONDS:
		# Заметное сплющивание при касании, быстро возвращается.
		var k := pow(1.0 - land_time / SQUASH_SECONDS, 1.5)
		sx_scale = 1.0 + 0.45 * k
		sy_scale = 1.0 - 0.4 * k
	if safe_left > 0.0 and int(safe_left * 12.0) % 2 == 0:
		col.a *= 0.4
	draw_set_transform(pos, 0.0, Vector2(sx_scale, sy_scale))
	draw_circle(Vector2.ZERO, DOT_R, col)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	_draw_hud()


func _draw_jelly() -> void:
	var cam := world_x - size.x * DOT_SCREEN_X
	var alpha := 1.0
	if fall_left > 0.0:
		# Об столбик тело растекается лужей и гаснет позже, в яме пропадает сразу.
		var k := fall_left / FALL_SECONDS
		alpha = clampf(k * 2.0, 0.0, 1.0) if fall_kind == Kind.PILLAR else k
	if safe_left > 0.0 and int(safe_left * 12.0) % 2 == 0:
		alpha *= 0.4
	jelly.draw(self, cam, size.x, alpha)
	_draw_hud()


## Прогресс дорожки сверху и падения справа; у желе метка падения вздрагивает.
func _draw_hud() -> void:
	var bar_x := size.x * 0.3
	var bar_w := size.x * 0.4
	draw_line(Vector2(bar_x, 60.0), Vector2(bar_x + bar_w, 60.0), Style.SURFACE_2, 4.0, true)
	draw_circle(Vector2(bar_x + bar_w * clampf(world_x / track_length, 0.0, 1.0), 60.0), 7.0, Style.INK)
	var gap2 := 28.0
	var rx := size.x - 48.0 - (FAIL_AT - 1) * gap2
	for i in FAIL_AT:
		var pop := 0.0
		if Jelly.on() and jelly != null:
			pop = clampf(jelly.pops[i].value * 0.04, -0.5, 1.0)
		draw_circle(Vector2(rx + i * gap2, 60.0), 7.0 * (1.0 + pop), Style.DANGER if i < falls else Style.SURFACE_2)
