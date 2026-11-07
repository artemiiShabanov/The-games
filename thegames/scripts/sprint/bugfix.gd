class_name Bugfix
extends RefCounted
## Спринт багфикса после плейтеста, спека `docs/specs/demos.md` (#27). Стоит обычный спринт
## (экономика: `bugfix_price`), это случайная аспектная мини-игра через `SprintRunner`; успех
## чинит половину текущих багов с округлением вверх, какие именно, случайно; провал ничего не
## добавляет. Возможность «Отдел QA» даёт второе предложение за релиз (#29).


## Сколько багов починит успех: половина с округлением вверх.
static func fix_count(record: GameRecord) -> int:
	return (record.bug_ids.size() + 1) / 2


## Случайная аспектная мини-игра со сценой; ни одна не подходит: null.
static func pick_minigame(pool: Array[MinigameDef], rng: RandomNumberGenerator) -> MinigameDef:
	var options: Array[MinigameDef] = []
	for d in pool:
		if d.kind == MinigameDef.Kind.ASPECT and d.scene != null:
			options.append(d)
	if options.is_empty():
		return null
	return options[rng.randi_range(0, options.size() - 1)]


## План из одной мини-игры для раннера.
static func plan_for(def: MinigameDef) -> SprintPlan:
	var p := SprintPlan.new()
	p.defs = [def]
	return p


## Починить половину багов записи случайно; возвращает id починенных.
static func apply_fix(record: GameRecord, rng: RandomNumberGenerator) -> Array[StringName]:
	var fixed: Array[StringName] = []
	var pool := record.bug_ids.duplicate()
	var n := fix_count(record)
	for i in n:
		if pool.is_empty():
			break
		var k := rng.randi_range(0, pool.size() - 1)
		fixed.append(pool[k])
		pool.remove_at(k)
	for id in fixed:
		record.bug_ids.erase(id)
	return fixed


## Цена спринта багфикса для записи.
static func price(record: GameRecord, economy: EconomyTuning, discount := 0.0) -> int:
	return economy.bugfix_price(record.genre, record.tech, record.setting, discount)
