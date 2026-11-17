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
## Кто приходит, если `character` ушёл (скандал: издатель или инвестор).
@export var alt_character: CharacterDef
## Ключ условия для планировщика (#64): см. `docs/specs/meta.md`, таблица вставок.
@export var condition: StringName = &""
@export_multiline var line := ""
@export_multiline var line_warm := ""
@export_multiline var line_cold := ""
## Ещё варианты той же реплики (#141): вставка приходит не раз за забег и не должна повторяться
## слово в слово. Вариант выбирается по числу выпущенных игр.
@export var lines_alt: PackedStringArray = []
@export var lines_warm_alt: PackedStringArray = []
@export var lines_cold_alt: PackedStringArray = []
@export var choices: Array[ChoiceDef] = []
## Не чаще раза в столько релизов (0 без ограничения); у концовки это повтор после отказа.
@export var cooldown := 0
## Один раз за забег.
@export var once := false
## Среди концовок с выполненным условием приходит та, у кого больше (легенда, корпорация, продажа).
@export var priority := 0


func line_for(mood: int, turn := 0) -> String:
	var pool: PackedStringArray = [line]
	pool.append_array(lines_alt)
	if mood > 0 and line_warm != "":
		pool = [line_warm]
		pool.append_array(lines_warm_alt)
	elif mood < 0 and line_cold != "":
		pool = [line_cold]
		pool.append_array(lines_cold_alt)
	return pool[posmod(turn, pool.size())]
