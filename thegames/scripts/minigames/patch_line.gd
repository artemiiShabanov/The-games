extends Minigame
## «Поправь» (patch_line, оптимизация), каталог `docs/specs/minigames_catalog.md`. Лента из
## крупных блоков бежит справа налево, курсор стоит; лента конечная, её последний блок
## подходит к курсору ровно к концу таймера (плейтест 2026-11-07). Часть блоков сдвинута
## вверх или вниз; когда сдвинутый блок под курсором, стрелка в сторону ленты (сдвинут вверх:
## ↓, вниз: ↑) ставит его на место со щелчком и пружинкой. С ростом `t` появляются блоки с
## двойным сдвигом: дальше от ленты, с двойной стрелкой, нужны два нажатия, соседи у него
## всегда на месте. Неверная стрелка
## только дёргает блок. Три блока проехали непоправленными: провал. Доля сдвинутых растёт по
## ходу раунда и с `t`, темп ленты с `t`. Параметры в `resources/minigames/patch_line.tres`:
## speed, shift, shift_end, double.

class Block:
	var x := 0.0
	## −2..2: знак куда сдвинут (вверх плюс), модуль сколько нажатий осталось.
	var shift := 0
	var fixed := false
	var missed := false
	var pop := 0.0
	var shake := 0.0
	var offset := 0.0

const BLOCK := 128.0
const GAP := 20.0
const SHIFT_PX := 84.0
## Двойной сдвиг дальше от ленты, чем два одинарных: читается сразу.
const DOUBLE_PX := 150.0
## Первый блок ленты стартует на этом расстоянии правее курсора.
const LEAD := 2.0 * (128.0 + 20.0)
const FAIL_AT := 3
const CURSOR_X := 0.42
const POP_SECONDS := 0.3
const SHAKE_SECONDS := 0.25
const SNAP_SECONDS := 0.1
const BOT_REACTION := 0.12

var speed := 240.0
var shift_share := 0.3
var shift_end := 0.6
var double_share := 0.0
var blocks: Array[Block] = []
var misses := 0
var fixed_count := 0
var _bot_timer := 0.0
var _click: AudioStreamPlayer
var _miss_sound: AudioStreamPlayer
var _wrong: AudioStreamPlayer


func _on_start() -> void:
	speed = def.param(&"speed", t, 240.0)
	shift_share = def.param(&"shift", t, 0.3)
	shift_end = def.param(&"shift_end", t, 0.6)
	double_share = def.param(&"double", t, 0.0)
	_click = Sfx.player(Sfx.blip(1100.0, 0.06, 0.4, 40.0))
	_miss_sound = Sfx.player(Sfx.thud(0.16, 0.5))
	_wrong = Sfx.player(Sfx.blip(220.0, 0.08, 0.25, 30.0))
	for p in [_click, _miss_sound, _wrong]:
		add_child(p)
	# Вся лента сразу: столько блоков, чтобы последний подошёл к курсору к концу таймера.
	var step := BLOCK + GAP
	var count := maxi(int(floor((speed * time_limit - LEAD) / step)) + 1, 1)
	var after_double := false
	for i in count:
		var b := Block.new()
		b.x = _cursor_x() - BLOCK / 2.0 + LEAD + i * step
		# Первые два блока на месте, чтобы игрок увидел ритм; дальше доля растёт по ленте.
		# Рядом с двойным блоком сдвинутых нет: сосед за ним на месте, а двойной выпадает
		# только после блока на месте (плейтест 2026-11-07).
		var share := lerpf(shift_share, shift_end, float(i) / maxi(count - 1, 1))
		if i >= 2 and not after_double and rng.randf() < share:
			var sign := 1 if rng.randf() < 0.5 else -1
			var prev_clear := blocks[i - 1].shift == 0
			b.shift = sign * (2 if prev_clear and rng.randf() < double_share else 1)
		after_double = absi(b.shift) == 2
		b.offset = _offset_for(b.shift)
		blocks.append(b)
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	if event.is_action_pressed(GameInput.UP):
		_press(1)
	elif event.is_action_pressed(GameInput.DOWN):
		_press(-1)
	else:
		return
	get_viewport().set_input_as_handled()


## Смещение блока от ленты по сдвигу: одинарный SHIFT_PX, двойной DOUBLE_PX.
func _offset_for(shift: int) -> float:
	match absi(shift):
		0:
			return 0.0
		1:
			return signf(shift) * SHIFT_PX
	return signf(shift) * DOUBLE_PX


func _cursor_x() -> float:
	return size.x * CURSOR_X


## Блок под курсором: его центр в пределах половины блока от курсора.
func _under_cursor() -> Block:
	var cx := _cursor_x()
	for b in blocks:
		if absf(b.x + BLOCK / 2.0 - cx) <= BLOCK / 2.0:
			return b
	return null


func _press(dir: int) -> void:
	var b := _under_cursor()
	if b == null or b.fixed or b.missed:
		return
	if b.shift == 0:
		b.shake = SHAKE_SECONDS
		_wrong.play()
		return
	# Сдвинут вверх: нужна стрелка вниз, и наоборот; двойной сдвиг сходит на один за нажатие.
	if dir == -signi(b.shift):
		b.shift -= signi(b.shift)
		_click.play()
		if b.shift == 0:
			b.fixed = true
			b.pop = POP_SECONDS
			fixed_count += 1
	else:
		b.shake = SHAKE_SECONDS
		_wrong.play()


func _on_tick(delta: float) -> void:
	var dx := speed * delta
	var cx := _cursor_x()
	for b in blocks:
		b.x -= dx
		b.pop = maxf(b.pop - delta, 0.0)
		b.shake = maxf(b.shake - delta, 0.0)
		# Поправленный блок едет на место за SNAP_SECONDS.
		b.offset = move_toward(b.offset, _offset_for(b.shift), SHIFT_PX / SNAP_SECONDS * delta)
		# Проехал курсор сдвинутым: промах.
		if b.shift != 0 and not b.missed and b.x + BLOCK < cx - BLOCK / 2.0:
			b.missed = true
			misses += 1
			_miss_sound.play()
			if misses >= FAIL_AT:
				finish(false)
				return
	while not blocks.is_empty() and blocks[0].x < -BLOCK * 2.0:
		blocks.remove_at(0)
	queue_redraw()


func _on_timeout() -> bool:
	return misses < FAIL_AT


## Бот: WIN жмёт нужную стрелку, когда сдвинутый блок под курсором, LOSE ничего не делает.
func _bot_step(delta: float) -> bool:
	if AutoTest.bot_mode != AutoTest.BotMode.WIN:
		return false
	var b := _under_cursor()
	if b == null or b.shift == 0 or b.fixed:
		_bot_timer = 0.0
		return false
	_bot_timer += delta
	if _bot_timer >= BOT_REACTION:
		_bot_timer = 0.0
		_press(-signi(b.shift))
	return false


# --- Рисование ----------------------------------------------------------------------------

func _draw() -> void:
	if def == null:
		return
	var mid := size.y * 0.5 + 20.0
	var cx := _cursor_x()
	# Рельсы ленты сверху и снизу ряда.
	var rail := Color(Style.INK, 0.08)
	draw_rect(Rect2(0, mid - BLOCK / 2.0 - 12, size.x, 4), rail)
	draw_rect(Rect2(0, mid + BLOCK / 2.0 + 8, size.x, 4), rail)
	for b in blocks:
		var k := b.pop / POP_SECONDS
		var scale_ := 1.0 + 0.12 * sin(k * PI)
		var w := BLOCK * scale_
		var x := b.x + (BLOCK - w) / 2.0
		if b.shake > 0.0:
			x += sin(b.shake * 50.0) * 6.0 * b.shake / SHAKE_SECONDS
		var y := mid - w / 2.0 - b.offset
		var color := Style.accent(0)
		if b.missed:
			color = Style.INK_3
		elif b.fixed:
			color = Style.SUCCESS.lerp(Style.accent(0), 1.0 - k)
		elif b.shift != 0:
			color = Style.accent(1)
		Style.flat(color, Style.R_CTL, Color.TRANSPARENT, 0).draw(get_canvas_item(), Rect2(x, y, w, w))
		# Метка на сдвинутом блоке: стрелки, куда его вернуть, по одной на нажатие.
		if b.shift != 0 and not b.missed:
			var n := absi(b.shift)
			var d := signi(b.shift) * 18.0
			for j in n:
				var c := Vector2(x + w / 2.0, y + w / 2.0 + (j - (n - 1) / 2.0) * 22.0 * signi(b.shift))
				draw_colored_polygon(PackedVector2Array([c + Vector2(-16, -d * 0.5), c + Vector2(16, -d * 0.5), c + Vector2(0, d)]), Color(1, 1, 1, 0.9))
	# Курсор: рамка фокуса вокруг места блока на ленте.
	var cursor := Rect2(cx - BLOCK / 2.0, mid - BLOCK / 2.0, BLOCK, BLOCK)
	Style.focus_ring(Style.R_CTL).draw(get_canvas_item(), cursor)
	# Промахи крестиками справа сверху.
	var r := 7.0
	var gap2 := 28.0
	var ex := size.x - 48.0 - (FAIL_AT - 1) * gap2
	for j in FAIL_AT:
		var c := Style.DANGER if j < misses else Style.SURFACE_2
		var px := ex + j * gap2
		draw_line(Vector2(px - r + 1, 60.0 - r + 1), Vector2(px + r - 1, 60.0 + r - 1), c, 3.0, true)
		draw_line(Vector2(px - r + 1, 60.0 + r - 1), Vector2(px + r - 1, 60.0 - r + 1), c, 3.0, true)
