class_name ThreedTuning
extends Resource
## Настройки картинки «продвинутых» (threed, #118), ресурс `res://resources/demos/threed.tres`:
## то, что от сеттинга не зависит. Свет, небо, туман, цветокоррекция и вода зависят от сеттинга
## и живут в его окружении (`SettingEnv`, #147).

const PATH := "res://resources/demos/threed.tres"

## Тени солнца: дальность и размытие.
@export var shadow_distance := 60.0
@export var shadow_blur := 1.6
## Контровой свет по краю моделей и шероховатость материала.
@export var rim := 0.35
@export var rough := 0.82
## Модели на скелете (#119): сила карты рельефа и размах колыхания ткани, метры.
@export var normal_strength := 1.2
@export var cloth_sway := 0.018
## Качание листьев пальмы (`ThreedScreen.add_palm`): метры на единицу доли качания.
@export var palm_sway := 0.03
## Дорогие эффекты в карточке (во встроенном режиме выключены): затенение в углах, сглаживание.
@export var ssao := true
@export var msaa := true


static func load_default() -> ThreedTuning:
	var t := load(PATH) as ThreedTuning
	return t if t != null else ThreedTuning.new()
