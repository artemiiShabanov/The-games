extends Node
## Автотест. Запуск:
##   Godot --path thegames -- --auto-test [--frames=N] [--screenshot=debug/playtest/x.png]
## Прогоняет N кадров (бот включён, `bot_active`), пишет скриншот, печатает `END ok`
## или `END fail: причины` и выходит с кодом 0 или 1. Относительный путь скриншота
## считается от корня проекта (`res://`). Обёртка с проверкой вывода: `tools/autotest.sh`.

const DEFAULT_FRAMES := 120

var enabled := false
## Системы спрашивают этот флаг, чтобы вместо игрока действовал бот.
var bot_active := false
var frames_left := 0
var screenshot_path := ""
var failures: PackedStringArray = []


func _ready() -> void:
	var args := _parse_args(OS.get_cmdline_user_args())
	enabled = args.has("auto-test")
	if not enabled:
		set_process(false)
		return
	bot_active = true
	frames_left = int(args.get("frames", str(DEFAULT_FRAMES)))
	screenshot_path = str(args.get("screenshot", ""))
	print("AUTO-TEST start: frames=%d screenshot=%s" % [frames_left, screenshot_path])


## Любая система может записать провал; автотест тогда закончится `END fail`.
func fail(reason: String) -> void:
	failures.append(reason)
	push_error("AUTO-TEST fail: " + reason)


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
	var headless := DisplayServer.get_name() == "headless"
	if not headless:
		# В headless кадры не рисуются и сигнал не приходит, ждать его нельзя.
		await RenderingServer.frame_post_draw
	if screenshot_path != "" and not headless:
		_save_screenshot(screenshot_path)
	if failures.is_empty():
		print("END ok")
	else:
		print("END fail: " + "; ".join(failures))
	get_tree().quit(0 if failures.is_empty() else 1)


func _save_screenshot(path: String) -> void:
	var abs_path := path
	if path.is_relative_path():
		abs_path = ProjectSettings.globalize_path("res://" + path)
	var dir_err := DirAccess.make_dir_recursive_absolute(abs_path.get_base_dir())
	if dir_err != OK:
		fail("screenshot dir: " + error_string(dir_err))
		return
	var image := get_viewport().get_texture().get_image()
	if image == null or image.is_empty():
		fail("screenshot: empty viewport image")
		return
	var err := image.save_png(abs_path)
	if err != OK:
		fail("screenshot save: " + error_string(err))
		return
	print("AUTO-TEST screenshot: " + abs_path)


## `--auto-test --frames=90` -> {"auto-test": "", "frames": "90"}.
func _parse_args(list: PackedStringArray) -> Dictionary:
	var out := {}
	for raw in list:
		var arg := raw.trim_prefix("--")
		var eq := arg.find("=")
		if eq < 0:
			out[arg] = ""
		else:
			out[arg.substr(0, eq)] = arg.substr(eq + 1)
	return out
