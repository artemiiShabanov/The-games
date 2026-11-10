extends Control
## Тестовая сцена галереи (#70): шесть игр двух забегов в тестовом профиле. Раздел «Галерея»
## дебаг-меню: «Открыть» и «Пустая». Под ботом: порядок по забегам и по критикам, ход фокуса,
## бот запускает демку первой игры и закрывает галерею, затем пустая галерея с подписью.
## `--no-checks [--empty]` держит экран для скриншота.

const SECTION: StringName = &"Галерея"
const G := Game.Genre
const T := Game.Tech
const S := Game.Setting

var screen: GalleryScreen
var _phase := 0
var _checks := false
var _played := ""


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
	return out


func _open(entries: Array[GalleryEntry]) -> void:
	if screen != null:
		screen.queue_free()
	screen = GalleryScreen.new()
	screen.setup(entries)
	screen.closed.connect(_on_closed)
	screen.demo_opened.connect(func(e: GalleryEntry) -> void: _played = e.title)
	add_child(screen)
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
