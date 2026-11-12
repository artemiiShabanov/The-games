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
			if not win.won or win.hits > 0 or why != "" or not (lose.ended and not lose.won):
				print("сид %d: %s WIN %s %.1f с, жизней %d, дублонов %d из %d, %s | LOSE %s %.1f с" % [sd,
						"" if why == "" else "ГЕНЕРАТОР: " + why + ";", "ок" if win.won else "ПРОВАЛ", win.time, win.lives, win.coins_got,
						level.coins.size() + level.crates.size(), " / ".join(win.hurt_log),
						"ок" if lose.ended and not lose.won else "ПРОВАЛ", lose.time])
		seconds.sort()
		var n := seconds.size()
		print("сидов %d: генератор отказал на %d; WIN побед %d, без потерь %d; LOSE поражений %d; время победы: медиана %.1f с, от %.1f до %.1f" % [
				count, bad, wins, clean, losses, seconds[n / 2] if n > 0 else 0.0, seconds[0] if n > 0 else 0.0,
				seconds[n - 1] if n > 0 else 0.0])
		quit(0)
		return true
	var lv := SpitLevelGen.generate(seed_, t)
	var why := SpitLevelGen.validate(lv, t)
	print("сид %d: длина %.0f м, кусков %d, ям %d, скелетов %d, ящиков %d, дублонов %d, проверка: %s" % [seed_, lv.length(),
			lv.pieces.size(), lv.gaps(), lv.guards.size(), lv.crates.size(), lv.coins.size(), "ок" if why == "" else why])
	for i in lv.pieces.size():
		var p := lv.pieces[i]
		var marks := ""
		for g in lv.guards:
			if g.piece == i:
				marks += " S(%.1f м/с)" % g.speed
		var crates := 0
		for c in lv.crates:
			if lv.piece_at(c.z) == i:
				crates += 1
		if crates > 0:
			marks += " " + "#".repeat(crates)
		var coins := 0
		for c in lv.coins:
			if c.z <= p.z0 + p.gap and c.z >= p.z1():
				coins += 1
		marks += " " + "o".repeat(coins)
		print("%2d %-6s %s длина %2d ширина %d x %+.1f высота %+.2f → %+.2f%s" % [i, SpitLevel.Kind.keys()[p.kind],
				"яма %.1f," % p.gap if p.gap > 0.0 else "         ", p.length, p.width, p.x, p.h0, p.h1, marks])
	for mode: AutoTest.BotMode in [AutoTest.BotMode.WIN, AutoTest.BotMode.LOSE]:
		var r := SpitSim.simulate(lv, dt, mode, 300.0, setup)
		print("%s: %s за %.1f с, жизней %d, падений %d, дублонов %d, ящиков %d; %s" % ["WIN" if mode == AutoTest.BotMode.WIN else "LOSE",
				"маяк" if r.won else ("провал" if r.ended else "не закончил"), r.time, r.lives, r.falls, r.coins_got, r.crates_got,
				r.describe_near()])
	quit(0)
	return true
