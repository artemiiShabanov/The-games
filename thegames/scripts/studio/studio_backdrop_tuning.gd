class_name StudioBackdropTuning
extends Resource
## Тюнинг пиксельной студии на фоне (#80, `StudioBackdrop`): тона, скорости, занятия
## человечков и их веса (спека `docs/specs/studio.md`, «Чем заняты человечки между делом»).
## Ресурс `resources/studio_backdrop.tres`.

const PATH := "res://resources/studio_backdrop.tres"

@export_group("Вид")
## Доли смешения фона с `studio-ink`: линия, средний тон, светлый тон.
@export var tones := Vector3(0.42, 0.2, 0.08)

@export_group("Человечки")
## Рубашки, кожа, волосы: облик каждого выбирается по месту без случайности. Цвета приглушаются
## к фону на `people_mix`, чтобы под оболочкой оставались тихими.
@export var shirts := PackedColorArray([Color("#5E7FC2"), Color("#6FA581"), Color("#C9775A"),
		Color("#D2A845"), Color("#9479BF"), Color("#5C9DB0")])
@export var skins := PackedColorArray([Color("#F0C9A6"), Color("#D9A27A"), Color("#A8714F")])
@export var hairs := PackedColorArray([Color("#2A2D3E"), Color("#5A3B2C"), Color("#A9773E"), Color("#7D8295")])
@export var people_mix := 0.8
## Менеджер в тёмном пиджаке.
@export var manager_shirt := Color("#3A4566")
## Доли чернил: брюки, глаза.
@export var pants_tone := 0.55
@export var eyes_tone := 0.95

@export_group("Движение")
## Скорость ходьбы, пикселей арта в секунду.
@export var walk_speed := 16.0
## Смена кадра шага, секунды.
@export var step_seconds := 0.2
## Смена кадра печати, секунды; во время спринтов (`busy`) быстрее.
@export var type_seconds := 0.32
@export var type_seconds_busy := 0.14
## Мигание экрана у печатающего, секунды.
@export var screen_seconds := 0.7

@export_group("Занятия")
## Сколько длится печать перед следующим выбором, секунды (спека: 5-20).
@export var type_min := 5.0
@export var type_max := 20.0
## Веса выбора: печатает, потягивается, кофе, к соседу, у доски, спит.
@export var w_type := 5.0
@export var w_stretch := 2.0
@export var w_coffee := 2.0
@export var w_visit := 2.0
@export var w_board := 1.0
@export var w_sleep := 1.0
## Длительности стоянок, секунды.
@export var stretch_seconds := 2.0
@export var coffee_seconds := 2.5
@export var visit_seconds := 4.0
@export var board_seconds := 3.5
@export var sleep_seconds := 9.0
## Спит лицом в стол только с этого релиза (спека: вторая половина забега).
@export var sleep_from_release := 6
## Поставленный мышью стоит и озирается, секунды, потом идёт к своему делу.
@export var drop_seconds := 0.8
## Менеджер стоит у стола, секунды.
@export var manager_stop_seconds := 2.5

@export_group("Реакции")
## «Релиз» (машут) и «вирусно» (прыгают), секунды.
@export var react_seconds := 2.0
## Высота прыжка, пикселей арта, и период.
@export var jump_height := 3.0
@export var jump_seconds := 0.4


static func load_default() -> StudioBackdropTuning:
	var t := load(PATH) as StudioBackdropTuning
	return t if t != null else StudioBackdropTuning.new()
