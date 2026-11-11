extends SceneTree
## Дамп уровня платформера по сиду в консоль: высоты земли (цифры, `.` яма), платформы `=`,
## ходоки `w`, попугаи `v`, монеты `o`, чекпоинт `C`, флаг `F`, плюс проходимость.
##   Godot --headless --path thegames -s debug/tools/dump_level.gd -- <seed> [from] [to] [ascii]
## `ascii` (#90): уровень ASCII-платформера, свой тюнинг генератора, три экрана по 104 колонки.

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var t := PlatformerAsciiTuning.gen() if args.has("ascii") else PlatformerGenTuning.load_default()
	var lv := PlatformerLevelGen.generate(seed_, t)
	var from := int(args[1]) if args.size() > 1 else 0
	var to := mini(int(args[2]) if args.size() > 2 else lv.width, lv.width)
	print("сид %d, ширина %d, проходим %s, флаг %s, чекпоинт %s" % [seed_, lv.width, PlatformerLevelGen.passable(lv, t), lv.flag, lv.checkpoint])
	for row in range(lv.height - 1, -1, -1):
		var line := "%2d " % row
		for x in range(from, to):
			var ch := " "
			if row < lv.ground_top(x):
				ch = "#"
			for p in lv.platforms:
				if p.position.y == row and x >= p.position.x and x < p.position.x + p.size.x:
					ch = "="
			for c in lv.coins:
				if c.x == x and c.y == row:
					ch = "o"
			for e in lv.enemies:
				if e.x == x and e.y == row:
					ch = "v" if e.flying else "w"
			if lv.checkpoint.x == x and lv.checkpoint.y == row:
				ch = "C"
			if lv.flag.x == x and lv.flag.y == row:
				ch = "F"
			line += ch
		print(line)
	var ruler := "   "
	for x in range(from, to):
		ruler += str(x % 10)
	print(ruler)
	quit(0)
	return true
