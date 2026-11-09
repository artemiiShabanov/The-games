class_name JellySurface
extends RefCounted
## Желейная поверхность: удары пускают по ней волны, которые бегут в стороны и гаснут, под
## телом она прогибается. `height(x)` смещение вниз в пикселях; хозяин прибавляет его к своей
## линии земли и рисует её ломаной с частым шагом. Координаты мира хозяина.

class Ripple:
	var x := 0.0
	var born := 0.0
	var amp := 0.0

var ripples: Array[Ripple] = []
var time := 0.0
## Прогиб под телом: центр, полуширина и глубина; хозяин ставит каждый кадр.
var dent_x := 0.0
var dent_w := 30.0
var dent_depth := 0.0


## Удар в точке `x` со скоростью падения `speed` (пиксели в секунду).
func impact(x: float, speed: float) -> void:
	var r := Ripple.new()
	r.x = x
	r.born = time
	r.amp = Jelly.tuning().ripple_amp * speed / 1000.0
	ripples.append(r)


func step(delta: float) -> void:
	time += delta
	var tu := Jelly.tuning()
	var keep: Array[Ripple] = []
	for r in ripples:
		if (time - r.born) * tu.ripple_decay < 5.0:
			keep.append(r)
	ripples = keep


func height(x: float) -> float:
	var tu := Jelly.tuning()
	var h := 0.0
	var k := TAU / tu.ripple_wavelength
	for r in ripples:
		var age := time - r.born
		var d := absf(x - r.x)
		var front := tu.ripple_speed * age
		if d > front + tu.ripple_wavelength * 0.5 or d > tu.ripple_range:
			continue
		# Гребень бежит наружу, за фронтом гладко, к краю дальности гаснет.
		var env := exp(-age * tu.ripple_decay) * (1.0 - d / tu.ripple_range)
		var edge := clampf((front + tu.ripple_wavelength * 0.5 - d) / (tu.ripple_wavelength * 0.5), 0.0, 1.0)
		h += r.amp * env * edge * cos(k * (d - front))
	if dent_depth > 0.0:
		var u := (x - dent_x) / dent_w
		h += dent_depth * exp(-u * u)
	return h


## Наклон поверхности в `x`: качает предметы, стоящие на ней.
func slope(x: float) -> float:
	return (height(x + 6.0) - height(x - 6.0)) / 12.0
