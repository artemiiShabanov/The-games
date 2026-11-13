extends SceneTree
## План «обороны аванпоста» (#123) по сиду текстом и бой ботов без окна:
## `Godot --headless --path thegames -s debug/tools/dump_outpost.gd -- <seed> [count]`.
## С `count` больше единицы: сводка по сидам.

const KINDS := ["бегун", "щитоносец", "метатель", "великан"]


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var rules := ShooterThreedTuning.load_default()
	if count > 1:
		var bad := 0
		var done := 0
		var lost := 0
		var seconds: Array[float] = []
		var health: Array[int] = []
		var acc := 0.0
		var refills := 0
		for sd in range(seed_, seed_ + count):
			var plan := OutpostPlanGen.generate(sd, rules)
			var why := OutpostPlanGen.validate(plan)
			bad += 0 if why == "" else 1
			var win := OutpostSim.simulate(plan, rules, AutoTest.BotMode.WIN)
			var lose := OutpostSim.simulate(plan, rules, AutoTest.BotMode.LOSE)
			done += 1 if win.won else 0
			lost += 1 if not lose.won else 0
			if win.won:
				seconds.append(win.time)
				health.append(win.health)
				acc += float(win.hits + win.popped + win.booms) / maxi(win.shots, 1)
				refills += win.refills
			if not win.won or why != "" or lose.won:
				print("сид %d: %s WIN %s %.1f с, здоровья %d, волна %d | LOSE %s" % [sd, "" if why == "" else "ПЛАН: " + why + ";",
						"выстоял" if win.won else "НЕ ВЫСТОЯЛ", win.time, win.health, win.wave + 1, "ПРОВАЛ" if lose.won else "ок"])
		seconds.sort()
		health.sort()
		var n := seconds.size()
		print("сидов %d: генератор отказал на %d; WIN выстоял %d, здоровье на финише медиана %d, от %d; меткость %.0f %%, пополнений %.1f; LOSE пал %d; время: медиана %.1f с, от %.1f до %.1f" % [
				count, bad, done, health[n / 2] if n > 0 else 0, health[0] if n > 0 else 0, 100.0 * acc / maxi(n, 1), float(refills) / maxi(n, 1),
				lost, seconds[n / 2] if n > 0 else 0.0, seconds[0] if n > 0 else 0.0, seconds[n - 1] if n > 0 else 0.0])
		quit(0)
		return
	var plan := OutpostPlanGen.generate(seed_, rules)
	var why := OutpostPlanGen.validate(plan)
	print("сид %d: волн %d, врагов %d (бегунов %d, щитоносцев %d, метателей %d, великанов %d), бочек %d, проверка: %s" % [seed_, plan.waves.size(),
			plan.total(), plan.count(OutpostPlan.Kind.RUNNER), plan.count(OutpostPlan.Kind.SHIELD), plan.count(OutpostPlan.Kind.THROWER),
			plan.count(OutpostPlan.Kind.BRUTE), plan.kegs.size(), "ок" if why == "" else why])
	for w in plan.waves.size():
		var line: PackedStringArray = []
		for s in plan.waves[w].spawns:
			line.append("%.1f с %s со стороны %d" % [s.at, KINDS[s.kind], s.side + 1])
		print("волна %d, сторон %d: %s" % [w + 1, plan.sides_of(w), "; ".join(line)])
	for mode: AutoTest.BotMode in [AutoTest.BotMode.WIN, AutoTest.BotMode.LOSE]:
		var sim := OutpostSim.simulate(plan, rules, mode)
		print("бот %s: %s за %.1f с, здоровья %d, волна %d, выстрелов %d, попаданий %d, в щит %d, убито %d из %d, бочек %d, бутылок сбито %d, пополнений %d" % [
				"WIN" if mode == AutoTest.BotMode.WIN else "LOSE", "выстоял" if sim.won else "не выстоял", sim.time, sim.health, sim.wave + 1,
				sim.shots, sim.hits, sim.blocked, sim.kills, plan.total(), sim.booms, sim.popped, sim.refills])
	quit(0)
