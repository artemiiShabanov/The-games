class_name AchievementToast
extends Control
## Пилюля достижения (#139): выезжает сверху по центру, висит `HOLD` секунд и уезжает; несколько
## подряд идут очередью. Хозяин зовёт `push` на своём единственном экземпляре. Ввод не трогает.

const HOLD := 4.5
const SLIDE := 0.35
const TOP := 8.0

var _queue: Array[AchievementDef] = []
var _busy := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	z_index = 50


func push(defs: Array[AchievementDef]) -> void:
	_queue.append_array(defs)
	if not _busy:
		_next()


func _next() -> void:
	if _queue.is_empty():
		_busy = false
		return
	_busy = true
	var d: AchievementDef = _queue.pop_front()
	var pill := PanelContainer.new()
	var sb := Style.flat(Style.INK, Style.R_PILL, Color.TRANSPARENT, 0)
	sb.content_margin_left = 32
	sb.content_margin_right = 32
	sb.content_margin_top = 14
	sb.content_margin_bottom = 14
	pill.add_theme_stylebox_override("panel", sb)
	pill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 0)
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pill.add_child(col)
	var head := _label("Достижение «%s»" % d.title, Style.FONT_BODY, Style.SURFACE_SOLID)
	head.add_theme_font_override("font", Jelly.fun_font(800))
	col.add_child(head)
	col.add_child(_label("Открыт сеттинг: %s. Действует во всех забегах." % Game.setting_name(d.setting), Style.FONT_CAPTION, Style.INK_3))
	add_child(pill)
	pill.reset_size()
	var w := pill.get_combined_minimum_size()
	pill.position = Vector2((Style.SCREEN.x - w.x) / 2.0, -w.y - 8.0)
	ShellSounds.play(&"done")
	var quick := Debug.skip_cards
	var tw := create_tween()
	tw.tween_property(pill, "position:y", TOP, 0.0 if quick else SLIDE).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)
	tw.tween_interval(HOLD)
	tw.tween_property(pill, "position:y", -w.y - 8.0, 0.0 if quick else SLIDE).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_CUBIC)
	tw.tween_callback(pill.queue_free)
	tw.tween_callback(_next)


func _label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l
