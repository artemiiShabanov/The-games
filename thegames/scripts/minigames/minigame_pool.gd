class_name MinigamePool
extends RefCounted
## Все `MinigameDef` из `res://resources/minigames/`, отсортированные по id. Прототипы на пробу
## лежат в подпапке `proto/`: в планы спринтов и общий набор не попадают, их видят только
## дебаг-меню и тест раннера (`load_protos`).

const DIR := "res://resources/minigames/"
const PROTO_DIR := "res://resources/minigames/proto/"
const TUNING_PATH := "res://resources/sprints.tres"

static var _cache: Array[MinigameDef] = []


static func load_all() -> Array[MinigameDef]:
	if _cache.is_empty():
		_cache = _load_dir(DIR)
	return _cache.duplicate()


## Прототипы мини-игр из `proto/`; папки может не быть.
static func load_protos() -> Array[MinigameDef]:
	return _load_dir(PROTO_DIR) if DirAccess.dir_exists_absolute(PROTO_DIR) else ([] as Array[MinigameDef])


static func _load_dir(path: String) -> Array[MinigameDef]:
	var out: Array[MinigameDef] = []
	var dir := DirAccess.open(path)
	if dir == null:
		push_error("MinigamePool: нет папки " + path)
		return out
	var names: PackedStringArray = []
	for f in dir.get_files():
		# В экспорте ресурсы лежат как `.tres.remap`.
		f = f.trim_suffix(".remap")
		if f.ends_with(".tres") or f.ends_with(".res"):
			names.append(f)
	names.sort()
	for f in names:
		var def := load(path + f) as MinigameDef
		if def != null:
			out.append(def)
	return out


static func load_tuning() -> SprintTuning:
	return load(TUNING_PATH) as SprintTuning


static func find(pool: Array[MinigameDef], id: StringName) -> MinigameDef:
	for d in pool:
		if d.id == id:
			return d
	return null
