extends SceneTree
## Дамп этажей платформера × вектор (#90) по сиду в консоль: сверху вниз линии с дырами (`-`
## линия, пробел дыра, стрелка и скорость линии справа), на этажах враги `>` и `<` по
## направлению, монеты `o`, флаг `F`, старт героя `H`; плюс проверка генератора и прогон без
## окна ботом WIN и ботом LOSE (`TowerSim.simulate`). С двумя числами сиды подряд по строке на
## сид и сводка. Третьим аргументом баги через запятую: `wild`, `sneeze`, `coins`.
##   Godot --headless --path thegames -s debug/tools/dump_tower.gd -- <seed> [count] [bug,bug]

const COLS := 104

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var bugs: PackedStringArray = args[2].split(",", false) if args.size() > 2 else PackedStringArray()
	var t := PlatformerVectorGenTuning.load_default()
	var dt := PlatformerVectorTuning.load_default()
	var setup := func(s: TowerSim) -> void:
		if bugs.has("wild"):
			s.jump_levels = 3
			s.enemy_mult = 2.0
		s.sneeze = bugs.has("sneeze")
		s.coins_high = bugs.has("coins")
	if count > 1:
		var wins := 0
		var losses := 0
		var seconds: Array[float] = []
		for sd in range(seed_, seed_ + count):
			var level := TowerLevelGen.generate(sd, t)
			var win := TowerSim.simulate(level, dt, AutoTest.BotMode.WIN, 300.0, setup)
			var lose := TowerSim.simulate(level, dt, AutoTest.BotMode.LOSE, 300.0, setup)
			wins += 1 if win.won else 0
			losses += 1 if lose.ended and not lose.won else 0
			if win.won:
				seconds.append(win.time)
			print("сид %d: WIN %s %.1f с, жизней %d, падений %d, монет %d | LOSE %s %.1f с, этаж %d" % [sd,
					"ок" if win.won else "ПРОВАЛ", win.time, win.lives, win.falls, win.coins_got,
					"ок" if lose.ended and not lose.won else "ПРОВАЛ", lose.time, lose.level])
		seconds.sort()
		var n := seconds.size()
		print("WIN побед %d из %d, LOSE поражений %d из %d; время победы: медиана %.1f с, от %.1f до %.1f, 90%% до %.1f" % [
				wins, count, losses, count, seconds[n / 2] if n > 0 else 0.0, seconds[0] if n > 0 else 0.0,
				seconds[n - 1] if n > 0 else 0.0, seconds[int(n * 0.9)] if n > 0 else 0.0])
		quit(0)
		return true
	var lv := TowerLevelGen.generate(seed_, t)
	var why := TowerLevelGen.validate(lv, t)
	print("сид %d, этажей %d, дыр %d, врагов %d, монет %d, проверка: %s" % [seed_, lv.floors, lv.holes.size(),
			lv.enemies.size(), lv.coins.size(), "ок" if why == "" else why])
	var k := COLS / lv.width
	for level in range(lv.floors, -1, -1):
		var row := " ".repeat(COLS)
		for c in lv.coins:
			if int(c.y) == level:
				row = _put(row, int(c.x * k), "o")
		for e in lv.enemies_of(level):
			row = _put(row, int(e.x * k), ">" if e.speed > 0.0 else "<")
		if level == lv.floors:
			row = _put(row, int(lv.flag_x * k), "F")
		if level == 0:
			row = _put(row, int(lv.start_x * k), "H")
		print("%d  %s" % [level, row])
		var line := "-".repeat(COLS)
		var note := ""
		for h in lv.holes_of(level):
			for i in COLS:
				if absf(TowerLevel.wrap_delta(h.x, (i + 0.5) / k, lv.width)) <= h.width / 2.0:
					line = _put(line, i, " ")
			note = "%s %.0f" % ["→" if h.speed > 0.0 else "←", absf(h.speed)]
		print("   %s %s" % ["=".repeat(COLS) if level == 0 else line, note])
	for mode: AutoTest.BotMode in [AutoTest.BotMode.WIN, AutoTest.BotMode.LOSE]:
		var r := TowerSim.simulate(lv, dt, mode, 300.0, setup)
		print("%s: %s за %.1f с, этаж %d, жизней %d, падений %d, монет %d" % ["WIN" if mode == AutoTest.BotMode.WIN else "LOSE",
				"флаг" if r.won else ("провал" if r.ended else "не закончил"), r.time, r.level, r.lives, r.falls, r.coins_got])
	quit(0)
	return true


func _put(row: String, i: int, ch: String) -> String:
	i = clampi(i, 0, row.length() - 1)
	return row.substr(0, i) + ch + row.substr(i + 1)
