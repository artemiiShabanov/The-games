extends Demo
## Демка платформер × 8-bit, каталог `docs/specs/demos_catalog.md`: классика NES. Ямы,
## враг-ходок, монеты, чекпоинт, прыжок с переменной высотой по длине нажатия, цель флаг
## справа, две жизни вместо таймера (решение 2026-11-05). Влево, вправо, A прыжок. Уровень из `PlatformerLevelGen` по сиду записи игры.
## Рисуется в виртуальном экране 480×270 с увеличением ×4, спрайты пиратов 16×16.
## Баги накладываются модификаторами по флагам записи (#14, #15).

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


func _on_start() -> void:
	tuning = PlatformerDemoTuning.load_default()
	level = PlatformerLevelGen.generate(record.seed)
	lives = tuning.lives
	for name in ["hero_run_0", "hero_run_1", "hero_run_2", "hero_jump", "enemy_0", "enemy_1", "coin", "checkpoint", "flag", "ground", "ground_inner", "platform", "cloud_small", "cloud_big"]:
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
	# Облака из сида, с параллаксом вдвое медленнее уровня.
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed, ":clouds"))
	for i in 26:
		var c := Cloud.new()
		c.x = rng.randf_range(0.0, level.width * TILE * 0.55)
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


func _tile_feet(col: int, row: int) -> Vector2:
	return Vector2((col + 0.5) * TILE, VIEW.y - row * TILE)


func _unhandled_input(event: InputEvent) -> void:
	super(event)
	if not running or paused:
		return
	if GameInput.is_a(event):
		_jump()
		get_viewport().set_input_as_handled()
	elif event.is_action_released(GameInput.A) and vel.y < 0.0:
		vel.y *= tuning.jump_cut


func _jump() -> void:
	if not grounded:
		return
	vel.y = -4.0 * tuning.jump_height / tuning.jump_time
	grounded = false


func _gravity() -> float:
	return 8.0 * tuning.jump_height / (tuning.jump_time * tuning.jump_time)


func _on_tick(delta: float) -> void:
	anim_time += delta
	invuln = maxf(invuln - delta, 0.0)
	move_dir = bot_dir if AutoTest.bot_active() else GameInput.axis().x
	if absf(move_dir) < 0.3:
		move_dir = 0.0
	else:
		move_dir = signf(move_dir)
		facing = int(move_dir)
	vel.x = move_dir * tuning.run_speed
	vel.y = minf(vel.y + _gravity() * delta, MAX_FALL)
	_move_x(vel.x * delta)
	_move_y(vel.y * delta)
	if move_dir != 0.0 and grounded:
		run_anim += delta * tuning.run_fps
	_update_walkers(delta)
	_collect()
	if hero.y > VIEW.y + 40.0:
		_die()
	if not checkpoint_hit and hero.x >= level.checkpoint.x * TILE:
		checkpoint_hit = true
		respawn = _tile_feet(level.checkpoint.x, level.checkpoint.y)
	if hero.x >= level.flag.x * TILE + TILE * 0.3:
		end_demo(true)
	cam_x = clampf(hero.x - VIEW.x * 0.38, 0.0, level.width * TILE - VIEW.x)
	world.position.x = -roundf(cam_x)
	world.queue_redraw()


# --- Движение и столкновения с тайлами ------------------------------------------------------

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
	if h > 0:
		out.append(VIEW.y - h * TILE)
	for p in level.platforms:
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
		if invuln > 0.0:
			continue
		var hit := absf(w.x - hero.x) < half + 6.0 and hero.y > w.y - TILE and hero.y - tuning.hero_height < w.y
		if hit:
			if vel.y > 0.0 and hero.y <= w.y - TILE * 0.5:
				w.alive = false
				vel.y = -tuning.stomp_bounce
				grounded = false
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
		i -= 1


func _die() -> void:
	deaths += 1
	lives -= 1
	if lives <= 0:
		end_demo(false)
		return
	hero = respawn
	vel = Vector2.ZERO
	grounded = false
	invuln = tuning.invulnerable_seconds


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

func _draw_world() -> void:
	world.draw_rect(Rect2(cam_x, 0, VIEW.x, VIEW.y), BG_COLOR)
	for c in clouds:
		var sx := c.x + cam_x * 0.5
		if sx + 32.0 < cam_x or sx > cam_x + VIEW.x:
			continue
		world.draw_texture(tex["cloud_big" if c.big else "cloud_small"], Vector2(roundf(sx), roundf(c.y)))
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
			world.draw_texture(tex["platform"], Vector2((p.position.x + i) * TILE, VIEW.y - (p.position.y + 1) * TILE))
	var bob := 1.0 if fmod(anim_time, 0.6) < 0.3 else 0.0
	for c in coins_left:
		if c.x < first or c.x > last:
			continue
		world.draw_texture(tex["coin"], Vector2(c.x * TILE, VIEW.y - (c.y + 1) * TILE - bob))
	world.draw_texture(tex["checkpoint"], Vector2(level.checkpoint.x * TILE, VIEW.y - (level.checkpoint.y + 1) * TILE),
			Color(1, 1, 1, 1) if checkpoint_hit else Color(1, 1, 1, 0.6))
	world.draw_texture(tex["flag"], Vector2(level.flag.x * TILE, VIEW.y - (level.flag.y + 1) * TILE))
	var enemy_frame := "enemy_0" if fmod(anim_time * tuning.enemy_fps, 2.0) < 1.0 else "enemy_1"
	for w in walkers:
		if not w.alive or w.x < first * TILE or w.x > (last + 1) * TILE:
			continue
		_draw_sprite(tex[enemy_frame], Vector2(w.x, w.y), w.dir)
	var visible := invuln <= 0.0 or fmod(invuln, 0.2) < 0.1
	if visible:
		var frame := "hero_jump"
		if grounded:
			# Цикл шага: узкий, вместе, широкий, вместе.
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
	# Жизни: головы героя справа сверху.
	for i in lives:
		world.draw_texture_rect_region(tex["hero_run_1"], Rect2(cam_x + VIEW.x - 8.0 - (i + 1) * 12.0, 3.0, 10.0, 8.0), Rect2(3, 1, 10, 8))


func _number_width(n: int) -> float:
	return str(n).length() * 8.0 - 2.0


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
