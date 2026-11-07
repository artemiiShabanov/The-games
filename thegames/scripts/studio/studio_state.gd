class_name StudioState
extends Resource
## Состояние студии на забег, спека `docs/specs/studio.md`: купленные прокачки, число
## человечков (предметы и люди на сцене в M5), было ли спасение издателя (второго нет, спека
## экономики). Эффекты возможностей читаются через `has(id)`, без разбросанных флагов (#29).

const MAX_PEOPLE := 12

@export var upgrade_ids: Array[StringName] = []
@export var people := 1
@export var rescued := false


func has(id: StringName) -> bool:
	return upgrade_ids.has(id)


func buy(def: UpgradeDef) -> void:
	if not has(def.id):
		upgrade_ids.append(def.id)
	people = mini(people + 1, MAX_PEOPLE)


## Скидка «Менеджера» на цену спринта.
func discount(economy: EconomyTuning) -> float:
	return economy.manager_discount if has(&"manager") else 0.0


func _to_string() -> String:
	return "прокачки %s, людей %d%s" % [upgrade_ids, people, ", спасены" if rescued else ""]
