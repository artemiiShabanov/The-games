class_name StudioState
extends Resource
## Состояние студии на забег, спеки `docs/specs/studio.md` и `staff.md`: купленные жанры и
## технологии, штат (люди с ролью и грейдом, 2026-11-17), число человечков на сцене, было ли
## спасение издателя (второго нет, спека экономики). Эффекты читаются методами ниже: считаются
## от штата; прежние возможности (`manager`, `qa`, ...) в старых сохранениях работают как были.

const MAX_PEOPLE := 12

@export var upgrade_ids: Array[StringName] = []
## Релиз покупки для каждой прокачки в `upgrade_ids` (#78, список купленного по порядку).
@export var bought_release: Array[int] = []
@export var people := 1
## Штат: нанятые с доски соискателей, по порядку найма.
@export var staff: Array[StaffMember] = []
@export var rescued := false


func has(id: StringName) -> bool:
	return upgrade_ids.has(id)


func buy(def: UpgradeDef, release := 0) -> void:
	if not has(def.id):
		upgrade_ids.append(def.id)
		bought_release.append(release)


func hire(m: StaffMember, release := 0) -> void:
	m.hired = release
	staff.append(m)


## Человечков на сцене: основатель, по разработчику каждые `developer_every` релизов (для
## картинки) и весь штат.
func refresh_people(release: int) -> void:
	var t := StaffTuning.load_default()
	people = mini(1 + (release - 1) / maxi(t.developer_every, 1) + staff.size(), MAX_PEOPLE)


## Скидка менеджеров на цену спринта, сложным процентом.
func discount(economy: EconomyTuning) -> float:
	var keep := 1.0 - Staff.share(staff, Staff.Role.MANAGER, StaffTuning.load_default())
	if has(&"manager"):
		keep *= 1.0 - economy.manager_discount
	return 1.0 - keep


## Скидка тестировщиков на спринт багфикса.
func bugfix_discount() -> float:
	return Staff.share(staff, Staff.Role.TESTER, StaffTuning.load_default())


## Скидка сеньора-продюсера на разработку сиквелов и ремейков.
func producer_discount() -> float:
	var t := StaffTuning.load_default()
	return t.producer_discount if Staff.best_grade(staff, Staff.Role.PRODUCER) >= Staff.Grade.SENIOR else 0.0


## Насколько проще мини-игры аспекта: доля, на которую падает их сложность.
func ease(aspect: int) -> float:
	return Staff.ease(staff, aspect, StaffTuning.load_default())


## Повторов проваленного спринта за релиз: от тимлидов.
func replays() -> int:
	var t := StaffTuning.load_default()
	return mini(Staff.replays(staff, t) + int(has(&"replay")) + int(has(&"replay2")), t.max_replays)


## Предложений багфикса за релиз: с тестировщиком-сеньором два.
func bugfix_offers() -> int:
	return 2 if has(&"qa") or Staff.best_grade(staff, Staff.Role.TESTER) >= Staff.Grade.SENIOR else 1


## Что видит аналитик: 0 ничего, 2 жанр и сеттинг в тренде (любой грейд, 2026-11-17).
## Уровни 1 и 3 конструктор ещё понимает, штат их больше не даёт.
func insider_level() -> int:
	return 2 if has(&"insider") or Staff.count(staff, Staff.Role.ANALYST) > 0 else 0


func insider() -> bool:
	return insider_level() > 0


func sequels_unlocked() -> bool:
	return has(&"sequels") or Staff.best_grade(staff, Staff.Role.PRODUCER) >= Staff.Grade.JUNIOR


func remakes_unlocked() -> bool:
	return has(&"remakes") or Staff.best_grade(staff, Staff.Role.PRODUCER) >= Staff.Grade.MIDDLE


## Релиз покупки прокачки номер `i` (0, если неизвестно: старое сохранение, дебаг).
func release_of(i: int) -> int:
	return bought_release[i] if i < bought_release.size() else 0


func _to_string() -> String:
	return "прокачки %s, штат %s, людей %d%s" % [upgrade_ids, staff, people, ", спасены" if rescued else ""]  # i18n: skip
