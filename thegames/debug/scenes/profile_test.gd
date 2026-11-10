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
	AutoTest.note("profile: %s" % p)
	AutoTest.fulfill("profile checks")


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("profile: " + what)
