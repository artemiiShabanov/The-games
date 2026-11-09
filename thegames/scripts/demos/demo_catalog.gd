class_name DemoCatalog
extends RefCounted
## Каталог демок по паре жанр × технология (#45), спека `docs/specs/demos.md`: сцена лежит в
## `res://scenes/demos/<жанр>_<технология>.tscn`. Петля (плейтест, «В демо» из ленты) и стрим
## ленты берут демку записи отсюда, а не зашитый платформер. Пока демки приходят по одной,
## пары без сцены в конструкторе закрыты с подписью «демка в работе».

const DIR := "res://scenes/demos/"
const GENRE_KEYS: Array[String] = ["platformer", "racing", "shooter", "sport", "fighting"]
const TECH_KEYS: Array[String] = ["ascii", "bit8", "bit16", "lowpoly", "threed"]

## Для тестов механики экранов: считать, что демка есть у любой пары (замки «демка в работе»
## не мешают проверять ремейки и мышь). В игре всегда false.
static var pretend_all := false


static func path(genre: Game.Genre, tech: Game.Tech) -> String:
	return DIR + GENRE_KEYS[genre] + "_" + TECH_KEYS[tech] + ".tscn"


static func has_demo(genre: Game.Genre, tech: Game.Tech) -> bool:
	return pretend_all or ResourceLoader.exists(path(genre, tech))


## Сцена демки пары или null, если её ещё нет.
static func scene(genre: Game.Genre, tech: Game.Tech) -> PackedScene:
	if not has_demo(genre, tech):
		return null
	return load(path(genre, tech)) as PackedScene


## Новая демка записи или null.
static func create(record: GameRecord) -> Demo:
	if not ResourceLoader.exists(path(record.genre, record.tech)):
		return null
	var s := load(path(record.genre, record.tech)) as PackedScene
	return s.instantiate() as Demo if s != null else null
