class_name RunStats
extends RefCounted
## Итоги забега для концовок и оценка студии, спека `docs/specs/success.md`.

var sequels := 0
var alive_tails := 0
var tail_total := 0
var best_critics := 0.0
var top3_critics := 0.0
var viral_count := 0
var reputation := 0.0
var franchises := 0
var valuation := 0


func _to_string() -> String:
	return "сиквелов %d, живых хвостов %d, тик %d, лучшая C %.1f, топ-3 %.1f, вирусных %d, R %.1f, оценка %d" % [
		sequels, alive_tails, tail_total, best_critics, top3_critics, viral_count, reputation, valuation]
