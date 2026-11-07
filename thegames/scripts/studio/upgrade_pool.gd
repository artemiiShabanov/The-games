class_name UpgradePool
extends RefCounted
## Все `UpgradeDef` из `res://resources/upgrades/`, отсортированные по имени файла.

const DIR := "res://resources/upgrades/"

static var _cache: Array[UpgradeDef] = []


static func load_all() -> Array[UpgradeDef]:
	if not _cache.is_empty():
		return _cache.duplicate()
	var dir := DirAccess.open(DIR)
	if dir == null:
		push_error("UpgradePool: нет папки " + DIR)
		return []
	var names: PackedStringArray = []
	for f in dir.get_files():
		if f.ends_with(".tres") or f.ends_with(".res"):
			names.append(f)
	names.sort()
	for f in names:
		var def := load(DIR + f) as UpgradeDef
		if def != null:
			_cache.append(def)
	return _cache.duplicate()


static func find(pool: Array[UpgradeDef], id: StringName) -> UpgradeDef:
	for d in pool:
		if d.id == id:
			return d
	return null
