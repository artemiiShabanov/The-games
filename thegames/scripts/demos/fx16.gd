class_name Fx16
extends RefCounted
## Мелкие эффекты демок 16/32 (плейтест 2026-11-12, «детализация как в битемапе»): пыль, искры
## монеты, звезда удара, вспышка выстрела из лент `fx16_*` (`tools/pixel_fx16.py`). Демка
## добавляет эффект в точке мира, шагает списком и рисует его со своим сдвигом камеры. Здесь же
## латунные рамки и полоски HUD, как у битемапа.

## Вид эффекта: лента, кадров, ширина кадра, кадров в секунду.
const KINDS := {"dust": ["fx16_dust", 5, 24, 14.0], "spark": ["fx16_spark", 4, 24, 18.0],
		"star": ["fx16_star", 4, 24, 18.0], "flash": ["fx16_flash", 3, 32, 24.0], "fire": ["fx16_fire", 4, 40, 20.0]}
const BRASS: Array[Color] = [Color("#3a240c"), Color("#8a5a1c"), Color("#d8a440"), Color("#fff0a0")]
const INK := Color("#1a1218")
const WELL := Color("#140e1c")

var tex := {}
## [вид, точка мира, секунды, зеркало].
var list: Array[Array] = []


static func create(set: SettingDef) -> Fx16:
	var f := Fx16.new()
	for k: String in KINDS:
		f.tex[k] = set.sprite16(KINDS[k][0])
	return f


func add(kind: String, at: Vector2, flip := false) -> void:
	list.append([kind, at, 0.0, flip])


func step(dt: float) -> void:
	for i in range(list.size() - 1, -1, -1):
		list[i][2] = float(list[i][2]) + dt
		var spec: Array = KINDS[list[i][0]]
		if float(list[i][2]) * float(spec[3]) >= int(spec[1]):
			list.remove_at(i)


## Все эффекты; `to_screen` переводит точку мира в экран.
func draw(canvas: CanvasItem, to_screen: Callable) -> void:
	for e in list:
		var spec: Array = KINDS[e[0]]
		var t: Texture2D = tex[e[0]]
		if t == null:
			continue
		var fw := float(spec[2])
		var fh := float(t.get_height())
		var frame := mini(int(float(e[2]) * float(spec[3])), int(spec[1]) - 1)
		var c: Vector2 = to_screen.call(e[1])
		var dst := Rect2((c - Vector2(fw, fh) * 0.5).round(), Vector2(fw, fh))
		if e[3]:
			dst.size.x = -fw
		canvas.draw_texture_rect_region(t, dst, Rect2(frame * fw, 0.0, fw, fh))


## Латунная рамка с фаской, заклёпками и тёмной лункой.
static func frame_box(canvas: CanvasItem, r: Rect2, bright := false) -> void:
	canvas.draw_rect(r.grow(1.0), INK)
	canvas.draw_rect(r, BRASS[2] if bright else BRASS[1])
	canvas.draw_rect(Rect2(r.position, Vector2(r.size.x, 1.0)), BRASS[3])
	canvas.draw_rect(Rect2(r.position, Vector2(1.0, r.size.y)), BRASS[3])
	canvas.draw_rect(Rect2(r.position.x, r.end.y - 1.0, r.size.x, 1.0), BRASS[0])
	canvas.draw_rect(Rect2(r.end.x - 1.0, r.position.y, 1.0, r.size.y), BRASS[0])
	canvas.draw_rect(r.grow(-2.0), INK)
	canvas.draw_rect(r.grow(-3.0), WELL)
	for c: Vector2 in [r.position, Vector2(r.end.x - 1.0, r.position.y), Vector2(r.position.x, r.end.y - 1.0), r.end - Vector2(1.0, 1.0)]:
		canvas.draw_rect(Rect2(c, Vector2(1.0, 1.0)), BRASS[3])


## Полоска в рамке: заливка рядами от светлого к тёмному по рампе, блик, насечки; при `blink`
## светлее.
static func bar(canvas: CanvasItem, r: Rect2, k: float, ramp: Array[Color], blink := false) -> void:
	frame_box(canvas, r.grow(3.0))
	var fill := roundf(r.size.x * clampf(k, 0.0, 1.0))
	if fill <= 0.0:
		return
	var rows: Array[Color] = [ramp[3], ramp[2], ramp[2], ramp[1], ramp[0]]
	for y in int(r.size.y):
		var c: Color = rows[mini(int(y * rows.size() / r.size.y), rows.size() - 1)]
		canvas.draw_rect(Rect2(r.position.x, r.position.y + y, fill, 1.0), c.lightened(0.4) if blink else c)
	canvas.draw_rect(Rect2(r.position + Vector2(1.0, 1.0), Vector2(maxf(fill - 2.0, 0.0), 1.0)), Color(1.0, 1.0, 1.0, 0.5))
	var x := 6.0
	while x < fill:
		canvas.draw_rect(Rect2(r.position.x + x, r.position.y + 1.0, 1.0, r.size.y - 2.0), Color(ramp[0], 0.35))
		x += 6.0
