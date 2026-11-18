class_name TitleGen
extends RefCounted
## Генератор названий из тегов сеттинга (существительные) и жанра (хвосты): «Пираты на
## платформах». Свободного ввода нет, R перегенерирует. Детерминирован от `rng`.
## По-английски (2026-11-18) хвост жанра переведён шаблоном с `%s` на месте существительного
## («%s: Platform Panic», «%s Grand Prix»), существительное переведено как есть; теги и выбор
## по `rng` общие, так что русское название не меняется. Название остаётся на языке, на котором
## игру создали.


static func make(setting: CatalogEntry, genre: CatalogEntry, rng: RandomNumberGenerator) -> String:
	var nouns := setting.title_tags if setting != null and not setting.title_tags.is_empty() else ["Игра"]
	var tails := genre.title_tags if genre != null and not genre.title_tags.is_empty() else [""]
	var noun: String = nouns[rng.randi_range(0, nouns.size() - 1)]
	var tail: String = tails[rng.randi_range(0, tails.size() - 1)]
	if Lang.english():
		var pattern := Lang.t(tail) if tail != "" else ""
		if pattern.contains("%s"):
			return (pattern % Lang.t(noun)).strip_edges()
		return (Lang.t(noun) + " " + pattern).strip_edges()
	return (noun + " " + tail).strip_edges()


## Следующее название, отличное от текущего, если теги позволяют.
static func another(current: String, setting: CatalogEntry, genre: CatalogEntry, rng: RandomNumberGenerator) -> String:
	for i in 8:
		var t := make(setting, genre, rng)
		if t != current:
			return t
	return make(setting, genre, rng)
