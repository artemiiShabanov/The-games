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

@export_group("Мышь")
## Взятый человечек поднимается над своей тенью на столько пикселей арта за `lift_seconds`.
@export var lift_height := 6.0
@export var lift_seconds := 0.08
## Отпущенный падает на тень: ускорение, пикселей арта в секунду за секунду; отскакивает
## на `bounce_height` пикселей (один раз, если падал быстрее `bounce_min`); сплющен на `squash_seconds`.
@export var gravity := 900.0
@export var bounce_height := 1.5
@export var bounce_min := 60.0
@export var squash_seconds := 0.09
## Кулер: пузырь всплывает в бутыли, выходит над ней и лопается, секунды.
@export var bubble_seconds := 0.9
## Телевизор: помехи и прокрутка кадра при переключении канала, секунды.
@export var tv_switch_seconds := 0.6
## Часы: нажатие прокручивает сутки вперёд на столько часов за столько секунд.
@export var clock_spin_hours := 3.0
@export var clock_spin_seconds := 0.8

@export_group("День и ночь")
## Полные сутки за окнами, секунды (плейтест 2026-11-11: около пяти минут). Начинаются с
## `start_hour`; время идёт от часов самой студии, без случайности.
@export var day_seconds := 300.0
@export var start_hour := 10.5
## Опорные часы неба и цвета в них: верх неба, полоса у горизонта, общий оттенок студии
## (цвет с прозрачностью поверх всего). Между опорами линейно, 24 равно 0.
@export var sky_hours := PackedFloat32Array([0.0, 4.5, 5.5, 6.5, 8.0, 15.5, 17.5, 19.0, 20.0, 21.5, 24.0])
@export var sky_top := PackedColorArray([Color("#465070"), Color("#465070"), Color("#6E7090"),
		Color("#A9B3C4"), Color("#C4CFDA"), Color("#C4CFDA"), Color("#C9C6BC"), Color("#9D93A7"),
		Color("#626786"), Color("#465070"), Color("#465070")])
@export var sky_low := PackedColorArray([Color("#56607A"), Color("#56607A"), Color("#B4A0A6"),
		Color("#E0CBB4"), Color("#DCE2E4"), Color("#DCE2E4"), Color("#E6CD9E"), Color("#D6A78E"),
		Color("#8C7F93"), Color("#56607A"), Color("#56607A")])
@export var ambient := PackedColorArray([Color(0.118, 0.165, 0.29, 0.11), Color(0.118, 0.165, 0.29, 0.11),
		Color(0.23, 0.23, 0.35, 0.08), Color(0.75, 0.56, 0.44, 0.035), Color(1, 1, 1, 0.0),
		Color(1, 1, 1, 0.0), Color(0.75, 0.54, 0.29, 0.04), Color(0.55, 0.35, 0.35, 0.06),
		Color(0.17, 0.2, 0.32, 0.085), Color(0.118, 0.165, 0.29, 0.11), Color(0.118, 0.165, 0.29, 0.11)])
## Солнце над горизонтом с `sunrise` до `sunset`: свет из окон пятнами на полу.
@export var sunrise := 6.0
@export var sunset := 19.6
## Длина пятна на полу: доля высоты окна над полом в полдень и у горизонта.
@export var shaft_noon := 0.35
@export var shaft_low := 1.7
## Наклон пятна вбок у горизонта, пикселей вбок на пиксель вглубь (утром влево, вечером вправо).
@export var shaft_slant := 0.85
## Цвет света: днём и в золотой час; прозрачность это сила пятна на полу.
@export var light_noon := Color(1.0, 0.96, 0.86, 0.6)
@export var light_golden := Color(0.96, 0.78, 0.5, 0.42)
## Лучи в воздухе от окна к пятну (сеткой через пиксель), когда солнце низко: прозрачность.
@export var beam_alpha := 0.22
## Город за окном: доля смешения низа неба с чернилами; облака, пикселей в секунду.
@export var skyline_tone := 0.28
@export var cloud_speed := 1.2
## Ночью мониторы, лампы и телевизор светятся: прозрачность света поверх оттенка ночи.
@export var glow_alpha := 0.5

@export_group("Реакции")
## «Релиз» (машут) и «вирусно» (прыгают), секунды.
@export var react_seconds := 2.0
## Высота прыжка, пикселей арта, и период.
@export var jump_height := 3.0
@export var jump_seconds := 0.4


static func load_default() -> StudioBackdropTuning:
	var t := load(PATH) as StudioBackdropTuning
	return t if t != null else StudioBackdropTuning.new()
