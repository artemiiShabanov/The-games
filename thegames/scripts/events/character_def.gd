class_name CharacterDef
extends Resource
## Персонаж мета-вставок, спека `docs/specs/meta.md` (#63): имя, роль, издание или фирма,
## акцент и портрет (`Portrait`, #140). Восемь лиц на забег: три критика и три
## стримера из ленты, издатель, инвестор; журналист это первый критик в другой роли
## (`person_id` связывает с `PersonDef` ленты). Ресурсы `res://resources/characters/*.tres`.

@export var id: StringName = &""
@export var name := ""
## Роль в карточке: «Издатель», «Инвестор», «Журналист».
@export var role := ""
## Фирма, издание или канал.
@export var subtitle := ""
## Акцент персонажа: цвет лица на портрете (`tools/portraits.py`) и имени в ленте.
@export var accent := Color("#2F5BFF")
## Персонаж ленты, если это он же (журналист = критик).
@export var person_id: StringName = &""
## Как упомянуть в пилюлях: «по договору с Виктором», «Виктор обидится».
@export var short_name := ""
## Короткое имя в творительном: «по договору с Виктором» (#66).
@export var name_with := ""
## Уходит до конца забега после стольких отказов подряд (ответ с `mood_delta` < 0); 0 никогда.
@export var leaves_after_refusals := 0


## Лист портрета: персонаж ленты, если это он же, иначе свой.
func portrait_id() -> StringName:
	return person_id if person_id != &"" else id


func short() -> String:
	return short_name if short_name != "" else name.get_slice(" ", 0)


func with_name() -> String:
	return name_with if name_with != "" else short()
