class_name Upkeep
extends RefCounted
## Содержание студии за релиз: база плюс надбавка каждой купленной прокачки (спека экономики).
## Надбавки хранятся по id прокачки, чтобы карточка предложения показывала свою до покупки.

var base := 0
var extras: Dictionary[StringName, int] = {}


func _init(base_ := 0) -> void:
	base = base_


func add(id: StringName, amount: int) -> void:
	extras[id] = amount


func total() -> int:
	var sum := base
	for v in extras.values():
		sum += v
	return sum


func _to_string() -> String:
	return "%d" % total()
