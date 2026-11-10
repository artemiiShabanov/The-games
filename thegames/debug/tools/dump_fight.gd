extends SceneTree
## Дамп плана соперника файтинга по сиду в консоль: фазы (профиль, секунды, паттерн H верхний,
## L нижний), реакция и промах, мачта и пропы, проверка, попытки генератора; затем раунд без
## окна ботом WIN и ботом LOSE (`FightSim.simulate`) со сводкой. С двумя числами дамп сидов
## подряд по строке на сид.
##   Godot --headless --path thegames -s debug/tools/dump_fight.gd -- <seed> [count]

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if not args.is_empty() else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var t := FightDemoTuning.load_default()
	var gen := FightGenTuning.load_default()
	var wins := 0
	var losses := 0
	for s in range(seed_, seed_ + count):
		var plan := FightPlanGen.generate(s, gen, t.round_seconds)
		var why := FightPlanGen.validate(plan, gen, t.round_seconds)
		var win := FightSim.simulate(plan, t, gen, AutoTest.BotMode.WIN)
		var lose := FightSim.simulate(plan, t, gen, AutoTest.BotMode.LOSE)
		wins += 1 if win.hero_won() else 0
		losses += 0 if lose.hero_won() else 1
		if count > 1:
			print("сид %d: WIN %s %d:%d %.1f с, LOSE %s %d:%d %.1f с | %s" % [s, "ок" if win.hero_won() else "ПРОВАЛ",
					win.hero.health, win.rival.health, win.seconds(), "ок" if not lose.hero_won() else "ПРОВАЛ",
					lose.hero.health, lose.rival.health, lose.seconds(), plan.describe(gen)])
			continue
		print("сид %d: реакция %d шагов, промах %.2f, мачта %+.0f, попыток %d%s, проверка %s" % [
				s, plan.reaction, plan.miss, plan.mast_x, plan.attempts, " (запасной)" if plan.fallback else "",
				"ок" if why == "" else why])
		for i in plan.phases.size():
			var ph := plan.phases[i]
			print("фаза %d: %s %.0f с, паттерн %s" % [i + 1, gen.profiles[ph.profile].title, ph.seconds, ph.pattern])
		for p in plan.props:
			print("проп %s у %s борта в %.0f px" % ["пушка" if p.kind == 0 else "сундук", "левого" if p.x < 0.0 else "правого", absf(p.x)])
		print("WIN: %s" % win.summary())
		print("LOSE: %s" % lose.summary())
	if count > 1:
		print("WIN побед %d из %d, LOSE поражений %d из %d" % [wins, count, losses, count])
	return true
