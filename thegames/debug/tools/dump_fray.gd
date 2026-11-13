extends SceneTree
## План «одного против всех» (#125) по сиду текстом и бой ботов без окна:
## `Godot --headless --path thegames -s debug/tools/dump_fray.gd -- <seed> [count]`.
## С `count` больше единицы: сводка по сидам.

const KINDS := ["пират", "щитоносец", "с ножом"]


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
		var best := 0
		for sd in range(seed_, seed_ + count):
			var plan := FrayPlanGen.generate(sd, t)
			var why := FrayPlanGen.validate(plan)
			bad += 0 if why == "" else 1
			var win := FraySim.simulate(plan, t, AutoTest.BotMode.WIN)
			var lose := FraySim.simulate(plan, t, AutoTest.BotMode.LOSE)
			done += 1 if win.won else 0
			lost += 1 if not lose.won else 0
			best += win.best
			if win.won:
				seconds.append(win.time)
				hp.append(win.hero_hp)
			if not win.won or why != "" or lose.won:
				print("сид %d: %s WIN %s %.1f с, здоровья %d, врагов осталось %d | LOSE %s" % [sd, "" if why == "" else "ПЛАН: " + why + ";",
						"победил" if win.won else "НЕ ПОБЕДИЛ", win.time, win.hero_hp, win.left_total(), "ПРОВАЛ" if lose.won else "ок"])
		seconds.sort()
		hp.sort()
		var n := seconds.size()
		print("сидов %d: генератор отказал на %d; WIN победил %d, здоровье медиана %d, от %d, лучшая серия в среднем %d; LOSE проиграл %d; время: медиана %.1f с, от %.1f до %.1f" % [
				count, bad, done, hp[n / 2] if n > 0 else 0, hp[0] if n > 0 else 0, best / count, lost, seconds[n / 2] if n > 0 else 0.0,
				seconds[0] if n > 0 else 0.0, seconds[n - 1] if n > 0 else 0.0])
		quit(0)
		return
	var plan := FrayPlanGen.generate(seed_, t)
	var why := FrayPlanGen.validate(plan)
	print("сид %d: волн %d, врагов %d (щитоносцев %d, с ножом %d), проверка: %s" % [seed_, plan.waves.size(), plan.total(),
			plan.count(FrayPlan.Kind.SHIELD), plan.count(FrayPlan.Kind.KNIFE), "ок" if why == "" else why])
	for w in plan.waves.size():
		var line: PackedStringArray = []
		for k in plan.waves[w].kinds:
			line.append(KINDS[k])
		print("волна %d: %s; замах %.2f с, атака раз в %.1f с, вдвоём с шансом %.0f %%" % [w + 1, ", ".join(line), plan.waves[w].windup,
				plan.waves[w].gap, plan.waves[w].pair * 100.0])
	for mode: AutoTest.BotMode in [AutoTest.BotMode.WIN, AutoTest.BotMode.LOSE]:
		var sim := FraySim.simulate(plan, t, mode)
		print("бот %s: %s за %.1f с, здоровья %d, уложил %d из %d, ударов %d, контратак %d, перекатов %d, отскоков от щита %d, пропущено %d, добиваний %d, лучшая серия %d" % [
				"WIN" if mode == AutoTest.BotMode.WIN else "LOSE", "победил" if sim.won else "не победил", sim.time, sim.hero_hp, sim.kos,
				plan.total(), sim.landed, sim.counters, sim.dodges, sim.bounces, sim.taken, sim.specials, sim.best])
	quit(0)
