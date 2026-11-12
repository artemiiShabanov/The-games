class_name LookTuning
extends Resource
## Числа обзора от первого лица мышью и правым стиком (#109), `res://resources/look.tres`.
## Ползунок настроек 0..1 (`Options.mouse_look`, `Options.stick_look`) выбирает скорость между
## «min» и «max», середина это умолчание.

const PATH := "res://resources/look.tres"

## Поворот на пиксель движения мыши, радианы: на нуле и на единице ползунка.
@export var mouse_min := 0.0008
@export var mouse_max := 0.0052
## Скорость поворота правым стиком до упора, рад/с: на нуле и на единице ползунка.
@export var stick_min := 1.2
@export var stick_max := 4.8
## Наклон стиком медленнее поворота во столько раз.
@export var stick_pitch := 0.6
## Мёртвая зона правого стика.
@export var stick_deadzone := 0.2

static var _default: LookTuning


static func load_default() -> LookTuning:
	if _default == null:
		_default = load(PATH) as LookTuning if ResourceLoader.exists(PATH) else LookTuning.new()
	return _default


## Радианы на пиксель при положении ползунка `v`.
func mouse_speed(v: float) -> float:
	return lerpf(mouse_min, mouse_max, clampf(v, 0.0, 1.0))


## Рад/с при положении ползунка `v`.
func stick_speed(v: float) -> float:
	return lerpf(stick_min, stick_max, clampf(v, 0.0, 1.0))
