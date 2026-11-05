class_name SprintPlan
extends RefCounted
## Упорядоченный список мини-игр релиза и остаток переигровок. Строит `SprintPlanner`.

var defs: Array[MinigameDef] = []
var replay_left := 0


func size() -> int:
	return defs.size()


func ids() -> Array[StringName]:
	var out: Array[StringName] = []
	for d in defs:
		out.append(d.id)
	return out


func _to_string() -> String:
	var parts: PackedStringArray = []
	for d in defs:
		parts.append("%s[%s]" % [d.verb, d.owner_name()])
	return " → ".join(parts)
