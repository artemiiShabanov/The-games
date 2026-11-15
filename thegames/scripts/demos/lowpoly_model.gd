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


## Бег с коленями и локтями (плейтест 2026-11-15, #132): всё ещё угловато, но похоже на бег.
## Нога, идущая вперёд, сильно согнута в колене и разгибается к шагу, задняя чуть согнута;
## руки согнуты в локтях и машут в противофазе, предплечье идущей вперёд руки поднимается выше;
## корпус наклонён вперёд. Вперёд у модели это −Z: плюс у бедра и плеча выносит вперёд, минус
## у голени сгибает колено, плюс у предплечья сгибает локоть.
func run(phase: float, swing := 0.85) -> void:
	var s := sin(phase)
	var c := cos(phase)
	_pitch(&"leg_l", (s * 0.9 + 0.12) * swing)
	_pitch(&"leg_r", (-s * 0.9 + 0.12) * swing)
	_pitch(&"shin_l", -(0.25 + 1.25 * maxf(c, 0.0)) * swing)
	_pitch(&"shin_r", -(0.25 + 1.25 * maxf(-c, 0.0)) * swing)
	_pitch(&"arm_l", -s * 0.95 * swing)
	_pitch(&"arm_r", s * 0.95 * swing)
	_pitch(&"fore_l", (1.1 + 0.5 * maxf(-s, 0.0)) * swing)
	_pitch(&"fore_r", (1.1 + 0.5 * maxf(s, 0.0)) * swing)
	_pitch(&"body", -0.16 * swing)


## Поза в воздухе: на взлёте (`rise` 1) одно колено подтянуто, руки вверх; в падении (`rise` −1)
## ноги почти прямые и чуть врозь, руки в стороны и вниз для равновесия.
func air(rise: float) -> void:
	var up := clampf(rise * 0.5 + 0.5, 0.0, 1.0)
	_pitch(&"leg_l", lerpf(0.25, 1.0, up))
	_pitch(&"shin_l", -lerpf(0.35, 1.5, up))
	_pitch(&"leg_r", lerpf(-0.2, -0.35, up))
	_pitch(&"shin_r", -lerpf(0.3, 0.9, up))
	_pitch(&"arm_l", lerpf(-0.5, 1.3, up))
	_pitch(&"arm_r", lerpf(0.7, -0.7, up))
	_pitch(&"fore_l", lerpf(0.5, 1.0, up))
	_pitch(&"fore_r", lerpf(0.5, 1.2, up))
	_pitch(&"body", lerpf(0.06, -0.1, up))


## Стойка: всё ровно, локти и колени едва согнуты, чтобы фигура не стояла столбом.
func stand() -> void:
	for n: StringName in [&"leg_l", &"leg_r", &"arm_l", &"arm_r", &"body"]:
		_pitch(n, 0.0)
	_pitch(&"shin_l", -0.06)
	_pitch(&"shin_r", -0.06)
	_pitch(&"fore_l", 0.22)
	_pitch(&"fore_r", 0.22)


func _pitch(name: StringName, angle: float) -> void:
	var p := part(name)
	if p != null:
		p.rotation.x = angle


## Белая заливка модели на кадр попадания (отклик удара).
func flash(on: bool) -> void:
	for child in find_children("*", "MeshInstance3D", true, false):
		(child as MeshInstance3D).material_overlay = _flash if on else null
