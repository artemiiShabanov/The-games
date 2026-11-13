extends SceneTree
## Склон «спуска по дюне» (#124) по сиду текстом и спуск ботов без окна:
## `Godot --headless --path thegames -s debug/tools/dump_dune.gd -- <seed> [count]`.
## С `count` больше единицы: сводка по сидам.

func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var t := SportThreedTuning.load_default()
	if count > 1:
		var bad := 0
		var done := 0
		var lost := 0
		var seconds: Array[float] = []
		var missed := 0
		var falls := 0
		var straight := 0.0
		for sd in range(seed_, seed_ + count):
			var course := DuneCourseGen.generate(sd, t)
			var why := DuneCourseGen.validate(course, t)
			bad += 0 if why == "" else 1
			var win := DuneSim.simulate(course, t, AutoTest.BotMode.WIN)
			var lose := DuneSim.simulate(course, t, AutoTest.BotMode.LOSE)
			done += 1 if win.won else 0
			lost += 1 if not lose.won else 0
			missed += win.missed
			falls += win.falls
			straight += float(lose.passed) / course.gates.size()
			if win.won:
				seconds.append(win.time)
			if not win.won or why != "" or lose.won:
				print("сид %d: %s WIN %s %.1f с, ворот %d из %d, падений %d | LOSE %s (ворот %d)" % [sd, "" if why == "" else "СКЛОН: " + why + ";",
						"прошёл" if win.won else "НЕ ПРОШЁЛ", win.time, win.passed, course.gates.size(), win.falls, "ПРОВАЛ" if lose.won else "ок",
						lose.passed])
		seconds.sort()
		var n := seconds.size()
		print("сидов %d: генератор отказал на %d; WIN прошёл %d, мимо ворот в среднем %.1f, падений %.1f; LOSE не прошёл %d (ворот прямо %.0f %%); время: медиана %.1f с, от %.1f до %.1f" % [
				count, bad, done, float(missed) / count, float(falls) / count, lost, 100.0 * straight / count, seconds[n / 2] if n > 0 else 0.0,
				seconds[0] if n > 0 else 0.0, seconds[n - 1] if n > 0 else 0.0])
		quit(0)
		return
	var course := DuneCourseGen.generate(seed_, t)
	var why := DuneCourseGen.validate(course, t)
	print("сид %d: длина %.0f м, перепад %.0f м, ворот %d, трамплинов %d, барьеров %d, препятствий %d (пальм %d), проверка: %s" % [seed_, course.length,
			course.drop(), course.gates.size(), course.ramps.size(), course.bars.size(), course.rocks.size(), course.tall_rocks(), "ок" if why == "" else why])
	for g in course.gates:
		print("ворота на %.0f м: вбок %.1f м, ширина %.1f м" % [g.s, g.x, g.half * 2.0])
	for r in course.ramps:
		print("трамплин на %.0f м: вбок %.1f м" % [r.s, r.x])
	for mode: AutoTest.BotMode in [AutoTest.BotMode.WIN, AutoTest.BotMode.LOSE]:
		var sim := DuneSim.simulate(course, t, mode)
		print("бот %s: %s за %.1f с, ворот %d из %d (надо %d), падений %d, срывов канта %d, трамплинов %d, прыжков %d, предел %.0f км/ч" % [
				"WIN" if mode == AutoTest.BotMode.WIN else "LOSE", "прошёл" if sim.won else "не прошёл", sim.time, sim.passed, course.gates.size(),
				sim.need(), sim.falls, sim.catches, sim.jumps, sim.hops, sim.top * 3.6])
	quit(0)
