extends SceneTree
## План соперника файтинга × low poly (#116) по сиду текстом и бой ботов без окна:
## `Godot --headless --path thegames -s debug/tools/dump_spar.gd -- <seed> [count]`.
## С `count` больше единицы: сводка по сидам.

func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var t := FightingLowpolyGenTuning.load_default()
	var rules := FightingLowpolyTuning.load_default()
	var names := ["рука", "нога", "СИЛЬНЫЙ"]
	if count > 1:
		var bad := 0
		var won := 0
		var lost := 0
		var seconds: Array[float] = []
		var hp := 0
		var taken := 0
		for sd in range(seed_, seed_ + count):
			var plan := SparPlanGen.generate(sd, t)
			var why := SparPlanGen.validate(plan, t)
			bad += 0 if why == "" else 1
			var win := SparSim.simulate(plan, rules, AutoTest.BotMode.WIN)
			var lose := SparSim.simulate(plan, rules, AutoTest.BotMode.LOSE)
			won += 1 if win.finished else 0
			lost += 1 if lose.ended and not lose.finished else 0
			seconds.append(win.time)
			hp += win.hero.hp
			taken += win.taken
			if not win.finished or why != "" or lose.finished:
				print("сид %d: %s WIN %s за %.1f с, здоровье %d против %d | LOSE %s за %.1f с" % [sd, "" if why == "" else "ПЛАН: " + why + ";",
						"победил" if win.finished else "ПРОИГРАЛ", win.time, win.hero.hp, win.rival.hp, "ПРОВАЛ" if lose.finished else "ок", lose.time])
		seconds.sort()
		print("сидов %d: генератор отказал на %d; WIN победил %d, бой: медиана %.1f с (от %.1f до %.1f), здоровья осталось в среднем %d, пропущено ударов %.1f; LOSE проиграл %d" % [
				count, bad, won, seconds[seconds.size() / 2], seconds[0], seconds[seconds.size() - 1], hp / count, float(taken) / count, lost])
		quit(0)
		return
	var plan := SparPlanGen.generate(seed_, t)
	var why := SparPlanGen.validate(plan, t)
	print("сид %d: связок %d, рукой %d, ногой %d, сильных %d, самая длинная %d, проверка: %s" % [seed_, plan.combos.size(),
			plan.count(SparPlan.Move.PUNCH), plan.count(SparPlan.Move.KICK), plan.count(SparPlan.Move.HEAVY), plan.longest(),
			"ок" if why == "" else why])
	for i in plan.combos.size():
		var c := plan.combos[i]
		var line: PackedStringArray = []
		for m in c.moves:
			line.append(names[m])
		print("связка %d: пауза %.2f с, замах %.2f с: %s" % [i + 1, c.gap, c.windup, ", ".join(line)])
	for mode: AutoTest.BotMode in [AutoTest.BotMode.WIN, AutoTest.BotMode.LOSE]:
		var sim := SparSim.simulate(plan, rules, mode)
		print("бот %s: %s за %.1f с, здоровье %d против %d, попал %d (сбоку %d), блоков %d, уходов %d, пропустил %d, связок прошло %d" % [
				"WIN" if mode == AutoTest.BotMode.WIN else "LOSE", "победил" if sim.finished else "проиграл", sim.time, sim.hero.hp,
				sim.rival.hp, sim.hero_hits, sim.flank_hits, sim.blocks, sim.dodges, sim.taken, sim.combo_index])
	quit(0)
