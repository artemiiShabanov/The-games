class_name ThreedTuning
extends Resource
## Настройки картинки «продвинутых» (threed, #118), ресурс `res://resources/demos/threed.tres`:
## свет, тени и пост-эффекты `ThreedScreen`.

const PATH := "res://resources/demos/threed.tres"

## Солнце: наклон и сторона (ниже, чем у low poly: тени длиннее и читаются), сила, цвет,
## дальность теней и их размытие.
@export var sun_pitch := -38.0
@export var sun_yaw := 58.0
@export var sun_energy := 1.75
@export var sun_color := Color(1.0, 0.95, 0.84)
@export var shadow_distance := 60.0
@export var shadow_blur := 1.6
## Свет неба в тенях.
@export var ambient_energy := 0.28
## Небо: во сколько раз зенит темнее и насыщеннее цвета сеттинга, а горизонт светлее.
@export var sky_top := 0.5
@export var sky_horizon := 1.12
## Туман: плотность и доля воздушной перспективы (даль уходит в цвет неба).
@export var fog_density := 0.0012
@export var fog_aerial := 0.35
## Свечение ярких мест.
@export var glow_intensity := 0.4
@export var glow_bloom := 0.06
@export var glow_threshold := 0.95
## Цветокоррекция: насыщенность, контраст, экспозиция.
@export var saturation := 1.22
@export var contrast := 1.06
@export var exposure := 0.84
## Контровой свет по краю моделей и шероховатость материала.
@export var rim := 0.35
@export var rough := 0.82
## Модели на скелете (#119): сила карты рельефа и размах колыхания ткани, метры.
@export var normal_strength := 1.2
@export var cloth_sway := 0.018
## Дорогие эффекты в карточке (во встроенном режиме выключены): затенение в углах, сглаживание.
## Вода (`ThreedScreen.add_water`): цвет глубины и мелководья, на скольких метрах толщи она
## становится непрозрачной, высота волн (1: до 0,45 м).
## Качание листьев пальмы (`ThreedScreen.add_palm`): метры на единицу доли качания.
@export var palm_sway := 0.03
@export var water_deep := Color(0.02, 0.15, 0.23)
@export var water_shallow := Color(0.13, 0.5, 0.53)
@export var water_clarity := 7.0
@export var water_waves := 1.0
@export var ssao := true
@export var msaa := true


static func load_default() -> ThreedTuning:
	var t := load(PATH) as ThreedTuning
	return t if t != null else ThreedTuning.new()
