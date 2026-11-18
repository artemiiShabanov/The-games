class_name Staff
extends RefCounted
## Штат студии (полировка 2026-11-17), спека `docs/specs/staff.md`. Улучшения студии это люди:
## роль и грейд (джуниор, мидл, сеньор) с разной ценой, зарплатой и силой эффекта. Соискатели
## приходят на доску после каждого релиза и ждут несколько релизов; нанимать можно сколько
## угодно, пока хватает денег. Жанры и технологии сюда не входят: их по-прежнему предлагает
## выбор после релиза (`StudioOffer`).
## Роли:
## - пять специалистов по аспектам упрощают мини-игры своего аспекта (сложность `t` ниже на
##   долю); одинаковые складываются сложным процентом, как и скидки;
## - менеджер: спринт дешевле; тестировщик: багфикс дешевле, сеньор ещё и второй спринт багфикса;
## - тимлид (только сеньор): повтор проваленного спринта;
## - продюсер: сиквелы (джуниор), ещё и ремейки (мидл), ещё и скидка на них (сеньор);
## - аналитик (только мидл): тренд жанра и сеттинга.
## Здесь чистые функции от списка людей и чисел `StaffTuning`.

enum Role { PROGRAMMER, SOUND, CONTROLS, ARTIST, DESIGNER, MANAGER, TESTER, LEAD, PRODUCER, ANALYST }
enum Grade { JUNIOR, MIDDLE, SENIOR }

## На карточках по-английски (2026-11-17): так грейды и называют в студиях.
const GRADE_NAMES: Array[String] = ["Junior", "Middle", "Senior"]
const TITLES: Array[String] = ["Программист", "Звукорежиссёр", "Дизайнер управления", "Художник", "Геймдизайнер",
		"Менеджер", "Тестировщик", "Тимлид", "Продюсер", "Аналитик"]
const IDS: Array[StringName] = [&"programmer", &"sound", &"controls", &"artist", &"designer", &"manager", &"tester",
		&"lead", &"producer", &"analyst"]
## Аспект, мини-игры которого упрощает роль; у остальных ролей −1.
const ASPECTS: Array[int] = [Game.Aspect.OPTIMIZATION, Game.Aspect.SOUND, Game.Aspect.CONTROLS, Game.Aspect.GRAPHICS,
		Game.Aspect.BALANCE, -1, -1, -1, -1, -1]


static func title(role: Role) -> String:
	return Lang.t(TITLES[role])


static func is_aspect(role: Role) -> bool:
	return ASPECTS[role] >= 0


## Роль, второй человек которой ничего не добавит сверх лучшего грейда.
static func is_unique(role: Role) -> bool:
	return role == Role.PRODUCER or role == Role.ANALYST


## Строка эффекта на карточке соискателя и в списке штата.
static func effect_line(role: Role, grade: Grade, t: StaffTuning) -> String:
	var v := t.value(role, grade)
	var pct := ("%d%%" if Lang.english() else "%d %%") % roundi(v * 100.0)
	if is_aspect(role):
		var aspect := Game.aspect_name(ASPECTS[role] as Game.Aspect)
		return Lang.t("Мини-игры аспекта «%s» проще на %s") % [aspect.left(1).to_upper() + aspect.substr(1) if Lang.english() else aspect.to_lower(), pct]
	match role:
		Role.MANAGER:
			return Lang.t("Цена спринта на %s ниже") % pct
		Role.TESTER:
			if grade == Grade.SENIOR:
				return Lang.t("Багфикс на %s дешевле, второй спринт багфикса за релиз") % pct
			return Lang.t("Багфикс на %s дешевле") % pct
		Role.LEAD:
			var n := roundi(v)
			return Lang.t("Повторов проваленного спринта за релиз: %d") % n
		Role.PRODUCER:
			if grade == Grade.JUNIOR:
				return Lang.t("Сиквелы в конструкторе")
			if grade == Grade.MIDDLE:
				return Lang.t("Сиквелы и ремейки в конструкторе")
			return Lang.t("Сиквелы и ремейки, их разработка на %d %% дешевле") % roundi(t.producer_discount * 100.0)
		Role.ANALYST:
			return Lang.t("Видны жанр и сеттинг в тренде")
	return ""


## Общая доля людей роли `role` сложным процентом: 10 % и 20 % дают 28 %.
static func share(staff: Array[StaffMember], role: Role, t: StaffTuning) -> float:
	var keep := 1.0
	for m in staff:
		if m.role == role:
			keep *= 1.0 - clampf(t.value(m.role, m.grade), 0.0, 1.0)
	return 1.0 - keep


## Насколько проще мини-игры аспекта: доля, на которую падает их сложность.
static func ease(staff: Array[StaffMember], aspect: int, t: StaffTuning) -> float:
	var i := ASPECTS.find(aspect)
	return share(staff, i as Role, t) if i >= 0 else 0.0


static func count(staff: Array[StaffMember], role: Role) -> int:
	var n := 0
	for m in staff:
		if m.role == role:
			n += 1
	return n


## Лучший грейд роли в штате или −1.
static func best_grade(staff: Array[StaffMember], role: Role) -> int:
	var best := -1
	for m in staff:
		if m.role == role:
			best = maxi(best, int(m.grade))
	return best


static func replays(staff: Array[StaffMember], t: StaffTuning) -> int:
	var n := 0.0
	for m in staff:
		if m.role == Role.LEAD:
			n += t.value(m.role, m.grade)
	return mini(roundi(n), t.max_replays)


## Случайный соискатель: роль равновероятно из тех, что ещё что-то дадут штату, грейд по весам.
## Уникальная роль не приходит грейдом не выше нанятого, тимлид не приходит при потолке повторов.
static func roll(staff: Array[StaffMember], t: StaffTuning, rng: RandomNumberGenerator, until: int) -> StaffMember:
	for attempt in 20:
		var role := rng.randi_range(0, Role.size() - 1) as Role
		# Грейд по весам среди тех, которыми роль приходит (`min_grade`..`max_grade`).
		var low := t.min_grade_of(role)
		var high := mini(t.max_grade_of(role), t.grade_weights.size() - 1)
		var total := 0.0
		for g in range(low, high + 1):
			total += t.grade_weights[g]
		var pick := rng.randf() * total
		var grade := low as Grade
		for g in range(low, high + 1):
			pick -= t.grade_weights[g]
			if pick <= 0.0:
				grade = g as Grade
				break
		if is_unique(role) and best_grade(staff, role) >= int(grade):
			continue
		if role == Role.LEAD and replays(staff, t) >= t.max_replays:
			continue
		return StaffMember.make(role, grade, until)
	return StaffMember.make(Role.PROGRAMMER, Grade.JUNIOR, until)
