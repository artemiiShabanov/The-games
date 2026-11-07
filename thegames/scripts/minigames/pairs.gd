extends Minigame
## «Запомни» (pairs, технология 8-bit), каталог `docs/specs/minigames_catalog.md`. Сетка 3×4
## закрытых карточек с пиктограммами, курсор стрелками, A открывает; две одинаковые остаются
## открытыми, разные закрываются через паузу. Собрать все пары до таймера, иначе провал. С `t`
## сетка 4×4 и карточки закрываются быстрее. Параметры в `resources/minigames/pairs.tres`:
## cols (3 или 4 при четырёх рядах), close (секунды до закрытия непарных).

enum Shape { CIRCLE, SQUARE, TRIANGLE, DIAMOND, RING, CROSS, STAR, HEX }

const ROWS := 4
const CARD := 128.0
const GAP := 16.0
const FLIP_SECONDS := 0.16
const BOT_STEP := 0.3

var cols := 3
var close_seconds := 1.0

var kinds: Array[int] = []
var open: Array[bool] = []
var matched: Array[bool] = []
var flip: Array[float] = []
var cursor := Vector2i.ZERO
var first := -1
var second := -1
var close_timer := 0.0
var pairs_done := 0
var _bot_timer := 0.0
var _bot_memory: Array[int] = []
var _flip_sound: AudioStreamPlayer
var _match_sound: AudioStreamPlayer
var _miss_sound: AudioStreamPlayer


func _on_start() -> void:
	cols = clampi(int(round(def.param(&"cols", t, 3.0))), 2, 5)
	close_seconds = def.param(&"close", t, 1.0)
	_flip_sound = Sfx.player(Sfx.blip(760.0, 0.05, 0.25, 40.0))
	_match_sound = Sfx.player(Sfx.blip(990.0, 0.14, 0.4, 16.0))
	_miss_sound = Sfx.player(Sfx.thud(0.1, 0.35))
	for p in [_flip_sound, _match_sound, _miss_sound]:
		add_child(p)
	var n := cols * ROWS
	var deck: Array[int] = []
	for i in n / 2:
		deck.append(i % Shape.size())
		deck.append(i % Shape.size())
	# Перемешивание своим генератором: сид задаёт раскладку.
	for i in range(deck.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var tmp := deck[i]
		deck[i] = deck[j]
		deck[j] = tmp
	kinds = deck
	for i in n:
		open.append(false)
		matched.append(false)
		flip.append(0.0)
		_bot_memory.append(-1)
	cursor = Vector2i(cols / 2, ROWS / 2)
	queue_redraw()


func _index(c: Vector2i) -> int:
	return c.y * cols + c.x


func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	if event.is_action_pressed(GameInput.LEFT):
		_move(Vector2i(-1, 0))
	elif event.is_action_pressed(GameInput.RIGHT):
		_move(Vector2i(1, 0))
	elif event.is_action_pressed(GameInput.UP):
		_move(Vector2i(0, -1))
	elif event.is_action_pressed(GameInput.DOWN):
		_move(Vector2i(0, 1))
	elif GameInput.is_a(event):
		_open(_index(cursor))
	else:
		return
	get_viewport().set_input_as_handled()


func _move(d: Vector2i) -> void:
	cursor = Vector2i(wrapi(cursor.x + d.x, 0, cols), wrapi(cursor.y + d.y, 0, ROWS))
	queue_redraw()


func _open(i: int) -> void:
	if open[i] or matched[i] or second >= 0:
		return
	open[i] = true
	flip[i] = FLIP_SECONDS
	_flip_sound.play()
	if first < 0:
		first = i
		return
	second = i
	if kinds[first] == kinds[second]:
		matched[first] = true
		matched[second] = true
		pairs_done += 1
		_match_sound.play()
		first = -1
		second = -1
		if pairs_done * 2 >= kinds.size():
			finish(true)
	else:
		close_timer = close_seconds


func _on_tick(delta: float) -> void:
	for i in flip.size():
		flip[i] = maxf(flip[i] - delta, 0.0)
	if second >= 0:
		close_timer -= delta
		if close_timer <= 0.0:
			open[first] = false
			open[second] = false
			flip[first] = FLIP_SECONDS
			flip[second] = FLIP_SECONDS
			_miss_sound.play()
			first = -1
			second = -1
	queue_redraw()


func _on_timeout() -> bool:
	return pairs_done * 2 >= kinds.size()


## Бот: WIN помнит всё увиденное и открывает известную пару, иначе разведывает; LOSE раз в
## секунду открывает карточки так, чтобы пара не сложилась.
func _bot_step(delta: float) -> bool:
	_bot_timer += delta
	var step := BOT_STEP if AutoTest.bot_mode == AutoTest.BotMode.WIN else 1.0
	if _bot_timer < step or second >= 0:
		return false
	_bot_timer = 0.0
	var target := -1
	if AutoTest.bot_mode == AutoTest.BotMode.WIN:
		for i in kinds.size():
			if open[i]:
				_bot_memory[i] = kinds[i]
		if first >= 0:
			for i in kinds.size():
				if i != first and not matched[i] and _bot_memory[i] == kinds[first]:
					target = i
			if target < 0:
				target = _unknown()
		else:
			# Известная пара среди запомненных?
			for i in kinds.size():
				if matched[i] or _bot_memory[i] < 0:
					continue
				for j in range(i + 1, kinds.size()):
					if not matched[j] and _bot_memory[j] == _bot_memory[i]:
						target = i
						break
				if target >= 0:
					break
			if target < 0:
				target = _unknown()
	else:
		# LOSE: вторую карточку всегда другого вида, пары не складываются.
		var options: Array[int] = []
		for i in kinds.size():
			if not open[i] and not matched[i] and (first < 0 or kinds[i] != kinds[first]):
				options.append(i)
		if not options.is_empty():
			target = options[rng.randi_range(0, options.size() - 1)]
	if target >= 0:
		cursor = Vector2i(target % cols, target / cols)
		_open(target)
	return false


func _unknown() -> int:
	for i in kinds.size():
		if not open[i] and not matched[i] and _bot_memory[i] < 0:
			return i
	for i in kinds.size():
		if not open[i] and not matched[i]:
			return i
	return -1


# --- Рисование ----------------------------------------------------------------------------

func _origin() -> Vector2:
	var grid := Vector2(cols * CARD + (cols - 1) * GAP, ROWS * CARD + (ROWS - 1) * GAP)
	return (size - grid) / 2.0 + Vector2(0, -8)


func _draw() -> void:
	if def == null or kinds.is_empty():
		return
	var o := _origin()
	for i in kinds.size():
		var c := Vector2i(i % cols, i / cols)
		var pos := o + Vector2(c) * (CARD + GAP)
		var shown := open[i] or matched[i]
		# Переворот: карточка сжимается по ширине к середине и обратно.
		var k := flip[i] / FLIP_SECONDS
		var w := CARD * absf(1.0 - 2.0 * k) if k > 0.0 else CARD
		var rect := Rect2(pos + Vector2((CARD - w) / 2.0, 0), Vector2(w, CARD))
		var bg := Style.SURFACE_SOLID if shown else Style.accent(0)
		if matched[i]:
			bg = Color(Style.SUCCESS, 0.18)
		Style.flat(bg, Style.R_CTL, Color.TRANSPARENT, 0).draw(get_canvas_item(), rect)
		if shown and k < 0.5:
			_draw_shape(kinds[i], rect.get_center(), CARD * 0.28, Style.accent(1 + kinds[i] % 3) if not matched[i] else Style.SUCCESS)
		elif not shown:
			# Рубашка: точка по центру.
			draw_circle(rect.get_center(), 8.0, Color(1, 1, 1, 0.5))
		if c == cursor:
			Style.focus_ring(Style.R_CTL).draw(get_canvas_item(), Rect2(pos, Vector2(CARD, CARD)))
	# Пары справа сверху.
	var total := kinds.size() / 2
	var r := 7.0
	var gap := 24.0
	var x0 := size.x - 48.0 - (total - 1) * gap
	for j in total:
		draw_circle(Vector2(x0 + j * gap, 60.0), r, Style.SUCCESS if j < pairs_done else Style.SURFACE_2)


func _draw_shape(kind: int, c: Vector2, r: float, color: Color) -> void:
	match kind:
		Shape.CIRCLE:
			draw_circle(c, r, color)
		Shape.SQUARE:
			draw_rect(Rect2(c - Vector2(r, r) * 0.9, Vector2(r, r) * 1.8), color)
		Shape.TRIANGLE:
			draw_colored_polygon(_poly(c, r * 1.1, 3), color)
		Shape.DIAMOND:
			draw_colored_polygon(PackedVector2Array([c + Vector2(0, -r), c + Vector2(r * 0.75, 0), c + Vector2(0, r), c + Vector2(-r * 0.75, 0)]), color)
		Shape.RING:
			draw_arc(c, r * 0.85, 0.0, TAU, 48, color, r * 0.4, true)
		Shape.CROSS:
			draw_line(c + Vector2(-r, -r) * 0.8, c + Vector2(r, r) * 0.8, color, r * 0.4, true)
			draw_line(c + Vector2(-r, r) * 0.8, c + Vector2(r, -r) * 0.8, color, r * 0.4, true)
		Shape.STAR:
			var pts := PackedVector2Array()
			for i in 10:
				var a := -PI / 2.0 + TAU * i / 10.0
				var rr := r if i % 2 == 0 else r * 0.45
				pts.append(c + Vector2(cos(a), sin(a)) * rr)
			draw_colored_polygon(pts, color)
		Shape.HEX:
			draw_colored_polygon(_poly(c, r, 6), color)


func _poly(c: Vector2, r: float, sides: int) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in sides:
		var a := -PI / 2.0 + TAU * i / sides
		pts.append(c + Vector2(cos(a), sin(a)) * r)
	return pts
