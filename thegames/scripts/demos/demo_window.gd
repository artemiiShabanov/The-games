class_name DemoWindow
extends Control
## Окно с живой демкой записи (#68): встроенный режим `Demo.embed`, бот играет, без звука, по
## концу демка перезапускается, как запись по кругу. Экран концовки и галерея. Без демки пары
## окно остаётся цветной плашкой жанра с названием.

var record: GameRecord
var _demo: Demo


func setup(record_: GameRecord, size_: Vector2) -> void:
	record = record_
	custom_minimum_size = size_
	size = size_
	clip_contents = true
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Style.STUDIO_INK
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)
	_start()


func _start() -> void:
	if record == null or not is_inside_tree():
		return
	_demo = DemoCatalog.create(record)
	if _demo == null:
		return
	# Корень сцены демки растянут на весь экран; встроенной нужен свой размер.
	_demo.set_anchors_preset(Control.PRESET_TOP_LEFT)
	_demo.setup(record, &"gallery")
	_demo.embed(custom_minimum_size)
	_demo.demo_finished.connect(_on_finished)
	add_child(_demo)
	_demo.start()


func _on_finished(_r: GameRecord, _reached: bool) -> void:
	if _demo != null:
		_demo.queue_free()
		_demo = null
	_start.call_deferred()
