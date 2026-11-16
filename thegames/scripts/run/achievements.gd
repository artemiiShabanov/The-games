class_name Achievements
extends RefCounted
## Достижения и открытие сеттингов (#139), спека `docs/specs/run.md`. Достижение засчитывается
## в любом забеге и слоте один раз и пишется в `Profile`; его сеттинг открыт сразу и во всех
## забегах. Сеттинг с неготовым набором (`SettingDef.complete`) достижением не открывается.
## Проверка `check` зовётся главной сценой в фазе студии и на концовке; прогресс `progress`
## читает экран сеттингов.

const DIR := "res://resources/achievements/"

static var _cache: Array[AchievementDef] = []


## Все достижения в порядке сеттингов.
static func load_all() -> Array[AchievementDef]:
	if _cache.is_empty():
		var dir := DirAccess.open(DIR)
		if dir == null:
			push_error("Achievements: нет папки " + DIR)
			return []
		for f in dir.get_files():
			var file := f.trim_suffix(".remap")
			if file.ends_with(".tres"):
				var d := load(DIR + file) as AchievementDef
				if d != null:
					_cache.append(d)
		_cache.sort_custom(func(a: AchievementDef, b: AchievementDef) -> bool: return a.setting < b.setting)
	return _cache.duplicate()


static func find(id: StringName) -> AchievementDef:
	for d in load_all():
		if d.id == id:
			return d
	return null


static func for_setting(s: Game.Setting) -> AchievementDef:
	for d in load_all():
		if d.setting == s:
			return d
	return null


## Набор сеттинга готов: только такой открывается и предлагается.
static func ready(s: Game.Setting) -> bool:
	var def := SettingDef.of(s)
	return def != null and def.complete


## Сеттинги, открытые достижениями профиля, по порядку перечисления.
static func unlocked(profile: Profile) -> Array[Game.Setting]:
	var out: Array[Game.Setting] = []
	if profile == null:
		return out
	for d in load_all():
		if profile.achievements.has(d.id) and ready(d.setting):
			out.append(d.setting)
	return out


## Что выполнено сейчас и ещё не засчитано: пишет в профиль, возвращает новые. `records` это
## игры забега вместе с текущей, `ending` ключ концовки, если забег кончился.
static func check(profile: Profile, run: RunState, records: Array[GameRecord], ending: StringName = &"") -> Array[AchievementDef]:
	var fresh: Array[AchievementDef] = []
	if profile == null:
		return fresh
	for d in load_all():
		if profile.achievements.has(d.id) or not ready(d.setting):
			continue
		if _done(d, run, records, ending):
			profile.achievements[d.id] = int(Time.get_unix_time_from_system())
			fresh.append(d)
	if not fresh.is_empty():
		profile.save()
	return fresh


static func _done(d: AchievementDef, run: RunState, records: Array[GameRecord], ending: StringName) -> bool:
	if d.condition == AchievementDef.Condition.ENDING:
		return ending != &"" and ending == d.ending
	return value(d, run, records) >= d.threshold


## Сколько набрано по условию в этом забеге (для порога и строки прогресса).
static func value(d: AchievementDef, run: RunState, records: Array[GameRecord]) -> int:
	match d.condition:
		AchievementDef.Condition.CASH:
			return run.wallet.cash if run != null else 0
		AchievementDef.Condition.PERFECT_CRITICS:
			var best := 0
			for r in records:
				best = maxi(best, _lowest_critic(r, run))
			return best
		AchievementDef.Condition.FRANCHISE_PART:
			var part := 0
			for r in records:
				if not r.remake:
					part = maxi(part, r.part)
			return part
		AchievementDef.Condition.PAID_STREAK:
			return _streak(records, func(r: GameRecord) -> bool:
				return r.score != null and r.cost > 0 and r.score.sales_first >= r.cost)
		AchievementDef.Condition.CLEAN_STREAK:
			return _streak(records, func(r: GameRecord) -> bool: return r.score != null and r.score.bugs == 0)
		AchievementDef.Condition.TECHS_IN_RUN:
			var techs := {}
			for r in records:
				techs[r.tech] = true
			return techs.size()
	return 0


## Самая низкая оценка критика у игры, целые баллы вниз (10 только когда все поставили 10).
static func _lowest_critic(r: GameRecord, run: RunState) -> int:
	if r.score == null or run == null or run.critics == null or run.critics.people.is_empty():
		return 0
	var low := 10.0
	for p in run.critics.people:
		low = minf(low, snappedf(Feed.critic_score(p, r.score, r, run.success), 0.1))
	return int(floorf(low + 0.001))


## Длина серии с конца списка.
static func _streak(records: Array[GameRecord], ok: Callable) -> int:
	var n := 0
	for i in range(records.size() - 1, -1, -1):
		if not ok.call(records[i]):
			break
		n += 1
	return n


## Прогресс в текущем забеге строкой, пусто, если показывать нечего.
static func progress(d: AchievementDef, run: RunState) -> String:
	if run == null:
		return ""
	var v := value(d, run, run.records)
	match d.condition:
		AchievementDef.Condition.CASH:
			return "%s из %s" % [Style.format_money(maxi(v, 0)), Style.format_money(d.threshold)]
		AchievementDef.Condition.PERFECT_CRITICS, AchievementDef.Condition.ENDING:
			return ""
		AchievementDef.Condition.FRANCHISE_PART:
			return "часть %d из %d" % [mini(v, d.threshold), d.threshold] if v > 1 else ""
	return "%d из %d" % [mini(v, d.threshold), d.threshold]
