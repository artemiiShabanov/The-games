class_name StudioNames
extends Resource
## Слова генератора названий студии и цвета логотипа, ресурс `res://resources/studio_names.tres` (#61):
## прилагательное в трёх родах через «|» (м|ж|ср), существительное с родом через «:»
## (m, f, n) и хвост, пустой хвост тоже вариант. «Ленивый Енот Games», «Сонная Табуретка».
## Свободного ввода нет, R перегенерирует.

const PATH := "res://resources/studio_names.tres"
const GENDERS := ["m", "f", "n"]

@export var adjectives: PackedStringArray = []
@export var nouns: PackedStringArray = []
@export var suffixes: PackedStringArray = []
## Цвета фона логотипа студии (`StudioLogo`).
@export var logo_colors: PackedColorArray = []


static func load_default() -> StudioNames:
	var r := load(PATH) as StudioNames
	return r if r != null else StudioNames.new()


func make(rng: RandomNumberGenerator) -> String:
	if adjectives.is_empty() or nouns.is_empty():
		return "Студия"
	var noun := nouns[rng.randi_range(0, nouns.size() - 1)].split(":")
	var g := maxi(GENDERS.find(noun[1] if noun.size() > 1 else "m"), 0)
	var forms := adjectives[rng.randi_range(0, adjectives.size() - 1)].split("|")
	var adj := forms[mini(g, forms.size() - 1)]
	var tail := suffixes[rng.randi_range(0, suffixes.size() - 1)] if not suffixes.is_empty() else ""
	return ("%s %s %s" % [adj, noun[0], tail]).strip_edges()


## Следующее название, отличное от текущего.
func another(current: String, rng: RandomNumberGenerator) -> String:
	for i in 8:
		var s := make(rng)
		if s != current:
			return s
	return make(rng)
