class_name UpgradeDef
extends Resource
## Прокачка студии, спека `docs/specs/studio.md`: технология, жанр или возможность. Пул лежит в
## `res://resources/upgrades/*.tres` (v1 из `debug/tools/bootstrap_upgrades.gd`). Цена и
## надбавка к содержанию не хранятся здесь, а берутся из `EconomyTuning`, чтобы тюнинг-числа
## жили в одном ресурсе. `requires` это id прокачек, без которых эта не предлагается.
## Предмет на экране (`prop`) словами из спеки, сцена предмета придёт в M5.

enum Kind { TECH, GENRE, CAPABILITY }

const KIND_NAMES: Array[String] = ["технология", "жанр", "возможность"]

@export var id: StringName = &""
@export var kind: Kind = Kind.CAPABILITY
@export var title := ""
## Одна строка эффекта на карточке предложения.
@export var effect_line := ""
@export var requires: Array[StringName] = []
## Для технологии и жанра: что открывает.
@export var tech: Game.Tech = Game.Tech.ASCII
@export var genre: Game.Genre = Game.Genre.PLATFORMER
@export var prop := ""


func kind_name() -> String:
	return KIND_NAMES[kind]


func price(economy: EconomyTuning) -> int:
	match kind:
		Kind.TECH:
			return economy.unlock_price_by_tech[tech]
		Kind.GENRE:
			return economy.genre_unlock_price
	return economy.capability_price(id)


func upkeep(economy: EconomyTuning) -> int:
	match kind:
		Kind.TECH:
			return economy.unlock_upkeep_by_tech[tech]
		Kind.GENRE:
			return economy.genre_unlock_upkeep
	return economy.capability_upkeep(id)


func _to_string() -> String:
	return "%s (%s)" % [id, kind_name()]
