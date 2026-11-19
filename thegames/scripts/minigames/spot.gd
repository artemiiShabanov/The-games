extends Minigame
## «Найди отличие» (spot, графика), каталог `docs/specs/minigames_catalog.md`. Заменила «Наведи»
## (beam) по плейтесту 2026-11-14, #131. Две пиксельные картинки рядом отличаются одной клеткой. Курсор стрелками ходит
## по правой картинке (на левой бледная рамка показывает ту же клетку), A отмечает. Угадал:
## следующая пара. Счёт (2026-11-18): доля найденных пар минус штраф по порогу `GRACE` за каждую
## неверную отметку, предела нет; неверные крестиками справа сверху.
## Клетка всегда отличается цветом палитры (оттенки сняты плейтестом 2026-11-14).
## Параметры от `t` в `resources/minigames/spot.tres`: size (сторона сетки, 6 → 8), pairs
## (пар, одно число на всех `t`), mirror (от 0.5 правая картинка зеркальная).

const GRID_PX := 480.0
const CELL_GAP := 4.0
## Счёт: неверная отметка стоит столько. Прежний «еле прошёл» это одна неверная, 0,8.
## Сколько ошибок стоят мало (`Minigame.mistake_loss`, 2026-11-19): каждая следующая резко
## поднимает шанс бага.
const GRACE := 1
## Бот LOSE: столько неверных отметок, потом просто водит рамку.
const BOT_LOSE_ERRORS := 5
const FOUND_SECONDS := 0.6
const BOT_STEP := 0.08
## Фон, чернила и три акцента палитры игрока (a1..a3): пять цветов клеток.
const PALETTE_SIZE := 5


static func palette_color(i: int) -> Color:
	match i:
		0:
			return Style.SURFACE_2
		1:
			return Style.INK
		2:
			return Style.accent(0)
		3:
			return Style.accent(1)
	return Style.accent(2)
## Доля клеток фона (первый цвет палитры).
const BACK_SHARE := 0.4

var n := 6
var pairs_total := 3
var mirror := false

## Картинка: номера цветов палитры по клеткам, строка за строкой.
var cells: Array[int] = []
var diff := Vector2i.ZERO
var diff_color := Color.WHITE
## Курсор в клетках правой картинки, как она на экране.
var cursor := Vector2i.ZERO
var found := 0
var errors := 0

var _found_left := 0.0
var _bot_timer := 0.0
var _shake := JellySpring.new()
var _pop := JellySpring.new()
## Мягкие брызги найденного отличия.
var _splash := SplashFx.new()


func _on_start() -> void:
	n = clampi(int(round(def.param(&"size", t, 6.0))), 3, 10)
	pairs_total = maxi(int(round(def.param(&"pairs", t, 3.0))), 1)
	mirror = def.param(&"mirror", t, 0.0) >= 0.5
	cursor = Vector2i(n / 2, n / 2)
	_new_pair()


func _new_pair() -> void:
	cells.clear()
	for i in n * n:
		cells.append(0 if rng.randf() < BACK_SHARE else rng.randi_range(1, PALETTE_SIZE - 1))
	diff = Vector2i(rng.randi_range(0, n - 1), rng.randi_range(0, n - 1))
	var at := diff.y * n + diff.x
	diff_color = palette_color((cells[at] + rng.randi_range(1, PALETTE_SIZE - 1)) % PALETTE_SIZE)
	queue_redraw()


## Клетка картинки под клеткой экрана правой сетки.
func _picture_cell(shown: Vector2i) -> Vector2i:
	return Vector2i(n - 1 - shown.x, shown.y) if mirror else shown


func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	if event.is_action_pressed(GameInput.UP):
		_move(Vector2i.UP)
	elif event.is_action_pressed(GameInput.DOWN):
		_move(Vector2i.DOWN)
	elif event.is_action_pressed(GameInput.LEFT):
		_move(Vector2i.LEFT)
	elif event.is_action_pressed(GameInput.RIGHT):
		_move(Vector2i.RIGHT)
	elif event.is_action_pressed(GameInput.A):
		_mark()
	else:
		return
	get_viewport().set_input_as_handled()


## Мышь: наведение на любую из картинок ставит курсор на клетку, клик отмечает.
func _on_mouse(event: InputEventMouse) -> bool:
	var m := event as InputEventMouseMotion
	if m == null or _found_left > 0.0:
		return false
	for which in 2:
		var local := (m.position - _grid_origin(which)) / (GRID_PX / n)
		if local.x >= 0.0 and local.y >= 0.0 and local.x < n and local.y < n:
			var c := Vector2i(int(local.x), int(local.y))
			var shown := c if which == 1 else _picture_cell(c)
			if shown != cursor:
				cursor = shown
				queue_redraw()
	return false


func _move(step: Vector2i) -> void:
	if _found_left > 0.0:
		return
	var to := Vector2i(clampi(cursor.x + step.x, 0, n - 1), clampi(cursor.y + step.y, 0, n - 1))
	if to == cursor:
		return
	cursor = to
	sfx(MiniSfx.Kind.TAP)
	queue_redraw()


func _mark() -> void:
	if _found_left > 0.0:
		return
	if _picture_cell(cursor) == diff:
		found += 1
		_found_left = FOUND_SECONDS
		_pop.kick(8.0)
		if Jelly.on():
			_splash.pop(_cell_rect(1, cursor).get_center(), Style.SUCCESS, 7, 460.0, 0.55)
		sfx(MiniSfx.Kind.HIT, 196.0, pow(2.0, (found - 1) / 6.0))
	else:
		errors += 1
		_shake.kick(70.0)
		sfx(MiniSfx.Kind.MISS)
	queue_redraw()


func _on_tick(delta: float) -> void:
	if _found_left > 0.0:
		_found_left -= delta
		if _found_left <= 0.0:
			if found >= pairs_total:
				finish_score(_score())
			else:
				_new_pair()
	queue_redraw()


## Счёт: найденные пары минус неверные отметки.
## Итог для сцены оценки мини-игр (`minigame_rating_test`).
func summary() -> String:
	return "пар %d из %d, неверных %d" % [found, pairs_total, errors]  # i18n: skip


func _score() -> float:
	return float(found) / pairs_total - mistake_loss(errors, GRACE)


func _on_finish(_success: bool) -> void:
	if AutoTest.enabled:
		AutoTest.note("spot: t %.2f, счёт %.2f, пар %d из %d, неверных %d, %.1f с" % [t, score, found, pairs_total, errors, elapsed])


## Бот: WIN идёт курсором к отличию и отмечает, LOSE отмечает клетки без отличия
## (`BOT_LOSE_ERRORS` раз), потом водит рамку мимо.
func _bot_step(delta: float) -> bool:
	if _found_left > 0.0:
		return false
	_bot_timer += delta
	if _bot_timer < BOT_STEP:
		return false
	_bot_timer = 0.0
	var goal := _picture_cell(diff)
	if AutoTest.bot_mode != AutoTest.BotMode.WIN:
		if cursor == goal or errors >= BOT_LOSE_ERRORS:
			_move(Vector2i.RIGHT if cursor.x < n - 1 else Vector2i.LEFT)
		else:
			_mark()
	elif cursor.x != goal.x:
		_move(Vector2i(signi(goal.x - cursor.x), 0))
	elif cursor.y != goal.y:
		_move(Vector2i(0, signi(goal.y - cursor.y)))
	else:
		_mark()
	return false


func _process(delta: float) -> void:
	super(delta)
	if def == null or paused:
		return
	var tu := Jelly.tuning()
	_shake.step(delta, tu.spring_stiffness, tu.spring_damping)
	_pop.step(delta, tu.spring_stiffness, tu.spring_damping)
	_splash.step(delta, Callable())
	if not running:
		queue_redraw()


# --- Рисование --------------------------------------------------------------------------------

## Левый верхний угол сетки: 0 образец слева, 1 правая с отличием.
func _grid_origin(which: int) -> Vector2:
	var cx := size.x * (0.3 if which == 0 else 0.7)
	return Vector2(cx - GRID_PX / 2.0, size.y * 0.53 - GRID_PX / 2.0)


func _cell_rect(which: int, shown: Vector2i) -> Rect2:
	var step := GRID_PX / n
	return Rect2(_grid_origin(which) + Vector2(shown) * step + Vector2.ONE * CELL_GAP / 2.0, Vector2.ONE * (step - CELL_GAP))


func _draw() -> void:
	if def == null or cells.is_empty():
		return
	var shake := Vector2(clampf(_shake.value, -20.0, 20.0), 0.0) if Jelly.on() else Vector2.ZERO
	for which in 2:
		var plate := Rect2(_grid_origin(which) - Vector2.ONE * 20.0, Vector2.ONE * (GRID_PX + 40.0))
		if which == 1:
			plate.position += shake
		Style.flat(Style.SURFACE_SOLID, Style.R_CARD).draw(get_canvas_item(), plate)
		for y in n:
			for x in n:
				var shown := Vector2i(x, y)
				var cell := shown if which == 0 else _picture_cell(shown)
				var col := palette_color(cells[cell.y * n + cell.x])
				if which == 1 and cell == diff:
					col = diff_color
				var rect := _cell_rect(which, shown)
				if which == 1:
					rect.position += shake
				if _found_left > 0.0 and cell == diff:
					rect = rect.grow(6.0 * clampf(1.0 + _pop.value * 0.1, 0.0, 2.0))
				draw_rect(rect, col)
	# Курсор: рамка на правой картинке, бледная на той же клетке левой.
	var hit := _found_left > 0.0
	draw_rect(_cell_rect(0, _picture_cell(cursor)).grow(5.0), Style.SUCCESS if hit else Style.INK_3, false, 4.0)
	var right := _cell_rect(1, cursor).grow(5.0)
	right.position += shake
	draw_rect(right, Style.SUCCESS if hit else Style.FOCUS, false, 6.0)
	_splash.draw_air(self, Vector2.ZERO)
	# Пары точками, ошибки крестиками справа сверху.
	for j in pairs_total:
		draw_circle(Vector2(size.x - 48.0 - (pairs_total - 1 - j) * 28.0, 92.0), 7.0,
				Style.SUCCESS if j < found else Style.SURFACE_2)
	draw_mistakes(errors)
