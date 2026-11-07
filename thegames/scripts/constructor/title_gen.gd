class_name TitleGen
extends RefCounted
## Генератор названий из тегов сеттинга (существительные) и жанра (хвосты): «Пираты на
## платформах». Свободного ввода нет, R перегенерирует. Детерминирован от `rng`.


static func make(setting: CatalogEntry, genre: CatalogEntry, rng: RandomNumberGenerator) -> String:
	var nouns := setting.title_tags if setting != null and not setting.title_tags.is_empty() else ["Игра"]
	var tails := genre.title_tags if genre != null and not genre.title_tags.is_empty() else [""]
	var noun: String = nouns[rng.randi_range(0, nouns.size() - 1)]
	var tail: String = tails[rng.randi_range(0, tails.size() - 1)]
	return (noun + " " + tail).strip_edges()


## Следующее название, отличное от текущего, если теги позволяют.
static func another(current: String, setting: CatalogEntry, genre: CatalogEntry, rng: RandomNumberGenerator) -> String:
	for i in 8:
		var t := make(setting, genre, rng)
		if t != current:
			return t
	return make(setting, genre, rng)
