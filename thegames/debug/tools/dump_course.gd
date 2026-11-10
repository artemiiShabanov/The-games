extends SceneTree
## Дамп поля гольфа (спорт × 8-bit, #52) по сиду в консоль: по лунке длина, пар, ветер, ти,
## грин, люк, пролив, пропы и профиль поверхности столбцами по 16 px (выше строка, выше
## поверхность): `.` песок, `=` палуба (ти и грин), `#` корма, `~` море, `U` люк, `T` ти;
## плюс проверка генератора и число попыток.
##   Godot --headless --path thegames -s debug/tools/dump_course.gd -- <seed>

const ROWS := 12

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	var args := OS.get_cmdline_user_args()
	var t := GolfGenTuning.load_default()
	var seed_ := int(args[0]) if not args.is_empty() else 1
	var c := GolfCourseGen.generate(seed_, t)
	var why := GolfCourseGen.validate(c, t)
	print("сид %d: лунок %d, пар %d, попыток %d%s, проверка %s" % [seed_, c.holes.size(), c.total_par(),
			c.attempts, " (запасное)" if c.fallback else "", "ок" if why == "" else why])
	for n in c.holes.size():
		var h := c.holes[n]
		var water := "нет" if not h.has_water() else "%d..%d" % [int(h.water_from), int(h.water_to)]
		print("лунка %d: длина %d, пар %d, ветер %+d, ти %d, грин %d..%d, люк %d (от ти %d), пролив %s, пропов %d" % [
				n + 1, h.length, h.par, h.wind, int(h.tee_x), int(h.green_from), int(h.green_to), int(h.cup_x),
				int(h.cup_x - h.tee_x), water, h.props.size()])
		var top := t.ground_top - t.stern_height - 8.0
		var bottom := t.ground_bottom + 8.0
		var lines: PackedStringArray = []
		lines.resize(ROWS)
		for x in range(0, h.length, 16):
			var mid := x + 8.0
			var kind := h.kind_at(mid)
			var y := h.height_at(mid)
			var row := clampi(int((y - top) / (bottom - top) * ROWS), 0, ROWS - 1)
			var mark := "."
			if kind == GolfCourse.Kind.WATER:
				mark = "~"
				row = ROWS - 1
			elif kind == GolfCourse.Kind.HULL:
				mark = "#"
			elif kind == GolfCourse.Kind.DECK:
				mark = "="
			if absf(mid - h.cup_x) <= 8.0:
				mark = "U"
			elif absf(mid - h.tee_x) <= 8.0:
				mark = "T"
			for r in ROWS:
				lines[r] += mark if r == row else (" " if r < row else ":")
		for l in lines:
			print(l)
	return true
