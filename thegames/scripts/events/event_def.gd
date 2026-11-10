class_name EventDef
extends Resource
## Мета-вставка (#63), спека `docs/specs/meta.md`: кто приходит, реплика по настроению,
## варианты. Когда приходит, решает планировщик (#64) по `kind` и `condition`. Реплика с
## подстановками {studio}, {genre}, {setting}, {tech}, {game}, {money} (их даёт
## `Events.resolve`); `line_warm` и `line_cold` для настроения +1 и −1, пустые: `line`.
## Ресурсы `res://resources/events/*.tres`.

enum Kind { RANDOM, ENDING, RESCUE }

@export var id: StringName = &""
@export var title := ""
@export var kind: Kind = Kind.RANDOM
@export var character: CharacterDef
## Ключ условия для планировщика (#64): см. `docs/specs/meta.md`, таблица вставок.
@export var condition: StringName = &""
@export_multiline var line := ""
@export_multiline var line_warm := ""
@export_multiline var line_cold := ""
@export var choices: Array[ChoiceDef] = []
## Не чаще раза в столько релизов (0 без ограничения); у концовки это повтор после отказа.
@export var cooldown := 0
## Один раз за забег.
@export var once := false


func line_for(mood: int) -> String:
	if mood > 0 and line_warm != "":
		return line_warm
	if mood < 0 and line_cold != "":
		return line_cold
	return line
