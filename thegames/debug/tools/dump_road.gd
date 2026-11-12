extends SceneTree
## Дамп трассы гонки × 16/32-bit (#99) по сиду в консоль: профиль строкой по 20 сегментов
## (`<` и `>` поворот, `{` и `}` крутой, `^` и `v` подъём и спуск, `-` прямая, `F` финиш),
## пропы и монеты числами; проверка генератора и прогон без окна ботом WIN и ботом LOSE
## (`RoadSim.simulate`). С двумя числами сиды подряд по строке на сид и сводка. Третьим
## аргументом баги через запятую: `wild`, `sneeze`, `walls`, `finish`; `nonitro` герой без нитро.
##   Godot --headless --path thegames -s debug/tools/dump_road.gd -- <seed> [count] [bug,bug]

const STEP := 20

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var bugs: PackedStringArray = args[2].split(",", false) if args.size() > 2 else PackedStringArray()
	var t := RacingBit16GenTuning.load_default()
	var dt := RacingBit16Tuning.load_default()
	var setup := func(s: RoadSim) -> void:
		if bugs.has("wild"):
			s.grip = 0.25
			s.rival_mult = 1.15
		s.sneeze = bugs.has("sneeze")
		s.walls_open = bugs.has("walls")
		if bugs.has("finish"):
			s.finish_late = 150.0 * RoadTrack.SEG
		# Без нитро: проверка, что первую тройку без него не обогнать.
		if bugs.has("nonitro"):
			s.nitros = 0
	if count > 1:
		var wins := 0
		var losses := 0
		var seconds: Array[float] = []
		var places: Array[int] = []
		var started := Time.get_ticks_msec()
		for sd in range(seed_, seed_ + count):
			var tr := RoadTrackGen.generate(sd, t)
			var why := RoadTrackGen.validate(tr, t)
			var win := RoadSim.simulate(tr, dt, AutoTest.BotMode.WIN, setup)
			var lose := RoadSim.simulate(tr, dt, AutoTest.BotMode.LOSE, setup)
			wins += 1 if win.won else 0
			losses += 1 if lose.ended and not lose.won else 0
			places.append(win.place)
			if win.won:
				seconds.append(win.time)
			print("сид %d: %sWIN %s место %d за %.1f с, ударов %d, аварий %d, нитро %d, монет %d из %d | LOSE %s место %d за %.1f с" % [sd,
					"" if why == "" else "ПРОВЕРКА: %s; " % why, "ок" if win.won else "ПРОВАЛ", win.place, win.time, win.bumps,
					win.crashes, dt.nitros - win.nitros, win.coins_got, tr.coins.size(), "ок" if not lose.won else "ПРОВАЛ",
					lose.place, lose.time])
		seconds.sort()
		places.sort()
		var n := seconds.size()
		print("WIN побед %d из %d, LOSE поражений %d из %d; места WIN: лучшее %d, медиана %d, худшее %d; время победы: медиана %.1f с, от %.1f до %.1f; счёт %.1f с" % [
				wins, count, losses, count, places[0], places[places.size() / 2], places[places.size() - 1],
				seconds[n / 2] if n > 0 else 0.0, seconds[0] if n > 0 else 0.0, seconds[n - 1] if n > 0 else 0.0,
				(Time.get_ticks_msec() - started) / 1000.0])
		quit(0)
		return true
	var tr := RoadTrackGen.generate(seed_, t)
	var why := RoadTrackGen.validate(tr, t)
	print("сид %d, сегментов %d, финиш %d, пропов %d, монет %d, соперников %d, проверка: %s" % [seed_, tr.count(), tr.finish,
			tr.props.size(), tr.coins.size(), tr.rivals.size(), "ок" if why == "" else why])
	var row := ""
	for i in range(0, tr.count(), STEP):
		var c := 0.0
		for k in STEP:
			c += tr.curve[mini(i + k, tr.count() - 1)]
		c /= STEP
		var dy := tr.y[mini(i + STEP - 1, tr.count() - 1)] - (tr.y[i - 1] if i > 0 else 0.0)
		var ch := "-"
		if absf(c) > 3.0:
			ch = "}" if c > 0.0 else "{"
		elif absf(c) > 0.7:
			ch = ">" if c > 0.0 else "<"
		elif absf(dy) > 400.0:
			ch = "v" if dy < 0.0 else "^"
		if i <= tr.finish and tr.finish < i + STEP:
			ch = "F"
		row += ch
	print(row)
	for r in tr.rivals:
		print("соперник x %.2f z %d темп %.2f" % [r.x, int(r.z), r.speed])
	var win := RoadSim.simulate(tr, dt, AutoTest.BotMode.WIN, setup)
	print("WIN: место %d за %.1f с, ударов %d, аварий %d, монет %d из %d" % [win.place, win.time, win.bumps, win.crashes, win.coins_got, tr.coins.size()])
	var lose := RoadSim.simulate(tr, dt, AutoTest.BotMode.LOSE, setup)
	print("LOSE: место %d за %.1f с" % [lose.place, lose.time])
	quit(0)
	return true
