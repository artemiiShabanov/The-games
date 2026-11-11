extends SceneTree
## Дамп волн шутера × вектор (#92) по сиду в консоль: расписание появлений (время, вид,
## направление в градусах, скорость), проверка генератора и прогон без окна ботом WIN и ботом
## LOSE (`TurretSim.simulate`). С двумя числами сиды подряд по строке на сид и сводка. Третьим
## аргументом баги через запятую: `through`, `ice`, `endless`, `sneeze`.
##   Godot --headless --path thegames -s debug/tools/dump_turret.gd -- <seed> [count] [bug,bug]

const KINDS: Array[String] = ["враг", "глыба", "осколок", "вьюн"]

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var bugs: PackedStringArray = args[2].split(",", false) if args.size() > 2 else PackedStringArray()
	var t := ShooterVectorGenTuning.load_default()
	var dt := ShooterVectorTuning.load_default()
	var setup := func(s: TurretSim) -> void:
		if bugs.has("through"):
			s.pass_every = 2
		if bugs.has("ice"):
			s.ice = 2.5
			s.foe_mult = 1.5
		if bugs.has("endless"):
			s.extra_per_kill = 1.0
		if bugs.has("sneeze"):
			s.near_miss = 18.0
			s.one_hit = true
	if count > 1:
		var wins := 0
		var losses := 0
		var seconds: Array[float] = []
		var lives := 0
		for sd in range(seed_, seed_ + count):
			var waves := TurretWaveGen.generate(sd, t)
			var win := TurretSim.simulate(waves, dt, AutoTest.BotMode.WIN, 300.0, setup)
			var lose := TurretSim.simulate(waves, dt, AutoTest.BotMode.LOSE, 300.0, setup)
			wins += 1 if win.won else 0
			losses += 1 if lose.ended and not lose.won else 0
			lives += win.lives
			if win.won:
				seconds.append(win.time)
			print("сид %d: WIN %s %.1f с, уничтожено %d, жизней %d, выстрелов %d | LOSE %s %.1f с" % [sd,
					"ок" if win.won else "ПРОВАЛ", win.time, win.kills, win.lives, win.shots_fired,
					"ок" if lose.ended and not lose.won else "ПРОВАЛ", lose.time])
		seconds.sort()
		var n := seconds.size()
		print("WIN побед %d из %d, LOSE поражений %d из %d; время победы: медиана %.1f с, от %.1f до %.1f; жизней у бота WIN в среднем %.2f" % [
				wins, count, losses, count, seconds[n / 2] if n > 0 else 0.0, seconds[0] if n > 0 else 0.0,
				seconds[n - 1] if n > 0 else 0.0, float(lives) / count])
		quit(0)
		return true
	var waves := TurretWaveGen.generate(seed_, t)
	var why := TurretWaveGen.validate(waves, t)
	print("сид %d, появлений %d за %.1f с, целей %d при цели %d, проверка: %s" % [seed_, waves.spawns.size(), waves.seconds,
			waves.targets(), dt.goal, "ок" if why == "" else why])
	for s in waves.spawns:
		print("%5.1f с  %-6s %4.0f°  %3.0f px/с%s" % [s.time, KINDS[s.kind], rad_to_deg(s.angle), s.speed,
				"  кружит %+.0f°/с" % rad_to_deg(s.spin) if s.spin != 0.0 else ""])
	for mode: AutoTest.BotMode in [AutoTest.BotMode.WIN, AutoTest.BotMode.LOSE]:
		var r := TurretSim.simulate(waves, dt, mode, 300.0, setup)
		print("%s: %s за %.1f с, уничтожено %d из %.0f, жизней %d, выстрелов %d" % ["WIN" if mode == AutoTest.BotMode.WIN else "LOSE",
				"отбился" if r.won else ("не отбился" if r.ended else "не закончил"), r.time, r.kills, r.goal, r.lives, r.shots_fired])
	quit(0)
	return true
