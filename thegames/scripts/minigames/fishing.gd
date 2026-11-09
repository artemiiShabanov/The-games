extends Minigame
## «Удержи» (fishing, баланс), каталог `docs/specs/minigames_catalog.md`. Рыбалка как в Stardew
## Valley: вертикальная дорожка, по ней скачет шарик по своей кривой, у игрока столбик. Клавиша
## зажата (A или любая стрелка): столбик поднимается, отпущена: падает. Пока шарик внутри
## столбика, шкала справа растёт, снаружи убывает. Заполнить шкалу до таймера, иначе провал.
## Параметры от `t` в `resources/minigames/fishing.tres`: sharp (резкость кривой шарика), bar
## (высота столбика долей дорожки).
## Мармелад (STYLE «Мармелад»): столбик и шарик мягкие тела `JellyShape` на тех же игровых
## позициях: в рывке тянутся, у края дорожки столбик плющится, нажатие поджимает его снизу.
## Шарик, попав в столбик, вздрагивает с кружком по воде; поимка: вздрог, два круга и пара
## капель, шкала пружинит вширь; провал: всё сжимается, шарик сереет и тонет. Геймплей прежний.

const TRACK_H := 600.0
const TRACK_W := 72.0
const BALL_R := 20.0
const GAUGE_W := 28.0
const GAUGE_START := 0.3
const FILL_RATE := 0.14
const DRAIN_RATE := 0.1
const BAR_ACCEL := 2.6
const GRAVITY := 2.2
const DAMPING := 2.4
const BOUNCE := 0.35
const BOT_LEAD := 0.12

var sharp := 0.4
var bar_size := 0.28

## Всё в долях дорожки, 0 низ, 1 верх.
var ball := 0.5
var ball_target := 0.5
var ball_speed := 0.0
var jump_timer := 0.0
var bar := 0.3
var bar_vel := 0.0
var gauge := GAUGE_START
var inside := false
var wobble := 0.0
var _tick: AudioStreamPlayer
var _win: AudioStreamPlayer
var _tick_timer := 0.0

## Мармелад: только рисунок, на геймплей не влияет.
var _bar_jelly: JellyShape
var _ball_jelly: JellyShape
var _rings := RingFx.new()
var _splash := SplashFx.new()
var _gauge_spring := JellySpring.new()
var _was_inside := false
var _was_holding := false
var _was_danger := false
var _prev_bar_vel := 0.0
var _poke_cooldown := 0.0
## Исход для рисунка: 0 идёт игра, 1 поймал, -1 упустил; `_end_age` секунды после.
var _outcome := 0
var _end_age := 0.0


func _on_start() -> void:
	sharp = clampf(def.param(&"sharp", t, 0.4), 0.05, 1.0)
	bar_size = clampf(def.param(&"bar", t, 0.28), 0.08, 0.6)
	_tick = Sfx.player(Sfx.blip(1200.0, 0.03, 0.12, 50.0))
	_win = Sfx.player(Sfx.blip(990.0, 0.3, 0.45, 8.0))
	add_child(_tick)
	add_child(_win)
	ball = 0.5
	ball_target = 0.5
	bar = 0.3
	_pick_target()
	_bar_jelly = JellyShape.rect(Vector2(TRACK_W - 12.0, bar_size * TRACK_H), Style.R_CTL, 96)
	_ball_jelly = JellyShape.circle(BALL_R)
	queue_redraw()


func _holding() -> bool:
	if AutoTest.bot_active():
		return _bot_hold
	return GameInput.a_pressed() or Input.is_action_pressed(GameInput.UP) or Input.is_action_pressed(GameInput.DOWN) \
			or Input.is_action_pressed(GameInput.LEFT) or Input.is_action_pressed(GameInput.RIGHT)


## Новая цель шарика: чем резче, тем дальше прыжок и быстрее к нему.
func _pick_target() -> void:
	var reach := lerpf(0.2, 0.55, sharp)
	ball_target = clampf(ball + rng.randf_range(-reach, reach), 0.05, 0.95)
	ball_speed = lerpf(0.35, 1.3, sharp) * rng.randf_range(0.7, 1.3)
	jump_timer = lerpf(1.4, 0.45, sharp) * rng.randf_range(0.6, 1.4)


func _on_tick(delta: float) -> void:
	wobble += delta
	# Шарик: к цели со своей скоростью плюс мелкая дрожь, цели меняются по таймеру.
	jump_timer -= delta
	if jump_timer <= 0.0 or absf(ball - ball_target) < 0.01:
		_pick_target()
	ball = move_toward(ball, ball_target, ball_speed * delta)
	var shown_ball := ball + sin(wobble * 9.0) * 0.012 * sharp
	# Столбик: зажатая клавиша тянет вверх, иначе падает; у краёв отскок.
	var accel := BAR_ACCEL if _holding() else -GRAVITY
	bar_vel += accel * delta
	bar_vel -= bar_vel * DAMPING * delta
	bar += bar_vel * delta
	var half := bar_size / 2.0
	if bar < half:
		bar = half
		bar_vel = absf(bar_vel) * BOUNCE
	elif bar > 1.0 - half:
		bar = 1.0 - half
		bar_vel = -absf(bar_vel) * BOUNCE
	inside = absf(shown_ball - bar) <= half
	gauge = clampf(gauge + (FILL_RATE if inside else -DRAIN_RATE) * delta, 0.0, 1.0)
	if inside:
		_tick_timer -= delta
		if _tick_timer <= 0.0:
			_tick_timer = 0.25
			_tick.play()
	if gauge >= 1.0:
		_win.play()
		finish(true)
		return
	queue_redraw()


func _on_timeout() -> bool:
	return gauge >= 1.0


var _bot_hold := false


## Бот: WIN держит, когда столбик ниже шарика с поправкой на скорость; LOSE уводит столбик от
## шарика (лежащий внизу столбик шарик иногда навещал сам, и шкала могла дорасти).
func _bot_step(_delta: float) -> bool:
	var predicted := bar + bar_vel * BOT_LEAD
	if AutoTest.bot_mode == AutoTest.BotMode.WIN:
		_bot_hold = predicted < ball
	else:
		_bot_hold = predicted < ball - 0.15 if ball < 0.5 else false
	return false


# --- Мармелад ------------------------------------------------------------------------------

## Верх дорожки и её ось по X.
func _track_origin() -> Vector2:
	return Vector2(size.x / 2.0 - 40.0, size.y / 2.0 - TRACK_H / 2.0 + 20.0)


func _shown_ball() -> float:
	return ball + sin(wobble * 9.0) * 0.012 * sharp


## Центр шарика на экране; после провала он тонет до дна дорожки.
func _ball_pos() -> Vector2:
	var o := _track_origin()
	var y := o.y + (1.0 - _shown_ball()) * TRACK_H
	if _outcome < 0:
		var e := 1.0 - pow(1.0 - clampf(_end_age / 0.6, 0.0, 1.0), 2.0)
		y = minf(y + 40.0 * e, maxf(y, o.y + TRACK_H - BALL_R - 4.0))
	return Vector2(o.x, y)


func _on_finish(success: bool) -> void:
	_outcome = 1 if success else -1
	_end_age = 0.0
	if _bar_jelly == null:
		return
	var at := _ball_pos()
	if success:
		_bar_jelly.poke(260.0)
		_ball_jelly.poke(200.0)
		_gauge_spring.kick(160.0)
		_rings.add(at, BALL_R, BALL_R * 2.4, Color(Style.accent(1), 0.35), 2, 0.6)
		_splash.burst(at - Vector2(0.0, BALL_R), 8, 520.0, -PI / 2.0, 0.6, Color(Style.accent(1), 0.75), 3.0, 6.0)
	else:
		_bar_jelly.poke(-220.0)
		_ball_jelly.poke(-180.0)
		_rings.add(at, BALL_R, BALL_R * 1.8, Color(Style.INK, 0.12), 1, 0.7)


## Мармелад живёт и после финиша, пока сцена на экране; на паузе стоит.
func _process(delta: float) -> void:
	super(delta)
	if _bar_jelly == null or paused or def == null:
		return
	var o := _track_origin()
	var half := bar_size / 2.0
	_poke_cooldown = maxf(_poke_cooldown - delta, 0.0)
	if _outcome != 0:
		_end_age += delta
	# Удар о край дорожки: скорость сменила знак у края, бьющая сторона плющится.
	var at_edge := bar <= half + 0.001 or bar >= 1.0 - half - 0.001
	if at_edge and signf(bar_vel) != signf(_prev_bar_vel) and absf(_prev_bar_vel) > 0.15:
		var hit_floor := _prev_bar_vel < 0.0
		var impact := absf(_prev_bar_vel) * TRACK_H * 0.3
		_bar_jelly.push(Vector2(0.0, -impact if hit_floor else impact), Vector2.DOWN if hit_floor else Vector2.UP)
	_prev_bar_vel = bar_vel
	# Нажатие поджимает столбик снизу, отпускание чуть оседает сверху.
	var holding := _holding()
	if running and holding != _was_holding:
		if holding:
			_bar_jelly.push(Vector2(0.0, -90.0), Vector2.DOWN)
		else:
			_bar_jelly.push(Vector2(0.0, 50.0), Vector2.UP)
	_was_holding = holding
	# Шарик зашёл в столбик: оба вздрагивают, по воде кружок; вышел: столбик чуть сжимается.
	if running and inside != _was_inside and _poke_cooldown <= 0.0:
		_poke_cooldown = 0.5
		if inside:
			_bar_jelly.poke(140.0)
			_ball_jelly.poke(120.0)
			_rings.add(_ball_pos(), BALL_R, BALL_R * 1.7, Color(Style.SUCCESS, 0.3), 1, 0.5)
		else:
			_bar_jelly.poke(-90.0)
	_was_inside = inside
	var danger := gauge <= 0.25
	if running and danger != _was_danger:
		_gauge_spring.kick(-80.0 if danger else 80.0)
	_was_danger = danger
	_bar_jelly.follow(delta, Vector2(o.x, o.y + (1.0 - bar) * TRACK_H))
	_ball_jelly.follow(delta, _ball_pos())
	var tu := Jelly.tuning()
	_gauge_spring.step(delta, tu.spring_stiffness, tu.spring_damping)
	_rings.step(delta)
	_splash.step(delta, func(_x: float) -> float: return INF)
	if not running:
		queue_redraw()


# --- Рисование ----------------------------------------------------------------------------

func _draw() -> void:
	if def == null:
		return
	var top := size.y / 2.0 - TRACK_H / 2.0 + 20.0
	var cx := size.x / 2.0 - 40.0
	var track := Rect2(cx - TRACK_W / 2.0, top, TRACK_W, TRACK_H)
	Style.flat(Style.SURFACE_2, Style.R_PILL, Color.TRANSPARENT, 0).draw(get_canvas_item(), track)
	var jelly := Jelly.on() and _bar_jelly != null
	if jelly:
		_rings.draw(self)
	# Столбик игрока.
	var half := bar_size / 2.0
	var bar_color := Style.SUCCESS if inside else Style.accent(0)
	if jelly:
		_bar_jelly.draw(self, Color(bar_color, 0.35))
		_bar_jelly.draw_outline(self, bar_color, 4.0)
	else:
		var bar_top := top + (1.0 - (bar + half)) * TRACK_H
		var bar_rect := Rect2(cx - TRACK_W / 2.0 + 6, bar_top, TRACK_W - 12, bar_size * TRACK_H)
		Style.flat(Color(bar_color, 0.35), Style.R_CTL, Color.TRANSPARENT, 0).draw(get_canvas_item(), bar_rect)
		draw_rect(bar_rect, bar_color, false, 4.0)
	# Шарик; упущенный сереет.
	var ball_color := Style.accent(1)
	if _outcome < 0:
		ball_color = ball_color.lerp(Style.INK_3, clampf(_end_age / 0.4, 0.0, 1.0))
	if jelly:
		var mid := Vector2.ZERO
		for p in _ball_jelly.blob.points:
			mid += p
		mid /= maxf(1.0, _ball_jelly.blob.points.size())
		_ball_jelly.draw(self, ball_color)
		draw_circle(mid + Vector2(-6, -6), 5.0, Color(1, 1, 1, 0.7))
		_splash.draw_air(self, Vector2.ZERO)
	else:
		var by := top + (1.0 - _shown_ball()) * TRACK_H
		draw_circle(Vector2(cx, by), BALL_R, ball_color)
		draw_circle(Vector2(cx - 6, by - 6), 5.0, Color(1, 1, 1, 0.7))
	# Шкала справа: от стартовой трети до полной; в мармеладе пружинит вширь.
	var gx := cx + TRACK_W / 2.0 + 48.0
	var gauge_rect := Rect2(gx, top, GAUGE_W, TRACK_H)
	Style.flat(Style.SURFACE_2, Style.R_PILL, Color.TRANSPARENT, 0).draw(get_canvas_item(), gauge_rect)
	var fill_h := TRACK_H * gauge
	var fill_color := Style.SUCCESS if gauge > 0.25 else Style.DANGER
	var bulge := clampf(_gauge_spring.value, -GAUGE_W * 0.3, GAUGE_W * 0.5) if jelly else 0.0
	Style.flat(fill_color, Style.R_PILL, Color.TRANSPARENT, 0).draw(get_canvas_item(), Rect2(gx - bulge / 2.0, top + TRACK_H - fill_h, GAUGE_W + bulge, fill_h))
	# Подпись действия.
	var font := get_theme_default_font()
	var caption := "держи" if _holding() else "отпусти"
	var w := font.get_string_size(caption, HORIZONTAL_ALIGNMENT_LEFT, -1, Style.FONT_CAPTION).x
	draw_string(font, Vector2(cx - w / 2.0, top - 24.0), caption, HORIZONTAL_ALIGNMENT_LEFT, -1, Style.FONT_CAPTION, Style.INK_3)
