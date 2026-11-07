extends Minigame
## «Удержи» (fishing, баланс), каталог `docs/specs/minigames_catalog.md`. Рыбалка как в Stardew
## Valley: вертикальная дорожка, по ней скачет шарик по своей кривой, у игрока столбик. Клавиша
## зажата (A или любая стрелка): столбик поднимается, отпущена: падает. Пока шарик внутри
## столбика, шкала справа растёт, снаружи убывает. Заполнить шкалу до таймера, иначе провал.
## Параметры от `t` в `resources/minigames/fishing.tres`: sharp (резкость кривой шарика), bar
## (высота столбика долей дорожки).

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


## Бот: WIN держит, когда столбик ниже шарика с поправкой на скорость, LOSE не держит.
func _bot_step(_delta: float) -> bool:
	if AutoTest.bot_mode != AutoTest.BotMode.WIN:
		_bot_hold = false
		return false
	var predicted := bar + bar_vel * BOT_LEAD
	_bot_hold = predicted < ball
	return false


# --- Рисование ----------------------------------------------------------------------------

func _draw() -> void:
	if def == null:
		return
	var top := size.y / 2.0 - TRACK_H / 2.0 + 20.0
	var cx := size.x / 2.0 - 40.0
	var track := Rect2(cx - TRACK_W / 2.0, top, TRACK_W, TRACK_H)
	Style.flat(Style.SURFACE_2, Style.R_PILL, Color.TRANSPARENT, 0).draw(get_canvas_item(), track)
	# Столбик игрока.
	var half := bar_size / 2.0
	var bar_top := top + (1.0 - (bar + half)) * TRACK_H
	var bar_rect := Rect2(cx - TRACK_W / 2.0 + 6, bar_top, TRACK_W - 12, bar_size * TRACK_H)
	var bar_color := Style.SUCCESS if inside else Style.accent(0)
	Style.flat(Color(bar_color, 0.35), Style.R_CTL, Color.TRANSPARENT, 0).draw(get_canvas_item(), bar_rect)
	draw_rect(bar_rect, bar_color, false, 4.0)
	# Шарик.
	var shown_ball := ball + sin(wobble * 9.0) * 0.012 * sharp
	var by := top + (1.0 - shown_ball) * TRACK_H
	draw_circle(Vector2(cx, by), BALL_R, Style.accent(1))
	draw_circle(Vector2(cx - 6, by - 6), 5.0, Color(1, 1, 1, 0.7))
	# Шкала справа: от стартовой трети до полной.
	var gx := cx + TRACK_W / 2.0 + 48.0
	var gauge_rect := Rect2(gx, top, GAUGE_W, TRACK_H)
	Style.flat(Style.SURFACE_2, Style.R_PILL, Color.TRANSPARENT, 0).draw(get_canvas_item(), gauge_rect)
	var fill_h := TRACK_H * gauge
	var fill_color := Style.SUCCESS if gauge > 0.25 else Style.DANGER
	Style.flat(fill_color, Style.R_PILL, Color.TRANSPARENT, 0).draw(get_canvas_item(), Rect2(gx, top + TRACK_H - fill_h, GAUGE_W, fill_h))
	# Подпись действия.
	var font := ThemeDB.fallback_font
	var caption := "держи" if _holding() else "отпусти"
	var w := font.get_string_size(caption, HORIZONTAL_ALIGNMENT_LEFT, -1, Style.FONT_CAPTION).x
	draw_string(font, Vector2(cx - w / 2.0, top + TRACK_H + 40.0), caption, HORIZONTAL_ALIGNMENT_LEFT, -1, Style.FONT_CAPTION, Style.INK_3)
