class_name SprintPlanner
extends RefCounted
## Подбор набора мини-игр на релиз, чистая функция от входов и `rng`.
## Правила (`docs/specs/minigames.md`): мини-игра технологии и мини-игра жанра всегда, если
## они есть в пуле; остальные спринты аспектным по убыванию суммы весов пары, по одному
## аспекту за круг, случайная из его мини-игр; когда спринтов больше, чем аспектов, второй
## круг отдаёт аспектам их вторые мини-игры в том же порядке. Порядок перемешан; первой не
## стоит `avoid_first`, если есть чем заменить.


static func plan(n: int, genre: Game.Genre, tech: Game.Tech, pool: Array[MinigameDef],
		tuning: SprintTuning, rng: RandomNumberGenerator, avoid_first: StringName = &"",
		replays := 0) -> SprintPlan:
	var result := SprintPlan.new()
	result.replay_left = replays
	var picked: Array[MinigameDef] = []

	var tech_def := _find(pool, MinigameDef.Kind.TECH, tech)
	if tech_def != null:
		picked.append(tech_def)
	var genre_def := _find(pool, MinigameDef.Kind.GENRE, genre)
	if genre_def != null:
		picked.append(genre_def)

	var slots := n - picked.size()
	var order := tuning.aspects_by_weight(genre, tech)
	var remaining := {}
	for a in order:
		var defs: Array[MinigameDef] = []
		for d in pool:
			if d.kind == MinigameDef.Kind.ASPECT and d.aspect == a:
				defs.append(d)
		remaining[a] = defs
	while slots > 0:
		var added := false
		for a in order:
			if slots <= 0:
				break
			var defs: Array[MinigameDef] = remaining[a]
			if defs.is_empty():
				continue
			var i := rng.randi_range(0, defs.size() - 1)
			picked.append(defs[i])
			defs.remove_at(i)
			slots -= 1
			added = true
		if not added:
			break

	_shuffle(picked, rng)
	if picked.size() > 1 and picked[0].id == avoid_first:
		var j := rng.randi_range(1, picked.size() - 1)
		var tmp := picked[0]
		picked[0] = picked[j]
		picked[j] = tmp
	result.defs = picked
	return result


## Доля аспектов, которые получили хотя бы один спринт: для подсказок и тестов.
static func aspects_in(plan_: SprintPlan) -> Array[Game.Aspect]:
	var out: Array[Game.Aspect] = []
	for d in plan_.defs:
		if d.kind == MinigameDef.Kind.ASPECT and not out.has(d.aspect):
			out.append(d.aspect)
	return out


static func _find(pool: Array[MinigameDef], kind: MinigameDef.Kind, owner: int) -> MinigameDef:
	for d in pool:
		if d.kind != kind:
			continue
		if kind == MinigameDef.Kind.TECH and d.tech == owner:
			return d
		if kind == MinigameDef.Kind.GENRE and d.genre == owner:
			return d
	return null


static func _shuffle(arr: Array[MinigameDef], rng: RandomNumberGenerator) -> void:
	for i in range(arr.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var tmp := arr[i]
		arr[i] = arr[j]
		arr[j] = tmp
