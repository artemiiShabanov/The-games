extends SceneTree
## Дамп матча футбола × 16/32-bit (#101) по сиду в консоль: план соперника и вратарей, проверка
## генератора и прогон без окна ботом WIN и ботом LOSE (`SoccerSim.simulate`). С двумя числами
## сиды подряд по строке на сид и сводка. Третьим аргументом баги через запятую: `wild`,
## `narrow`, `sneeze`, `space`.
##   Godot --headless --path thegames -s debug/tools/dump_soccer.gd -- <seed> [count] [bug,bug]

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var bugs: PackedStringArray = args[2].split(",", false) if args.size() > 2 else PackedStringArray()
	var t := SportBit16GenTuning.load_default()
	var dt := SportBit16Tuning.load_default()
	var setup := func(s: SoccerSim) -> void:
		if bugs.has("wild"):
			s.bounce_mult = 1.9
		if bugs.has("narrow"):
			s.goal_mult = 0.5
		s.sneeze = bugs.has("sneeze")
		if bugs.has("space"):
			s.space_every = 9.0
	if count > 1:
		var wins := 0
		var losses := 0
		var seconds: Array[float] = []
		var against := 0
		var started := Time.get_ticks_msec()
		for sd in range(seed_, seed_ + count):
			var p := SoccerPlanGen.generate(sd, t)
			var why := SoccerPlanGen.validate(p, t)
			var win := SoccerSim.simulate(p, dt, AutoTest.BotMode.WIN, setup)
			var lose := SoccerSim.simulate(p, dt, AutoTest.BotMode.LOSE, setup)
			wins += 1 if win.won else 0
			losses += 1 if not lose.won else 0
			if win.won:
				seconds.append(win.time)
			against += win.score[1]
			print("сид %d: %sWIN %s %d:%d за %.1f с, ударов %d | LOSE %s %d:%d за %.1f с" % [sd,
					"" if why == "" else "ПРОВЕРКА: %s; " % why, "ок" if win.won else "ПРОВАЛ", win.score[0], win.score[1],
					win.time, win.kicks, "ок" if not lose.won else "ПРОВАЛ", lose.score[0], lose.score[1], lose.time])
		seconds.sort()
		var n := seconds.size()
		print("WIN побед %d из %d, LOSE поражений %d из %d; время победы: медиана %.1f с, от %.1f до %.1f; пропущено WIN в среднем %.2f; счёт %.1f с" % [
				wins, count, losses, count, seconds[n / 2] if n > 0 else 0.0, seconds[0] if n > 0 else 0.0,
				seconds[n - 1] if n > 0 else 0.0, float(against) / count, (Time.get_ticks_msec() - started) / 1000.0])
		quit(0)
		return true
	var p := SoccerPlanGen.generate(seed_, t)
	print("сид %d: соперник бег %.0f, бьёт с %.0f, зарядка %.2f, подкат %.2f, реакция %.2f; вратари прыжок %.0f/%.0f реакция %.2f/%.2f; форма %d; проверка: %s" % [
			seed_, p.rival_speed, p.rival_shot_range, p.rival_charge, p.rival_tackle, p.rival_react, p.keeper_reach,
			p.rival_keeper_reach, p.keeper_react, p.rival_keeper_react, p.rival_kit, SoccerPlanGen.validate(p, t)])
	var win := SoccerSim.simulate(p, dt, AutoTest.BotMode.WIN, setup)
	print("WIN: %s %d:%d за %.1f с, ударов %d" % ["победа" if win.won else "поражение", win.score[0], win.score[1], win.time, win.kicks])
	var lose := SoccerSim.simulate(p, dt, AutoTest.BotMode.LOSE, setup)
	print("LOSE: %s %d:%d за %.1f с" % ["победа" if lose.won else "поражение", lose.score[0], lose.score[1], lose.time])
	quit(0)
	return true
