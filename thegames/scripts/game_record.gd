class_name GameRecord
extends Resource
## Запись игры студии, спека `docs/specs/demos.md`: конфигурация релиза, сид уровня демки,
## список багов и результаты спринтов. Ресурс, чтобы сохраняться вместе с забегом.

@export var title := ""
@export var genre: Game.Genre = Game.Genre.PLATFORMER
@export var tech: Game.Tech = Game.Tech.BIT8
@export var setting: Game.Setting = Game.Setting.PIRATES
## Сид уровня демки: плейтест, лента и галерея показывают один уровень.
@export var seed: int = 0
@export var bug_ids: Array[StringName] = []
@export var sprint_results: Array[bool] = []


static func create(genre_: Game.Genre, tech_: Game.Tech, seed_: int, title_ := "", setting_ := Game.Setting.PIRATES) -> GameRecord:
	var r := GameRecord.new()
	r.genre = genre_
	r.tech = tech_
	r.setting = setting_
	r.seed = seed_
	r.title = title_
	return r


func add_bug(id: StringName) -> void:
	if not bug_ids.has(id):
		bug_ids.append(id)


func has_bug(id: StringName) -> bool:
	return bug_ids.has(id)


func add_sprint(success: bool) -> void:
	sprint_results.append(success)


## Качество игры: успехи / спринты (спека мини-игр).
func quality() -> float:
	if sprint_results.is_empty():
		return 0.0
	var ok := 0
	for s in sprint_results:
		if s:
			ok += 1
	return float(ok) / sprint_results.size()


func _to_string() -> String:
	return "%s (%s × %s, сид %d, баги %s, качество %.2f)" % [
		title, Game.genre_name(genre), Game.tech_name(tech), seed, bug_ids, quality()]
