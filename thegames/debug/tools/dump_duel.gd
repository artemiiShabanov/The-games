extends SceneTree
## Дамп дуэли на реакцию (файтинг × вектор, #94) по сиду в консоль: по раунду пауза до вспышки
## и задержка соперника, проверка генератора и прогон без окна ботом WIN и ботом LOSE
## (`DuelSim.simulate`). С двумя числами сиды подряд по строке на сид и сводка. Третьим
## аргументом баги через запятую: `ghost`, `float`, `immortal`, `frail`.
##   Godot --headless --path thegames -s debug/tools/dump_duel.gd -- <seed> [count] [bug,bug]

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var bugs: PackedStringArray = args[2].split(",", false) if args.size() > 2 else PackedStringArray()
	var t := FightingVectorGenTuning.load_default()
	var dt := FightingVectorTuning.load_default()
	var setup := func(s: DuelSim) -> void:
		if bugs.has("ghost"):
			s.pass_every = 2
		if bugs.has("float"):
			s.rival_mult = 0.75
		s.immortal = bugs.has("immortal")
		s.frail = bugs.has("frail")
	if count > 1:
		var wins := 0
		var losses := 0
		var seconds := 0.0
		for sd in range(seed_, seed_ + count):
			var plan := DuelPlanGen.generate(sd, t)
			var win := DuelSim.simulate(plan, dt, AutoTest.BotMode.WIN, 120.0, setup)
			var lose := DuelSim.simulate(plan, dt, AutoTest.BotMode.LOSE, 120.0, setup)
			wins += 1 if win.won else 0
			losses += 1 if lose.ended and not lose.won else 0
			seconds += win.time
			print("сид %d: WIN %s %d:%d (ничьих %d) за %.1f с | LOSE %s %d:%d за %.1f с, фальстартов %d" % [sd,
					"ок" if win.won else "ПРОВАЛ", win.hero_wins, win.rival_wins, win.draws, win.time,
					"ок" if lose.ended and not lose.won else "ПРОВАЛ", lose.hero_wins, lose.rival_wins, lose.time, lose.false_starts])
		print("WIN побед %d из %d, LOSE поражений %d из %d; дуэль бота WIN в среднем %.1f с" % [wins, count, losses, count,
				seconds / count])
		quit(0)
		return true
	var plan := DuelPlanGen.generate(seed_, t)
	var why := DuelPlanGen.validate(plan, t)
	print("сид %d, раундов %d, проверка: %s" % [seed_, plan.rounds(), "ок" if why == "" else why])
	for i in plan.rounds():
		print("раунд %d: пауза %.2f с, соперник бьёт через %.2f с" % [i + 1, plan.waits[i], plan.delays[i]])
	for mode: AutoTest.BotMode in [AutoTest.BotMode.WIN, AutoTest.BotMode.LOSE]:
		var r := DuelSim.simulate(plan, dt, mode, 120.0, setup)
		print("%s: %s %d:%d, ничьих %d, фальстартов %d, за %.1f с" % ["WIN" if mode == AutoTest.BotMode.WIN else "LOSE",
				"победа" if r.won else ("поражение" if r.ended else "не закончил"), r.hero_wins, r.rival_wins, r.draws,
				r.false_starts, r.time])
	quit(0)
	return true
