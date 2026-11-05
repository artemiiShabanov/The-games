extends Control
## Тестовая сцена подбора спринтов: планы для N = 4..8 выбранной пары при фиксированном сиде.
## Влево-вправо технология, вверх-вниз жанр, A новый сид; то же в дебаг-меню, раздел «Спринты».
## Под ботом проверяет правила подбора на N = 4, 5, 8 для платформера × 8-bit и роняет
## автотест при нарушении.

const SECTION: StringName = &"Спринты"
const INK := Style.STUDIO_INK

var genre := Game.Genre.PLATFORMER
var tech := Game.Tech.BIT8
var seed_value := 1
var pool: Array[MinigameDef] = []
var tuning: SprintTuning
var _checked := false
var _label: Label


func _ready() -> void:
	pool = MinigamePool.load_all()
	tuning = MinigamePool.load_tuning()
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	_label = Label.new()
	_label.set_anchors_preset(Control.PRESET_FULL_RECT)
	_label.offset_left = 48
	_label.offset_top = 40
	_label.offset_right = -48
	_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_label.add_theme_font_size_override("font_size", 26)
	_label.add_theme_color_override("font_color", INK)
	add_child(_label)
	Debug.add_choice(SECTION, "Жанр", Game.GENRE_NAMES,
			func() -> String: return Game.genre_name(genre),
			func(v: String) -> void:
				genre = Game.GENRE_NAMES.find(v) as Game.Genre
				_refresh())
	Debug.add_choice(SECTION, "Технология", Game.TECH_NAMES,
			func() -> String: return Game.tech_name(tech),
			func(v: String) -> void:
				tech = Game.TECH_NAMES.find(v) as Game.Tech
				_refresh())
	Debug.add_number(SECTION, "Сид", func() -> int: return seed_value,
			func(v: float) -> void:
				seed_value = int(v)
				_refresh(), 1, 999, 1)
	_refresh()


func _exit_tree() -> void:
	Debug.clear_section(SECTION)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(GameInput.RIGHT):
		tech = wrapi(tech + 1, 0, Game.Tech.size()) as Game.Tech
	elif event.is_action_pressed(GameInput.LEFT):
		tech = wrapi(tech - 1, 0, Game.Tech.size()) as Game.Tech
	elif event.is_action_pressed(GameInput.DOWN):
		genre = wrapi(genre + 1, 0, Game.Genre.size()) as Game.Genre
	elif event.is_action_pressed(GameInput.UP):
		genre = wrapi(genre - 1, 0, Game.Genre.size()) as Game.Genre
	elif event.is_action_pressed(GameInput.A):
		seed_value += 1
	else:
		return
	_refresh()


func _process(_delta: float) -> void:
	if AutoTest.enabled and not _checked:
		_checked = true
		_run_checks()


func _refresh() -> void:
	var lines: PackedStringArray = []
	lines.append("Подбор спринтов: %s × %s, сид %d   (← → технология, ↑ ↓ жанр, A сид)" % [
		Game.genre_name(genre), Game.tech_name(tech), seed_value])
	var weights: PackedStringArray = []
	for a in tuning.aspects_by_weight(genre, tech):
		weights.append("%s %d" % [Game.aspect_name(a), tuning.weight(genre, tech, a)])
	lines.append("веса: " + " · ".join(weights))
	lines.append("")
	for n in range(4, 9):
		var rng := RandomNumberGenerator.new()
		rng.seed = seed_value * 100 + n
		var p := SprintPlanner.plan(n, genre, tech, pool, tuning, rng)
		lines.append("N=%d  %s" % [n, p])
	lines.append("")
	lines.append("пул: %d мини-игр" % pool.size())
	_label.text = "\n".join(lines)


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("sprint plan: " + what)


func _plan(n: int, seed_: int, p: Array[MinigameDef], avoid: StringName = &"") -> SprintPlan:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_
	return SprintPlanner.plan(n, Game.Genre.PLATFORMER, Game.Tech.BIT8, p, tuning, rng, avoid)


func _same_set(a: Array[Game.Aspect], b: Array) -> bool:
	if a.size() != b.size():
		return false
	for x in b:
		if not a.has(x):
			return false
	return true


func _run_checks() -> void:
	_expect(pool.size() == 20, "в пуле %d мини-игр, не 20" % pool.size())
	_expect(tuning != null and tuning.genre_weights.size() == 5 and tuning.tech_weights.size() == 5,
			"тюнинг весов неполный")
	var order := tuning.aspects_by_weight(Game.Genre.PLATFORMER, Game.Tech.BIT8)
	_expect(order == [Game.Aspect.GRAPHICS, Game.Aspect.OPTIMIZATION, Game.Aspect.SOUND,
			Game.Aspect.CONTROLS, Game.Aspect.BALANCE], "порядок аспектов платформер × 8-bit: %s" % [order])

	for n in [4, 5, 8]:
		var p := _plan(n, 42, pool)
		_expect(p.size() == n, "N=%d дал %d спринтов" % [n, p.size()])
		_expect(p.ids().has(&"pairs") and p.ids().has(&"runner"), "N=%d без технологической или жанровой" % n)
		var aspects := SprintPlanner.aspects_in(p)
		match n:
			4:
				_expect(_same_set(aspects, [Game.Aspect.GRAPHICS, Game.Aspect.OPTIMIZATION]),
						"N=4 аспекты %s" % [aspects])
			5:
				_expect(_same_set(aspects, [Game.Aspect.GRAPHICS, Game.Aspect.OPTIMIZATION, Game.Aspect.SOUND]),
						"N=5 аспекты %s" % [aspects])
			8:
				_expect(aspects.size() == 5, "N=8 аспектов %d, не 5" % aspects.size())
				var graphics: Array[StringName] = []
				for d in p.defs:
					if d.kind == MinigameDef.Kind.ASPECT and d.aspect == Game.Aspect.GRAPHICS:
						graphics.append(d.id)
				_expect(graphics.size() == 2 and graphics[0] != graphics[1],
						"N=8 лишний спринт не у графики второй мини-игрой: %s" % [graphics])
		var again := _plan(n, 42, pool)
		_expect(again.ids() == p.ids(), "N=%d не детерминирован" % n)

	for i in range(50):
		var p := _plan(5, i, pool, &"pairs")
		_expect(p.defs[0].id != &"pairs", "avoid_first нарушен на сиде %d" % i)

	var m0: Array[MinigameDef] = []
	for d in pool:
		if d.kind != MinigameDef.Kind.TECH:
			m0.append(d)
	var pm0 := _plan(5, 7, m0)
	_expect(pm0.size() == 5 and not pm0.ids().has(&"pairs"), "M0 без технологической: %s" % pm0)
	_expect(_same_set(SprintPlanner.aspects_in(pm0), [Game.Aspect.GRAPHICS, Game.Aspect.OPTIMIZATION,
			Game.Aspect.SOUND, Game.Aspect.CONTROLS]), "M0 аспекты %s" % [SprintPlanner.aspects_in(pm0)])

	var tiny: Array[MinigameDef] = []
	for d in pool:
		if d.id == &"runner" or d.id == &"flood_fill":
			tiny.append(d)
	var ptiny := _plan(6, 1, tiny)
	_expect(ptiny.size() == 2, "пул из двух мини-игр должен дать 2 спринта, дал %d" % ptiny.size())

	AutoTest.note("sprint plan checks done")
