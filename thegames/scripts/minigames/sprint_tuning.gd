class_name SprintTuning
extends Resource
## Тюнинг спринтов: длительности карточек, множитель первого релиза, веса аспектов по
## жанрам и технологиям. Ресурс `res://resources/sprints.tres`.

@export var intro_seconds := 1.0
## Вдох после мини-игры перед следующим интро (2026-11-18: цепочка без карточки результата и
## без паузы на студию).
@export var result_seconds := 0.4
## Пауза на студию после последнего спринта, перед плейтестом.
@export var studio_seconds := 1.0
## Исход спринта по счёту мини-игры (2026-11-18): от `clean_score` и выше бага нет, до
## `bug_score` и ниже баг точно, между ними шанс бага падает линейно.
@export var clean_score := 0.95
@export var bug_score := 0.45
## Цена ошибки в шансе бага (2026-11-19): до порога мини-игры каждая ошибка добавляет
## `mistake_soft`, каждая следующая за порогом `mistake_hard`.
@export var mistake_soft := 0.06
@export var mistake_hard := 0.45
## Шанс бага × это, индекс = `Game.Tech` (2026-11-20): набор мини-игр у всех технологий
## одинаковый, поэтому простая технология прощает больше: примитив в полтора раза реже даёт баг,
## чем «продвинутые», между ними лесенка.
@export var bug_mult_by_tech: Array[float] = [0.667, 0.75, 0.833, 0.917, 1.0]
## Темп цепочки: каждый следующий спринт релиза сложнее на столько (`t`, до 1).
@export var chain_t_step := 0.03
## Время мини-игр в первом релизе × это.
@export var first_release_time_multiplier := 1.5
## Индекс = `Game.Genre`.
@export var genre_weights: Array[AspectWeights] = []
## Индекс = `Game.Tech`.
@export var tech_weights: Array[AspectWeights] = []


## Шанс бага по счёту мини-игры 0..1; `mult` это множитель технологии (`bug_mult`).
func bug_chance(score: float, mult := 1.0) -> float:
	if clean_score <= bug_score:
		return 0.0 if score >= clean_score else mult
	return clampf((clean_score - score) / (clean_score - bug_score), 0.0, 1.0) * mult


## Множитель шанса бага технологии; без записи в таблице 1.
func bug_mult(tech: Game.Tech) -> float:
	return bug_mult_by_tech[tech] if tech < bug_mult_by_tech.size() else 1.0


## Сколько счёта снимают `n` ошибок мини-игры с порогом `grace`: столько, чтобы шанс бага
## вышел `mistake_soft` за ошибку до порога и `mistake_hard` за каждую после.
func mistake_loss(n: int, grace: int) -> float:
	if n <= 0:
		return 0.0
	var chance := mistake_soft * mini(n, grace) + mistake_hard * maxi(n - grace, 0)
	return (1.0 - clean_score) + chance * (clean_score - bug_score)


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
