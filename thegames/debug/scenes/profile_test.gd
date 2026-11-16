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
	_expect(run.unlocked_settings() == ([S.ZOMBIES, S.SPACE, S.CASTLES] as Array[Game.Setting]), "старт %s" % [run.unlocked_settings()])
	_expect(Achievements.load_all().size() == 7, "достижений %d" % Achievements.load_all().size())
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
	# Серии: без багов три подряд, окупились пять подряд; срыв серии обнуляет.
	for i in 5:
		var r := GameRecord.create(Game.Genre.PLATFORMER, Game.Tech.LOWPOLY, i, "Игра %d" % i, S.SPACE)
		r.score = ReleaseScore.new()
		r.score.critics = 6.0
		r.score.bugs = 1 if i == 1 else 0
		r.cost = 1000
		r.score.sales_first = 999 if i == 0 else 1000
		run.records.append(r)
		var ids := run.check_achievements().map(func(a: AchievementDef) -> StringName: return a.id)
		_expect(ids == ([&"no_trace"] if i == 4 else []), "релиз %d: %s" % [i + 1, ids])
	_expect(run.check_achievements().is_empty(), "сладкая жизнь без окупаемости")
	run.records[0].score.sales_first = 1000
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
	# Десятка: все критики 10. Общая 10 без багов на ретро с новизной даёт её, 9.5 нет.
	var top := run.records[1]
	top.tech = Game.Tech.BIT8
	top.score.bugs = 0
	top.score.novelty = 1.0
	top.score.critics = 9.5
	_expect(run.check_achievements().is_empty(), "десятка на 9.5")
	top.score.critics = 10.0
	_expect(_ids(run.check_achievements()) == [&"ten"], "десятка: низшая %d" % Achievements._lowest_critic(top, run))
	# Концовка.
	_expect(run.check_achievements(null, &"sale").is_empty(), "офис за продажу")
	_expect(_ids(run.check_achievements(null, &"corporation")) == [&"corporation"], "корпорация")
	_expect(run.unlocked_settings().size() == Game.Setting.size(), "открыто %d" % run.unlocked_settings().size())
	# «Новый сеттинг»: одна карточка на предложение, только закрытые, покупка открывает на забег.
	var fresh := RunState.start(9, true)
	fresh.profile = Profile.new()
	fresh.profile.achievements[&"treasure"] = 1
	var seen := {}
	for i in 60:
		var offer := StudioOffer.compose(fresh.upgrades, fresh.studio, fresh.unlocked_genres(), fresh.unlocked_techs(),
				fresh.rng, 3, fresh.unlocked_settings())
		var cards := offer.filter(func(d: UpgradeDef) -> bool: return d.setting >= 0)
		_expect(cards.size() <= 1, "сеттингов в предложении %d" % cards.size())
		for d: UpgradeDef in cards:
			seen[d.setting] = true
			_expect(not fresh.unlocked_settings().has(d.setting as Game.Setting), "предложен открытый сеттинг %d" % d.setting)
	_expect(seen.size() == 6 and not seen.has(int(S.PIRATES)), "предлагались сеттинги %s" % [seen.keys()])
	var ninja := UpgradePool.find(fresh.upgrades, &"setting_ninja")
	_expect(ninja != null and ninja.price(fresh.economy) == fresh.economy.capability_price(&"new_setting"), "цена нового сеттинга")
	fresh.studio.buy(ninja, 1)
	_expect(fresh.unlocked_settings().has(S.NINJA), "купленный сеттинг не открыт")
	_expect(not fresh.profile.achievements.has(&"no_trace"), "покупка выдала достижение")
	# Старый слот: рынок на три сеттинга дорастает, стартовая тройка прежняя.
	var old := fresh.to_save(&"release")
	old.start_settings = [0, 1, 2]
	old.market.demand_setting.resize(3)
	old.market.saturation_setting.resize(3)
	var back := RunState.from_save(old)
	_expect(back.start_settings == ([S.PIRATES, S.SPACE, S.CASTLES] as Array[Game.Setting])
			and back.market.demand_setting.size() == Game.Setting.size(), "старый слот: %s" % [back.start_settings])
	AutoTest.note("achievements: %s" % [prof.achievements.keys()])


func _ids(list: Array[AchievementDef]) -> Array:
	return list.map(func(a: AchievementDef) -> StringName: return a.id)


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("profile: " + what)
