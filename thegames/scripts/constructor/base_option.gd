class_name BaseOption
extends RefCounted
## Основа следующей игры (#24): новая игра, сиквел или ремейк прошлой игры забега. Строит
## `BaseOption.list`: ремейк закрыт для ремейка и когда нет другой открытой технологии.
## Название задано основой: «Пираты на платформах 2» (номер растёт у сиквела сиквела),
## «Пираты на платформах: ремейк».

var kind: GameConfig.Kind = GameConfig.Kind.NEW
var parent: GameRecord
var open := true
## Почему закрыта: пилюля на карточке.
var lock_reason := ""


static func fresh() -> BaseOption:
	return BaseOption.new()


static func sequel_of(p: GameRecord) -> BaseOption:
	var o := BaseOption.new()
	o.kind = GameConfig.Kind.SEQUEL
	o.parent = p
	return o


static func remake_of(p: GameRecord, unlocked_techs: Array[Game.Tech]) -> BaseOption:
	var o := BaseOption.new()
	o.kind = GameConfig.Kind.REMAKE
	o.parent = p
	var other := false
	for t in unlocked_techs:
		if t != p.tech:
			other = true
	if p.remake:
		o.open = false
		o.lock_reason = "ремейк ремейка нельзя"
	elif not other:
		o.open = false
		o.lock_reason = "нужна вторая технология"
	return o


## Основы одного вида по прошлым играм от последней к первой.
static func list(kind_: GameConfig.Kind, past: Array[GameRecord], unlocked_techs: Array[Game.Tech]) -> Array[BaseOption]:
	var out: Array[BaseOption] = []
	if kind_ == GameConfig.Kind.NEW:
		out.append(fresh())
		return out
	for k in range(past.size() - 1, -1, -1):
		out.append(sequel_of(past[k]) if kind_ == GameConfig.Kind.SEQUEL else remake_of(past[k], unlocked_techs))
	return out


func is_franchise() -> bool:
	return kind != GameConfig.Kind.NEW and parent != null


func title() -> String:
	match kind:
		GameConfig.Kind.SEQUEL:
			return "%s %d" % [parent.franchise_title(), parent.part + 1]
		GameConfig.Kind.REMAKE:
			return "%s: ремейк" % parent.title
	return ""


func kind_name() -> String:
	return ["новая игра", "сиквел", "ремейк"][kind]


func _to_string() -> String:
	return kind_name() + (" " + parent.title if parent != null else "")
