class_name GalleryEntry
extends Resource
## Игра в галерее профиля (#69): плоская копия записи релиза (тройка, название, часть, сид,
## баги, оценки) и где она вышла (номер забега, релиз, студия). Демка галереи пересобирает из
## неё `GameRecord` с тем же сидом и багами (`to_record`).

@export var title := ""
@export var genre: Game.Genre = Game.Genre.PLATFORMER
@export var tech: Game.Tech = Game.Tech.BIT8
@export var setting: Game.Setting = Game.Setting.PIRATES
@export var part := 1
@export var remake := false
@export var seed := 0
@export var bug_ids: Array[StringName] = []
@export var critics := 0.0
@export var sales_first := 0
@export var streamers := 0
@export var viral := false
@export var run_number := 1
@export var release := 1
@export var studio := ""


static func of(r: GameRecord, run_number_: int, release_: int, studio_: String) -> GalleryEntry:
	var e := GalleryEntry.new()
	e.title = r.title
	e.genre = r.genre
	e.tech = r.tech
	e.setting = r.setting
	e.part = r.part
	e.remake = r.remake
	e.seed = r.seed
	e.bug_ids = r.bug_ids.duplicate()
	if r.score != null:
		e.critics = r.score.critics
		e.sales_first = r.score.sales_first
		e.streamers = r.score.streamers
		e.viral = r.score.viral
	e.run_number = run_number_
	e.release = release_
	e.studio = studio_
	return e


## Запись для демки: тот же сид и те же баги.
func to_record() -> GameRecord:
	var r := GameRecord.create(genre, tech, seed, title, setting)
	r.part = part
	r.remake = remake
	r.bug_ids = bug_ids.duplicate()
	r.score = ReleaseScore.new()
	r.score.critics = critics
	r.score.sales_first = sales_first
	r.score.streamers = streamers
	r.score.viral = viral
	return r
