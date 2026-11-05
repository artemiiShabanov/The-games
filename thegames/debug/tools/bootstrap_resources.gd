extends SceneTree
## Разовое создание ресурсов из каталога мини-игр и таблицы весов. Существующие файлы не
## трогает: тюнинг потом правится в редакторе, не здесь.
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
	["mash", K.TECH, T.ASCII, "Разгони", "Влево-вправо как можно быстрее", 10.0, [L, R]],
	["pairs", K.TECH, T.BIT8, "Запомни", "Открывай карточки парами", 25.0, [L, R, U, D, BA]],
	["stack", K.TECH, T.BIT16, "Поставь", "A роняет блок на башню, свес отрезается", 20.0, [BA]],
	["doorway", K.TECH, T.LOWPOLY, "Проверни", "Влево-вправо вращай фигуру под вырез в стене", 20.0, [L, R]],
	["inflate", K.TECH, T.THREED, "Раздуй", "Держи A: шар растёт, отпусти у метки", 20.0, [BA]],
	["runner", K.GENRE, G.PLATFORMER, "Прыгай", "A прыжок через ямы и столбики", 20.0, [BA]],
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
const TECH_WEIGHTS := {
	T.ASCII: [1, 1, 2, 1, 2],
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
	print("bootstrap: создано %d ресурсов" % made)
	quit()


func _save(res: Resource, path: String) -> void:
	var err := ResourceSaver.save(res, path)
	if err != OK:
		push_error("bootstrap: не сохранён %s: %s" % [path, error_string(err)])
	else:
		print("bootstrap: " + path)
