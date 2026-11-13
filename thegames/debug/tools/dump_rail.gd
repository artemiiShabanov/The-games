extends SceneTree
## Маршрут «рельсового тира» (#114) по сиду текстом и бой ботов без окна:
## `Godot --headless --path thegames -s debug/tools/dump_rail.gd -- <seed> [count]`.
## С `count` больше единицы: сводка по сидам (отказы генератора, сколько раз бот WIN дошёл, с
## какими потерями, время).

func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var t := ShooterLowpolyGenTuning.load_default()
	var rules := ShooterLowpolyTuning.load_default()
	if count > 1:
		var bad := 0
		var done := 0
		var lost := 0
		var lives := [0, 0, 0, 0]
		var seconds: Array[float] = []
		var foes := 0
		var accuracy := 0.0
		for sd in range(seed_, seed_ + count):
			var level := RailLevelGen.generate(sd, t, rules)
			var why := RailLevelGen.validate(level, t, rules)
			bad += 0 if why == "" else 1
			var win := RailSim.simulate(level, rules, AutoTest.BotMode.WIN)
			var lose := RailSim.simulate(level, rules, AutoTest.BotMode.LOSE)
			done += 1 if win.finished else 0
			lost += 1 if lose.ended and not lose.finished else 0
			foes += level.hostiles()
			accuracy += float(win.hits) / maxf(win.shots, 1.0)
			if win.finished:
				lives[win.lives] += 1
				seconds.append(win.time)
			if not win.finished or why != "" or win.hostage_hits > 0 or not (lose.ended and not lose.finished):
				print("сид %d: %s WIN %s %.1f с, жизней %d, убито %d из %d, в пленных %d | LOSE %s %.1f с" % [sd,
						"" if why == "" else "ГЕНЕРАТОР: " + why + ";", "дошёл" if win.finished else "НЕ ДОШЁЛ", win.time, win.lives,
						win.kills, level.hostiles(), win.hostage_hits, "ок" if lose.ended and not lose.finished else "ПРОВАЛ", lose.time])
		seconds.sort()
		var n := seconds.size()
		print("сидов %d: генератор отказал на %d; WIN дошёл %d, осталось жизней [0,1,2,3] %s, врагов в среднем %.1f, точность %.0f%%; LOSE не дошёл %d; время: медиана %.1f с, от %.1f до %.1f" % [
				count, bad, done, lives, float(foes) / count, accuracy / count * 100.0, lost, seconds[n / 2] if n > 0 else 0.0,
				seconds[0] if n > 0 else 0.0, seconds[n - 1] if n > 0 else 0.0])
		quit(0)
		return
	var level := RailLevelGen.generate(seed_, t, rules)
	var why := RailLevelGen.validate(level, t, rules)
	print("сид %d: путь %.0f м, остановок %d, укрытий %d, врагов %d (метателей %d, капитанов %d, бегунов %d), пленных %d, бочек с порохом %d, проверка: %s" % [
			seed_, level.length(), level.stops.size() - 1, level.covers.size(), level.hostiles(), level.count(RailLevel.Kind.THROWER),
			level.count(RailLevel.Kind.CAPTAIN), level.count(RailLevel.Kind.RUNNER), level.count(RailLevel.Kind.HOSTAGE), level.kegs.size(),
			"ок" if why == "" else why])
	var names := ["матрос", "метатель", "капитан", "пленный", "бегун"]
	for i in level.stops.size():
		var s := level.stops[i]
		print("остановка %d: (%.1f, %.1f, %.1f), курс %.0f°, наклон %.0f°, ехать %.1f с, групп %d" % [i, s.pos.x, s.pos.y, s.pos.z,
				rad_to_deg(s.yaw), rad_to_deg(s.pitch), s.travel, s.groups])
		for f in level.foes:
			if f.stop == i:
				print("  %s: группа %d, задержка %.2f, укрытие %d, целится %.2f с" % [names[f.kind], f.group, f.delay, f.cover, f.aim])
	for mode: AutoTest.BotMode in [AutoTest.BotMode.WIN, AutoTest.BotMode.LOSE]:
		var sim := RailSim.simulate(level, rules, mode)
		print("бот %s: %s за %.1f с, жизней %d, выстрелов %d, попаданий %d, убито %d, в пленных %d" % [
				"WIN" if mode == AutoTest.BotMode.WIN else "LOSE", "дошёл" if sim.finished else "не дошёл", sim.time, sim.lives, sim.shots,
				sim.hits, sim.kills, sim.hostage_hits])
	quit(0)
