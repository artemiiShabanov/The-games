class_name BugDef
extends Resource
## Описание бага, спека `docs/specs/demos.md`. Один ресурс на баг в `res://resources/bugs/<id>.tres`,
## все собраны в `BugCatalog`. Баг накладывается на демку как модификатор по флагу из записи
## игры; параметры проявления лежат в `params` и читаются демкой.

enum Kind { ASPECT, GENRE, TECH }

@export var id: StringName
@export var kind: Kind = Kind.ASPECT
@export var aspect: Game.Aspect = Game.Aspect.OPTIMIZATION
@export var genre: Game.Genre = Game.Genre.PLATFORMER
@export var tech: Game.Tech = Game.Tech.ASCII
## Крупно на штампе карточки результата: «15 FPS», «ПРЫЖОК ×3».
@export var stamp: String
## Штамп под жанр записи (#51): ключ `Game.Genre`, без записи общий `stamp`. Нужен багам, чьё
## проявление в жанре другое («ПРЫЖОК ×3» у гонок и шутера это лёд).
@export var stamp_by_genre: Dictionary[int, String] = {}
## Проявление в демке, одной строкой: для карточки результата и ленты.
@export var manifestation: String
## Текст твита в ленте отклика.
@export var tweet: String
## Кадр для клипа стримера: что видно на стоп-кадре.
@export var clip: String
## Те же строки под жанр демки (#44): ключ `Game.Genre`. Баги баланса в каждом жанре проявляются
## по-своему («цель недостижима», «враги от чиха»), у общих багов слова про героя и монеты; без
## записи для жанра берутся общие строки выше.
@export var manifestation_by_genre: Dictionary[int, String] = {}
@export var tweet_by_genre: Dictionary[int, String] = {}
@export var clip_by_genre: Dictionary[int, String] = {}
## Зрелищный баг: чаще попадает в клипы и даёт вирусность.
@export var spectacular := false
## Вес при выборе среди подходящих багов, которых ещё нет в записи (#38).
@export var weight := 1.0
## Параметры проявления: демка читает `param(&"freeze_ms_max", 400.0)`.
@export var params: Dictionary[StringName, float] = {}


func stamp_for(genre: Game.Genre) -> String:
	return stamp_by_genre.get(int(genre), stamp)


func manifestation_for(genre: Game.Genre) -> String:
	return manifestation_by_genre.get(int(genre), manifestation)


func tweet_for(genre: Game.Genre) -> String:
	return tweet_by_genre.get(int(genre), tweet)


func clip_for(genre: Game.Genre) -> String:
	return clip_by_genre.get(int(genre), clip)


func param(name: StringName, default: float) -> float:
	return float(params.get(name, default))


## Подходит ли баг под провал этой мини-игры: аспект к аспекту, жанр к жанру, технология к
## технологии.
func matches(def: MinigameDef) -> bool:
	match def.kind:
		MinigameDef.Kind.ASPECT:
			return kind == Kind.ASPECT and aspect == def.aspect
		MinigameDef.Kind.GENRE:
			return kind == Kind.GENRE and genre == def.genre
		MinigameDef.Kind.TECH:
			return kind == Kind.TECH and tech == def.tech
	return false


func owner_name() -> String:
	match kind:
		Kind.ASPECT:
			return Game.aspect_name(aspect)
		Kind.GENRE:
			return Game.genre_name(genre)
		Kind.TECH:
			return Game.tech_name(tech)
	return ""
