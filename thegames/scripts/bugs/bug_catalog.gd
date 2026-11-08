class_name BugCatalog
extends Resource
## Каталог багов, ресурс `res://resources/bugs/catalog.tres`. Подбирает баг под проваленную
## мини-игру с учётом того, что уже есть в записи игры: второй провал того же аспекта даёт
## второй баг аспекта, если он есть в каталоге, иначе нового бага нет (спека мини-игр). У
## каждого аспекта по два бага (#38), выбор среди ещё не полученных по весам `BugDef.weight`
## от `rng`; без `rng` первый по порядку каталога (детерминированные тесты).

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
## уже там (или подходящих нет вовсе). С `rng` случайный по весам.
func pick_new(def: MinigameDef, record: GameRecord, rng: RandomNumberGenerator = null) -> BugDef:
	var fresh: Array[BugDef] = []
	for b in matching(def):
		if not record.has_bug(b.id):
			fresh.append(b)
	if fresh.is_empty():
		return null
	if rng == null:
		return fresh[0]
	var total := 0.0
	for b in fresh:
		total += maxf(b.weight, 0.0)
	var roll := rng.randf() * total
	for b in fresh:
		roll -= maxf(b.weight, 0.0)
		if roll <= 0.0:
			return b
	return fresh[fresh.size() - 1]


## Баг для штампа на карточке результата: новый, а если новых нет, уже имеющийся того же
## владельца. Null, если в каталоге нет бага под эту мини-игру.
func stamp_bug(def: MinigameDef, record: GameRecord) -> BugDef:
	var fresh := pick_new(def, record)
	if fresh != null:
		return fresh
	var all := matching(def)
	return all[all.size() - 1] if not all.is_empty() else null


## Провал спринта: кладёт баг в запись, возвращает его (или null, если нечего класть).
func apply_fail(def: MinigameDef, record: GameRecord, rng: RandomNumberGenerator = null) -> BugDef:
	var bug := pick_new(def, record, rng)
	if bug != null:
		record.add_bug(bug.id)
	return bug
