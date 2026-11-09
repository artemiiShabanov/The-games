extends Control
## Прототип желе (ветка proto/jelly): «Прыгай» прямо на фоне, без спринта, и лист кадров в
## движении. Флаги: `--lose` бот проваливает (падения и удары), `--from=N` первый кадр,
## `--every=N` шаг, `--count=N` кадров в листе, `--crop=x,y,w,h` вырезка, `--flat` без желе,
## `--t=0.5` сложность. Лист пишется в `debug/playtest/jelly_sheet.png`.

const SHEET := "debug/playtest/jelly_sheet.png"

var runner: Minigame
var frame := 0
var shots: Array[int] = []
var crop := Rect2i(240, 560, 760, 380)
var images: Array[Image] = []


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
	var def := MinigamePool.find(MinigamePool.load_all(), &"runner")
	runner = def.scene.instantiate() as Minigame
	runner.setup(def, float(args.get("t", "0.3")), int(args.get("seed", "3")))
	add_child(runner)
	runner.start()
	runner.finished.connect(func(ok: bool) -> void: AutoTest.note("runner finished: %s" % ok))


func _process(_delta: float) -> void:
	frame += 1
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
