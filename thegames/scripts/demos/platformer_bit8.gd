extends Demo
## Демка платформер × 8-bit, каталог `docs/specs/demos_catalog.md`: классика NES. Ямы,
## враг-ходок, монеты, чекпоинт, прыжок с переменной высотой по длине нажатия, цель флаг
## справа, две жизни вместо таймера (решение 2026-11-05). Влево, вправо, A прыжок. Уровень из
## `PlatformerLevelGen` по сиду записи игры. Дэш на B (плейтест 2026-11-06): рывок в сторону
## взгляда без гравитации, в воздухе один раз до приземления; в дэше герой уязвим, врагов не
## давит. Второй враг: попугай-летун над землёй, под ним проходят, сверху давят, снизу и сбоку
## он бьёт (плейтест 2026-11-06). Ямы шире прыжка перелетаются прыжком с дэшем. Рисуется в
## виртуальном экране внутри карточки демки с увеличением ×4 (`view`
## 416×208), три слоя: `backdrop` статичный фон (небо, солнце, море, острова, облака: на
## камеру не реагируют), `world` со сдвигом камеры, `hud` поверх. Камера целочисленная,
## привязана к округлённой позиции героя, чтобы его спрайт не дрожал; по вертикали мёртвая
## зона. Спрайты и цвета фона из сеттинга записи (`SettingDef`, #46), 16×16, чиптюн-петля.
##
## Баги по флагам записи (параметры в `resources/bugs/<id>.tres`). Общие (#44) механикой
## живут в `Demo`, демка только зовёт хуки в своих местах:
## `frame_drops` фризы в движении с догоном времени; `audio_stutter` заикание музыки и
## задержка звуков; `sticky_input` ввод с опозданием и залипание прыжка; `pink_placeholders`
## часть спрайтов розовыми квадратами; `unreachable_coins` платформы с монетами подняты выше
## прыжка; `wild_physics` (баг жанра) прыжок втрое выше и враги вдвое быстрее (#15);
## `sprite_flicker` (баг технологии 8-bit, #37) спрайты сверх `max_per_line` на одной строке
## тайлов показываются через кадр, как на приставке; `alien_palette` (#38) весь слой мира в
## сдвинутых на `hue_shift` цветах при обычном небе; `sneeze_enemies` (#38) враги гибнут от
## любого касания, без добивания.

class Cloud:
	var x := 0.0
	var y := 0.0
	var big := false


class Walker:
	var x := 0.0
	## Низ спрайта; у летуна `base` это высота полёта, `y` качается вокруг неё.
	var y := 0.0
	var base := 0.0
	var dir := -1
	var from_px := 0.0
	var to_px := 0.0
	var alive := true
	var flying := false


const SCALE := 4
## Увеличение во встроенном режиме (запись стрима в ленте).
const EMBED_SCALE := 2
const GHOST_LIFE := 0.22
## Хитбокс попугая внутри спрайта 16×16: от низа до верха в пикселях.
const FLYER_BOTTOM := 3.0
const FLYER_TOP := 12.0
const FLYER_BOB := 3.0
const GHOST_EVERY := 0.03
const DUST_LIFE := 0.3
const TILE := 16
const MAX_FALL := 400.0
const RUN_CYCLE: Array[int] = [0, 1, 2, 1]
const HUD_INK := Color("#F4EFE6")
const HUD_SHADOW := Color("#161412")
## Что может стать розовой заглушкой; герой и земля никогда.
const PLACEHOLDER_SLOTS: Array[String] = ["enemy", "coin", "platform", "checkpoint", "flag", "cloud"]
const MELODY := [0, null, 3, null, 7, 7, 5, 3, 2, null, 5, null, 3, 2, 0, null,
	-2, null, 2, null, 5, 5, 3, 2, 0, null, 3, null, 2, 0, -2, null]
const BASS := [-12, -12, -9, -9, -14, -14, -12, -12, -14, -14, -10, -10, -12, -12, -14, -14]

var tuning: PlatformerDemoTuning
var level: PlatformerLevel
## Виртуальный экран в пикселях демки: внутренность карточки, делённая на `SCALE`.
var view := Vector2(416, 208)
## Низ уровня в пикселях мира: ряд 0 стоит на `base_y`.
var base_y := 256.0
var tex := {}
var backdrop: Node2D
var world: Node2D
var hud: Node2D
var hero := Vector2.ZERO
var vel := Vector2.ZERO
var grounded := false
var facing := 1
var run_anim := 0.0
var anim_time := 0.0
var respawn := Vector2.ZERO
var coins_left: Array[Vector2i] = []
var coins_total := 0
var coins_got := 0
var deaths := 0
var lives := 2
var clouds: Array[Cloud] = []
var invuln := 0.0
var walkers: Array[Walker] = []
var checkpoint_hit := false
var cam_x := 0.0
var cam_y := 0.0
var move_dir := 0.0
var dash_left := 0.0
var dash_cooldown := 0.0
var dash_air_used := false
var _ghost_timer := 0.0
var _bot_wait := 0.0
## Призраки дэша: x, y, направление, остаток жизни.
var _ghosts: Array[Vector4] = []
## Пыль: позиция, скорость, остаток жизни.
var _dust: Array[Vector3] = []
var bot_dir := 0.0
## Сеттинг записи: спрайты и цвета фона.
var scene_set: SettingDef

# Звук.
var _music: AudioStreamPlayer
var _sfx := {}

# Баги жанра и баланса; общие баги в `Demo` (#44).
var _jump_mult := 1.0
var _enemy_mult := 1.0


func _on_start() -> void:
	tuning = PlatformerDemoTuning.load_default()
	# Сеттинг записи (#46): спрайты и фон; без своего спрайта слот берёт пиратский.
	scene_set = SettingDef.of(record.setting)
	level = PlatformerLevelGen.generate(record.seed)
	base_y = level.height * TILE
	lives = tuning.lives
	_setup_bugs()
	for name in ["hero_run_0", "hero_run_1", "hero_run_2", "hero_jump", "hero_dash", "enemy_0", "enemy_1", "parrot_0", "parrot_1", "coin",
			"checkpoint", "flag", "ground", "ground_inner", "platform", "cloud_small", "cloud_big"]:
		tex[name] = scene_set.sprite(name)
	var scale_px := EMBED_SCALE if embedded else SCALE
	view = ((embed_size if embedded else CardFrame.inner_size()) / scale_px).floor()
	var container := SubViewportContainer.new()
	# Кадр по центру области явной позицией: якоря по центру во встроенном режиме уводили его в угол.
	var area := embed_size if embedded else CardFrame.inner_size()
	container.position = ((area - view * scale_px) / 2.0).floor()
	container.size = view * scale_px
	container.custom_minimum_size = view * scale_px
	container.stretch = true
	container.stretch_shrink = scale_px
	container.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	container.mouse_filter = Control.MOUSE_FILTER_IGNORE
	screen.add_child(container)
	var viewport := SubViewport.new()
	viewport.size = Vector2i(view)
	viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	viewport.snap_2d_transforms_to_pixel = true
	container.add_child(viewport)
	backdrop = Node2D.new()
	backdrop.draw.connect(_draw_backdrop)
	viewport.add_child(backdrop)
	world = Node2D.new()
	if bug_palette() != null:
		world.material = bug_palette()
	world.draw.connect(_draw_world)
	viewport.add_child(world)
	hud = Node2D.new()
	hud.draw.connect(_draw_hud)
	viewport.add_child(hud)
	cam_y = base_y - view.y

	hero = _tile_feet(level.spawn.x, level.spawn.y)
	respawn = hero
	coins_left = level.coins.duplicate()
	coins_total = coins_left.size()
	# Облака статичные, в координатах экрана, из сида; на камеру не реагируют.
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed, ":clouds"))
	for i in 8:
		var c := Cloud.new()
		c.x = roundf(rng.randf_range(0.0, view.x - 32.0))
		c.y = roundf(rng.randf_range(TILE * 0.75, TILE * 5.5))
		c.big = rng.randf() < 0.5
		clouds.append(c)
	for e in level.enemies:
		var w := Walker.new()
		w.x = (e.x + 0.5) * TILE
		w.y = base_y - e.y * TILE
		w.base = w.y
		w.flying = e.flying
		w.from_px = e.patrol_from * TILE + TILE * 0.5
		w.to_px = (e.patrol_to + 1) * TILE - TILE * 0.5
		walkers.append(w)
	_setup_audio()


func _setup_audio() -> void:
	_music = Sfx.player(Sfx.chiptune_loop(MELODY, BASS), tuning.music_db if not embedded else -80.0)
	add_child(_music)
	bug_music = _music
	if not embedded:
		_music.play()
	_sfx["jump"] = Sfx.player(Sfx.blip(520.0, 0.09, 0.35, 26.0))
	_sfx["coin"] = Sfx.player(Sfx.blip(1318.0, 0.1, 0.35, 22.0))
	_sfx["stomp"] = Sfx.player(Sfx.thud(0.14, 0.5))
	_sfx["death"] = Sfx.player(Sfx.blip(196.0, 0.4, 0.45, 6.0))
	_sfx["finish"] = Sfx.player(Sfx.blip(880.0, 0.5, 0.45, 5.0))
	_sfx["dash"] = Sfx.player(Sfx.blip(330.0, 0.12, 0.3, 20.0))
	for p in _sfx.values():
		(p as AudioStreamPlayer).volume_db = tuning.sfx_db if not embedded else -80.0
		add_child(p)


## Баги жанра и баланса: дикая физика и монеты выше прыжка; общие ставит `Demo`.
func _setup_bugs() -> void:
	if has_bug(&"wild_physics"):
		_jump_mult = bug_param(&"wild_physics", &"jump_mult", 3.0)
		_enemy_mult = bug_param(&"wild_physics", &"enemy_speed_mult", 2.0)
	if has_bug(&"unreachable_coins"):
		# Платформы с монетами поднимаются выше прыжка вместе со своими монетами.
		var lift := int(bug_param(&"unreachable_coins", &"lift_rows", 5.0))
		for i in level.platforms.size():
			var p := level.platforms[i]
			var new_y := mini(p.position.y + lift, level.height - 3)
			var dy := new_y - p.position.y
			var moved := false
			for j in level.coins.size():
				var c := level.coins[j]
				if c.y == p.position.y + 2 and c.x >= p.position.x and c.x < p.position.x + p.size.x:
					level.coins[j] = Vector2i(c.x, c.y + dy)
					moved = true
			if moved:
				p.position.y = new_y
				level.platforms[i] = p


## Что может стать розовой заглушкой; герой и земля никогда.
func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _tile_feet(col: int, row: int) -> Vector2:
	return Vector2((col + 0.5) * TILE, base_y - row * TILE)


func _play(name: String) -> void:
	bug_play(_sfx[name])


func _on_end(goal: bool) -> void:
	_music.stop()
	if goal:
		_play("finish")


# --- Ввод ------------------------------------------------------------------------------------

func _game_input(event: InputEvent) -> void:
	if GameInput.is_a(event):
		_request_jump()
		get_viewport().set_input_as_handled()
	elif GameInput.is_b(event):
		_dash()
		get_viewport().set_input_as_handled()
	elif event.is_action_released(GameInput.A) and vel.y < 0.0 and not has_bug(&"sticky_input"):
		vel.y *= tuning.jump_cut


## Нажатие прыжка: с багом управления уходит в очередь с задержкой (`Demo.bug_press`).
func _request_jump() -> void:
	bug_press(_jump)


func _jump() -> void:
	if not grounded:
		return
	vel.y = -4.0 * tuning.jump_height * _jump_mult / tuning.jump_time
	grounded = false
	_play("jump")
	# Залипание: прыжок повторится на приземлениях (`Demo.bug_stick`).
	bug_stick()


## Дэш: в сторону взгляда, без гравитации, в воздухе один раз до приземления.
func _dash() -> void:
	if dash_left > 0.0 or dash_cooldown > 0.0 or (not grounded and dash_air_used):
		return
	dash_left = tuning.dash_time
	dash_cooldown = tuning.dash_cooldown
	if not grounded:
		dash_air_used = true
	vel.y = 0.0
	_ghost_timer = 0.0
	_play("dash")


func _gravity() -> float:
	return 8.0 * tuning.jump_height * _jump_mult / (tuning.jump_time * tuning.jump_time)


## Ось движения: с багом управления берётся из прошлого на delay_ms (`Demo.bug_axis`).
func _current_axis() -> float:
	var raw := bot_dir if bot_driven() else GameInput.axis().x
	return bug_axis(Vector2(raw, 0.0)).x


# --- Шаг ----------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	# Фризы в движении с догоном времени (`Demo.bug_frame`).
	if bug_frame(delta, move_dir != 0.0, _step):
		world.queue_redraw()


func _step(delta: float) -> void:
	anim_time += delta
	invuln = maxf(invuln - delta, 0.0)
	bug_input_tick()
	dash_cooldown = maxf(dash_cooldown - delta, 0.0)
	if dash_left > 0.0:
		dash_left -= delta
		move_dir = float(facing)
		vel.x = facing * tuning.dash_speed
		vel.y = 0.0
		_ghost_timer -= delta
		if _ghost_timer <= 0.0:
			_ghost_timer = GHOST_EVERY
			_ghosts.append(Vector4(hero.x, hero.y, facing, GHOST_LIFE))
	else:
		move_dir = _current_axis()
		if absf(move_dir) < 0.3:
			move_dir = 0.0
		else:
			move_dir = signf(move_dir)
			facing = int(move_dir)
		vel.x = move_dir * tuning.run_speed
		vel.y = minf(vel.y + _gravity() * delta, MAX_FALL)
	for i in range(_ghosts.size() - 1, -1, -1):
		_ghosts[i].w -= delta
		if _ghosts[i].w <= 0.0:
			_ghosts.remove_at(i)
	for i in range(_dust.size() - 1, -1, -1):
		_dust[i].z -= delta
		_dust[i].y -= delta * 10.0
		if _dust[i].z <= 0.0:
			_dust.remove_at(i)
	_move_x(vel.x * delta)
	var was_grounded := grounded
	_move_y(vel.y * delta)
	if grounded:
		dash_air_used = false
	if grounded and not was_grounded and bug_take_stick():
		_jump()
	if move_dir != 0.0 and grounded and dash_left <= 0.0:
		run_anim += delta * tuning.run_fps
	_update_walkers(delta)
	_collect()
	if hero.y > base_y + 40.0:
		_die()
	if not running:
		return
	if not checkpoint_hit and hero.x >= level.checkpoint.x * TILE:
		checkpoint_hit = true
		respawn = _tile_feet(level.checkpoint.x, level.checkpoint.y)
	if hero.x >= level.flag.x * TILE + TILE * 0.3:
		end_demo(true)
	_update_camera()


## Камера целочисленная и привязана к округлённому герою: его экранная позиция не дрожит.
## По вертикали мёртвая зона: камера едет, только когда ноги героя выходят за поля.
func _update_camera() -> void:
	cam_x = clampf(roundf(hero.x) - roundf(view.x * 0.38), 0.0, level.width * TILE - view.x)
	var feet_screen := hero.y - cam_y
	if feet_screen < tuning.cam_top_margin:
		cam_y = hero.y - tuning.cam_top_margin
	elif feet_screen > view.y - tuning.cam_bottom_margin:
		cam_y = hero.y - (view.y - tuning.cam_bottom_margin)
	cam_y = clampf(roundf(cam_y), 0.0, base_y - view.y)
	world.position = Vector2(-cam_x, -cam_y)
	hud.queue_redraw()


func _solid(col: int, row: int) -> bool:
	if col < 0 or col >= level.width or row < 0:
		return false
	return row < level.ground_top(col)


func _move_x(dx: float) -> void:
	if dx == 0.0:
		return
	var half := tuning.hero_width / 2.0
	var new_x := hero.x + dx
	var edge := new_x + half if dx > 0.0 else new_x - half
	var col := int(floor(edge / TILE))
	var feet_row := int(floor((base_y - hero.y + 1.0) / TILE))
	var head_row := int(floor((base_y - hero.y + tuning.hero_height - 1.0) / TILE))
	for row in range(feet_row, head_row + 1):
		if _solid(col, row):
			new_x = (col * TILE - half - 0.01) if dx > 0.0 else ((col + 1) * TILE + half + 0.01)
			break
	hero.x = clampf(new_x, half, level.width * TILE - half)


func _move_y(dy: float) -> void:
	var half := tuning.hero_width / 2.0
	var old_y := hero.y
	var new_y := hero.y + dy
	if dy >= 0.0:
		var best := INF
		for col in [int(floor((hero.x - half + 1.0) / TILE)), int(floor((hero.x + half - 1.0) / TILE))]:
			for top in _surface_tops(col):
				if old_y <= top + 0.01 and new_y >= top:
					best = minf(best, top)
		if best < INF:
			hero.y = best
			vel.y = 0.0
			grounded = true
			return
		grounded = false
	hero.y = new_y


## Верх поверхностей колонки в пикселях: земля и платформы.
func _surface_tops(col: int) -> Array[float]:
	var out: Array[float] = []
	if col < 0 or col >= level.width:
		return out
	var h := level.ground_top(col)
	if h > 0:
		out.append(base_y - h * TILE)
	for p in level.platforms:
		if col >= p.position.x and col < p.position.x + p.size.x:
			out.append(base_y - (p.position.y + 1) * TILE)
	return out


func _update_walkers(delta: float) -> void:
	var half := tuning.hero_width / 2.0
	for w in walkers:
		if not w.alive:
			continue
		w.x += w.dir * tuning.enemy_speed * _enemy_mult * (tuning.flyer_speed_mult if w.flying else 1.0) * delta
		if w.flying:
			w.y = w.base + sin(anim_time * 4.0 + w.base) * FLYER_BOB
		if w.x < w.from_px:
			w.x = w.from_px
			w.dir = 1
		elif w.x > w.to_px:
			w.x = w.to_px
			w.dir = -1
		if invuln > 0.0 or not running:
			continue
		# Ходок односторонний, как платформа под ним: снизу в подъёме герой проходит сквозь.
		# Попугай нет: в него можно впрыгнуть снизу.
		if not w.flying and vel.y < 0.0 and hero.y > w.y:
			continue
		var top: float = w.y - (FLYER_TOP if w.flying else float(TILE))
		var bottom: float = w.y - (FLYER_BOTTOM if w.flying else 0.0)
		var hit := absf(w.x - hero.x) < half + 3.0 and hero.y > top and hero.y - tuning.hero_height < bottom
		if hit:
			# Ноги героя выше ног врага: добивание, и в подъёме тоже (прощающие хитбоксы). В дэше
			# герой уязвим и не давит (плейтест 2026-11-06). Баг «чих»: гибнет от любого касания.
			if has_bug(&"sneeze_enemies"):
				w.alive = false
				_play("stomp")
			elif hero.y <= bottom - TILE * 0.25 and dash_left <= 0.0:
				w.alive = false
				vel.y = -tuning.stomp_bounce
				grounded = false
				_play("stomp")
			else:
				_die()


func _collect() -> void:
	var half := tuning.hero_width / 2.0
	var i := coins_left.size() - 1
	while i >= 0:
		var c := coins_left[i]
		var cx := (c.x + 0.5) * TILE
		var cy := base_y - (c.y + 0.5) * TILE
		if absf(cx - hero.x) < half + 5.0 and cy > hero.y - tuning.hero_height - 4.0 and cy < hero.y + 4.0:
			coins_left.remove_at(i)
			coins_got += 1
			_play("coin")
		i -= 1


func _die() -> void:
	if not running:
		return
	deaths += 1
	lives -= 1
	_play("death")
	if AutoTest.enabled and not embedded:
		var near: Array[String] = []
		for w in walkers:
			if w.alive and absf(w.x - hero.x) < 48.0:
				near.append("(%.2f,%.2f%s)" % [w.x / TILE, (base_y - w.y) / TILE, "✈" if w.flying else ""])
		AutoTest.note("platformer: смерть %d в колонке %.2f ряд %.2f, grounded=%s vel=%s dash=%.2f air_used=%s, враги рядом %s" % [
				deaths, hero.x / TILE, (base_y - hero.y) / TILE, grounded, vel, dash_left, dash_air_used, near])
	if lives <= 0:
		end_demo(false)
		return
	hero = respawn
	vel = Vector2.ZERO
	grounded = false
	invuln = tuning.invulnerable_seconds
	bug_clear_stick()
	dash_left = 0.0
	_ghosts.clear()
	_update_camera()


func _result_caption() -> String:
	return "монеты %d из %d · падений %d · %d с" % [coins_got, coins_total, deaths, int(round(elapsed))]


## Бот: WIN бежит вправо, прыгает перед ямой, стеной и врагом, а падая над ямой делает дэш;
## LOSE бежит вправо, перепрыгивает только ступеньки и теряет обе жизни в ямах и врагах.
func _bot_step(delta: float) -> void:
	bot_dir = 1.0
	var half := tuning.hero_width / 2.0
	var ahead := int(floor((hero.x + half + 6.0) / TILE))
	var feet_row := int(round((base_y - hero.y) / TILE))
	if active_bot_mode() != AutoTest.BotMode.WIN:
		if grounded and not level.is_pit(ahead) and level.ground_top(ahead) > feet_row:
			_jump()
		return
	if not grounded:
		if vel.y > 0.0 and dash_left <= 0.0 and not dash_air_used:
			var below := int(floor(hero.x / TILE))
			var feet := int(floor((base_y - hero.y) / TILE))
			var landing := false
			for sy in level.surfaces_at(below):
				if sy <= feet:
					landing = true
			# Падение в яму это верная смерть, враг на той стороне только возможная.
			if not landing:
				_dash()
		return
	var step_up := not level.is_pit(ahead) and level.ground_top(ahead) > feet_row
	var need := level.is_pit(ahead) or step_up
	if not need:
		for w in walkers:
			if w.alive and not w.flying and w.x > hero.x and w.x - hero.x < 56.0 and absf(w.y - hero.y) < 20.0:
				need = true
				break
	if step_up and _bot_wait < 2.0:
		# Перед ступенькой: если в месте приземления ходок, подождать, пока уйдёт (не дольше
		# двух секунд). Выше по дуге прыжка ходок не страшен.
		var land_y := base_y - level.ground_top(ahead) * TILE
		for w in walkers:
			if w.alive and not w.flying and w.x - hero.x > 70.0 and w.x - hero.x < 112.0 and absf(w.y - land_y) < 20.0:
				bot_dir = 0.0
				_bot_wait += delta
				return
	if need:
		_bot_wait = 0.0
		_jump()


# --- Рисование виртуального экрана -----------------------------------------------------------

func _tex_or_pink(slot: String, name: String, pos: Vector2, size_px := Vector2(16, 16), canvas: CanvasItem = null) -> void:
	if canvas == null:
		canvas = world
	if is_pink(slot):
		canvas.draw_rect(Rect2(pos, size_px), PINK)
	else:
		canvas.draw_texture(tex[name], pos)


## Статичный фон в координатах экрана из цветов сеттинга (#46): полосы неба, светило, полоса
## горизонта с бликами, силуэты на горизонте, облака.
func _draw_backdrop() -> void:
	var horizon := roundf(view.y * 0.72)
	var bands := scene_set.sky_bands
	var band_h := horizon / bands.size()
	for i in bands.size():
		backdrop.draw_rect(Rect2(0, roundf(i * band_h), view.x, ceilf(band_h) + 1), bands[i])
	# Солнце: круг из квадратов справа сверху.
	var sun := Vector2(view.x - 56.0, 30.0)
	for r in [[Vector2(-6, -12), Vector2(12, 24)], [Vector2(-12, -6), Vector2(24, 12)], [Vector2(-10, -10), Vector2(20, 20)]]:
		backdrop.draw_rect(Rect2(sun + r[0], r[1]), scene_set.sun)
	# Острова на горизонте.
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed, ":islands"))
	var x := -8.0
	while x < view.x:
		var w := rng.randf_range(28.0, 64.0)
		var h := rng.randf_range(6.0, 18.0)
		var steps := 4
		for i in steps:
			var k := float(i) / steps
			var sw := w * (1.0 - k * 0.8)
			backdrop.draw_rect(Rect2(roundf(x + (w - sw) / 2.0), roundf(horizon - h * (i + 1) / steps), roundf(sw), ceilf(h / steps) + 1),
					scene_set.silhouette_dark if i % 2 == 0 else scene_set.silhouette)
		x += w + rng.randf_range(10.0, 50.0)
	# Море до низа экрана с полосками бликов.
	backdrop.draw_rect(Rect2(0, horizon, view.x, view.y - horizon), scene_set.horizon)
	for i in 14:
		var y := horizon + 3 + i * 6
		var bx := fmod(i * 37.0, view.x - 24.0)
		backdrop.draw_rect(Rect2(bx, y, 8 + (i % 3) * 6, 1), scene_set.horizon_light)
	for c in clouds:
		_tex_or_pink("cloud", "cloud_big" if c.big else "cloud_small", Vector2(c.x, c.y),
				Vector2(32, 16) if c.big else Vector2(16, 16), backdrop)


## Баг мерцания: спрайт на строке тайлов сверх лимита виден только через кадр.
func _flicker_hidden(y_px: float) -> bool:
	return flicker_hidden(int(floor(y_px / TILE)))


func _draw_world() -> void:
	flicker_reset()
	var first := maxi(int(floor(cam_x / TILE)) - 1, 0)
	var last := mini(int(ceil((cam_x + view.x) / TILE)) + 1, level.width - 1)
	for col in range(first, last + 1):
		var h := level.ground_top(col)
		for row in h:
			world.draw_texture(tex["ground" if row == h - 1 else "ground_inner"], Vector2(col * TILE, base_y - (row + 1) * TILE))
	for p in level.platforms:
		if p.position.x + p.size.x < first or p.position.x > last:
			continue
		for i in p.size.x:
			_tex_or_pink("platform", "platform", Vector2((p.position.x + i) * TILE, base_y - (p.position.y + 1) * TILE), Vector2(16, 5))
	var bob := 1.0 if fmod(anim_time, 0.6) < 0.3 else 0.0
	for c in coins_left:
		if c.x < first or c.x > last:
			continue
		if _flicker_hidden(base_y - (c.y + 0.5) * TILE):
			continue
		_tex_or_pink("coin", "coin", Vector2(c.x * TILE, base_y - (c.y + 1) * TILE - bob))
	if is_pink("checkpoint"):
		world.draw_rect(Rect2(level.checkpoint.x * TILE, base_y - (level.checkpoint.y + 1) * TILE, 16, 16), PINK)
	else:
		world.draw_texture(tex["checkpoint"], Vector2(level.checkpoint.x * TILE, base_y - (level.checkpoint.y + 1) * TILE),
				Color(1, 1, 1, 1) if checkpoint_hit else Color(1, 1, 1, 0.6))
	_tex_or_pink("flag", "flag", Vector2(level.flag.x * TILE, base_y - (level.flag.y + 1) * TILE))
	var enemy_frame := "enemy_0" if fmod(anim_time * tuning.enemy_fps, 2.0) < 1.0 else "enemy_1"
	var parrot_frame := "parrot_0" if fmod(anim_time * tuning.flyer_fps, 2.0) < 1.0 else "parrot_1"
	for w in walkers:
		if not w.alive or w.x < first * TILE or w.x > (last + 1) * TILE:
			continue
		if _flicker_hidden(w.y - TILE / 2.0):
			continue
		if is_pink("enemy"):
			world.draw_rect(Rect2(roundf(w.x - TILE / 2.0), roundf(w.y - TILE), 16, 16), PINK)
		else:
			_draw_sprite(tex[parrot_frame if w.flying else enemy_frame], Vector2(w.x, w.y), w.dir)
	for d in _dust:
		var k := d.z / DUST_LIFE
		world.draw_rect(Rect2(roundf(d.x) - 1.0, roundf(d.y) - 1.0, 2.0 + roundf(2.0 * (1.0 - k)), 2.0), Color(HUD_INK, 0.8 * k))
	for g in _ghosts:
		_draw_sprite(tex["hero_dash"], Vector2(g.x, g.y), int(g.z), Color(1, 1, 1, 0.45 * g.w / GHOST_LIFE))
	var visible := invuln <= 0.0 or fmod(invuln, 0.2) < 0.1
	if visible and running and _flicker_hidden(hero.y - TILE / 2.0):
		visible = false
	if visible and running:
		var frame := "hero_jump"
		if dash_left > 0.0:
			frame = "hero_dash"
		elif grounded:
			frame = "hero_run_%d" % RUN_CYCLE[int(run_anim) % RUN_CYCLE.size()] if move_dir != 0.0 else "hero_run_1"
		_draw_sprite(tex[frame], hero, facing)


## Спрайт 16×16 ногами в `feet`, лицом по `dir`.
func _draw_sprite(t: Texture2D, feet: Vector2, dir: int, tint := Color.WHITE) -> void:
	var pos := Vector2(roundf(feet.x) - TILE / 2.0, roundf(feet.y) - TILE)
	if dir >= 0:
		world.draw_texture(t, pos, tint)
	else:
		# Отрицательная ширина отражает текстуру, позиция прямоугольника при этом не сдвигается.
		world.draw_texture_rect(t, Rect2(pos, Vector2(-TILE, TILE)), false, tint)


## HUD в координатах экрана: монеты слева, жизни справа.
func _draw_hud() -> void:
	hud.draw_texture(tex["coin"], Vector2(4.0, 2.0))
	_draw_number(Vector2(22.0, 7.0), coins_got)
	for i in lives:
		hud.draw_texture_rect_region(tex["hero_run_1"], Rect2(view.x - 8.0 - (i + 1) * 12.0, 3.0, 10.0, 8.0), Rect2(3, 1, 10, 8))


func _draw_number(pos: Vector2, n: int) -> void:
	draw_pixel_text(hud, pos, str(n), HUD_INK, HUD_SHADOW)
