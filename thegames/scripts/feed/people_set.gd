class_name PeopleSet
extends Resource
## Набор персонажей одной роли, ресурсы `res://resources/people/critics.tres` и
## `streamers.tres`. Порядок это порядок карточек в ленте.

const DIR := "res://resources/people/"

@export var people: Array[PersonDef] = []


static func load_critics() -> PeopleSet:
	var p := load(DIR + "critics.tres") as PeopleSet
	return p if p != null else PeopleSet.new()


static func load_streamers() -> PeopleSet:
	var p := load(DIR + "streamers.tres") as PeopleSet
	return p if p != null else PeopleSet.new()
