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
## Франшиза: номер части (1 новая игра), ремейк и родитель для сиквела и ремейка (#24).
@export var part := 1
@export var remake := false
@export var parent: GameRecord
## Отклик на релиз (спека успеха); хвост тикает между релизами.
@export var score: ReleaseScore
## Из вставок (#66): доля с хвоста (сумма долей, не больше `MetaTuning.max_tail_share`) и кому,
## хвост продан (больше не платит), бонусы к отклику этой игры.
@export var tail_share := 0.0
@export var share_to: PackedStringArray = []
@export var tail_sold := false
@export var bonus_critics := 0.0
@export var bonus_streamers := 0.0
@export var bonus_sales := 0.0


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


## Имя франшизы: название первой части.
func franchise_title() -> String:
	var r := self
	while r.parent != null and not r.remake:
		r = r.parent
	return r.title


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
