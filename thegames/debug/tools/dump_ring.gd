extends SceneTree
## Дамп трассы гонок × low poly (#113) по сиду в консоль: кольцо знаками на сетке (`S` старт,
## `=` участок без бортов, `m` грязь, `w` ветер, `^` трамплин, `·` обычная трасса), длина и
## разметка; плюс проверка генератора и заезд без окна ботом WIN и ботом LOSE
## (`RingSim.simulate`). С двумя числами сиды подряд по строке на сид и сводка.
##   Godot --headless --path thegames -s debug/tools/dump_ring.gd -- <seed> [count]

const COLS := 100
const ROWS := 34

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	var args := OS.get_cmdline_user_args()
	var seed_ := int(args[0]) if args.size() > 0 else 1
	var count := int(args[1]) if args.size() > 1 else 1
	var t := RacingLowpolyGenTuning.load_default()
	var rules := RacingLowpolyTuning.load_default()
	if count > 1:
		var done := 0
		var bad := 0
		var places := [0, 0, 0, 0]
		var sinks := 0
		var boosts := 0
		var seconds: Array[float] = []
		var lost := 0
		## На сколько секунд первый соперник обогнал бота.
		var leads: Array[float] = []
		for sd in range(seed_, seed_ + count):
			var track := RingTrackGen.generate(sd, t)
			var why := RingTrackGen.validate(track, t)
			bad += 0 if why == "" else 1
			var win := RingSim.simulate(track, rules, AutoTest.BotMode.WIN)
			var lose := RingSim.simulate(track, rules, AutoTest.BotMode.LOSE)
			done += 1 if win.finished else 0
			lost += 1 if lose.ended and not lose.finished else 0
			sinks += win.sinks
			boosts += win.boosts
			if win.finished:
				places[win.place() - 1] += 1
				seconds.append(win.time)
				var first := win.time
				for i in range(1, win.cars.size()):
					if win.cars[i].finished >= 0.0:
						first = minf(first, win.cars[i].finished)
				leads.append(win.time - first)
			if not win.finished or why != "" or win.sinks > 2 or not (lose.ended and not lose.finished):
				print("сид %d: %s WIN %s %.1f с, место %d, в воде %d, бортов %d, ускорений %d | LOSE %s %.1f с" % [sd,
						"" if why == "" else "ГЕНЕРАТОР: " + why + ";", "доехал" if win.finished else "НЕ ДОЕХАЛ", win.time, win.place(), win.sinks,
						win.bumps, win.boosts, "ок" if lose.ended and not lose.finished else "ПРОВАЛ", lose.time])
		seconds.sort()
		var n := seconds.size()
		print("сидов %d: генератор отказал на %d; WIN доехал %d, места %s, в воде в среднем %.2f, ускорений от дрифта %.1f; LOSE не доехал %d; время: медиана %.1f с, от %.1f до %.1f" % [
				count, bad, done, places, float(sinks) / count, float(boosts) / count, lost, seconds[n / 2] if n > 0 else 0.0,
				seconds[0] if n > 0 else 0.0, seconds[n - 1] if n > 0 else 0.0])
		leads.sort()
		if not leads.is_empty():
			print("первый соперник впереди бота: медиана %.1f с, от %.1f до %.1f" % [leads[leads.size() / 2], leads[0], leads[leads.size() - 1]])
		quit(0)
		return true
	var track := RingTrackGen.generate(seed_, t)
	var why := RingTrackGen.validate(track, t)
	var tightest := 0.0
	for c in track.curves:
		tightest = maxf(tightest, absf(c))
	print("сид %d: длина круга %.0f м, точек %d, самый крутой поворот радиусом %.1f м, участков без бортов %d, грязи %d, ветра %d, трамплин на %.0f м, проверка: %s" % [
			seed_, track.length, track.count(), 1.0 / maxf(tightest, 0.0001), track.open.size(), track.muds.size(), track.winds.size(),
			track.ramp_s, "ок" if why == "" else why])
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	for p in track.points:
		lo = lo.min(p)
		hi = hi.max(p)
	var rows: Array[String] = []
	for r in ROWS:
		rows.append(" ".repeat(COLS))
	var s := 0.0
	while s < track.length:
		var p := track.center(s)
		var col := int((p.x - lo.x) / maxf(hi.x - lo.x, 1.0) * (COLS - 1))
		var row := int((p.y - lo.y) / maxf(hi.y - lo.y, 1.0) * (ROWS - 1))
		var mark := "·"
		if s < 4.0:
			mark = "S"
		elif track.in_gap(s) or (track.delta(s, track.ramp_s) > 0.0 and track.delta(s, track.ramp_s) < track.ramp_run):
			mark = "^"
		elif track.is_open(s):
			mark = "="
		elif track.in_mud(s, track.half_width - 0.5) or track.in_mud(s, -track.half_width + 0.5):
			mark = "m"
		elif track.in_wind(s, track.winds[0].d) or track.in_wind(s, track.winds[1].d) or track.in_wind(s, track.winds[2].d):
			mark = "w"
		rows[row] = rows[row].substr(0, col) + mark + rows[row].substr(col + 1)
		s += 1.0
	for row in rows:
		print(row)
	for mode: AutoTest.BotMode in [AutoTest.BotMode.WIN, AutoTest.BotMode.LOSE]:
		var r := RingSim.simulate(track, rules, mode)
		print("%s: %s за %.1f с, место %d из %d, в воде %d, бортов %d, ускорений от дрифта %d" % ["WIN" if mode == AutoTest.BotMode.WIN else "LOSE",
				"доехал" if r.finished else "не доехал", r.time, r.place(), r.cars.size(), r.sinks, r.bumps, r.boosts])
	quit(0)
	return true
