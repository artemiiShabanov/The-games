class_name Scaler16
extends RefCounted
## Вид вглубь экрана для демок 16/32-bit (#95): камера за спиной героя, земля уходит к
## горизонту, спрайты растут, приближаясь. Мир: `x` поперёк, `z` вперёд от камеры, в пикселях
## мира; на расстоянии `focal` спрайт рисуется один к одному. Земля полосами поперёк, которые
## бегут навстречу (`draw_ground`), по ней можно положить дорогу (`draw_road`). Спрайты
## копятся в `add` и рисуются в `flush` от дальних к ближним.

var view := Vector2(832, 416)
## Горизонт на экране, высота камеры над землёй и фокус, пиксели мира.
var horizon := 170.0
var cam_height := 64.0
var focal := 240.0
## Ближе этого к камере не рисуется.
var near := 28.0

var _queue: Array[Array] = []


static func make(view_: Vector2) -> Scaler16:
	var s := Scaler16.new()
	s.view = view_
	s.horizon = roundf(view_.y * 0.42)
	return s


## Точка земли (`x`, `z`) на экране: x, y и масштаб спрайта.
func project(x: float, z: float) -> Vector3:
	var s := focal / maxf(z, 1.0)
	return Vector3(view.x / 2.0 + x * s, horizon + cam_height * s, s)


## Расстояние `z` до строки экрана `y` ниже горизонта.
func depth_at(y: float) -> float:
	return cam_height * focal / maxf(y - horizon, 0.5)


## Земля полосами: `dist` пройденный путь, полоса длиной `stripe`, два цвета по очереди.
func draw_ground(canvas: CanvasItem, dist: float, a: Color, b: Color, stripe := 120.0) -> void:
	var y := horizon
	var run_from := y
	var run_band := -1
	while y < view.y:
		var band := int(floor((depth_at(y + 0.5) + dist) / stripe)) & 1
		if band != run_band:
			if run_band >= 0:
				canvas.draw_rect(Rect2(0, run_from, view.x, y - run_from), a if run_band == 0 else b)
			run_from = y
			run_band = band
		y += 1.0
	canvas.draw_rect(Rect2(0, run_from, view.x, view.y - run_from), a if run_band == 0 else b)


## Дорога шириной `half_width` в обе стороны от `center_x` мира: полотно, бордюр в полоску и
## пунктир по `lanes` полосам.
func draw_road(canvas: CanvasItem, dist: float, center_x: float, half_width: float, road: Color, curb_a: Color,
		curb_b: Color, mark: Color, lanes := 1, stripe := 120.0) -> void:
	var y := horizon + 1.0
	while y < view.y:
		var z := depth_at(y + 0.5)
		var s := focal / z
		var cx := view.x / 2.0 + center_x * s
		var hw := half_width * s
		var band := int(floor((z + dist) / (stripe / 2.0))) & 1
		var curb := maxf(half_width * 0.07 * s, 1.0)
		canvas.draw_rect(Rect2(cx - hw - curb, y, 2.0 * (hw + curb), 1.0), curb_a if band == 0 else curb_b)
		canvas.draw_rect(Rect2(cx - hw, y, 2.0 * hw, 1.0), road)
		if band == 0:
			for l in range(1, lanes):
				var lx := cx - hw + 2.0 * hw * l / lanes
				canvas.draw_rect(Rect2(lx - maxf(s, 0.5), y, maxf(2.0 * s, 1.0), 1.0), mark)
		y += 1.0


## Спрайт на земле в точке (`x`, `z`): уйдёт в очередь и нарисуется в `flush`. `pink` заглушка.
func add(tex: Texture2D, frame: int, x: float, z: float, flip := false, pink := false, lift := 0.0) -> void:
	if z < near:
		return
	_queue.append([z, tex, frame, x, flip, pink, lift])


## Нарисовать очередь от дальних к ближним.
func flush(screen: Bit16Screen, canvas: CanvasItem) -> void:
	_queue.sort_custom(func(p: Array, q: Array) -> bool: return float(p[0]) > float(q[0]))
	for it in _queue:
		var p := project(float(it[3]), float(it[0]))
		var feet := Vector2(p.x, p.y - float(it[6]) * p.z)
		if feet.x < -200.0 or feet.x > view.x + 200.0:
			continue
		if bool(it[5]):
			screen.pink(canvas, feet, p.z)
		else:
			screen.sprite(canvas, it[1], int(it[2]), feet, bool(it[4]), p.z)
	_queue.clear()
