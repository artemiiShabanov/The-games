class_name EventState
extends RefCounted
## Состояние мета-вставок на забег (#63), спека `docs/specs/meta.md`: когда была последняя,
## сколько раз какая показана, настроения персонажей, флаги и всё, что вставки оставили на
## следующие релизы: ограничения (#66 читает в конструкторе), доли с хвоста (#66, экономика),
## бонусы следующей игре, выбранная концовка (#68). Деньги и репутацию вставки меняют сразу.

## Ограничение следующего релиза: что, какое значение, по чьему договору (`by` в творительном:
## «по договору с Виктором»).
class Restriction:
	var kind: EffectDef.Kind
	var value := 0
	var by := ""

	func _to_string() -> String:
		return "%s=%d (%s)" % [EffectDef.Kind.keys()[kind], value, by]


## Доля с хвоста следующих `games` игр.
class TailShare:
	var share := 0.0
	var games := 1
	var by := ""

	func _to_string() -> String:
		return "%d%% × %d (%s)" % [roundi(share * 100.0), games, by]


class Bonus:
	var stat: EffectDef.Stat
	var value := 0.0

	func _to_string() -> String:
		return "%s %+.1f" % [EffectDef.Stat.keys()[stat], value]


var last_event_release := -100
var shown: Dictionary[StringName, int] = {}
var last_shown: Dictionary[StringName, int] = {}
var moods: Dictionary[StringName, int] = {}
## Отказы подряд по персонажам; ушедшие в `flags` как `left_<id>`.
var refusals: Dictionary[StringName, int] = {}
## Флаг и релиз, когда поставлен.
var flags: Dictionary[StringName, int] = {}
var restrictions: Array[Restriction] = []
var tail_shares: Array[TailShare] = []
var bonuses: Array[Bonus] = []
## Индексы игр забега, чьи хвосты проданы: больше не платят.
var sold_tails: Array[int] = []
var ending: StringName = &""


func mood(character: StringName) -> int:
	return moods.get(character, 0)


func shift_mood(character: StringName, delta: int) -> void:
	moods[character] = clampi(mood(character) + delta, -1, 1)


func left(character: StringName) -> bool:
	return flags.has(StringName("left_" + String(character)))


func mark_shown(id: StringName, release: int) -> void:
	shown[id] = shown.get(id, 0) + 1
	last_shown[id] = release
	last_event_release = release


func _to_string() -> String:
	return "вставок %d, настроения %s, ограничения %s, доли %s, бонусы %s, флаги %s%s" % [
		shown.values().reduce(func(a: int, b: int) -> int: return a + b, 0), moods, restrictions, tail_shares,
		bonuses, flags.keys(), (", концовка " + String(ending)) if ending != &"" else ""]
