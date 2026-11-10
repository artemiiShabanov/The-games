extends Demo
## Демка файтинг × 8-bit (#54), каталог `docs/specs/demos_catalog.md`: вид сбоку, один на один
## на палубе пиратского корабля, матрос против капитана, бойцы 16×32. Влево, вправо шаг, вниз
## присед, B блок стоя, A удар: стоя верхний, в приседе нижний. Блок держит верхний, присед
## уходит от верхнего, нижний не держит ничто, кроме дистанции. Раунд один на `round_seconds`:
## нокаут раньше, иначе побеждает тот, у кого больше здоровья; поровну ничья, итог не цель.
## Правила боя в `FightSim` ровным шагом, соперник по плану из сида (`FightPlanGen`, `FightAi`:
## фазы профилей напор, стена, подсечка, контра с паттернами ударов), бот героя `FightBot`.
## Виртуальный экран ×6 в карточке (×3 во встроенном режиме) без SubViewport, как у гольфа:
## слои `backdrop` (небо, море, мачта, фальшборт и палуба из цветов и тайлов сеттинга,
## статичный), `world` (пропы, бойцы, искры) и `hud` (полосы здоровья, таймер, отсчёт)
## увеличены целым масштабом. Спрайты файтинга пока только у пиратов (`fight_*`), палуба и
## пропы берутся у гольфа (`golf_deck`, `golf_hull`, `golf_cannon`, `golf_chest`).
##
## Баги по флагам записи; общие (#44) механикой живут в `Demo`: `frame_drops` фризы в бою;
## `audio_stutter` заикание музыки и звуки с задержкой; `sticky_input` ход и присед, A и B с
## опозданием, после удара A залипает и удар повторяется сам, как только герой свободен;
## `pink_placeholders` капитан, пушка, сундук или искры розовыми прямоугольниками (герой и
## палуба никогда); `alien_palette` фон и бойцы в сдвинутых цветах; `sprite_flicker` на строке
## ног четыре спрайта (пушка, сундук, два бойца), нижняя половина капитана мерцает через кадр.
## Баги жанра и баланса у файтинга отдельной задачей (#55).

enum Phase { COUNT, FIGHT, OVER }

## Увеличение в карточке: ×6 (экран 277×138), бойцы в полный рост читаются издалека.
const SCALE := 6
## Увеличение во встроенном режиме (запись стрима в ленте, экран 293×136).
const EMBED_SCALE := 3
const TILE := 16
## Палуба под ногами бойцов, px до низа экрана.
const DECK_H := 24
const HUD_INK := Color("#F4EFE6")
const HUD_SHADOW := Color("#161412")
const HUD_DIM := Color(0.086, 0.078, 0.071, 0.45)
const BAR_FILL := Color("#F2C85A")
const WOOD := Color("#A85A2A")
const SPARK_LIFE := 0.22
## Что может стать розовой заглушкой; герой и палуба никогда.
const PLACEHOLDER_SLOTS: Array[String] = ["rival", "cannon", "chest", "spark"]
const FRAMES: Array[String] = ["idle_0", "idle_1", "walk", "high_0", "high_1", "crouch", "low_1", "block", "hit", "ko"]
const SPRITES: Array[String] = ["fight_spark", "fight_guard", "golf_deck", "golf_hull", "golf_cannon", "golf_chest"]
const MELODY := [0, null, 0, 3, null, 5, null, 7, 6, null, 5, 3, 0, null, null, null,
	0, null, 0, 3, null, 5, null, 10, 9, null, 7, 5, 7, null, null, null]
const BASS := [-12, -12, -9, -9, -7, -7, -6, -6, -12, -12, -9, -9, -5, -5, -7, -7]

var tuning: FightDemoTuning
var gen: FightGenTuning
var plan: FightPlan
var sim: FightSim
var ai: FightAi
var bot: FightBot
var scene_set: SettingDef
## Виртуальный экран в пикселях демки: внутренность карточки, делённая на `SCALE`.
var view := Vector2(277, 138)
var scale_px := SCALE
var tex := {}
var backdrop: Node2D
var world: Node2D
var hud: Node2D
var ground_y := 168.0
var center_x := 208.0
var phase := Phase.COUNT
var count_left := 0.0
var over_left := 0.0
var _last_count := -1
var _acc := 0.0
var _dt := 1.0 / 60.0
## Отстающая полоса здоровья (белая) за настоящей.
var _ghost := Vector2(100, 100)
## Искры: позиция, остаток жизни, вид (0 удар, 1 блок) и взгляд по z/w.
var _sparks: Array[Vector4] = []
var _spark_flip: Array[bool] = []
## Ввод игрока (через `Demo.bug_press`): A нажата и ждёт шага, B зажата.
var _a_req := false
var _hold_b := false
var _bot_b := false
## Залипшая A (`sticky_input`): удар, который сейчас начнётся, повтор залипания.
var _stick_strike := false
var stuck_strikes := 0
var flicker_frames := 0
var _music: AudioStreamPlayer
var _sfx := {}


func _on_start() -> void:
	tuning = FightDemoTuning.load_default()
	gen = FightGenTuning.load_default()
	scene_set = SettingDef.of(record.setting)
	plan = FightPlanGen.generate(record.seed, gen, tuning.round_seconds)
	_dt = 1.0 / tuning.physics_hz
	for who in ["fight_hero_", "fight_rival_"]:
		for f in FRAMES:
			tex[who + f] = scene_set.sprite(who + f)
	for name in SPRITES:
		tex[name] = scene_set.sprite(name)
	scale_px = EMBED_SCALE if embedded else SCALE
	var area := embed_size if embedded else CardFrame.inner_size()
	view = (area / scale_px).floor()
	ground_y = view.y - DECK_H
	center_x = floorf(view.x / 2.0)
	# Бой в своих координатах с серединой арены в нуле (как у проверки без окна, бой тот же
	# до бита), рисуется со сдвигом `center_x`.
	sim = FightSim.new(tuning, 0.0)
	ai = FightAi.new(sim, plan, gen)
	if bot_driven():
		bot = FightBot.new(sim, active_bot_mode(), record.seed)
	_ghost = Vector2(tuning.health, tuning.health)
	var stage := Control.new()
	stage.position = ((area - view * scale_px) / 2.0).floor()
	stage.size = view * scale_px
	stage.clip_contents = true
	stage.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	stage.mouse_filter = Control.MOUSE_FILTER_IGNORE
	screen.add_child(stage)
	backdrop = Node2D.new()
	backdrop.scale = Vector2.ONE * scale_px
	backdrop.draw.connect(_draw_backdrop)
	stage.add_child(backdrop)
	world = Node2D.new()
	world.scale = Vector2.ONE * scale_px
	world.draw.connect(_draw_world)
	stage.add_child(world)
	if bug_palette() != null:
		backdrop.material = bug_palette()
		world.material = bug_palette()
	hud = Node2D.new()
	hud.scale = Vector2.ONE * scale_px
	hud.draw.connect(_draw_hud)
	stage.add_child(hud)
	count_left = tuning.countdown
	_setup_audio()


func _setup_audio() -> void:
	_music = Sfx.player(Sfx.chiptune_loop(MELODY, BASS, 160.0), tuning.music_db if not embedded else -80.0)
	add_child(_music)
	bug_music = _music
	if not embedded:
		_music.play()
	_sfx["count"] = Sfx.player(Sfx.blip(440.0, 0.12, 0.35, 18.0))
	_sfx["go"] = Sfx.player(Sfx.blip(880.0, 0.25, 0.4, 10.0))
	_sfx["swing"] = Sfx.player(Sfx.blip(520.0, 0.05, 0.25, 40.0))
	_sfx["hit"] = Sfx.player(Sfx.thud(0.1, 0.45))
	_sfx["guard"] = Sfx.player(Sfx.blip(1320.0, 0.06, 0.3, 30.0))
	_sfx["ko"] = Sfx.player(Sfx.thud(0.35, 0.55))
	_sfx["finish"] = Sfx.player(Sfx.blip(880.0, 0.5, 0.45, 5.0))
	_sfx["lose"] = Sfx.player(Sfx.blip(196.0, 0.4, 0.45, 6.0))
	for p in _sfx.values():
		(p as AudioStreamPlayer).volume_db = tuning.sfx_db if not embedded else -80.0
		add_child(p)


func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _play(name: String) -> void:
	# Во встроенном режиме демка стартует до входа в дерево (стрим ленты собирается заранее).
	if is_inside_tree():
		bug_play(_sfx[name])


# --- Итог ------------------------------------------------------------------------------------

func _on_end(goal_: bool) -> void:
	_music.stop()
	_play("finish" if goal_ else "lose")
	if AutoTest.enabled and not embedded:
		AutoTest.note("fighting: %s, %s; сид %d, реакция %d, промах %.2f, попыток генератора %d, план: %s" % [
				"цель" if goal_ else "провал", sim.summary(), record.seed, plan.reaction, plan.miss, plan.attempts,
				plan.describe(gen)])
		if not record.bug_ids.is_empty():
			AutoTest.note("fighting bugs: розовые %s, залипших ударов %d, кадров с мерцанием %d" % [
					PLACEHOLDER_SLOTS.filter(func(s: String) -> bool: return is_pink(s)), stuck_strikes, flicker_frames])


func _result_title(goal: bool) -> String:
	if sim == null:
		return "поражение"
	if goal:
		return "нокаут" if sim.knocked_out() else "победа"
	return "ничья" if sim.hero.health == sim.rival.health else "поражение"


func _result_caption() -> String:
	var how := ("нокаут на %d с" % int(round(sim.seconds()))) if sim.knocked_out() else "время вышло"
	return "здоровье %d : %d · ударов %d · блоков %d · %s" % [sim.hero.health, sim.rival.health,
			sim.hero.highs + sim.hero.lows, sim.hero.blocks, how]


# --- Ввод ------------------------------------------------------------------------------------

## A и B идут через `Demo.bug_press`: с багом управления и нажатие, и отпускание с опозданием.
func _game_input(event: InputEvent) -> void:
	if event.is_action_pressed(GameInput.A, false):
		bug_press(func() -> void: _a_req = true)
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed(GameInput.B, false):
		bug_press(func() -> void: _hold_b = true)
		get_viewport().set_input_as_handled()
	elif event.is_action_released(GameInput.B):
		bug_press(func() -> void: _hold_b = false)


# --- Шаг ----------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	# Фризы в бою с догоном времени (`Demo.bug_frame`).
	if bug_frame(delta, phase == Phase.FIGHT, _step):
		world.queue_redraw()
		hud.queue_redraw()


func _step(delta: float) -> void:
	if not running:
		return
	bug_input_tick()
	if not bot_driven() and not has_bug(&"sticky_input"):
		# Отпускание могло уйти в паузу: кнопка не зажата, значит отпущена.
		_hold_b = _hold_b and Input.is_action_pressed(GameInput.B)
	for i in range(_sparks.size() - 1, -1, -1):
		_sparks[i].z -= delta
		if _sparks[i].z <= 0.0:
			_sparks.remove_at(i)
			_spark_flip.remove_at(i)
	if phase == Phase.COUNT:
		count_left -= delta
		var shown := _count_digit()
		if shown != _last_count:
			_last_count = shown
			_play("go" if shown == 0 else "count")
		if count_left <= 0.0:
			phase = Phase.FIGHT
		return
	_acc += delta
	var n := 0
	while _acc >= _dt and running and n < 30:
		_fixed()
		_acc -= _dt
		n += 1
	if n >= 30:
		_acc = 0.0
	if phase == Phase.OVER:
		over_left -= delta
		if over_left <= 0.0:
			end_demo(sim.hero_won())


## Цифра отсчёта 3-2-1, 0 после старта.
func _count_digit() -> int:
	return int(ceil(maxf(count_left, 0.0) / (tuning.countdown / 3.0)))


func _fixed() -> void:
	var hero_in := FightSim.Controls.new()
	var rival_in := FightSim.Controls.new()
	if phase == Phase.FIGHT:
		hero_in = _hero_controls()
		rival_in = ai.think()
	sim.step(hero_in, rival_in)
	for e in sim.events:
		_on_event(e)
	# Белая полоса свежего урона догоняет здоровье на 40 в секунду.
	var rate := 40.0 * _dt
	_ghost.x = maxf(_ghost.x - rate, float(sim.hero.health))
	_ghost.y = maxf(_ghost.y - rate, float(sim.rival.health))
	if phase == Phase.FIGHT:
		var limit := int(round(tuning.round_seconds * tuning.physics_hz))
		if sim.knocked_out() or sim.frame >= limit:
			phase = Phase.OVER
			over_left = tuning.end_pause
			sim.stopped = true


## Ввод героя на шаг: клавиатура или бот, ось через `Demo.bug_axis`, A и B через `bug_press`.
func _hero_controls() -> FightSim.Controls:
	var raw := GameInput.axis()
	if bot != null:
		var want := bot.think()
		raw = Vector2(want.x, 1.0 if want.down else 0.0)
		if want.a:
			bug_press(func() -> void: _a_req = true)
		if want.b != _bot_b:
			_bot_b = want.b
			var held := want.b
			bug_press(func() -> void: _hold_b = held)
	var ax := bug_axis(raw)
	var c := FightSim.Controls.new()
	c.x = 1 if ax.x > 0.5 else (-1 if ax.x < -0.5 else 0)
	c.down = ax.y > 0.5
	c.b = _hold_b
	if FightSim.actionable(sim.hero) and not _a_req and bug_take_stick():
		# Залипшая A: удар повторяется сам, как только герой свободен.
		_a_req = true
		_stick_strike = true
	c.a = _a_req
	_a_req = false
	return c


func _on_event(e: FightSim.Event) -> void:
	match e.kind:
		&"swing":
			_play("swing")
			if e.by_hero:
				if _stick_strike:
					_stick_strike = false
					stuck_strikes += 1
					if stuck_strikes == 1 and AutoTest.enabled and not embedded:
						AutoTest.note("fighting bug: удар повторился сам от залипшей A на %.1f с" % sim.seconds())
				else:
					bug_stick()
		&"hit", &"ko":
			_play("hit" if e.kind == &"hit" else "ko")
			_add_spark(e.pos, 0, false)
		&"guard":
			_play("guard")
			# Дуга щита к бьющему: блокирует герой, бьёт соперник, и наоборот.
			var blocker := sim.hero if e.by_hero else sim.rival
			_add_spark(e.pos, 1, blocker.face < 0)


func _add_spark(pos: Vector2, kind: int, flip: bool) -> void:
	_sparks.append(Vector4(center_x + pos.x, pos.y, SPARK_LIFE, kind))
	_spark_flip.append(flip)


# --- Рисование -------------------------------------------------------------------------------

## Кадр бойца по состоянию: стойка дышит, шаг через кадр, удар замахом и вытянутой рукой (ногой),
## которая держится ещё `strike_hold` шагов восстановления.
func _frame_name(f: FightSim.Fighter) -> String:
	match f.state:
		FightSim.State.WALK:
			return "walk" if int(sim.ticks / 8.0) % 2 == 1 else "idle_0"
		FightSim.State.CROUCH:
			return "crouch"
		FightSim.State.BLOCK, FightSim.State.GUARD:
			return "block"
		FightSim.State.HIT:
			return "hit"
		FightSim.State.KO:
			return "hit" if f.t < 8 else "ko"
		FightSim.State.STRIKE:
			var fr := sim.frames(f.move)
			var low := f.move == FightSim.Move.LOW
			if f.t <= fr.x:
				return "crouch" if low else "high_0"
			if f.t <= fr.x + fr.y + tuning.strike_hold:
				return "low_1" if low else "high_1"
			return "crouch" if low else "idle_0"
	return "idle_%d" % (int(sim.ticks / 30.0) % 2)


func _draw_world() -> void:
	flicker_reset()
	var hide := {}
	# Пропы у бортов на строке ног бойцов: с мерцанием 8-bit их четыре на строке.
	for p in plan.props:
		var slot := "cannon" if p.kind == 0 else "chest"
		var px := _prop_x(p)
		if flicker_hidden(int(floor((ground_y - 8.0) / TILE))):
			continue
		var at := Vector2(px - 8.0, ground_y - 16.0)
		if is_pink(slot):
			world.draw_rect(Rect2(at + Vector2(3, 3), Vector2(10, 10)), PINK)
		elif p.x < 0.0 and p.kind == 0:
			world.draw_texture_rect(tex["golf_cannon"], Rect2(at, Vector2(-16, 16)), false)
		else:
			world.draw_texture(tex["golf_cannon" if p.kind == 0 else "golf_chest"], at)
	# Мерцание считается героем, потом капитаном: лишним на строке оказывается капитан.
	for who in 2:
		var f := sim.hero if who == 0 else sim.rival
		var halves := 1 if f.state == FightSim.State.KO and f.t >= 8 else 2
		for half in halves:
			var top := ground_y - 32.0 + half * 16.0 if halves == 2 else ground_y - 14.0
			hide[who * 2 + half] = flicker_hidden(int(floor((top + 8.0) / TILE)))
	if hide.values().has(true):
		flicker_frames += 1
	_draw_fighter(sim.rival, "fight_rival_", "rival", hide.get(2, false), hide.get(3, false))
	_draw_fighter(sim.hero, "fight_hero_", "hero", hide.get(0, false), hide.get(1, false))
	for i in _sparks.size():
		var s := _sparks[i]
		var at := Vector2(roundf(s.x) - 8.0, ground_y + roundf(s.y) - 8.0)
		if flicker_hidden(int(floor((at.y + 8.0) / TILE))):
			continue
		if is_pink("spark"):
			world.draw_rect(Rect2(at + Vector2(4, 4), Vector2(8, 8)), PINK)
			continue
		var name := "fight_spark" if s.w < 0.5 else "fight_guard"
		if _spark_flip[i]:
			world.draw_texture_rect(tex[name], Rect2(at, Vector2(-16, 16)), false)
		else:
			world.draw_texture(tex[name], at)


## Боец ногами на палубе, лицом по взгляду (влево отражён), двумя половинами 16 строк: у каждой
## своя строка тайлов для мерцания. KO лёжа 32×16 одним куском. Отрицательная ширина в
## `draw_texture_rect*` отражает кадр на месте, позиция остаётся левым краем.
func _draw_fighter(f: FightSim.Fighter, prefix: String, slot: String, hide_top: bool, hide_bottom: bool) -> void:
	var name := _frame_name(f)
	var tx: Texture2D = tex[prefix + name]
	var w := float(tx.get_width())
	var h := float(tx.get_height())
	var x := roundf(center_x + f.x)
	if is_pink(slot):
		if name == "ko":
			world.draw_rect(Rect2(x - 12.0, ground_y - 7.0, 24.0, 6.0), PINK)
		else:
			var r := sim.hurt_rect(f)
			world.draw_rect(Rect2(roundf(center_x + r.position.x), ground_y + r.position.y + 1.0, r.size.x, r.size.y - 1.0), PINK)
		return
	var flip := f.face < 0
	if name == "ko":
		if hide_top:
			return
		var at := Vector2(x - 16.0, ground_y - 14.0)
		# Лёжа головой назад: смотрел вправо, голова слева.
		world.draw_texture_rect(tx, Rect2(at, Vector2(-w if flip else w, h)), false)
		return
	var left := x - 8.0 if not flip else x + 8.0 - w
	for half in 2:
		if (hide_top if half == 0 else hide_bottom):
			continue
		var dst := Rect2(left, ground_y - h + half * 16.0, -w if flip else w, 16.0)
		world.draw_texture_rect_region(tx, dst, Rect2(0.0, half * 16.0, w, 16.0))


## Середина пропа по x: от своего борта внутрь на `|x|`.
func _prop_x(p: FightPlan.Prop) -> float:
	var half := tuning.arena_width / 2.0
	return roundf(center_x - half + absf(p.x)) if p.x < 0.0 else roundf(center_x + half - absf(p.x))


## Статичный фон в координатах экрана из цветов сеттинга: полосы неба, светило, острова и море
## на горизонте, мачта с реем, свёрнутым парусом и вантами, фальшборт за бойцами, палуба тайлами,
## у краёв арены стойки борта.
func _draw_backdrop() -> void:
	var horizon := roundf(ground_y - 44.0)
	var bands := scene_set.sky_bands
	var band_h := horizon / maxi(bands.size(), 1)
	for i in bands.size():
		backdrop.draw_rect(Rect2(0, roundf(i * band_h), view.x, ceilf(band_h) + 1), bands[i])
	var sun := Vector2(view.x - 64.0, 40.0)
	for r in [[Vector2(-6, -12), Vector2(12, 24)], [Vector2(-12, -6), Vector2(24, 12)], [Vector2(-10, -10), Vector2(20, 20)]]:
		backdrop.draw_rect(Rect2(sun + r[0], r[1]), scene_set.sun)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed, ":islands"))
	var x := -8.0
	while x < view.x:
		var w := rng.randf_range(28.0, 64.0)
		var h := rng.randf_range(6.0, 16.0)
		for i in 4:
			var k := float(i) / 4.0
			var sw := w * (1.0 - k * 0.8)
			backdrop.draw_rect(Rect2(roundf(x + (w - sw) / 2.0), roundf(horizon - h * (i + 1) / 4.0), roundf(sw), ceilf(h / 4.0) + 1),
					scene_set.silhouette_dark if i % 2 == 0 else scene_set.silhouette)
		x += w + rng.randf_range(16.0, 60.0)
	backdrop.draw_rect(Rect2(0, horizon, view.x, ground_y - horizon), scene_set.horizon)
	for i in 6:
		var y := horizon + 3 + i * 6
		var bx := fmod(i * 53.0 + 11.0, view.x - 24.0)
		backdrop.draw_rect(Rect2(bx, y, 8 + (i % 3) * 6, 1), scene_set.horizon_light)
	_draw_mast()
	# Фальшборт за бойцами: доски с планширем и стойками.
	var wall := ground_y - 14.0
	backdrop.draw_rect(Rect2(0, wall, view.x, 14.0), WOOD)
	backdrop.draw_rect(Rect2(0, wall, view.x, 2.0), HUD_SHADOW)
	backdrop.draw_rect(Rect2(0, wall + 7.0, view.x, 1.0), HUD_SHADOW)
	var post := fmod(center_x, 32.0) - 32.0
	while post < view.x:
		backdrop.draw_rect(Rect2(post, wall, 2.0, 14.0), HUD_SHADOW)
		post += 32.0
	# Палуба: верхний тайл палубы, ниже борт.
	var tx := 0.0
	while tx < view.x:
		backdrop.draw_texture(tex["golf_deck"], Vector2(tx, ground_y))
		var ty := ground_y + TILE
		while ty < view.y:
			backdrop.draw_texture(tex["golf_hull"], Vector2(tx, ty))
			ty += TILE
		tx += TILE
	# Края арены: высокие стойки борта с канатом, дальше бойцы не отходят.
	for side in [-1.0, 1.0]:
		var ex := roundf(center_x + side * tuning.arena_width / 2.0)
		var px := ex - 3.0 if side < 0.0 else ex - 1.0
		backdrop.draw_rect(Rect2(px - 1.0, ground_y - 41.0, 6.0, 41.0), HUD_SHADOW)
		backdrop.draw_rect(Rect2(px, ground_y - 40.0, 4.0, 40.0), WOOD)
		backdrop.draw_rect(Rect2(px, ground_y - 40.0, 4.0, 2.0), BAR_FILL)


## Мачта со смещением из плана, рей со свёрнутым парусом, ванты к фальшборту.
func _draw_mast() -> void:
	var mx := roundf(center_x + plan.mast_x)
	var yard := 30.0
	var wall := ground_y - 14.0
	for side in [-1.0, 1.0]:
		var foot := Vector2(mx + side * 72.0, wall)
		var head := Vector2(mx + side * 3.0, 6.0)
		for k in 3:
			backdrop.draw_line(head + Vector2(side * k * 4.0, k * 10.0), foot + Vector2(side * k * 10.0, 0.0), HUD_SHADOW, 1.0)
	backdrop.draw_rect(Rect2(mx - 4.0, 0.0, 8.0, wall), HUD_SHADOW)
	backdrop.draw_rect(Rect2(mx - 3.0, 0.0, 6.0, wall), WOOD)
	backdrop.draw_rect(Rect2(mx - 1.0, 0.0, 1.0, wall), BAR_FILL)
	backdrop.draw_rect(Rect2(mx - 52.0, yard - 1.0, 104.0, 5.0), HUD_SHADOW)
	backdrop.draw_rect(Rect2(mx - 51.0, yard, 102.0, 3.0), WOOD)
	# Свёрнутый парус под реем: белые складки с тенью.
	backdrop.draw_rect(Rect2(mx - 46.0, yard + 4.0, 92.0, 6.0), HUD_SHADOW)
	for i in 23:
		backdrop.draw_rect(Rect2(mx - 45.0 + i * 4.0, yard + 4.0, 3.0, 5.0), HUD_INK)
	# Воронье гнездо.
	backdrop.draw_rect(Rect2(mx - 9.0, 9.0, 18.0, 7.0), HUD_SHADOW)
	backdrop.draw_rect(Rect2(mx - 8.0, 10.0, 16.0, 5.0), WOOD)


## HUD в координатах экрана: полосы здоровья с лицами по краям (герой слева, капитан справа),
## отстающая белая часть показывает свежий урон; таймер посередине; отсчёт и «KO» / «ВРЕМЯ»
## крупно по центру.
func _draw_hud() -> void:
	var top := 4.0
	var bar_w := floorf(view.x / 2.0 - 40.0)
	_draw_face("fight_hero_idle_0", Vector2(4, top - 2.0), false, false)
	_draw_face("fight_rival_idle_0", Vector2(view.x - 20.0, top - 2.0), true, is_pink("rival"))
	_draw_bar(Vector2(22, top), bar_w, sim.hero.health, _ghost.x, false)
	_draw_bar(Vector2(view.x - 22.0 - bar_w, top), bar_w, sim.rival.health, _ghost.y, true)
	var left := ceili(maxf(tuning.round_seconds - sim.seconds(), 0.0))
	var t := "%02d" % left
	draw_pixel_text(hud, Vector2(center_x - 7.0, top), t, HUD_INK, HUD_SHADOW)
	if phase == Phase.COUNT and _count_digit() > 0:
		var cell := 6.0
		draw_pixel_text(hud, (Vector2(center_x - 1.5 * cell, view.y * 0.3)).round(), str(_count_digit()), HUD_INK, HUD_SHADOW, cell)
	elif phase == Phase.OVER:
		var word := "KO" if sim.knocked_out() else "ВРЕМЯ"
		var cell := 6.0
		var w := word.length() * 4.0 * cell - cell
		draw_pixel_text(hud, (Vector2(center_x - w / 2.0, view.y * 0.3)).round(), word, HUD_INK, HUD_SHADOW, cell)


## Полоса здоровья 9 px: тень, тусклая основа, белый недавний урон, жёлтое здоровье. Капитанская
## прижата к правому краю и убывает к середине, как и геройская к левому.
func _draw_bar(at: Vector2, w: float, health: int, ghost: float, right: bool) -> void:
	hud.draw_rect(Rect2(at + Vector2(1, 1), Vector2(w, 9)), HUD_SHADOW)
	hud.draw_rect(Rect2(at, Vector2(w, 9)), HUD_SHADOW)
	hud.draw_rect(Rect2(at + Vector2(1, 1), Vector2(w - 2, 7)), HUD_DIM)
	var inner := w - 2.0
	var g := roundf(inner * clampf(ghost / tuning.health, 0.0, 1.0))
	var f := roundf(inner * clampf(float(health) / tuning.health, 0.0, 1.0))
	var gx := at.x + 1.0 + (inner - g if right else 0.0)
	var fx := at.x + 1.0 + (inner - f if right else 0.0)
	hud.draw_rect(Rect2(gx, at.y + 1.0, g, 7.0), HUD_INK)
	hud.draw_rect(Rect2(fx, at.y + 1.0, f, 7.0), BAR_FILL)
	hud.draw_rect(Rect2(fx, at.y + 1.0, f, 1.0), HUD_INK)


## Лицо бойца у края полосы: верх кадра стойки 16×11.
func _draw_face(name: String, at: Vector2, flip: bool, pink: bool) -> void:
	if pink:
		hud.draw_rect(Rect2(at + Vector2(4, 3), Vector2(8, 8)), PINK)
		return
	var tx: Texture2D = tex[name]
	var dst := Rect2(at, Vector2(-16 if flip else 16, 11))
	hud.draw_texture_rect_region(tx, dst, Rect2(0, 0, 16, 11))
