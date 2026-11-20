class_name MinigameStats
extends RefCounted
## Журнал сыгранных мини-игр для баланса (2026-11-20), спека `docs/specs/minigames.md`. Каждая
## доигранная мини-игра дописывается строкой JSON в `user://minigame_stats.jsonl` (под автотестом
## свой файл): какая, на какой сложности, сколько времени и ошибок, счёт и вышел ли баг. Никуда
## не отправляется; `export_csv` выгружает всё таблицей в «Загрузки» (строка в настройках и
## раздел «Мини-игры» дебаг-меню). Пишет `SprintRunner`, контекст (релиз, жанр, технология) даёт
## его хозяин.

const PATH := "user://minigame_stats.jsonl"
const TEST_PATH := "user://minigame_stats_autotest.jsonl"
## Столбцы выгрузки по порядку. Поля строки журнала с теми же именами.
const COLUMNS: Array[String] = [
	"time", "session", "context", "release", "sprint", "sprints", "genre", "tech", "setting",
	"minigame", "kind", "owner", "t", "seed", "time_limit", "time_spent", "time_left", "timed_out",
	"score", "mistakes", "grace", "bug_chance", "bug", "pauses", "input", "bot", "details"]

## Выключатель записи (дебаг и тесты).
static var enabled := true
## Метка запуска игры: строки одного запуска в выгрузке держатся вместе.
static var _session := ""


static func path() -> String:
	return TEST_PATH if AutoTest.enabled else PATH


## Строка об одной доигранной мини-игре. `context` от хозяина раннера: `context` (release,
## bugfix, test), `release`, `genre`, `tech`, `setting`.
static func record(minigame: Minigame, context: Dictionary, sprint: int, sprints: int,
		seed_: int, bug_chance: float, bug: bool) -> void:
	if not enabled or minigame == null or minigame.def == null:
		return
	var def := minigame.def
	var row := {
		"time": Time.get_datetime_string_from_system(false, true),
		"session": _session_id(),
		"context": context.get("context", "test"),
		"release": context.get("release", 0),
		"sprint": sprint,
		"sprints": sprints,
		"genre": _key(Game.Genre.keys(), context.get("genre", -1)),
		"tech": _key(Game.Tech.keys(), context.get("tech", -1)),
		"setting": _key(Game.Setting.keys(), context.get("setting", -1)),
		"minigame": String(def.id),
		"kind": _key(MinigameDef.Kind.keys(), def.kind),
		"owner": _owner(def),
		"t": snappedf(minigame.t, 0.001),
		"seed": seed_,
		"time_limit": snappedf(minigame.time_limit, 0.01),
		"time_spent": snappedf(minigame.elapsed, 0.01),
		"time_left": snappedf(minigame.time_left, 0.01),
		"timed_out": minigame.time_left <= 0.0,
		"score": snappedf(minigame.score, 0.001),
		# Мини-игра без счёта ошибок (нет `mistake_loss`): пусто.
		"mistakes": minigame.mistakes if minigame.mistakes >= 0 else null,
		"grace": minigame.mistake_grace if minigame.mistake_grace >= 0 else null,
		"bug_chance": snappedf(bug_chance, 0.001),
		"bug": bug,
		"pauses": minigame.pauses,
		"input": "mouse" if GameInput.mouse else "keys",
		"bot": AutoTest.bot_active(),
		"details": minigame.summary(),
	}
	var file := path()
	var f := FileAccess.open(file, FileAccess.READ_WRITE) if FileAccess.file_exists(file) \
			else FileAccess.open(file, FileAccess.WRITE)
	if f == null:
		push_warning("MinigameStats: не открыть %s" % file)
		return
	f.seek_end()
	f.store_line(JSON.stringify(row))
	f.close()


## Все строки журнала по порядку записи.
static func rows() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	var f := FileAccess.open(path(), FileAccess.READ)
	if f == null:
		return out
	while not f.eof_reached():
		var line := f.get_line()
		if line.strip_edges() == "":
			continue
		var data: Variant = JSON.parse_string(line)
		if data is Dictionary:
			out.append(data)
	return out


static func count() -> int:
	return rows().size()


static func clear() -> void:
	if FileAccess.file_exists(path()):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(path()))


## Выгрузка журнала таблицей CSV в `dir` (по умолчанию «Загрузки», под автотестом `user://`).
## Возвращает полный путь файла или пустую строку, если журнал пуст или файл не записать.
static func export_csv(dir := "") -> String:
	var all := rows()
	if all.is_empty():
		return ""
	if dir == "":
		dir = default_export_dir()
	var stamp := Time.get_datetime_string_from_system(false, true).replace(":", "").replace(" ", "_")
	var file := dir.path_join("studio_running_minigames_%s.csv" % stamp)
	var f := FileAccess.open(file, FileAccess.WRITE)
	if f == null:
		push_warning("MinigameStats: не записать %s" % file)
		return ""
	f.store_csv_line(PackedStringArray(COLUMNS))
	for row in all:
		var cells := PackedStringArray()
		for c in COLUMNS:
			cells.append(_cell(row.get(c, "")))
		f.store_csv_line(cells)
	f.close()
	return ProjectSettings.globalize_path(file)


static func default_export_dir() -> String:
	if AutoTest.enabled:
		return "user://"
	for d: OS.SystemDir in [OS.SYSTEM_DIR_DOWNLOADS, OS.SYSTEM_DIR_DESKTOP, OS.SYSTEM_DIR_DOCUMENTS]:
		var p := OS.get_system_dir(d)
		if p != "" and DirAccess.dir_exists_absolute(p):
			return p
	return OS.get_user_data_dir()


static func _cell(v: Variant) -> String:
	if v == null:
		return ""
	if v is bool:
		return "1" if v else "0"
	if v is float and is_equal_approx(v, roundf(v)):
		return str(int(v))
	return str(v)


static func _key(keys: Array, i: Variant) -> String:
	var n := int(i)
	return String(keys[n]).to_lower() if n >= 0 and n < keys.size() else ""


static func _owner(def: MinigameDef) -> String:
	match def.kind:
		MinigameDef.Kind.ASPECT:
			return _key(Game.Aspect.keys(), def.aspect)
		MinigameDef.Kind.GENRE:
			return _key(Game.Genre.keys(), def.genre)
		MinigameDef.Kind.TECH:
			return _key(Game.Tech.keys(), def.tech)
	return ""


static func _session_id() -> String:
	if _session == "":
		_session = "%x" % (int(Time.get_unix_time_from_system()) ^ (randi() << 8))
	return _session
