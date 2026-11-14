extends Minigame
## «Запомни» (pairs, технология 8-bit), каталог `docs/specs/minigames_catalog.md`. Сетка 3×4
## закрытых карточек с пиктограммами, курсор стрелками, A открывает; две одинаковые остаются
## открытыми, разные закрываются через паузу. Собрать все пары до таймера, иначе провал. С `t`
## сетка 4×4 и карточки закрываются быстрее. Параметры в `resources/minigames/pairs.tres`:
## cols (3 или 4 при четырёх рядах), close (секунды до закрытия непарных).
## Мармелад (STYLE «Мармелад»): карточки мягкими телами `JellyShape`, курсор показан толщиной
## (карточка на бортике темнее себя, подъём пружинит) вместо синей рамки, переворот сжимает
## карточку по ширине и она садится вздрогом, пара вздрагивает обеими и брызгает мягкими каплями
## цвета своей фигуры (`SplashFx.pop`), непарные трясутся вбок. Поле стоит на белой карточке
## спринта, поэтому карточки серые (STYLE: «внутри белой карточки карточки серые»): закрытые
## темнее, открытые светлее, собранные с зелёным оттенком; бортик от своей заливки.

enum Shape { CIRCLE, SQUARE, TRIANGLE, DIAMOND, RING, CROSS, STAR, HEX }

const ROWS := 4
const CARD := 128.0
const GAP := 16.0
const FLIP_SECONDS := 0.16
const BOT_STEP := 0.3
## Заливки карточек: закрытая (рубашка) тёплый серый темнее `surface-2`, открытая `surface-2`,
## собранная `surface-2` с оттенком успеха. Все читаются на белой карточке спринта.
const HIDDEN_COLOR := Color("#DFDAD1")
const OPEN_COLOR := Style.SURFACE_2
const MATCHED_COLOR := Color("#C9DFCF")
## Брызги пары: капель с карточки (до масштаба тюнинга), скорость, жизнь, приглушение к серому.
const POP_COUNT := 7
const POP_SPEED := 300.0
const POP_LIFE := 0.5
const POP_MUTE := 0.3

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

# Мармелад: только вид, геймплей о нём не знает. Состояние игры сверяется в `_process`.
var _cards: Array[JellyShape] = []
var _lift: Array[JellySpring] = []
var _press_left: Array[float] = []
var _prev_flip: Array[float] = []
var _prev_matched: Array[bool] = []
var _match_wait: Array[int] = []
var _shaken := -1
var _rest_reach := 1.0
var _fx := SplashFx.new()


func _on_start() -> void:
	cols = clampi(int(round(def.param(&"cols", t, 3.0))), 2, 5)
	close_seconds = def.param(&"close", t, 1.0)
	_flip_sound = MiniSfx.tap(760.0, -3.0)
	_match_sound = MiniSfx.hit(494.0)
	_miss_sound = MiniSfx.miss(220.0, -3.0)
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
	_setup_jelly()
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


## Мышь (#83): наведение ставит курсор на карточку, клик открывает её.
func _on_mouse(event: InputEventMouse) -> bool:
	if event is InputEventMouseMotion:
		var i := _card_at(event.position)
		if i >= 0 and _index(cursor) != i:
			cursor = Vector2i(i % cols, i / cols)
			queue_redraw()
	return false


func _mouse_action(button: MouseButton, pos: Vector2) -> StringName:
	var i := _card_at(pos)
	if button != MOUSE_BUTTON_LEFT or i < 0:
		return &""
	cursor = Vector2i(i % cols, i / cols)
	return GameInput.A


## Карточка под точкой поля или −1.
func _card_at(pos: Vector2) -> int:
	for i in cols * ROWS:
		var d := (pos - _card_home(i)).abs()
		if d.x <= CARD / 2.0 and d.y <= CARD / 2.0:
			return i
	return -1


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


func _card_home(i: int) -> Vector2:
	return _origin() + Vector2(i % cols, i / cols) * (CARD + GAP) + Vector2(CARD, CARD) / 2.0


func _draw() -> void:
	if def == null or kinds.is_empty() or _cards.is_empty():
		return
	for i in kinds.size():
		var shown := open[i] or matched[i]
		# Переворот: карточка сжимается по ширине к середине и обратно.
		var k := flip[i] / FLIP_SECONDS
		var w := absf(1.0 - 2.0 * k) if k > 0.0 else 1.0
		var bg := OPEN_COLOR if shown else HIDDEN_COLOR
		if matched[i]:
			bg = MATCHED_COLOR
		var center := _card_center(i)
		var lift := _lift[i].value
		if CARD * w >= 2.0:
			if lift > 0.2:
				Jelly.fill(self, _card_contour(i, center, w, lift), Jelly.lip_color(bg))
			Jelly.fill(self, _card_contour(i, center, w, 0.0), bg)
		# Лицо и рубашка идут за телом: центр, вздрог и сжатие переворота.
		var grow := _card_reach(i, center) / _rest_reach
		draw_set_transform(center, 0.0, Vector2(w, 1.0) * grow)
		if shown and k < 0.5:
			_draw_shape(kinds[i], Vector2.ZERO, CARD * 0.28, _kind_color(kinds[i]) if not matched[i] else Style.SUCCESS)
		elif not shown:
			# Рубашка: точка по центру.
			draw_circle(Vector2.ZERO, 8.0, Style.INK_3)
		draw_set_transform(Vector2.ZERO)
	# Брызги пары поверх карточек.
	_fx.draw_air(self, Vector2.ZERO)
	# Пары справа сверху.
	var total := kinds.size() / 2
	var r := 7.0
	var gap := 24.0
	var x0 := size.x - 48.0 - (total - 1) * gap
	for j in total:
		draw_circle(Vector2(x0 + j * gap, 60.0), r, Style.SUCCESS if j < pairs_done else Style.SURFACE_2)


func _kind_color(kind: int) -> Color:
	return Style.accent(1 + kind % 3)


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


# --- Мармелад ------------------------------------------------------------------------------

func _setup_jelly() -> void:
	for i in kinds.size():
		var card := JellyShape.rect(Vector2(CARD, CARD), Style.R_CTL)
		_cards.append(card)
		_lift.append(JellySpring.new())
		_press_left.append(0.0)
		_prev_flip.append(0.0)
		_prev_matched.append(false)
		_place(i)
	_rest_reach = maxf(_card_reach(0, _card_center(0)), 1.0)


## Тело в покое оседает на свою посадку и тяжесть (`_sag`); рисуется поднятым на неё же,
## поэтому ставится сразу осевшим: иначе на старте все карточки качнутся вниз.
func _place(i: int) -> void:
	var card := _cards[i]
	card.snap(_card_home(i))
	var sag := Vector2(0.0, _sag())
	var pts := card.blob.points
	for p in pts.size():
		pts[p] += sag
	card.blob.points = pts


func _sag() -> float:
	var tu := Jelly.tuning()
	return tu.blob_sit * CARD / 2.0 + tu.blob_gravity / maxf(tu.blob_stiffness, 1.0)


## Видимый центр карточки: среднее точек тела (толчок вбок сдвигает их, а не ведущий центр).
func _card_center(i: int) -> Vector2:
	var pts := _cards[i].blob.points
	if pts.is_empty():
		return _card_home(i)
	var c := Vector2.ZERO
	for p in pts:
		c += p
	return c / pts.size() - Vector2(0.0, _sag())


## Средний радиус тела: насколько вздрог раздул или сжал карточку.
func _card_reach(i: int, center: Vector2) -> float:
	var pts := _cards[i].blob.points
	if pts.is_empty():
		return _rest_reach
	var sum := 0.0
	var lifted := center + Vector2(0.0, _sag())
	for p in pts:
		sum += p.distance_to(lifted)
	return sum / pts.size()


## Контур карточки, сжатый по ширине `w` к видимому центру и сдвинутый вниз на `drop` (бортик).
func _card_contour(i: int, center: Vector2, w: float, drop: float) -> PackedVector2Array:
	var poly := _cards[i].contour(Vector2(0.0, drop - _sag()))
	if w < 1.0:
		for p in poly.size():
			poly[p] = Vector2(center.x + (poly[p].x - center.x) * w, poly[p].y)
	return poly


## Мармелад живёт и после финиша, пока сцена на экране; на паузе стоит. Состояние игры только
## читается: начатый переворот, новая пара, вскрытая непарная.
func _process(delta: float) -> void:
	super(delta)
	if _cards.is_empty() or paused:
		return
	var tu := Jelly.tuning()
	var moving := Jelly.on()
	var cur := _index(cursor)
	_fx.step(delta, Callable())
	for i in _cards.size():
		if flip[i] > _prev_flip[i] + 0.0001 and open[i]:
			# Открыли: карточка вдавливается в бортик, как кнопка.
			_press_left[i] = 0.12
		if _prev_flip[i] > 0.0 and flip[i] <= 0.0 and moving:
			# Переворот закончился: карточка садится лёгким вздрогом.
			_cards[i].poke(110.0)
		_prev_flip[i] = flip[i]
		if matched[i] and not _prev_matched[i]:
			_match_wait.append(i)
		_prev_matched[i] = matched[i]
		_step_lift(i, i == cur, delta, tu, moving)
	# Пара вздрагивает обеими, когда вторая перевернулась.
	if not _match_wait.is_empty():
		var landed := true
		for i in _match_wait:
			landed = landed and flip[i] <= 0.0
		if landed:
			if moving:
				for i in _match_wait:
					_cards[i].poke(280.0)
					# Мягкие брызги цвета фигуры, приглушённые к серому карточки.
					var col := _kind_color(kinds[i]).lerp(OPEN_COLOR, POP_MUTE)
					_fx.pop(_card_center(i) + Vector2(0.0, -CARD * 0.25), col, POP_COUNT, POP_SPEED, POP_LIFE)
			_match_wait.clear()
	# Непарные трясутся вбок в разные стороны, как только вторая открылась.
	if second < 0:
		_shaken = -1
	elif _shaken != second and flip[second] <= 0.0:
		_shaken = second
		if moving:
			_cards[first].push(Vector2(-240.0, 0.0))
			_cards[second].push(Vector2(240.0, 0.0))
	for i in _cards.size():
		var home := _card_home(i)
		if not moving or _cards[i].blob.center.distance_to(home) > CARD / 2.0:
			_place(i)
		else:
			_cards[i].follow(delta, home)
	queue_redraw()


## Подъём курсора как у `JellyLift`: вверх с лёгким перелётом, вниз без него, в фокусе дышит.
func _step_lift(i: int, focused: bool, delta: float, tu: JellyTuning, moving: bool) -> void:
	var target := 0.0
	if focused:
		target = tu.lift_px
		if moving:
			target += sin(Time.get_ticks_msec() / 1000.0 * 2.2 + i) * tu.lift_breathe
	if _press_left[i] > 0.0:
		target = minf(target, tu.lift_press)
		_press_left[i] -= delta
	var spring := _lift[i]
	if moving:
		var k := tu.ui_stiffness * 1.6
		var damping := tu.ui_damping * 1.1 if target > spring.value else 2.0 * sqrt(k)
		spring.step(delta, k, damping, target)
	else:
		spring.value = target
		spring.velocity = 0.0
	if target <= 0.0 and spring.value < 0.2:
		spring.value = 0.0
		spring.velocity = 0.0
