class_name LowpolyModel
extends Node3D
## Модель слота в сцене low poly (#108): части `LowpolyModelDef` узлами в своих точках вращения.
## Анимация без скелета: демка крутит части (`part`, `walk`). Розовая заглушка это та же
## модель без частей с розовым ящиком в шашку по габаритам (`pink`). Создаёт
## `LowpolyScreen.model` и `LowpolyScreen.pink_model`.

var def: LowpolyModelDef
var parts: Dictionary[StringName, MeshInstance3D] = {}
## Розовая заглушка вместо меша (`pink_placeholders`).
var pink := false
var _flash: Material


func part(name: StringName) -> MeshInstance3D:
	return parts.get(name)


## Шаг двуногого: ноги и руки качаются в противофазе; `swing` размах в радианах, 0 ставит ровно.
## У модели с коленями и локтями (`shin_*`, `fore_*`) нога, идущая вперёд, согнута в колене, а
## руки согнуты в локтях.
func walk(phase: float, swing := 0.7) -> void:
	var s := sin(phase) * swing
	var lift := cos(phase)
	_pitch(&"leg_l", s)
	_pitch(&"leg_r", -s)
	_pitch(&"arm_l", -s * 0.8)
	_pitch(&"arm_r", s * 0.8)
	_pitch(&"shin_l", -maxf(lift, 0.0) * swing * 1.3)
	_pitch(&"shin_r", -maxf(-lift, 0.0) * swing * 1.3)
	var bend := minf(swing / 0.5, 1.0) * 0.45
	_pitch(&"fore_l", bend)
	_pitch(&"fore_r", bend)


func _pitch(name: StringName, angle: float) -> void:
	var p := part(name)
	if p != null:
		p.rotation.x = angle


## Белая заливка модели на кадр попадания (отклик удара).
func flash(on: bool) -> void:
	for child in find_children("*", "MeshInstance3D", true, false):
		(child as MeshInstance3D).material_overlay = _flash if on else null
