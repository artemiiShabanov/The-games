extends SceneTree
## Дамп заезда гонок × вектор (#91) по сиду в консоль: соперники (полоса, фора, темп), ряды
## препятствий (`#` препятствие, `.` свободно), проверка генератора и прогон без окна ботом WIN
## и ботом LOSE (`LaneSim.simulate`). С двумя числами сиды подряд по строке на сид и сводка.
## Третьим аргументом баги через запятую: `ice`, `walls`, `sneeze`.
##   Godot --headless --path thegames -s debug/tools/dump_lanes.gd -- <seed> [count] [bug,bug]

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var bugs: PackedStringArray = args[2].split(",", false) if args.size() > 2 else PackedStringArray()
	var t := RacingVectorGenTuning.load_default()
	var dt := RacingVectorTuning.load_default()
	var setup := func(s: LaneSim) -> void:
		if bugs.has("ice"):
			s.slide = 1
			s.rival_mult = 1.12
		s.walls_open = bugs.has("walls")
		s.sneeze = bugs.has("sneeze")
	if count > 1:
		var wins := 0
		var losses := 0
		var seconds: Array[float] = []
		var crashes := 0
		for sd in range(seed_, seed_ + count):
			var race := LaneRaceGen.generate(sd, t)
			var win := LaneSim.simulate(race, dt, AutoTest.BotMode.WIN, 240.0, setup)
			var lose := LaneSim.simulate(race, dt, AutoTest.BotMode.LOSE, 240.0, setup)
			wins += 1 if win.won else 0
			losses += 1 if lose.ended and not lose.won else 0
			crashes += win.player.crashes
			if win.won:
				seconds.append(win.time)
			print("сид %d: WIN %s %.1f с, место %d, столкновений %d | LOSE %s %.1f с, место %d, столкновений %d" % [sd,
					"ок" if win.won else "ПРОВАЛ", win.time, win.place(), win.player.crashes,
					"ок" if lose.ended and not lose.won else "ПРОВАЛ", lose.time, lose.place(), lose.player.crashes])
		seconds.sort()
		var n := seconds.size()
		print("WIN побед %d из %d, LOSE поражений %d из %d; время победы: медиана %.1f с, от %.1f до %.1f; столкновений бота WIN в среднем %.2f" % [
				wins, count, losses, count, seconds[n / 2] if n > 0 else 0.0, seconds[0] if n > 0 else 0.0,
				seconds[n - 1] if n > 0 else 0.0, float(crashes) / count])
		quit(0)
		return true
	var race := LaneRaceGen.generate(seed_, t)
	var why := LaneRaceGen.validate(race, t)
	print("сид %d, полос %d, длина %.0f, препятствий %d, старт на полосе %d, проверка: %s" % [seed_, race.lanes, race.length,
			race.obstacles.size(), race.start_lane, "ок" if why == "" else why])
	for r in race.rivals:
		print("соперник: полоса %d, фора %.0f, темп %.0f" % [r.lane, r.head, r.pace])
	var row := ""
	var row_d := -1.0
	for o in race.obstacles:
		if not is_equal_approx(o.y, row_d):
			if row != "":
				print("%6.0f  %s" % [row_d, row])
			row = ".".repeat(race.lanes)
			row_d = o.y
		row = row.substr(0, int(o.x)) + "#" + row.substr(int(o.x) + 1)
	if row != "":
		print("%6.0f  %s" % [row_d, row])
	for mode: AutoTest.BotMode in [AutoTest.BotMode.WIN, AutoTest.BotMode.LOSE]:
		var s := LaneSim.simulate(race, dt, mode, 240.0, setup)
		print("%s: %s за %.1f с, место %d, столкновений %d, соперников на финише %d" % ["WIN" if mode == AutoTest.BotMode.WIN else "LOSE",
				"первый" if s.won else ("не первый" if s.ended else "не закончил"), s.time, s.place(), s.player.crashes, s.rivals_finished])
	quit(0)
	return true
