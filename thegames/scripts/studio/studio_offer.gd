class_name StudioOffer
extends RefCounted
## Состав предложения после релиза как чистая функция, спека `docs/specs/studio.md`: до трёх
## разных карточек, только жанры и технологии (2026-11-17: улучшения студии ушли в штат,
## `docs/specs/staff.md`), хотя бы одна технология и один жанр, пока они остались. Купленное, уже открытое и то, чьи `requires` не куплены,
## не предлагается; ремейки не предлагаются, пока открыта одна технология. «Новый сеттинг»
## (#139) одна карточка на предложение: случайный из закрытых сеттингов с готовым набором. Пул исчерпан: карточек меньше, пуст: ни одной. Порядок случайный от `rng`.


static func compose(pool: Array[UpgradeDef], state: StudioState, unlocked_genres: Array[Game.Genre],
		unlocked_techs: Array[Game.Tech], rng: RandomNumberGenerator, count := 3,
		unlocked_settings: Array[Game.Setting] = []) -> Array[UpgradeDef]:
	var candidates := available(pool, state, unlocked_genres, unlocked_techs, unlocked_settings)
	_shuffle(candidates, rng)
	# Сначала по одной карточке каждого вида, чтобы выбор был между жанром и технологией.
	var out: Array[UpgradeDef] = []
	for kind in [UpgradeDef.Kind.TECH, UpgradeDef.Kind.GENRE]:
		for d in candidates:
			if d.kind == kind and out.size() < count:
				out.append(d)
				candidates.erase(d)
				break
	for d in candidates:
		if out.size() >= count:
			break
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
