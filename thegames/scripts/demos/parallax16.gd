class_name Parallax16
extends RefCounted
## Вид сбоку для демок 16/32-bit (#95): фон в три слоя, которые едут медленнее мира. Небо
## градиентом из палитры с полосами перехода, на нём облака (`par_sky`), на горизонте дальний
## берег (`par_far`), под ним вода с барашками (`par_mid`). Слои это ленты, которые стыкуются
## по краям; чем слой ближе, тем быстрее он едет за камерой (`factors`).
## Баг технологии 16/32 (#97) ломает именно это: `bug_dir` разворачивает слои в разные стороны,
## `bug_tear` рвёт каждый слой пополам по высоте со сдвигом.
## Демка может дать свои слои (`of_layers`, у тропы #98 лес без неба): ленты по порядку от
## дальней, у каждой доля скорости и верх на экране; первая закрывает экран целиком.

var sky: Texture2D
var far: Texture2D
var mid: Texture2D
## Доля скорости камеры у слоёв: облака, берег, вода.
var factors: Array[float] = [0.08, 0.25, 0.5]
var bug_dir: Array[float] = [1.0, 1.0, 1.0]
var bug_tear := 0.0
## Свои слои демки вместо неба, берега и воды: ленты, доли скорости, верх на экране.
var layers: Array[Texture2D] = []
var layer_factors: Array[float] = []
var layer_tops: Array[float] = []


static func of(setting: SettingDef) -> Parallax16:
	var p := Parallax16.new()
	p.sky = setting.sprite16("par_sky")
	p.far = setting.sprite16("par_far")
	p.mid = setting.sprite16("par_mid")
	return p


## Свои слои: имена лент сеттинга от дальней к ближней, доли скорости и верх каждой на экране.
static func of_layers(setting: SettingDef, names: Array[String], factors: Array[float], tops: Array[float]) -> Parallax16:
	var p := Parallax16.new()
	for n in names:
		p.layers.append(setting.sprite16(n))
	p.layer_factors = factors
	p.layer_tops = tops
	return p


## Нарисовать фон: `horizon` линия горизонта на экране, `cam_x` сдвиг камеры в пикселях мира.
func draw(canvas: CanvasItem, view: Vector2, cam_x: float, horizon: float, palette: Array[Color]) -> void:
	if not layers.is_empty():
		canvas.draw_rect(Rect2(Vector2.ZERO, view), palette[Bit16Screen.K])
		for i in layers.size():
			_strip(canvas, layers[i], view, cam_x * layer_factors[i] * bug_dir[i % bug_dir.size()], layer_tops[i])
		return
	# Небо: четыре цвета сверху вниз, между ними по три строки через одну (переход без плавности,
	# как на 16 цветах).
	var bands: Array[int] = [Bit16Screen.NAVY, Bit16Screen.SEA, Bit16Screen.AQUA, Bit16Screen.SKY]
	var band_h := horizon / bands.size()
	for i in bands.size():
		var y := roundf(i * band_h)
		canvas.draw_rect(Rect2(0, y, view.x, ceilf(band_h) + 1.0), palette[bands[i]])
		if i > 0:
			for k in 3:
				canvas.draw_rect(Rect2(0, y + 1.0 + k * 2.0, view.x, 1.0), palette[bands[i - 1]])
	_strip(canvas, sky, view, cam_x * factors[0] * bug_dir[0], roundf(horizon * 0.18))
	if far != null:
		_strip(canvas, far, view, cam_x * factors[1] * bug_dir[1], horizon - far.get_height())
	# Вода от горизонта до низа экрана, по её кромке лента волн.
	canvas.draw_rect(Rect2(0, horizon, view.x, view.y - horizon), palette[Bit16Screen.SEA])
	_strip(canvas, mid, view, cam_x * factors[2] * bug_dir[2], horizon - 4.0)


## Лента слоя, размноженная по ширине экрана со сдвигом; с разрывом нижняя половина уезжает.
func _strip(canvas: CanvasItem, tex: Texture2D, view: Vector2, shift: float, y: float) -> void:
	if tex == null:
		return
	var w := float(tex.get_width())
	var h := float(tex.get_height())
	var x := -fposmod(roundf(shift), w)
	while x < view.x:
		if bug_tear == 0.0:
			canvas.draw_texture(tex, Vector2(x, y))
		else:
			var half := floorf(h / 2.0)
			canvas.draw_texture_rect_region(tex, Rect2(x, y, w, half), Rect2(0, 0, w, half))
			canvas.draw_texture_rect_region(tex, Rect2(x + bug_tear, y + half, w, h - half), Rect2(0, half, w, h - half))
		x += w
	if bug_tear > 0.0:
		# Разрыв сдвинул нижнюю половину вправо: слева дыру закрывает ещё одна копия.
		var half := floorf(h / 2.0)
		canvas.draw_texture_rect_region(tex, Rect2(-fposmod(roundf(shift), w) - w + bug_tear, y + half, w, h - half),
				Rect2(0, half, w, h - half))
