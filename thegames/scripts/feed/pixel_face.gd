class_name PixelFace
extends Control
## Пиксельное лицо персонажа 16×16 в масштабе: заглушка до портретов M5, но уже живое:
## говорит (рот открывается и закрывается в своём ритме) и моргает. Цвета по STYLE: `studio-ink`
## плюс акцент персонажа.

const HEAD := [
	"....KKKKKKKK....",
	"...KAAAAAAAAK...",
	"..KAAAAAAAAAAK..",
	".KAAAAAAAAAAAAK.",
	".KAAAAAAAAAAAAK.",
	".KAAEEAAAAEEAAK.",
	".KAAEEAAAAEEAAK.",
	".KAAAAAAAAAAAAK.",
	".KAAAAAAAAAAAAK.",
	".KAAAMMMMMMAAAK.",
	".KAAAAAAAAAAAAK.",
	"..KAAAAAAAAAAK..",
	"..KKAAAAAAAAKK..",
	"....KKKKKKKK....",
	"......KAAK......",
	".....KAAAAK.....",
]

var accent := Style.INK_3
var scale_px := 5
var talking := true
var _mouth_open := false
var _blink := false
var _mouth_timer := 0.0
var _blink_timer := 1.5
var _rng := RandomNumberGenerator.new()


func _init(accent_ := Style.INK_3, scale_ := 5) -> void:
	accent = accent_
	scale_px = scale_
	custom_minimum_size = Vector2(16, 16) * scale_px
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_rng.randomize()


func _process(delta: float) -> void:
	_mouth_timer -= delta
	if _mouth_timer <= 0.0:
		_mouth_open = talking and not _mouth_open
		_mouth_timer = _rng.randf_range(0.08, 0.22) if talking else 0.5
		queue_redraw()
	_blink_timer -= delta
	if _blink_timer <= 0.0:
		_blink = not _blink
		_blink_timer = 0.12 if _blink else _rng.randf_range(1.5, 4.0)
		queue_redraw()


func _draw() -> void:
	var ink := Style.STUDIO_INK
	for y in HEAD.size():
		var row: String = HEAD[y]
		for x in row.length():
			var ch := row[x]
			var color := Color.TRANSPARENT
			match ch:
				"K":
					color = ink
				"A":
					color = accent
				"E":
					color = accent if (_blink and y == 5) else ink
				"M":
					color = ink if _mouth_open or x in [6, 9] else accent
					if _mouth_open and y == 9 and x > 5 and x < 10:
						color = ink
			if color.a > 0.0:
				draw_rect(Rect2(x * scale_px, y * scale_px, scale_px, scale_px), color)
	if _mouth_open:
		draw_rect(Rect2(6 * scale_px, 10 * scale_px, 4 * scale_px, scale_px), ink)
