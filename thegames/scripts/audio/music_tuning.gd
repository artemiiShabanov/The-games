class_name MusicTuning
extends Resource
## Настройки музыки (#87), ресурс `res://resources/music.tres`. Тема игры это мелодия сеттинга
## в аранжировке технологии, жанр даёт темп и рисунок ударных.

const PATH := "res://resources/music.tres"

## Скорость проигрывания по жанру (`Game.Genre`): темп, вместе с ним чуть сдвигается высота.
## Те же числа в `tools/music.py` (`GENRES`).
@export var genre_rate: Array[float] = [1.0, 1.12, 1.06, 0.92, 1.04]
## Громкость темы последней игры на главном экране забега, дБ.
@export var hub_db := -24.0
## Громкость темы под клипом стримера в ленте, дБ.
@export var feed_db := -16.0
## Плавное появление и уход темы на главном экране, секунды.
@export var hub_fade := 1.5
