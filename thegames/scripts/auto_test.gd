extends Node
## Автотест. Запуск:
##   Godot --path thegames -- --auto-test [--frames=N] [--screenshot=debug/playtest/x.png] [--time-scale=4]
## Прогоняет N кадров с ботом (`bot_mode = WIN`), пишет скриншот, печатает `END ok`
## или `END fail: причины` и выходит с кодом 0 или 1. Относительный путь скриншота
## считается от корня проекта (`res://`). Обёртка с проверкой вывода: `tools/autotest.sh`.
## Не зависит от дебаг-меню: меню только переключает `bot_mode` отсюда.

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


func _ready() -> void:
	# Считает кадры и при паузе дерева (открытое дебаг-меню), иначе прогон не закончится.
	process_mode = Node.PROCESS_MODE_ALWAYS
	var args := parse_args(OS.get_cmdline_user_args())
	enabled = args.has("auto-test")
	if not enabled:
		set_process(false)
		return
	bot_mode = BotMode.WIN
	frames_left = int(args.get("frames", str(DEFAULT_FRAMES)))
	screenshot_path = str(args.get("screenshot", ""))
	# `--time-scale=4`: игровое время быстрее, чтобы длинные прогоны ботом укладывались в кадры.
	Engine.time_scale = float(args.get("time-scale", "1"))
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
