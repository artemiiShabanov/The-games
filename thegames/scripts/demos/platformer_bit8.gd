extends Demo
## Демка платформер × 8-bit, каталог `docs/specs/demos_catalog.md`: классика NES. Ямы,
## враг-ходок, монеты, чекпоинт, прыжок с переменной высотой по длине нажатия, цель флаг
## справа, две жизни вместо таймера (решение 2026-11-05). Влево, вправо, A прыжок. Уровень из
## `PlatformerLevelGen` по сиду записи игры. Рисуется в виртуальном экране 480×270 с
## увеличением ×4, спрайты пиратов 16×16, статичные облака, чиптюн-петля.
##
## Баги по флагам записи (параметры в `resources/bugs/<id>.tres`):
## `frame_drops` фризы в движении с догоном времени; `audio_stutter` заикание музыки и
## задержка звуков; `sticky_input` ввод с опозданием и залипание прыжка; `pink_placeholders`
## часть спрайтов розовыми квадратами; `through_floor` часть платформ и отдельные колонки пола
## теряют коллизию, выглядят как обычно (#15).

class Cloud:
	var x := 0.0
	var y := 0.0
	var big := false


class Walker:
	var x := 0.0
	var y := 0.0
	var dir := -1
	var from_px := 0.0
	var to_px := 0.0
	var alive := true


const VIEW := Vector2(480, 270)
const SCALE := 4
const TILE := 16
const SPRITES := "res://assets/settings/pirates/8bit/"
const MAX_FALL := 400.0
const RUN_CYCLE: Array[int] = [0, 1, 2, 1]
const DIGITS := {
	"0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"],
	"2": ["111", "001", "111", "100", "111"], "3": ["111", "001", "111", "001", "111"],
	"4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "111", "001", "111"],
	"6": ["111", "100", "111", "101", "111"], "7": ["111", "001", "001", "001", "001"],
	"8": ["111", "101", "111", "101", "111"], "9": ["111", "101", "111", "001", "111"],
}
const BG_COLOR := Color("#2F6FB5")
const HUD_INK := Color("#F4EFE6")
const HUD_SHADOW := Color("#161412")
const PINK := Color("#FF2BD6")
## Что может стать розовой заглушкой; герой и земля никогда.
const PLACEHOLDER_SLOTS: Array[String] = ["enemy", "coin", "platform", "checkpoint", "flag", "cloud"]
const MELODY := [0, null, 3, null, 7, 7, 5, 3, 2, null, 5, null, 3, 2, 0, null,
	-2, null, 2, null, 5, 5, 3, 2, 0, null, 3, null, 2, 0, -2, null]
const BASS := [-12, -12, -9, -9, -14, -14, -12, -12, -14, -14, -10, -10, -12, -12, -14, -14]
const STUTTER_SECONDS := 0.35
const STUTTER_CHUNK := 0.07

var tuning: PlatformerDemoTuning
var level: PlatformerLevel
var tex := {}
var world: Node2D
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
var move_dir := 0.0
var bot_dir := 0.0
var _bug_rng := RandomNumberGenerator.new()

# Звук.
var _music: AudioStreamPlayer
var _sfx := {}

# Баги.
var _freeze_timer := 0.0
var _freeze_left := 0.0
var _frozen := 0.0
var _stutter_timer := 0.0
var _stutter_left := 0.0
var _stutter_pos := 0.0
var _stutter_chunk := 0.0
var _axis_log: Array[Vector2] = []
var _jump_queue: Array[float] = []
var _sticky_extra := 0
var _sticky_first := true
var _pink: Dictionary = {}
var _phantom_platforms: Dictionary = {}
var _phantom_cols: Dictionary = {}


func _on_start() -> void:
	tuning = PlatformerDemoTuning.load_default()
	level = PlatformerLevelGen.generate(record.seed)
	lives = tuning.lives
	_bug_rng.seed = hash(str(record.seed, ":bugs"))
	for name in ["hero_run_0", "hero_run_1", "hero_run_2", "hero_jump", "enemy_0", "enemy_1", "coin",
			"checkpoint", "flag", "ground", "ground_inner", "platform", "cloud_small", "cloud_big"]:
		tex[name] = load(SPRITES + name + ".png")
	var container := SubViewportContainer.new()
	container.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	container.stretch = true
	container.stretch_shrink = SCALE
	container.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	container.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(container)
	move_child(container, 0)
	var viewport := SubViewport.new()
	viewport.size = Vector2i(VIEW)
	viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	viewport.snap_2d_transforms_to_pixel = true
	container.add_child(viewport)
	world = Node2D.new()
	world.draw.connect(_draw_world)
	viewport.add_child(world)

	hero = _tile_feet(level.spawn.x, level.spawn.y)
	respawn = hero
	coins_left = level.coins.duplicate()
	coins_total = coins_left.size()
	# Облака статичные, на экране, из сида.
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed, ":clouds"))
	for i in 9:
		var c := Cloud.new()
		c.x = rng.randf_range(0.0, VIEW.x - 32.0)
		c.y = rng.randf_range(TILE * 1.0, TILE * 7.5)
		c.big = rng.randf() < 0.5
		clouds.append(c)
	for e in level.enemies:
		var w := Walker.new()
		w.x = (e.x + 0.5) * TILE
		w.y = VIEW.y - e.y * TILE
		w.from_px = e.patrol_from * TILE + TILE * 0.5
		w.to_px = (e.patrol_to + 1) * TILE - TILE * 0.5
		walkers.append(w)
	_setup_audio()
	_setup_bugs()


func _setup_audio() -> void:
	_music = Sfx.player(Sfx.chiptune_loop(MELODY, BASS), -8.0)
	add_child(_music)
	_music.play()
	_sfx["jump"] = Sfx.player(Sfx.blip(520.0, 0.09, 0.35, 26.0))
	_sfx["coin"] = Sfx.player(Sfx.blip(1318.0, 0.1, 0.35, 22.0))
	_sfx["stomp"] = Sfx.player(Sfx.thud(0.14, 0.5))
	_sfx["death"] = Sfx.player(Sfx.blip(196.0, 0.4, 0.45, 6.0))
	_sfx["finish"] = Sfx.player(Sfx.blip(880.0, 0.5, 0.45, 5.0))
	for p in _sfx.values():
		add_child(p)


func _setup_bugs() -> void:
	if has_bug(&"frame_drops"):
		_freeze_timer = 1.0
	if has_bug(&"audio_stutter"):
		_stutter_timer = 1.5
	if has_bug(&"through_floor"):
		# Доля платформ без опоры, минимум одна; плюс одна фантомная колонка пола на каждые
		# ~40 тайлов вне старта, чекпоинта и флага, чтобы баг был виден в первые секунды.
		var share := _bug_param(&"through_floor", &"platform_share", 0.3)
		for i in level.platforms.size():
			if _bug_rng.randf() < share:
				_phantom_platforms[i] = true
		if _phantom_platforms.is_empty() and not level.platforms.is_empty():
			_phantom_platforms[_bug_rng.randi_range(0, level.platforms.size() - 1)] = true
		var x := 14
		while x < level.width - 14:
			var col := x + _bug_rng.randi_range(0, 24)
			var safe := absi(col - level.checkpoint.x) > 2 and absi(col - level.flag.x) > 3
			if safe and col < level.width - 14 and not level.is_pit(col) and not level.is_pit(col - 1) and not level.is_pit(col + 1):
				_phantom_cols[col] = true
			x += 40
	if has_bug(&"pink_placeholders"):
		var share := _bug_param(&"pink_placeholders", &"share", 0.35)
		var slots := PLACEHOLDER_SLOTS.duplicate()
		var count := maxi(1, int(round(slots.size() * share)))
		for i in count:
			var k := _bug_rng.randi_range(0, slots.size() - 1)
			_pink[slots[k]] = true
			slots.remove_at(k)


func _bug_param(bug_id: StringName, name: StringName, default: float) -> float:
	var catalog := BugCatalog.load_default()
	var bug := catalog.by_id(bug_id) if catalog != null else null
	return bug.param(name, default) if bug != null else default


func _tile_feet(col: int, row: int) -> Vector2:
	return Vector2((col + 0.5) * TILE, VIEW.y - row * TILE)


func _play(name: String) -> void:
	var p: AudioStreamPlayer = _sfx[name]
	if has_bug(&"audio_stutter"):
		get_tree().create_timer(_bug_param(&"audio_stutter", &"delay_ms", 350.0) / 1000.0).timeout.connect(p.play)
	else:
		p.play()


func _on_end(goal: bool) -> void:
	_music.stop()
	if goal:
		_play("finish")


# --- Ввод ------------------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	super(event)
	if not running or paused:
		return
	if GameInput.is_a(event):
		_request_jump()
		get_viewport().set_input_as_handled()
	elif event.is_action_released(GameInput.A) and vel.y < 0.0 and not has_bug(&"sticky_input"):
		vel.y *= tuning.jump_cut


## Нажатие прыжка: с багом управления уходит в очередь с задержкой.
func _request_jump() -> void:
	if has_bug(&"sticky_input"):
		_jump_queue.append(elapsed + _bug_param(&"sticky_input", &"delay_ms", 120.0) / 1000.0)
	else:
		_jump()


func _jump() -> void:
	if not grounded:
		return
	vel.y = -4.0 * tuning.jump_height / tuning.jump_time
	grounded = false
	_play("jump")
	if has_bug(&"sticky_input") and _sticky_extra == 0:
		# Первый прыжок залипает всегда, чтобы баг был виден в первые секунды, дальше по шансу.
		if _sticky_first or _bug_rng.randf() < _bug_param(&"sticky_input", &"stick_chance", 0.25):
			_sticky_extra = int(_bug_param(&"sticky_input", &"extra_presses", 2.0))
		_sticky_first = false


func _gravity() -> float:
	return 8.0 * tuning.jump_height / (tuning.jump_time * tuning.jump_time)


## Ось движения: с багом управления берётся из прошлого на delay_ms.
func _current_axis() -> float:
	var raw := bot_dir if AutoTest.bot_active() else GameInput.axis().x
	if not has_bug(&"sticky_input"):
		return raw
	_axis_log.append(Vector2(elapsed, raw))
	var delay := _bug_param(&"sticky_input", &"delay_ms", 120.0) / 1000.0
	var value := raw
	for sample in _axis_log:
		if sample.x <= elapsed - delay:
			value = sample.y
	while _axis_log.size() > 0 and _axis_log[0].x < elapsed - delay - 0.5:
		_axis_log.remove_at(0)
	return value


# --- Шаг ----------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	_update_audio_bug(delta)
	if has_bug(&"frame_drops"):
		if _freeze_left > 0.0:
			# Фриз: мир стоит, кадр не обновляется, время копится и догоняется рывком.
			_freeze_left -= delta
			_frozen += delta
			if _freeze_left <= 0.0:
				var steps := 3
				for i in steps:
					_step(_frozen / steps)
				_frozen = 0.0
				world.queue_redraw()
			return
		_freeze_timer -= delta
		if _freeze_timer <= 0.0 and move_dir != 0.0:
			var lo := _bug_param(&"frame_drops", &"freeze_ms_min", 200.0)
			var hi := _bug_param(&"frame_drops", &"freeze_ms_max", 400.0)
			_freeze_left = _bug_rng.randf_range(lo, hi) / 1000.0
			_freeze_timer = _bug_param(&"frame_drops", &"period_s", 2.5) * _bug_rng.randf_range(0.7, 1.3)
			return
	_step(delta)
	world.queue_redraw()


func _step(delta: float) -> void:
	anim_time += delta
	invuln = maxf(invuln - delta, 0.0)
	while not _jump_queue.is_empty() and _jump_queue[0] <= elapsed:
		_jump_queue.remove_at(0)
		_jump()
	move_dir = _current_axis()
	if absf(move_dir) < 0.3:
		move_dir = 0.0
	else:
		move_dir = signf(move_dir)
		facing = int(move_dir)
	vel.x = move_dir * tuning.run_speed
	vel.y = minf(vel.y + _gravity() * delta, MAX_FALL)
	_move_x(vel.x * delta)
	var was_grounded := grounded
	_move_y(vel.y * delta)
	if grounded and not was_grounded and _sticky_extra > 0:
		_sticky_extra -= 1
		_jump()
	if move_dir != 0.0 and grounded:
		run_anim += delta * tuning.run_fps
	_update_walkers(delta)
	_collect()
	if hero.y > VIEW.y + 40.0:
		_die()
	if not running:
		return
	if not checkpoint_hit and hero.x >= level.checkpoint.x * TILE:
		checkpoint_hit = true
		respawn = _tile_feet(level.checkpoint.x, level.checkpoint.y)
	if hero.x >= level.flag.x * TILE + TILE * 0.3:
		end_demo(true)
	cam_x = clampf(hero.x - VIEW.x * 0.38, 0.0, level.width * TILE - VIEW.x)
	world.position.x = -roundf(cam_x)


func _update_audio_bug(delta: float) -> void:
	if not has_bug(&"audio_stutter") or not _music.playing:
		return
	if _stutter_left > 0.0:
		_stutter_left -= delta
		_stutter_chunk -= delta
		if _stutter_chunk <= 0.0:
			_music.seek(_stutter_pos)
			_stutter_chunk = STUTTER_CHUNK
		return
	_stutter_timer -= delta
	if _stutter_timer <= 0.0:
		_stutter_left = STUTTER_SECONDS
		_stutter_pos = _music.get_playback_position()
		_stutter_chunk = STUTTER_CHUNK
		_stutter_timer = _bug_param(&"audio_stutter", &"stutter_period_s", 3.0) * _bug_rng.randf_range(0.8, 1.2)


# --- Движение и столкновения с тайлами ------------------------------------------------------

func _solid(col: int, row: int) -> bool:
	if col < 0 or col >= level.width or row < 0 or _phantom_cols.has(col):
		return false
	return row < level.ground_top(col)


func _move_x(dx: float) -> void:
	if dx == 0.0:
		return
	var half := tuning.hero_width / 2.0
	var new_x := hero.x + dx
	var edge := new_x + half if dx > 0.0 else new_x - half
	var col := int(floor(edge / TILE))
	var feet_row := int(floor((VIEW.y - hero.y + 1.0) / TILE))
	var head_row := int(floor((VIEW.y - hero.y + tuning.hero_height - 1.0) / TILE))
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
	if h > 0 and not _phantom_cols.has(col):
		out.append(VIEW.y - h * TILE)
	for i in level.platforms.size():
		var p := level.platforms[i]
		if _phantom_platforms.has(i):
			continue
		if col >= p.position.x and col < p.position.x + p.size.x:
			out.append(VIEW.y - (p.position.y + 1) * TILE)
	return out


func _update_walkers(delta: float) -> void:
	var half := tuning.hero_width / 2.0
	for w in walkers:
		if not w.alive:
			continue
		w.x += w.dir * tuning.enemy_speed * delta
		if w.x < w.from_px:
			w.x = w.from_px
			w.dir = 1
		elif w.x > w.to_px:
			w.x = w.to_px
			w.dir = -1
		if invuln > 0.0 or not running:
			continue
		var hit := absf(w.x - hero.x) < half + 6.0 and hero.y > w.y - TILE and hero.y - tuning.hero_height < w.y
		if hit:
			if vel.y > 0.0 and hero.y <= w.y - TILE * 0.5:
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
		var cy := VIEW.y - (c.y + 0.5) * TILE
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
	if lives <= 0:
		end_demo(false)
		return
	hero = respawn
	vel = Vector2.ZERO
	grounded = false
	invuln = tuning.invulnerable_seconds
	_sticky_extra = 0


func _result_caption() -> String:
	return "монеты %d из %d · падений %d · %d с" % [coins_got, coins_total, deaths, int(round(elapsed))]


## Бот: WIN бежит вправо и прыгает перед ямой, стеной и врагом, LOSE бежит не прыгая и
## теряет обе жизни.
func _bot_step(_delta: float) -> void:
	bot_dir = 1.0
	if AutoTest.bot_mode != AutoTest.BotMode.WIN:
		return
	if not grounded:
		return
	var half := tuning.hero_width / 2.0
	var ahead := int(floor((hero.x + half + 6.0) / TILE))
	var feet_row := int(round((VIEW.y - hero.y) / TILE))
	var need := level.is_pit(ahead) or level.ground_top(ahead) > feet_row
	if not need:
		for w in walkers:
			if w.alive and w.x > hero.x and w.x - hero.x < 40.0 and absf(w.y - hero.y) < 20.0:
				need = true
				break
	if need:
		_jump()


# --- Рисование виртуального экрана -----------------------------------------------------------

func _tex_or_pink(slot: String, name: String, pos: Vector2, size_px := Vector2(16, 16)) -> void:
	if _pink.has(slot):
		world.draw_rect(Rect2(pos, size_px), PINK)
	else:
		world.draw_texture(tex[name], pos)


func _draw_world() -> void:
	world.draw_rect(Rect2(cam_x, 0, VIEW.x, VIEW.y), BG_COLOR)
	for c in clouds:
		_tex_or_pink("cloud", "cloud_big" if c.big else "cloud_small", Vector2(roundf(cam_x + c.x), roundf(c.y)),
				Vector2(32, 16) if c.big else Vector2(16, 16))
	var first := maxi(int(floor(cam_x / TILE)) - 1, 0)
	var last := mini(int(ceil((cam_x + VIEW.x) / TILE)) + 1, level.width - 1)
	for col in range(first, last + 1):
		var h := level.ground_top(col)
		for row in h:
			world.draw_texture(tex["ground" if row == h - 1 else "ground_inner"], Vector2(col * TILE, VIEW.y - (row + 1) * TILE))
	for p in level.platforms:
		if p.position.x + p.size.x < first or p.position.x > last:
			continue
		for i in p.size.x:
			_tex_or_pink("platform", "platform", Vector2((p.position.x + i) * TILE, VIEW.y - (p.position.y + 1) * TILE), Vector2(16, 5))
	var bob := 1.0 if fmod(anim_time, 0.6) < 0.3 else 0.0
	for c in coins_left:
		if c.x < first or c.x > last:
			continue
		_tex_or_pink("coin", "coin", Vector2(c.x * TILE, VIEW.y - (c.y + 1) * TILE - bob))
	if _pink.has("checkpoint"):
		world.draw_rect(Rect2(level.checkpoint.x * TILE, VIEW.y - (level.checkpoint.y + 1) * TILE, 16, 16), PINK)
	else:
		world.draw_texture(tex["checkpoint"], Vector2(level.checkpoint.x * TILE, VIEW.y - (level.checkpoint.y + 1) * TILE),
				Color(1, 1, 1, 1) if checkpoint_hit else Color(1, 1, 1, 0.6))
	_tex_or_pink("flag", "flag", Vector2(level.flag.x * TILE, VIEW.y - (level.flag.y + 1) * TILE))
	var enemy_frame := "enemy_0" if fmod(anim_time * tuning.enemy_fps, 2.0) < 1.0 else "enemy_1"
	for w in walkers:
		if not w.alive or w.x < first * TILE or w.x > (last + 1) * TILE:
			continue
		if _pink.has("enemy"):
			world.draw_rect(Rect2(roundf(w.x - TILE / 2.0), roundf(w.y - TILE), 16, 16), PINK)
		else:
			_draw_sprite(tex[enemy_frame], Vector2(w.x, w.y), w.dir)
	var visible := invuln <= 0.0 or fmod(invuln, 0.2) < 0.1
	if visible and running:
		var frame := "hero_jump"
		if grounded:
			frame = "hero_run_%d" % RUN_CYCLE[int(run_anim) % RUN_CYCLE.size()] if move_dir != 0.0 else "hero_run_1"
		_draw_sprite(tex[frame], hero, facing)
	_draw_hud()


## Спрайт 16×16 ногами в `feet`, лицом по `dir`.
func _draw_sprite(t: Texture2D, feet: Vector2, dir: int) -> void:
	var pos := Vector2(roundf(feet.x - TILE / 2.0), roundf(feet.y - TILE))
	if dir >= 0:
		world.draw_texture(t, pos)
	else:
		# Отрицательная ширина отражает текстуру, позиция прямоугольника при этом не сдвигается.
		world.draw_texture_rect(t, Rect2(pos, Vector2(-TILE, TILE)), false)


func _draw_hud() -> void:
	var x0 := cam_x + 8.0
	world.draw_texture(tex["coin"], Vector2(x0 - 4.0, 2.0))
	_draw_number(Vector2(x0 + 14.0, 7.0), coins_got)
	for i in lives:
		world.draw_texture_rect_region(tex["hero_run_1"], Rect2(cam_x + VIEW.x - 8.0 - (i + 1) * 12.0, 3.0, 10.0, 8.0), Rect2(3, 1, 10, 8))


func _draw_number(pos: Vector2, n: int) -> void:
	var s := str(n)
	for i in s.length():
		var rows: Array = DIGITS[s[i]]
		for ry in rows.size():
			for rx in 3:
				if rows[ry][rx] == "1":
					var r := Rect2(pos + Vector2(i * 8 + rx * 2, ry * 2), Vector2(2, 2))
					world.draw_rect(Rect2(r.position + Vector2(1, 1), r.size), HUD_SHADOW)
					world.draw_rect(r, HUD_INK)
