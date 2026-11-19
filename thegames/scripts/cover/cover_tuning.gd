class_name CoverTuning
extends Resource
## Числа обложки коробки (`docs/specs/cover.md`): палитра, размеры коробки и лица, пределы
## стикеров и названия, когда снимать кадры плейтеста. Ресурс `res://resources/cover.tres`.

@export_group("Палитра")  # i18n: skip
## Цвета фона, коробки и названия: один набор на всё.
@export var colors: Array[Color] = [
	Color("#F4F1EC"), Color("#1C1B19"), Color("#CB2F43"), Color("#E2622B"),
	Color("#E2B540"), Color("#8DBB3C"), Color("#1A7444"), Color("#00B49B"),
	Color("#78CDD0"), Color("#006EB8"), Color("#1C4286"), Color("#6A4CE0"),
	Color("#C254B8"), Color("#F29CB7"), Color("#8A5A3C"), Color("#8E8E93"),
]

@export_group("Коробка")  # i18n: skip
## Лицо обложки в пикселях своего вьюпорта; коробка в метрах это лицо, делённое на `px_per_unit`.
@export var face_px := Vector2i(532, 760)
@export var px_per_unit := 400.0
## Поле пластика вокруг вкладыша и толщина коробки, метры.
@export var case_border := 0.035
@export var case_depth := 0.16
@export var camera_distance := 6.7
@export var camera_fov := 24.0
## Наклон коробки в покое и покачивание, чтобы блик и фольга жили.
@export var rest_yaw := 0.42
@export var rest_pitch := 0.1
@export var sway_yaw := 0.11
@export var sway_pitch := 0.035
@export var sway_seconds := 5.0
@export var turn_seconds := 0.45
## Радиан на пиксель экрана при вращении мышью и предел наклона.
@export var drag_speed := 0.008
@export var pitch_limit := 0.6

@export_group("Предметы")  # i18n: skip
@export var max_stickers := 12
## Длинная сторона стикера при размере 1, в долях ширины лица.
@export var sticker_base := 0.3
@export var size_min := 0.4
@export var size_max := 3.0
@export var size_step := 0.1
@export var rot_step := 7.5
@export var move_step := 0.02
## Кегль названия при размере 1, пиксели лица.
@export var title_px := 64
@export var title_size_min := 0.5
@export var title_size_max := 2.0

@export_group("Кадры")  # i18n: skip
## Секунды плейтеста, на которых снимаются кадры для оборота (первый он же кадр галереи).
@export var shot_seconds: Array[float] = [4.0, 12.0, 22.0, 34.0, 48.0]
## Картинка коробки для галереи и карточки игры.
@export var snapshot_px := Vector2i(480, 540)

const PATH := "res://resources/cover.tres"

static var _loaded: CoverTuning


static func get_default() -> CoverTuning:
	if _loaded == null:
		_loaded = load(PATH) as CoverTuning if ResourceLoader.exists(PATH) else null
		if _loaded == null:
			_loaded = CoverTuning.new()
	return _loaded
