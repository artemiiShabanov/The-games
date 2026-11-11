extends SceneTree
## Дамп матча понга (спорт × вектор, #93) по сиду в консоль: соперник (скорость ракетки, ошибка,
## запоздание), подачи, проверка генератора и прогон без окна ботом WIN и ботом LOSE
## (`PongSim.simulate`). С двумя числами сиды подряд по строке на сид и сводка. Третьим
## аргументом баги через запятую: `space`, `bouncy`, `wall`, `frail`.
##   Godot --headless --path thegames -s debug/tools/dump_pong.gd -- <seed> [count] [bug,bug]

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var bugs: PackedStringArray = args[2].split(",", false) if args.size() > 2 else PackedStringArray()
	var t := SportVectorGenTuning.load_default()
	var dt := SportVectorTuning.load_default()
	var setup := func(s: PongSim) -> void:
		if bugs.has("space"):
			s.stick_every = 4
		if bugs.has("bouncy"):
			s.bounce_gain = 0.15
			s.kick = deg_to_rad(14.0)
		s.ai_wall = bugs.has("wall")
		s.ai_frail = bugs.has("frail")
	if count > 1:
		var wins := 0
		var losses := 0
		var seconds: Array[float] = []
		var conceded := 0
		for sd in range(seed_, seed_ + count):
			var game := PongMatchGen.generate(sd, t)
			var win := PongSim.simulate(game, dt, AutoTest.BotMode.WIN, 400.0, setup)
			var lose := PongSim.simulate(game, dt, AutoTest.BotMode.LOSE, 400.0, setup)
			wins += 1 if win.won else 0
			losses += 1 if lose.ended and not lose.won else 0
			conceded += win.score_ai
			if win.won:
				seconds.append(win.time)
			print("сид %d: WIN %s %d:%d за %.1f с, ударов %d | LOSE %s %d:%d за %.1f с" % [sd,
					"ок" if win.won else "ПРОВАЛ", win.score_player, win.score_ai, win.time, win.hits,
					"ок" if lose.ended and not lose.won else "ПРОВАЛ", lose.score_player, lose.score_ai, lose.time])
		seconds.sort()
		var n := seconds.size()
		print("WIN побед %d из %d, LOSE поражений %d из %d; время победы: медиана %.1f с, от %.1f до %.1f; бот WIN пропускает в среднем %.2f" % [
				wins, count, losses, count, seconds[n / 2] if n > 0 else 0.0, seconds[0] if n > 0 else 0.0,
				seconds[n - 1] if n > 0 else 0.0, float(conceded) / count])
		quit(0)
		return true
	var game := PongMatchGen.generate(seed_, t)
	var why := PongMatchGen.validate(game, t)
	print("сид %d: ракетка соперника %.0f px/с, ошибка до %.0f px, следит с %.0f %% поля, проверка: %s" % [seed_, game.ai_speed,
			game.ai_error, game.ai_react * 100.0, "ок" if why == "" else why])
	var angles: PackedStringArray = []
	for a in game.serves:
		angles.append("%+.0f°" % rad_to_deg(a))
	print("подачи: %s" % ", ".join(angles))
	for mode: AutoTest.BotMode in [AutoTest.BotMode.WIN, AutoTest.BotMode.LOSE]:
		var r := PongSim.simulate(game, dt, mode, 400.0, setup)
		print("%s: %s %d:%d за %.1f с, ударов ракеток %d, отскоков от стенок %d" % ["WIN" if mode == AutoTest.BotMode.WIN else "LOSE",
				"выиграл" if r.won else ("проиграл" if r.ended else "не закончил"), r.score_player, r.score_ai, r.time, r.hits, r.wall_bounces])
	quit(0)
	return true
