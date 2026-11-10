class_name ChoiceDef
extends Resource
## Вариант ответа мета-вставки (#63): текст кнопки, последствия, сдвиг настроения персонажа.
## Монетка: с `coin` последствия `effects` выпадают с шансом `MetaTuning.coin_chance`, иначе
## `lose_effects`; на карточке пилюля «монетка» и обе ветки через «или».

@export var text := ""
@export var effects: Array[EffectDef] = []
@export var coin := false
@export var lose_effects: Array[EffectDef] = []
## −1, 0, +1: настроение персонажа после ответа (пилюля «Виктор обидится» / «доволен»).
@export var mood_delta := 0
