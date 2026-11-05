class_name BugCatalog
extends Resource
## Каталог багов, ресурс `res://resources/bugs/catalog.tres`. Подбирает баг под проваленную
## мини-игру с учётом того, что уже есть в записи игры: второй провал того же аспекта даёт
## второй баг аспекта, если он есть в каталоге, иначе нового бага нет (спека мини-игр).

const PATH := "res://resources/bugs/catalog.tres"

@export var bugs: Array[BugDef] = []


static func load_default() -> BugCatalog:
	return load(PATH) as BugCatalog


func by_id(id: StringName) -> BugDef:
	for b in bugs:
		if b.id == id:
			return b
	return null


func matching(def: MinigameDef) -> Array[BugDef]:
	var out: Array[BugDef] = []
	for b in bugs:
		if b.matches(def):
			out.append(b)
	return out


## Новый баг за провал мини-игры, которого ещё нет в записи, или null, если все подходящие
## уже там (или подходящих нет вовсе).
func pick_new(def: MinigameDef, record: GameRecord) -> BugDef:
	for b in matching(def):
		if not record.has_bug(b.id):
			return b
	return null


## Баг для штампа на карточке результата: новый, а если новых нет, уже имеющийся того же
## владельца. Null, если в каталоге нет бага под эту мини-игру.
func stamp_bug(def: MinigameDef, record: GameRecord) -> BugDef:
	var fresh := pick_new(def, record)
	if fresh != null:
		return fresh
	var all := matching(def)
	return all[all.size() - 1] if not all.is_empty() else null


## Провал спринта: кладёт баг в запись, возвращает его (или null, если нечего класть).
func apply_fail(def: MinigameDef, record: GameRecord) -> BugDef:
	var bug := pick_new(def, record)
	if bug != null:
		record.add_bug(bug.id)
	return bug
