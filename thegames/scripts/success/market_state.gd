class_name MarketState
extends Resource
## Скрытое состояние рынка на забег, спека `docs/specs/success.md`: спрос по жанрам и
## сеттингам, шум синергии по парам, тренд, насыщение, части франшиз, репутация, настрой
## рынка текущего релиза. Создаётся на старте забега; `deterministic` даёт единицы и нули для
## модельных прогонов и автотеста.

@export var demand_genre: Array[float] = []
@export var demand_setting: Array[float] = []
## Ключ `tech * 5 + genre` → множитель 1 ± jitter.
@export var synergy_jitter: Dictionary[int, float] = {}
@export var trend_genre := -1
@export var trend_setting := -1
@export var saturation_genre: Array[float] = []
@export var saturation_setting: Array[float] = []
## Название франшизы → число выпущенных частей.
@export var franchise_parts: Dictionary[String, int] = {}
@export var reputation := 0.0
@export var mood := 1.0


static func create(tuning: SuccessTuning, rng: RandomNumberGenerator, deterministic := false) -> MarketState:
	var m := MarketState.new()
	for g in Game.Genre.size():
		m.demand_genre.append(1.0 if deterministic else rng.randf_range(1.0 - tuning.demand_spread, 1.0 + tuning.demand_spread))
		m.saturation_genre.append(0.0)
	for s in Game.Setting.size():
		m.demand_setting.append(1.0 if deterministic else rng.randf_range(1.0 - tuning.demand_spread, 1.0 + tuning.demand_spread))
		m.saturation_setting.append(0.0)
	for t in Game.Tech.size():
		for g in Game.Genre.size():
			m.synergy_jitter[t * Game.Genre.size() + g] = 1.0 if deterministic else 1.0 + rng.randf_range(-tuning.syn_jitter, tuning.syn_jitter)
	m.mood = 1.0
	if not deterministic:
		m.roll_release(tuning, rng)
	return m


## Перед релизом: настрой рынка и тренд (жанр и сеттинг не те, что в прошлый раз).
func roll_release(tuning: SuccessTuning, rng: RandomNumberGenerator) -> void:
	mood = rng.randf_range(tuning.mood_min, tuning.mood_max)
	var g := rng.randi_range(0, Game.Genre.size() - 1)
	if g == trend_genre:
		g = (g + 1) % Game.Genre.size()
	trend_genre = g
	var s := rng.randi_range(0, Game.Setting.size() - 1)
	if s == trend_setting:
		s = (s + 1) % Game.Setting.size()
	trend_setting = s


func saturation(genre: Game.Genre, setting: Game.Setting) -> float:
	return maxf(saturation_genre[genre], saturation_setting[setting])


## Метка насыщения для конструктора: пусто, «недавно было», «надоело».
func saturation_label(value: float, tuning: SuccessTuning) -> String:
	if value >= tuning.saturation_bored:
		return "надоело"
	if value >= tuning.saturation_recent:
		return "недавно было"
	return ""


func trend_mult(genre: Game.Genre, setting: Game.Setting, tuning: SuccessTuning) -> float:
	var m := 1.0
	if genre == trend_genre:
		m += tuning.sales_trend
	if setting == trend_setting:
		m += tuning.sales_trend
	return m
