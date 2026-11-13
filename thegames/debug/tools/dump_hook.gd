extends SceneTree
## Уровень «крюк-кошки» (#121) по сиду текстом и боты без окна:
## `Godot --headless --path thegames -s debug/tools/dump_hook.gd -- <seed> [count]`.
## С `count` больше единицы: сводка по сидам.

const KINDS := ["прыжок", "уступ", "кольца"]


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var t := PlatformerThreedGenTuning.load_default()
	var rules := PlatformerThreedTuning.load_default()
	if count > 1:
		var bad := 0
		var done := 0
		var lost := 0
		var lives := [0, 0, 0, 0]
		var seconds: Array[float] = []
		var rings := 0
		for sd in range(seed_, seed_ + count):
			var level := HookLevelGen.generate(sd, t, rules)
			var why := HookLevelGen.validate(level, t, rules)
			bad += 0 if why == "" else 1
			var win := HookSim.simulate(level, rules, AutoTest.BotMode.WIN)
			var lose := HookSim.simulate(level, rules, AutoTest.BotMode.LOSE)
			done += 1 if win.finished else 0
			lost += 1 if lose.ended and not lose.finished else 0
			rings += level.rings.size()
			if win.finished:
				lives[win.lives] += 1
				seconds.append(win.time)
			if not win.finished or why != "" or lose.finished:
				print("сид %d: %s WIN %s %.1f с, жизней %d, остров %d из %d | LOSE %s" % [sd, "" if why == "" else "УРОВЕНЬ: " + why + ";",
						"дошёл" if win.finished else "НЕ ДОШЁЛ", win.time, win.lives, win.islet, level.gaps.size(), "ПРОВАЛ" if lose.finished else "ок"])
		seconds.sort()
		var n := seconds.size()
		print("сидов %d: генератор отказал на %d; WIN дошёл %d, осталось жизней [0,1,2,3] %s, колец в среднем %.1f; LOSE не дошёл %d; время: медиана %.1f с, от %.1f до %.1f" % [
				count, bad, done, lives, float(rings) / count, lost, seconds[n / 2] if n > 0 else 0.0, seconds[0] if n > 0 else 0.0,
				seconds[n - 1] if n > 0 else 0.0])
		quit(0)
		return
	var level := HookLevelGen.generate(seed_, t, rules)
	var why := HookLevelGen.validate(level, t, rules)
	print("сид %d: путь %.0f м, пропастей %d (прыжков %d, уступов %d, с кольцами %d), колец %d (движущихся %d), самая длинная цепочка %d, камней %d, вещей %d, проверка: %s" % [
			seed_, level.length(), level.gaps.size(), level.count(HookLevel.Kind.JUMP), level.count(HookLevel.Kind.CLIMB),
			level.count(HookLevel.Kind.RINGS), level.rings.size(), level.moving(), level.longest_chain(), level.small(), level.props.size(),
			"ок" if why == "" else why])
	for g in level.gaps.size():
		var gap := level.gaps[g]
		var a := level.islets[g]
		var b := level.islets[g + 1]
		var line: PackedStringArray = []
		for i in level.rings_of(g):
			var r := level.rings[i]
			line.append("%.1f м на высоте %.1f%s" % [Vector2(r.pos.x - gap.a.x, r.pos.z - gap.a.z).length(), r.pos.y,
					" (ходит ±%.1f)" % r.amp if r.amp > 0.0 else ""])
		print("пропасть %d, %s: %.1f м, остров радиусом %.1f на высоте %.1f → радиусом %.1f на высоте %.1f, курс %.0f°%s" % [g + 1, KINDS[gap.kind],
				gap.length(), a.radius, a.pos.y, b.radius, b.pos.y, rad_to_deg(atan2(-gap.dir.x, -gap.dir.y)),
				"" if line.is_empty() else ", кольца: " + "; ".join(line)])
	for mode: AutoTest.BotMode in [AutoTest.BotMode.WIN, AutoTest.BotMode.LOSE]:
		var sim := HookSim.simulate(level, rules, mode)
		print("бот %s: %s за %.1f с, жизней %d, прыжков %d, уступов %d, зацепов %d, падений %d, остров %d" % [
				"WIN" if mode == AutoTest.BotMode.WIN else "LOSE", "дошёл" if sim.finished else "не дошёл", sim.time, sim.lives, sim.jumps,
				sim.climbs, sim.hooks, sim.falls, sim.islet])
	quit(0)
