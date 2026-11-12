extends SceneTree
## Дамп волн битемапа × 16/32-bit (#102) по сиду в консоль: враги по экранам (`T` головорез, `K`
## ножовщик, `B` боцман, сторона и задержка выхода), проверка генератора и прогон без окна ботом
## WIN и ботом LOSE (`BrawlSim.simulate`). С двумя числами сиды подряд по строке на сид и сводка.
## Третьим аргументом баги через запятую: `wild`, `immortal`, `sneeze`, `ghost`.
##   Godot --headless --path thegames -s debug/tools/dump_brawl.gd -- <seed> [count] [bug,bug]

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var bugs: PackedStringArray = args[2].split(",", false) if args.size() > 2 else PackedStringArray()
	var dt := FightingBit16Tuning.load_default()
	var setup := func(s: BrawlSim) -> void:
		if bugs.has("wild"):
			s.launch = 180.0
		s.immortal = bugs.has("immortal")
		s.sneeze = bugs.has("sneeze")
		s.ghost_every = 2 if bugs.has("ghost") else 0
	if count > 1:
		var wins := 0
		var losses := 0
		var seconds: Array[float] = []
		var lost := 0
		var started := Time.get_ticks_msec()
		for sd in range(seed_, seed_ + count):
			var w := BrawlWavesGen.generate(sd, dt.depth)
			var why := BrawlWavesGen.validate(w)
			var win := BrawlSim.simulate(w, dt, AutoTest.BotMode.WIN, setup)
			var lose := BrawlSim.simulate(w, dt, AutoTest.BotMode.LOSE, setup)
			wins += 1 if win.won else 0
			losses += 1 if not lose.won else 0
			lost += win.deaths
			if win.won:
				seconds.append(win.time)
			print("сид %d: %sWIN %s за %.1f с, экран %d, жизней %d, здоровье %d | LOSE %s за %.1f с" % [sd,
					"" if why == "" else "ПРОВЕРКА: %s; " % why, "ок" if win.won else "ПРОВАЛ", win.time, win.screen + 1,
					win.lives, win.hero.hp, "ок" if not lose.won else "ПРОВАЛ", lose.time])
		seconds.sort()
		var n := seconds.size()
		print("WIN побед %d из %d, LOSE поражений %d из %d; время победы: медиана %.1f с, от %.1f до %.1f; WIN теряет жизней в среднем %.2f; счёт %.1f с" % [
				wins, count, losses, count, seconds[n / 2] if n > 0 else 0.0, seconds[0] if n > 0 else 0.0,
				seconds[n - 1] if n > 0 else 0.0, float(lost) / count, (Time.get_ticks_msec() - started) / 1000.0])
		quit(0)
		return true
	var w := BrawlWavesGen.generate(seed_, dt.depth)
	print("сид %d, проверка: %s" % [seed_, BrawlWavesGen.validate(w)])
	for i in w.screens.size():
		var row := "экран %d:" % (i + 1)
		for sp: BrawlWaves.Spawn in w.screens[i]:
			row += " %s%s%.1f" % [["H", "T", "K", "B"][sp.kind], "<" if sp.side < 0.0 else ">", sp.delay]
		print(row)
	var win := BrawlSim.simulate(w, dt, AutoTest.BotMode.WIN, setup)
	print("WIN: %s за %.1f с, экран %d, жизней %d, здоровье %d, ударов %d" % ["победа" if win.won else "поражение", win.time,
			win.screen + 1, win.lives, win.hero.hp, win.hits])
	var lose := BrawlSim.simulate(w, dt, AutoTest.BotMode.LOSE, setup)
	print("LOSE: %s за %.1f с" % ["победа" if lose.won else "поражение", lose.time])
	quit(0)
	return true
