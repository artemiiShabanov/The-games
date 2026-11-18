extends Control
## Тест профиля (#69) без экрана: запись и чтение `profile.tres` (свой тестовый файл), галерея
## пересобирает запись с тем же сидом и багами, лучшая оценка концовки, другая версия формата
## даёт пустой профиль.


func _ready() -> void:
	AutoTest.require("profile checks")
	Profile.use_test_file()
	var p := Profile.load_saved()
	_expect(p.gallery.is_empty() and p.runs_started == 0, "свежий профиль не пустой")
	var n := p.start_run(Game.Genre.SHOOTER, Game.Tech.BIT8)
	var r := GameRecord.create(Game.Genre.SHOOTER, Game.Tech.BIT8, 4242, "Корсары в прицеле", Game.Setting.SPACE)
	r.add_bug(&"sprite_flicker")
	r.score = ReleaseScore.new()
	r.score.critics = 8.7
	r.score.viral = true
	p.add_game(r, n, 1, "Тихая Лампа")
	p.finish_run(&"sale", 120000)
	p.finish_run(&"sale", 90000)
	var q := Profile.load_saved()
	_expect(q.runs_started == 1 and q.runs_finished == 2, "забеги %d/%d" % [q.runs_started, q.runs_finished])
	_expect(q.last_start_genre == int(Game.Genre.SHOOTER), "пара %d" % q.last_start_genre)
	_expect(q.best_endings.get(&"sale", 0) == 120000 and q.ending_counts.get(&"sale", 0) == 2, "концовки %s %s" % [q.best_endings, q.ending_counts])
	_expect(q.gallery.size() == 1, "галерея %d" % q.gallery.size())
	if q.gallery.size() == 1:
		var e := q.gallery[0]
		var back := e.to_record()
		_expect(back.seed == 4242 and back.bug_ids == [&"sprite_flicker"] and back.setting == Game.Setting.SPACE
				and is_equal_approx(back.score.critics, 8.7) and e.run_number == 1 and e.studio == "Тихая Лампа",
				"запись из галереи %s" % back)
	q.version = Profile.VERSION + 1
	ResourceSaver.save(q, Profile.path)
	var fresh := Profile.load_saved()
	_expect(fresh.gallery.is_empty() and fresh.runs_started == 0, "другая версия не дала пустой профиль")
	Profile.use_test_file()
	_achievements()
	Profile.use_test_file()
	AutoTest.note("profile: %s" % p)
	AutoTest.fulfill("profile checks")


## Достижения и сеттинги (#139): каждое условие по порогу, один раз на профиль, сеттинг открыт
## сразу; «новый сеттинг» одной карточкой и только из закрытых.
func _achievements() -> void:
	var S := Game.Setting
	var prof := Profile.load_saved()
	var run := RunState.start(7, true)
	run.profile = prof
	_expect(run.unlocked_settings() == ([S.CASTLES] as Array[Game.Setting]), "старт %s" % [run.unlocked_settings()])
	_expect(Achievements.load_all().size() == 9, "достижений %d" % Achievements.load_all().size())
	_expect(run.check_achievements().is_empty(), "достижение на пустом забеге")
	run.wallet.cash = 199999
	_expect(run.check_achievements().is_empty(), "сокровище до порога")
	run.wallet.cash = 200000
	var got := run.check_achievements()
	_expect(got.size() == 1 and got[0].id == &"treasure", "сокровище: %s" % [got.map(func(a: AchievementDef) -> StringName: return a.id)])
	_expect(run.unlocked_settings().has(S.PIRATES), "пираты не открылись сразу")
	_expect(run.check_achievements().is_empty(), "сокровище засчитано дважды")
	_expect(Profile.load_saved().achievements.has(&"treasure"), "достижение не записано в профиль")
	var other := RunState.start(8, true)
	other.profile = Profile.load_saved()
	_expect(other.unlocked_settings().has(S.PIRATES), "пираты не открыты в другом забеге")
	# Серии: без багов три подряд, окупились три подряд (2026-11-18, было пять); срыв серии обнуляет.
	for i in 5:
		var r := GameRecord.create(Game.Genre.PLATFORMER, Game.Tech.LOWPOLY, i, "Игра %d" % i, S.SPACE)
		r.score = ReleaseScore.new()
		r.score.critics = 6.0
		r.score.bugs = 1 if i == 1 else 0
		r.cost = 1000
		r.score.sales_first = 999 if i == 2 else 1000
		run.records.append(r)
		var ids := run.check_achievements().map(func(a: AchievementDef) -> StringName: return a.id)
		# Первая игра открывает космос, третья зомби (полировка 2026-11-17).
		var want: Array = {0: [&"first_game"], 2: [&"three_games"], 4: [&"no_trace"]}.get(i, [])
		_expect(ids == want, "релиз %d: %s" % [i + 1, ids])
		if i == 0:
			_expect(run.unlocked_settings().has(S.SPACE) and not run.unlocked_settings().has(S.ZOMBIES), "космос после первой игры")
	_expect(run.check_achievements().is_empty(), "сладкая жизнь без окупаемости")
	run.records[2].score.sales_first = 1000
	_expect(_ids(run.check_achievements()) == [&"sweet_life"], "сладкая жизнь")
	# Трилогия: третья часть, ремейк не в счёт.
	run.records[2].part = 3
	run.records[2].remake = true
	_expect(run.check_achievements().is_empty(), "трилогия ремейком")
	run.records[2].remake = false
	_expect(_ids(run.check_achievements()) == [&"trilogy"], "трилогия")
	# Пять технологий за забег.
	for i in 4:
		run.records[i].tech = i as Game.Tech
	_expect(run.check_achievements().is_empty(), "пять технологий на четырёх")
	run.records[4].tech = Game.Tech.THREED
	run.records[3].tech = Game.Tech.LOWPOLY
	_expect(_ids(run.check_achievements()) == [&"five_techs"], "пять технологий")
	# «Девять из десяти» (id ten): все критики от 9 (2026-11-18, было 10). Общая 9 без багов на ретро
	# с новизной даёт её, 8.5 нет: у Игната (без багов +0.4) там 8.9.
	var top := run.records[1]
	top.tech = Game.Tech.BIT8
	top.score.bugs = 0
	top.score.novelty = 1.0
	top.score.critics = 8.5
	_expect(run.check_achievements().is_empty(), "девятка на 8.5")
	top.score.critics = 9.0
	_expect(_ids(run.check_achievements()) == [&"ten"], "десятка: низшая %d" % Achievements._lowest_critic(top, run))
	# Концовка.
	_expect(run.check_achievements(null, &"sale").is_empty(), "офис за продажу")
	_expect(_ids(run.check_achievements(null, &"corporation")) == [&"corporation"], "корпорация")
	_expect(run.unlocked_settings().size() == Game.Setting.size(), "открыто %d" % run.unlocked_settings().size())
	# Сеттинг не покупается (2026-11-17): в предложении после релиза только жанры и технологии.
	var fresh := RunState.start(9, true)
	fresh.profile = Profile.new()
	for i in 30:
		var offer := StudioOffer.compose(fresh.upgrades, fresh.studio, fresh.unlocked_genres(), fresh.unlocked_techs(),
				fresh.rng, 3, fresh.unlocked_settings())
		for d: UpgradeDef in offer:
			_expect(d.kind != UpgradeDef.Kind.CAPABILITY and d.setting < 0, "в предложении не жанр и не технология: %s" % d)
	_staff()
	# Старый слот: рынок на три сеттинга дорастает, стартовая тройка прежняя.
	var old := fresh.to_save(&"release")
	old.start_settings = [0, 1, 2]
	old.market.demand_setting.resize(3)
	old.market.saturation_setting.resize(3)
	var back := RunState.from_save(old)
	_expect(back.start_settings == ([S.PIRATES, S.SPACE, S.CASTLES] as Array[Game.Setting])
			and back.market.demand_setting.size() == Game.Setting.size(), "старый слот: %s" % [back.start_settings])
	AutoTest.note("achievements: %s" % [prof.achievements.keys()])


## Штат и доска соискателей (спека `docs/specs/staff.md`): сложный процент, эффекты ролей,
## срок соискателя, наём с запасом на релиз, сложность мини-игр.
func _staff() -> void:
	var R := Staff.Role
	var G := Staff.Grade
	var t := StaffTuning.load_default()
	var run := RunState.start(11, true)
	_expect(run.board.size() == t.board_start, "на старте соискателей %d" % run.board.size())
	for m in run.board:
		_expect(m.until == t.board_stay, "соискатель ждёт до релиза %d" % m.until)
	_expect(is_equal_approx(run.t_value(), run.tuning.t_start), "сложность первого релиза %.2f" % run.t_value())
	var st := run.studio
	st.hire(StaffMember.make(R.ARTIST, G.JUNIOR))
	st.hire(StaffMember.make(R.ARTIST, G.MIDDLE))
	_expect(is_equal_approx(st.ease(Game.Aspect.GRAPHICS), 1.0 - 0.9 * 0.8) and st.ease(Game.Aspect.SOUND) == 0.0,
			"два художника сложным процентом: %.3f" % st.ease(Game.Aspect.GRAPHICS))
	var graphics: MinigameDef = null
	var other: MinigameDef = null
	for d in run.minigames:
		if d.kind == MinigameDef.Kind.ASPECT and d.aspect == Game.Aspect.GRAPHICS:
			graphics = d
		elif d.kind == MinigameDef.Kind.ASPECT and other == null:
			other = d
	if graphics != null and other != null:
		_expect(is_equal_approx(run.t_for(graphics), run.t_value() * 0.72) and is_equal_approx(run.t_for(other), run.t_value()),
				"художники упрощают только графику: %.3f и %.3f" % [run.t_for(graphics), run.t_for(other)])
	# Жанр и технология (2026-11-18): от `t_start` до `t_owner_max` на капе, аспектные до 1.
	var owner: MinigameDef = null
	for d in run.minigames:
		if d.kind != MinigameDef.Kind.ASPECT:
			owner = d
			break
	if owner != null:
		var release := run.release
		run.release = run.cap
		_expect(is_equal_approx(run.t_for(owner), run.tuning.t_owner_max) and is_equal_approx(run.t_value(), 1.0),
				"на капе жанр и технология %.2f, аспекты %.2f" % [run.t_for(owner), run.t_value()])
		run.release = release
		_expect(is_equal_approx(run.t_for(owner), run.tuning.t_start), "жанр и технология на первом релизе %.2f" % run.t_for(owner))
	_expect(st.replays() == 0 and st.bugfix_offers() == 1 and not st.sequels_unlocked() and st.insider_level() == 0, "пустые эффекты")
	st.hire(StaffMember.make(R.LEAD, G.SENIOR))
	_expect(st.replays() == 1, "тимлид-сеньор: повторов %d" % st.replays())
	st.hire(StaffMember.make(R.TESTER, G.JUNIOR))
	_expect(st.bugfix_offers() == 1 and is_equal_approx(st.bugfix_discount(), t.value(R.TESTER, G.JUNIOR)), "тестировщик-джуниор")
	st.hire(StaffMember.make(R.TESTER, G.SENIOR))
	_expect(st.bugfix_offers() == 2, "тестировщик-сеньор: второй спринт багфикса")
	var lead_rng := RandomNumberGenerator.new()
	lead_rng.seed = 7
	var low_ok := true
	for k in 300:
		var m := Staff.roll([], t, lead_rng, 0)
		if (m.role == R.LEAD and m.grade != G.SENIOR) or (m.role == R.ANALYST and m.grade != G.MIDDLE):
			low_ok = false
	_expect(low_ok, "тимлид приходит только сеньором, аналитик только мидлом")
	st.hire(StaffMember.make(R.PRODUCER, G.JUNIOR))
	_expect(st.sequels_unlocked() and not st.remakes_unlocked() and st.producer_discount() == 0.0, "продюсер-джуниор")
	st.hire(StaffMember.make(R.PRODUCER, G.SENIOR))
	_expect(st.remakes_unlocked() and st.producer_discount() > 0.0, "продюсер-сеньор")
	st.hire(StaffMember.make(R.ANALYST, G.MIDDLE))
	_expect(st.insider_level() == 2, "аналитик-мидл: уровень %d" % st.insider_level())
	st.hire(StaffMember.make(R.MANAGER, G.JUNIOR))
	st.hire(StaffMember.make(R.MANAGER, G.SENIOR))
	_expect(is_equal_approx(st.discount(run.economy), 1.0 - 0.95 * 0.85), "менеджеры: %.4f" % st.discount(run.economy))
	# Наём с доски: цена сразу, зарплата в содержание, запас на релиз не тратится.
	var hired := RunState.start(12, true)
	var m: StaffMember = hired.board[0]
	var cash := hired.wallet.cash
	var upkeep := hired.upkeep.total()
	_expect(hired.hire(m) and hired.wallet.cash == cash - hired.hire_price(m)
			and hired.upkeep.total() == upkeep + hired.hire_salary(m) and hired.studio.staff == [m] and not hired.board.has(m), "наём")
	hired.wallet.cash = hired.cheapest_next() + hired.hire_price(hired.board[0]) - 1
	_expect(not hired.hire(hired.board[0]), "наём съел запас на релиз")
	# Доска после релизов: по `board_add` приходят, отсидевшие `board_stay` уходят.
	var left := hired.board.size()
	hired.release = 2
	hired.refresh_board()
	_expect(hired.board.size() == left + t.board_add, "после релиза на доске %d" % hired.board.size())
	hired.release = t.board_stay + 1
	hired.refresh_board()
	for b in hired.board:
		_expect(b.until >= hired.release, "на доске остался просроченный соискатель")
	# Слот помнит штат и доску.
	var back := RunState.from_save(hired.to_save(&"release"))
	_expect(back.studio.staff.size() == 1 and back.board.size() == hired.board.size(), "слот: штат %d, доска %d" % [
			back.studio.staff.size(), back.board.size()])
	AutoTest.note("staff: %s; доска %s" % [st.staff, hired.board])


func _ids(list: Array[AchievementDef]) -> Array:
	return list.map(func(a: AchievementDef) -> StringName: return a.id)


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("profile: " + what)
