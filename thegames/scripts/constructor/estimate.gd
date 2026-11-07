class_name Estimate
extends RefCounted
## Смета конструктора как чистая функция от тройки, экономики и денег: число спринтов, цена
## спринта, итог, остаток и хватает ли. Скидка «Менеджера» передаётся хозяином.

var sprints := 0
var sprint_price := 0
var total := 0
var remainder := 0
var affordable := false


static func compute(genre: Game.Genre, tech: Game.Tech, setting: Game.Setting, economy: EconomyTuning,
		cash: int, discount := 0.0) -> Estimate:
	var e := Estimate.new()
	e.sprints = economy.sprints(tech)
	e.sprint_price = economy.sprint_price(genre, tech, setting, discount)
	e.total = e.sprints * e.sprint_price
	e.remainder = cash - e.total
	e.affordable = e.remainder >= 0
	return e


## Сколько не хватает, ноль если хватает.
func shortfall() -> int:
	return maxi(-remainder, 0)


func _to_string() -> String:
	return "%d × %d = %d, остаток %d" % [sprints, sprint_price, total, remainder]
