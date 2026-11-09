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
## гнездо на ленте. Возвращаемый блок тянет за собой склизкий след (`SlimeTrail`, в координатах
## ленты, чтобы след ехал с ней); севший блок продавливает рельс с той стороны, куда ехал
## (рельс прогибается дугой на затухающей пружине, как стенка в «Выведи»), и брызгает мягкими
## каплями (`SplashFx.pop`) из углов. Игра и бот от мармелада не зависят: он только рисуется.

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
	## Куда ехал блок от последнего верного нажатия: 1 вверх, −1 вниз; след за ним.
	var move_dir := 0
	var trail: SlimeTrail

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
## Мармелад: след возвращаемого блока (жизнь, с, и непрозрачность), толчок прогиба рельса
## (пик около RAIL_BOW_PX), длина прогнутого куска рельса и его непрозрачность на пике прогиба,
## брызги при посадке.
const TRAIL_LIFE := 0.7
const TRAIL_ALPHA := 0.2
const RAIL_KICK := 370.0
const RAIL_BOW_PX := 8.0
const RAIL_BOW_ALPHA := 0.45
const RAIL_BOW_LENGTH := BLOCK + 2.0 * GAP
const SPLASH_COUNT := 3
const SPLASH_SPEED := 300.0
const SPLASH_LIFE := 0.45

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
## Мармелад, только рисование: сколько проехала лента (следы хранятся в её координатах),
## прогиб рельса под севшим блоком и брызги.
var _scroll := 0.0
var _rail := JellySpring.new()
var _rail_block: Block
var _rail_dir := 0
var _fx := SplashFx.new()


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
		b.move_dir = dir
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
	_scroll += dx
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
	_fx.step(delta, Callable())
	_rail.step(delta, tu.spring_stiffness * 2.0, tu.spring_damping * 1.5)
	for b in blocks:
		b.sway.step(delta, tu.spring_stiffness, tu.spring_damping)
		b.lift = move_toward(b.lift, tu.lift_px if b == under else 0.0, lift_rate)
		if b.trail != null:
			b.trail.step(delta)
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
		_jelly_trail(b, center)
		if b.fixed and not b.landed and is_zero_approx(b.offset):
			b.landed = true
			b.jelly.poke(LAND_POKE)
			_jelly_land(b, center)
		if b.missed and not b.miss_seen:
			b.miss_seen = true
			b.jelly.poke(MISS_POKE)
	if not running:
		queue_redraw()


## След за блоком, пока он едет к ленте: точки в координатах ленты, рвётся, когда блок встал.
func _jelly_trail(b: Block, center: Vector2) -> void:
	var moving := not is_equal_approx(b.offset, _offset_for(b.shift))
	if moving:
		if b.trail == null:
			b.trail = SlimeTrail.new(Style.accent(1), TRAIL_LIFE, TRAIL_ALPHA)
		b.trail.add(center + Vector2(_scroll, 0.0), BLOCK)
	elif b.trail != null:
		b.trail.cut()


## Посадка: рельс со стороны, куда ехал блок, прогибается наружу, из углов на передней кромке
## блока брызги его цвета.
func _jelly_land(b: Block, center: Vector2) -> void:
	_rail_block = b
	_rail_dir = b.move_dir
	_rail.value = 0.0
	_rail.velocity = 0.0
	_rail.kick(RAIL_KICK)
	var edge := center.y - b.move_dir * BLOCK / 2.0
	var color := _block_color(b)
	for side: float in [-1.0, 1.0]:
		_fx.pop(Vector2(center.x + side * BLOCK * 0.45, edge), color, SPLASH_COUNT, SPLASH_SPEED, SPLASH_LIFE)


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
	# Рельсы ленты сверху и снизу ряда; рельс под только что севшим блоком прогнут.
	var rail := Color(Style.INK, 0.08)
	_draw_rail(rail, 1)
	_draw_rail(rail, -1)
	# Курсор: бледное гнездо на месте блока в ленте, сам блок под ним поднят на бортике.
	var cursor := Rect2(cx - BLOCK / 2.0, mid - BLOCK / 2.0, BLOCK, BLOCK)
	Style.flat(Color(Style.INK, 0.06), Style.R_CTL, Color.TRANSPARENT, 0).draw(get_canvas_item(), cursor)
	# Следы под блоками, из координат ленты в экран.
	var ci := get_canvas_item()
	for b in blocks:
		if b.trail != null:
			b.trail.draw(self, Vector2(-_scroll, 0.0))
	for b in blocks:
		if b.x > size.x + BLOCK or b.x < -BLOCK * 2.0:
			continue
		var color := _block_color(b)
		var up := Vector2(0.0, -b.lift)
		var c: Vector2
		if b.jelly != null:
			b.jelly.draw_lifted(self, color, b.lift, up)
			c = _jelly_mid(b) + up
		else:
			var at := _block_center(b, mid) + up
			Style.flat(color, Style.R_CTL, Color.TRANSPARENT, 0).draw(ci, Rect2(at - Vector2(BLOCK, BLOCK) / 2.0, Vector2(BLOCK, BLOCK)))
			c = at
		# Метка на сдвинутом блоке: стрелки, куда его вернуть, по одной на нажатие.
		if b.shift != 0 and not b.missed:
			var n := absi(b.shift)
			var d := signi(b.shift) * 18.0
			for j in n:
				var a := c + Vector2(0.0, (j - (n - 1) / 2.0) * 22.0 * signi(b.shift))
				draw_colored_polygon(PackedVector2Array([a + Vector2(-16, -d * 0.5), a + Vector2(16, -d * 0.5), a + Vector2(0, d)]), Color(1, 1, 1, 0.9))
	# Прогнутый кусок рельса поверх блоков: иначе севший блок, вытянутый посадкой, его прячет.
	_draw_rail_bow(rail)
	_fx.draw_air(self, Vector2.ZERO)
	# Промахи крестиками справа сверху.
	var r := 7.0
	var gap2 := 28.0
	var ex := size.x - 48.0 - (FAIL_AT - 1) * gap2
	for j in FAIL_AT:
		var col := Style.DANGER if j < misses else Style.SURFACE_2
		var px := ex + j * gap2
		draw_line(Vector2(px - r + 1, 60.0 - r + 1), Vector2(px + r - 1, 60.0 + r - 1), col, 3.0, true)
		draw_line(Vector2(px - r + 1, 60.0 + r - 1), Vector2(px + r - 1, 60.0 - r + 1), col, 3.0, true)


func _block_color(b: Block) -> Color:
	if b.missed:
		return Style.INK_3
	if b.fixed:
		return Style.SUCCESS.lerp(Style.accent(0), 1.0 - b.pop / POP_SECONDS)
	if b.shift != 0:
		return Style.accent(1)
	return Style.accent(0)


## Рельс полосой во всю ширину: `side` 1 верхний, −1 нижний.
func _rail_rect(side: int) -> Rect2:
	var mid := _lane_mid()
	if side > 0:
		return Rect2(0, mid - BLOCK / 2.0 - 12, size.x, 4)
	return Rect2(0, mid + BLOCK / 2.0 + 8, size.x, 4)


## Прогибается ли сейчас рельс `side`: блок только что сел, ехав в его сторону.
func _rail_bowing(side: int) -> bool:
	return _rail_block != null and _rail_dir == side and absf(_rail.value) >= 0.05 and Jelly.on()


## Края прогнутого куска рельса по x: он идёт за севшим блоком.
func _rail_bow_x() -> float:
	return _rail_block.x + BLOCK / 2.0 + _rail_block.sway.value - RAIL_BOW_LENGTH / 2.0


## Рельс под блоками; на прогибе без куска под севшим блоком, тот рисует `_draw_rail_bow`.
func _draw_rail(col: Color, side: int) -> void:
	var rect := _rail_rect(side)
	if not _rail_bowing(side):
		draw_rect(rect, col)
		return
	var x0 := _rail_bow_x()
	var x1 := x0 + RAIL_BOW_LENGTH
	draw_rect(Rect2(rect.position.x, rect.position.y, maxf(x0 - rect.position.x, 0.0), rect.size.y), col)
	draw_rect(Rect2(x1, rect.position.y, maxf(rect.end.x - x1, 0.0), rect.size.y), col)


## Прогнутый кусок рельса поверх блоков: дуга наружу (концы стоят), как стенка в «Выведи»;
## на пике цвета севшего блока, по мере затухания пружины гаснет к бледному рельсу.
func _draw_rail_bow(col: Color) -> void:
	var side := _rail_dir
	if not _rail_bowing(side):
		return
	var rect := _rail_rect(side)
	var bow := _rail.value
	var k := clampf(absf(bow) / RAIL_BOW_PX, 0.0, 1.0)
	var ink := col.lerp(Color(_block_color(_rail_block), RAIL_BOW_ALPHA), k)
	var x0 := _rail_bow_x()
	# Наружу: верхний рельс вверх, нижний вниз.
	var out := Vector2(0.0, -side * bow)
	var steps := 12
	var poly := PackedVector2Array()
	for j in steps + 1:
		var u := float(j) / steps
		poly.append(Vector2(x0 + RAIL_BOW_LENGTH * u, rect.position.y) + out * sin(PI * u))
	for j in range(steps, -1, -1):
		var u := float(j) / steps
		poly.append(Vector2(x0 + RAIL_BOW_LENGTH * u, rect.end.y) + out * sin(PI * u))
	draw_colored_polygon(poly, ink)
