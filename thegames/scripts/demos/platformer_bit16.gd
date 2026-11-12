extends Demo
## Демка платформер × 16/32-bit, каталог `docs/specs/demos_catalog.md`: «по клеткам» (#98,
## решение 2026-11-12: не физика с инерцией и склонами, а геймплей попроще и под технологию).
## Вид сбоку с фоном в три слоя. Герой стоит на клетке: стрелка это плавный шаг на соседнюю,
## A прыжок ровно через одну клетку в сторону взгляда; зажатая стрелка ведёт шаг за шагом. На
## пути ловушки по ритму: шипы выезжают из палубы и прячутся, якорь на цепи падает на клетку и
## поднимается, плиты над водой осыпаются под ногами, стражники ходят по своим участкам. Яма,
## шипы, якорь и стражник стоят жизни, жизней три; после потери герой продолжает с последней
## пройденной клетки отдыха. Цель: флаг справа.
## Уровень из `GridLevelGen` по сиду записи: порядок ловушек и их ритм. Правила и боты живут в
## `GridSim` (без окна, им же проверяются сто сидов); демка ведёт его шагами, рисует и
## озвучивает его события. Рисуется на `Bit16Screen` крупным планом (×3) лентами кадров
## сеттинга: шаг это шесть кадров бега, прыжок четыре кадра.
##
## Баги по флагам записи (параметры в `resources/bugs/<id>.tres`). Общие (#44) и баг технологии
## `layer_tear` живут в `Demo`, `Bit16Screen` и `Parallax16`, демка только зовёт хуки: фризы
## `bug_frame`, заикание трекера, шаг и прыжок с опозданием, залипший прыжок (повторяется после
## приземления), розовые заглушки. Свои проявления: `wild_physics` (баг жанра) прыжок через
## три клетки вместо одной и стражники вдвое быстрее; `unreachable_coins` монеты висят выше
## любого прыжка и не берутся; `sneeze_enemies` стражник падает от касания.

const TILE := 32.0
## Крупный план: экран ×3 (554×277), на нём 17 клеток в ширину, герой вполовину выше, чем в 8-bit.
const ZOOM := 3
## Палуба занимает три ряда клеток снизу экрана.
const FLOOR_ROWS := 3
const JUMP_HEIGHT := 26.0
## Монета над клеткой (низ спрайта над полом) и она же под багом «не достать»: выше головы
## героя даже в прыжке через три клетки.
const COIN_HEIGHT := 26.0
const COIN_LIFTED := 92.0
const ANCHOR_HANG := 118.0
const PLACEHOLDER_SLOTS: Array[String] = ["guard", "coin", "flag", "spikes", "anchor"]
const SPRITES: Array[String] = ["hero_run", "hero_idle", "hero_leap", "guard_walk", "spikes", "anchor", "plate", "heart",
		"coin", "flag", "ground", "ground_inner"]
const MELODY := [0, null, 3, 5, 7, null, 5, 3, 0, null, 3, 5, 7, 10, 7, null,
	-2, null, 2, 3, 5, null, 3, 2, -2, null, 2, 3, 5, 7, 5, null]
const BASS := [-12, -12, -12, -12, -9, -9, -9, -9, -14, -14, -14, -14, -10, -10, -7, -7]

var tuning: PlatformerBit16Tuning
var level: GridLevel
var sim: GridSim
var parallax: Parallax16
var tex := {}
var cam_x := 0.0
var bot_axis := 0.0

var _time := 0.0
var _jump_pressed := false
## Упавшие стражники (баг «чих»): индекс и секунды с падения.
var _guard_fall: Dictionary[int, float] = {}
## Осыпавшиеся плиты: клетка и секунды с падения.
var _plate_fall: Dictionary[int, float] = {}
var _music: AudioStreamPlayer
var _sfx := {}


func _on_start() -> void:
	tuning = PlatformerBit16Tuning.load_default()
	level = GridLevelGen.generate(record.seed if record != null else 1)
	sim = GridSim.create(level, tuning)
	# Баги жанра и баланса; общие баги в `Demo` (#44).
	if has_bug(&"wild_physics"):
		sim.jump_over = maxi(int(round(bug_param(&"wild_physics", &"jump_mult", 3.0))), 1)
		sim.enemy_mult = bug_param(&"wild_physics", &"enemy_speed_mult", 2.0)
	sim.coins_high = has_bug(&"unreachable_coins")
	sim.sneeze = has_bug(&"sneeze_enemies")
	bit16_screen(_draw_backdrop, _draw_world, _draw_hud, ZOOM)
	parallax = parallax16()
	for name in SPRITES:
		tex[name] = bit16_set.sprite16(name)
	_setup_audio()


func _setup_audio() -> void:
	_music = Sfx.music(Sfx.tracker_loop(MELODY, BASS, 126.0), tuning.music_db if not embedded else -80.0)
	add_child(_music)
	bug_music = _music
	if not embedded:
		_music.play()
	_sfx["step"] = Sfx.player(Sfx.blip(260.0, 0.04, 0.12, 60.0))
	_sfx["jump"] = Sfx.player(Sfx.blip(520.0, 0.12, 0.3, 18.0))
	_sfx["land"] = Sfx.player(Sfx.thud(0.06, 0.25))
	_sfx["fall"] = Sfx.player(Sfx.beep(520.0, 0.3, 0.25, 110.0))
	_sfx["crack"] = Sfx.player(Sfx.blip(180.0, 0.05, 0.22, 50.0))
	_sfx["crumble"] = Sfx.player(Sfx.thud(0.18, 0.3))
	_sfx["coin"] = Sfx.player(Sfx.blip(1318.0, 0.12, 0.3, 16.0))
	_sfx["hurt"] = Sfx.player(Sfx.blip(196.0, 0.35, 0.4, 7.0))
	_sfx["guard_down"] = Sfx.player(Sfx.blip(392.0, 0.2, 0.3, 12.0))
	_sfx["finish"] = Sfx.player(Sfx.blip(880.0, 0.5, 0.45, 5.0))
	for p in _sfx.values():
		(p as AudioStreamPlayer).volume_db = tuning.sfx_db if not embedded else -80.0
		add_child(p)


func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _play(name: String) -> void:
	bug_play(_sfx[name])


func _on_end(goal: bool) -> void:
	_music.stop()
	if goal:
		_play("finish")
	if AutoTest.enabled and not embedded:
		AutoTest.note("platformer bit16: %s за %.1f с, клетка %d из %d, жизней %d, монет %d из %d" % [
				"флаг" if goal else "провал", elapsed, sim.cell, level.flag, sim.lives, sim.coins_got, level.coins.size()])


func _result_caption() -> String:
	return "монеты %d из %d · потеряно жизней %d · %d с" % [sim.coins_got, level.coins.size(), sim.deaths, int(round(elapsed))]


# --- Ввод и шаг ------------------------------------------------------------------------------

func _game_input(event: InputEvent) -> void:
	if GameInput.is_a(event):
		# С багом управления нажатие уходит в очередь с задержкой (`Demo.bug_press`).
		bug_press(_press_jump)
		get_viewport().set_input_as_handled()


func _press_jump() -> void:
	_jump_pressed = true


func _bot_step(delta: float) -> void:
	bot_axis = sim.bot(active_bot_mode(), delta)
	if sim.bot_jump:
		_jump_pressed = true


func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	# Фризы в движении с догоном времени (`Demo.bug_frame`).
	bug_frame(delta, sim.act != GridSim.Act.IDLE, _step)


func _step(dt: float) -> void:
	_time += dt
	for i: int in _guard_fall.keys():
		_guard_fall[i] += dt
	for c: int in _plate_fall.keys():
		_plate_fall[c] += dt
	bug_input_tick()
	# Стрелка: с багом управления из прошлого на delay_ms (`Demo.bug_axis`).
	var raw := bot_axis if bot_driven() else GameInput.axis().x
	sim.step(dt, bug_axis(Vector2(raw, 0.0)).x, _jump_pressed)
	_jump_pressed = false
	for ev in sim.events:
		_on_event(ev)
	sim.events.clear()
	var want := clampf(sim.x * TILE + TILE / 2.0 - bit16.view.x * 0.38, 0.0, maxf(level.width * TILE - bit16.view.x, 0.0))
	cam_x = lerpf(cam_x, want, minf(dt * 8.0, 1.0))


## Событие правил: звук, эффект, заметка автотеста, конец демки.
func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"step":
			_play("step")
		&"jump":
			_play("jump")
			# Залипание: прыжок повторится после приземления (`Demo.bug_stick`).
			bug_stick()
		&"land":
			_play("land")
			if bug_take_stick():
				_jump_pressed = true
		&"fall":
			bug_clear_stick()
			_play("fall")
		&"crack":
			_play("crack")
		&"crumble":
			_plate_fall[int(ev[1])] = 0.0
			_play("crumble")
		&"coin":
			_play("coin")
		&"hurt":
			bug_clear_stick()
			_play("hurt")
			if AutoTest.enabled and not embedded:
				AutoTest.note("platformer bit16: жизнь %d потеряна (%s) в клетке %d на %.1f с" % [sim.deaths, ev[1], sim.cell, elapsed])
		&"respawn":
			_plate_fall.clear()
		&"guard_down":
			_guard_fall[int(ev[1])] = 0.0
			_play("guard_down")
		&"win":
			end_demo(true)
		&"lose":
			end_demo(false)


# --- Рисование -------------------------------------------------------------------------------

## Верх палубы на экране.
func _floor_y() -> float:
	return bit16.view.y - FLOOR_ROWS * TILE


## Середина клетки (дробной) на экране.
func _cx(cell_x: float) -> float:
	return roundf(cell_x * TILE + TILE / 2.0 - cam_x)


func _draw_backdrop(canvas: CanvasItem) -> void:
	parallax.draw(canvas, bit16.view, cam_x, roundf(bit16.view.y * 0.5), bit16.palette)


func _draw_world(canvas: CanvasItem) -> void:
	var view := bit16.view
	var gy := _floor_y()
	var first := maxi(int(floor(cam_x / TILE)) - 1, 0)
	var last := mini(first + int(view.x / TILE) + 3, level.width - 1)
	# Палуба: под ямой и плитой пусто, там видна вода.
	for c in range(first, last + 1):
		var kind := level.cell(c)
		var left := roundf(c * TILE - cam_x)
		if kind == GridLevel.Cell.PIT:
			continue
		if kind == GridLevel.Cell.PLATE:
			_draw_plate(canvas, c, left, gy)
			continue
		canvas.draw_texture(tex["ground"], Vector2(left, gy))
		for row in range(1, FLOOR_ROWS):
			canvas.draw_texture(tex["ground_inner"], Vector2(left, gy + row * TILE))
	# Ловушки на палубе.
	for c in range(first, last + 1):
		match level.cell(c):
			GridLevel.Cell.SPIKES:
				draw_sprite16(canvas, "spikes", tex["spikes"], _spike_frame(c), Vector2(_cx(c), gy))
			GridLevel.Cell.ANCHOR:
				_draw_anchor(canvas, c, gy)
	# Монеты, флаг.
	var frame := int(_time * 10.0)
	for i in level.coins.size():
		var c := level.coins[i]
		if sim.coin_taken[i] or c < first or c > last:
			continue
		draw_sprite16(canvas, "coin", tex["coin"], frame, Vector2(_cx(c), gy - (COIN_LIFTED if sim.coins_high else COIN_HEIGHT)))
	draw_sprite16(canvas, "flag", tex["flag"], int(_time * 8.0), Vector2(_cx(level.flag), gy))
	# Стражники: лицом по ходу; упавший от чиха валится вниз.
	for i in sim.guards.size():
		var g := sim.guards[i]
		if g.pos < first - 1 or g.pos > last + 1:
			continue
		var drop := 0.0
		if not g.alive:
			var t := float(_guard_fall.get(i, 9.0))
			if t > 0.6:
				continue
			drop = t * t * 420.0
		draw_sprite16(canvas, "guard", tex["guard_walk"], int(_time * 8.0) if g.moving else 0, Vector2(_cx(g.pos), gy + drop), g.dir > 0)
	_draw_hero(canvas, gy)


## Плита: целая, в трещинах и дрожит, а осыпавшаяся летит вниз обломками.
func _draw_plate(canvas: CanvasItem, c: int, left: float, gy: float) -> void:
	if sim.plate_fallen.has(c):
		var t := float(_plate_fall.get(c, 9.0))
		if t < 0.5:
			canvas.draw_texture_rect_region(tex["plate"], Rect2(left, gy + t * t * 520.0, TILE, TILE), Rect2(2 * TILE, 0, TILE, TILE))
		return
	var cracking := sim.plate_t.has(c)
	var shake := roundf(sin(_time * 70.0)) if cracking else 0.0
	canvas.draw_texture_rect_region(tex["plate"], Rect2(left + shake, gy, TILE, TILE), Rect2((1 if cracking else 0) * TILE, 0, TILE, TILE))


## Кадр шипов по фазе: спрятаны, кончики перед выездом, наполовину, во весь рост.
func _spike_frame(c: int) -> int:
	var ph := sim.spike_phase(c, sim.time)
	if ph >= 1.0 - tuning.spike_warn:
		return 1
	if ph >= tuning.spike_up:
		return 0
	return 2 if ph < 0.04 or ph > tuning.spike_up - 0.04 else 3


## Якорь на цепи: висит наверху, перед падением дрожит, падает на клетку, лежит, поднимается.
func _draw_anchor(canvas: CanvasItem, c: int, gy: float) -> void:
	var ph := sim.spike_phase(c, sim.time)
	var down := tuning.anchor_down
	var lift := 1.0
	if ph < 0.05:
		lift = 1.0 - ph / 0.05
	elif ph < down - 0.06:
		lift = 0.0
	elif ph < down + 0.14:
		lift = (ph - (down - 0.06)) / 0.2
	var x := _cx(c)
	if ph >= 1.0 - tuning.anchor_warn:
		x += roundf(sin(_time * 60.0))
	var feet := Vector2(x, gy - roundf(lift * ANCHOR_HANG))
	var links := 0.0
	while links < feet.y - TILE:
		canvas.draw_rect(Rect2(x - 1.0, links, 2.0, 5.0), bit16.ink(Bit16Screen.GREY))
		links += 8.0
	draw_sprite16(canvas, "anchor", tex["anchor"], 0, feet)


## Герой: стойка, шесть кадров шага, четыре кадра прыжка по дуге; в яму падает, после потери
## жизни мигает.
func _draw_hero(canvas: CanvasItem, gy: float) -> void:
	if sim.lives <= 0:
		return
	if sim.act == GridSim.Act.HURT and fmod(sim.act_t, 0.16) < 0.08:
		return
	if sim.invuln > 0.0 and sim.act != GridSim.Act.HURT and fmod(sim.invuln, 0.2) < 0.1:
		return
	var feet := Vector2(_cx(sim.x), gy)
	var name := "hero_idle"
	var frame := int(_time * 2.0)
	match sim.act:
		GridSim.Act.STEP:
			name = "hero_run"
			frame = int(clampf(sim.act_t / tuning.step_seconds, 0.0, 0.99) * 6.0)
		GridSim.Act.JUMP:
			var k := clampf(sim.act_t / sim.jump_time(), 0.0, 1.0)
			name = "hero_leap"
			frame = 0 if k < 0.12 else (1 if k < 0.5 else (2 if k < 0.88 else 3))
			feet.y -= roundf(sin(PI * k) * JUMP_HEIGHT * sim.jump_span() / 2.0)
		GridSim.Act.FALL:
			name = "hero_leap"
			frame = 2
			var k := sim.act_t / tuning.fall_seconds
			feet.y += roundf(k * k * 110.0)
	bit16.sprite(canvas, tex[name], frame, feet, sim.facing < 0)


## HUD: сердца по числу жизней и счёт монет.
func _draw_hud(canvas: CanvasItem) -> void:
	for i in sim.lives:
		bit16.sprite(canvas, tex["heart"], 0, Vector2(24.0 + i * 30.0, 40.0))
	var x := 24.0 + tuning.lives * 30.0 + 14.0
	bit16.sprite(canvas, tex["coin"], 0, Vector2(x, 40.0))
	draw_pixel_text(canvas, Vector2(x + 20.0, 16.0), str(sim.coins_got), bit16.ink(Bit16Screen.WHITE), bit16.ink(Bit16Screen.K), 3.0)
