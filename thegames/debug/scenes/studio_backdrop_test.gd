extends Control
## Тестовая сцена пиксельной студии на фоне (#80, `StudioBackdrop`). Стадии роста: 0 пустая
## (стол, человечек), 1 четвёртый релиз, 2 восьмой, 3 полная (12 человек, всё куплено, плюс
## незнакомый id). Аргументы: `--stage=N`, или своя студия `--people=N --upgrades=a,b,c`,
## `--release=N`, `--tech=N`, `--genre=N` (стартовая пара); `--grid` четыре стадии сеткой
## (превью роста), `--card` карточка оболочки посреди (проверка читаемости), `--static` без
## движения, `--react=release|viral|broke`, `--busy`; `--sheet` пишет превью-лист всех спрайтов
## в `debug/playtest/studio_sheet.png`. Под ботом проверяет раскладку: сколько
## людей и предметов, одинаковость при одинаковом состоянии, рост с покупками, вход новичков,
## перетаскивание мышью синтетическими событиями (`_drag_check`). Кадр с человечком в руке:
## `--bot=off "--input=20:move=684x472,22:press=684x472,40:move=900x640" --stage=2`.
## Раздел «Студия фон» дебаг-меню: стадия, люди, движение, спринт, реакции, карточка.

const SECTION: StringName = &"Студия фон"
const STAGES := [
	[1, [], 1],
	[4, [&"replay", &"genre_racing"], 4],
	[8, [&"replay", &"genre_racing", &"sequels", &"qa", &"manager", &"genre_shooter"], 8],
	[12, [&"replay", &"replay2", &"genre_racing", &"genre_shooter", &"genre_sport", &"genre_fighting",
			&"sequels", &"remakes", &"qa", &"manager", &"insider", &"setting_space"], 12],
]

var stage := 0
var people := -1
var upgrades: Array[StringName] = []
var release := 0
var start_tech := Game.Tech.BIT8
var start_genre := Game.Genre.PLATFORMER
var grid := false
var card := false
var backdrops: Array[StudioBackdrop] = []
var _card: PanelContainer


func _ready() -> void:
	var args := AutoTest.parse_args(OS.get_cmdline_user_args())
	stage = clampi(int(args.get("stage", "0")), 0, STAGES.size() - 1)
	if args.has("people"):
		people = int(args["people"])
	if args.has("upgrades"):
		for id in str(args["upgrades"]).split(",", false):
			upgrades.append(StringName(id))
	release = int(args.get("release", "0"))
	if args.has("tech"):
		start_tech = int(args["tech"]) as Game.Tech
	if args.has("genre"):
		start_genre = int(args["genre"]) as Game.Genre
	grid = args.has("grid")
	card = args.has("card")
	_build()
	for b in backdrops:
		b.animate = not args.has("static")
		b.busy = args.has("busy")
		if args.has("react"):
			b.react(StringName(str(args["react"])))
	Debug.add_choice(SECTION, "Стадия", ["пустая", "релиз 4", "релиз 8", "полная"],
			func() -> int: return stage, _set_stage)
	Debug.add_number(SECTION, "Люди", func() -> int: return _people(), _set_people, 1, 12, 1)
	Debug.add_toggle(SECTION, "Движение", func() -> bool: return backdrops[0].animate,
			func(v: bool) -> void: _each(func(b: StudioBackdrop) -> void: b.animate = v))
	Debug.add_toggle(SECTION, "Спринт (печатают быстрее)", func() -> bool: return backdrops[0].busy,
			func(v: bool) -> void: _each(func(b: StudioBackdrop) -> void: b.busy = v))
	Debug.add_toggle(SECTION, "Таскать мышью", func() -> bool: return backdrops[0].drag_enabled,
			func(v: bool) -> void: _each(func(b: StudioBackdrop) -> void: b.drag_enabled = v))
	Debug.add_toggle(SECTION, "Карточка поверх", func() -> bool: return card, _set_card)
	Debug.add_number(SECTION, "Сила чернил", func() -> float: return backdrops[0].strength,
			func(v: float) -> void: _each(func(b: StudioBackdrop) -> void: b.strength = v), 0.0, 1.0, 0.1)
	for kind: String in ["release", "viral", "broke", ""]:
		Debug.add_action(SECTION, "Реакция «%s»" % (kind if kind != "" else "снять"),
				func() -> void: _each(func(b: StudioBackdrop) -> void: b.react(StringName(kind))))
	Debug.add_action(SECTION, "Встряхнуть (между спринтами)",
			func() -> void: _each(func(b: StudioBackdrop) -> void: b.nudge()))
	if args.has("sheet"):
		var path := ProjectSettings.globalize_path("res://debug/playtest/studio_sheet.png")
		DirAccess.make_dir_recursive_absolute(path.get_base_dir())
		var err := backdrops[0].sheet_image().save_png(path)
		AutoTest.note("лист спрайтов: %s (%s)" % [path, error_string(err)])
	if AutoTest.enabled and not args.has("no-checks"):
		_checks()
		if not grid:
			_drag_check.call_deferred()


func _each(fn: Callable) -> void:
	for b in backdrops:
		fn.call(b)


func _set_stage(v: int) -> void:
	stage = v
	people = -1
	upgrades.clear()
	_apply()


func _set_people(v: float) -> void:
	people = int(v)
	_apply()


func _set_card(v: bool) -> void:
	card = v
	_card.visible = v


func _people() -> int:
	return people if people > 0 else int(STAGES[stage][0])


func _state(s: int, n := -1, ids: Array[StringName] = []) -> StudioState:
	var st := StudioState.new()
	st.people = n if n > 0 else int(STAGES[s][0])
	if ids.is_empty():
		for id in STAGES[s][1]:
			st.upgrade_ids.append(id)
	else:
		st.upgrade_ids = ids.duplicate()
	return st


func _build() -> void:
	var count := 4 if grid else 1
	for i in count:
		var b := StudioBackdrop.new()
		add_child(b)
		backdrops.append(b)
	_layout()
	resized.connect(_layout)
	_card = PanelContainer.new()
	_card.add_theme_stylebox_override("panel", Style.card())
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 16)
	var h := Label.new()
	h.text = "Что улучшим?"
	h.add_theme_font_size_override("font_size", Style.FONT_H1)
	h.add_theme_color_override("font_color", Style.INK)
	var p := Label.new()
	p.text = "Одно из трёх или ничего. Содержание студии сейчас $ 3 000 за релиз."
	p.add_theme_font_size_override("font_size", Style.FONT_BODY)
	p.add_theme_color_override("font_color", Style.INK_2)
	var m := Label.new()
	m.text = Style.format_money(38200)
	m.add_theme_font_override("font", Style.mono_font())
	m.add_theme_font_size_override("font_size", Style.FONT_H2)
	m.add_theme_color_override("font_color", Style.MONEY)
	box.add_child(h)
	box.add_child(p)
	box.add_child(m)
	_card.add_child(box)
	_card.custom_minimum_size = Vector2(1000, 420)
	_card.position = (Vector2(Style.SCREEN) - _card.custom_minimum_size) / 2.0
	_card.visible = card
	add_child(_card)
	_apply()


func _layout() -> void:
	if backdrops.size() == 1:
		backdrops[0].set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		return
	var half := size / 2.0
	for i in backdrops.size():
		backdrops[i].position = Vector2(i % 2, i / 2) * half
		backdrops[i].size = half


func _apply() -> void:
	for i in backdrops.size():
		var s := i if grid else stage
		var rel := release if release > 0 else int(STAGES[s][2])
		var st := _state(s) if grid else _state(s, people, upgrades)
		backdrops[i].set_studio(st, rel, start_tech, start_genre)


## Раскладка без окна: люди и предметы по стадиям, одинаковость, рост, вход новичков, мотор.
func _checks() -> void:
	AutoTest.require("backdrop checks")
	var last_props := -1
	for s in STAGES.size():
		var b := StudioBackdrop.new()
		add_child(b)
		b.set_studio(_state(s), int(STAGES[s][2]), start_tech, start_genre)
		_expect(b.people_count() == int(STAGES[s][0]), "стадия %d: людей %d" % [s, b.people_count()])
		_expect(b.prop_count() > last_props, "стадия %d: предметов %d не больше %d" % [s, b.prop_count(), last_props])
		last_props = b.prop_count()
		var twin := StudioBackdrop.new()
		add_child(twin)
		twin.set_studio(_state(s), int(STAGES[s][2]), start_tech, start_genre)
		_expect(b.layout_dump() == twin.layout_dump(), "стадия %d: одно состояние, разная картинка" % s)
		for i in 600:
			b._process(1.0 / 30.0)
			twin._process(1.0 / 30.0)
		_expect(b.layout_dump() == twin.layout_dump(), "стадия %d: разошлись через 20 с" % s)
		AutoTest.note("backdrop стадия %d: людей %d, предметов %d" % [s, b.people_count(), b.prop_count()])
		b.queue_free()
		twin.queue_free()
	# Незнакомые id ставят предметы, люди не больше столов.
	var odd := StudioBackdrop.new()
	add_child(odd)
	var st := _state(0, 12, [&"tech_mystery", &"setting_space", &"x"] as Array[StringName])
	odd.set_studio(st, 1)
	_expect(odd.prop_count() > 0 and odd.people_count() == 12, "незнакомые id: %d людей" % odd.people_count())
	# Новичок входит в дверь: после покупки один человечек идёт, остальные на месте.
	var grow := StudioBackdrop.new()
	add_child(grow)
	grow.set_studio(_state(0, 2), 1)
	grow.set_studio(_state(0, 3), 1)
	_expect(grow.walking_count() == 1, "после покупки идут %d" % grow.walking_count())
	for i in 3600:
		grow._process(1.0 / 30.0)
	_expect(grow.walking_count() <= 3, "через 2 минуты идут %d" % grow.walking_count())
	odd.queue_free()
	grow.queue_free()
	AutoTest.fulfill("backdrop checks")


## Перетаскивание мышью синтетическими событиями во вьюпорт: человечек поднимается, висит,
## встаёт куда отпустили, потом идёт к своему делу; на стене встаёт на пол; под элементом
## оболочки не поднимается.
func _drag_check() -> void:
	AutoTest.require("backdrop drag")
	await get_tree().process_frame
	await get_tree().process_frame
	var b := backdrops[0]
	var to_screen := b.get_global_transform_with_canvas()
	var start := to_screen * b.worker_local_rect(0).get_center()
	_mouse(start, -1)
	_mouse(start, 1)
	_expect(b.worker_info(0)["held"], "нажатие на человечка его не подняло")
	var target := start + Vector2(520, 260)
	_mouse(target, -1)
	_mouse(target, 0)
	var info := b.worker_info(0)
	_expect(not info["held"] and info["placed"], "после отпускания %s" % info)
	var moved: float = (info["pos"] as Vector2).distance_to(info["home"])
	_expect(moved > 60.0, "отпустили, а он в %.0f px арта от места" % moved)
	var home := false
	for i in 2400:
		b._process(1.0 / 30.0)
		var now := b.worker_info(0)
		home = home or (now["pos"] == now["home"] and now["act"] != "walk")
	var last := b.worker_info(0)
	_expect(home and not last["placed"], "за 80 с не вернулся к делу: %s" % last)
	# На стену: встаёт на пол.
	start = to_screen * b.worker_local_rect(0).get_center()
	_mouse(start, -1)
	_mouse(start, 1)
	_mouse(Vector2(start.x, 20), -1)
	_mouse(Vector2(start.x, 20), 0)
	var wall := b.worker_info(0)
	_expect((wall["pos"] as Vector2).y >= StudioBackdrop.FLOOR_RECT.position.y, "встал на стену: %s" % wall)
	for i in 2400:
		b._process(1.0 / 30.0)
	# Под элементом оболочки не поднимается и событие не съедается.
	start = to_screen * b.worker_local_rect(0).get_center()
	var cover := ColorRect.new()
	cover.color = Color(1, 1, 1, 0.5)
	cover.position = start - Vector2(40, 40)
	cover.size = Vector2(80, 80)
	add_child(cover)
	_mouse(start, -1)
	_mouse(start, 1)
	_expect(not b.worker_info(0)["held"], "поднялся из-под элемента оболочки")
	_mouse(start, 0)
	cover.queue_free()
	AutoTest.note("backdrop drag: сдвинут на %.0f, вернулся к делу, стена и оболочка ок" % moved)
	AutoTest.fulfill("backdrop drag")


## Событие мыши во вьюпорт: `button` -1 движение, 1 нажать, 0 отпустить левую.
func _mouse(at: Vector2, button: int) -> void:
	var e: InputEventMouse
	if button < 0:
		e = InputEventMouseMotion.new()
	else:
		var mb := InputEventMouseButton.new()
		mb.button_index = MOUSE_BUTTON_LEFT
		mb.pressed = button == 1
		e = mb
	e.position = at
	e.global_position = at
	get_viewport().push_input(e, true)


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("backdrop: " + what)
