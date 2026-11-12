extends SceneTree
## Дамп уровня платформера × 16/32-bit «тропа» (#98) по сиду в консоль: профиль земли строкой
## по 32 пикселя (цифра это высота над водой в десятках пикселей, пробел яма), под ним ловушки
## (`V` лиана, `A` арка, `c` краб, `p` попугай, `|` место возврата, `F` флаг); проверка
## генератора и прогон без окна ботом WIN и ботом LOSE (`TrailSim.simulate`). С двумя числами
## сиды подряд по строке на сид и сводка. Третьим аргументом баги через запятую: `wild`,
## `sneeze`, `coins`.
##   Godot --headless --path thegames -s debug/tools/dump_trail.gd -- <seed> [count] [bug,bug]

const CELL := 32.0

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
	var setup := func(s: TrailSim) -> void:
		if bugs.has("wild"):
			s.jump_mult = 3.0
			s.enemy_mult = 2.0
		s.sneeze = bugs.has("sneeze")
		s.coins_high = bugs.has("coins")
	if count > 1:
		var wins := 0
		var losses := 0
		var seconds: Array[float] = []
		var deaths := 0
		var started := Time.get_ticks_msec()
		for sd in range(seed_, seed_ + count):
			var lv := TrailLevelGen.generate(sd, t)
			var why := TrailLevelGen.validate(lv, t)
			var win := TrailSim.simulate(lv, dt, AutoTest.BotMode.WIN, 240.0, setup)
			var lose := TrailSim.simulate(lv, dt, AutoTest.BotMode.LOSE, 240.0, setup)
			wins += 1 if win.won else 0
			losses += 1 if lose.ended and not lose.won else 0
			deaths += win.deaths
			if win.won:
				seconds.append(win.time)
			print("сид %d: %sWIN %s %.1f с, x %d из %d, жизней %d, монет %d из %d | LOSE %s %.1f с, x %d" % [sd,
					"" if why == "" else "ПРОВЕРКА: %s; " % why, "ок" if win.won else "ПРОВАЛ", win.time, int(win.pos.x),
					int(lv.flag_x), win.lives, win.coins_got, lv.coins.size(), "ок" if lose.ended and not lose.won else "ПРОВАЛ",
					lose.time, int(lose.pos.x)])
		seconds.sort()
		var n := seconds.size()
		print("WIN побед %d из %d, LOSE поражений %d из %d; время победы: медиана %.1f с, от %.1f до %.1f; бот WIN теряет жизней в среднем %.2f; счёт %.1f с" % [
				wins, count, losses, count, seconds[n / 2] if n > 0 else 0.0, seconds[0] if n > 0 else 0.0,
				seconds[n - 1] if n > 0 else 0.0, float(deaths) / count, (Time.get_ticks_msec() - started) / 1000.0])
		quit(0)
		return true
	var lv := TrailLevelGen.generate(seed_, t)
	var why := TrailLevelGen.validate(lv, t)
	print("сид %d, ширина %d, ям %d, лиан %d, арок %d, врагов %d, монет %d, проверка: %s" % [seed_, int(lv.width),
			lv.gaps.size() / 2, lv.vines.size(), lv.arches.size(), lv.foes.size(), lv.coins.size(), "ок" if why == "" else why])
	var cells := int(ceil(lv.width / CELL))
	var row := ""
	var marks := ""
	for c in cells:
		var x := c * CELL + CELL * 0.5
		var h := lv.height_at(x)
		row += " " if h == INF else str(clampi(int((lv.water_y - h) / 10.0), 0, 9))
		var m := "."
		for v in lv.vines:
			if absf(v.anchor.x - x) <= CELL * 0.5:
				m = "V"
		for a in lv.arches:
			if x >= a.from and x <= a.to:
				m = "A"
		for f in lv.foes:
			if x >= f.from and x <= f.to:
				m = "c" if f.kind == TrailLevel.FoeKind.CRAB else "p"
		for cp in lv.checkpoints:
			if absf(cp - x) <= CELL * 0.5:
				m = "|"
		if absf(lv.flag_x - x) <= CELL * 0.5:
			m = "F"
		marks += m
	print(row)
	print(marks)
	var win := TrailSim.simulate(lv, dt, AutoTest.BotMode.WIN, 240.0, setup)
	print("WIN: %s за %.1f с, x %d из %d, жизней %d, монет %d из %d" % ["дошёл" if win.won else "не дошёл", win.time,
			int(win.pos.x), int(lv.flag_x), win.lives, win.coins_got, lv.coins.size()])
	var lose := TrailSim.simulate(lv, dt, AutoTest.BotMode.LOSE, 240.0, setup)
	print("LOSE: %s за %.1f с, x %d" % ["дошёл" if lose.won else "не дошёл", lose.time, int(lose.pos.x)])
	quit(0)
	return true
