class_name SprintTuning
extends Resource
## Тюнинг спринтов: длительности карточек, множитель первого релиза, веса аспектов по
## жанрам и технологиям. Ресурс `res://resources/sprints.tres`.

@export var intro_seconds := 1.0
@export var result_seconds := 1.0
@export var studio_seconds := 2.5
## Время мини-игр в первом релизе × это.
@export var first_release_time_multiplier := 1.5
## Индекс = `Game.Genre`.
@export var genre_weights: Array[AspectWeights] = []
## Индекс = `Game.Tech`.
@export var tech_weights: Array[AspectWeights] = []


## Сумма весов пары для аспекта.
func weight(genre: Game.Genre, tech: Game.Tech, aspect: Game.Aspect) -> int:
	var w := 0
	if genre < genre_weights.size() and genre_weights[genre] != null:
		w += genre_weights[genre].get_weight(aspect)
	if tech < tech_weights.size() and tech_weights[tech] != null:
		w += tech_weights[tech].get_weight(aspect)
	return w


## Аспекты по убыванию веса пары; при равенстве порядок `Game.Aspect`.
func aspects_by_weight(genre: Game.Genre, tech: Game.Tech) -> Array[Game.Aspect]:
	var out: Array[Game.Aspect] = []
	for a in Game.Aspect.values():
		out.append(a)
	var weights := {}
	for a in out:
		weights[a] = weight(genre, tech, a)
	out.sort_custom(func(x: Game.Aspect, y: Game.Aspect) -> bool:
		if weights[x] != weights[y]:
			return weights[x] > weights[y]
		return x < y)
	return out
