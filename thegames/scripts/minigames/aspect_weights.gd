class_name AspectWeights
extends Resource
## Веса пяти аспектов для одного жанра или одной технологии (таблица в
## `docs/specs/minigames_catalog.md`). Подресурс `SprintTuning`.

@export var optimization := 1
@export var sound := 1
@export var controls := 1
@export var graphics := 1
@export var balance := 1


func get_weight(a: Game.Aspect) -> int:
	match a:
		Game.Aspect.OPTIMIZATION:
			return optimization
		Game.Aspect.SOUND:
			return sound
		Game.Aspect.CONTROLS:
			return controls
		Game.Aspect.GRAPHICS:
			return graphics
		Game.Aspect.BALANCE:
			return balance
	return 0


static func make(o: int, s: int, c: int, g: int, b: int) -> AspectWeights:
	var w := AspectWeights.new()
	w.optimization = o
	w.sound = s
	w.controls = c
	w.graphics = g
	w.balance = b
	return w
