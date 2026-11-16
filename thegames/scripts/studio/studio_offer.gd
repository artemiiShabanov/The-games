class_name StudioOffer
extends RefCounted
## Состав предложения прокачки как чистая функция, спека `docs/specs/studio.md`: до трёх
## разных карточек, не больше одной технологии, не больше одного жанра, хотя бы одна
## возможность, если она осталась. Купленное, уже открытое и то, чьи `requires` не куплены,
## не предлагается; ремейки не предлагаются, пока открыта одна технология. «Новый сеттинг»
## (#139) одна карточка на предложение: случайный из закрытых сеттингов с готовым набором. Пул исчерпан: карточек меньше, пуст: ни одной. Порядок случайный от `rng`.


static func compose(pool: Array[UpgradeDef], state: StudioState, unlocked_genres: Array[Game.Genre],
		unlocked_techs: Array[Game.Tech], rng: RandomNumberGenerator, count := 3,
		unlocked_settings: Array[Game.Setting] = []) -> Array[UpgradeDef]:
	var candidates := available(pool, state, unlocked_genres, unlocked_techs, unlocked_settings)
	# «Новый сеттинг» это одна возможность пула: из закрытых остаётся один случайный.
	var closed: Array[UpgradeDef] = []
	for d in candidates:
		if d.setting >= 0:
			closed.append(d)
	if closed.size() > 1:
		var keep := closed[rng.randi_range(0, closed.size() - 1)]
		for d in closed:
			if d != keep:
				candidates.erase(d)
	_shuffle(candidates, rng)
	var out: Array[UpgradeDef] = []
	for d in candidates:
		if d.kind == UpgradeDef.Kind.CAPABILITY:
			out.append(d)
			candidates.erase(d)
			break
	var tech_used := false
	var genre_used := false
	for d in candidates:
		if out.size() >= count:
			break
		if d.kind == UpgradeDef.Kind.TECH:
			if tech_used:
				continue
			tech_used = true
		elif d.kind == UpgradeDef.Kind.GENRE:
			if genre_used:
				continue
			genre_used = true
		out.append(d)
	_shuffle(out, rng)
	return out


## Что вообще может выпасть при этом состоянии.
static func available(pool: Array[UpgradeDef], state: StudioState, unlocked_genres: Array[Game.Genre],
		unlocked_techs: Array[Game.Tech], unlocked_settings: Array[Game.Setting] = []) -> Array[UpgradeDef]:
	var out: Array[UpgradeDef] = []
	for d in pool:
		if state.has(d.id):
			continue
		if d.setting >= 0 and (unlocked_settings.is_empty() or unlocked_settings.has(d.setting as Game.Setting)
				or not Achievements.ready(d.setting as Game.Setting)):
			continue
		if d.kind == UpgradeDef.Kind.TECH and unlocked_techs.has(d.tech):
			continue
		if d.kind == UpgradeDef.Kind.GENRE and unlocked_genres.has(d.genre):
			continue
		# Ремейк требует другую технологию: пока открыта одна, он не предлагается (#45).
		if d.id == &"remakes" and unlocked_techs.size() < 2:
			continue
		var ok := true
		for r in d.requires:
			if not state.has(r):
				ok = false
		if ok:
			out.append(d)
	return out


## Тасование своим генератором: `Array.shuffle` берёт глобальный.
static func _shuffle(arr: Array[UpgradeDef], rng: RandomNumberGenerator) -> void:
	for i in range(arr.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var tmp := arr[i]
		arr[i] = arr[j]
		arr[j] = tmp
