class_name Jelly
extends RefCounted
## Прототип желе (ветка proto/jelly): общий выключатель и тюнинг. Системы спрашивают
## `Jelly.on()` и рисуют по-старому, если желе выключено, чтобы сравнивать. Ручки живут в
## разделе «Желе» дебаг-меню; `register_debug` зовёт сцена, которая желе использует.

const SECTION: StringName = &"Желе"
const PATH := "res://resources/jelly.tres"

static var enabled := true
static var _tuning: JellyTuning


static func on() -> bool:
	return enabled


static func tuning() -> JellyTuning:
	if _tuning == null:
		_tuning = load(PATH) as JellyTuning
		if _tuning == null:
			_tuning = JellyTuning.new()
	return _tuning


static func register_debug() -> void:
	Debug.clear_section(SECTION)
	var tu := tuning()
	Debug.add_toggle(SECTION, "Желе включено", func() -> bool: return enabled,
			func(v: bool) -> void: enabled = v, true)
	_num("Жёсткость тела", tu, &"blob_stiffness", 100.0, 1200.0, 20.0)
	_num("Затухание тела", tu, &"blob_damping", 1.0, 30.0, 1.0)
	_num("Давление", tu, &"blob_pressure", 0.0, 4000.0, 100.0)
	_num("Инерция шлепка", tu, &"blob_inertia", 0.0, 1.0, 0.05)
	_num("Тяжесть", tu, &"blob_gravity", 0.0, 6000.0, 200.0)
	_num("Вытягивание", tu, &"blob_stretch", 0.0, 0.0012, 0.00005)
	_num("Брызги", tu, &"splash_scale", 0.0, 3.0, 0.1)
	_num("Волна поверхности", tu, &"ripple_amp", 0.0, 30.0, 1.0)
	_num("Жёсткость предметов", tu, &"spring_stiffness", 60.0, 900.0, 20.0)


static func _num(label: String, tu: JellyTuning, prop: StringName, lo: float, hi: float, step: float) -> void:
	Debug.add_number(SECTION, label, func() -> float: return float(tu.get(prop)),
			func(v: float) -> void: tu.set(prop, v), lo, hi, step)
