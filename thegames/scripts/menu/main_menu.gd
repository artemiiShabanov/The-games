class_name MainMenu
extends Control
## Главное меню (#71), спека `docs/specs/run.md`: в большой карточке название игры, три слота
## забегов (логотип и название студии, «Релиз N · $ X» или «пусто») и кнопки «Галерея» и
## «Выход». ← → по слотам, ↓ к кнопкам, ␣ или клик: пустой слот начинает забег, занятый
## продолжает с сохранённой фазы. R на занятом слоте: новый забег в нём, с подтверждением
## (␣ подтвердить, Esc отмена). Del на занятом слоте или клик по его пилюле «Удалить» удаляет
## сохранение, тоже с подтверждением (полировка 2026-11-17); игры забега остаются в галерее.
## Галерея профиля поверх, по Esc назад в меню.
## Под автотестом без `--menu` меню сразу открывает игру без слота, как раньше.

const GAME_PATH := "res://scenes/main.tscn"
const SLOT_SIZE := Vector2(480, 300)
const LOGO := 96.0

var focus := 0
var saves: Array[RunSave] = []
var confirming := -1
## Подтверждение на экране про удаление сохранения, а не про новый забег в слоте.
var deleting := false

var card: CardFrame
var _slots: Array[PanelContainer] = []
var _slot_lifts: Array[JellyLift] = []
var _buttons: Array[PanelContainer] = []
var _button_lifts: Array[JellyLift] = []
var _confirm: Control
## Пилюля «да» в подтверждении: удаление мышью подтверждает только клик по ней.
var _confirm_yes: Control
## Пилюли «Удалить» занятых слотов; у пустого слота `null`.
var _delete_pills: Array[Control] = []
var _slot_row: HBoxContainer
var _gallery: GalleryScreen
var _bed: MusicBed
## Нижние пилюли меню: прячутся вместе с карточкой, иначе лежат под пилюлями галереи.
var _hints: HBoxContainer
var _options: OptionsScreen
var _settings: SettingsScreen
var _leaving := false


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var args := AutoTest.parse_args(OS.get_cmdline_user_args())
	# `--scene=<id>`: тестовую сцену откроет дебаг, меню не мешает.
	if args.has("scene"):
		return
	if AutoTest.enabled:
		RunSave.test_files = true
		if not args.has("menu"):
			_open_game.call_deferred(0, null)
			return
		AutoTest.bot_mode = AutoTest.BotMode.OFF
	else:
		# Материалы «продвинутых» собираются заранее, пока игрок в меню (#130).
		ThreedScreen.prewarm(self)
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)
	# Заглавная тема Studio Running (2026-11-18); молчит, пока открыта галерея с демками.
	_bed = MusicBed.main(Music.tuning().menu_db)
	add_child(_bed)
	# Первый запуск (2026-11-18): сначала язык, меню после выбора. Автотест: `--first-launch`.
	if (Options.language == "" and not AutoTest.enabled) or (AutoTest.enabled and args.has("first-launch")):
		_leaving = true
		var picker := LanguageScreen.new()
		add_child(picker)
		await picker.chosen
		picker.queue_free()
		_leaving = false
	for i in RunSave.SLOTS:
		saves.append(RunSave.load_slot(i + 1))
	ShellHeader.studio = ""
	_build()
	_refresh()
	card.raise_card()
	# Автотест `--menu --settings`: экран сеттингов поверх меню.
	if AutoTest.enabled and args.has("settings"):
		_open_settings.call_deferred()


func _process(_delta: float) -> void:
	if _bed != null:
		_bed.active = _gallery == null


func _open_game(slot: int, save: RunSave) -> void:
	Main.slot = slot
	Main.pending = save
	get_tree().change_scene_to_file(GAME_PATH)


# --- Ввод -------------------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	# Выбор может синхронно увести экран из дерева, поэтому вьюпорт берётся заранее.
	var viewport := get_viewport()
	if _leaving or _gallery != null or _options != null or _settings != null:
		return
	if event is InputEventMouseMotion:
		var over := _item_at(event)
		if over >= 0 and over != focus and confirming < 0:
			focus = over
			ShellSounds.play(&"tick")
			_refresh()
		return
	if MouseUi.is_click(event):
		var at := _item_at(event)
		var del := _delete_at(event)
		if confirming >= 0:
			_confirm_new(not deleting or MouseUi.hit(_confirm_yes, event))
		elif del >= 0:
			focus = del
			_refresh()
			ask_delete(del)
		elif at >= 0:
			focus = at
			activate()
		MouseUi.consume(viewport)
		return
	if event.is_echo():
		return
	var key := event as InputEventKey
	var esc := key != null and key.pressed and key.keycode == KEY_ESCAPE
	if confirming >= 0:
		if GameInput.is_a(event):
			_confirm_new(true)
		elif esc or GameInput.is_b(event):
			_confirm_new(false)
		MouseUi.consume(viewport)
		return
	if key != null and key.pressed and key.keycode == KEY_R:
		ask_new(focus)
	elif key != null and key.pressed and key.keycode in [KEY_DELETE, KEY_BACKSPACE]:
		ask_delete(focus)
	elif event.is_action_pressed(GameInput.LEFT):
		move(-1)
	elif event.is_action_pressed(GameInput.RIGHT):
		move(1)
	elif event.is_action_pressed(GameInput.DOWN):
		_set_focus(RunSave.SLOTS if focus < RunSave.SLOTS else focus)
	elif event.is_action_pressed(GameInput.UP):
		_set_focus(0 if focus >= RunSave.SLOTS else focus)
	elif GameInput.is_a(event):
		activate()
	else:
		return
	MouseUi.consume(viewport)


## Слот, по пилюле «Удалить» которого пришёлся клик, или -1.
func _delete_at(event: InputEvent) -> int:
	for i in _delete_pills.size():
		if _delete_pills[i] != null and MouseUi.hit(_delete_pills[i], event):
			return i
	return -1


func _item_at(event: InputEvent) -> int:
	for i in _slots.size():
		if MouseUi.hit(_slots[i], event):
			return i
	for i in _buttons.size():
		if MouseUi.hit(_buttons[i], event):
			return RunSave.SLOTS + i
	return -1


func move(dir: int) -> void:
	var count := RunSave.SLOTS + _buttons.size()
	var lo := 0 if focus < RunSave.SLOTS else RunSave.SLOTS
	var hi := RunSave.SLOTS - 1 if focus < RunSave.SLOTS else count - 1
	_set_focus(clampi(focus + dir, lo, hi))


func _set_focus(i: int) -> void:
	if i == focus:
		return
	focus = i
	ShellSounds.play(&"tick")
	_refresh()


## ␣ на пункте: слот (продолжить или новый забег), галерея, выход.
func activate() -> void:
	if focus < RunSave.SLOTS:
		_leaving = true
		ShellSounds.play(&"done")
		_slot_lifts[focus].press()
		await card.drop_card()
		_open_game(focus + 1, saves[focus])
	elif focus == RunSave.SLOTS:
		_open_gallery()
	elif focus == RunSave.SLOTS + 1:
		_open_settings()
	elif focus == RunSave.SLOTS + 2:
		_open_options()
	else:
		ShellSounds.play(&"tick")
		get_tree().quit()


## R: новый забег в занятом слоте, с подтверждением; в пустом слоте сразу.
func ask_new(i: int) -> void:
	if i >= RunSave.SLOTS:
		return
	if saves[i] == null:
		activate()
		return
	confirming = i
	deleting = false
	_confirm = _make_confirm(i)
	add_child(_confirm)
	ShellSounds.play(&"intro")


## Del или пилюля «Удалить»: стереть сохранение слота, с подтверждением. Пустой слот не трогает.
func ask_delete(i: int) -> void:
	if i < 0 or i >= RunSave.SLOTS or saves[i] == null:
		return
	confirming = i
	deleting = true
	_confirm = _make_confirm(i)
	add_child(_confirm)
	ShellSounds.play(&"intro")


func _confirm_new(yes: bool) -> void:
	var i := confirming
	var delete_only := deleting
	confirming = -1
	deleting = false
	if _confirm != null:
		_confirm.queue_free()
		_confirm = null
		_confirm_yes = null
	if not yes:
		ShellSounds.play(&"tick")
		return
	RunSave.delete_slot(i + 1)
	saves[i] = null
	focus = i
	if delete_only:
		AutoTest.note("menu: сохранение слота %d удалено, файл %s" % [i + 1, "остался" if RunSave.exists(i + 1) else "стёрт"])
		ShellSounds.play(&"done")
		_rebuild_slot(i)
		_refresh()
		return
	_refresh()
	activate()


## Слот заново после удаления сохранения: на месте занятого встаёт пустой.
func _rebuild_slot(i: int) -> void:
	var old := _slots[i]
	var fresh := _make_slot(i)
	_slot_row.add_child(fresh)
	_slot_row.move_child(fresh, old.get_index())
	_slot_row.remove_child(old)
	old.queue_free()
	_slots[i] = fresh
	_slot_lifts[i] = Jelly.button(fresh, float(Style.R_CARD))
	MouseUi.pass_through(fresh)


func _open_gallery() -> void:
	ShellSounds.play(&"done")
	card.visible = false
	_hints.visible = false
	_gallery = GalleryScreen.new()
	var profile := Profile.load_saved()
	_gallery.setup(profile.gallery, profile.runs)
	_gallery.closed.connect(func() -> void:
		_gallery.queue_free()
		_gallery = null
		card.visible = true
		_hints.visible = true
		card.raise_card())
	add_child(_gallery)


## Сеттинги и достижения (#139) поверх меню.
func _open_settings() -> void:
	ShellSounds.play(&"done")
	_hints.visible = false
	_settings = SettingsScreen.new()
	_settings.setup(Profile.load_saved())
	_settings.closed.connect(func() -> void:
		_settings.queue_free()
		_settings = null
		_hints.visible = true)
	add_child(_settings)


## Настройки (#81) поверх меню; меню ждёт, пока их закроют.
func _open_options() -> void:
	ShellSounds.play(&"done")
	_hints.visible = false
	_options = OptionsScreen.new()
	_options.closed.connect(func() -> void:
		_options.queue_free()
		_options = null
		_hints.visible = true)
	_options.language_changed.connect(_rebuild)
	add_child(_options)


## Язык сменился в настройках: меню заново, подписи с подстановкой переводятся при сборке.
func _rebuild() -> void:
	card.queue_free()
	_hints.queue_free()
	_slots.clear()
	_slot_lifts.clear()
	_buttons.clear()
	_button_lifts.clear()
	_delete_pills.clear()
	_build()
	_hints.visible = false
	move_child(_options, -1)
	_refresh()
	card.raise_card(false)


# --- Построение ---------------------------------------------------------------------------------

func _build() -> void:
	card = CardFrame.new()
	add_child(card)
	var inner := CardFrame.inner_size()
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 24)
	column.size = inner
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.content.add_child(column)
	var logo := GameLogo.new()
	logo.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	var head := VBoxContainer.new()
	head.add_theme_constant_override("separation", 4)
	head.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(head)
	head.add_child(logo)
	# Подпись автора под логотипом, с тем же отступом слева, что у букв.
	var by := MarginContainer.new()
	by.add_theme_constant_override("margin_left", int(logo.inset) + 6)
	by.mouse_filter = Control.MOUSE_FILTER_IGNORE
	by.add_child(_label("A game by Artemii Shabanov", Style.FONT_H2, Style.INK_2))
	head.add_child(by)
	var filler := Control.new()
	filler.size_flags_vertical = Control.SIZE_EXPAND_FILL
	filler.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(filler)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", Style.GAP_CARDS)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(row)
	_slot_row = row
	_delete_pills.resize(RunSave.SLOTS)
	for i in RunSave.SLOTS:
		var s := _make_slot(i)
		row.add_child(s)
		_slots.append(s)
		_slot_lifts.append(Jelly.button(s, float(Style.R_CARD)))
	var buttons := HBoxContainer.new()
	buttons.add_theme_constant_override("separation", Style.GAP_CARDS)
	buttons.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(buttons)
	for text in ["Галерея", "Сеттинги", "Настройки", "Выход"]:
		var b := PanelContainer.new()
		b.custom_minimum_size = Vector2(300, Style.BUTTON_HEIGHT)
		b.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var l := _label(text, Style.FONT_H2, Style.INK)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		b.add_child(l)
		buttons.add_child(b)
		_buttons.append(b)
		_button_lifts.append(Jelly.button(b))

	var hints := HBoxContainer.new()
	hints.alignment = BoxContainer.ALIGNMENT_CENTER
	hints.add_theme_constant_override("separation", 16)
	hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hints.offset_top = -(Style.PILL_HEIGHT + Style.HINTS_BOTTOM)
	hints.offset_bottom = -Style.HINTS_BOTTOM
	hints.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hints.add_child(HintPill.make("← → ↑ ↓ выбрать"))
	hints.add_child(HintPill.make(GameInput.hint(GameInput.A, tr("открыть"))))
	hints.add_child(HintPill.make("R новый забег в слоте"))
	hints.add_child(HintPill.make("Del удалить сохранение"))
	add_child(hints)
	_hints = hints
	MouseUi.pass_through(self)


## Слот: «Слот N», логотип и название студии, релиз и деньги; пустой: «пусто · Новый забег».
func _make_slot(i: int) -> PanelContainer:
	var s := saves[i]
	var p := PanelContainer.new()
	var w := floorf((CardFrame.inner_size().x - (RunSave.SLOTS - 1) * Style.GAP_CARDS) / RunSave.SLOTS)
	p.custom_minimum_size = Vector2(w, SLOT_SIZE.y)
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sb := Style.flat(Style.SURFACE_2, Style.R_CARD, Color.TRANSPARENT, 0)
	sb.content_margin_left = 28
	sb.content_margin_right = 28
	sb.content_margin_top = 24
	sb.content_margin_bottom = 24
	p.add_theme_stylebox_override("panel", sb)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 10)
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.add_child(col)
	var top := HBoxContainer.new()
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_child(top)
	var slot_label := _slot_label(_label(tr("Слот %d") % (i + 1), Style.FONT_CAPTION, Style.INK_3))
	slot_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(slot_label)
	_delete_pills[i] = null
	if s != null:
		var del := PanelContainer.new()
		var dsb := Style.flat(Style.SURFACE_SOLID, Style.R_PILL, Color.TRANSPARENT, 0)
		dsb.content_margin_left = 14
		dsb.content_margin_right = 14
		dsb.content_margin_top = 2
		dsb.content_margin_bottom = 2
		del.add_theme_stylebox_override("panel", dsb)
		del.add_child(_label("Удалить", Style.FONT_CAPTION, Style.INK_2))
		top.add_child(del)
		Jelly.attach_pill(del)
		_delete_pills[i] = del
	if s == null:
		var f := Control.new()
		f.size_flags_vertical = Control.SIZE_EXPAND_FILL
		f.mouse_filter = Control.MOUSE_FILTER_IGNORE
		col.add_child(f)
		col.add_child(_slot_label(_label("пусто", Style.FONT_H2, Style.INK_3)))
		col.add_child(_slot_label(_label("Пустой слот", Style.FONT_BODY, Style.INK_2)))
		return p
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 16)
	head.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_child(head)
	var logo := RunSave.logo_from_dict(s.logo)
	if logo != null:
		var view := StudioLogoView.new()
		view.custom_minimum_size = Vector2(LOGO, LOGO)
		view.set_logo(logo, false)
		head.add_child(view)
	var name_label := _slot_label(_label(s.studio_name, 30, Style.INK))
	name_label.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	name_label.add_theme_font_override("font", Jelly.fun_font(800))
	name_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	head.add_child(name_label)
	var f2 := Control.new()
	f2.size_flags_vertical = Control.SIZE_EXPAND_FILL
	f2.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_child(f2)
	col.add_child(_slot_label(_label(tr("Релиз %d") % s.release, Style.FONT_H2, Style.INK)))
	var money := _slot_label(_label(Style.format_money(s.cash), Style.FONT_BODY, Style.DANGER if s.cash < 0 else Style.MONEY))
	money.add_theme_font_override("font", Style.mono_font())
	col.add_child(money)
	return p


func _make_confirm(i: int) -> Control:
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var dim := ColorRect.new()
	dim.color = Color(Style.BG, 0.9)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(center)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.card(true))
	panel.custom_minimum_size = Vector2(760, 0)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	center.add_child(panel)
	Jelly.panel(panel)
	Jelly.cover(root)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 16)
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(col)
	col.add_child(_label((tr("Удалить сохранение в слоте %d?") if deleting else tr("Новый забег в слоте %d?")) % (i + 1),
			Style.FONT_H1, Style.INK))
	var text := _label((tr("Сохранение студии «%s» будет удалено. Игры останутся в галерее.") if deleting
			else tr("Студия «%s» будет закрыта. Игры останутся в галерее.")) % saves[i].studio_name,
			Style.FONT_BODY, Style.INK_2)
	text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	col.add_child(text)
	var hint := HBoxContainer.new()
	hint.add_theme_constant_override("separation", 16)
	_confirm_yes = HintPill.make(GameInput.hint(GameInput.A, tr("удалить") if deleting else tr("начать заново")))
	hint.add_child(_confirm_yes)
	hint.add_child(HintPill.make("Esc отмена"))
	col.add_child(hint)
	return root


func _refresh() -> void:
	for i in _slots.size():
		var slot_on := focus == i
		_slot_lifts[i].focused = slot_on
		# Фокус слота тёмной подложкой, как у кнопок; текст инвертируется.
		var sb := _slots[i].get_theme_stylebox("panel") as StyleBoxFlat
		sb.bg_color = Style.INK if slot_on else Style.SURFACE_2
		for l: Label in _slots[i].find_children("*", "Label", true, false):
			if l.has_meta(&"ink"):
				var c: Color = l.get_meta(&"ink")
				l.add_theme_color_override("font_color", _on_ink(c) if slot_on else c)
	for i in _buttons.size():
		var on := focus == RunSave.SLOTS + i
		_buttons[i].add_theme_stylebox_override("panel", Style.flat(Style.INK if on else Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 0))
		(_buttons[i].get_child(0) as Label).add_theme_color_override("font_color", Style.SURFACE_SOLID if on else Style.INK)
		_button_lifts[i].focused = on
	if focus < _slots.size():
		Jelly.poke(_slots[focus])


## Подпись слота: цвет запоминается, на тёмной подложке фокуса он меняется (`_on_ink`).
func _slot_label(l: Label) -> Label:
	l.set_meta(&"ink", l.get_theme_color("font_color"))
	return l


## Цвет текста слота на тёмной подложке фокуса.
static func _on_ink(c: Color) -> Color:
	if c == Style.INK:
		return Style.SURFACE_SOLID
	if c == Style.INK_2:
		return Style.SURFACE_2
	if c == Style.INK_3:
		return Style.INK_2.lightened(0.25)
	return c.lightened(0.45)


func _label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l
