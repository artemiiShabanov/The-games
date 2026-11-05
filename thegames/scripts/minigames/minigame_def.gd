class_name MinigameDef
extends Resource
## Описание мини-игры, спека `docs/specs/minigames.md`. Один ресурс на мини-игру в
## `res://resources/minigames/<id>.tres`. Кривые параметров от `t` (сложность 0..1) лежат
## в `params`: мини-игра читает `def.param(&"targets", t, 6.0)`.

enum Kind { ASPECT, TECH, GENRE }

@export var id: StringName
@export var kind: Kind = Kind.ASPECT
## Только для аспектных: чей баг даёт провал.
@export var aspect: Game.Aspect = Game.Aspect.OPTIMIZATION
## Только для жанровых.
@export var genre: Game.Genre = Game.Genre.PLATFORMER
## Только для технологических.
@export var tech: Game.Tech = Game.Tech.ASCII
## Крупно на интро.
@export var verb: String
## Подпись одной строкой под глаголом в первом релизе.
@export var hint: String
## Время мини-игры при t = 0; с `t` не растёт.
@export var time_seconds: float = 20.0
## Сцена мини-игры; пустая, пока мини-игра не сделана (раннер тогда подставляет заглушку).
@export var scene: PackedScene
## Какие действия использует, для значков на интро: `GameInput.LEFT` и т.д.
@export var inputs: Array[StringName] = []
## Кривые параметров от `t`.
@export var params: Dictionary[StringName, Curve] = {}


func param(name: StringName, t: float, default: float) -> float:
	var curve: Curve = params.get(name)
	if curve == null:
		return default
	return curve.sample(clampf(t, 0.0, 1.0))


## Чей значок на интро: аспект, жанр или технология.
func owner_name() -> String:
	match kind:
		Kind.ASPECT:
			return Game.aspect_name(aspect)
		Kind.GENRE:
			return Game.genre_name(genre)
		Kind.TECH:
			return Game.tech_name(tech)
	return ""


func _to_string() -> String:
	return "%s (%s, %s)" % [verb, id, owner_name()]
