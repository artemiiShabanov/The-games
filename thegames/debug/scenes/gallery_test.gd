extends Control
## Тестовая сцена галереи (#70): шесть игр двух забегов в тестовом профиле. Раздел «Галерея»
## дебаг-меню: «Открыть» и «Пустая». Под ботом: порядок по забегам и по критикам, ход фокуса,
## вкладка «Студии» (законченный забег с концовкой и забег в пути по играм), бот запускает
## демку первой игры и закрывает галерею, затем пустая галерея с подписью.
## `--no-checks [--empty] [--studios]` держит экран для скриншота.

const SECTION: StringName = &"Галерея"
const G := Game.Genre
const T := Game.Tech
const S := Game.Setting

var screen: GalleryScreen
var _phase := 0
var _checks := false
var _played := ""
var _studios := false


func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	Debug.add_action(SECTION, "Открыть", func() -> void: _open(_entries()))
	Debug.add_action(SECTION, "Пустая", func() -> void: _open([]))
	var empty := false
	if AutoTest.enabled:
		var args := AutoTest.parse_args(OS.get_cmdline_user_args())
		empty = args.has("empty")
		_studios = args.has("studios")
		if args.has("no-checks"):
			AutoTest.bot_mode = AutoTest.BotMode.OFF
		else:
			_checks = true
			Debug.skip_cards = true
			AutoTest.require("gallery checks")
	_open([] if empty else _entries())


func _exit_tree() -> void:
	Debug.clear_section(SECTION)


func _entries() -> Array[GalleryEntry]:
	var out: Array[GalleryEntry] = []
	var data := [
		[1, 1, G.PLATFORMER, S.PIRATES, "Пираты на платформах", 7.2, []],
		[1, 2, G.SHOOTER, S.SPACE, "Корсары в прицеле", 8.9, [&"sprite_flicker"]],
		[1, 3, G.RACING, S.CASTLES, "Рыцари на трассе", 6.4, [&"through_walls", &"frame_drops"]],
		[2, 1, G.SPORT, S.PIRATES, "Абордаж на лунке", 9.3, []],
		[2, 2, G.FIGHTING, S.SPACE, "Звёздный ринг", 5.8, [&"ghost_hits"]],
		[2, 3, G.PLATFORMER, S.CASTLES, "Замки по крышам", 8.1, [&"wild_physics"]],
	]
	for d in data:
		var r := GameRecord.create(d[2], T.BIT8, 100 + d[1] + 10 * d[0], d[4], d[3])
		for id in d[6]:
			r.add_bug(id)
		r.score = ReleaseScore.new()
		r.score.critics = d[5]
		r.score.viral = d[5] > 9.0
		out.append(GalleryEntry.of(r, d[0], d[1], "Тихая Лампа" if d[0] == 1 else "Ночной Пельмень"))
	# Кадр у первой игры второго забега: небо, земля и солнце, чтобы видеть картинку в строке.
	var img := Image.create(480, 270, false, Image.FORMAT_RGB8)
	img.fill(Color("#5C94FC"))
	img.fill_rect(Rect2i(0, 200, 480, 70), Color("#C84C0C"))
	img.fill_rect(Rect2i(380, 30, 50, 50), Color("#FCE0A8"))
	DirAccess.make_dir_recursive_absolute("user://shots_autotest/")
	if img.save_png("user://shots_autotest/gallery_test.png") == OK:
		out[3].shot = "user://shots_autotest/gallery_test.png"
	return out


## Первый забег закончен продажей, второй в пути.
func _runs() -> Array[Dictionary]:
	var logo := RunSave.logo_to_dict(StudioLogo.new())
	return [{"run": 1, "studio": "Тихая Лампа", "logo": logo, "ending": &"sale", "score": 640, "releases": 3, "finished": 0}]


func _open(entries: Array[GalleryEntry]) -> void:
	if screen != null:
		screen.queue_free()
	screen = GalleryScreen.new()
	var runs: Array[Dictionary] = []
	if not entries.is_empty():
		runs = _runs()
	screen.setup(entries, runs)
	screen.closed.connect(_on_closed)
	screen.demo_opened.connect(func(e: GalleryEntry) -> void: _played = e.title)
	add_child(screen)
	if _studios:
		screen.set_tab(GalleryScreen.Tab.STUDIOS)
	if _checks and _phase == 0:
		_order_checks()


func _order_checks() -> void:
	var titles := screen.entries.map(func(e: GalleryEntry) -> String: return e.title)
	_expect(titles[0] == "Абордаж на лунке" and titles[2] == "Замки по крышам" and titles[3] == "Пираты на платформах",
			"по забегам: %s" % [titles])
	screen.toggle_sort()
	titles = screen.entries.map(func(e: GalleryEntry) -> String: return e.title)
	_expect(titles[0] == "Абордаж на лунке" and titles[1] == "Корсары в прицеле" and titles[5] == "Звёздный ринг",
			"по критикам: %s" % [titles])
	_expect(screen.index == 0, "фокус после сортировки на той же игре: %d" % screen.index)
	screen.focus(5)
	_expect(screen.index == 5, "фокус %d" % screen.index)
	screen.focus(0)
	# Вкладка студий: новые сверху, у второго забега концовки нет, у первого продажа.
	screen.set_tab(GalleryScreen.Tab.STUDIOS)
	var st := screen.studios
	_expect(screen.count() == 2 and int(st[0]["run"]) == 2 and st[0]["ending"] == &"" and st[1]["ending"] == &"sale",
			"студии: %s" % [st])
	_expect(st[0]["best"] == "Абордаж на лунке" and int(st[1]["games"]) == 3 and int(st[1]["releases"]) == 3,
			"лучшая и релизы: %s" % [st])
	screen.set_tab(GalleryScreen.Tab.GAMES)
	_expect(screen.index == 0 and screen.count() == 6, "назад на игры")


func _on_closed() -> void:
	if not _checks:
		return
	if _phase == 0:
		_expect(_played == "Абордаж на лунке", "бот запустил «%s»" % _played)
		_phase = 1
		_open([])
	else:
		AutoTest.note("gallery: порядок, фокус, демка «%s», пустая галерея" % _played)
		AutoTest.fulfill("gallery checks")


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("gallery: " + what)
