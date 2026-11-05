class_name MinigamePool
extends RefCounted
## Все `MinigameDef` из `res://resources/minigames/`, отсортированные по id.

const DIR := "res://resources/minigames/"
const TUNING_PATH := "res://resources/sprints.tres"

static var _cache: Array[MinigameDef] = []


static func load_all() -> Array[MinigameDef]:
	if not _cache.is_empty():
		return _cache.duplicate()
	var dir := DirAccess.open(DIR)
	if dir == null:
		push_error("MinigamePool: нет папки " + DIR)
		return []
	var names: PackedStringArray = []
	for f in dir.get_files():
		if f.ends_with(".tres") or f.ends_with(".res"):
			names.append(f)
	names.sort()
	for f in names:
		var def := load(DIR + f) as MinigameDef
		if def != null:
			_cache.append(def)
	return _cache.duplicate()


static func load_tuning() -> SprintTuning:
	return load(TUNING_PATH) as SprintTuning


static func find(pool: Array[MinigameDef], id: StringName) -> MinigameDef:
	for d in pool:
		if d.id == id:
			return d
	return null
