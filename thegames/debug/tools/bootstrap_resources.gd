extends SceneTree
## Разовое создание ресурсов из каталога мини-игр, таблицы весов и каталога багов M0.
## Существующие файлы не трогает: тюнинг потом правится в редакторе, не здесь.
##   Godot --headless --path thegames -s debug/tools/bootstrap_resources.gd

const K := MinigameDef.Kind
const A := Game.Aspect
const G := Game.Genre
const T := Game.Tech
const L := GameInput.LEFT
const R := GameInput.RIGHT
const U := GameInput.UP
const D := GameInput.DOWN
const BA := GameInput.A
const BB := GameInput.B

# id, kind, владелец, глагол, подпись, секунды, действия
const MINIGAMES := [
	["fit_frame", K.ASPECT, A.OPTIMIZATION, "Подгони", "Вверх-вниз число сторон, влево или вправо отправить в трафарет", 20.0, [U, D, L, R]],
	["patch_line", K.ASPECT, A.OPTIMIZATION, "Поправь", "Сдвинутый блок под курсором: стрелка ставит его на место", 25.0, [U, D]],
	["in_time", K.ASPECT, A.SOUND, "В такт", "Ноты бегут к метке: нужная стрелка в такт, длинные держи", 20.0, [L, D, R]],
	["tune", K.ASPECT, A.SOUND, "Настрой волну", "Влево-вправо частота, вверх-вниз амплитуда, A фиксирует", 20.0, [L, R, U, D, BA]],
	["repeat", K.ASPECT, A.CONTROLS, "Повтори", "Запомни последовательность и повтори её", 20.0, [L, R, U, D, BA, BB]],
	["inverted", K.ASPECT, A.CONTROLS, "Выведи", "Выведи точку к выходу: движется то точка, то лабиринт", 20.0, [L, R, U, D]],
	["flood_fill", K.ASPECT, A.GRAPHICS, "Залей", "Влево-вправо цвет, A заливает из угла: сделай сетку одноцветной", 30.0, [L, R, BA]],
	["beam", K.ASPECT, A.GRAPHICS, "Наведи", "Влево-вправо наклон, A передаёт луч следующему зеркалу", 20.0, [L, R, BA]],
	["decide_cards", K.ASPECT, A.BALANCE, "Реши", "Карточка подходит под правило: A, не подходит: B", 20.0, [BA, BB]],
	["fishing", K.ASPECT, A.BALANCE, "Удержи", "Держи клавишу: столбик вверх, отпусти: вниз, держи шарик внутри", 20.0, [BA]],
	["mash", K.TECH, T.VECTOR, "Разгони", "Влево-вправо как можно быстрее", 10.0, [L, R]],
	["pairs", K.TECH, T.BIT8, "Запомни", "Открывай карточки парами", 25.0, [L, R, U, D, BA]],
	["stack", K.TECH, T.BIT16, "Поставь", "A роняет блок на башню, свес отрезается", 20.0, [BA]],
	["doorway", K.TECH, T.LOWPOLY, "Проверни", "Влево-вправо вращай фигуру под вырез в стене", 20.0, [L, R]],
	["inflate", K.TECH, T.THREED, "Раздуй", "Держи A: шар растёт, отпусти у метки", 20.0, [BA]],
	["runner", K.GENRE, G.PLATFORMER, "Прыгай", "A прыжок через ямы и столбики, держи дольше: выше", 20.0, [BA]],
	["lights_out", K.GENRE, G.RACING, "Старт", "Огни погасли: жми A, раньше фальстарт", 20.0, [BA]],
	["mole", K.GENRE, G.SHOOTER, "Бей", "Кружок выскочил: стрелка в его сторону", 20.0, [L, R, U, D]],
	["putt", K.GENRE, G.SPORT, "Натяни", "Держи A: сила растёт, отпусти, шар летит в лунку", 20.0, [BA]],
	["rings", K.GENRE, G.FIGHTING, "Выстрой", "A останавливает кольцо: выстрой вырезы", 20.0, [BA]],
]

# оптимизация, звук, управление, графика, баланс
const GENRE_WEIGHTS := {
	G.PLATFORMER: [2, 1, 1, 2, 1],
	G.RACING: [2, 1, 2, 1, 1],
	G.SHOOTER: [1, 1, 2, 1, 2],
	G.SPORT: [2, 1, 1, 1, 2],
	G.FIGHTING: [1, 1, 2, 1, 2],
}
const BUGS_DIR := "res://resources/bugs/"
# id, вид, владелец, штамп, проявление, твит, кадр клипа, зрелищный, параметры
const BUGS := [
	["frame_drops", BugDef.Kind.ASPECT, A.OPTIMIZATION, "15 FPS", "Кадры проседают: фризы по 200-400 мс в движении",
		"Играл бы, если бы не слайд-шоу. 15 FPS, серьёзно?", "Герой замирает в прыжке, камера дёргается", false,
		{&"freeze_ms_min": 200.0, &"freeze_ms_max": 400.0, &"period_s": 2.5}],
	["audio_stutter", BugDef.Kind.ASPECT, A.SOUND, "ЗАИКАЕТСЯ", "Музыка заикается, звуки с задержкой",
		"Саундтрек как с зажёванной кассеты", "Прыжок есть, звук прыжка через секунду", false,
		{&"stutter_period_s": 3.0, &"delay_ms": 350.0}],
	["sticky_input", BugDef.Kind.ASPECT, A.CONTROLS, "ЗАЛИПЛО", "Кнопка залипает, ввод с опозданием",
		"Нажал прыжок один раз, герой прыгнул трижды", "Герой скачет сам после одного нажатия", false,
		{&"stick_chance": 0.25, &"extra_presses": 2.0, &"delay_ms": 120.0}],
	["pink_placeholders", BugDef.Kind.ASPECT, A.GRAPHICS, "ЗАГЛУШКИ", "Розовые квадраты вместо части спрайтов",
		"Враги розовые квадраты. Это стиль или дедлайн?", "Розовый квадрат бежит на героя", false,
		{&"share": 0.35}],
	["unreachable_coins", BugDef.Kind.ASPECT, A.BALANCE, "НЕ ДОСТАТЬ", "Платформы с монетами висят выше прыжка",
		"Монеты видно, монеты не взять. Кто это тестировал?", "Герой прыгает под платформой, монеты над головой", false,
		{&"lift_rows": 5.0}],
	["wild_physics", BugDef.Kind.GENRE, G.PLATFORMER, "ПРЫЖОК ×3", "Прыжок втрое выше, враги вдвое быстрее",
		"Герой улетает за верх экрана, скелеты носятся как спринтеры", "Герой уходит за верх экрана, внизу мелькает скелет", true,
		{&"jump_mult": 3.0, &"enemy_speed_mult": 2.0}],
]

const TECH_WEIGHTS := {
	T.VECTOR: [1, 1, 2, 1, 2],
	T.BIT8: [1, 2, 1, 2, 1],
	T.BIT16: [1, 2, 1, 2, 1],
	T.LOWPOLY: [2, 1, 1, 2, 1],
	T.THREED: [2, 1, 1, 2, 1],
}


func _init() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(MinigamePool.DIR))
	var made := 0
	for row: Array in MINIGAMES:
		var path: String = MinigamePool.DIR + str(row[0]) + ".tres"
		if FileAccess.file_exists(path):
			continue
		var def := MinigameDef.new()
		def.id = StringName(row[0])
		def.kind = row[1]
		match def.kind:
			K.ASPECT:
				def.aspect = row[2]
			K.TECH:
				def.tech = row[2]
			K.GENRE:
				def.genre = row[2]
		def.verb = row[3]
		def.hint = row[4]
		def.time_seconds = row[5]
		var inputs: Array[StringName] = []
		for i in row[6]:
			inputs.append(i)
		def.inputs = inputs
		_save(def, path)
		made += 1

	if not FileAccess.file_exists(MinigamePool.TUNING_PATH):
		var tuning := SprintTuning.new()
		for g in Game.Genre.values():
			var w: Array = GENRE_WEIGHTS[g]
			tuning.genre_weights.append(AspectWeights.make(w[0], w[1], w[2], w[3], w[4]))
		for t in Game.Tech.values():
			var w: Array = TECH_WEIGHTS[t]
			tuning.tech_weights.append(AspectWeights.make(w[0], w[1], w[2], w[3], w[4]))
		_save(tuning, MinigamePool.TUNING_PATH)
		made += 1
	made += _bootstrap_bugs()
	print("bootstrap: создано %d ресурсов" % made)
	quit()


func _bootstrap_bugs() -> int:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(BUGS_DIR))
	var made := 0
	var defs: Array[BugDef] = []
	for row: Array in BUGS:
		var path: String = BUGS_DIR + str(row[0]) + ".tres"
		if FileAccess.file_exists(path):
			defs.append(load(path) as BugDef)
			continue
		var bug := BugDef.new()
		bug.id = StringName(row[0])
		bug.kind = row[1]
		match bug.kind:
			BugDef.Kind.ASPECT:
				bug.aspect = row[2]
			BugDef.Kind.GENRE:
				bug.genre = row[2]
			BugDef.Kind.TECH:
				bug.tech = row[2]
		bug.stamp = row[3]
		bug.manifestation = row[4]
		bug.tweet = row[5]
		bug.clip = row[6]
		bug.spectacular = row[7]
		var params: Dictionary[StringName, float] = {}
		for key in row[8]:
			params[key] = row[8][key]
		bug.params = params
		_save(bug, path)
		defs.append(bug)
		made += 1
	if not FileAccess.file_exists(BugCatalog.PATH):
		var catalog := BugCatalog.new()
		catalog.bugs = defs
		_save(catalog, BugCatalog.PATH)
		made += 1
	return made


func _save(res: Resource, path: String) -> void:
	var err := ResourceSaver.save(res, path)
	if err != OK:
		push_error("bootstrap: не сохранён %s: %s" % [path, error_string(err)])
	else:
		# Чтобы каталоги ссылались на файл, а не вкладывали копию.
		res.take_over_path(path)
		print("bootstrap: " + path)
