extends Control
## Тестовая сцена ленты отклика (#26): релиз с настраиваемыми качеством, числом багов и
## сдвигом репутации из раздела «Лента» дебаг-меню, счёт по формулам успеха без шума. После
## «Дальше» или «В демо» показывает, что нажали, A запускает снова. Под ботом: состав ленты по
## спеке, сдвиги критиков, выбор стримера, сигналы кнопок. Флаги `--no-checks`, `--quality=`,
## `--bugs=`, `--end` (пролистать в конец).

const SECTION: StringName = &"Лента"
## Сцена грузится при запуске, не `preload`: константная ссылка на сцену с вложенным классом
## `FeedContent.Item` в сигнатурах держала ресурсы при выходе.
const SCENE_PATH := "res://scenes/feed.tscn"

var quality := 0.6
var bugs := 2
var rep_delta := 0.0
var seed_value := 1
var tuning: SuccessTuning
var catalog: BugCatalog
var critics: PeopleSet
var streamers: PeopleSet
var texts: FeedTexts
var feed: FeedScreen
var record: GameRecord
var content: FeedContent
var _label: Label
var _checked := false


func _ready() -> void:
	tuning = SuccessTuning.load_default()
	catalog = BugCatalog.load_default()
	critics = PeopleSet.load_critics()
	streamers = PeopleSet.load_streamers()
	texts = FeedTexts.load_default()
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	_label = Label.new()
	_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	_label.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_label.grow_vertical = Control.GROW_DIRECTION_BOTH
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.add_theme_font_size_override("font_size", Style.FONT_H2)
	_label.visible = false
	add_child(_label)
	Debug.add_number(SECTION, "Качество", func() -> float: return quality, func(v: float) -> void: quality = v, 0.0, 1.0, 0.1)
	Debug.add_number(SECTION, "Багов", func() -> int: return bugs, func(v: float) -> void: bugs = int(v), 0, 6, 1)
	Debug.add_number(SECTION, "ΔR", func() -> float: return rep_delta, func(v: float) -> void: rep_delta = v, -3.0, 3.0, 0.5)
	Debug.add_number(SECTION, "Сид", func() -> int: return seed_value, func(v: float) -> void: seed_value = int(v), 1, 999, 1)
	Debug.add_action(SECTION, "Открыть ленту", _launch)
	Debug.watch("лента", func() -> String: return "%s, элементов %d" % [record.score, content.items.size()] if content else "")
	if AutoTest.enabled:
		var args := AutoTest.parse_args(OS.get_cmdline_user_args())
		if args.has("quality"):
			quality = float(args["quality"])
		if args.has("bugs"):
			bugs = int(args["bugs"])
		if args.has("no-checks"):
			_checked = true
		else:
			AutoTest.require("feed checks")
	_launch()
	if AutoTest.enabled and AutoTest.parse_args(OS.get_cmdline_user_args()).has("end"):
		# `--end`: через секунду пролистать в конец, для скриншота цифр и кнопок.
		await get_tree().create_timer(1.0).timeout
		if feed != null:
			feed.scroll_to_end()


func _exit_tree() -> void:
	Debug.clear_section(SECTION)


func _make_record() -> GameRecord:
	var rec := GameRecord.create(Game.Genre.PLATFORMER, Game.Tech.BIT8, seed_value, "Пираты на платформах", Game.Setting.PIRATES)
	var sprints := 5
	var ok := int(round(quality * sprints))
	for k in sprints:
		rec.add_sprint(k < ok)
	var ids: Array[StringName] = []
	for b in catalog.bugs:
		if b.spectacular:
			ids.push_front(b.id)
		else:
			ids.push_back(b.id)
	for k in mini(bugs, ids.size()):
		rec.add_bug(ids[k])
	return rec


func _launch() -> void:
	_label.visible = false
	if feed != null:
		feed.queue_free()
	record = _make_record()
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var market := MarketState.create(tuning, rng, true)
	record.score = Success.score_release(record, [], market, tuning, catalog, rng, false)
	content = Feed.build(record, record.score, critics, streamers, texts, tuning, catalog, rng, rep_delta)
	feed = (load(SCENE_PATH) as PackedScene).instantiate() as FeedScreen
	feed.setup(content, record, 2, 29000)
	feed.demo_requested.connect(_done.bind("В демо"))
	feed.finished.connect(_done.bind("Дальше"))
	add_child(feed)


func _done(what: String) -> void:
	if feed != null:
		feed.queue_free()
		feed = null
	_label.text = "Нажали: %s\n%s\n\nA снова, F1 меню" % [what, record.score]
	_label.visible = true


func _unhandled_input(event: InputEvent) -> void:
	if feed == null and GameInput.is_a(event):
		_launch()


func _process(_delta: float) -> void:
	if AutoTest.enabled and not _checked and feed != null:
		_checked = true
		_run_checks()


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("feed: " + what)


func _run_checks() -> void:
	var K := FeedContent.Kind
	var counts := {K.TWEET: 0, K.CRITIC: 0, K.CLIP: 0, K.NUMBERS: 0}
	for item in content.items:
		counts[item.kind] += 1
	_expect(counts[K.TWEET] == 4 and counts[K.CRITIC] == 3 and counts[K.CLIP] == 1 and counts[K.NUMBERS] == 1
			and content.items[-1].kind == K.NUMBERS and content.items[0].kind != K.CLIP, "состав ленты %s" % [counts])
	_expect(content.views > 0 and content.views % 100 == 0 and content.online > 0, "просмотры %d, онлайн %d" % [content.views, content.online])
	_expect(FeedContent.format_count(1234567) == "1,2 млн" and FeedContent.format_count(140400) == "140 тыс." and FeedContent.format_count(640) == "640",
			"формат просмотров")
	_expect(content.tag == "#ПиратыНаПлатформах", "хэштег %s" % content.tag)
	# Сдвиги: ненавистник багов ниже общей C при двух багах, любитель ретро выше на 8-bit.
	var by_id := {}
	for item in content.items:
		if item.kind == K.CRITIC:
			by_id[item.person.id] = item.score
	var c := record.score.critics
	_expect(by_id[&"ignat"] < c and by_id[&"marta"] > c, "сдвиги критиков %s при C %.1f" % [by_id, c])
	_expect(content.clip_person != null and content.clip_person.id == &"kraken", "клип у любителя багов: %s" % (content.clip_person.id if content.clip_person else ""))
	var clip: FeedContent.Item
	for item in content.items:
		if item.kind == K.CLIP:
			clip = item
	_expect(clip != null and clip.stamp == "ПРЫЖОК ×3", "штамп клипа %s" % (clip.stamp if clip else ""))
	for item in content.items:
		if item.kind == K.TWEET:
			_expect(item.text.find(content.tag) >= 0, "твит без тега: %s" % item.text)
	# Без багов: клип чистый, стример не любитель багов, у ненавистника бонус.
	bugs = 0
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var clean := _make_record()
	clean.score = Success.score_release(clean, [], MarketState.create(tuning, rng, true), tuning, catalog, rng, false)
	var clean_feed := Feed.build(clean, clean.score, critics, streamers, texts, tuning, catalog, rng)
	_expect(clean_feed.clip_person.id != &"kraken", "чистая сборка: клип у %s" % clean_feed.clip_person.id)
	_expect(Feed.critic_score(critics.people[1], clean.score, clean, tuning) > clean.score.critics, "ненавистник багов без багов")
	bugs = 2
	# Кнопки.
	var got: Array[String] = []
	var f := feed  # после первого сигнала сцена убирает экран, но нода жива до конца кадра
	f.demo_requested.connect(func() -> void: got.append("demo"))
	f.finished.connect(func() -> void: got.append("next"))
	_expect(not f.at_end() and f.index == 0, "фокус в начале не на кнопках")
	f.scroll_to_end()
	_expect(f.at_end() and not f.focus_demo, "A вниз ставит фокус на «Дальше»")
	f.set_focus_demo(true)
	f.confirm()
	f.set_focus_demo(false)
	f.confirm()
	_expect(got == ["demo", "next"], "сигналы кнопок %s" % [got])
	_expect(f._demo != null and f._demo.embedded and f._demo.running, "встроенная демка стрима не запущена")
	AutoTest.fulfill("feed checks")
	AutoTest.note("feed checks done")
