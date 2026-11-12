class_name LowpolyFirstPerson
extends RefCounted
## Вид от первого лица для демок low poly и 3D (#108): место ног, курс и наклон взгляда. Обзор
## стрелками через `turn`; мышь и правый стик (#109) приходят через `look_by`. Ход считает
## демка: `wish` даёт направление в мире из бега и стрейфа, столкновения её дело. Числа в
## `LowpolyTuning`.

var eye_height := 1.5
var look_speed := 2.4
var pitch_limit := 1.2
## Ноги игрока в мире.
var position := Vector3.ZERO
## Курс: 0 смотрит в −Z, плюс поворачивает влево (как `rotation.y`).
var yaw := 0.0
var pitch := 0.0


static func make(t: LowpolyTuning) -> LowpolyFirstPerson:
	var p := LowpolyFirstPerson.new()
	p.eye_height = t.eye_height
	p.look_speed = t.look_speed
	p.pitch_limit = t.pitch_limit
	return p


func forward() -> Vector3:
	return Vector3(-sin(yaw), 0.0, -cos(yaw))


func right() -> Vector3:
	return Vector3(cos(yaw), 0.0, -sin(yaw))


## Обзор стрелками: `look` −1 влево, 1 вправо.
func turn(look: float, dt: float) -> void:
	yaw = wrapf(yaw - look * look_speed * dt, -PI, PI)


## Обзор мышью или стиком: смещение в радианах, вправо и вниз плюс.
func look_by(delta: Vector2) -> void:
	yaw = wrapf(yaw - delta.x, -PI, PI)
	pitch = clampf(pitch - delta.y, -pitch_limit, pitch_limit)


## Направление хода в мире: `walk.x` стрейф вправо, `walk.y` вперёд.
func wish(walk: Vector2) -> Vector3:
	return right() * walk.x + forward() * walk.y


## Угол, на который надо повернуть вправо (плюс) или влево (минус), чтобы смотреть на точку.
func bearing_to(point: Vector3) -> float:
	var to := point - position
	return wrapf(yaw - atan2(-to.x, -to.z), -PI, PI)


func apply(camera: Camera3D) -> void:
	camera.transform = Transform3D(Basis.from_euler(Vector3(pitch, yaw, 0.0)), position + Vector3.UP * eye_height)
