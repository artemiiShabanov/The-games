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
## Крупно на штампе карточки результата: «15 FPS», «СКВОЗЬ ПОЛ».
@export var stamp: String
## Проявление в демке, одной строкой: для карточки результата и ленты.
@export var manifestation: String
## Текст твита в ленте отклика.
@export var tweet: String
## Кадр для клипа стримера: что видно на стоп-кадре.
@export var clip: String
## Зрелищный баг: чаще попадает в клипы и даёт вирусность.
@export var spectacular := false
## Параметры проявления: демка читает `param(&"freeze_ms_max", 400.0)`.
@export var params: Dictionary[StringName, float] = {}


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
