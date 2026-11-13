extends SceneTree
## Трасса спринта (#122) по сиду текстом и заезд ботов без окна:
## `Godot --headless --path thegames -s debug/tools/dump_sprint.gd -- <seed> [count]`.
## С `count` больше единицы: сводка по сидам.

func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var t := RacingThreedGenTuning.load_default()
	var rules := RacingThreedTuning.load_default()
	if count > 1:
		var bad := 0
		var done := 0
		var lost := 0
		var places := [0, 0, 0, 0, 0]
		var seconds: Array[float] = []
		var hits := 0
		for sd in range(seed_, seed_ + count):
			var track := SprintTrackGen.generate(sd, t, rules)
			var why := SprintTrackGen.validate(track, t)
			bad += 0 if why == "" else 1
			var win := SprintSim.simulate(track, rules, AutoTest.BotMode.WIN)
			var lose := SprintSim.simulate(track, rules, AutoTest.BotMode.LOSE)
			done += 1 if win.finished else 0
			lost += 1 if not lose.finished else 0
			hits += win.crashes + win.scrapes
			if win.finished:
				places[win.place()] += 1
				seconds.append(win.time)
			if not win.finished or why != "" or lose.finished or win.place() > 2:
				print("сид %d: %s WIN %s %.1f с, место %d, бортов %d, камней %d | LOSE %s" % [sd, "" if why == "" else "ТРАССА: " + why + ";",
						"доехал" if win.finished else "НЕ ДОЕХАЛ на %.0f м" % win.player().s, win.time, win.place(), win.scrapes, win.crashes,
						"ПРОВАЛ" if lose.finished else "ок"])
		seconds.sort()
		var n := seconds.size()
		print("сидов %d: генератор отказал на %d; WIN доехал %d, места [1,2,3,4] %s, ударов в среднем %.1f; LOSE не доехал %d; время: медиана %.1f с, от %.1f до %.1f" % [
				count, bad, done, places.slice(1), float(hits) / count, lost, seconds[n / 2] if n > 0 else 0.0, seconds[0] if n > 0 else 0.0,
				seconds[n - 1] if n > 0 else 0.0])
		quit(0)
		return
	var track := SprintTrackGen.generate(seed_, t, rules)
	var why := SprintTrackGen.validate(track, t)
	print("сид %d: длина %.0f м, поворотов %d (связок %d), самый крутой %.0f м, перепад высот %.1f м, сужений %d, участков песка %d, проверка: %s" % [
			seed_, track.length, track.corners.size(), track.links, track.tightest(), track.climb(), track.narrows.size(), track.sands.size(),
			"ок" if why == "" else why])
	for c in track.corners:
		print("поворот на %.0f м: %s, радиус %.0f м, длина %.0f м" % [c.x, "влево" if c.y > 0.0 else "вправо", absf(c.y), c.z])
	for r in track.narrows:
		print("сужение: %.0f–%.0f м" % [r.x, r.y])
	for r in track.sands:
		print("песок: %.0f–%.0f м" % [r.x, r.y])
	for mode: AutoTest.BotMode in [AutoTest.BotMode.WIN, AutoTest.BotMode.LOSE]:
		var sim := SprintSim.simulate(track, rules, mode)
		var line := ""
		for i in range(1, sim.cars.size()):
			line += " %.1f" % sim.cars[i].finished
		print("бот %s: %s за %.1f с, место %d, предел скорости %.1f м/с, переключений %d, бортов %d, камней %d, касаний %d; соперники финишировали:%s" % [
				"WIN" if mode == AutoTest.BotMode.WIN else "LOSE", "доехал" if sim.finished else "не доехал (%.0f м)" % sim.player().s, sim.time,
				sim.place(), sim.top, sim.shifts, sim.scrapes, sim.crashes, sim.bumps, line])
	quit(0)
