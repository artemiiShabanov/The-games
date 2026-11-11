extends Demo
## Демка платформер × ASCII (#90), каталог `docs/specs/demos_catalog.md`: вид сбоку на текстовом
## экране (`Demo.ascii_screen`, 104×26). Герой, враги и монеты глифами сеттинга, земля и
## платформы `=`. Всё по клеткам: шаг вбок раз в `step_seconds`, прыжок на две клетки вверх с
## зависанием на вершине, падение по клетке. Уровень в три экрана (312 колонок) из того же
## генератора, что у 8-bit (`PlatformerLevelGen`), со своими числами
## (`platformer_ascii_gen.tres`): прыжок на 4 колонки вровень, на 3 вверх, без рывка. Экран не
## едет, а перелистывается, когда герой уходит за край. Две жизни, чекпоинт посередине, цель флаг
## справа. Влево, вправо, A прыжок. Монету берёт клетка героя или клетка над ним (прыжок на две
## клетки не дотянулся бы до дуги монет над ямой). Ходока давят, упав на него сверху, иначе он
## убивает. Звук пищалкой.
##
## Баги по флагам записи: общие через хуки `Demo` (фризы, заикание пищалки, запоздалый ввод и
## залипание прыжка, розовые «?», чужая палитра, `glyph_mixup` технологии ASCII);
## `wild_physics` прыжок втрое выше и враги вдвое быстрее; `unreachable_coins` платформы с
## монетами подняты выше прыжка; `sneeze_enemies` враги гибнут от любого касания.

const HUD_ROW := 0
## Мир идёт фиксированными тиками: шаги по клеткам не зависят от частоты кадров, а бот решает
## внутри тика, между вертикалью и шагом вбок, как игрок с зажатой клавишей.
const TICK := 1.0 / 120.0
## Ряд экрана под нулевым рядом уровня; ниже пустой ряд и легенда.
const PLAY_BOTTOM_FROM_END := 3
const PLACEHOLDER_SLOTS: Array[String] = ["enemy", "bonus", "platform", "finish", "prop_a", "prop_b"]
const LEGEND: Array[StringName] = [&"hero", &"enemy", &"bonus", &"finish"]
const MELODY := [0, null, 3, null, 7, 7, 5, 3, 2, null, 5, null, 3, 2, 0, null,
	-2, null, 2, null, 5, 5, 3, 2, 0, null, 3, null, 2, 0, -2, null]

class Walker:
	var x := 0
	var y := 0
	var dir := -1
	var from_x := 0
	var to_x := 0
	var alive := true


var tuning: PlatformerAsciiTuning
var gen: PlatformerGenTuning
var level: PlatformerLevel
## Клетка героя: колонка уровня и ряд снизу (стоит на ряду `y`, под ним твёрдое).
var hero := Vector2i.ZERO
var respawn := Vector2i.ZERO
var grounded := true
## Прыжок: сколько клеток ещё вверх и сколько тиков висеть.
var rise := 0
var hang := 0
var falling := false
var move_dir := 0
var walkers: Array[Walker] = []
var coins_left: Array[Vector2i] = []
var coins_total := 0
var coins_got := 0
var lives := 2
var deaths := 0
var checkpoint_hit := false
var invuln := 0.0
var props: Dictionary[int, bool] = {}
var bot_dir := 0
var _acc := 0.0
var _step_timer := 0.0
var _v_timer := 0.0
var _enemy_timer := 0.0
var _dying := 0.0
var _bot_wait := 0.0
var _jump_rows := 2
var _enemy_mult := 1.0
var _play_bottom := 23
var _music: AudioStreamPlayer
var _sfx: Dictionary[String, AudioStreamPlayer] = {}


func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _on_start() -> void:
	tuning = PlatformerAsciiTuning.load_default()
	gen = PlatformerAsciiTuning.gen()
	level = PlatformerLevelGen.generate(record.seed, gen)
	lives = tuning.lives
	_jump_rows = tuning.jump_rows
	_setup_bugs()
	ascii_screen()
	_play_bottom = ascii.rows - PLAY_BOTTOM_FROM_END
	hero = Vector2i(level.spawn.x, level.ground_top(level.spawn.x))
	respawn = hero
	coins_left = level.coins.duplicate()
	coins_total = coins_left.size()
	for e in level.enemies:
		var w := Walker.new()
		w.x = e.x
		w.y = e.y
		w.from_x = e.patrol_from
		w.to_x = e.patrol_to
		walkers.append(w)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed, ":props"))
	for x in level.width:
		if not level.is_pit(x) and x > level.spawn.x + 2 and x < level.flag.x - 2 and rng.randf() < tuning.prop_chance:
			props[x] = true
	_setup_audio()
	_redraw()


func _setup_bugs() -> void:
	if has_bug(&"wild_physics"):
		_jump_rows = int(round(tuning.jump_rows * bug_param(&"wild_physics", &"jump_mult", 3.0)))
		_enemy_mult = bug_param(&"wild_physics", &"enemy_speed_mult", 2.0)
	if has_bug(&"unreachable_coins"):
		# Платформы с монетами поднимаются выше прыжка вместе со своими монетами.
		var lift := int(bug_param(&"unreachable_coins", &"lift_rows", 5.0))
		for i in level.platforms.size():
			var p := level.platforms[i]
			var new_y := mini(p.position.y + lift, level.height + 4)
			var dy := new_y - p.position.y
			var moved := false
			for j in level.coins.size():
				var c := level.coins[j]
				if c.y == p.position.y + gen.platform_coin_lift and c.x >= p.position.x and c.x < p.position.x + p.size.x:
					level.coins[j] = Vector2i(c.x, c.y + dy)
					moved = true
			if moved:
				# Ходоки на этой платформе едут вместе с ней, а не висят в воздухе.
				for e in level.enemies:
					if e.y == p.position.y + 1 and e.patrol_from >= p.position.x and e.patrol_to < p.position.x + p.size.x:
						e.y += dy
				p.position.y = new_y
				level.platforms[i] = p


func _setup_audio() -> void:
	var quiet := embedded
	_music = Sfx.music(Sfx.beeper_loop(MELODY, 160.0), -80.0 if quiet else tuning.music_db)
	add_child(_music)
	bug_music = _music
	if not quiet:
		_music.play()
	_sfx["jump"] = Sfx.player(Sfx.beep(440.0, 0.08, 0.3, 880.0))
	_sfx["coin"] = Sfx.player(Sfx.beep(988.0, 0.06, 0.25, 1976.0))
	_sfx["stomp"] = Sfx.player(Sfx.beep(220.0, 0.08, 0.3, 110.0))
	_sfx["death"] = Sfx.player(Sfx.beep(440.0, 0.4, 0.3, 110.0))
	_sfx["finish"] = Sfx.player(Sfx.beep(523.0, 0.35, 0.3, 1046.0))
	for p in _sfx.values():
		p.volume_db = -80.0 if quiet else tuning.sfx_db
		add_child(p)


func _play(name: String) -> void:
	bug_play(_sfx[name])


func _on_end(goal: bool) -> void:
	_music.stop()
	if goal:
		_play("finish")


# --- Ввод -------------------------------------------------------------------------------------

func _game_input(event: InputEvent) -> void:
	if GameInput.is_a(event):
		bug_press(_jump)
		get_viewport().set_input_as_handled()


func _jump() -> void:
	if not grounded or _dying > 0.0:
		return
	grounded = false
	falling = false
	rise = _jump_rows
	hang = tuning.hang_ticks
	_v_timer = 0.0
	_play("jump")
	bug_stick()


func _axis() -> int:
	var raw := float(bot_dir) if bot_driven() else GameInput.axis().x
	var v := bug_axis(Vector2(raw, 0.0)).x
	return 0 if absf(v) < 0.3 else int(signf(v))


# --- Шаг --------------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	if bug_frame(delta, move_dir != 0 or not grounded, _step):
		_redraw()


func _step(dt: float) -> void:
	_acc += dt
	while _acc >= TICK and running:
		_acc -= TICK
		_tick(TICK)


func _tick(dt: float) -> void:
	bug_input_tick()
	invuln = maxf(invuln - dt, 0.0)
	if _dying > 0.0:
		_dying -= dt
		if _dying <= 0.0:
			_respawn()
		return
	move_dir = _axis()
	# Вертикаль: подъём, зависание, падение по клетке.
	_v_timer -= dt
	while _v_timer <= 0.0 and running:
		_v_timer += tuning.vtick
		_vertical()
	if bot_driven():
		_bot_think()
		move_dir = _axis()
	# Шаг вбок.
	_step_timer -= dt
	if move_dir == 0:
		_step_timer = minf(_step_timer, 0.0)
	elif _step_timer <= 0.0:
		_step_timer += tuning.step_seconds
		_horizontal(move_dir)
	_enemy_timer -= dt
	if _enemy_timer <= 0.0:
		_enemy_timer += tuning.enemy_step / _enemy_mult
		_move_walkers()
	_touch_walkers()
	_collect()
	if not running or _dying > 0.0:
		return
	if not checkpoint_hit and hero.x >= level.checkpoint.x:
		checkpoint_hit = true
		respawn = Vector2i(level.checkpoint.x, level.ground_top(level.checkpoint.x))
	if hero.x >= level.flag.x:
		end_demo(true)


func _vertical() -> void:
	if grounded:
		if not _on_surface(hero):
			grounded = false
			falling = true
		return
	if rise > 0:
		rise -= 1
		hero.y += 1
		return
	if hang > 0:
		hang -= 1
		return
	falling = true
	# Падение: на ходока сверху давит его, на поверхность приземляет.
	for w in walkers:
		if w.alive and w.x == hero.x and w.y == hero.y - 1:
			_stomp(w)
			return
	if _on_surface(hero):
		_land()
		return
	hero.y -= 1
	if _on_surface(hero):
		_land()
	elif hero.y < -1:
		_die()


func _land() -> void:
	grounded = true
	falling = false
	if bug_take_stick():
		_jump()


func _horizontal(dir: int) -> void:
	var nx := hero.x + dir
	if nx < 0 or nx >= level.width:
		return
	var top := level.ground_top(nx)
	if hero.y < top:
		# Край уступа на клетку выше в воздухе: герой забирается на него (прощающий прыжок).
		if not grounded and rise == 0 and hero.y == top - 1:
			hero = Vector2i(nx, top)
			_land()
		return
	hero.x = nx


## Стоит ли клетка на твёрдом: земля под ней или платформа ровно под ней.
func _on_surface(c: Vector2i) -> bool:
	if c.y >= 0 and c.y == level.ground_top(c.x) and not level.is_pit(c.x):
		return true
	for p in level.platforms:
		if c.y == p.position.y + 1 and c.x >= p.position.x and c.x < p.position.x + p.size.x:
			return true
	return false


func _move_walkers() -> void:
	for w in walkers:
		if not w.alive:
			continue
		w.x += w.dir
		if w.x <= w.from_x:
			w.x = w.from_x
			w.dir = 1
		elif w.x >= w.to_x:
			w.x = w.to_x
			w.dir = -1


func _touch_walkers() -> void:
	if invuln > 0.0 or _dying > 0.0 or not running:
		return
	for w in walkers:
		if not w.alive or w.x != hero.x or w.y != hero.y:
			continue
		# В воздухе касание давит ходока (прощающие хитбоксы, как в 8-bit); на земле убивает.
		if has_bug(&"sneeze_enemies") or not grounded:
			_stomp(w)
		else:
			_die()
		return


func _stomp(w: Walker) -> void:
	w.alive = false
	_play("stomp")
	grounded = false
	falling = false
	rise = 1
	hang = 1


func _collect() -> void:
	for i in range(coins_left.size() - 1, -1, -1):
		var c := coins_left[i]
		if c.x == hero.x and (c.y == hero.y or c.y == hero.y + 1):
			coins_left.remove_at(i)
			coins_got += 1
			_play("coin")


func _die() -> void:
	if not running or _dying > 0.0:
		return
	deaths += 1
	lives -= 1
	_play("death")
	if AutoTest.enabled and not embedded:
		var near: Array[String] = []
		for w in walkers:
			if w.alive and absi(w.x - hero.x) <= 4:
				near.append("(%d,%d→%d)" % [w.x, w.y, w.dir])
		var cols: Array[int] = []
		for x in range(hero.x - 3, hero.x + 6):
			cols.append(level.ground_top(x))
		AutoTest.note("platformer ascii: смерть %d в (%d,%d), rise %d hang %d falling %s, земля %d..%d %s, враги %s" % [
				deaths, hero.x, hero.y, rise, hang, falling, hero.x - 3, hero.x + 5, cols, near])
	bug_clear_stick()
	if lives <= 0:
		_redraw()
		end_demo(false)
		return
	_dying = tuning.death_pause


func _respawn() -> void:
	hero = respawn
	grounded = true
	falling = false
	rise = 0
	hang = 0
	invuln = tuning.invulnerable_seconds


func _result_caption() -> String:
	return "%s %d из %d · падений %d · %d с" % [ascii_set.ascii_names.get(&"bonus", "монеты"), coins_got,
			coins_total, deaths, int(round(elapsed))]


func _result_title(goal: bool) -> String:
	return "добежал" if goal else "не добежал"


# --- Бот --------------------------------------------------------------------------------------

## WIN бежит вправо и прыгает с края, перед ступенькой и ходоком (ждёт, если ходок на месте
## приземления на ступеньку); LOSE прыгает только на ступеньки и теряет жизни в ямах и врагах.
func _bot_step(_delta: float) -> void:
	pass


## Решение бота внутри тика мира (`_tick`). В воздухе WIN перестаёт лететь вперёд, если иначе
## упадёт в яму (как игрок, отпустивший стрелку над опорой); на земле прыгает, только если
## прыжок кончается на опоре.
func _bot_think() -> void:
	bot_dir = 1
	if _dying > 0.0:
		return
	var win := active_bot_mode() == AutoTest.BotMode.WIN
	if not grounded:
		if win and not _lands_safe(1, false) and _lands_safe(0, false):
			bot_dir = 0
		return
	var ahead := hero.x + 1
	var step_up := not level.is_pit(ahead) and level.ground_top(ahead) > hero.y
	if not win:
		if step_up:
			_jump()
		return
	# Край: впереди нет опоры на этом ряду (яма, обрыв платформы, ступенька вниз).
	var edge := not _on_surface(Vector2i(ahead, hero.y)) and level.ground_top(ahead) <= hero.y
	var foe := false
	for w in walkers:
		if w.alive and w.y == hero.y and (w.x > hero.x and w.x - hero.x <= 3 or w.x == hero.x - 1 and w.dir > 0):
			foe = true
	if step_up and _bot_wait < 2.0:
		var top := level.ground_top(ahead)
		for w in walkers:
			if w.alive and w.y == top and w.x >= ahead and w.x <= ahead + 3:
				bot_dir = 0
				_bot_wait += TICK
				return
	if not (edge or step_up or foe):
		return
	_bot_wait = 0.0
	if _lands_safe(1, true) or not _lands_safe(1, false):
		_jump()


## Куда приведёт движение без врагов: прыжок сейчас (`jump`) или нет, стрелка `dir`. true, если
## герой встанет на опору, false, если упадёт за низ уровня.
func _lands_safe(dir: int, jump: bool) -> bool:
	var c := hero
	var g := grounded
	var r := rise
	var h := hang
	var vt := _v_timer
	var st := _step_timer
	if jump:
		g = false
		r = _jump_rows
		h = tuning.hang_ticks
		vt = 0.0
	var moved := false
	var start_air := jump or not grounded
	for i in int(4.0 / TICK):
		vt -= TICK
		while vt <= 0.0:
			vt += tuning.vtick
			if g:
				if not _on_surface(c):
					g = false
			elif r > 0:
				r -= 1
				c.y += 1
			elif h > 0:
				h -= 1
			elif _on_surface(c):
				g = true
			else:
				c.y -= 1
				if _on_surface(c):
					g = true
				elif c.y < -1:
					return false
		if g and i > 0 and (start_air or moved or dir == 0):
			return true
		st -= TICK
		if dir != 0 and st <= 0.0:
			st += tuning.step_seconds
			var nx := c.x + dir
			if nx >= 0 and nx < level.width:
				var top := level.ground_top(nx)
				if c.y >= top:
					c.x = nx
					moved = true
				elif not g and r == 0 and c.y == top - 1:
					c = Vector2i(nx, top)
					g = true
	return true


# --- Рисование --------------------------------------------------------------------------------

func _row(y: int) -> int:
	return _play_bottom - y


func _redraw() -> void:
	ascii.clear()
	var cols := ascii.cols
	var screen_i := clampi(hero.x / cols, 0, maxi(0, (level.width - 1) / cols))
	var x0 := screen_i * cols
	for sx in cols:
		var x := x0 + sx
		if x >= level.width:
			break
		var top := level.ground_top(x)
		for y in range(0, top):
			var r := _row(y)
			if r > HUD_ROW and r <= _play_bottom:
				put_slot(sx, r, &"ground")
		if props.has(x):
			put_slot(sx, _row(top), &"prop_b")
	for p in level.platforms:
		for i in p.size.x:
			var x := p.position.x + i - x0
			if x >= 0 and x < cols and _row(p.position.y) > HUD_ROW:
				put_slot(x, _row(p.position.y), &"platform")
	for c in coins_left:
		if c.x >= x0 and c.x < x0 + cols and _row(c.y) > HUD_ROW:
			put_slot(c.x - x0, _row(c.y), &"bonus")
	var cp := level.checkpoint
	if cp.x >= x0 and cp.x < x0 + cols:
		put_slot(cp.x - x0, _row(cp.y), &"prop_a")
		if checkpoint_hit:
			ascii.put(cp.x - x0, _row(cp.y), ascii.at(cp.x - x0, _row(cp.y)), 2)
	if level.flag.x >= x0 and level.flag.x < x0 + cols:
		put_slot(level.flag.x - x0, _row(level.flag.y), &"finish")
	for w in walkers:
		if w.alive and w.x >= x0 and w.x < x0 + cols:
			put_slot(w.x - x0, _row(w.y), &"enemy")
	var blink := invuln > 0.0 and int(elapsed * 10.0) % 2 == 0
	var hr := _row(hero.y)
	if hr > HUD_ROW and hr <= _play_bottom and not blink:
		if _dying > 0.0 or (not running and not reached):
			ascii.put(hero.x - x0, hr, "x", 4)
		else:
			put_slot(hero.x - x0, hr, &"hero")
	_draw_hud(screen_i)
	ascii_legend(ascii.rows - 1, LEGEND)


func _draw_hud(screen_i: int) -> void:
	for i in maxi(lives, 0):
		put_slot(1 + i * 2, HUD_ROW, &"hero")
	put_slot(8, HUD_ROW, &"bonus")
	ascii.text(10, HUD_ROW, "%d/%d" % [coins_got, coins_total], 1)
	var s := "ЭКРАН %d/%d" % [screen_i + 1, (level.width + ascii.cols - 1) / ascii.cols]
	ascii.text_center(HUD_ROW, s, 3)
	ascii.text(ascii.cols - 11, HUD_ROW, "ВРЕМЯ %3d" % int(elapsed), 1)
