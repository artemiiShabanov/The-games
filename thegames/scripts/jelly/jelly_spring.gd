class_name JellySpring
extends RefCounted
## Затухающая пружина одного числа к нулю: качание столбика, флажка, точки. `kick` толкает
## скоростью, `pull` тянет к цели силой, `step` двигает.

var value := 0.0
var velocity := 0.0


func kick(v: float) -> void:
	velocity += v


func step(delta: float, stiffness: float, damping: float, target := 0.0) -> void:
	# Полунеявный Эйлер с подшагами: устойчиво при жёстких пружинах.
	var n := 4
	var dt := delta / n
	for i in n:
		velocity += (-stiffness * (value - target) - damping * velocity) * dt
		value += velocity * dt
