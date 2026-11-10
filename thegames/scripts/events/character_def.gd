class_name CharacterDef
extends Resource
## Персонаж мета-вставок, спека `docs/specs/meta.md` (#63): имя, роль, издание или фирма,
## акцент пиксельного лица (`PixelFace` ленты, портреты в M5). Восемь лиц на забег: три критика и три
## стримера из ленты, издатель, инвестор; журналист это первый критик в другой роли
## (`person_id` связывает с `PersonDef` ленты). Ресурсы `res://resources/characters/*.tres`.

@export var id: StringName = &""
@export var name := ""
## Роль в карточке: «Издатель», «Инвестор», «Журналист».
@export var role := ""
## Фирма, издание или канал.
@export var subtitle := ""
## Акцент пиксельного лица (`PixelFace` из ленты до портретов M5).
@export var accent := Color("#2F5BFF")
## Персонаж ленты, если это он же (журналист = критик).
@export var person_id: StringName = &""
## Как упомянуть в пилюлях: «по договору с Виктором», «Виктор обидится».
@export var short_name := ""
## Уходит до конца забега после стольких отказов подряд (ответ с `mood_delta` < 0); 0 никогда.
@export var leaves_after_refusals := 0


func short() -> String:
	return short_name if short_name != "" else name.get_slice(" ", 0)
