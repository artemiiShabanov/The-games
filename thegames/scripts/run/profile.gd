class_name Profile
extends RefCounted
## Профиль игрока, общий на все забеги и слоты (`docs/specs/run.md`). Пока только стартовая
## пара прошлого забега (#61): розыгрыш не даёт тот же жанр подряд. Записи забегов, лучшие
## концовки, достижения и сеттинги придут в #69. Файл `user://profile.cfg`; под автотестом
## не читается и не пишется (хозяин не зовёт `load_saved`/`save`).

const PATH := "user://profile.cfg"

## Стартовая пара прошлого забега, −1 если забегов не было.
var last_start_genre := -1
var last_start_tech := -1


static func load_saved() -> Profile:
	var p := Profile.new()
	var cfg := ConfigFile.new()
	if cfg.load(PATH) == OK:
		p.last_start_genre = int(cfg.get_value("run", "last_start_genre", -1))
		p.last_start_tech = int(cfg.get_value("run", "last_start_tech", -1))
	return p


func save() -> void:
	var cfg := ConfigFile.new()
	cfg.load(PATH)
	cfg.set_value("run", "last_start_genre", last_start_genre)
	cfg.set_value("run", "last_start_tech", last_start_tech)
	cfg.save(PATH)
