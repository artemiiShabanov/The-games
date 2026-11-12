extends SceneTree
## Дамп уровня платформера × 16/32-bit «по клеткам» (#98) по сиду в консоль: ряд клеток (`_`
## пол, пробел яма, `^` шипы, `Y` якорь, `=` плита), под ним стражники (`g` участок, `G`
## старт), монеты `o`, клетки отдыха `|`, флаг `F`; проверка генератора и прогон без окна
## ботом WIN и ботом LOSE (`GridSim.simulate`). С двумя числами сиды подряд по строке на сид и
## сводка. Третьим аргументом баги через запятую: `wild`, `sneeze`, `coins`.
##   Godot --headless --path thegames -s debug/tools/dump_grid.gd -- <seed> [count] [bug,bug]

const GLYPHS: Array[String] = ["_", " ", "^", "Y", "="]

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var bugs: PackedStringArray = args[2].split(",", false) if args.size() > 2 else PackedStringArray()
	var t := PlatformerBit16GenTuning.load_default()
	var dt := PlatformerBit16Tuning.load_default()
	var setup := func(s: GridSim) -> void:
		if bugs.has("wild"):
			s.jump_over = 3
			s.enemy_mult = 2.0
		s.sneeze = bugs.has("sneeze")
		s.coins_high = bugs.has("coins")
	if count > 1:
		var wins := 0
		var losses := 0
		var seconds: Array[float] = []
		var deaths := 0
		for sd in range(seed_, seed_ + count):
			var lv := GridLevelGen.generate(sd, t)
			var win := GridSim.simulate(lv, dt, AutoTest.BotMode.WIN, 240.0, setup)
			var lose := GridSim.simulate(lv, dt, AutoTest.BotMode.LOSE, 240.0, setup)
			wins += 1 if win.won else 0
			losses += 1 if lose.ended and not lose.won else 0
			deaths += win.deaths
			if win.won:
				seconds.append(win.time)
			print("сид %d: WIN %s %.1f с, клетка %d из %d, жизней %d, монет %d | LOSE %s %.1f с, клетка %d" % [sd,
					"ок" if win.won else "ПРОВАЛ", win.time, win.cell, lv.flag, win.lives, win.coins_got,
					"ок" if lose.ended and not lose.won else "ПРОВАЛ", lose.time, lose.cell])
		seconds.sort()
		var n := seconds.size()
		print("WIN побед %d из %d, LOSE поражений %d из %d; время победы: медиана %.1f с, от %.1f до %.1f; бот WIN теряет жизней в среднем %.2f" % [
				wins, count, losses, count, seconds[n / 2] if n > 0 else 0.0, seconds[0] if n > 0 else 0.0,
				seconds[n - 1] if n > 0 else 0.0, float(deaths) / count])
		quit(0)
		return true
	var lv := GridLevelGen.generate(seed_, t)
	var why := GridLevelGen.validate(lv, t)
	var kinds := lv.counts()
	print("сид %d, клеток %d, ям %d, шипов %d, якорей %d, плит %d, стражников %d, монет %d, проверка: %s" % [seed_, lv.width,
			kinds[1], kinds[2], kinds[3], kinds[4], lv.guards.size(), lv.coins.size(), "ок" if why == "" else why])
	var row := ""
	var marks := ""
	for x in lv.width:
		row += GLYPHS[lv.cells[x]]
		var ch := " "
		for g in lv.guards:
			if x >= g.from and x <= g.to:
				ch = "G" if x == g.start else "g"
		if lv.coins.has(x):
			ch = "o"
		if lv.checkpoints.has(x):
			ch = "|"
		if x == lv.flag:
			ch = "F"
		marks += ch
	print(row)
	print(marks)
	for mode: AutoTest.BotMode in [AutoTest.BotMode.WIN, AutoTest.BotMode.LOSE]:
		var r := GridSim.simulate(lv, dt, mode, 240.0, setup)
		print("%s: %s за %.1f с, клетка %d из %d, жизней %d, монет %d из %d" % ["WIN" if mode == AutoTest.BotMode.WIN else "LOSE",
				"дошёл" if r.won else ("не дошёл" if r.ended else "не закончил"), r.time, r.cell, lv.flag, r.lives, r.coins_got,
				lv.coins.size()])
	quit(0)
	return true
