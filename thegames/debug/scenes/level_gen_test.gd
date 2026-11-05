extends Control
## Тестовая сцена генератора уровня платформера: сто уровней из сидов подряд миникартами с
## отметкой проходимости, A переключает на крупный вид одного уровня, ← → листают сид.
## Под ботом: сто сидов проходимы, генерация детерминирована, в уровне есть ямы, враги,
## монеты, чекпоинт в средней трети и флаг в конце.

const SECTION: StringName = &"Уровни"
const COUNT := 100
const COLS := 4

var tuning: PlatformerGenTuning
var seed_base := 1
var zoom := false
var zoom_seed := 1
var levels: Array[PlatformerLevel] = []
var passable: Array[bool] = []
var _checked := false


func _ready() -> void:
	tuning = PlatformerGenTuning.load_default()
	if AutoTest.enabled and AutoTest.parse_args(OS.get_cmdline_user_args()).has("zoom"):
		zoom = true
	Debug.add_number(SECTION, "Сид", func() -> int: return zoom_seed, _set_zoom_seed, 1, 999, 1, true)
	Debug.add_toggle(SECTION, "Крупно один уровень", func() -> bool: return zoom, _set_zoom)
	_rebuild()


func _exit_tree() -> void:
	Debug.clear_section(SECTION)


func _set_zoom_seed(v: float) -> void:
	zoom_seed = int(v)
	queue_redraw()


func _set_zoom(v: bool) -> void:
	zoom = v
	queue_redraw()


func _rebuild() -> void:
	levels.clear()
	passable.clear()
	for i in COUNT:
		var lv := PlatformerLevelGen.generate(seed_base + i, tuning)
		levels.append(lv)
		passable.append(PlatformerLevelGen.passable(lv, tuning))
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(GameInput.RIGHT):
		if zoom:
			zoom_seed += 1
		else:
			seed_base += COUNT
			_rebuild()
	elif event.is_action_pressed(GameInput.LEFT):
		if zoom:
			zoom_seed = maxi(zoom_seed - 1, 1)
		else:
			seed_base = maxi(seed_base - COUNT, 1)
			_rebuild()
	elif GameInput.is_a(event):
		zoom = not zoom
	else:
		return
	queue_redraw()


func _process(_delta: float) -> void:
	if AutoTest.enabled and not _checked:
		_checked = true
		_run_checks()


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Style.BG)
	var font := ThemeDB.fallback_font
	var ink := Style.STUDIO_INK
	if zoom:
		var lv := PlatformerLevelGen.generate(zoom_seed, tuning)
		var ok := PlatformerLevelGen.passable(lv, tuning)
		draw_string(font, Vector2(48, 60), "Уровень из сида %d: %s   (← → сид, A все сто)" % [
			zoom_seed, "проходим" if ok else "НЕ ПРОХОДИМ"], HORIZONTAL_ALIGNMENT_LEFT, -1, 28, ink)
		_draw_level(lv, Rect2(48, 100, size.x - 96, 240), ok, true)
		draw_string(font, Vector2(48, 380), "ямы %d · платформы %d · враги %d · монеты %d · чекпоинт x=%d · флаг x=%d" % [
			lv.pit_count(), lv.platforms.size(), lv.enemies.size(), lv.coins.size(), lv.checkpoint.x, lv.flag.x],
			HORIZONTAL_ALIGNMENT_LEFT, -1, 24, Style.INK_2)
		return
	var bad := 0
	for p in passable:
		if not p:
			bad += 1
	draw_string(font, Vector2(48, 60), "Сто уровней из сидов %d-%d, непроходимых: %d   (← → страница сидов, A крупно)" % [
		seed_base, seed_base + COUNT - 1, bad], HORIZONTAL_ALIGNMENT_LEFT, -1, 28, ink)
	var top := 90.0
	var cell_w := (size.x - 96.0) / COLS
	var cell_h := (size.y - top - 40.0) / (COUNT / COLS)
	for i in COUNT:
		var rect := Rect2(48 + (i % COLS) * cell_w, top + (i / COLS) * cell_h, cell_w - 12.0, cell_h - 6.0)
		_draw_level(levels[i], rect, passable[i], false)


func _draw_level(lv: PlatformerLevel, rect: Rect2, ok: bool, detailed: bool) -> void:
	var sx := rect.size.x / lv.width
	var sy := rect.size.y / lv.height
	draw_rect(rect, Style.SUCCESS if ok else Style.DANGER, false, 2.0)
	for x in lv.width:
		var h := lv.ground_top(x)
		if h > 0:
			draw_rect(Rect2(rect.position.x + x * sx, rect.end.y - h * sy, maxf(sx, 1.0), h * sy), Color(Style.STUDIO_INK, 0.8))
	for p in lv.platforms:
		draw_rect(Rect2(rect.position.x + p.position.x * sx, rect.end.y - (p.position.y + 1) * sy, p.size.x * sx, maxf(sy * 0.6, 1.0)), Style.accent(1))
	for c in lv.coins:
		draw_circle(Vector2(rect.position.x + (c.x + 0.5) * sx, rect.end.y - (c.y + 0.5) * sy), maxf(sy * 0.3, 1.5), Style.accent(2))
	for e in lv.enemies:
		draw_rect(Rect2(rect.position.x + e.x * sx, rect.end.y - (e.y + 1) * sy, maxf(sx, 2.0), sy), Style.DANGER)
	draw_rect(Rect2(rect.position.x + lv.checkpoint.x * sx, rect.end.y - (lv.checkpoint.y + 2) * sy, maxf(sx, 2.0), sy * 2.0), Style.accent(0))
	draw_rect(Rect2(rect.position.x + lv.flag.x * sx, rect.end.y - (lv.flag.y + 3) * sy, maxf(sx, 2.0), sy * 3.0), Style.accent(3))
	if detailed:
		draw_circle(Vector2(rect.position.x + (lv.spawn.x + 0.5) * sx, rect.end.y - (lv.spawn.y + 0.5) * sy), sy * 0.5, Style.INK)


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("level gen: " + what)


func _run_checks() -> void:
	AutoTest.require("level gen checks")
	for i in COUNT:
		_expect(passable[i], "сид %d не проходим" % (seed_base + i))
	var a := PlatformerLevelGen.generate(42, tuning)
	var b := PlatformerLevelGen.generate(42, tuning)
	_expect(a.signature() == b.signature(), "сид 42 не детерминирован")
	_expect(PlatformerLevelGen.generate(43, tuning).signature() != a.signature(), "сиды 42 и 43 дали один уровень")
	var pits := 0
	var enemies := 0
	var coins := 0
	var platforms := 0
	for lv in levels:
		pits += lv.pit_count()
		enemies += lv.enemies.size()
		coins += lv.coins.size()
		platforms += lv.platforms.size()
		_expect(lv.checkpoint.x > lv.width / 3 and lv.checkpoint.x < lv.width * 2 / 3, "чекпоинт не в средней трети: x=%d" % lv.checkpoint.x)
		_expect(not lv.is_pit(lv.checkpoint.x) and not lv.is_pit(lv.flag.x), "чекпоинт или флаг над ямой")
		_expect(lv.flag.x >= lv.width - 8, "флаг не в конце: x=%d" % lv.flag.x)
		for x in lv.width:
			_expect(lv.ground_top(x) <= tuning.max_height, "земля выше максимума в колонке %d" % x)
	_expect(pits >= COUNT * 3, "в среднем меньше 3 ям на уровень: %d" % pits)
	_expect(enemies >= COUNT * 2, "в среднем меньше 2 врагов: %d" % enemies)
	_expect(coins >= COUNT * 10, "в среднем меньше 10 монет: %d" % coins)
	AutoTest.fulfill("level gen checks")
	AutoTest.note("level gen checks done: pits=%d enemies=%d coins=%d platforms=%d per 100" % [pits, enemies, coins, platforms])
