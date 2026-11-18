class_name RunningLamp
extends Control
## Лампа «в эфире» из логотипа Studio Running (2026-11-17): красная точка, которая дышит, пока
## студия работает. Стоит слева от названия студии в шапке забега. Цвет `danger` палитры игрока;
## с выключенным движением интерфейса (`Jelly.enabled`) горит ровно.

var _t := 0.0


func _ready() -> void:
	var d := (Style.LAMP_RADIUS + Style.LAMP_HALO) * 2.0
	custom_minimum_size = Vector2(d, d)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _process(delta: float) -> void:
	_t += delta
	queue_redraw()


func _draw() -> void:
	var c := size / 2.0
	var k := 1.0
	if Jelly.enabled:
		k = 0.5 + 0.5 * cos(TAU * _t / Style.LAMP_BREATH_SECONDS)
	var lit := lerpf(Style.LAMP_DIM, 1.0, k)
	draw_circle(c, Style.LAMP_RADIUS + Style.LAMP_HALO * 0.5, Color(Style.ACCENT, 0.22 * k), false, Style.LAMP_HALO * 0.6, true)
	draw_circle(c, Style.LAMP_RADIUS, Color(Style.ACCENT, lit), true, -1.0, true)
