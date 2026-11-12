extends SceneTree
## Дамп карты шутера × 16/32-bit «до выхода» (#100) по сиду в консоль: клетки (`#` доски,
## `%` камень, `c` каюта, `h` борт, `x` склад, `O` колонна, `E` дверь выхода, `.` пол, `S`
## старт, `K` ключ, `m` скелет с мушкетом, `s` с саблей, `+` аптечка), проверка генератора и прогон без окна ботом WIN и ботом LOSE (`HoldSim.simulate`).
## С двумя числами сиды подряд по строке на сид и сводка. Третьим аргументом баги через
## запятую: `wild`, `sneeze`, `pass`, `endless`, `walls`.
##   Godot --headless --path thegames -s debug/tools/dump_hold.gd -- <seed> [count] [bug,bug]

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var bugs: PackedStringArray = args[2].split(",", false) if args.size() > 2 else PackedStringArray()
	var t := ShooterBit16GenTuning.load_default()
	var dt := ShooterBit16Tuning.load_default()
	var setup := func(s: HoldSim) -> void:
		if bugs.has("wild"):
			s.foe_mult = 1.5
			s.ice = 2.5
		s.sneeze = bugs.has("sneeze")
		s.pass_every = 2 if bugs.has("pass") else 0
		s.extra_per_kill = 1 if bugs.has("endless") else 0
		s.walls_open = bugs.has("walls")
	if count > 1:
		var wins := 0
		var losses := 0
		var seconds: Array[float] = []
		var health := 0
		var started := Time.get_ticks_msec()
		for sd in range(seed_, seed_ + count):
			var m := HoldMapGen.generate(sd, t)
			var why := HoldMapGen.validate(m, t)
			var win := HoldSim.simulate(m, dt, AutoTest.BotMode.WIN, setup)
			var lose := HoldSim.simulate(m, dt, AutoTest.BotMode.LOSE, setup)
			wins += 1 if win.won else 0
			losses += 1 if not lose.won else 0
			if win.won:
				seconds.append(win.time)
				health += win.health
			print("сид %d: %sWIN %s за %.1f с, здоровье %d, убито %d из %d, попаданий по нему %d | LOSE %s за %.1f с" % [sd,
					"" if why == "" else "ПРОВЕРКА: %s; " % why, "ок" if win.won else "ПРОВАЛ", win.time, win.health,
					win.kills, m.foes.size(), win.hurts, "ок" if not lose.won else "ПРОВАЛ", lose.time])
		seconds.sort()
		var n := seconds.size()
		print("WIN побед %d из %d, LOSE поражений %d из %d; время победы: медиана %.1f с, от %.1f до %.1f; здоровье на выходе в среднем %d; счёт %.1f с" % [
				wins, count, losses, count, seconds[n / 2] if n > 0 else 0.0, seconds[0] if n > 0 else 0.0,
				seconds[n - 1] if n > 0 else 0.0, health / maxi(n, 1), (Time.get_ticks_msec() - started) / 1000.0])
		quit(0)
		return true
	var m := HoldMapGen.generate(seed_, t)
	var why := HoldMapGen.validate(m, t)
	print("сид %d, %d×%d, комнат %d, скелетов %d, аптечек %d, проверка: %s" % [seed_, m.width, m.height, m.rooms.size(),
			m.foes.size(), m.medkits.size(), "ок" if why == "" else why])
	var glyph := {HoldMap.Cell.FLOOR: ".", HoldMap.Cell.PLANKS: "#", HoldMap.Cell.STONE: "%", HoldMap.Cell.EXIT: "E",
			HoldMap.Cell.PILLAR: "O", HoldMap.Cell.CABIN: "c", HoldMap.Cell.HULL: "h", HoldMap.Cell.CARGO: "x"}
	for y in m.height:
		var row := ""
		for x in m.width:
			var g: String = glyph[m.cell(x, y)]
			var c := Vector2(x + 0.5, y + 0.5)
			if Vector2i(floor(m.start)) == Vector2i(x, y):
				g = "S"
			elif Vector2i(floor(m.key)) == Vector2i(x, y):
				g = "K"
			for k in m.foes.size():
				if m.foes[k].distance_to(c) < 0.1:
					g = "m" if m.foe_kinds[k] == HoldMap.Foe.MUSKET else "s"
			for k in m.medkits:
				if k.distance_to(c) < 0.1:
					g = "+"
			row += g
		print(row)
	var win := HoldSim.simulate(m, dt, AutoTest.BotMode.WIN, setup)
	print("WIN: %s за %.1f с, здоровье %d, убито %d из %d" % ["вышел" if win.won else "не вышел", win.time, win.health, win.kills, m.foes.size()])
	var lose := HoldSim.simulate(m, dt, AutoTest.BotMode.LOSE, setup)
	print("LOSE: %s за %.1f с" % ["вышел" if lose.won else "не вышел", lose.time])
	quit(0)
	return true
