class_name CatalogEntry
extends Resource
## Карточка каталога конструктора: жанр, технология или сеттинг. `value` это значение своего
## перечисления `Game.Genre` / `Game.Tech` / `Game.Setting`. Цвет фона карточки и теги для
## генератора названий. Иллюстрации карточек приходят в M5, пока крупная буква.

enum Kind { GENRE, TECH, SETTING }

@export var kind: Kind = Kind.GENRE
@export var value := 0
@export var id: StringName = &""
@export var title := ""
@export var color := Color.WHITE
## Для генератора названий: у сеттинга существительные, у жанра хвосты «на платформах».
@export var title_tags: Array[String] = []
