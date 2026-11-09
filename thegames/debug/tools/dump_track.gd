extends SceneTree
## Дамп трассы гонок по сиду в консоль: вода `~`, отмель `:`, берег ` `, средняя линия `·`,
## финиш `F`, бочки `b`, рифы `r`, буи `o`, плюс проверка и число попыток генератора.
## Без сида сводка по сотне сидов: сколько трасс взяли запасной эллипс, длины петель, время.
##   Godot --headless --path thegames -s debug/tools/dump_track.gd -- <seed>
##   Godot --headless --path thegames -s debug/tools/dump_track.gd

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	var args := OS.get_cmdline_user_args()
	var t := RacingGenTuning.load_default()
	if args.is_empty():
		_summary(t)
		return true
	var seed_ := int(args[0])
	var tr := RacingTrackGen.generate(seed_, t)
	var why := RacingTrackGen.validate(tr, t)
	print("сид %d: %dx%d тайлов, петля %d точек (%.0f px), попыток %d%s, проверка %s" % [
			seed_, tr.width, tr.height, tr.count(), tr.count() * t.sample_step, tr.attempts,
			" (запасной эллипс)" if tr.fallback else "", "ок" if why == "" else why])
	var grid: Array[PackedStringArray] = []
	for row in tr.height:
		var line := PackedStringArray()
		for col in tr.width:
			line.append(["  ", "::", "~~"][tr.tile(col, row)])
		grid.append(line)
	for p in tr.points:
		_mark(tr, grid, p, "··")
	for b in tr.buoys:
		_mark(tr, grid, b, "oo")
	for o in tr.obstacles:
		_mark(tr, grid, o.pos, "bb" if o.kind == RacingTrack.Kind.BARREL else "rr")
	_mark(tr, grid, tr.points[0], "FF")
	for line in grid:
		print("".join(line))
	return true


func _mark(tr: RacingTrack, grid: Array[PackedStringArray], p: Vector2, ch: String) -> void:
	var col := int(floor(p.x / RacingTrack.TILE))
	var row := int(floor(p.y / RacingTrack.TILE))
	if row >= 0 and row < tr.height and col >= 0 and col < tr.width:
		grid[row][col] = ch


func _summary(t: RacingGenTuning) -> void:
	var t0 := Time.get_ticks_msec()
	var fallbacks := 0
	var attempts := 0
	var bad := 0
	var lo := INF
	var hi := 0.0
	for s in range(1, 101):
		var tr := RacingTrackGen.generate(s, t)
		if RacingTrackGen.validate(tr, t) != "":
			bad += 1
		fallbacks += 1 if tr.fallback else 0
		attempts += tr.attempts
		lo = minf(lo, tr.count() * t.sample_step)
		hi = maxf(hi, tr.count() * t.sample_step)
	print("100 сидов: не прошли %d, запасной эллипс %d, попыток в среднем %.1f, петля %.0f-%.0f px, %d мс" % [
			bad, fallbacks, attempts / 100.0, lo, hi, Time.get_ticks_msec() - t0])
	var reasons := {}
	for s in range(1, 101):
		var rng := RandomNumberGenerator.new()
		rng.seed = hash(str(s, ":track:", 0))
		var why := RacingTrackGen.validate(RacingTrackGen._build(rng, t, false), t)
		var key := why.get_slice(" ", 0) if why != "" else "ок"
		reasons[key] = int(reasons.get(key, 0)) + 1
	print("первая попытка: ", reasons)
