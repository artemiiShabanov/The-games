class_name Profile
extends Resource
## Профиль игрока, общий на все забеги и слоты (`docs/specs/run.md`, #69), файл
## `user://profile.tres`: галерея всех выпущенных игр (`GalleryEntry`), лучшая оценка и число
## по каждой концовке, сколько забегов начато и закончено, стартовая пара прошлого забега
## (розыгрыш старта, #61). Пишется на старте забега, по закрытию релиза и по концу забега,
## читается на старте. Версия формата: другая версия (или битый файл) даёт пустой профиль;
## пара из старого `profile.cfg` (#61) переносится. Под автотестом свой файл `TEST_PATH`,
## который хозяин чистит на старте (`use_test_file`), профиль игрока не трогается.

const PATH := "user://profile.tres"
const TEST_PATH := "user://profile_autotest.tres"
const OLD_CFG := "user://profile.cfg"
const VERSION := 1

static var path := PATH

@export var version := VERSION
@export var gallery: Array[GalleryEntry] = []
## Лучшая оценка по концовке (`Endings.KEYS`) и сколько раз она была.
@export var best_endings: Dictionary[StringName, int] = {}
@export var ending_counts: Dictionary[StringName, int] = {}
@export var runs_started := 0
@export var runs_finished := 0
## Стартовая пара прошлого забега, −1 если забегов не было.
@export var last_start_genre := -1
@export var last_start_tech := -1


## Автотест: свой файл, пустой на старте прогона.
static func use_test_file() -> void:
	path = TEST_PATH
	if FileAccess.file_exists(TEST_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(TEST_PATH))


static func load_saved() -> Profile:
	var p: Profile = null
	if ResourceLoader.exists(path):
		p = ResourceLoader.load(path, "", ResourceLoader.CACHE_MODE_IGNORE) as Profile
	if p == null or p.version != VERSION:
		p = Profile.new()
		_import_old(p)
	return p


## Пара из профиля #61 (ConfigFile), если нового файла ещё нет.
static func _import_old(p: Profile) -> void:
	var cfg := ConfigFile.new()
	if path == PATH and cfg.load(OLD_CFG) == OK:
		p.last_start_genre = int(cfg.get_value("run", "last_start_genre", -1))
		p.last_start_tech = int(cfg.get_value("run", "last_start_tech", -1))


func save() -> void:
	version = VERSION
	var err := ResourceSaver.save(self, path)
	if err != OK:
		push_warning("Profile: не сохранился %s: %s" % [path, error_string(err)])


## Старт забега: номер забега и стартовая пара.
func start_run(genre: Game.Genre, tech: Game.Tech) -> int:
	runs_started += 1
	last_start_genre = int(genre)
	last_start_tech = int(tech)
	save()
	return runs_started


## Релиз закрыт: игра в галерею.
func add_game(r: GameRecord, run_number: int, release: int, studio: String) -> void:
	gallery.append(GalleryEntry.of(r, run_number, release, studio))
	save()


## Конец забега: лучшая оценка концовки и счётчики.
func finish_run(ending: StringName, score: int) -> void:
	runs_finished += 1
	ending_counts[ending] = ending_counts.get(ending, 0) + 1
	if not best_endings.has(ending) or score > best_endings[ending]:
		best_endings[ending] = score
	save()


func _to_string() -> String:
	return "забегов %d/%d, игр %d, концовки %s, лучшие %s, пара %d×%d" % [runs_finished, runs_started, gallery.size(),
		ending_counts, best_endings, last_start_genre, last_start_tech]
