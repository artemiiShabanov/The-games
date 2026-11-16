extends SceneTree
## Разовое создание каталогов конструктора `resources/catalog/{genres,techs,settings}.tres`
## (#23). Перезаписывает: цвета и теги правятся здесь или в инспекторе, иллюстрации в M5.
##   Godot --headless --path thegames -s debug/tools/bootstrap_catalog.gd

const K := CatalogEntry.Kind

const GENRES := [
	[Game.Genre.PLATFORMER, "platformer", "Платформер", "#E8B93A", ["на платформах", "в прыжке", "над пропастью", "по крышам"]],
	[Game.Genre.RACING, "racing", "Гонки", "#E0457B", ["на трассе", "на полной скорости", "в большой гонке", "до финиша"]],
	[Game.Genre.SHOOTER, "shooter", "Шутер", "#2BB37A", ["в прицеле", "под огнём", "и пушки", "на передовой"]],
	[Game.Genre.SPORT, "sport", "Спорт", "#F07A1C", ["на арене", "в финале", "и мяч", "на чемпионате"]],
	[Game.Genre.FIGHTING, "fighting", "Файтинг", "#8E44AD", ["на ринге", "против всех", "в драке", "один на один"]],
]
const TECHS := [
	[Game.Tech.VECTOR, "vector", "Примитив", "#2F4A40", []],
	[Game.Tech.BIT8, "bit8", "Ретро", "#2F5BFF", []],
	[Game.Tech.BIT16, "bit16", "2D", "#7A4FE0", []],
	[Game.Tech.LOWPOLY, "lowpoly", "3D", "#27AE8F", []],
	[Game.Tech.THREED, "threed", "Продвинутые", "#3A3F8F", []],
]
## Порядок карусели (#139): стартовые зомби, космос, замки, дальше открываемые.
const SETTINGS := [
	[Game.Setting.ZOMBIES, "zombies", "Зомби", "#4E7A3A", ["Зомби", "Мертвецы", "Карантин", "Выжившие", "Последняя ночь"]],
	[Game.Setting.SPACE, "space", "Космос", "#2B2A6B", ["Звёзды", "Астронавты", "Орбита", "Пустота", "Созвездие"]],
	[Game.Setting.CASTLES, "castles", "Замки", "#8A5A2A", ["Рыцари", "Замки", "Осада", "Латники", "Турнир"]],
	[Game.Setting.PIRATES, "pirates", "Пираты", "#1F7A8C", ["Пираты", "Корсары", "Флибустьеры", "Абордаж", "Чёрная метка"]],
	[Game.Setting.SUPERHEROES, "superheroes", "Супергерои", "#C8323C", ["Супергерои", "Плащи", "Маски", "Лига", "Суперсила"]],
	[Game.Setting.FANTASY, "fantasy", "Фэнтези", "#6B3FA0", ["Драконы", "Маги", "Эльфы", "Зелья", "Заклинание"]],
	[Game.Setting.SWEETS, "sweets", "Сладости", "#E46FA8", ["Конфеты", "Пончики", "Карамель", "Зефир", "Сахарная лихорадка"]],
	[Game.Setting.NINJA, "ninja", "Ниндзя", "#2E3440", ["Ниндзя", "Сюрикены", "Тени", "Клан", "Додзё"]],
	[Game.Setting.DINOSAURS, "dinosaurs", "Динозавры", "#B5651D", ["Динозавры", "Ящеры", "Рапторы", "Юрский период", "Мезозой"]],
	[Game.Setting.OFFICE, "office", "Офис", "#5B7C99", ["Офис", "Менеджеры", "Дедлайн", "Планёрка", "Отчёт"]],
]

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	_save(K.GENRE, "genres", GENRES)
	_save(K.TECH, "techs", TECHS)
	_save(K.SETTING, "settings", SETTINGS)
	quit(0)
	return true


func _save(kind: K, name: String, rows: Array) -> void:
	var c := Catalog.new()
	for r in rows:
		var e := CatalogEntry.new()
		e.kind = kind
		e.value = int(r[0])
		e.id = StringName(r[1])
		e.title = r[2]
		e.color = Color(r[3])
		e.title_tags.assign(r[4])
		c.entries.append(e)
	var path := Catalog.DIR + name + ".tres"
	var err := ResourceSaver.save(c, path)
	print("%s: %s (%d)" % [path, error_string(err), c.entries.size()])
