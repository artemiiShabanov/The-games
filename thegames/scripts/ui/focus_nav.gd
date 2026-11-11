class_name FocusNav
extends RefCounted
## Стрелки по экрану без сетки (#77): следующий элемент в направлении стрелки, ближайший по
## прямой с штрафом за уход вбок. Экраны с разбросанными кнопками (главный экран забега) держат
## список прямоугольников и спрашивают отсюда, куда перейти.

const SIDE_WEIGHT := 2.5


## Индекс соседа `from` в направлении `dir` среди `rects`; `from`, если там никого.
static func step(rects: Array[Rect2], from: int, dir: Vector2) -> int:
	if from < 0 or from >= rects.size():
		return 0 if not rects.is_empty() else -1
	var c0 := rects[from].get_center()
	var best := from
	var best_score := INF
	for i in rects.size():
		if i == from:
			continue
		var d := rects[i].get_center() - c0
		var along := d.dot(dir)
		if along <= 1.0:
			continue
		var side := absf(d.dot(Vector2(dir.y, -dir.x)))
		var score := along + side * SIDE_WEIGHT
		if score < best_score:
			best_score = score
			best = i
	return best


## Направление стрелки из события или ноль.
static func dir_of(event: InputEvent) -> Vector2:
	if event.is_action_pressed(GameInput.LEFT, true):
		return Vector2.LEFT
	if event.is_action_pressed(GameInput.RIGHT, true):
		return Vector2.RIGHT
	if event.is_action_pressed(GameInput.UP, true):
		return Vector2.UP
	if event.is_action_pressed(GameInput.DOWN, true):
		return Vector2.DOWN
	return Vector2.ZERO
