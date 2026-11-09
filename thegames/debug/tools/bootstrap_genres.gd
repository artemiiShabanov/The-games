extends SceneTree
## Разовое создание прокачек жанров (#45): четыре `UpgradeDef` вида GENRE в
## `resources/upgrades/genre_<жанр>.tres`. Цена и надбавка общие из `economy.tres`
## (`genre_unlock_price`, `genre_unlock_upkeep`). Стартовый платформер не предлагается.
##   Godot --headless --path thegames -s debug/tools/bootstrap_genres.gd

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	for g in [Game.Genre.RACING, Game.Genre.SHOOTER, Game.Genre.SPORT, Game.Genre.FIGHTING]:
		var d := UpgradeDef.new()
		var key: String = DemoCatalog.GENRE_KEYS[g]
		d.id = StringName("genre_" + key)
		d.kind = UpgradeDef.Kind.GENRE
		d.genre = g as Game.Genre
		var name: String = Game.genre_name(g)
		d.title = name.substr(0, 1).to_upper() + name.substr(1)
		d.effect_line = "Новый жанр в конструкторе, своя мини-игра в каждом релизе"
		d.prop = "плакат «%s» на стене" % Game.genre_name(g)
		var path: String = UpgradePool.DIR + "genre_" + key + ".tres"
		print("%s: %s" % [path, error_string(ResourceSaver.save(d, path))])
	quit(0)
	return true
