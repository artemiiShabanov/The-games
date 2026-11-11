class_name StudioState
extends Resource
## Состояние студии на забег, спека `docs/specs/studio.md`: купленные прокачки, число
## человечков (предметы и люди на сцене в M5), было ли спасение издателя (второго нет, спека
## экономики). Эффекты возможностей читаются через `has(id)`, без разбросанных флагов (#29).

const MAX_PEOPLE := 12

@export var upgrade_ids: Array[StringName] = []
## Релиз покупки для каждой прокачки в `upgrade_ids` (#78, список купленного по порядку).
@export var bought_release: Array[int] = []
@export var people := 1
@export var rescued := false


func has(id: StringName) -> bool:
	return upgrade_ids.has(id)


func buy(def: UpgradeDef, release := 0) -> void:
	if not has(def.id):
		upgrade_ids.append(def.id)
		bought_release.append(release)
	people = mini(people + 1, MAX_PEOPLE)


## Скидка «Менеджера» на цену спринта.
func discount(economy: EconomyTuning) -> float:
	return economy.manager_discount if has(&"manager") else 0.0


## Эффекты возможностей (#29), читаются хозяевами систем.
## Переигровок за релиз: «Переигровка» одна, «Вторая переигровка» ещё одна.
func replays() -> int:
	return int(has(&"replay")) + int(has(&"replay2"))


## Предложений багфикса за релиз: с «Отделом QA» два.
func bugfix_offers() -> int:
	return 2 if has(&"qa") else 1


## «Инсайдер»: в конструкторе видно тренд.
func insider() -> bool:
	return has(&"insider")


func sequels_unlocked() -> bool:
	return has(&"sequels")


func remakes_unlocked() -> bool:
	return has(&"remakes")


## Релиз покупки прокачки номер `i` (0, если неизвестно: старое сохранение, дебаг).
func release_of(i: int) -> int:
	return bought_release[i] if i < bought_release.size() else 0


func _to_string() -> String:
	return "прокачки %s, людей %d%s" % [upgrade_ids, people, ", спасены" if rescued else ""]
