extends SceneTree
## План бросков «в кольцо» (#115) по сиду текстом и игра ботов без окна:
## `Godot --headless --path thegames -s debug/tools/dump_hoop.gd -- <seed> [count]`.
## С `count` больше единицы: сводка по сидам.

func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var t := SportLowpolyGenTuning.load_default()
	var rules := SportLowpolyTuning.load_default()
	if count > 1:
		var bad := 0
		var won := 0
		var lost := 0
		var scores: Array[int] = []
		var made := 0
		var clean := 0
		var seconds := 0.0
		for sd in range(seed_, seed_ + count):
			var plan := HoopPlanGen.generate(sd, t, rules)
			var why := HoopPlanGen.validate(plan, t, rules)
			bad += 0 if why == "" else 1
			var win := HoopSim.simulate(plan, rules, AutoTest.BotMode.WIN)
			var lose := HoopSim.simulate(plan, rules, AutoTest.BotMode.LOSE)
			won += 1 if win.finished else 0
			lost += 1 if not lose.finished else 0
			scores.append(win.score)
			made += win.made
			clean += win.clean
			seconds += win.time
			if not win.finished or why != "" or lose.finished:
				print("сид %d: %s WIN %s очков %d, попал %d, чисто %d | LOSE %s очков %d" % [sd, "" if why == "" else "ПЛАН: " + why + ";",
						"набрал" if win.finished else "НЕ НАБРАЛ", win.score, win.made, win.clean, "ПРОВАЛ" if lose.finished else "ок", lose.score])
		scores.sort()
		print("сидов %d: генератор отказал на %d; WIN набрал порог %d, очков медиана %d (от %d до %d), попаданий в среднем %.1f, чистых %.1f, время %.0f с; LOSE не набрал %d" % [
				count, bad, won, scores[scores.size() / 2], scores[0], scores[scores.size() - 1], float(made) / count, float(clean) / count,
				seconds / count, lost])
		quit(0)
		return
	var plan := HoopPlanGen.generate(seed_, t, rules)
	var why := HoopPlanGen.validate(plan, t, rules)
	print("сид %d: бросков %d, с ветром %d, с ездящим кольцом %d, очков самое большее без серии %d, порог %d, проверка: %s" % [seed_,
			plan.shots.size(), plan.count_wind(), plan.count_moving(), plan.max_points(rules), rules.goal, "ок" if why == "" else why])
	for i in plan.shots.size():
		var s := plan.shots[i]
		print("бросок %d: %.1f м, %d очка, подъём %.0f°, скорость %.2f–%.2f м/с, летит %.2f с, ветер %+d (стрелка %.1f°), кольцо ±%.1f м, зона %.2f±%.3f, шкала %.2f с" % [
				i + 1, s.dist, s.points, rad_to_deg(s.lift), s.v_lo, s.v_hi, s.flight, s.wind, rad_to_deg(s.tick), s.move_amp, s.zone,
				s.zone_half, s.meter])
	for mode: AutoTest.BotMode in [AutoTest.BotMode.WIN, AutoTest.BotMode.LOSE]:
		var sim := HoopSim.simulate(plan, rules, mode)
		print("бот %s: очков %d (%s), попал %d, чисто %d, броски %s, время %.1f с" % ["WIN" if mode == AutoTest.BotMode.WIN else "LOSE",
				sim.score, "порог взят" if sim.finished else "порог не взят", sim.made, sim.clean, sim.results, sim.time])
	quit(0)
