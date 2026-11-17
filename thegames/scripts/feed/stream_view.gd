class_name StreamView
extends PanelContainer
## Кадр стрима: живая запись геймплея (встроенная демка с багами записи, бот играет, без звука),
## сверху плашка «● имя» и онлайн, слева снизу говорящее пиксельное лицо стримера, под кадром
## реплика. Размер кадра задаёт хозяин: окно стрима после релиза (`StreamScreen`) или лента.
## Запись идёт по кругу, под ней тема игры (#87).

var record: GameRecord
var item: FeedContent.Item
var frame := Vector2(880, 408)

var _holder: Control
var _demo: Demo
var _bed: MusicBed


func setup(record_: GameRecord, item_: FeedContent.Item, frame_: Vector2) -> void:
	record = record_
	item = item_
	frame = frame_


func _ready() -> void:
	var sb := Style.inner_card()
	sb.set_content_margin_all(0)
	add_theme_stylebox_override("panel", sb)
	clip_contents = true
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 0)
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(col)
	_holder = Control.new()
	_holder.custom_minimum_size = frame
	_holder.clip_contents = true
	_holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_child(_holder)
	var backdrop := ColorRect.new()
	backdrop.color = Style.STUDIO_INK
	backdrop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_holder.add_child(backdrop)
	_start()
	# Шапка стрима поверх кадра: точка «в эфире», имя, онлайн.
	var top := HBoxContainer.new()
	top.position = Vector2(20, 16)
	top.add_theme_constant_override("separation", 12)
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_holder.add_child(top)
	top.add_child(_pill("● " + item.person.name, Style.DANGER))
	top.add_child(_pill(item.caption, Color(Style.INK, 0.7)))
	# Лицо стримера в левом нижнем углу, на плашке.
	var cam := PanelContainer.new()
	cam.add_theme_stylebox_override("panel", Style.flat(Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 8))
	cam.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cam.add_child(Portrait.new(item.person.id, 4, item.mood))
	_holder.add_child(cam)
	cam.position = Vector2(20, frame.y - 16 - Portrait.GRID * 4 - 16)
	var quote := Label.new()
	quote.text = item.text
	quote.add_theme_font_size_override("font_size", Style.FONT_BODY)
	quote.add_theme_color_override("font_color", Style.INK)
	quote.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	quote.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var quote_margin := MarginContainer.new()
	for side in ["left", "right", "top", "bottom"]:
		quote_margin.add_theme_constant_override("margin_" + side, 24 if side != "left" and side != "right" else Style.PAD_CARD)
	quote_margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	quote_margin.add_child(quote)
	col.add_child(quote_margin)


func _exit_tree() -> void:
	_demo = null


func _pill(text: String, color: Color) -> PanelContainer:
	var p := HintPill.make(text)
	(p.get_child(0) as Label).add_theme_color_override("font_color", Style.SURFACE_SOLID)
	var sb := Style.flat(color, Style.R_PILL, Color.TRANSPARENT, 0)
	sb.content_margin_left = 16
	sb.content_margin_right = 16
	sb.content_margin_top = 6
	sb.content_margin_bottom = 6
	p.add_theme_stylebox_override("panel", sb)
	return p


## Запустить встроенную демку записи; по концу перезапускается, как запись по кругу.
func _start() -> void:
	if record == null or _holder == null:
		return
	# Тема игры под клипом (#87): встроенная демка свою музыку не играет.
	if _bed == null:
		_bed = MusicBed.new(record, Music.tuning().feed_db, true)
		add_child(_bed)
	# Демка записи из каталога (#45); без неё кадр стрима остаётся фоном.
	_demo = DemoCatalog.create(record)
	if _demo == null:
		return
	_demo.set_anchors_preset(Control.PRESET_TOP_LEFT)
	_demo.setup(record, &"clip")
	_demo.embed(frame)
	_demo.demo_finished.connect(_on_finished)
	_holder.add_child(_demo)
	_holder.move_child(_demo, 1)
	_demo.start()


func _on_finished(_r: GameRecord, _reached: bool) -> void:
	if _demo != null:
		_demo.queue_free()
		_demo = null
	if is_inside_tree() and _holder != null:
		_start()
