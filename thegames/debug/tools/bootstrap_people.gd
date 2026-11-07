extends SceneTree
## Разовое создание персонажей ленты и шаблонов текстов (#26): `resources/people/critics.tres`,
## `streamers.tres`, `resources/texts/feed.tres`. Перезаписывает: тексты черновые до M5,
## правятся здесь или в инспекторе.
##   Godot --headless --path thegames -s debug/tools/bootstrap_people.gd

const R := PersonDef.Role
const TR := PersonDef.Nature

const CRITICS := [
	["marta", "Марта Гринвуд", TR.RETRO, "Pixel Gazette", "#E0457B"],
	["ignat", "Игнат Белый", TR.BUG_HATER, "Патчноут", "#2F5BFF"],
	["sol", "Соль Ахметова", TR.NOVELTY, "Новая волна", "#2BB37A"],
]
const STREAMERS := [
	["kraken", "KrakenPlays", TR.BUG_LOVER, "48 тыс. онлайн", "#F07A1C"],
	["polygonna", "Polygonna", TR.LOVER_3D, "21 тыс. онлайн", "#8E44AD"],
	["dedushka", "ДедушкаДжойстик", TR.RETRO, "9 тыс. онлайн", "#1F8A4C"],
]

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	_save_people(R.CRITIC, "critics", CRITICS)
	_save_people(R.STREAMER, "streamers", STREAMERS)
	_save_texts()
	quit(0)
	return true


func _save_people(role: R, file: String, rows: Array) -> void:
	var set := PeopleSet.new()
	for r in rows:
		var p := PersonDef.new()
		p.id = StringName(r[0])
		p.name = r[1]
		p.role = role
		p.nature = r[2]
		p.subtitle = r[3]
		p.accent = Color(r[4])
		set.people.append(p)
	var path := PeopleSet.DIR + file + ".tres"
	print("%s: %s" % [path, error_string(ResourceSaver.save(set, path))])


func _save_texts() -> void:
	var t := FeedTexts.new()
	t.handles.assign(["@noodle_dev", "@pixel_pete", "@gamer_olya", "@retro_rita", "@sashaplays", "@dev_null", "@mira_m", "@kotofey"])
	t.tweets_good.assign([
		"{title}: прошёл за вечер и хочу ещё. {genre} в сеттинге «{setting}» это да {tag}",
		"ну наконец нормальный {genre}, управление как надо {tag}",
		"{tech}, а ощущается дороже. Респект студии {tag}",
		"сидел до двух ночи. {tag}",
	])
	t.tweets_bad.assign([
		"{title} сыроват. Идея есть, рук не хватило {tag}",
		"{genre} на {tech}, ок, но зачем {tag}",
		"дропнул на второй минуте, простите {tag}",
		"ждал большего от сеттинга «{setting}» {tag}",
	])
	t.tweets_viral.assign([
		"ВЫ ВИДЕЛИ КЛИП?? {tag}",
		"весь чат орёт с {title}, это теперь мем {tag}",
		"{tag} в трендах, студия, вы это специально?",
	])
	t.tweets_quiet.assign([
		"кто-нибудь играл в {title}? {tag}",
		"вышла {title}, тихо как-то {tag}",
		"{tag} видел у одного стримера, вроде норм",
	])
	t.critic_warm.assign([
		"«{title}» делает ровно то, что обещает, и делает хорошо. Редкий случай, когда {genre} не утомляет».",
		"«Короткая, цельная, с характером. Сеттинг «{setting}» раскрыт лучше, чем у игр втрое дороже».",
		"«Хочется второй части. Это лучшее, что можно сказать о {genre}».",
	])
	t.critic_neutral.assign([
		"«Крепкая середина: {genre} как {genre}, ни провалов, ни открытий».",
		"«Приятная, но забывается к вечеру. {tech} здесь ни помогает, ни мешает».",
		"«Есть идея, есть исполнение, нет искры. Поиграть можно».",
	])
	t.critic_sour.assign([
		"«Не доделано. Баги не украшают даже сеттинг «{setting}»».",
		"«{title} выглядит как черновик самой себя».",
		"«Я бы подождал патча. Или следующей игры студии».",
	])
	t.critic_nature_remarks.assign([
		"Ретро мне всегда ближе, тут не скрою.",
		"За каждый баг снимаю балл, и это ещё мягко.",
		"Такого сочетания я ещё не видела, за это плюс.",
		"", "",
	])
	t.clip_bug.assign([
		"«{bug}. чат, это лучшее за неделю»",
		"«СМОТРИТЕ. {bug}. я не могу»",
		"«это фича, скажите мне, что это фича»",
	])
	t.clip_clean.assign([
		"«чисто прошёл. красиво, но где хаос?»",
		"«нормальная игра, чат заскучал»",
	])
	t.viewers_viral.assign(["1,2 млн просмотров", "870 тыс. просмотров", "2,4 млн просмотров"])
	t.viewers_noticed.assign(["140 тыс. просмотров", "96 тыс. просмотров", "210 тыс. просмотров"])
	t.viewers_quiet.assign(["3 тыс. просмотров", "1,1 тыс. просмотров", "640 просмотров"])
	print("%s: %s" % [FeedTexts.PATH, error_string(ResourceSaver.save(t, FeedTexts.PATH))])
