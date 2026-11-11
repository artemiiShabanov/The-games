extends Node
## Дебаг-меню и реестр ручек, спека `docs/specs/debug.md`. Автолоад `Debug`.
## Только в дебаг-сборке: в релизе `_ready` выходит, все `add_*` пустые. Этот файл остаётся в
## экспорте, потому что на него ссылается автолоад; из экспорта исключается `debug/scenes/`.
##
## F1 меню, F2 оверлей, F3 скорость времени, F5 перезапуск сцены, F9 скриншот.
## `--debug` открывает меню на старте, `--scene=<id>` запускает `debug/scenes/<id>.tscn`.
##
## Системы регистрируют ручки в `_ready`:
##   Debug.add_action(&"Мини-игры", "Запустить", _on_run)
##   Debug.add_toggle(&"Переключатели", "Хитбоксы", get_fn, set_fn)
##   Debug.add_number(&"Мини-игры", "t", get_fn, set_fn, 0.0, 1.0, 0.05, true)  # persist
##   Debug.add_choice(&"Демки", "Жанр", ["платформер", "гонки"], get_fn, set_fn)
##   Debug.watch("релиз", func() -> String: return str(release_index))

enum Kind { ACTION, TOGGLE, NUMBER, CHOICE }

const SCENES_DIR := "res://debug/scenes/"
const PLAYTEST_DIR := "debug/playtest/"
const CFG_PATH := "user://debug.cfg"
const TIME_SCALES: Array[float] = [0.25, 1.0, 4.0]
const BOT_LABELS: Array[String] = ["как игрок", "всегда выигрывает", "всегда проигрывает"]
const SECTION_SCENES: StringName = &"Сцены"
const SECTION_TOGGLES: StringName = &"Переключатели"
const SECTION_TOOLS: StringName = &"Инструменты"
const SECTION_MINIGAMES: StringName = &"Мини-игры"
const MINIGAME_SCENE := "sprint_runner_test"
const SECTION_DEMOS: StringName = &"Демки"
const DEMO_SCENE := "demo_test"
const INK := Style.STUDIO_INK
const BG := Style.BG
const FOCUS := Style.FOCUS


class Entry:
	var kind: Kind
	var label: String
	var fn: Callable
	var getter: Callable
	var setter: Callable
	var min_value := 0.0
	var max_value := 1.0
	var step := 1.0
	var options: Array = []
	var persist := false


## Пропускать карточки интро, результата и анимации студии.
var skip_cards := false
## Раздел «Мини-игры»: что запускать в `sprint_runner_test`. Сцена читает это в `_ready`.
var minigame_id := "fit_frame"
var minigame_t := 0.0
var minigame_seed := 1
var minigame_loop := false
## Переигровок в плане тестовой сцены раннера (#29).
var minigame_replays := 0
## true: одна мини-игра `minigame_id`, false: весь план из 8.
var minigame_single := false
## Раздел «Демки»: сид, жанр и набор багов для `demo_test`.
var demo_seed := 1
## Сеттинг записи тестовой демки (#46): 0 пираты, 1 космос, 2 замки.
var demo_setting := 0
## Жанр тестовой демки (#48, #50, #52, #54): `Game.Genre`, 0 платформер, 1 гонки, 2 шутер, 3 спорт
## (гольф), 4 файтинг; технология всегда 8-bit.
var demo_genre := 0
var demo_bugs: Array[StringName] = []
var active := false

var _sections: Dictionary = {}
var _order: Array[StringName] = []
var _watches: Array[Array] = []
var _cfg := ConfigFile.new()
var _layer: CanvasLayer
var _section_list: ItemList
var _entries_box: VBoxContainer
var _overlay: Label
var _hint: Label


func _ready() -> void:
	if not OS.is_debug_build():
		set_process(false)
		set_process_input(false)
		return
	active = true
	process_mode = Node.PROCESS_MODE_ALWAYS
	_cfg.load(CFG_PATH)
	_build_ui()
	_register_builtin()
	var args := AutoTest.parse_args(OS.get_cmdline_user_args())
	if args.has("scene"):
		run_test_scene.call_deferred(str(args["scene"]))
	if args.has("debug"):
		_open_menu_when_scene_ready()


# --- Реестр -------------------------------------------------------------------------------

func add_action(section: StringName, label: String, fn: Callable) -> void:
	var e := Entry.new()
	e.kind = Kind.ACTION
	e.label = label
	e.fn = fn
	_add(section, e)


func add_toggle(section: StringName, label: String, getter: Callable, setter: Callable,
		persist := false) -> void:
	var e := Entry.new()
	e.kind = Kind.TOGGLE
	e.label = label
	e.getter = getter
	e.setter = setter
	e.persist = persist
	_add(section, e)


func add_number(section: StringName, label: String, getter: Callable, setter: Callable,
		min_value: float, max_value: float, step: float, persist := false) -> void:
	var e := Entry.new()
	e.kind = Kind.NUMBER
	e.label = label
	e.getter = getter
	e.setter = setter
	e.min_value = min_value
	e.max_value = max_value
	e.step = step
	e.persist = persist
	_add(section, e)


func add_choice(section: StringName, label: String, options: Array, getter: Callable,
		setter: Callable, persist := false) -> void:
	var e := Entry.new()
	e.kind = Kind.CHOICE
	e.label = label
	e.options = options
	e.getter = getter
	e.setter = setter
	e.persist = persist
	_add(section, e)


## Строка в оверлее F2: `label: getter()`.
func watch(label: String, getter: Callable) -> void:
	if active:
		_watches.append([label, getter])


## Убрать все ручки раздела: когда сцена-владелец уходит.
func clear_section(section: StringName) -> void:
	if active and _sections.has(section):
		(_sections[section] as Array).clear()


func _add(section: StringName, e: Entry) -> void:
	if not active:
		return
	if not _sections.has(section):
		_sections[section] = []
		_order.append(section)
	(_sections[section] as Array).append(e)
	var key := _key(section, e)
	if e.persist and _cfg.has_section_key("values", key):
		e.setter.call(_cfg.get_value("values", key))


func _key(section: StringName, e: Entry) -> String:
	return "%s/%s" % [section, e.label]


# --- Меню -----------------------------------------------------------------------------------

func is_open() -> bool:
	return active and _layer.visible


func toggle_menu() -> void:
	if is_open():
		close_menu()
	else:
		open_menu()


func open_menu() -> void:
	if not active:
		return
	_rebuild_scenes()
	_rebuild_sections()
	_layer.visible = true
	get_tree().paused = true
	_section_list.grab_focus()


func close_menu() -> void:
	if not active:
		return
	_layer.visible = false
	get_tree().paused = false


func run_test_scene(id: String) -> void:
	var path := SCENES_DIR + id + ".tscn"
	if not ResourceLoader.exists(path):
		push_error("Debug: нет тестовой сцены " + path)
		return
	close_menu()
	get_tree().change_scene_to_file(path)


## Открыть меню, когда текущая сцена сменится и отработает `_ready` (для `--debug --scene`).
func _open_menu_when_scene_ready() -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	open_menu()


func go_to_main() -> void:
	close_menu()
	get_tree().change_scene_to_file(str(ProjectSettings.get_setting("application/run/main_scene")))


func restart_scene() -> void:
	close_menu()
	get_tree().reload_current_scene()


func cycle_time_scale() -> void:
	var i := TIME_SCALES.find(Engine.time_scale)
	Engine.time_scale = TIME_SCALES[(i + 1) % TIME_SCALES.size()]
	_flash("скорость ×%s" % Engine.time_scale)


func save_screenshot() -> void:
	await RenderingServer.frame_post_draw
	var path := PLAYTEST_DIR + "shot_" + Time.get_datetime_string_from_system().replace(":", "-") + ".png"
	var err := Screenshot.save(get_viewport(), path)
	if err == OK:
		_flash("скриншот: " + path)
	else:
		push_error("Debug: скриншот не сохранён: " + error_string(err))


func _input(event: InputEvent) -> void:
	if event.is_action_pressed(&"debug_menu"):
		toggle_menu()
		get_viewport().set_input_as_handled()
	elif is_open() and event.is_action_pressed(&"ui_cancel"):
		close_menu()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed(&"debug_overlay"):
		_overlay.visible = not _overlay.visible
	elif event.is_action_pressed(&"debug_time"):
		cycle_time_scale()
	elif event.is_action_pressed(&"debug_restart"):
		restart_scene()
	elif event.is_action_pressed(&"debug_screenshot"):
		save_screenshot()


func _process(_delta: float) -> void:
	if _overlay.visible:
		var lines: PackedStringArray = ["%d FPS  %.1f ms  ×%s" % [
			Engine.get_frames_per_second(), Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0,
			Engine.time_scale]]
		for w in _watches:
			lines.append("%s: %s" % [w[0], str((w[1] as Callable).call())])
		_overlay.text = "\n".join(lines)


# --- Встроенные разделы ---------------------------------------------------------------------

func _register_builtin() -> void:
	_sections[SECTION_SCENES] = []
	_order.append(SECTION_SCENES)
	add_choice(SECTION_TOGGLES, "Бот", BOT_LABELS,
			func() -> String: return BOT_LABELS[AutoTest.bot_mode],
			func(v: String) -> void: AutoTest.bot_mode = BOT_LABELS.find(v) as AutoTest.BotMode)
	add_choice(SECTION_TOGGLES, "Скорость времени (F3)", TIME_SCALES,
			func() -> float: return Engine.time_scale,
			func(v: float) -> void: Engine.time_scale = v)
	add_toggle(SECTION_TOGGLES, "Оверлей FPS (F2)",
			func() -> bool: return _overlay.visible,
			func(v: bool) -> void: _overlay.visible = v)
	add_toggle(SECTION_TOGGLES, "Хитбоксы (для новых нод)",
			func() -> bool: return get_tree().debug_collisions_hint,
			func(v: bool) -> void: get_tree().debug_collisions_hint = v)
	add_toggle(SECTION_TOGGLES, "Без звука",
			func() -> bool: return AudioServer.is_bus_mute(0),
			func(v: bool) -> void: AudioServer.set_bus_mute(0, v))
	add_toggle(SECTION_TOGGLES, "Пропуск карточек и анимаций",
			func() -> bool: return skip_cards,
			func(v: bool) -> void: skip_cards = v)
	var ids: Array[String] = []
	for d in MinigamePool.load_all():
		ids.append(String(d.id))
	add_choice(SECTION_MINIGAMES, "Мини-игра", ids,
			func() -> String: return minigame_id,
			func(v: String) -> void: minigame_id = v, true)
	add_number(SECTION_MINIGAMES, "t", func() -> float: return minigame_t,
			func(v: float) -> void: minigame_t = v, 0.0, 1.0, 0.05, true)
	add_number(SECTION_MINIGAMES, "Сид", func() -> int: return minigame_seed,
			func(v: float) -> void: minigame_seed = int(v), 1, 999, 1, true)
	add_toggle(SECTION_MINIGAMES, "Зациклить", func() -> bool: return minigame_loop,
			func(v: bool) -> void: minigame_loop = v)
	add_number(SECTION_MINIGAMES, "Переигровок", func() -> int: return minigame_replays,
			func(v: float) -> void: minigame_replays = int(v), 0, 2, 1)
	# Мышь (#83): пилюли ввода как у игрока на мыши; клик или клавиша переключат сами.
	add_toggle(SECTION_MINIGAMES, "Пилюли: мышь", func() -> bool: return GameInput.mouse,
			func(v: bool) -> void: GameInput.mouse = v)
	add_action(SECTION_MINIGAMES, "Запустить мини-игру", func() -> void:
		minigame_single = true
		run_test_scene(MINIGAME_SCENE))
	add_action(SECTION_MINIGAMES, "Весь план из 8 спринтов", func() -> void:
		minigame_single = false
		run_test_scene(MINIGAME_SCENE))
	add_number(SECTION_DEMOS, "Сид", func() -> int: return demo_seed,
			func(v: float) -> void: demo_seed = int(v), 1, 999, 1, true)
	var genre_names: Array[String] = ["платформер", "гонки", "шутер", "спорт", "файтинг"]
	add_choice(SECTION_DEMOS, "Жанр", genre_names, func() -> String: return genre_names[clampi(demo_genre, 0, genre_names.size() - 1)],
			func(v: String) -> void: demo_genre = maxi(genre_names.find(v), 0), true)
	var setting_names: Array[String] = ["пираты", "космос", "замки"]
	add_choice(SECTION_DEMOS, "Сеттинг", setting_names, func() -> String: return setting_names[demo_setting],
			func(v: String) -> void: demo_setting = maxi(setting_names.find(v), 0), true)
	var catalog := BugCatalog.load_default()
	if catalog != null:
		for bug in catalog.bugs:
			var id := bug.id
			add_toggle(SECTION_DEMOS, "%s (%s)" % [bug.stamp, bug.owner_name()],
					func() -> bool: return demo_bugs.has(id),
					func(v: bool) -> void:
						if v and not demo_bugs.has(id):
							demo_bugs.append(id)
						elif not v:
							demo_bugs.erase(id))
	add_action(SECTION_DEMOS, "Запустить демку", func() -> void: run_test_scene(DEMO_SCENE))
	add_action(SECTION_TOOLS, "Скриншот в debug/playtest (F9)", func() -> void:
		close_menu()
		save_screenshot())
	add_action(SECTION_TOOLS, "Перезапустить сцену (F5)", restart_scene)
	add_action(SECTION_TOOLS, "В главную сцену", go_to_main)


func _rebuild_scenes() -> void:
	var list: Array = _sections[SECTION_SCENES]
	list.clear()
	var dir := DirAccess.open(SCENES_DIR)
	if dir == null:
		return
	var names: PackedStringArray = []
	for f in dir.get_files():
		if f.ends_with(".tscn"):
			names.append(f.get_basename())
	names.sort()
	for id in names:
		add_action(SECTION_SCENES, id.replace("_", " "), run_test_scene.bind(id))
	add_action(SECTION_SCENES, "В игру", go_to_main)


# --- UI -----------------------------------------------------------------------------------

func _build_ui() -> void:
	_layer = CanvasLayer.new()
	_layer.layer = 100
	_layer.visible = false
	add_child(_layer)

	var dim := ColorRect.new()
	dim.color = Color(INK, 0.55)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_layer.add_child(dim)

	var panel := PanelContainer.new()
	panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	panel.offset_left = 360
	panel.offset_top = 160
	panel.offset_right = -360
	panel.offset_bottom = -160
	panel.theme = _make_theme()
	var style := Style.flat(BG, 16)
	style.set_content_margin_all(24)
	panel.add_theme_stylebox_override("panel", style)
	_layer.add_child(panel)

	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 12)
	panel.add_child(root)

	var title := Label.new()
	title.text = "Дебаг  ·  F1 закрыть  ·  F2 оверлей  ·  F3 скорость  ·  F5 перезапуск  ·  F9 скриншот"
	title.add_theme_color_override("font_color", INK)
	title.add_theme_font_size_override("font_size", 20)
	root.add_child(title)

	var row := HBoxContainer.new()
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	row.add_theme_constant_override("separation", 24)
	root.add_child(row)

	_section_list = ItemList.new()
	_section_list.custom_minimum_size = Vector2(280, 0)
	_section_list.add_theme_font_size_override("font_size", 22)
	_section_list.add_theme_color_override("font_color", INK)
	_section_list.item_selected.connect(_on_section_selected)
	row.add_child(_section_list)

	var scroll := ScrollContainer.new()
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	row.add_child(scroll)

	_entries_box = VBoxContainer.new()
	_entries_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_entries_box.add_theme_constant_override("separation", 8)
	scroll.add_child(_entries_box)

	_hint = Label.new()
	_hint.add_theme_color_override("font_color", Color(INK, 0.6))
	_hint.add_theme_font_size_override("font_size", 18)
	_hint.text = "Стрелки по списку, вправо к ручкам, Enter нажимает, Esc закрывает. Мышь тоже."
	root.add_child(_hint)

	_overlay = Label.new()
	_overlay.visible = false
	_overlay.position = Vector2(16, 12)
	_overlay.add_theme_font_size_override("font_size", 22)
	_overlay.add_theme_color_override("font_color", INK)
	_overlay.add_theme_color_override("font_outline_color", BG)
	_overlay.add_theme_constant_override("outline_size", 6)
	var overlay_layer := CanvasLayer.new()
	overlay_layer.layer = 101
	overlay_layer.add_child(_overlay)
	add_child(overlay_layer)


## Компактная светлая тема меню поверх темы оболочки: мелкие кнопки, список, ползунки.
func _make_theme() -> Theme:
	var t := Theme.new()
	var normal := Style.flat(Color(INK, 0.08), 8)
	var hover := Style.flat(Color(INK, 0.14), 8)
	var pressed := Style.flat(Color(INK, 0.22), 8)
	var focus := Style.flat(Color.TRANSPARENT, 8, FOCUS)
	for cls in ["Button", "CheckButton", "OptionButton"]:
		t.set_stylebox("normal", cls, normal)
		t.set_stylebox("hover", cls, hover)
		t.set_stylebox("pressed", cls, pressed)
		t.set_stylebox("focus", cls, focus)
		for state in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
			t.set_color(state, cls, INK)
	t.set_stylebox("panel", "ItemList", Style.flat(Color(INK, 0.06), 8))
	t.set_stylebox("focus", "ItemList", focus)
	t.set_stylebox("selected", "ItemList", Style.flat(Color(INK, 0.18), 6))
	t.set_stylebox("selected_focus", "ItemList", Style.flat(FOCUS, 6))
	t.set_stylebox("hovered", "ItemList", Style.flat(Color(INK, 0.1), 6))
	t.set_color("font_color", "ItemList", INK)
	t.set_color("font_hovered_color", "ItemList", INK)
	t.set_color("font_selected_color", "ItemList", BG)
	t.set_constant("v_separation", "ItemList", 10)
	t.set_stylebox("panel", "PopupMenu", Style.flat(BG, 8))
	t.set_stylebox("hover", "PopupMenu", Style.flat(Color(INK, 0.14), 6))
	t.set_color("font_color", "PopupMenu", INK)
	t.set_color("font_hover_color", "PopupMenu", INK)
	t.set_color("font_color", "Label", INK)
	t.set_color("font_color", "HSlider", INK)
	t.set_stylebox("slider", "HSlider", Style.flat(Color(INK, 0.15), 4))
	t.set_stylebox("grabber_area", "HSlider", Style.flat(FOCUS, 4))
	t.set_stylebox("grabber_area_highlight", "HSlider", Style.flat(FOCUS, 4))
	return t


func _rebuild_sections() -> void:
	_section_list.clear()
	for s in _order:
		_section_list.add_item(String(s))
	var wanted := str(_cfg.get_value("menu", "section", String(_order[0])))
	var idx := maxi(_order.find(StringName(wanted)), 0)
	_section_list.select(idx)
	_on_section_selected(idx)


func _on_section_selected(idx: int) -> void:
	var section := _order[idx]
	_cfg.set_value("menu", "section", String(section))
	_cfg.save(CFG_PATH)
	for c in _entries_box.get_children():
		_entries_box.remove_child(c)
		c.queue_free()
	var first: Control = null
	for e: Entry in _sections[section]:
		var ctl := _make_control(section, e)
		_entries_box.add_child(ctl)
		if first == null:
			first = ctl.get_meta(&"focus_target", ctl)
	_section_list.focus_neighbor_right = first.get_path() if first != null else NodePath()


## Возвращает контрол, который получает фокус (кнопка, галка, ползунок или список).
func _make_control(section: StringName, e: Entry) -> Control:
	match e.kind:
		Kind.ACTION:
			var b := Button.new()
			b.text = e.label
			b.alignment = HORIZONTAL_ALIGNMENT_LEFT
			b.add_theme_font_size_override("font_size", 22)
			b.pressed.connect(func() -> void: e.fn.call())
			return b
		Kind.TOGGLE:
			var cb := CheckButton.new()
			cb.text = e.label
			cb.button_pressed = bool(e.getter.call())
			cb.add_theme_font_size_override("font_size", 22)
			cb.toggled.connect(func(v: bool) -> void: _apply(section, e, v))
			return cb
		Kind.NUMBER:
			var slider := HSlider.new()
			slider.min_value = e.min_value
			slider.max_value = e.max_value
			slider.step = e.step
			slider.value = float(e.getter.call())
			slider.custom_minimum_size = Vector2(400, 0)
			slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			var value_label := Label.new()
			value_label.text = str(slider.value)
			value_label.custom_minimum_size = Vector2(90, 0)
			slider.value_changed.connect(func(v: float) -> void:
				value_label.text = str(v)
				_apply(section, e, v))
			return _labeled_row(e.label, slider, value_label)
		Kind.CHOICE:
			var ob := OptionButton.new()
			for o in e.options:
				ob.add_item(str(o))
			ob.selected = maxi(e.options.find(e.getter.call()), 0)
			ob.add_theme_font_size_override("font_size", 22)
			ob.item_selected.connect(func(i: int) -> void: _apply(section, e, e.options[i]))
			return _labeled_row(e.label, ob, null)
	return Control.new()


func _labeled_row(text: String, ctl: Control, extra: Control) -> Control:
	# Строка «подпись + контрол»; фокус отдаём контролу, строка сама его не берёт.
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 16)
	var label := Label.new()
	label.text = text
	label.custom_minimum_size = Vector2(320, 0)
	label.add_theme_font_size_override("font_size", 22)
	label.add_theme_color_override("font_color", INK)
	row.add_child(label)
	row.add_child(ctl)
	if extra != null:
		row.add_child(extra)
	row.focus_mode = Control.FOCUS_NONE
	row.set_meta(&"focus_target", ctl)
	return row


func _apply(section: StringName, e: Entry, value: Variant) -> void:
	e.setter.call(value)
	if e.persist:
		_cfg.set_value("values", _key(section, e), value)
		_cfg.save(CFG_PATH)


func _flash(text: String) -> void:
	print("Debug: " + text)
	if _overlay.visible:
		return
	_overlay.text = text
	_overlay.visible = true
	await get_tree().create_timer(1.5, true).timeout
	if _overlay.text == text:
		_overlay.visible = false
