class_name Jelly
extends RefCounted
## Прототип желе (ветка proto/jelly): общий выключатель и тюнинг. Системы спрашивают
## `Jelly.on()` и рисуют по-старому, если желе выключено, чтобы сравнивать. Ручки живут в
## разделе «Желе» дебаг-меню; `register_debug` зовёт сцена, которая желе использует.

const SECTION: StringName = &"Желе"
const MATERIALS: Array[String] = ["мармелад", "желе"]
const PATHS: Array[String] = ["res://resources/jelly.tres", "res://resources/jelly_soft.tres"]

static var enabled := true
static var material := 0
static var _tunings: Array[JellyTuning] = []


static func on() -> bool:
	return enabled


static func tuning() -> JellyTuning:
	if _tunings.is_empty():
		for path in PATHS:
			var tu := load(path) as JellyTuning
			_tunings.append(tu if tu != null else JellyTuning.new())
	return _tunings[clampi(material, 0, _tunings.size() - 1)]


static func register_debug() -> void:
	Debug.clear_section(SECTION)
	Debug.add_toggle(SECTION, "Желе включено", func() -> bool: return enabled,
			func(v: bool) -> void: enabled = v, true)
	Debug.add_choice(SECTION, "Материал (ручки ниже от него)", MATERIALS,
			func() -> String: return MATERIALS[material],
			func(v: String) -> void: material = maxi(MATERIALS.find(v), 0), true)
	var tu := tuning()
	_num("Жёсткость тела", tu, &"blob_stiffness", 100.0, 1200.0, 20.0)
	_num("Затухание тела", tu, &"blob_damping", 1.0, 30.0, 1.0)
	_num("Давление", tu, &"blob_pressure", 0.0, 4000.0, 100.0)
	_num("Инерция шлепка", tu, &"blob_inertia", 0.0, 1.0, 0.05)
	_num("Тяжесть", tu, &"blob_gravity", 0.0, 6000.0, 200.0)
	_num("Вытягивание", tu, &"blob_stretch", 0.0, 0.0012, 0.00005)
	_num("Брызги", tu, &"splash_scale", 0.0, 3.0, 0.1)
	_num("Волна поверхности", tu, &"ripple_amp", 0.0, 30.0, 1.0)
	_num("Жёсткость предметов", tu, &"spring_stiffness", 60.0, 900.0, 20.0)


static func _num(label: String, _tu: JellyTuning, prop: StringName, lo: float, hi: float, step: float) -> void:
	# Ручка правит текущий материал, а не тот, что был при регистрации.
	Debug.add_number(SECTION, label, func() -> float: return float(tuning().get(prop)),
			func(v: float) -> void: tuning().set(prop, v), lo, hi, step)
