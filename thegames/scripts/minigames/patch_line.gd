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
## speed, shift, shift_end, double. Мармелад (STYLE «Мармелад»): блоки мягкие тела
## `JellyShape`, на место садятся с вытяжкой, сплющиванием и вздрогом, от неверной стрелки
## качаются вбок на пружинке; курсор не рамка, а подъём на бортике блока под ним и бледное
## гнездо на ленте. Игра и бот от мармелада не зависят: он только рисуется.

class Block:
	var x := 0.0
	## −2..2: знак куда сдвинут (вверх плюс), модуль сколько нажатий осталось.
	var shift := 0
	var fixed := false
	var missed := false
	var pop := 0.0
	var shake := 0.0
	var offset := 0.0
	## Мармелад, только рисование: тело (заводится, когда блок подъезжает к экрану),
	## подъём под курсором, качание вбок от неверной стрелки, отметки уже показанных событий.
	var jelly: JellyShape
	var lift := 0.0
	var sway := JellySpring.new()
	var landed := false
	var miss_seen := false

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
## Мармелад: вздрог при посадке на место, сжатие от нажатия, толчок вбок от неверной стрелки,
## за сколько секунд блок поднимается под курсором.
const LAND_POKE := 240.0
const PRESS_POKE := -140.0
const MISS_POKE := -180.0
const SWAY_KICK := 240.0
const SWAY_PUSH := 120.0
const LIFT_SECONDS := 0.1

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
		_jelly_wrong(b, dir)
		return
	# Сдвинут вверх: нужна стрелка вниз, и наоборот; двойной сдвиг сходит на один за нажатие.
	if dir == -signi(b.shift):
		b.shift -= signi(b.shift)
		_click.play()
		if b.jelly != null:
			b.jelly.poke(PRESS_POKE)
		if b.shift == 0:
			b.fixed = true
			b.pop = POP_SECONDS
			fixed_count += 1
	else:
		b.shake = SHAKE_SECONDS
		_wrong.play()
		_jelly_wrong(b, dir)


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


# --- Мармелад -----------------------------------------------------------------------------

## Неверная стрелка: блок качается вбок на пружинке, бок со стороны толчка вминается.
func _jelly_wrong(b: Block, dir: int) -> void:
	var side := float(dir)
	b.sway.kick(SWAY_KICK * side)
	if b.jelly != null:
		b.jelly.push(Vector2(SWAY_PUSH * side, 0.0), Vector2(-side, 0.0))


func _block_center(b: Block, mid: float) -> Vector2:
	return Vector2(b.x + BLOCK / 2.0 + b.sway.value, mid - b.offset)


func _lane_mid() -> float:
	return size.y * 0.5 + 20.0


## Тела блоков на экране ведутся за игровыми координатами; мармелад живёт и после финиша,
## пока сцена на экране; на паузе стоит.
func _process(delta: float) -> void:
	super(delta)
	if def == null or paused or blocks.is_empty():
		return
	var tu := Jelly.tuning()
	var mid := _lane_mid()
	var under: Block = _under_cursor() if running else null
	var lift_rate := tu.lift_px / LIFT_SECONDS * delta
	for b in blocks:
		b.sway.step(delta, tu.spring_stiffness, tu.spring_damping)
		b.lift = move_toward(b.lift, tu.lift_px if b == under else 0.0, lift_rate)
		var on_screen := b.x < size.x + BLOCK and b.x > -BLOCK * 2.0
		if not on_screen:
			continue
		var center := _block_center(b, mid)
		if b.jelly == null:
			# Тянется только по вертикали (по осям, STYLE): лента едет ровно, посадка тянет блок.
			b.jelly = JellyShape.rect(Vector2(BLOCK, BLOCK), Style.R_CTL)
			b.jelly.blob.stretch_free = false
			b.jelly.snap(center)
			b.jelly.blob.center_velocity = Vector2(-speed, 0.0)
		if not Jelly.on():
			b.jelly.snap(center)
			continue
		b.jelly.follow(delta, center)
		if b.fixed and not b.landed and is_zero_approx(b.offset):
			b.landed = true
			b.jelly.poke(LAND_POKE)
		if b.missed and not b.miss_seen:
			b.miss_seen = true
			b.jelly.poke(MISS_POKE)
	if not running:
		queue_redraw()


## Середина тела с его качанием: туда же рисуются стрелки.
func _jelly_mid(b: Block) -> Vector2:
	var pts := b.jelly.blob.points
	var sum := Vector2.ZERO
	for p in pts:
		sum += p
	return sum / maxf(pts.size(), 1.0)


# --- Рисование ----------------------------------------------------------------------------

func _draw() -> void:
	if def == null:
		return
	var mid := _lane_mid()
	var cx := _cursor_x()
	# Рельсы ленты сверху и снизу ряда.
	var rail := Color(Style.INK, 0.08)
	draw_rect(Rect2(0, mid - BLOCK / 2.0 - 12, size.x, 4), rail)
	draw_rect(Rect2(0, mid + BLOCK / 2.0 + 8, size.x, 4), rail)
	# Курсор: бледное гнездо на месте блока в ленте, сам блок под ним поднят на бортике.
	var cursor := Rect2(cx - BLOCK / 2.0, mid - BLOCK / 2.0, BLOCK, BLOCK)
	Style.flat(Color(Style.INK, 0.06), Style.R_CTL, Color.TRANSPARENT, 0).draw(get_canvas_item(), cursor)
	for b in blocks:
		if b.x > size.x + BLOCK or b.x < -BLOCK * 2.0:
			continue
		var k := b.pop / POP_SECONDS
		var color := Style.accent(0)
		if b.missed:
			color = Style.INK_3
		elif b.fixed:
			color = Style.SUCCESS.lerp(Style.accent(0), 1.0 - k)
		elif b.shift != 0:
			color = Style.accent(1)
		var up := Vector2(0.0, -b.lift)
		var c: Vector2
		if b.jelly != null:
			b.jelly.draw_lifted(self, color, b.lift, up)
			c = _jelly_mid(b) + up
		else:
			var at := _block_center(b, mid) + up
			Style.flat(color, Style.R_CTL, Color.TRANSPARENT, 0).draw(get_canvas_item(), Rect2(at - Vector2(BLOCK, BLOCK) / 2.0, Vector2(BLOCK, BLOCK)))
			c = at
		# Метка на сдвинутом блоке: стрелки, куда его вернуть, по одной на нажатие.
		if b.shift != 0 and not b.missed:
			var n := absi(b.shift)
			var d := signi(b.shift) * 18.0
			for j in n:
				var a := c + Vector2(0.0, (j - (n - 1) / 2.0) * 22.0 * signi(b.shift))
				draw_colored_polygon(PackedVector2Array([a + Vector2(-16, -d * 0.5), a + Vector2(16, -d * 0.5), a + Vector2(0, d)]), Color(1, 1, 1, 0.9))
	# Промахи крестиками справа сверху.
	var r := 7.0
	var gap2 := 28.0
	var ex := size.x - 48.0 - (FAIL_AT - 1) * gap2
	for j in FAIL_AT:
		var col := Style.DANGER if j < misses else Style.SURFACE_2
		var px := ex + j * gap2
		draw_line(Vector2(px - r + 1, 60.0 - r + 1), Vector2(px + r - 1, 60.0 + r - 1), col, 3.0, true)
		draw_line(Vector2(px - r + 1, 60.0 + r - 1), Vector2(px + r - 1, 60.0 - r + 1), col, 3.0, true)
