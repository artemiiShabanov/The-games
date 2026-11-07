class_name EconomyTuning
extends Resource
## Числа экономики, ресурс `res://resources/economy.tres`, спека `docs/specs/economy.md`,
## значения из `economy_model.md` и `tools/model_run.py`. Расчёты здесь чистые функции от
## тюнинга: цена спринта, стоимость релиза, самый дешёвый релиз, порог банкротства.
## Индексы массивов это `Game.Tech`, `Game.Genre`, `Game.Setting`.

const PATH := "res://resources/economy.tres"

@export var start_cash := 36000
@export var upkeep_base := 800
@export var sprints_by_tech: Array[int] = [4, 5, 6, 7, 8]
@export var sprint_base_by_tech: Array[int] = [1000, 1400, 1900, 2500, 3200]
@export var genre_cost_mult: Array[float] = [1.0, 1.1, 1.05, 1.0, 1.15]
@export var setting_cost_mult: Array[float] = [1.0, 1.1, 1.05]
@export var unlock_price_by_tech: Array[int] = [3000, 5000, 8000, 12000, 18000]
@export var unlock_upkeep_by_tech: Array[int] = [300, 400, 500, 700, 900]
@export var genre_unlock_price := 7000
@export var genre_unlock_upkeep := 250
## Возможности из спеки студии: id → цена и надбавка к содержанию.
@export var capability_prices: Dictionary[StringName, int] = {}
@export var capability_upkeeps: Dictionary[StringName, int] = {}
@export var rescue_amount := 12000
## Спринт багфикса стоит обычный спринт × это.
@export var bugfix_price_mult := 1.0
## Скидка «Менеджера» на цену спринта.
@export var manager_discount := 0.1


static func load_default() -> EconomyTuning:
	var t := load(PATH) as EconomyTuning
	return t if t != null else EconomyTuning.new()


## Число спринтов релиза задаёт технология.
func sprints(tech: Game.Tech) -> int:
	return sprints_by_tech[tech]


## Цена спринта = база технологии × множитель жанра × множитель сеттинга × (1 − скидка),
## округлённая до 10.
func sprint_price(genre: Game.Genre, tech: Game.Tech, setting: Game.Setting, discount := 0.0) -> int:
	var raw := sprint_base_by_tech[tech] * genre_cost_mult[genre] * setting_cost_mult[setting] * (1.0 - discount)
	return int(roundf(raw / 10.0)) * 10


## Стоимость релиза = спринты × цена спринта; списывается целиком при старте разработки.
func release_cost(genre: Game.Genre, tech: Game.Tech, setting: Game.Setting, discount := 0.0) -> int:
	return sprints(tech) * sprint_price(genre, tech, setting, discount)


func bugfix_price(genre: Game.Genre, tech: Game.Tech, setting: Game.Setting, discount := 0.0) -> int:
	return int(roundf(sprint_price(genre, tech, setting, discount) * bugfix_price_mult / 10.0)) * 10


## Самый дешёвый релиз из открытых жанров, технологий и сеттингов.
func cheapest_release(genres: Array[Game.Genre], techs: Array[Game.Tech], settings: Array[Game.Setting], discount := 0.0) -> int:
	var best := -1
	for g in genres:
		for t in techs:
			for s in settings:
				var c := release_cost(g, t, s, discount)
				if best < 0 or c < best:
					best = c
	return best


## Банкротство: после содержания денег меньше, чем стоит самый дешёвый открытый релиз.
## Минус считается тем же условием.
func is_bankrupt(cash: int, cheapest: int) -> bool:
	return cash < cheapest


func capability_price(id: StringName) -> int:
	return capability_prices.get(id, 0)


func capability_upkeep(id: StringName) -> int:
	return capability_upkeeps.get(id, 0)
