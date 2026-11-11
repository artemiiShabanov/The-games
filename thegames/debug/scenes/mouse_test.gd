extends Control
## Мышь в мини-играх (#83) без живой мыши: синтетические события мыши через
## `Input.parse_input_event`, бот выключен. На каждую игру клик, колесо или ведение в нужную
## точку поля и проверка, что сработало то же, что от клавиши (`Minigame.mouse_last_action`)
## или прямое действие (курсор, цвет, частота, наводка луча). Плюс фокус паузы наведением и
## живая пилюля ввода. Запуск: `sh tools/autotest.sh --scene=mouse_test --frames=1500`.

var game: Minigame


func _ready() -> void:
	AutoTest.bot_mode = AutoTest.BotMode.OFF
	AutoTest.require("mouse_test")
	AutoTest.note("mouse_test: растяжка окна %s" % get_tree().root.get_final_transform())
	_run.call_deferred()


func _run() -> void:
	await _generic()
	await _decide_cards()
	await _inverted()
	await _fit_frame()
	await _patch_line()
	await _in_time()
	await _repeat()
	await _mole()
	await _pairs()
	await _flood_fill()
	await _tune()
	await _beam()
	await _pause_hover()
	await _pill()
	_close()
	AutoTest.note("mouse_test: все игры")
	AutoTest.fulfill("mouse_test")


# --- Случаи -------------------------------------------------------------------------------

## Игры без своей мыши: левая кнопка = ␣ (держится, пока зажата), правая = Ctrl.
func _generic() -> void:
	for id: StringName in [&"runner", &"fishing", &"lights_out", &"rings", &"putt"]:
		await _open(id)
		await _button(Vector2(960, 540), MOUSE_BUTTON_LEFT, true)
		_check(game.mouse_last_action == GameInput.A, "%s: левая кнопка не A" % id)
		_check(Input.is_action_pressed(GameInput.A), "%s: A не держится кнопкой" % id)
		await _button(Vector2(960, 540), MOUSE_BUTTON_LEFT, false)
		_check(not Input.is_action_pressed(GameInput.A), "%s: A не отпущено" % id)
	await _open(&"runner")
	await _click(Vector2(960, 540))
	_check(not game.get("grounded"), "runner: клик не прыгает")
	await _open(&"fishing")
	await _button(Vector2(960, 540), MOUSE_BUTTON_LEFT, true)
	_check(game.call("_holding"), "fishing: кнопка не держит столбик")
	await _button(Vector2(960, 540), MOUSE_BUTTON_LEFT, false)
	_check(not game.call("_holding"), "fishing: столбик держится после отпускания")


func _decide_cards() -> void:
	await _open(&"decide_cards")
	await _until(func() -> bool: return game.call("_active") != null)
	await _click(Vector2(960, 200))
	_check(game.mouse_last_action == GameInput.UP and int(game.get("decided")) == 1, "decide_cards: клик выше не принял")
	await _until(func() -> bool: return game.call("_active") != null)
	await _click(Vector2(960, 900), MOUSE_BUTTON_RIGHT)
	_check(game.mouse_last_action == GameInput.DOWN and int(game.get("decided")) == 2, "decide_cards: правая не отклонила")


func _inverted() -> void:
	await _open(&"inverted")
	var cell: Vector2i = game.get("cell")
	var dirs: Array[Vector2i] = [Vector2i(0, -1), Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0)]
	var d := 0
	while game.call("_has_wall", cell, d):
		d += 1
	game.call("_layout")
	var dot: Vector2 = game.get("_dot_screen")
	await _click(dot + Vector2(dirs[d]) * 200.0)
	_check(game.get("cell") == cell + dirs[d], "inverted: клик со стороны не сдвинул точку")


func _fit_frame() -> void:
	await _open(&"fit_frame")
	var sides := int(game.get("stencil_sides"))
	await _wheel(Vector2(960, 540), sides < 8)
	_check(int(game.get("stencil_sides")) == sides + (1 if sides < 8 else -1), "fit_frame: колесо не меняет стороны")
	await _click(Vector2(300, 540))
	_check(game.mouse_last_action == GameInput.LEFT, "fit_frame: клик слева не влево")
	await _click(Vector2(1600, 540))
	_check(game.mouse_last_action == GameInput.RIGHT, "fit_frame: клик справа не вправо")


func _patch_line() -> void:
	await _open(&"patch_line")
	var mid: float = game.call("_lane_mid")
	await _click(Vector2(960, mid - 150.0))
	_check(game.mouse_last_action == GameInput.UP, "patch_line: клик выше не ↑")
	await _click(Vector2(960, mid + 150.0))
	_check(game.mouse_last_action == GameInput.DOWN, "patch_line: клик ниже не ↓")
	await _wheel(Vector2(960, 540), true)
	_check(game.mouse_last_action == GameInput.UP, "patch_line: колесо вверх не ↑")


func _in_time() -> void:
	await _open(&"in_time")
	var actions: Array[StringName] = [GameInput.LEFT, GameInput.DOWN, GameInput.RIGHT]
	for lane in 3:
		var at := Vector2(float(game.call("_lane_x", lane)), 600.0)
		await _button(at, MOUSE_BUTTON_LEFT, true)
		var action := actions[lane]
		_check(game.mouse_last_action == action and Input.is_action_pressed(action), "in_time: дорожка %d не жмётся" % lane)
		await _button(at, MOUSE_BUTTON_LEFT, false)
		_check(not Input.is_action_pressed(action), "in_time: дорожка %d не отпущена" % lane)


func _repeat() -> void:
	# Неверные клавиши копят ошибки, поэтому каждая клавиша на свежей игре.
	var keys: Array[StringName] = [GameInput.LEFT, GameInput.UP, GameInput.DOWN, GameInput.RIGHT, GameInput.A, GameInput.B]
	for i in keys.size():
		await _open(&"repeat")
		await _click(game.call("_pad_center", i))
		_check(game.mouse_last_action == keys[i], "repeat: клик по клавише %s" % keys[i])
	game.mouse_last_action = &""
	await _click(Vector2(60, 1000))
	_check(game.mouse_last_action == &"", "repeat: клик мимо клавиш что-то нажал")


func _mole() -> void:
	await _open(&"mole")
	var c: Vector2 = game.call("_center")
	for pair: Array in [[Vector2(0, -200), GameInput.UP], [Vector2(220, 0), GameInput.RIGHT],
			[Vector2(0, 200), GameInput.DOWN], [Vector2(-220, 30), GameInput.LEFT]]:
		await _click(c + (pair[0] as Vector2))
		_check(game.mouse_last_action == pair[1], "mole: клик по лунке %s" % pair[1])
		await _frames(25)


func _pairs() -> void:
	await _open(&"pairs")
	var cols := int(game.get("cols"))
	await _move(game.call("_card_home", 5))
	_check(game.get("cursor") == Vector2i(5 % cols, 5 / cols), "pairs: наведение не двигает курсор")
	await _click(game.call("_card_home", 2))
	var open: Array[bool] = game.get("open")
	_check(open[2] and game.get("cursor") == Vector2i(2 % cols, 2 / cols), "pairs: клик не открыл карточку")


func _flood_fill() -> void:
	await _open(&"flood_fill")
	await _frames(30)
	await _move(game.call("_swatch_center", 1))
	_check(int(game.get("sel")) == 1, "flood_fill: наведение не выбирает цвет")
	await _click(game.call("_swatch_center", 2))
	_check(int(game.get("sel")) == 2 and int(game.get("used")) == 1, "flood_fill: клик по цвету не залил")
	# Клетка не цвета угла: её заливка это ход.
	var shown: PackedInt32Array = game.get("shown")
	var n := int(game.get("n"))
	var step := 560.0 / n
	var last := n * n - 1
	while last > 0 and shown[last] == shown[0]:
		last -= 1
	var at := Vector2((1920 - 560) / 2.0, (1080 - 560) / 2.0 - 40.0) + Vector2(last % n + 0.5, last / n + 0.5) * step
	await _click(at)
	_check(int(game.get("sel")) == shown[last] and int(game.get("used")) == 2, "flood_fill: клик по клетке не залил её цветом")


func _tune() -> void:
	await _open(&"tune")
	var f := float(game.get("freq"))
	var a := float(game.get("amp"))
	var from := Vector2(960, 540)
	await _button(from, MOUSE_BUTTON_LEFT, true)
	for i in 4:
		await _move(from + Vector2(20.0 * (i + 1), -13.0 * (i + 1)), Vector2(20, -13))
	await _button(from + Vector2(80, -52), MOUSE_BUTTON_LEFT, false)
	_check(float(game.get("freq")) > f, "tune: ведение вправо не подняло частоту")
	_check(float(game.get("amp")) > a, "tune: ведение вверх не подняло амплитуду")
	_check(game.mouse_last_action != GameInput.A, "tune: ведение зафиксировало волну")
	await _click(from)
	_check(game.mouse_last_action == GameInput.A, "tune: клик не фиксирует")


func _beam() -> void:
	await _open(&"beam")
	var angle := float(game.get("emitter_angle"))
	var turn := 0.8 if angle < 0.0 else -0.8
	var aim := Vector2(200, 550) + Vector2.from_angle(angle + turn) * 250.0
	await _button(aim, MOUSE_BUTTON_LEFT, true)
	await _frames(20)
	await _button(aim, MOUSE_BUTTON_LEFT, false)
	_check(absf(float(game.get("emitter_angle")) - angle) > 0.2, "beam: зажатая кнопка не ведёт луч к курсору")
	await _click(Vector2(960, 540), MOUSE_BUTTON_RIGHT)
	_check(game.mouse_last_action == GameInput.B and is_equal_approx(float(game.get("emitter_angle")), float(game.get("start_emitter"))), "beam: правая не вернула к началу")


## Наведение на кнопку паузы переносит фокус.
func _pause_hover() -> void:
	await _open(&"runner")
	game.pause()
	await _frames(2)
	var menu: Control = game.get("_menu_button")
	var resume: Control = game.get("_resume_button")
	await _move(MouseUi.rect_of(menu).get_center())
	_check(int(game.get("_pause_focus")) == 1, "пауза: наведение на «В меню» не переносит фокус")
	await _move(MouseUi.rect_of(resume).get_center())
	_check(int(game.get("_pause_focus")) == 0, "пауза: наведение на «Продолжить» не переносит фокус")
	await _click(MouseUi.rect_of(resume).get_center())
	_check(not game.paused, "пауза: клик по «Продолжить» не продолжил")


## Пилюля ввода: после клика мыши показывает подсказку мыши, после клавиши снова клавиши.
func _pill() -> void:
	await _open(&"runner")
	await _click(Vector2(960, 540))
	await _frames(2)
	_check(GameInput.mouse, "пилюля: клик не включил мышь")
	var pill := _find_pill(game)
	_check(pill != null and pill.label().text == game.def.mouse_hint, "пилюля: нет подсказки мыши")
	var key := InputEventKey.new()
	key.keycode = KEY_SHIFT
	key.pressed = true
	Input.parse_input_event(key)
	await _frames(2)
	key = key.duplicate() as InputEventKey
	key.pressed = false
	Input.parse_input_event(key)
	await _frames(2)
	_check(not GameInput.mouse and pill.label().text == GameInput.key(GameInput.A), "пилюля: клавиша не вернула подсказку клавиш")


# --- Помощники ----------------------------------------------------------------------------

func _open(id: StringName) -> void:
	_close()
	var def := MinigamePool.find(MinigamePool.load_all(), id)
	game = def.scene.instantiate() as Minigame
	game.setup(def, 0.0, 3)
	add_child(game)
	game.start()
	await _frames(3)


func _close() -> void:
	if game != null:
		game.queue_free()
		remove_child(game)
		game = null


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _until(cond: Callable, limit := 300) -> void:
	for i in limit:
		if cond.call():
			return
		await get_tree().process_frame
	AutoTest.fail("mouse_test: не дождались условия")


func _button(pos: Vector2, button: MouseButton, pressed: bool) -> void:
	var e := InputEventMouseButton.new()
	e.button_index = button
	e.pressed = pressed
	e.position = _to_window(pos)
	e.global_position = e.position
	if pressed:
		e.button_mask = MouseButtonMask.MOUSE_BUTTON_MASK_LEFT if button == MOUSE_BUTTON_LEFT else MouseButtonMask.MOUSE_BUTTON_MASK_RIGHT
	Input.parse_input_event(e)
	await _frames(2)


func _click(pos: Vector2, button := MOUSE_BUTTON_LEFT) -> void:
	await _button(pos, button, true)
	await _button(pos, button, false)


func _wheel(pos: Vector2, up: bool) -> void:
	await _button(pos, MOUSE_BUTTON_WHEEL_UP if up else MOUSE_BUTTON_WHEEL_DOWN, true)
	await _button(pos, MOUSE_BUTTON_WHEEL_UP if up else MOUSE_BUTTON_WHEEL_DOWN, false)


func _move(pos: Vector2, relative := Vector2.ZERO) -> void:
	var e := InputEventMouseMotion.new()
	e.position = _to_window(pos)
	e.global_position = e.position
	e.relative = get_tree().root.get_final_transform().basis_xform(relative)
	if Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		e.button_mask = MouseButtonMask.MOUSE_BUTTON_MASK_LEFT
	Input.parse_input_event(e)
	await _frames(2)


## События идут в окно: точку поля (1920×1080) переводим растяжкой окна, без окна она другая.
func _to_window(pos: Vector2) -> Vector2:
	return get_tree().root.get_final_transform() * pos


func _check(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("mouse_test: " + what)


func _find_pill(node: Node) -> HintPill:
	for child in node.get_children():
		if child is HintPill:
			return child as HintPill
		var found := _find_pill(child)
		if found != null:
			return found
	return null
