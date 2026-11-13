extends SceneTree
## План «дуэли на саблях» (#125) по сиду текстом и бой ботов без окна:
## `Godot --headless --path thegames -s debug/tools/dump_saber.gd -- <seed> [count]`.
## С `count` больше единицы: сводка по сидам.

const SIDES := ["слева", "сверху", "справа"]


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var t := FightingThreedTuning.load_default()
	if count > 1:
		var bad := 0
		var done := 0
		var lost := 0
		var seconds: Array[float] = []
		var hp: Array[int] = []
		for sd in range(seed_, seed_ + count):
			var plan := SaberPlanGen.generate(sd, t)
			var why := SaberPlanGen.validate(plan, t)
			bad += 0 if why == "" else 1
			var win := SaberSim.simulate(plan, t, AutoTest.BotMode.WIN)
			var lose := SaberSim.simulate(plan, t, AutoTest.BotMode.LOSE)
			done += 1 if win.won else 0
			lost += 1 if not lose.won else 0
			if win.won:
				seconds.append(win.time)
				hp.append(win.hero_hp)
			if not win.won or why != "" or lose.won:
				print("сид %d: %s WIN %s %.1f с, здоровья %d, у соперника %d | LOSE %s" % [sd, "" if why == "" else "ПЛАН: " + why + ";",
						"победил" if win.won else "НЕ ПОБЕДИЛ", win.time, win.hero_hp, win.rival_hp, "ПРОВАЛ" if lose.won else "ок"])
		seconds.sort()
		hp.sort()
		var n := seconds.size()
		print("сидов %d: генератор отказал на %d; WIN победил %d, здоровье медиана %d, от %d; LOSE проиграл %d; время: медиана %.1f с, от %.1f до %.1f" % [
				count, bad, done, hp[n / 2] if n > 0 else 0, hp[0] if n > 0 else 0, lost, seconds[n / 2] if n > 0 else 0.0,
				seconds[0] if n > 0 else 0.0, seconds[n - 1] if n > 0 else 0.0])
		quit(0)
		return
	var plan := SaberPlanGen.generate(seed_, t)
	var why := SaberPlanGen.validate(plan, t)
	print("сид %d: ходов %d, ударов %d, финтов %d, выпадов %d, самая длинная связка %d, проверка: %s" % [seed_, plan.moves.size(), plan.strikes(),
			plan.feints(), plan.lunges(), plan.longest(), "ок" if why == "" else why])
	for i in mini(plan.moves.size(), 16):
		var m := plan.moves[i]
		var line: PackedStringArray = []
		for s in m.strikes:
			line.append("%s%s за %.2f с" % [SIDES[s.side], " (финт: показывает %s)" % SIDES[s.shown] if s.feint() else "", s.windup])
		print("ход %d: пауза %.1f с, %s: %s" % [i + 1, m.pause, "ВЫПАД" if m.lunge else "удары", "; ".join(line)])
	for mode: AutoTest.BotMode in [AutoTest.BotMode.WIN, AutoTest.BotMode.LOSE]:
		var sim := SaberSim.simulate(plan, t, mode)
		print("бот %s: %s за %.1f с, здоровья %d, у соперника %d, ходов %d, попал %d, отбито соперником %d, блоков %d, пропущено %d, уходов %d" % [
				"WIN" if mode == AutoTest.BotMode.WIN else "LOSE", "победил" if sim.won else "не победил", sim.time, sim.hero_hp, sim.rival_hp,
				sim.move, sim.landed, sim.parried, sim.blocks, sim.taken, sim.dodges])
	quit(0)
