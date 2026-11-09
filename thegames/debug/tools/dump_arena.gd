extends SceneTree
## Дамп арены шутера по сиду в консоль: палуба `.`, борт `#`, трапы `D`, старт героя `@`, бочки
## `b`, сундуки `c`, пушки `k`, плюс проверка, число попыток генератора и волны (`w` скелет,
## `g` канонир, цифра это трап: 0 верх, 1 право, 2 низ, 3 лево).
##   Godot --headless --path thegames -s debug/tools/dump_arena.gd -- <seed>

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	var args := OS.get_cmdline_user_args()
	var t := ShooterGenTuning.load_default()
	var seed_ := int(args[0]) if not args.is_empty() else 1
	var a := ShooterArenaGen.generate(seed_, t)
	var why := ShooterArenaGen.validate(a, t)
	print("сид %d: %dx%d тайлов, пропов %d, врагов %d, попыток %d%s, проверка %s" % [
			seed_, a.width, a.height, a.props.size(), a.total_enemies(), a.attempts,
			" (без пропов)" if a.fallback else "", "ок" if why == "" else why])
	var marks := {}
	for p in a.props:
		marks[p.cell] = ["b", "c", "k"][p.kind]
	marks[a.start_cell()] = "@"
	for row in a.height:
		var line := ""
		for col in a.width:
			var c := Vector2i(col, row)
			line += str(marks[c]) if marks.has(c) else [".", "#", "D", "?"][a.tile(col, row)]
		print(line)
	for i in a.waves.size():
		var parts: PackedStringArray = []
		for s in a.waves[i].spawns:
			parts.append("%s%d" % ["g" if s.kind == ShooterArena.Enemy.GUNNER else "w", s.door])
		print("волна %d (%d): %s" % [i + 1, a.waves[i].spawns.size(), " ".join(parts)])
	return true
