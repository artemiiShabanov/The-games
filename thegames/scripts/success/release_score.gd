class_name ReleaseScore
extends Resource
## Отклик на релиз, спека `docs/specs/success.md`: критики, первый тик продаж, охват
## стримеров, вирусность, параметры хвоста и сколько тиков уже выплачено. Хранится в записи
## игры (`GameRecord.score`), чтобы хвосты тикали между релизами и сохранялись с забегом.

@export var critics := 0.0
@export var sales_first := 0
@export var streamers := 0
@export var viral := false
@export var novelty := 0.0
@export var synergy := 1.0
@export var quality := 0.0
@export var bugs := 0
@export var spectacular_bugs := 0
## Распад хвоста: тик i = sales_first · tail_decay^i.
@export var tail_decay := 0.5
@export var tail_ticks := 0
@export var last_tick := 0
@export var tail_alive := true


## Слово стримеров по порогам спеки.
func streamers_word(tuning: SuccessTuning) -> String:
	if viral:
		return "вирусно"
	return "заметили" if streamers >= tuning.noticed_threshold else "тихо"


func _to_string() -> String:
	return "C %.1f, P0 %d, V %d%s, d %.2f" % [critics, sales_first, streamers, "*" if viral else "", tail_decay]
