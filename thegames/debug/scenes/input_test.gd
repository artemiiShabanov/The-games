extends Control
## Тестовая сцена ввода: шесть действий подсвечиваются при нажатии, внизу последнее сырое
## событие. Под ботом (автотест) проверяет, что карта ввода совпадает со спекой, и
## `AutoTest.fail`, если нет. Запуск: F1 → Сцены → input test, или `--scene=input_test`.

## Что обязано быть в карте: действие → сколько событий минимум и какие клавиши.
const EXPECTED := {
	GameInput.LEFT: [KEY_LEFT, KEY_A],
	GameInput.RIGHT: [KEY_RIGHT, KEY_D],
	GameInput.UP: [KEY_UP, KEY_W],
	GameInput.DOWN: [KEY_DOWN, KEY_S],
	GameInput.A: [KEY_Z, KEY_SPACE, KEY_ENTER, KEY_KP_ENTER],
	GameInput.B: [KEY_X, KEY_C, KEY_CTRL],
}
const BOX := Vector2(200, 200)
const GAP := 40.0

var _last_event := "—"
var _checked := false


func _ready() -> void:
	set_process(true)


func _input(event: InputEvent) -> void:
	if event is InputEventKey or event is InputEventJoypadButton or event is InputEventJoypadMotion:
		if not (event is InputEventJoypadMotion and absf((event as InputEventJoypadMotion).axis_value) < 0.2):
			_last_event = event.as_text()


func _process(_delta: float) -> void:
	queue_redraw()
	if AutoTest.enabled and not _checked:
		_checked = true
		_check_input_map()


func _draw() -> void:
	var font := ThemeDB.fallback_font
	var ink := Style.STUDIO_INK
	var accent := Style.FOCUS
	draw_rect(Rect2(Vector2.ZERO, size), Style.BG)
	draw_string(font, Vector2(48, 72), "Ввод: стрелки или WASD, A (Z, пробел, Enter), B (X, C, Ctrl) или геймпад",
			HORIZONTAL_ALIGNMENT_LEFT, -1, 32, ink)
	var total_w := GameInput.ALL.size() * BOX.x + (GameInput.ALL.size() - 1) * GAP
	var x := (size.x - total_w) / 2.0
	var y := (size.y - BOX.y) / 2.0
	for action in GameInput.ALL:
		var rect := Rect2(Vector2(x, y), BOX)
		var pressed := Input.is_action_pressed(action)
		draw_rect(rect, accent if pressed else Color(ink, 0.08))
		draw_rect(rect, ink, false, 4.0)
		var label: String = GameInput.key(action)
		draw_string(font, Vector2(x, y + BOX.y / 2.0 + 28), label, HORIZONTAL_ALIGNMENT_CENTER,
				BOX.x, 80, Style.BG if pressed else ink)
		draw_string(font, Vector2(x, y + BOX.y + 40), String(action), HORIZONTAL_ALIGNMENT_CENTER,
				BOX.x, 20, Color(ink, 0.6))
		x += BOX.x + GAP
	var a := GameInput.axis()
	draw_string(font, Vector2(48, size.y - 96), "axis = (%.2f, %.2f)" % [a.x, a.y],
			HORIZONTAL_ALIGNMENT_LEFT, -1, 24, ink)
	draw_string(font, Vector2(48, size.y - 56), "последнее событие: " + _last_event,
			HORIZONTAL_ALIGNMENT_LEFT, -1, 24, Color(ink, 0.7))


func _check_input_map() -> void:
	for action: StringName in EXPECTED:
		if not InputMap.has_action(action):
			AutoTest.fail("input: нет действия %s" % action)
			continue
		var keys: Array[int] = []
		var has_pad := false
		for ev in InputMap.action_get_events(action):
			if ev is InputEventKey:
				keys.append((ev as InputEventKey).physical_keycode)
			elif ev is InputEventJoypadButton or ev is InputEventJoypadMotion:
				has_pad = true
		for key: int in EXPECTED[action]:
			if not keys.has(key):
				AutoTest.fail("input: у %s нет клавиши %s" % [action, OS.get_keycode_string(key)])
		if not has_pad:
			AutoTest.fail("input: у %s нет геймпада" % action)
	# Хелпер читает те же действия, что и Input.
	Input.action_press(GameInput.A)
	if not GameInput.a_pressed():
		AutoTest.fail("input: GameInput.a_pressed не видит action_press")
	Input.action_release(GameInput.A)
	AutoTest.note("input map checked: %d actions" % EXPECTED.size())
