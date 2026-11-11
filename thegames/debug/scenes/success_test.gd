extends Control
## Тестовая сцена успеха (#25): модельный забег «хорошие руки» из `docs/specs/economy_model.md`
## на двенадцать релизов без шума, рядом числа из таблицы. Раздел «Успех» в дебаг-меню:
## средние руки (q × 0.65, багов +1), сид шума, шум вкл. Под ботом сверяет C, P0, хвосты, V
## и R каждого релиза с таблицей, а также слова стримеров, метки насыщения и оценку студии.

const SECTION: StringName = &"Успех"
const G := Game.Genre
const T := Game.Tech
const S := Game.Setting
## Жанр, технология, сеттинг, q, баги, зрелищных, часть; затем ожидания: C, P0, хвосты, V, R.
const RUN := [
	[G.PLATFORMER, T.BIT8, S.PIRATES, 0.6, 2, 1, 1, 7.8, 6300, 0, 65, 1.4],
	[G.SHOOTER, T.BIT8, S.PIRATES, 0.8, 1, 0, 1, 8.5, 4800, 3200, 47, 3.1],
	[G.PLATFORMER, T.BIT8, S.SPACE, 0.6, 2, 1, 1, 7.0, 5900, 4500, 70, 4.1],
	[G.SHOOTER, T.VECTOR, S.SPACE, 1.0, 0, 0, 1, 10.0, 4700, 5500, 51, 6.6],
	[G.PLATFORMER, T.BIT8, S.PIRATES, 0.8, 1, 0, 2, 8.2, 9400, 6200, 55, 8.2],
	[G.PLATFORMER, T.VECTOR, S.CASTLES, 0.75, 1, 0, 1, 8.2, 3800, 9500, 38, 9.8],
	[G.SHOOTER, T.LOWPOLY, S.CASTLES, 0.57, 3, 1, 1, 5.6, 11000, 7900, 77, 11.1],
	[G.SHOOTER, T.BIT8, S.PIRATES, 0.8, 1, 0, 2, 7.2, 7800, 9700, 47, 12.2],
	[G.RACING, T.LOWPOLY, S.SPACE, 0.71, 2, 1, 1, 7.2, 17200, 9700, 90, 14.3],
	[G.PLATFORMER, T.LOWPOLY, S.PIRATES, 0.86, 1, 0, 3, 7.2, 18400, 14600, 70, 16.4],
	[G.RACING, T.THREED, S.CASTLES, 0.75, 2, 1, 1, 7.4, 22500, 19300, 99, 18.6],
	[G.SHOOTER, T.THREED, S.SPACE, 0.875, 1, 1, 1, 9.3, 32600, 23300, 100, 21.8],
]

var tuning: SuccessTuning
var catalog: BugCatalog
var mid := false
var noise := false
var seed_value := 1
var rows: Array[Dictionary] = []
var market: MarketState
var records: Array[GameRecord] = []
var _label: Label
var _checked := false


func _ready() -> void:
	tuning = SuccessTuning.load_default()
	catalog = BugCatalog.load_default()
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	_label = Label.new()
	_label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_label.offset_left = 48
	_label.offset_top = 36
	_label.offset_right = -48
	_label.add_theme_font_size_override("font_size", 22)
	_label.add_theme_color_override("font_color", Style.STUDIO_INK)
	_label.add_theme_font_override("font", Style.mono_font())
	add_child(_label)
	Debug.add_toggle(SECTION, "Средние руки", func() -> bool: return mid, func(v: bool) -> void:
		mid = v
		_refresh())
	Debug.add_toggle(SECTION, "Шум", func() -> bool: return noise, func(v: bool) -> void:
		noise = v
		_refresh())
	Debug.add_number(SECTION, "Сид шума", func() -> int: return seed_value, func(v: float) -> void:
		seed_value = int(v)
		_refresh(), 1, 999, 1)
	Debug.watch("рынок", func() -> String: return "R %.1f, тренд %d/%d, настрой %.2f" % [market.reputation, market.trend_genre, market.trend_setting, market.mood] if market else "")
	if AutoTest.enabled:
		AutoTest.require("success checks")
	_refresh()


func _exit_tree() -> void:
	Debug.clear_section(SECTION)


func _unhandled_input(event: InputEvent) -> void:
	if GameInput.is_a(event):
		mid = not mid
		_refresh()
	elif GameInput.is_b(event):
		noise = not noise
		_refresh()


## Забег модели: синергия включена, спрос и настрой 1.0, тренд не выпадает (детерминированно).
func _simulate() -> void:
	rows.clear()
	records.clear()
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	market = MarketState.create(tuning, rng, true)
	if noise:
		market.roll_release(tuning, rng)
	var spectacular_ids: Array[StringName] = []
	var plain_ids: Array[StringName] = []
	for b in catalog.bugs:
		(spectacular_ids if b.spectacular else plain_ids).append(b.id)
	for i in RUN.size():
		var r: Array = RUN[i]
		var q: float = r[3]
		var bugs: int = r[4]
		var bs: int = r[5]
		if mid:
			q = snappedf(q * 0.65, 0.01)
			bugs += 1
		var rec := GameRecord.create(r[0], r[1], 1000 + i, "Игра %d" % (i + 1), r[2])
		rec.part = r[6]
		if rec.part > 1:
			for p in records:
				if p.genre == rec.genre and p.part == rec.part - 1:
					rec.parent = p
					rec.title = p.franchise_title()
		# Качество через результаты спринтов: модель считала q из спринтов технологии (3/5, 4/7),
		# для средних рук берётся ближайшая дробь.
		var sprints: int = EconomyTuning.load_default().sprints(r[1])
		var ok := int(round(q * sprints))
		for k in sprints:
			rec.add_sprint(k < ok)
		# Баги: столько зрелищных и обычных, сколько в таблице (каталог M0 даёт один зрелищный).
		for k in bs:
			if k < spectacular_ids.size():
				rec.add_bug(spectacular_ids[k])
		for k in bugs - bs:
			if k < plain_ids.size():
				rec.add_bug(plain_ids[k])
		var score := Success.score_release(rec, records, market, tuning, catalog, rng, noise)
		rec.score = score
		var tails := Success.tick_tails(records, tuning)
		Success.apply_release(rec, score, market, tuning, rng, noise)
		records.append(rec)
		if noise:
			market.roll_release(tuning, rng)
		rows.append({"i": i + 1, "rec": rec, "q": q, "b": bugs, "score": score, "tails": tails,
				"R": market.reputation, "exp": r.slice(7)})


func _refresh() -> void:
	_simulate()
	var lines: PackedStringArray = []
	lines.append("Успех: забег модели %s%s   (A руки, B шум, F1 меню)" % ["средние руки" if mid else "хорошие руки", ", с шумом" if noise else ""])
	lines.append("")
	lines.append(" #  игра                          q     b   C     P0      хвосты  V    R      | модель: C    P0     хвосты V   R")
	for row in rows:
		var rec: GameRecord = row["rec"]
		var sc: ReleaseScore = row["score"]
		var e: Array = row["exp"]
		lines.append("%2d  %-28s  %.2f  %d  %4.1f  %6d%s %6d  %3d  %5.1f  | %4.1f  %6d  %6d  %3d  %4.1f" % [
				row["i"], ("%s %s %s" % [Game.genre_name(rec.genre), Game.tech_name(rec.tech), Game.setting_name(rec.setting)]).substr(0, 28),
				row["q"], row["b"], sc.critics, sc.sales_first, "*" if sc.viral else " ", row["tails"], sc.streamers, row["R"],
				e[0], e[1], e[2], e[3], e[4]])
	lines.append("")
	var stats := Success.run_stats(records, market, 0, tuning)
	lines.append("итоги: " + str(stats))
	lines.append("насыщение жанров %s, сеттингов %s" % [_fmt(market.saturation_genre), _fmt(market.saturation_setting)])
	_label.text = "\n".join(lines)


func _fmt(a: Array[float]) -> String:
	var out: PackedStringArray = []
	for v in a:
		out.append("%.2f" % v)
	return "[" + ", ".join(out) + "]"


func _process(_delta: float) -> void:
	if AutoTest.enabled and not _checked:
		_checked = true
		_run_checks()


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("success: " + what)


func _run_checks() -> void:
	mid = false
	noise = false
	_simulate()
	for row in rows:
		var sc: ReleaseScore = row["score"]
		var e: Array = row["exp"]
		var i: int = row["i"]
		_expect(absf(sc.critics - e[0]) <= 0.1, "релиз %d: C %.2f, в модели %.1f" % [i, sc.critics, e[0]])
		_expect(absi(sc.sales_first - int(e[1])) <= 60, "релиз %d: P0 %d, в модели %d" % [i, sc.sales_first, e[1]])
		_expect(absi(int(row["tails"]) - int(e[2])) <= 60, "релиз %d: хвосты %d, в модели %d" % [i, row["tails"], e[2]])
		_expect(absi(sc.streamers - int(e[3])) <= 1, "релиз %d: V %d, в модели %d" % [i, sc.streamers, e[3]])
		_expect(absf(float(row["R"]) - e[4]) <= 0.1, "релиз %d: R %.2f, в модели %.1f" % [i, row["R"], e[4]])
	# Релиз 3: V 69.7, в таблице округлён до 70 со звёздочкой, но порог не взят.
	var first: ReleaseScore = rows[0]["score"]
	var third: ReleaseScore = rows[2]["score"]
	var seventh: ReleaseScore = rows[6]["score"]
	_expect(first.streamers_word(tuning) == "заметили" and third.streamers_word(tuning) == "заметили"
			and seventh.streamers_word(tuning) == "вирусно", "слова стримеров")
	_expect(market.saturation_label(0.1, tuning) == "" and market.saturation_label(0.4, tuning) == "недавно было"
			and market.saturation_label(0.7, tuning) == "надоело", "метки насыщения")
	var stats := Success.run_stats(records, market, 10000, tuning)
	_expect(stats.sequels == 3 and stats.viral_count == 5 and stats.franchises == 2, "итоги: %s" % stats)
	_expect(stats.valuation % tuning.valuation_round == 0 and stats.valuation > 10000, "оценка студии %d" % stats.valuation)
	# Шум не ломает диапазоны.
	noise = true
	_simulate()
	for row in rows:
		var sc: ReleaseScore = row["score"]
		_expect(sc.critics >= 0.0 and sc.critics <= 10.0 and sc.streamers >= 0 and sc.streamers <= 100 and sc.sales_first > 0,
				"шум: релиз %d вне диапазона %s" % [row["i"], sc])
	noise = false
	_refresh()
	AutoTest.fulfill("success checks")
	AutoTest.note("success checks done")
