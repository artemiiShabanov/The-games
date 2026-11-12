class_name LowpolyFollowCam
extends RefCounted
## Камера за спиной для демок low poly и 3D (#108): висит позади и выше цели, догоняет её с
## подводкой и доворачивает за курсом героя, когда он идёт не на камеру. Демка зовёт `step` в
## шаге мира и `apply` перед кадром; ввод героя переводит в мир через `to_world`. Числа в
## `LowpolyTuning`.

var distance := 6.5
var height := 3.2
var look_height := 1.1
var lag := 7.0
var turn := 2.2
## Курс камеры: 0 смотрит в −Z, плюс поворачивает влево (как `rotation.y`).
var yaw := 0.0
## Точка, за которой камера следит (сглаженная цель), и место самой камеры.
var focus := Vector3.ZERO
var position := Vector3.ZERO
var _started := false


static func make(t: LowpolyTuning) -> LowpolyFollowCam:
	var c := LowpolyFollowCam.new()
	c.distance = t.follow_distance
	c.height = t.follow_height
	c.look_height = t.follow_look_height
	c.lag = t.follow_lag
	c.turn = t.follow_turn
	return c


func forward() -> Vector3:
	return Vector3(-sin(yaw), 0.0, -cos(yaw))


func right() -> Vector3:
	return Vector3(cos(yaw), 0.0, -sin(yaw))


## Ввод стрелок или стика (вверх это −y) в направление в мире относительно камеры.
func to_world(axis: Vector2) -> Vector3:
	return right() * axis.x - forward() * axis.y


## Направление в мире обратно во ввод: для бота.
func to_axis(dir: Vector3) -> Vector2:
	return Vector2(dir.dot(right()), -dir.dot(forward()))


## Шаг: цель `target`, курс героя `heading`; `follow` доворачивать ли камеру за курсом.
func step(dt: float, target: Vector3, heading: float, follow: bool) -> void:
	if not _started:
		_started = true
		focus = target
		yaw = heading
	else:
		focus = focus.lerp(target, 1.0 - exp(-lag * dt))
		if follow:
			yaw = lerp_angle(yaw, heading, 1.0 - exp(-turn * dt))
	position = focus - forward() * distance + Vector3.UP * height


func apply(camera: Camera3D) -> void:
	if not _started:
		return
	var to := focus + Vector3.UP * look_height - position
	if to.length_squared() > 0.0001:
		camera.transform = Transform3D(Basis.looking_at(to.normalized()), position)
