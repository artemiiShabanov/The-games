extends SceneTree
## Разовое создание пула прокачек `resources/upgrades/*.tres` (#28): семь возможностей из
## спеки студии («новый сеттинг» ждёт M2, технологии и жанры придут со своими вехами). Цены
## и надбавки в `economy.tres`. Перезаписывает.
##   Godot --headless --path thegames -s debug/tools/bootstrap_upgrades.gd

const ROWS := [
	["replay", "Переигровка", "Один проваленный спринт за релиз можно сыграть ещё раз", [], "второй монитор у стола"],
	["replay2", "Вторая переигровка", "Ещё одна переигровка за релиз", ["replay"], "третий монитор"],
	["sequels", "Сиквелы", "В конструкторе появляется переключатель «сиквел»", [], "полка с коробками игр"],
	["remakes", "Ремейки", "В конструкторе появляется переключатель «ремейк»", [], "архивный шкаф"],
	["qa", "Отдел QA", "Второй спринт багфикса за релиз", [], "стол с тестировщиком"],
	["insider", "Инсайдер", "В конструкторе видно, какие жанр и сеттинг в тренде", [], "человечек с телефоном у окна"],
	["manager", "Менеджер", "Цена спринта на 10 % ниже", [], "человечек с планшетом у входа"],
]

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	for r in ROWS:
		var d := UpgradeDef.new()
		d.id = StringName(r[0])
		d.kind = UpgradeDef.Kind.CAPABILITY
		d.title = r[1]
		d.effect_line = r[2]
		for req in r[3]:
			d.requires.append(StringName(req))
		d.prop = r[4]
		var path: String = UpgradePool.DIR + str(r[0]) + ".tres"
		var err := ResourceSaver.save(d, path)
		print("%s: %s" % [path, error_string(err)])
	quit(0)
	return true
