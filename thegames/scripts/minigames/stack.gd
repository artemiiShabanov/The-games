extends Minigame
## «Поставь» (stack, технология 16/32-bit), каталог `docs/specs/minigames_catalog.md`. Блок
## ездит влево-вправо над башней, A роняет его: блок падает прямо вниз. Что легло на верхний
## этаж, остаётся, что свесилось за его край, отрезается и падает, башня сужается. Промахнулся
## целиком: провал. Поставить `FLOORS` этажей до таймера. Попал почти точно (свес меньше
## `PERFECT`): блок встаёт ровно и ничего не теряет.
## Параметры от `t` в `resources/minigames/stack.tres`: speed (скорость блока, пикселей в
## секунду), width (ширина первого блока), flip (шанс, что блок на проходе развернётся на лету).
## Разворот на лету бывает не раньше, чем блок дойдёт передним краем до дальнего края основания
## башни (плейтест 2026-11-14, #131): пройти мимо башни, не показавшись над ней целиком, нельзя.
## Звуки мармеладные из общей библиотеки `Sfx`: шлепок посадки лесенкой вверх, чвяк обрезка,
## боньк разворота, унылый съезд промаха.
## Вид как у всех мини-игр, в стиле оболочки: рендера технологии здесь нет (решение
## 2026-11-11). Мармелад: блоки мягкие тела `JellyShape`, едущий блок тянется за движением и
## стоит на бортике как текущий элемент, от посадки вздрагивает он и этаж под ним, а башня
## качается на пружине; обрезок сереет и падает, кувыркаясь; точная посадка брызгает неяркими
## каплями, промах сереет в `ink-3` и улетает вниз.
## Мышь (#83): клик роняет блок, как A.

enum Phase { RIDE, FALL, MISS }

const FLOORS := 8
const BLOCK_H := 44.0
const RADIUS := 12.0
## Блок ездит на столько в обе стороны от середины и висит на столько над башней.
const RANGE := 430.0
const HOVER := 104.0
const FALL_SECONDS := 0.16
## Свес меньше этого прощается: блок встаёт ровно. Перекрытие меньше `MIN_OVERLAP` это промах.
const PERFECT := 10.0
const MIN_OVERLAP := 6.0
## Разворот на лету: не раньше дальнего края основания, не дальше этой доли пути от края до края.
const FLIP_TO := 0.8
## Полутоны шлепка посадки по этажам: пентатоника вверх.
const STEP_NOTES: Array[int] = [0, 2, 4, 7, 9, 12, 14, 16]
const STEP_BASE_HZ := 150.0
const BASE_BOTTOM := 132.0
const DOT_R := 9.0
const DOT_GAP := 34.0
const LIFT := 8.0
## Бот LOSE роняет блок через столько после его появления: блок ещё у края, мимо башни.
const BOT_LOSE_WAIT := 0.05

var speed := 380.0
var start_width := 340.0
var flip_chance := 0.0
var phase := Phase.RIDE
var placed := 0
## Этажи башни снизу вверх: x середины и ширина.
var floors_x: Array[float] = []
var floors_w: Array[float] = []
## Едущий блок: середина, ширина, направление.
var block_x := 0.0
var block_w := 340.0
var dir := 1.0
var phase_time := 0.0

var _flip_at := -1.0
var _shapes: Array[JellyShape] = []
var _block: JellyShape
## Обрезки: [тело, точка, скорость, угол, ширина].
var _scraps: Array[Array] = []
var _sway := JellySpring.new()
var _dots: Array[JellySpring] = []
var _splash := SplashFx.new()
var _steps: Array[AudioStreamPlayer] = []
var _cut: AudioStreamPlayer
var _miss: AudioStreamPlayer
var _win: AudioStreamPlayer
var _turn: AudioStreamPlayer
var _miss_y := 0.0
var _bot_wait := 0.0


func _on_start() -> void:
	speed = maxf(def.param(&"speed", t, 380.0), 60.0)
	start_width = clampf(def.param(&"width", t, 340.0), 120.0, 520.0)
	flip_chance = clampf(def.param(&"flip", t, 0.0), 0.0, 1.0)
	for note in STEP_NOTES:
		var p := Sfx.player(Sfx.plop(STEP_BASE_HZ * pow(2.0, note / 12.0), 0.55, _steps.size()))
		add_child(p)
		_steps.append(p)
	_cut = Sfx.player(Sfx.squelch())
	_miss = Sfx.player(Sfx.droop())
	_win = Sfx.player(Sfx.blip(990.0, 0.3, 0.45, 8.0))
	_turn = Sfx.player(Sfx.boing())
	var players: Array[AudioStreamPlayer] = [_cut, _miss, _win, _turn]
	for p in players:
		add_child(p)
	for i in FLOORS:
		_dots.append(JellySpring.new())
	# Основание башни: первый этаж уже стоит по центру.
	floors_x.append(0.0)
	floors_w.append(start_width)
	_shapes.append(JellyShape.rect(Vector2(start_width, BLOCK_H), RADIUS))
	_shapes[0].snap(_floor_center(0))
	block_w = start_width
	_spawn()
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if running and GameInput.is_a(event):
		drop()
		get_viewport().set_input_as_handled()


## Уронить едущий блок: он падает прямо вниз с того места, где был.
func drop() -> void:
	if not running or phase != Phase.RIDE:
		return
	phase = Phase.FALL
	phase_time = 0.0


func _on_tick(delta: float) -> void:
	phase_time += delta
	match phase:
		Phase.RIDE:
			var before := block_x
			block_x += dir * speed * delta
			# Разворот на лету: блок прошёл назначенную точку пути.
			if _flip_at >= 0.0 and (before - _flip_at) * (block_x - _flip_at) <= 0.0:
				_flip_at = -1.0
				dir = -dir
				_turn.play()
			elif absf(block_x) >= RANGE:
				block_x = clampf(block_x, -RANGE, RANGE)
				dir = -dir
				_plan_flip()
		Phase.FALL:
			if phase_time >= FALL_SECONDS:
				_land()
	queue_redraw()


## Время вышло: башня не достроена.
func _on_timeout() -> bool:
	return false


## Новый блок выезжает с края; ширина как у верхнего этажа.
func _spawn() -> void:
	phase = Phase.RIDE
	phase_time = 0.0
	dir = -dir
	block_x = -RANGE * dir
	block_w = floors_w[floors_w.size() - 1]
	_block = JellyShape.rect(Vector2(block_w, BLOCK_H), RADIUS)
	_block.snap(_block_center())
	_plan_flip()


## Решить, развернётся ли блок на этом проходе и где.
func _plan_flip() -> void:
	_flip_at = -1.0
	if rng.randf() < flip_chance:
		# Передний край блока дошёл до дальнего края основания: середина блока вот здесь.
		var reach := (floors_w[0] - block_w) / 2.0
		_flip_at = dir * rng.randf_range(reach, maxf(RANGE * (2.0 * FLIP_TO - 1.0), reach))


## Блок долетел до башни: остаётся то, что легло на верхний этаж.
func _land() -> void:
	var top_x := floors_x[floors_x.size() - 1]
	var top_w := floors_w[floors_w.size() - 1]
	var left := maxf(block_x - block_w / 2.0, top_x - top_w / 2.0)
	var right := minf(block_x + block_w / 2.0, top_x + top_w / 2.0)
	if right - left < MIN_OVERLAP:
		phase = Phase.MISS
		phase_time = 0.0
		_miss_y = 0.0
		_miss.play()
		if _block != null:
			_block.poke(-200.0)
		finish(false)
		return
	var perfect := absf(block_x - top_x) <= PERFECT
	var new_x := top_x if perfect else (left + right) / 2.0
	var new_w := block_w if perfect else right - left
	if not perfect:
		# Обрезок: то, что свесилось с той стороны, куда блок промахнулся.
		var side := signf(block_x - top_x)
		var scrap_w := block_w - new_w
		var scrap_x := new_x + side * (new_w + scrap_w) / 2.0
		var body := JellyShape.rect(Vector2(scrap_w, BLOCK_H), minf(RADIUS, scrap_w / 2.0))
		var at := Vector2(size.x / 2.0 + scrap_x, _floor_y(floors_x.size()))
		body.snap(at)
		_scraps.append([body, at, Vector2(side * 90.0, -60.0), 0.0, side])
		_cut.play()
	floors_x.append(new_x)
	floors_w.append(new_w)
	placed += 1
	var shape := JellyShape.rect(Vector2(new_w, BLOCK_H), minf(RADIUS, new_w / 2.0))
	shape.snap(_floor_center(floors_x.size() - 1))
	_shapes.append(shape)
	# Высота шлепка чуть гуляет от раза к разу (не из геймплейного rng), и точная посадка звонче.
	var step := _steps[clampi(placed - 1, 0, _steps.size() - 1)]
	step.pitch_scale = randf_range(0.96, 1.04) * (1.06 if perfect else 1.0)
	step.play()
	if Jelly.on():
		shape.poke(-260.0)
		_shapes[_shapes.size() - 2].poke(-140.0)
		_sway.kick((block_x - top_x) * 6.0)
		_dots[placed - 1].kick(9.0)
		if perfect:
			_splash.pop(_floor_center(floors_x.size() - 1) - Vector2(0.0, BLOCK_H / 2.0), _floor_color(floors_x.size() - 1), 5, 360.0, 0.5)
	if placed >= FLOORS:
		_block = null
		_win.play()
		finish(true)
		return
	_spawn()


## Бот: WIN роняет, когда блок над серединой верхнего этажа; LOSE сразу, пока блок у края.
func _bot_step(delta: float) -> bool:
	if phase != Phase.RIDE:
		return false
	if AutoTest.bot_mode == AutoTest.BotMode.WIN:
		if absf(block_x - floors_x[floors_x.size() - 1]) <= speed * delta * 0.6:
			tap_action(GameInput.A)
	else:
		_bot_wait += delta
		if _bot_wait >= BOT_LOSE_WAIT:
			tap_action(GameInput.A)
	return false


func _on_finish(success: bool) -> void:
	if success and Jelly.on():
		for i in _shapes.size():
			_shapes[i].poke(200.0)
		_splash.pop(_floor_center(floors_x.size() - 1) - Vector2(0.0, BLOCK_H), Style.SUCCESS, 8, 460.0, 0.6)


# --- Геометрия и мармелад ---------------------------------------------------------------------

## Середина этажа `i` (0 основание) по вертикали.
func _floor_y(i: int) -> float:
	return size.y - BASE_BOTTOM - (i + 0.5) * BLOCK_H


## Середина этажа `i`; башня качается сильнее к верху.
func _floor_center(i: int) -> Vector2:
	var sway := clampf(_sway.value, -30.0, 30.0) * float(i) / FLOORS if Jelly.on() else 0.0
	return Vector2(size.x / 2.0 + floors_x[i] + sway, _floor_y(i))


## Середина едущего блока: над башней, в падении опускается на неё, промах улетает вниз.
func _block_center() -> Vector2:
	var rest := _floor_y(floors_x.size())
	var y := rest - HOVER
	if phase == Phase.FALL:
		var k := clampf(phase_time / FALL_SECONDS, 0.0, 1.0)
		y = lerpf(rest - HOVER, rest, k * k)
	elif phase == Phase.MISS:
		y = rest + _miss_y
	return Vector2(size.x / 2.0 + block_x, y)


func _floor_color(i: int) -> Color:
	return Style.accent(i % 2)


func _process(delta: float) -> void:
	super(delta)
	if def == null or paused or _shapes.is_empty():
		return
	var tu := Jelly.tuning()
	_sway.step(delta, tu.spring_stiffness, tu.spring_damping)
	for d in _dots:
		d.step(delta, tu.spring_stiffness, tu.spring_damping)
	for i in _shapes.size():
		_shapes[i].follow(delta, _floor_center(i))
	if phase == Phase.MISS:
		# Промах улетает вниз и после финиша: таймер мини-игры уже стоит.
		phase_time += delta
		_miss_y += (900.0 + 2400.0 * phase_time) * delta
	if _block != null:
		_block.follow(delta, _block_center())
	for i in range(_scraps.size() - 1, -1, -1):
		var s := _scraps[i]
		var vel: Vector2 = s[2]
		vel.y += 1900.0 * delta
		var at: Vector2 = (s[1] as Vector2) + vel * delta
		s[1] = at
		s[2] = vel
		s[3] = float(s[3]) + float(s[4]) * 5.0 * delta
		(s[0] as JellyShape).follow(delta, at, float(s[3]))
		if at.y > size.y + 120.0:
			_scraps.remove_at(i)
	_splash.step(delta, func(_x: float) -> float: return INF)
	if not running:
		queue_redraw()


# --- Рисование --------------------------------------------------------------------------------

func _draw() -> void:
	if def == null or _shapes.is_empty():
		return
	var ci := get_canvas_item()
	var jelly := Jelly.on()
	# Стол под башней.
	var table := Rect2(size.x / 2.0 - RANGE - 120.0, size.y - BASE_BOTTOM, 2.0 * RANGE + 240.0, 22.0)
	Style.flat(Style.SURFACE_2, Style.R_PILL, Color.TRANSPARENT, 0).draw(ci, table)
	# Этажи.
	for i in _shapes.size():
		if jelly:
			_shapes[i].draw(self, _floor_color(i))
		else:
			var c := _floor_center(i)
			Style.flat(_floor_color(i), int(RADIUS), Color.TRANSPARENT, 0).draw(ci, Rect2(c.x - floors_w[i] / 2.0, c.y - BLOCK_H / 2.0, floors_w[i], BLOCK_H))
	# Обрезки серые.
	for s in _scraps:
		(s[0] as JellyShape).draw(self, Style.INK_3)
	# Едущий блок: текущий элемент на бортике; промах сереет.
	if _block != null:
		var color := _floor_color(floors_x.size())
		if phase == Phase.MISS:
			color = color.lerp(Style.INK_3, clampf(phase_time / 0.2, 0.0, 1.0))
		if jelly:
			if phase == Phase.RIDE:
				_block.draw_lifted(self, color, LIFT)
			else:
				_block.draw(self, color)
		else:
			var c := _block_center()
			Style.flat(color, int(RADIUS), Color.TRANSPARENT, 0).draw(ci, Rect2(c.x - block_w / 2.0, c.y - BLOCK_H / 2.0, block_w, BLOCK_H))
	if jelly:
		_splash.draw_air(self, Vector2.ZERO)
	_draw_dots()


## Кружки этажей сверху по центру: поставленные `success`.
func _draw_dots() -> void:
	var y := 40.0 + AspectIcon.SIZE / 2.0
	var x0 := size.x / 2.0 - (FLOORS - 1) * DOT_GAP / 2.0
	for i in FLOORS:
		var c := Style.SUCCESS if i < placed else Color(Style.INK, 0.12)
		var r := DOT_R
		if i == placed and running:
			r *= 1.3
		r *= clampf(1.0 + _dots[i].value, 0.5, 1.8)
		draw_circle(Vector2(x0 + i * DOT_GAP, y), r, c)
