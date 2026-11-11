class_name StudioDaylight
extends RefCounted
## Время суток за окнами студии (#80, плейтест 2026-11-11): цвета неба, общий оттенок студии,
## солнце и свет из окон на полу. Только числа из `StudioBackdropTuning` и час, без случайности;
## рисует `StudioBackdrop`.

## Час 0..24.
var hour := 0.0
## Верх неба и полоса у горизонта.
var top := Color.WHITE
var low := Color.WHITE
## Оттенок всей студии поверх: цвет с прозрачностью.
var ambient := Color(1, 1, 1, 0)
## Свет из окон на полу: цвет, прозрачность это сила (0 ночью).
var light := Color(1, 1, 1, 0)
## Лучи в воздухе, прозрачность.
var beam := 0.0
## Пятно на полу: глубина на пиксель высоты окна над полом и сдвиг вбок на пиксель глубины.
var shaft := 0.0
var slant := 0.0
## Солнце: 0..1 от восхода до заката (меньше 0 под горизонтом) и высота 0..1.
var sun_t := -1.0
var elev := 0.0
## Ночь 0..1: звёзды, огни города, свет мониторов.
var night := 0.0


static func at(t: StudioBackdropTuning, hour_: float) -> StudioDaylight:
	var d := StudioDaylight.new()
	var h := fposmod(hour_, 24.0)
	d.hour = h
	var hs := t.sky_hours
	var i := 0
	while i < hs.size() - 2 and h > hs[i + 1]:
		i += 1
	var k := clampf((h - hs[i]) / maxf(0.001, hs[i + 1] - hs[i]), 0.0, 1.0)
	d.top = t.sky_top[i].lerp(t.sky_top[i + 1], k)
	d.low = t.sky_low[i].lerp(t.sky_low[i + 1], k)
	d.ambient = t.ambient[i].lerp(t.ambient[i + 1], k)
	d.sun_t = (h - t.sunrise) / (t.sunset - t.sunrise)
	if d.sun_t >= 0.0 and d.sun_t <= 1.0:
		d.elev = sin(PI * d.sun_t)
		var low_sun := pow(1.0 - d.elev, 2.0)
		var fade := clampf(minf(d.sun_t, 1.0 - d.sun_t) / 0.05, 0.0, 1.0)
		d.shaft = lerpf(t.shaft_noon, t.shaft_low, low_sun)
		d.slant = (d.sun_t * 2.0 - 1.0) * t.shaft_slant
		d.light = t.light_noon.lerp(t.light_golden, low_sun)
		d.light.a *= fade
		d.beam = t.beam_alpha * low_sun * fade
	else:
		d.sun_t = -1.0
	var dusk_end := t.sunset + 1.9
	var dawn_start := t.sunrise - 1.5
	if h >= dusk_end or h <= dawn_start:
		d.night = 1.0
	elif h > t.sunset:
		d.night = (h - t.sunset) / (dusk_end - t.sunset)
	elif h < t.sunrise:
		d.night = 1.0 - (h - dawn_start) / (t.sunrise - dawn_start)
	return d
