class_name GalleryScreen
extends Control
## Галерея (#70), спека `docs/specs/run.md`. Две вкладки в большой карточке, обе вертикальным
## списком с прокруткой (плейтест 2026-11-11: список вместо сетки по четыре).
## - «Игры»: все выпущенные игры всех забегов из профиля (`Profile.gallery`). Строка: полоски
##   цветов тройки, тройка словами, название, критики, «вирусная», баги штампами, «Забег N ·
##   релиз M · студия», справа кадр демки с плейтеста (`GalleryEntry.shot`; без кадра заглушка
##   цвета жанра). ␣ или клик по выбранной запускает демку с тем же сидом и багами
##   (полноэкранную, как в ленте), по её концу галерея возвращается на ту же строку. R меняет
##   сортировку: по забегам (новые сверху, внутри по релизам) и по критикам.
## - «Студии»: забеги, новые сверху. Строка: логотип, название студии, концовка с оценкой
##   (незаконченный забег: «в пути»), релизов, лучшая игра, средние критики, вирусных.
##   Источник: законченные забеги профиля (`Profile.runs`) и игры галереи по номеру забега.
## ↑ ↓ и наведение мыши выбирают, колесо и тачпад листают, ← → или клик по пилюле вкладки
## меняют вкладку. Esc или B закрывают (`closed`). Пустая вкладка: одна подпись.

signal closed
signal demo_opened(entry: GalleryEntry)

enum Sort { RUNS, CRITICS }
enum Tab { GAMES, STUDIOS }

const ROW_HEIGHT := 200
const STUDIO_ROW_HEIGHT := 140
const SHOT := Vector2(320, 180)
const STRIPE := 10
const ROW_GAP := 20
const BOT_SECONDS := 0.6

var entries: Array[GalleryEntry] = []
## Строки вкладки «Студии»: `run`, `studio`, `logo`, `ending`, `score`, `releases`, `games`,
## `best`, `best_critics`, `avg_critics`, `viral`.
var studios: Array[Dictionary] = []
var sort := Sort.RUNS
var tab := Tab.GAMES
var index := 0
var playing := false

var card: CardFrame
var _scroll: ScrollContainer
var _list: VBoxContainer
var _empty: Label
var _rows: Array[PanelContainer] = []
var _lifts: Array[JellyLift] = []
var _sort_pill: Control
var _sort_label: Label
var _tabs: Array[PanelContainer] = []
var _tab_labels: Array[Label] = []
var _header_label: Label
var _sort_hint: Control
var _play_hint: Control
var _catalogs: Array[Catalog] = []
var _bugs: BugCatalog
var _demo: Demo
var _closing := false
var _bot_timer := 0.0
var _bot_played := false
var _runs: Array[Dictionary] = []
var _fade: EdgeFade


func setup(entries_: Array[GalleryEntry], runs_: Array[Dictionary] = []) -> void:
	entries = entries_.duplicate()
	_runs = runs_.duplicate()


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	for k in [CatalogEntry.Kind.GENRE, CatalogEntry.Kind.TECH, CatalogEntry.Kind.SETTING]:
		_catalogs.append(Catalog.load_kind(k))
	_bugs = BugCatalog.load_default()
	_sort_entries()
	studios = build_studios(entries, _runs)
	_build()
	card.raise_card()


func sorted() -> Array[GalleryEntry]:
	return entries


func count() -> int:
	return entries.size() if tab == Tab.GAMES else studios.size()


func _sort_entries() -> void:
	if sort == Sort.RUNS:
		entries.sort_custom(func(a: GalleryEntry, b: GalleryEntry) -> bool:
			return a.run_number > b.run_number or (a.run_number == b.run_number and a.release < b.release))
	else:
		entries.sort_custom(func(a: GalleryEntry, b: GalleryEntry) -> bool:
			return a.critics > b.critics or (a.critics == b.critics and a.run_number > b.run_number))


## Забеги для вкладки «Студии»: законченные из профиля и все, у кого есть игры в галерее,
## новые сверху.
static func build_studios(games: Array[GalleryEntry], runs: Array[Dictionary]) -> Array[Dictionary]:
	var by_run := {}
	for r in runs:
		var n := int(r.get("run", 0))
		by_run[n] = {"run": n, "studio": str(r.get("studio", "")), "logo": r.get("logo", {}),
				"ending": StringName(str(r.get("ending", ""))), "score": int(r.get("score", 0)),
				"releases": int(r.get("releases", 0)), "games": 0, "best": "", "best_critics": -1.0,
				"sum_critics": 0.0, "viral": 0}
	for e in games:
		if not by_run.has(e.run_number):
			by_run[e.run_number] = {"run": e.run_number, "studio": e.studio, "logo": {}, "ending": &"",
					"score": 0, "releases": 0, "games": 0, "best": "", "best_critics": -1.0, "sum_critics": 0.0,
					"viral": 0}
		var d: Dictionary = by_run[e.run_number]
		d["games"] = int(d["games"]) + 1
		d["sum_critics"] = float(d["sum_critics"]) + e.critics
		if e.viral:
			d["viral"] = int(d["viral"]) + 1
		if e.critics > float(d["best_critics"]):
			d["best_critics"] = e.critics
			d["best"] = e.title
		if str(d["studio"]) == "":
			d["studio"] = e.studio
	var out: Array[Dictionary] = []
	for k in by_run:
		var d: Dictionary = by_run[k]
		d["releases"] = maxi(int(d["releases"]), int(d["games"]))
		d["avg_critics"] = float(d["sum_critics"]) / int(d["games"]) if int(d["games"]) > 0 else 0.0
		out.append(d)
	out.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return int(a["run"]) > int(b["run"]))
	return out


# --- Ввод ------------------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	# Выбор может синхронно увести экран из дерева, поэтому вьюпорт берётся заранее.
	var viewport := get_viewport()
	if playing or _closing:
		return
	if event is InputEventMouseMotion:
		var over := _row_at(event)
		if over >= 0 and over != index:
			focus(over, false)
		return
	if MouseUi.is_mouse(event):
		var px := MouseUi.scroll_px(event)
		if px != 0.0:
			if _scroll != null:
				_scroll.scroll_vertical += int(px)
			MouseUi.consume(viewport)
		elif MouseUi.is_click(event):
			for t in _tabs.size():
				if MouseUi.hit(_tabs[t], event):
					set_tab(t as Tab)
					MouseUi.consume(viewport)
					return
			if _sort_pill != null and _sort_pill.visible and MouseUi.hit(_sort_pill, event):
				toggle_sort()
				MouseUi.consume(viewport)
				return
			var at := _row_at(event)
			if at >= 0:
				focus(at, false)
				play()
				MouseUi.consume(viewport)
		return
	if event.is_echo() and not (event.is_action(GameInput.UP) or event.is_action(GameInput.DOWN)):
		return
	var key := event as InputEventKey
	if key != null and key.pressed and not key.echo and key.keycode == KEY_R:
		toggle_sort()
	elif key != null and key.pressed and key.keycode == KEY_ESCAPE or GameInput.is_b(event):
		close()
	elif event.is_action_pressed(GameInput.LEFT):
		set_tab(Tab.GAMES)
	elif event.is_action_pressed(GameInput.RIGHT):
		set_tab(Tab.STUDIOS)
	elif event.is_action_pressed(GameInput.UP, true):
		focus(index - 1)
	elif event.is_action_pressed(GameInput.DOWN, true):
		focus(index + 1)
	elif GameInput.is_a(event):
		play()
	else:
		return
	MouseUi.consume(viewport)


func _row_at(event: InputEvent) -> int:
	if _scroll == null or not MouseUi.hit(_scroll, event):
		return -1
	for i in _rows.size():
		if MouseUi.hit(_rows[i], event):
			return i
	return -1


func focus(i: int, scroll := true) -> void:
	if count() == 0:
		return
	i = clampi(i, 0, count() - 1)
	if i == index:
		return
	index = i
	ShellSounds.play(&"tick")
	_refresh_focus()
	if scroll:
		_scroll_to(i)


func set_tab(t: Tab) -> void:
	if t == tab:
		return
	tab = t
	index = 0
	ShellSounds.play(&"tick")
	_fill()
	if _scroll != null:
		_scroll.scroll_vertical = 0


func toggle_sort() -> void:
	if tab != Tab.GAMES:
		return
	var current: GalleryEntry = entries[index] if not entries.is_empty() else null
	sort = Sort.CRITICS if sort == Sort.RUNS else Sort.RUNS
	_sort_entries()
	ShellSounds.play(&"tick")
	_fill()
	index = maxi(entries.find(current), 0)
	_refresh_focus()
	_scroll_to(index)


## Демка выбранной игры: тот же сид и те же баги, полноэкранная, по концу назад в галерею.
## На вкладке студий ␣ только вздрагивает строкой.
func play() -> void:
	if tab == Tab.STUDIOS:
		if index < _rows.size():
			Jelly.poke(_rows[index], -1.0)
		return
	if entries.is_empty() or playing:
		if entries.is_empty():
			ShellSounds.play(&"miss")
		return
	var e := entries[index]
	var record := e.to_record()
	_demo = DemoCatalog.create(record)
	if _demo == null:
		Jelly.poke(_rows[index], -2.0)
		ShellSounds.play(&"miss")
		return
	playing = true
	_lifts[index].press()
	ShellSounds.play(&"done")
	card.visible = false
	_demo.setup(record, &"gallery")
	_demo.demo_finished.connect(_on_demo_finished)
	add_child(_demo)
	_demo.start()
	demo_opened.emit(e)


func _on_demo_finished(_r: GameRecord, _reached: bool) -> void:
	if _demo != null:
		_demo.queue_free()
		_demo = null
	playing = false
	card.visible = true
	_refresh_focus()


func close() -> void:
	if _closing:
		return
	_closing = true
	ShellSounds.play(&"tick")
	await card.drop_card()
	closed.emit()


## Бот автотеста: открывает демку выбранной игры (если есть), затем закрывает галерею.
func _process(delta: float) -> void:
	if not AutoTest.bot_active() or playing or _closing:
		return
	_bot_timer += delta
	if _bot_timer < BOT_SECONDS:
		return
	_bot_timer = 0.0
	if not _bot_played and not entries.is_empty():
		_bot_played = true
		play()
	else:
		close()


# --- Построение ----------------------------------------------------------------------------

func _build() -> void:
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 12)
	head.position = Vector2(Style.EDGE, Style.HEADER_Y - Style.PILL_HEIGHT / 2.0 - 8)
	head.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(head)
	var title := HintPill.header(ShellHeader.text("Галерея"))
	title.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(title)
	_header_label = title.get_child(0) as Label
	for t in 2:
		var p := PanelContainer.new()
		p.custom_minimum_size = Vector2(0, Style.PILL_HEIGHT + 16)
		var l := _label("", Style.FONT_BODY, Style.INK)
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		p.add_child(l)
		head.add_child(p)
		_tabs.append(p)
		_tab_labels.append(l)
	_tab_labels[0].text = "Игры · %d" % entries.size()
	_tab_labels[1].text = "Студии · %d" % studios.size()

	var right := HBoxContainer.new()
	right.alignment = BoxContainer.ALIGNMENT_END
	right.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	right.offset_left = Style.EDGE
	right.offset_right = -Style.EDGE
	right.offset_top = Style.HEADER_Y - Style.PILL_HEIGHT / 2.0
	right.offset_bottom = right.offset_top + Style.PILL_HEIGHT
	right.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(right)
	_sort_pill = HintPill.header("")
	_sort_label = _sort_pill.get_child(0) as Label
	right.add_child(_sort_pill)

	card = CardFrame.new()
	add_child(card)
	var inner := CardFrame.inner_size()
	_scroll = ScrollContainer.new()
	_scroll.size = inner
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	card.content.add_child(_scroll)
	var margin := MarginContainer.new()
	for side in ["top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 12)
	for side in ["left", "right"]:
		margin.add_theme_constant_override("margin_" + side, 4)
	margin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_scroll.add_child(margin)
	_list = VBoxContainer.new()
	_list.add_theme_constant_override("separation", ROW_GAP)
	_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	margin.add_child(_list)
	# Края списка растворяются, как в карусели конструктора (плейтест 2026-11-11).
	_fade = EdgeFade.attach(_scroll)
	_empty = _label("", Style.FONT_H2, Style.INK_2)
	_empty.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_empty.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_empty.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_empty.size = inner
	card.content.add_child(_empty)

	var hints := HBoxContainer.new()
	hints.alignment = BoxContainer.ALIGNMENT_CENTER
	hints.add_theme_constant_override("separation", 16)
	hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hints.offset_top = -(Style.PILL_HEIGHT + 16)
	hints.offset_bottom = -16
	hints.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hints.add_child(HintPill.make("↑ ↓ выбрать"))
	hints.add_child(HintPill.make("← → вкладка"))
	_play_hint = HintPill.make(GameInput.hint(GameInput.A, "запустить"))
	hints.add_child(_play_hint)
	_sort_hint = HintPill.make("R сортировка")
	hints.add_child(_sort_hint)
	hints.add_child(HintPill.make("Esc назад"))
	add_child(hints)
	_fill()
	MouseUi.pass_through(self)


## Строки текущей вкладки заново; шапка, пилюли вкладок и подсказки под неё.
func _fill() -> void:
	var games := tab == Tab.GAMES
	_sort_label.text = "по забегам" if sort == Sort.RUNS else "по критикам"
	_sort_pill.visible = games and not entries.is_empty()
	_sort_hint.visible = games and not entries.is_empty()
	_play_hint.visible = games and not entries.is_empty()
	for t in _tabs.size():
		var on := t == int(tab)
		var sb := Style.flat(Style.INK if on else Style.SURFACE_SOLID, Style.R_PILL, Color.TRANSPARENT, 0)
		sb.content_margin_left = 24
		sb.content_margin_right = 24
		_tabs[t].add_theme_stylebox_override("panel", sb)
		_tab_labels[t].add_theme_color_override("font_color", Style.SURFACE_SOLID if on else Style.INK)
	for c in _list.get_children():
		_list.remove_child(c)
		c.queue_free()
	_rows.clear()
	_lifts.clear()
	var w := CardFrame.inner_size().x - 8
	if games:
		for e in entries:
			_add_row(_game_row(e, w))
	else:
		for d in studios:
			_add_row(_studio_row(d, w))
	_empty.visible = count() == 0
	_empty.text = "Пока пусто. Выпусти игру, и она поселится здесь навсегда, со всеми своими багами." if games \
			else "Ни одной студии. Самое время основать первую."
	MouseUi.pass_through(_list)
	if _fade != null:
		_fade.refresh()
	_refresh_focus()


func _add_row(c: PanelContainer) -> void:
	_list.add_child(c)
	_rows.append(c)
	var lift := Jelly.button(c, float(Style.R_CARD))
	# Строка студии не нажимается: бортик бледный, как у поста ленты.
	lift.neutral = tab == Tab.STUDIOS
	_lifts.append(lift)


func _row_panel(w: float, h: float) -> PanelContainer:
	var c := PanelContainer.new()
	c.custom_minimum_size = Vector2(w, h)
	var sb := Style.flat(Style.SURFACE_2, Style.R_CARD, Color.TRANSPARENT, 0)
	sb.content_margin_left = 28
	sb.content_margin_right = 10
	sb.content_margin_top = 10
	sb.content_margin_bottom = 10
	c.add_theme_stylebox_override("panel", sb)
	return c


## Строка игры: слева полоски тройки, тройка словами, название, критики и штампы, забег;
## справа кадр демки.
func _game_row(e: GalleryEntry, w: float) -> PanelContainer:
	var c := _row_panel(w, ROW_HEIGHT)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 28)
	c.add_child(h)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 8)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	h.add_child(col)
	var stripes := HBoxContainer.new()
	stripes.add_theme_constant_override("separation", 6)
	stripes.custom_minimum_size = Vector2(240, 0)
	stripes.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	col.add_child(stripes)
	var values := [int(e.genre), int(e.tech), int(e.setting)]
	var names: PackedStringArray = []
	for k in 3:
		var entry := _catalogs[k].by_value(values[k])
		var bar := Panel.new()
		bar.custom_minimum_size = Vector2(0, STRIPE)
		bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		bar.add_theme_stylebox_override("panel", Style.flat(entry.color if entry != null else Style.INK_3, Style.R_PILL, Color.TRANSPARENT, 0))
		stripes.add_child(bar)
		names.append(entry.title if entry != null else "?")
	col.add_child(_label(" × ".join(names), Style.FONT_CAPTION, Style.INK_2))
	var title := _label(e.title, Style.FONT_H2, Style.INK)
	title.add_theme_font_override("font", Jelly.fun_font(800))
	title.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	title.clip_text = true
	col.add_child(title)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	col.add_child(row)
	var critics := _label("%.1f" % e.critics, Style.FONT_H2, Style.INK)
	critics.add_theme_font_override("font", Style.mono_font())
	row.add_child(critics)
	if e.viral:
		row.add_child(_pill("вирусная", Style.TINT_PLUS, Style.MONEY, 0.0))
	for id in e.bug_ids:
		var bug := _bugs.by_id(id)
		row.add_child(_pill(bug.stamp_for(e.genre, e.tech) if bug != null else String(id), Style.BUG, Style.SURFACE_SOLID, -4.0))
	col.add_child(_label("Забег %d · релиз %d%s" % [e.run_number, e.release, (" · «%s»" % e.studio) if e.studio != "" else ""],
			Style.FONT_CAPTION, Style.INK_3))
	h.add_child(_shot_view(e))
	return c


## Кадр демки 16:9; файла нет: заглушка цвета жанра с технологией.
func _shot_view(e: GalleryEntry) -> Control:
	var frame := PanelContainer.new()
	frame.custom_minimum_size = SHOT
	frame.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	frame.clip_contents = true
	var genre := _catalogs[0].by_value(int(e.genre))
	var color := genre.color if genre != null else Style.INK_3
	frame.add_theme_stylebox_override("panel", Style.flat(color, Style.R_CTL, Color.TRANSPARENT, 0))
	var tex := _load_shot(e.shot)
	if tex != null:
		var r := TextureRect.new()
		r.texture = tex
		r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		r.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
		r.custom_minimum_size = SHOT
		r.mouse_filter = Control.MOUSE_FILTER_IGNORE
		frame.add_child(r)
	else:
		var l := _label(Game.tech_name(e.tech), Style.FONT_H2, Color(Style.SURFACE_SOLID, 0.7))
		l.add_theme_font_override("font", Jelly.fun_font(800))
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		frame.add_child(l)
	return frame


static func _load_shot(path: String) -> Texture2D:
	if path == "" or not FileAccess.file_exists(path):
		return null
	var img := Image.load_from_file(path)
	if img == null or img.is_empty():
		return null
	return ImageTexture.create_from_image(img)


## Строка студии: логотип, название, концовка с оценкой, релизы, лучшая игра.
func _studio_row(d: Dictionary, w: float) -> PanelContainer:
	var c := _row_panel(w, STUDIO_ROW_HEIGHT)
	var sb := c.get_theme_stylebox("panel") as StyleBoxFlat
	sb.content_margin_right = 28
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 24)
	c.add_child(h)
	var logo_dict: Dictionary = d.get("logo", {})
	var logo := StudioLogoView.new()
	logo.custom_minimum_size = Vector2(80, 80)
	logo.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	logo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if not logo_dict.is_empty():
		logo.set_logo(RunSave.logo_from_dict(logo_dict), false)
	else:
		logo.set_logo(StudioLogo.new(), false)
	h.add_child(logo)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 6)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	h.add_child(col)
	var name_ := str(d["studio"]) if str(d["studio"]) != "" else "Студия без вывески"
	var title := _label(name_, Style.FONT_H2, Style.INK)
	title.add_theme_font_override("font", Jelly.fun_font(800))
	col.add_child(title)
	var games := int(d["games"])
	var line := "Забег %d · релизов %d" % [int(d["run"]), int(d["releases"])]
	if games > 0:
		line += " · критики в среднем %.1f" % float(d["avg_critics"])
	if int(d["viral"]) > 0:
		line += " · вирусных %d" % int(d["viral"])
	col.add_child(_label(line, Style.FONT_BODY, Style.INK_2))
	if str(d["best"]) != "":
		col.add_child(_label("Лучшая: «%s», %.1f" % [str(d["best"]), float(d["best_critics"])], Style.FONT_CAPTION, Style.INK_3))
	var right := VBoxContainer.new()
	right.alignment = BoxContainer.ALIGNMENT_CENTER
	h.add_child(right)
	var ending: StringName = d["ending"]
	var k := Endings.KEYS.find(ending)
	if k >= 0:
		var bad := ending == &"bankruptcy"
		right.add_child(_pill(Endings.NAMES[k], Style.TINT_MINUS if bad else Style.TINT_PLUS, Style.DANGER if bad else Style.MONEY, 0.0, Style.FONT_BODY))
		var score := _label("оценка %d" % int(d["score"]), Style.FONT_CAPTION, Style.INK_2)
		score.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		right.add_child(score)
	else:
		# Без концовки: последний забег ещё идёт, более ранний брошен.
		var latest := studios.is_empty() or int(d["run"]) >= int(studios[0]["run"])
		right.add_child(_pill("в пути" if latest else "не закончен", Style.SURFACE_SOLID, Style.INK_2, 0.0, Style.FONT_BODY))
	return c


func _pill(text: String, bg: Color, ink: Color, degrees: float, font_size := 16) -> Control:
	var p := PanelContainer.new()
	var sb := Style.flat(bg, Style.R_PILL, Color.TRANSPARENT, 0)
	sb.content_margin_left = 14
	sb.content_margin_right = 14
	sb.content_margin_top = 2
	sb.content_margin_bottom = 2
	p.add_theme_stylebox_override("panel", sb)
	p.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	p.add_child(_label(text, font_size, ink))
	p.rotation_degrees = degrees
	return p


func _refresh_focus() -> void:
	for i in _lifts.size():
		_lifts[i].focused = i == index
	if index < _rows.size():
		Jelly.poke(_rows[index])


func _scroll_to(i: int) -> void:
	if _scroll == null or i >= _rows.size():
		return
	var h := ROW_HEIGHT if tab == Tab.GAMES else STUDIO_ROW_HEIGHT
	var top := 12 + i * (h + ROW_GAP)
	var view := _scroll.size.y
	var target := _scroll.scroll_vertical
	if top - 12 < target:
		target = top - 12
	elif top + h + 24 > target + view:
		target = int(top + h + 24 - view)
	create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC).tween_property(_scroll, "scroll_vertical", target, Style.FOCUS_MOVE_SECONDS)


static func _games_text(n: int) -> String:
	var m10 := n % 10
	var m100 := n % 100
	var word := "игр"
	if m10 == 1 and m100 != 11:
		word = "игра"
	elif m10 >= 2 and m10 <= 4 and (m100 < 12 or m100 > 14):
		word = "игры"
	return "%d %s" % [n, word]


func _label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l
