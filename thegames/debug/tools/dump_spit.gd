extends SceneTree
## Дамп тропы платформера × low poly (#112) по сиду в консоль: куски по порядку от старта к
## маяку (вид, яма перед куском, длина, ширина, сдвиг вбок, высоты), на них скелеты `S`, ряды
## ящиков `#`, дублоны `o`; плюс проверка генератора и прогон без окна ботом WIN и ботом LOSE
## (`SpitSim.simulate`). С двумя числами сиды подряд по строке на сид и сводка. Третьим
## аргументом баги через запятую: `wild`, `sneeze`, `coins`.
##   Godot --headless --path thegames -s debug/tools/dump_spit.gd -- <seed> [count] [bug,bug]

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var bugs: PackedStringArray = args[2].split(",", false) if args.size() > 2 else PackedStringArray()
	var t := PlatformerLowpolyGenTuning.load_default()
	var dt := PlatformerLowpolyTuning.load_default()
	var setup := func(s: SpitSim) -> void:
		if bugs.has("wild"):
			s.jump_mult = 3.0
			s.enemy_mult = 2.0
		s.sneeze = bugs.has("sneeze")
		s.coins_high = bugs.has("coins")
	if count > 1:
		var wins := 0
		var clean := 0
		var losses := 0
		var bad := 0
		var seconds: Array[float] = []
		var causes := {}
		var risks := 0
		for sd in range(seed_, seed_ + count):
			var level := SpitLevelGen.generate(sd, t)
			var why := SpitLevelGen.validate(level, t)
			bad += 0 if why == "" else 1
			var win := SpitSim.simulate(level, dt, AutoTest.BotMode.WIN, 300.0, setup)
			var lose := SpitSim.simulate(level, dt, AutoTest.BotMode.LOSE, 300.0, setup)
			wins += 1 if win.won else 0
			clean += 1 if win.won and win.hits == 0 else 0
			losses += 1 if lose.ended and not lose.won else 0
			if win.won:
				seconds.append(win.time)
			risks += level.risks()
			for line in win.hurt_log:
				var cause := line.get_slice(" ", 0)
				causes[cause] = int(causes.get(cause, 0)) + 1
			if not win.won or why != "" or not (lose.ended and not lose.won):
				print("сид %d: %s WIN %s %.1f с, жизней %d, дублонов %d из %d, %s | LOSE %s %.1f с" % [sd,
						"" if why == "" else "ГЕНЕРАТОР: " + why + ";", "ок" if win.won else "ПРОВАЛ", win.time, win.lives, win.coins_got,
						level.coins.size() + level.crates.size(), " / ".join(win.hurt_log) + " ; сейчас: " + win.describe_near() + (" плот" if win.raft >= 0 else ""),
						"ок" if lose.ended and not lose.won else "ПРОВАЛ", lose.time])
		seconds.sort()
		var n := seconds.size()
		print("сидов %d: генератор отказал на %d; WIN побед %d, без потерь %d, потери по причинам %s; LOSE поражений %d; рискованных мест в среднем %.1f; время победы: медиана %.1f с, от %.1f до %.1f" % [
				count, bad, wins, clean, causes, losses, float(risks) / count, seconds[n / 2] if n > 0 else 0.0, seconds[0] if n > 0 else 0.0,
				seconds[n - 1] if n > 0 else 0.0])
		quit(0)
		return true
	var lv := SpitLevelGen.generate(seed_, t)
	var why := SpitLevelGen.validate(lv, t)
	print("сид %d: длина %.0f м, кусков %d, ям %d, плотов %d, уступов %d, поворотов %d, скелетов %d, катков %d, пушек %d, ящиков %d, дублонов %d, рискованных мест %d, проверка: %s" % [
			seed_, lv.total, lv.pieces.size(), lv.gaps(), lv.rafts.size(), lv.steps(), lv.turns(), lv.guards.size(), lv.rollers.size(),
			lv.cannons.size(), lv.crates.size(), lv.coins.size(), lv.risks(), "ок" if why == "" else why])
	for i in lv.pieces.size():
		var p := lv.pieces[i]
		var marks := ""
		for g in lv.guards:
			if g.piece == i:
				marks += " S(%.1f м/с)" % g.speed
		for r in lv.rollers:
			if r.piece == i:
				marks += " бочки(%.1f м/с, раз в %.1f с)" % [r.speed, r.period]
		for c in lv.cannons:
			if c.piece == i:
				marks += " пушка(s %.0f, раз в %.1f с)" % [c.s, c.period]
		var crates := 0
		for c in lv.crates:
			if lv.piece_at(c + Vector3(0.0, 0.01, 0.0)) == i:
				crates += 1
		if crates > 0:
			marks += " " + "#".repeat(crates)
		var before := ""
		if p.raft >= 0:
			before = "плот,"
		elif p.gap > 0.0:
			before = "яма %.1f," % p.gap
		elif i > 0 and absf(p.h0 - lv.pieces[i - 1].h1) > 0.5:
			before = "уступ %+.1f," % (p.h0 - lv.pieces[i - 1].h1)
		var heading := "вперёд" if p.dir.z < -0.5 else ("вправо" if p.dir.x > 0.5 else "влево")
		print("%2d %-6s %-11s %-6s длина %2.0f ширина %.0f высота %+.2f → %+.2f%s" % [i, SpitLevel.Kind.keys()[p.kind], before, heading,
				p.length, p.width, p.h0, p.h1, marks])
	for mode: AutoTest.BotMode in [AutoTest.BotMode.WIN, AutoTest.BotMode.LOSE]:
		var r := SpitSim.simulate(lv, dt, mode, 300.0, setup)
		print("%s: %s за %.1f с, жизней %d, дублонов %d, ящиков %d; %s" % ["WIN" if mode == AutoTest.BotMode.WIN else "LOSE",
				"маяк" if r.won else ("провал" if r.ended else "не закончил"), r.time, r.lives, r.coins_got, r.crates_got,
				" / ".join(r.hurt_log) if not r.hurt_log.is_empty() else r.describe_near()])
	quit(0)
	return true
