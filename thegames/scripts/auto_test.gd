extends Node
## Автотест. Запуск:
##   Godot --path thegames -- --auto-test [--frames=N] [--screenshot=debug/playtest/x.png] [--time-scale=4]
## Прогоняет N кадров с ботом (`bot_mode = WIN`), пишет скриншот, печатает `END ok`
## или `END fail: причины` и выходит с кодом 0 или 1. Относительный путь скриншота
## считается от корня проекта (`res://`). Обёртка с проверкой вывода: `tools/autotest.sh`.
## Не зависит от дебаг-меню: меню только переключает `bot_mode` отсюда.
## Ввод по кадрам (#82): `--input=30:move=960x900,40:click=960x900,60:wheel=3@300x500,
## 70:pan=-2@300x500,80:key=space` подаёт движение мыши, клик, колесо (знак: вниз +),
## жест тачпада и клавишу (space, esc, up, down, left, right, r, ctrl) в корневой вьюпорт в
## координатах экрана 1920×1080, как от игрока. Обычно с `--bot=off`.

## Бот вместо игрока. Системы читают при принятии решений: WIN проходит мини-игры,
## LOSE проваливает, OFF играет человек.
enum BotMode { OFF, WIN, LOSE }

const DEFAULT_FRAMES := 120

var enabled := false
var bot_mode := BotMode.OFF
var frames_left := 0
var screenshot_path := ""
var failures: PackedStringArray = []
var _required: PackedStringArray = []
var _inputs: Dictionary[int, PackedStringArray] = {}
var _frame := 0


func _ready() -> void:
	# Считает кадры и при паузе дерева (открытое дебаг-меню), иначе прогон не закончится.
	process_mode = Node.PROCESS_MODE_ALWAYS
	var args := parse_args(OS.get_cmdline_user_args())
	enabled = args.has("auto-test")
	if not enabled:
		set_process(false)
		return
	bot_mode = BotMode.WIN
	# `--bot=off|lose`: без бота (ввод из `--input`) или проигрывающий бот.
	match str(args.get("bot", "win")):
		"off":
			bot_mode = BotMode.OFF
		"lose":
			bot_mode = BotMode.LOSE
	# Прогоны молчат: звук в автотесте только мешает за соседним столом.
	AudioServer.set_bus_mute(0, true)
	frames_left = int(args.get("frames", str(DEFAULT_FRAMES)))
	screenshot_path = str(args.get("screenshot", ""))
	# `--time-scale=4`: игровое время быстрее, чтобы длинные прогоны ботом укладывались в кадры.
	Engine.time_scale = float(args.get("time-scale", "1"))
	for part in str(args.get("input", "")).split(",", false):
		var at := part.find(":")
		if at > 0:
			var f := int(part.substr(0, at))
			if not _inputs.has(f):
				_inputs[f] = PackedStringArray()
			_inputs[f].append(part.substr(at + 1))
	print("AUTO-TEST start: frames=%d screenshot=%s" % [frames_left, screenshot_path])


func bot_active() -> bool:
	return bot_mode != BotMode.OFF


## Любая система может записать провал; автотест тогда закончится `END fail`.
func fail(reason: String) -> void:
	failures.append(reason)
	push_error("AUTO-TEST fail: " + reason)


## Объявить обязательную отметку: если к концу прогона её не сняли `fulfill`, это провал.
## Так незавершившиеся проверки не проходят молча.
func require(tag: String) -> void:
	if not _required.has(tag):
		_required.append(tag)


func fulfill(tag: String) -> void:
	var i := _required.find(tag)
	if i >= 0:
		_required.remove_at(i)


## Заметка в лог прогона, для чтения глазами.
func note(text: String) -> void:
	print("AUTO-TEST note: " + text)


func _process(_delta: float) -> void:
	_frame += 1
	if _inputs.has(_frame):
		for what in _inputs[_frame]:
			_inject(what)
	frames_left -= 1
	if frames_left > 0:
		return
	set_process(false)
	_finish()


func _finish() -> void:
	print("AUTO-TEST finishing")
	var headless := DisplayServer.get_name() == "headless"
	# Не ждём frame_post_draw: под нагрузкой он иногда не приходит и прогон висит. Два кадра
	# процесса дают отрисованный кадр для скриншота.
	await get_tree().process_frame
	await get_tree().process_frame
	for tag in _required:
		failures.append("не дождались: " + tag)
	if screenshot_path != "" and not headless:
		var err := Screenshot.save(get_viewport(), screenshot_path)
		if err != OK:
			fail("screenshot: " + error_string(err))
		else:
			print("AUTO-TEST screenshot: " + Screenshot.absolute(screenshot_path))
	if failures.is_empty():
		print("END ok")
	else:
		print("END fail: " + "; ".join(failures))
	get_tree().quit(0 if failures.is_empty() else 1)


func _inject(what: String) -> void:
	var kv := what.split("=", true, 1)
	var kind := kv[0]
	var arg := kv[1] if kv.size() > 1 else ""
	var amount := 1.0
	if arg.contains("@"):
		amount = float(arg.get_slice("@", 0))
		arg = arg.get_slice("@", 1)
	var pos := Vector2(float(arg.get_slice("x", 0)), float(arg.get_slice("x", 1))) if arg.contains("x") else Vector2.ZERO
	var vp := get_tree().root
	match kind:
		"move":
			var m := InputEventMouseMotion.new()
			m.position = pos
			m.global_position = pos
			vp.push_input(m, true)
		"click":
			for pressed in [true, false]:
				var b := InputEventMouseButton.new()
				b.button_index = MOUSE_BUTTON_LEFT
				b.pressed = pressed
				b.position = pos
				b.global_position = pos
				vp.push_input(b, true)
		"wheel":
			for i in absi(int(amount)):
				var w := InputEventMouseButton.new()
				w.button_index = MOUSE_BUTTON_WHEEL_DOWN if amount > 0 else MOUSE_BUTTON_WHEEL_UP
				w.pressed = true
				w.factor = 1.0
				w.position = pos
				w.global_position = pos
				vp.push_input(w, true)
		"pan":
			var g := InputEventPanGesture.new()
			g.delta = Vector2(0, amount)
			g.position = pos
			vp.push_input(g, true)
		"key":
			var codes := {"space": KEY_SPACE, "esc": KEY_ESCAPE, "up": KEY_UP, "down": KEY_DOWN, "left": KEY_LEFT,
					"right": KEY_RIGHT, "r": KEY_R, "ctrl": KEY_CTRL, "enter": KEY_ENTER}
			for pressed in [true, false]:
				var k := InputEventKey.new()
				k.keycode = codes.get(arg, KEY_SPACE)
				k.physical_keycode = k.keycode
				k.pressed = pressed
				Input.parse_input_event(k)
	var hov := vp.gui_get_hovered_control()
	note("input %d: %s%s" % [_frame, what, (" · под курсором %s" % hov.get_path()) if hov != null else ""])


## `--auto-test --frames=90` -> {"auto-test": "", "frames": "90"}.
static func parse_args(list: PackedStringArray) -> Dictionary:
	var out := {}
	for raw in list:
		var arg := raw.trim_prefix("--")
		var eq := arg.find("=")
		if eq < 0:
			out[arg] = ""
		else:
			out[arg.substr(0, eq)] = arg.substr(eq + 1)
	return out
