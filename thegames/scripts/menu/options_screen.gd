class_name OptionsScreen
extends Control
## Экран настроек (#81) поверх меню или паузы: карточка со строками громкости (общая, музыка,
## звуки), полного экрана, движения интерфейса и подписей клавиш, внизу «Готово». ↑ ↓ строка,
## ← → меняют значение (громкость шагом 10 %), ␣ переключает или закрывает на «Готово».
## Мышь: наведение берёт строку, клик по полосе громкости ставит значение по месту, клик по
## переключателю меняет его, колесо и тачпад над строкой крутят значение. Esc или Ctrl
## закрывают. Всё применяется сразу (`Options.apply`) и пишется при закрытии. Работает и на
## паузе дерева.

signal closed

const WIDTH := 880.0
const ROW_HEIGHT := 72.0
const BAR := Vector2(320, 12)
const STEP := 0.1
## Зазор между строками (плейтест 2026-11-11: строки слипались).
const ROW_GAP := 20

enum Row { MASTER, MUSIC, SFX, FULLSCREEN, MOTION, GLYPHS, DONE }

const TITLES: Array[String] = ["Громкость", "Музыка", "Звуки", "Полный экран", "Мармелад и суета", "Подписи клавиш", "Готово"]

var index := 0
var _rows: Array[PanelContainer] = []
var _values: Array[Label] = []
var _bars: Array[Control] = []
var _fills: Array[ColorRect] = []
var _lifts: Array[JellyLift] = []


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var dim := ColorRect.new()
	dim.color = Color(Style.BG, 0.92)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.card(true))
	panel.custom_minimum_size = Vector2(WIDTH, 0)
	center.add_child(panel)
	Jelly.panel(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", ROW_GAP)
	panel.add_child(column)
	var title := _label("Настройки", Style.FONT_H1, Style.INK)
	title.add_theme_font_override("font", Jelly.fun_font(800))
	column.add_child(title)
	column.add_child(_spacer(8))
	for i in TITLES.size():
		column.add_child(_make_row(i))
		if i == Row.SFX or i == Row.GLYPHS:
			column.add_child(_spacer(12))
	var hints := HBoxContainer.new()
	hints.alignment = BoxContainer.ALIGNMENT_CENTER
	hints.add_theme_constant_override("separation", 16)
	hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hints.offset_top = -(Style.PILL_HEIGHT + 16)
	hints.offset_bottom = -16
	hints.add_child(HintPill.make("↑ ↓ строка"))
	hints.add_child(HintPill.make("← → менять"))
	hints.add_child(HintPill.make("Esc готово"))
	add_child(hints)
	MouseUi.pass_through(self)
	_refresh()
	ShellSounds.play(&"intro")


# --- Значения ---------------------------------------------------------------------------------

func change(row: int, dir: int) -> void:
	match row:
		Row.MASTER:
			Options.master = _step(Options.master, dir)
		Row.MUSIC:
			Options.music = _step(Options.music, dir)
		Row.SFX:
			Options.sfx = _step(Options.sfx, dir)
		Row.FULLSCREEN:
			Options.fullscreen = not Options.fullscreen
		Row.MOTION:
			Options.motion = not Options.motion
		Row.GLYPHS:
			Options.glyphs = wrapi(int(Options.glyphs) + (dir if dir != 0 else 1), 0, Options.Glyphs.size()) as Options.Glyphs
		_:
			return
	Options.apply()
	ShellSounds.play(&"tick")
	Jelly.poke(_rows[row], 0.6)
	_refresh()


func set_volume(row: int, v: float) -> void:
	v = snappedf(clampf(v, 0.0, 1.0), 0.05)
	match row:
		Row.MASTER:
			Options.master = v
		Row.MUSIC:
			Options.music = v
		Row.SFX:
			Options.sfx = v
		_:
			return
	Options.apply()
	ShellSounds.play(&"tick")
	_refresh()


func close() -> void:
	Options.save()
	ShellSounds.play(&"done")
	closed.emit()


func _step(v: float, dir: int) -> float:
	return clampf(snappedf(v + STEP * dir, STEP), 0.0, 1.0)


func _volume_of(row: int) -> float:
	match row:
		Row.MASTER:
			return Options.master
		Row.MUSIC:
			return Options.music
		Row.SFX:
			return Options.sfx
	return 0.0


func _value_text(row: int) -> String:
	match row:
		Row.MASTER, Row.MUSIC, Row.SFX:
			var v := _volume_of(row)
			return "тишина" if v <= 0.001 else "%d %%" % roundi(v * 100.0)
		Row.FULLSCREEN:
			return "да" if Options.fullscreen else "окно"
		Row.MOTION:
			return "всё пружинит" if Options.motion else "спокойно"
		Row.GLYPHS:
			return Options.GLYPH_NAMES[Options.glyphs]
	return ""


# --- Ввод -------------------------------------------------------------------------------------

func _input(event: InputEvent) -> void:
	var viewport := get_viewport()
	if MouseUi.is_motion(event):
		var over := _row_at(event)
		if over >= 0 and over != index:
			index = over
			ShellSounds.play(&"tick")
			_refresh()
		return
	var w := MouseUi.wheel(event)
	if w != 0:
		var at := _row_at(event)
		if at >= 0 and at != Row.DONE:
			index = at
			change(at, -w)
		MouseUi.consume(viewport)
		return
	if MouseUi.is_click(event):
		var at := _row_at(event)
		if at == Row.DONE:
			close()
		elif at >= 0:
			index = at
			if at <= Row.SFX and MouseUi.hit(_bars[at], event):
				var r := MouseUi.rect_of(_bars[at])
				set_volume(at, ((event as InputEventMouse).position.x - r.position.x) / r.size.x)
			else:
				change(at, 1)
		MouseUi.consume(viewport)
		return
	if MouseUi.is_mouse(event):
		MouseUi.consume(viewport)
		return
	var key := event as InputEventKey
	if key != null and key.pressed and not key.echo and key.keycode == KEY_ESCAPE:
		close()
	elif GameInput.is_b(event):
		close()
	elif event.is_action_pressed(GameInput.UP, true):
		_move(-1)
	elif event.is_action_pressed(GameInput.DOWN, true):
		_move(1)
	elif event.is_action_pressed(GameInput.LEFT, true):
		change(index, -1)
	elif event.is_action_pressed(GameInput.RIGHT, true):
		change(index, 1)
	elif GameInput.is_a(event) and not event.is_echo():
		if index == Row.DONE:
			close()
		elif index > Row.SFX:
			change(index, 1)
	elif key == null:
		return
	MouseUi.consume(viewport)


func _move(dir: int) -> void:
	var next := clampi(index + dir, 0, Row.DONE)
	if next != index:
		index = next
		ShellSounds.play(&"tick")
		_refresh()


func _row_at(event: InputEvent) -> int:
	for i in _rows.size():
		if MouseUi.hit(_rows[i], event):
			return i
	return -1


# --- Построение ---------------------------------------------------------------------------------

func _make_row(i: int) -> PanelContainer:
	var row := PanelContainer.new()
	row.custom_minimum_size = Vector2(0, ROW_HEIGHT)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 24)
	row.add_child(h)
	var name_label := _label(TITLES[i], Style.FONT_H2, Style.INK)
	name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	if i == Row.DONE:
		name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	h.add_child(name_label)
	var bar := Control.new()
	var fill := ColorRect.new()
	if i <= Row.SFX:
		bar.custom_minimum_size = BAR
		bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		var track := Panel.new()
		track.add_theme_stylebox_override("panel", Style.flat(Style.SURFACE_2, Style.R_PILL, Color.TRANSPARENT, 0))
		track.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		bar.add_child(track)
		fill.color = Style.INK
		fill.size = Vector2(0, BAR.y)
		bar.add_child(fill)
		h.add_child(bar)
	var value := _label("", Style.FONT_BODY, Style.INK_2)
	value.custom_minimum_size = Vector2(180 if i != Row.DONE else 0, 0)
	value.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	value.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	h.add_child(value)
	_rows.append(row)
	_values.append(value)
	_bars.append(bar)
	_fills.append(fill)
	_lifts.append(Jelly.button(row))
	return row


func _refresh() -> void:
	for i in _rows.size():
		var on := i == index
		var sb := Style.flat(Style.INK if on else Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 0)
		sb.content_margin_left = 24
		sb.content_margin_right = 24
		_rows[i].add_theme_stylebox_override("panel", sb)
		_lifts[i].focused = on
		var h := _rows[i].get_child(0) as HBoxContainer
		(h.get_child(0) as Label).add_theme_color_override("font_color", Style.SURFACE_SOLID if on else Style.INK)
		_values[i].text = _value_text(i)
		_values[i].add_theme_color_override("font_color", Style.SURFACE_SOLID if on else Style.INK_2)
		if i <= Row.SFX:
			_fills[i].size = Vector2(BAR.x * _volume_of(i), BAR.y)
			_fills[i].color = Style.SURFACE_SOLID if on else Style.INK
			var track := _bars[i].get_child(0) as Panel
			track.add_theme_stylebox_override("panel", Style.flat(Style.INK_2 if on else Style.BG, Style.R_PILL, Color.TRANSPARENT, 0))


func _label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	return l


func _spacer(h: int) -> Control:
	var s := Control.new()
	s.custom_minimum_size = Vector2(0, h)
	return s
