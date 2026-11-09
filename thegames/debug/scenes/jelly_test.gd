extends Control
## Прототип желе (ветка proto/jelly): мини-игра прямо на фоне, без спринта, и лист кадров в
## движении. Флаги: `--game=fit_frame` другая мини-игра (по умолчанию runner), `--lose` бот проваливает (падения и удары), `--from=N` первый кадр,
## `--every=N` шаг, `--count=N` кадров в листе, `--crop=x,y,w,h` вырезка, `--flat` без желе,
## `--t=0.5` сложность. Лист пишется в `debug/playtest/jelly_sheet.png`.

const SHEET := "debug/playtest/jelly_sheet.png"

var runner: Minigame
var frame := 0
var shots: Array[int] = []
var crop := Rect2i(240, 560, 760, 380)
var images: Array[Image] = []
var constructor: Constructor
## Действия по кадрам для экрана: кадр -> команда (down, up, left, right, a, mouse=XxY,
## click=XxY, release=XxY). `--locked` открыт только первый жанр.
var actions: Dictionary[int, String] = {}


func _ready() -> void:
	var args := AutoTest.parse_args(OS.get_cmdline_user_args())
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	if args.has("lose"):
		AutoTest.bot_mode = AutoTest.BotMode.LOSE
	if args.has("flat"):
		Jelly.enabled = false
	if args.has("crop"):
		var c := str(args["crop"]).split(",")
		crop = Rect2i(int(c[0]), int(c[1]), int(c[2]), int(c[3]))
	var from := int(args.get("from", "60"))
	var every := int(args.get("every", "4"))
	for i in int(args.get("count", "0")):
		shots.append(from + i * every)
	for part in str(args.get("actions", "")).split(",", false):
		var kv := part.split(":")
		actions[int(kv[0])] = kv[1]
	if args.has("screen"):
		_open_constructor(args.has("locked"))
		return
	var def := MinigamePool.find(MinigamePool.load_all(), StringName(str(args.get("game", "runner"))))
	runner = def.scene.instantiate() as Minigame
	runner.setup(def, float(args.get("t", "0.3")), int(args.get("seed", "3")))
	add_child(runner)
	runner.start()
	runner.finished.connect(func(ok: bool) -> void: AutoTest.note("runner finished: %s" % ok))


## Экран настройки игры со всем открытым, как в `constructor_test`.
func _open_constructor(locked := false) -> void:
	var genres: Array[Game.Genre] = []
	for g in Game.Genre.values():
		if not locked or genres.size() < 1:
			genres.append(g as Game.Genre)
	var techs: Array[Game.Tech] = []
	for t in Game.Tech.values():
		techs.append(t as Game.Tech)
	var settings: Array[Game.Setting] = []
	for st in Game.Setting.values():
		settings.append(st as Game.Setting)
	constructor = (load("res://scenes/constructor.tscn") as PackedScene).instantiate() as Constructor
	constructor.setup(genres, techs, settings, 60000, 2, 1)
	add_child(constructor)


func _act(cmd: String) -> void:
	if cmd.begins_with("click=") or cmd.begins_with("release="):
		var xy2 := cmd.get_slice("=", 1).split("x")
		var b := InputEventMouseButton.new()
		b.button_index = MOUSE_BUTTON_LEFT
		b.pressed = cmd.begins_with("click=")
		b.position = Vector2(float(xy2[0]), float(xy2[1]))
		b.global_position = b.position
		Input.parse_input_event(b)
		return
	if cmd.begins_with("mouse="):
		var xy := cmd.trim_prefix("mouse=").split("x")
		var pos := Vector2(float(xy[0]), float(xy[1]))
		var e := InputEventMouseMotion.new()
		e.position = pos
		e.global_position = pos
		get_viewport().warp_mouse(pos)
		Input.parse_input_event(e)
		return
	match cmd:
		"down": constructor.move(1)
		"up": constructor.move(-1)
		"left": constructor.focus(constructor.focus_row - 1)
		"right": constructor.focus(constructor.focus_row + 1)
		"a": constructor.confirm()


func _process(_delta: float) -> void:
	frame += 1
	if actions.has(frame) and constructor != null:
		_act(actions[frame])
	if shots.has(frame):
		await RenderingServer.frame_post_draw
		var img := get_viewport().get_texture().get_image()
		if img != null and not img.is_empty():
			var scale := Vector2(img.get_size()) / Vector2(Style.SCREEN)
			var r := Rect2i(Vector2i(Vector2(crop.position) * scale), Vector2i(Vector2(crop.size) * scale))
			var part := img.get_region(r)
			part.resize(crop.size.x, crop.size.y)
			images.append(part)
		if images.size() == shots.size():
			_save_sheet()


func _save_sheet() -> void:
	var cols := 3
	var rows := ceili(images.size() / float(cols))
	var sheet := Image.create(crop.size.x * cols + (cols - 1) * 4, crop.size.y * rows + (rows - 1) * 4, false, Image.FORMAT_RGBA8)
	sheet.fill(Color.BLACK)
	for i in images.size():
		var img := images[i]
		img.convert(Image.FORMAT_RGBA8)
		sheet.blit_rect(img, Rect2i(Vector2i.ZERO, crop.size), Vector2i((i % cols) * (crop.size.x + 4), (i / cols) * (crop.size.y + 4)))
	sheet.save_png(ProjectSettings.globalize_path("res://" + SHEET))
	AutoTest.note("sheet " + SHEET)
