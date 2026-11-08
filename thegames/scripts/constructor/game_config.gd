class_name GameConfig
extends Resource
## Конфигурация следующей игры из конструктора, спека `docs/specs/constructor.md`: тройка,
## вид (новая, сиквел, ремейк), родитель для сиквела и ремейка, название, число спринтов и
## цена спринта на момент старта. Сиквелы и ремейки с #24.

enum Kind { NEW, SEQUEL, REMAKE }

@export var genre: Game.Genre = Game.Genre.PLATFORMER
@export var tech: Game.Tech = Game.Tech.BIT8
@export var setting: Game.Setting = Game.Setting.PIRATES
@export var kind: Kind = Kind.NEW
@export var parent: GameRecord
@export var title := ""
@export var sprints := 0
@export var sprint_cost := 0


func total_cost() -> int:
	return sprints * sprint_cost


## Запись игры для разработки: сид демки задаёт хозяин. Сиквел получает номер части и
## родителя, ремейк флаг и родителя (входы формул успеха).
func to_record(seed_: int) -> GameRecord:
	var r := GameRecord.create(genre, tech, seed_, title, setting)
	match kind:
		Kind.SEQUEL:
			r.parent = parent
			r.part = parent.part + 1 if parent != null else 2
		Kind.REMAKE:
			r.parent = parent
			r.remake = true
			r.part = parent.part if parent != null else 1
	return r


func _to_string() -> String:
	return "%s (%s × %s × %s, %d × %d = %d)" % [title, Game.genre_name(genre), Game.tech_name(tech),
			Game.setting_name(setting), sprints, sprint_cost, total_cost()]
