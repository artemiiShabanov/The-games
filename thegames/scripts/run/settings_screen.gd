class_name SettingsScreen
extends Control
## Список сеттингов и достижений, которые их открывают (#139), поверх главного меню или
## главного экрана забега: десять плашек в два столбца, у каждой портрет героя, название и
## состояние. Открытый со старта, открытый достижением, купленный на этот забег или закрытый:
## у закрытого силуэт, название достижения, условие и прогресс в идущем забеге. Сеттинг без
## готового набора помечен «скоро». Экран только показывает: Esc или ␣ закрывают, клик только
## мимо карточки (полировка 2026-11-17: клик по самой карточке её не закрывает).
## Работает и на паузе дерева.

signal closed

const WIDTH := 1480.0
const CELL_HEIGHT := 124.0
const FACE := 80.0

var profile: Profile
var run: RunState
var _panel: PanelContainer


func setup(profile_: Profile, run_: RunState = null) -> void:
	profile = profile_
	run = run_


## Сколько сеттингов открыто сейчас: в забеге с купленными, в меню стартовые и достижения.
static func open_count(profile_: Profile, run_: RunState = null) -> int:
	if run_ != null:
		return run_.unlocked_settings().size()
	var n := RunTuning.load_default().start_settings.size()
	for s in Achievements.unlocked(profile_):
		if not RunTuning.load_default().start_settings.has(s):
			n += 1
	return n


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
	_panel = panel
	Jelly.panel(panel)
	Jelly.cover(self)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 12)
	panel.add_child(column)
	var title := _label("Сеттинги", Style.FONT_H1, Style.INK)
	title.add_theme_font_override("font", Jelly.fun_font(800))
	column.add_child(title)
	column.add_child(_label("Открыто %d из %d. Достижение открывает сеттинг во всех забегах." % [
			open_count(profile, run), Game.Setting.size()], Style.FONT_BODY, Style.INK_2))
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 8)
	column.add_child(gap)
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 16)
	grid.add_theme_constant_override("v_separation", 12)
	column.add_child(grid)
	var catalog := Catalog.load_kind(CatalogEntry.Kind.SETTING)
	for s in _order():
		grid.add_child(_cell(s, catalog.by_value(int(s))))
	var hints := HBoxContainer.new()
	hints.alignment = BoxContainer.ALIGNMENT_CENTER
	hints.add_theme_constant_override("separation", 16)
	hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hints.offset_top = -(Style.PILL_HEIGHT + 16)
	hints.offset_bottom = -16
	hints.add_child(HintPill.make("Esc назад"))
	add_child(hints)
	MouseUi.pass_through(self)
	ShellSounds.play(&"intro")


## Стартовые первыми, дальше открываемые по порядку перечисления.
func _order() -> Array[Game.Setting]:
	var out: Array[Game.Setting] = _start().duplicate()
	for s in Game.Setting.values():
		if not out.has(s as Game.Setting):
			out.append(s as Game.Setting)
	return out


func _start() -> Array[Game.Setting]:
	return run.start_settings if run != null else RunTuning.load_default().start_settings


func _cell(s: Game.Setting, entry: CatalogEntry) -> PanelContainer:
	var ach := Achievements.for_setting(s)
	var earned := ach != null and profile != null and profile.achievements.has(ach.id)
	var ready := Achievements.ready(s)
	var start := _start().has(s)
	var in_run := run != null and run.unlocked_settings().has(s)
	var open := start or (earned and ready) or in_run
	var cell := PanelContainer.new()
	var sb := Style.flat(Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 0)
	sb.content_margin_left = 16
	sb.content_margin_right = 20
	sb.content_margin_top = 16
	sb.content_margin_bottom = 16
	cell.add_theme_stylebox_override("panel", sb)
	cell.custom_minimum_size = Vector2((WIDTH - 2 * Style.PAD_CARD - 16) / 2.0, CELL_HEIGHT)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 20)
	cell.add_child(row)
	# Портрет героя на плашке цвета сеттинга; у закрытого тёмный силуэт.
	var tile := PanelContainer.new()
	var color := entry.color if entry != null else Style.INK_3
	var tsb := Style.flat(color if open else Style.INK_3, 12, Color.TRANSPARENT, 0)
	tile.add_theme_stylebox_override("panel", tsb)
	tile.custom_minimum_size = Vector2(FACE, FACE)
	tile.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var def := SettingDef.of(s)
	var face := TextureRect.new()
	face.texture = def.sprite16("brawl_face_hero") if def != null and ready else null
	face.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	face.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	face.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	if not open:
		face.modulate = Color(0.1, 0.1, 0.12, 0.55)
	tile.add_child(face)
	row.add_child(tile)
	var col := VBoxContainer.new()
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	col.add_theme_constant_override("separation", 2)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(col)
	var name_label := _label(entry.title if entry != null else Game.setting_name(s), 30, Style.INK if open else Style.INK_2)
	name_label.add_theme_font_override("font", Jelly.fun_font(800))
	col.add_child(name_label)
	var status := ""
	var status_color := Style.INK_2
	var detail := ""
	if start:
		status = "Открыт со старта" if ach == null else "Открыт в этом забеге со старта"
	elif not ready:
		status = "Скоро"
	elif earned:
		status = "Открыт · достижение «%s»" % ach.title
		status_color = Style.MONEY
	elif ach != null:
		status = "«%s»: %s" % [ach.title, ach.text.substr(0, 1).to_lower() + ach.text.substr(1)]
		var p := Achievements.progress(ach, run)
		if in_run:
			detail = "Куплен на этот забег"
		if p != "":
			detail += (" · " if detail != "" else "") + "Сейчас: " + p
	var sl := _label(status, Style.FONT_CAPTION, status_color)
	sl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	col.add_child(sl)
	if detail != "":
		col.add_child(_label(detail, Style.FONT_CAPTION, Style.ACCENT if in_run else Style.INK_3))
	return cell


func close() -> void:
	ShellSounds.play(&"done")
	closed.emit()


## Экран забирает весь ввод, пока открыт: под ним меню или главный экран забега.
func _input(event: InputEvent) -> void:
	var viewport := get_viewport()
	if MouseUi.is_motion(event):
		return
	var key := event as InputEventKey
	if (MouseUi.is_click(event) and not MouseUi.hit(_panel, event)) or (key != null and key.pressed and not key.echo and key.keycode == KEY_ESCAPE) \
			or (not event.is_echo() and (GameInput.is_a(event) or GameInput.is_b(event))):
		close()
	if viewport != null and (event is InputEventKey or event is InputEventMouseButton or event is InputEventJoypadButton
			or event is InputEventJoypadMotion or event is InputEventPanGesture):
		viewport.set_input_as_handled()


func _label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l
