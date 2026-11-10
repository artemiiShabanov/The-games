extends Demo
## Демка спорт × 8-bit: гольф вид сбоку (#52), каталог `docs/specs/demos_catalog.md`. Две-три
## лунки из сида (`GolfCourseGen`): ти на помосте, песчаный остров с холмами, иногда пролив с
## морем, грин на палубе корабля с люком-лункой и флагом, корма стеной за грином. Ветер на
## лунку делениями от −3 до 3. Вверх и вниз угол удара (целые градусы), A зажать: шкала силы
## бежит до полной и обратно, отпустить: удар; B развернуться (удар в другую сторону, нужен,
## когда мяч перелетел лунку и сам разворот не угадал). Меньше ударов лучше: море и аут штраф
## в один удар и мяч на прежнее место; на лунку не больше `пар + 3` ударов, дальше мяч
## подобран. Цель: сумма ударов не больше суммы пара всех лунок, итог «в пар» или «−2 к
## пару»; больше: «+3 к пару»; вышла страховка `max_seconds`: «не доиграл».
## Физика мяча в `GolfBall` ровным шагом, бот WIN считает удар той же физикой: перебирает углы
## и силы по делениям шкалы, бьёт в лунку или ближе всего к ней. LOSE бьёт слабо и коротко.
## Виртуальный экран ×4 в карточке (×2 во встроенном режиме) без SubViewport, как у шутера:
## слои `backdrop` (небо, светило, острова, море на горизонте из цветов сеттинга, статичный),
## `world` (лунка запечена в текстуру на старте лунки, камера едет по x) и `hud` увеличены
## целым масштабом. Спрайты гольфа пока только у пиратов (`golf_*`), другие сеттинги берут их.
##
## Баги по флагам записи. Общие (#44) механикой живут в `Demo`: `frame_drops` фризы, пока мяч
## летит или катится; `audio_stutter` заикание музыки и звуки с задержкой; `sticky_input` угол,
## A и B с опозданием (отпущенная A ещё качает шкалу, удар сильнее), после удара A залипает:
## следующий удар срывается сам слабым тычком; `pink_placeholders` мяч, люк, флаг, брызги или
## пропы розовыми квадратами; `alien_palette` небо и лунка в сдвинутых цветах;
## `sprite_flicker` спрайты сверх лимита на строке тайлов через кадр. Свои проявления (#53,
## числа в `resources/bugs/<id>.tres`, читаются один раз в `_setup_bugs`): `ball_to_space`
## (жанровый баг спорта) каждый третий удар, коснувшийся песка, залипает: мяч уходит в песок
## наполовину, дрожит и выстреливает в небо, за верхом экрана потерян, штраф в удар и мяч на
## прежнее место; `unreachable_coins` люк на остром пике над палубой грина, склоны круче
## стены, на наклоне мяч в люк не падает: лунку кончает лимит ударов; `sneeze_enemies` посреди
## полёта налетает порыв ветра в случайную сторону и сносит мяч; `wild_physics` мяч-попрыгунчик:
## упругие отскоки от всех поверхностей (бот считает той же физикой).

enum Phase { INTRO, AIM, FLIGHT, REST, PENALTY, HOLED, STUCK }

const SCALE := 4
## Увеличение во встроенном режиме (запись стрима в ленте).
const EMBED_SCALE := 2
## Мир лунки высотой в экран демки в карточке; во встроенном режиме обрезан по центру.
const WORLD_H := 208
const TILE := 16
const HUD_INK := Color("#F4EFE6")
const HUD_SHADOW := Color("#161412")
const HUD_DIM := Color(0.086, 0.078, 0.071, 0.45)
const METER_FILL := Color("#F2C85A")
const SEA := Color("#2F6FB5")
const SPLASH_LIFE := 0.6
## Борт под палубой ти и грина, px; ниже песок.
const HULL_DEPTH := 24
## Что может стать розовой заглушкой; герой и земля никогда.
const PLACEHOLDER_SLOTS: Array[String] = ["ball", "cup", "flag", "splash", "cannon", "chest"]
const SPRITES: Array[String] = ["golf_hero_0", "golf_hero_1", "golf_hero_2", "golf_ball", "golf_cup",
	"golf_flag", "golf_sand", "golf_sand_inner", "golf_deck", "golf_hull", "golf_sea", "golf_splash",
	"golf_cannon", "golf_chest"]
const PROP_SPRITES: Array[String] = ["golf_cannon", "golf_chest"]
const PROP_SLOTS: Array[String] = ["cannon", "chest"]
## Флажок лунки в HUD, 5×7.
const FLAG_ICON: Array[String] = ["11111", "11110", "11100", "10000", "10000", "10000", "10000"]
const MELODY := [0, null, 4, 7, 9, null, 7, 4, 5, null, 9, null, 7, null, null, null,
	0, null, 4, 7, 12, null, 11, 9, 7, 5, 4, 2, 0, null, null, null]
const BASS := [-12, -12, -5, -5, -7, -7, -5, -5, -12, -12, -8, -8, -10, -10, -5, -5]

var tuning: GolfDemoTuning
var course: GolfCourse
var hole: GolfCourse.Hole
var hole_index := 0
## Виртуальный экран в пикселях демки: внутренность карточки, делённая на `SCALE`.
var view := Vector2(416, 208)
var scale_px := SCALE
var tex := {}
var backdrop: Node2D
var world: Node2D
var hud: Node2D
var scene_set: SettingDef
var ball := GolfBall.new()
var phase := Phase.INTRO
var phase_left := 0.0
## Удар вправо (1) или влево (−1); угол целыми градусами.
var dir := 1
var angle := 40
var charging := false
var charge_steps := 0
var meter := 0.0
## Сила прошлого удара, отметка на шкале; −1 до первого удара.
var last_power := -1.0
## Откуда бил: сюда мяч возвращается после моря или аута; там стоит матрос, пока мяч летит.
var last_spot := Vector2.ZERO
var golfer_x := 0.0
var golfer_dir := 1
var strokes := 0
## Удары по сыгранным лункам, по порядку.
var scores: Array[int] = []
var penalties := 0
var picked := 0
var play_time := 0.0
var cam_x := 0.0
var swing_left := 0.0
## Брызги: позиция и остаток жизни.
var _splash := Vector3.ZERO
var _dt := 1.0 / 120.0
var _fill_steps := 120
var _acc := 0.0
var _angle_acc := 1.0
var _cam_from := 0.0
var _origin_y := 0.0
var _terrain_tex: ImageTexture
var _bounces_heard := 0
## Кнопки игрока (через `Demo.bug_press`): A зажата, просьба развернуться.
var _a_down := false
var _flip_req := false
## Залипание A: удар срывается сам, шкала отпускается на этом делении (−1 нет).
var _stuck_release := -1
var stuck_shots := 0
## Бот: ось угла на кадр, A, план удара (угол, деление шкалы), перебор.
var _bot_axis := 0.0
var _bot_a := false
var _bot_pressed := false
var _bot_release_sent := false
var _release_at := -1
var _bot_ready := false
var _bot_angle := 0
var _bot_k := 0
var _bot_stage := 0
var _bot_cands: Array[Vector2i] = []
var _bot_ci := 0
var _bot_best := Vector2i(-1, -1)
var _bot_best_score := INF
var _bot_wait := 0.0
var _bot_turn := 0.0
## Куда бот целит этот удар (x): люк или мимо него издалека; случайность промаха из сида.
var _bot_target := 0.0
var _bot_rng := RandomNumberGenerator.new()
var bot_sims := 0
var bot_shots := 0
var bot_usec := 0
## Баги жанра и баланса (#53), числа из ресурсов багов читаются один раз в `_setup_bugs`.
var _bug_rng := RandomNumberGenerator.new()
## «Мяч в космос»: каждый `_stick_every`-й удар, коснувшийся песка, залипает (0 без бага); мяч
## тонет за `_sink_s`, дрожит `_stuck_s`, вылетает вверх со скоростью `_eject_speed`, разгоняясь
## на `_eject_accel`, и потерян выше экрана на `_space_px`. Счёт ударов по песку, удар уже
## проверен, залипший мяч.
var _stick_every := 0
var _sink_s := 0.3
var _stuck_s := 1.2
var _eject_speed := 150.0
var _eject_accel := 200.0
var _eject_drift := 40.0
var _space_px := 80.0
var _sand_shots := 0
var _sand_checked := false
var _stuck_t := 0.0
var _stuck_at := Vector2.ZERO
var _eject_vel := Vector2.ZERO
var stuck_balls := 0
var space_lost := 0
## «Чих»: порыв ветра `_gust_wind` делений (0 без бага) через `_gust_after` (от, до) с
## удара; порыв этого удара и сколько он дует.
var _gust_wind := 0
var _gust_after := Vector2(0.25, 0.6)
var _gust_at := 0.0
var _gust := 0
var _gust_t := 0.0
var gusts := 0
## «Не достать»: люк на пике (`_raise_peak`): высота над палубой, полуширина, вершина не выше y.
var _peak := false
var _peak_rise := 96.0
var _peak_half := 24.0
var _peak_top_min := 40.0
## «Дикая физика»: мяч-попрыгунчик (тюнинг мяча подменён копией), больше всего отскоков за удар,
## первый удар уже в заметках автотеста.
var _rubber := false
var max_bounces := 0
var _rubber_noted := false

# Звук.
var _music: AudioStreamPlayer
var _sfx := {}


func _on_start() -> void:
	tuning = GolfDemoTuning.load_default()
	scene_set = SettingDef.of(record.setting)
	_setup_bugs()
	course = GolfCourseGen.generate(record.seed)
	if _peak:
		for h in course.holes:
			_raise_peak(h)
		if AutoTest.enabled and not embedded:
			var h0 := course.holes[0]
			AutoTest.note("golf bug: люк на пике в %.0f px над палубой грина с первого кадра" % [h0.height_at(h0.green_from) - h0.height_at(h0.cup_x)])
	_bot_rng.seed = hash(str(record.seed, ":golf_bot"))
	_dt = 1.0 / tuning.physics_hz
	_fill_steps = maxi(int(round(tuning.meter_fill * tuning.physics_hz)), 1)
	for name in SPRITES:
		tex[name] = scene_set.sprite(name)
	scale_px = EMBED_SCALE if embedded else SCALE
	var area := embed_size if embedded else CardFrame.inner_size()
	view = (area / scale_px).floor()
	var stage := Control.new()
	stage.position = ((area - view * scale_px) / 2.0).floor()
	stage.size = view * scale_px
	stage.clip_contents = true
	stage.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	stage.mouse_filter = Control.MOUSE_FILTER_IGNORE
	screen.add_child(stage)
	_origin_y = floorf((view.y - WORLD_H) / 2.0)
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
	_setup_audio()
	_start_hole(0)


## Баги жанра и баланса (#53): параметры из ресурсов багов один раз (`Demo.bug_param` грузит
## каталог на каждый вызов).
func _setup_bugs() -> void:
	_bug_rng.seed = hash(str(record.seed, ":golf_bugs"))
	if has_bug(&"ball_to_space"):
		_stick_every = maxi(int(bug_param(&"ball_to_space", &"stick_every", 3.0)), 1)
		_sink_s = bug_param(&"ball_to_space", &"sink_s", 0.3)
		_stuck_s = bug_param(&"ball_to_space", &"stuck_s", 1.2)
		_eject_speed = bug_param(&"ball_to_space", &"eject_speed", 150.0)
		_eject_accel = bug_param(&"ball_to_space", &"eject_accel", 200.0)
		_eject_drift = bug_param(&"ball_to_space", &"eject_drift", 40.0)
		_space_px = bug_param(&"ball_to_space", &"space_px", 80.0)
	if has_bug(&"sneeze_enemies"):
		_gust_wind = maxi(int(bug_param(&"sneeze_enemies", &"gust_wind", 9.0)), 1)
		_gust_after = Vector2(bug_param(&"sneeze_enemies", &"gust_after_min", 0.25),
				bug_param(&"sneeze_enemies", &"gust_after_max", 0.6))
	if has_bug(&"unreachable_coins"):
		_peak = true
		_peak_rise = bug_param(&"unreachable_coins", &"peak_rise", 96.0)
		_peak_half = bug_param(&"unreachable_coins", &"peak_half", 24.0)
		_peak_top_min = bug_param(&"unreachable_coins", &"peak_top_min", 40.0)
	if has_bug(&"wild_physics"):
		# Попрыгунчик: своя копия тюнинга мяча, бот считает удар ей же.
		_rubber = true
		tuning = tuning.duplicate() as GolfDemoTuning
		var bounce := bug_param(&"wild_physics", &"ball_bounce", 0.75)
		var keep := bug_param(&"wild_physics", &"ball_keep", 0.95)
		tuning.sand_bounce = maxf(tuning.sand_bounce, bounce)
		tuning.deck_bounce = maxf(tuning.deck_bounce, bounce)
		tuning.hull_bounce = maxf(tuning.hull_bounce, bounce)
		tuning.sand_keep = maxf(tuning.sand_keep, keep)
		tuning.deck_keep = maxf(tuning.deck_keep, keep)
		tuning.hull_keep = maxf(tuning.hull_keep, keep)
		tuning.gravity *= bug_param(&"wild_physics", &"ball_gravity_mult", 1.0)


## «Не достать» (#53): люк на острый пик посреди палубы грина. Пик треугольником на
## `_peak_rise` над палубой (вершина не выше `_peak_top_min`), полушириной `_peak_half`, склоны
## песком круче стены; люк ровно на вершине, на наклоне мяч в него не падает (`cup_max_slope`).
func _raise_peak(h: GolfCourse.Hole) -> void:
	var ci := int(round(h.cup_x / h.step))
	h.cup_x = ci * h.step
	var half := maxi(int(round(_peak_half / h.step)), 1)
	var heights := h.heights
	var kinds := h.kinds
	var deck := heights[ci]
	var top := maxf(deck - _peak_rise, _peak_top_min)
	for k in range(-half + 1, half):
		heights[ci + k] = roundf(lerpf(deck, top, 1.0 - float(absi(k)) / half))
	for i in range(ci - half, ci + half):
		kinds[i] = GolfCourse.Kind.SAND
	h.heights = heights
	h.kinds = kinds


func _setup_audio() -> void:
	_music = Sfx.player(Sfx.chiptune_loop(MELODY, BASS, 132.0), tuning.music_db if not embedded else -80.0)
	add_child(_music)
	bug_music = _music
	if not embedded:
		_music.play()
	_sfx["hole"] = Sfx.player(Sfx.blip(660.0, 0.2, 0.35, 10.0))
	_sfx["swing"] = Sfx.player(Sfx.blip(520.0, 0.08, 0.35, 30.0))
	_sfx["bounce"] = Sfx.player(Sfx.thud(0.05, 0.3))
	_sfx["cup"] = Sfx.player(Sfx.blip(988.0, 0.35, 0.4, 8.0))
	_sfx["splash"] = Sfx.player(Sfx.thud(0.3, 0.45))
	_sfx["out"] = Sfx.player(Sfx.blip(220.0, 0.25, 0.35, 10.0))
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


# --- Счёт и итог ---------------------------------------------------------------------------

func total_strokes() -> int:
	var s := 0
	for v in scores:
		s += v
	return s


func _par_played() -> int:
	var p := 0
	for i in scores.size():
		p += course.holes[i].par
	return p


func _cap() -> int:
	return hole.par + tuning.max_over_par


## «в пар», «+3 к пару», «−1 к пару».
static func rel_text(diff: int) -> String:
	if diff == 0:
		return "в пар"
	return ("+%d к пару" % diff) if diff > 0 else ("−%d к пару" % -diff)


func _all_played() -> bool:
	return scores.size() == course.holes.size()


func _on_end(goal_: bool) -> void:
	_music.stop()
	_play("finish" if goal_ else "lose")
	if AutoTest.enabled and not embedded:
		var parts: PackedStringArray = []
		for i in scores.size():
			parts.append("%d/%d" % [scores[i], course.holes[i].par])
		AutoTest.note("golf: %s, ударов %d при паре %d (%s), лунки %s, сыграно %d из %d, штрафов %d, подобрано %d, %.1f с, сид %d, попыток генератора %d" % [
				"цель" if goal_ else "провал", total_strokes(), _par_played(), rel_text(total_strokes() - _par_played()),
				" ".join(parts), scores.size(), course.holes.size(), penalties, picked, play_time, record.seed, course.attempts])
		if bot_shots > 0:
			AutoTest.note("golf bot: траекторий на удар %.0f, расчёт удара %.1f мс в среднем" % [
					float(bot_sims) / bot_shots, bot_usec / 1000.0 / bot_shots])
		if not record.bug_ids.is_empty():
			AutoTest.note("golf bugs: сорвалось ударов от залипшей A %d, залипло в песке %d, в космос %d, порывов %d, отскоков за удар до %d" % [
					stuck_shots, stuck_balls, space_lost, gusts, max_bounces])


func _result_title(goal: bool) -> String:
	if course == null or not _all_played():
		return "не доиграл"
	return rel_text(total_strokes() - course.total_par())


func _result_caption() -> String:
	var t := int(round(play_time))
	if not _all_played():
		return "сыграно лунок %d из %d · время вышло" % [scores.size(), course.holes.size()]
	return "ударов %d при паре %d · лунок %d · %d с" % [total_strokes(), course.total_par(), scores.size(), t]


# --- Ввод ------------------------------------------------------------------------------------

## A и B идут через `Demo.bug_press`: с багом управления и нажатие, и отпускание с опозданием.
func _game_input(event: InputEvent) -> void:
	if event.is_action_pressed(GameInput.A, false):
		bug_press(func() -> void: _a_down = true)
		get_viewport().set_input_as_handled()
	elif event.is_action_released(GameInput.A):
		bug_press(func() -> void: _a_down = false)
	elif event.is_action_pressed(GameInput.B, false):
		bug_press(func() -> void: _flip_req = true)
		get_viewport().set_input_as_handled()


# --- Шаг ----------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	# Фризы, пока мяч летит или катится (`Demo.bug_frame`).
	if bug_frame(delta, ball.moving() or phase == Phase.INTRO, _step):
		world.position = Vector2(-roundf(cam_x * scale_px), _origin_y * scale_px)
		world.queue_redraw()
		hud.queue_redraw()


## Шаг кадра: физика и логика ровными шагами `_dt`, остаток копится.
func _step(delta: float) -> void:
	if not running:
		return
	bug_input_tick()
	if not bot_driven() and not has_bug(&"sticky_input"):
		# Отпускание могло уйти в паузу: кнопка не зажата, значит отпущена.
		_a_down = _a_down and Input.is_action_pressed(GameInput.A)
	play_time += delta
	_acc += delta
	var n := 0
	while _acc >= _dt and running and n < 60:
		_fixed()
		_acc -= _dt
		n += 1
	if n >= 60:
		_acc = 0.0
	if running and play_time >= tuning.max_seconds:
		end_demo(false)


func _fixed() -> void:
	swing_left = maxf(swing_left - _dt, 0.0)
	_gust_t += _dt
	_splash.z = maxf(_splash.z - _dt, 0.0)
	match phase:
		Phase.INTRO:
			phase_left -= _dt
			var k := smoothstep(0.2, 1.0, 1.0 - phase_left / tuning.intro_time)
			cam_x = lerpf(_cam_from, _clamp_cam(_aim_target()), k)
			if phase_left <= 0.0:
				_enter_aim()
			return
		Phase.AIM:
			_aim_step()
		Phase.FLIGHT:
			_flight_step()
		Phase.STUCK:
			_stuck_step()
		Phase.REST:
			phase_left -= _dt
			if phase_left <= 0.0:
				if strokes >= _cap():
					_finish_hole(false)
				else:
					_enter_aim()
		Phase.PENALTY:
			phase_left -= _dt
			if phase_left <= 0.0:
				ball.pos = last_spot
				ball.mode = GolfBall.Mode.REST
				if strokes >= _cap():
					_finish_hole(false)
				else:
					_enter_aim()
		Phase.HOLED:
			phase_left -= _dt
			if phase_left <= 0.0:
				if hole_index + 1 < course.holes.size():
					_start_hole(hole_index + 1)
				else:
					end_demo(total_strokes() <= course.total_par())
				return
	_follow_camera()


func _start_hole(i: int) -> void:
	hole_index = i
	hole = course.holes[i]
	strokes = 0
	ball = GolfBall.new()
	ball.pos = Vector2(hole.tee_x, hole.height_at(hole.tee_x) - tuning.ball_radius)
	ball.mode = GolfBall.Mode.REST
	last_spot = ball.pos
	last_power = -1.0
	dir = 1
	golfer_x = ball.pos.x - 10.0
	golfer_dir = 1
	angle = tuning.angle_start
	charging = false
	meter = 0.0
	phase = Phase.INTRO
	phase_left = tuning.intro_time
	_cam_from = _clamp_cam(hole.cup_x - view.x / 2.0)
	cam_x = _cam_from
	_bake_terrain()
	_play("hole")


func _enter_aim() -> void:
	phase = Phase.AIM
	charging = false
	meter = 0.0
	_a_down = _a_down and not bot_driven()
	dir = 1 if hole.cup_x >= ball.pos.x else -1
	golfer_dir = dir
	golfer_x = ball.pos.x - 10.0 * dir
	var on_deck := hole.kind_at(ball.pos.x) == GolfCourse.Kind.DECK and ball.pos.x >= hole.green_from
	angle = tuning.angle_deck if on_deck else tuning.angle_start
	_gust = 0
	_bot_reset()
	if bug_take_stick():
		# Залипшая A: удар срывается сам, слабым тычком.
		bug_clear_stick()
		charging = true
		charge_steps = 0
		_stuck_release = maxi(int(round(_fill_steps * 0.12)), 1)


func _a_held() -> bool:
	if _stuck_release >= 0:
		return charge_steps < _stuck_release
	return _bot_a if bot_driven() else _a_down


func _aim_step() -> void:
	var raw := _bot_axis if bot_driven() else -GameInput.axis().y
	var ax := bug_axis(Vector2(0.0, raw)).y
	if not charging:
		if _flip_req:
			_flip_req = false
			dir = -dir
			golfer_dir = dir
			golfer_x = ball.pos.x - 10.0 * dir
		if absf(ax) > 0.3:
			_angle_acc += tuning.angle_rate * _dt
			while _angle_acc >= 1.0:
				_angle_acc -= 1.0
				angle = clampi(angle + (1 if ax > 0.0 else -1), tuning.angle_min, tuning.angle_max)
		else:
			_angle_acc = 1.0
		if _a_held():
			charging = true
			charge_steps = 0
			meter = 0.0
		return
	_flip_req = false
	if _a_held():
		charge_steps += 1
		meter = _meter_at(charge_steps)
		if bot_driven() and _stuck_release < 0 and not _bot_release_sent and _release_at >= 0 and charge_steps >= _release_at:
			_bot_release_sent = true
			bug_press(func() -> void: _bot_a = false)
	if not _a_held():
		_release()


## Шкала силы на делении `k`: от нуля до полной за `_fill_steps` и обратно.
func _meter_at(k: int) -> float:
	var m := fmod(float(k) / _fill_steps, 2.0)
	return m if m <= 1.0 else 2.0 - m


func _release() -> void:
	charging = false
	var stuck := _stuck_release >= 0
	_stuck_release = -1
	var power := _meter_at(charge_steps)
	if power < tuning.min_power:
		return
	if stuck:
		stuck_shots += 1
		if stuck_shots == 1 and AutoTest.enabled and not embedded:
			AutoTest.note("golf bug: удар сорвался сам от залипшей A на %.1f с" % play_time)
	last_spot = ball.pos
	strokes += 1
	last_power = power
	ball.launch(ball.pos, angle, dir, power, tuning)
	_bounces_heard = 0
	_sand_checked = false
	_gust = 0
	if _gust_wind > 0:
		_gust_at = _bug_rng.randf_range(_gust_after.x, _gust_after.y)
	phase = Phase.FLIGHT
	swing_left = 0.45
	_play("swing")
	if not stuck:
		bug_stick()


func _flight_step() -> void:
	if _gust_wind > 0 and _gust == 0 and ball.mode == GolfBall.Mode.AIR and ball.time >= _gust_at:
		# Чих: порыв ветра посреди полёта в случайную сторону.
		_gust = _gust_wind * (1 if _bug_rng.randf() < 0.5 else -1)
		_gust_t = 0.0
		gusts += 1
		if gusts == 1 and AutoTest.enabled and not embedded:
			AutoTest.note("golf bug: порыв ветра %+d посреди полёта на %.1f с" % [_gust, play_time])
	var before := ball.bounces
	ball.step(hole, tuning, course.sea_y, _wind_now(), _dt)
	if ball.bounces > _bounces_heard:
		_bounces_heard = ball.bounces
		_play("bounce")
	if _stick_every > 0 and not _sand_checked and _sand_touch(before):
		_sand_checked = true
		_sand_shots += 1
		if (_sand_shots - 1) % _stick_every == 0:
			_stick_ball()
			return
	match ball.mode:
		GolfBall.Mode.REST:
			phase = Phase.REST
			phase_left = tuning.rest_pause
			max_bounces = maxi(max_bounces, ball.bounces)
			if _rubber and not _rubber_noted and AutoTest.enabled and not embedded:
				_rubber_noted = true
				AutoTest.note("golf bug: мяч-попрыгунчик, отскоков за первый удар %d, лёг на %.1f с" % [ball.bounces, play_time])
		GolfBall.Mode.CUP:
			_play("cup")
			_finish_hole(true)
		GolfBall.Mode.WATER, GolfBall.Mode.OUT:
			var water := ball.mode == GolfBall.Mode.WATER
			if water:
				_splash = Vector3(ball.pos.x, course.sea_y, SPLASH_LIFE)
			_play("splash" if water else "out")
			strokes += tuning.penalty
			penalties += 1
			phase = Phase.PENALTY
			phase_left = tuning.penalty_pause


## Ветер, который сейчас дует на мяч: порыв чиха или ветер лунки.
func _wind_now() -> int:
	return _gust if _gust != 0 else hole.wind


## Мяч этого шага коснулся песка: отскочил от него или катится, лежит на нём.
func _sand_touch(bounces_before: int) -> bool:
	if ball.mode != GolfBall.Mode.AIR and ball.mode != GolfBall.Mode.ROLL and ball.mode != GolfBall.Mode.REST:
		return false
	if ball.mode == GolfBall.Mode.AIR and ball.bounces == bounces_before:
		return false
	return hole.kind_at(ball.pos.x) == GolfCourse.Kind.SAND


## «Мяч в космос»: мяч встал в песок, дальше `_stuck_step`.
func _stick_ball() -> void:
	phase = Phase.STUCK
	_stuck_t = 0.0
	_stuck_at = Vector2(ball.pos.x, hole.height_at(ball.pos.x) - tuning.ball_radius)
	_eject_vel = Vector2.ZERO
	ball.pos = _stuck_at
	ball.vel = Vector2.ZERO
	ball.roll = 0.0
	ball.mode = GolfBall.Mode.REST
	stuck_balls += 1
	if stuck_balls == 1 and AutoTest.enabled and not embedded:
		AutoTest.note("golf bug: мяч залип в песке на %.1f с" % play_time)


## Залипший мяч: тонет в песок наполовину, дрожит, выстреливает вверх с разгоном; выше экрана
## на `_space_px` потерян: штраф в удар и мяч на прежнее место, как за аут.
func _stuck_step() -> void:
	_stuck_t += _dt
	var r := tuning.ball_radius
	if _stuck_t < _sink_s:
		ball.pos = _stuck_at + Vector2(0.0, r * _stuck_t / _sink_s)
		return
	if _stuck_t < _sink_s + _stuck_s:
		var shake := 1.0 if int(_stuck_t * 16.0) % 2 == 0 else -1.0
		ball.pos = _stuck_at + Vector2(shake, r)
		return
	if _eject_vel == Vector2.ZERO:
		_eject_vel = Vector2(_bug_rng.randf_range(-_eject_drift, _eject_drift), -_eject_speed)
		ball.pos = _stuck_at + Vector2(0.0, r)
		ball.mode = GolfBall.Mode.AIR
		_play("swing")
	_eject_vel.y -= _eject_accel * _dt
	ball.pos += _eject_vel * _dt
	ball.spin -= _eject_vel.y * _dt
	if ball.pos.y < -_space_px:
		ball.mode = GolfBall.Mode.OUT
		_play("out")
		strokes += tuning.penalty
		penalties += 1
		space_lost += 1
		if space_lost == 1 and AutoTest.enabled and not embedded:
			AutoTest.note("golf bug: мяч улетел в космос на %.1f с" % play_time)
		phase = Phase.PENALTY
		phase_left = tuning.penalty_pause


func _finish_hole(holed: bool) -> void:
	scores.append(strokes)
	if not holed:
		picked += 1
	phase = Phase.HOLED
	phase_left = tuning.holed_pause


## Камера: в прицеле мяч в трети экрана со стороны удара (или мяч и лунка вместе, если
## помещаются), в полёте за мячом с упреждением по ходу.
func _aim_target() -> float:
	if absf(hole.cup_x - ball.pos.x) < view.x - 80.0:
		return (hole.cup_x + ball.pos.x) / 2.0 - view.x / 2.0
	return ball.pos.x - view.x * (0.3 if dir > 0 else 0.7)


func _follow_camera() -> void:
	var target := cam_x
	if phase == Phase.AIM:
		target = _aim_target()
	elif phase == Phase.FLIGHT:
		target = ball.pos.x - view.x * (0.4 if ball.vel.x >= 0.0 else 0.6)
	cam_x = lerpf(cam_x, _clamp_cam(target), 1.0 - exp(-tuning.cam_follow * _dt))


func _clamp_cam(x: float) -> float:
	if hole.length <= view.x:
		return (hole.length - view.x) / 2.0
	return clampf(x, 0.0, hole.length - view.x)


# --- Бот ------------------------------------------------------------------------------------

func _bot_reset() -> void:
	_bot_a = false
	_bot_pressed = false
	_bot_release_sent = false
	_release_at = -1
	_bot_ready = false
	_bot_stage = 0
	_bot_cands.clear()
	_bot_ci = 0
	_bot_best = Vector2i(-1, -1)
	_bot_best_score = INF
	# В ленте бот не медлит сверх расчёта: в записи стрима больше полёта мяча.
	_bot_wait = 0.0 if embedded else tuning.bot_think
	_bot_turn = 0.0


## Бот автотеста и стрима. WIN: перебор ударов той же физикой (`_bot_search`, несколько
## траекторий за кадр), потом поворот угла стрелками и A до нужного деления шкалы. LOSE: слабый
## короткий удар под малым углом.
func _bot_step(delta: float) -> void:
	_bot_axis = 0.0
	if phase != Phase.AIM or charging or _stuck_release >= 0:
		return
	_bot_wait -= delta
	if not _bot_ready:
		if active_bot_mode() == AutoTest.BotMode.WIN:
			_bot_search()
			return
		_bot_angle = tuning.bot_lose_angle
		_bot_k = maxi(int(round(tuning.bot_lose_power * _fill_steps)), 1)
		_bot_ready = true
	if angle != _bot_angle and _bot_turn < tuning.bot_turn_max:
		_bot_turn += delta
		_bot_axis = 1.0 if _bot_angle > angle else -1.0
		return
	if _bot_wait > 0.0 or _bot_pressed:
		return
	_bot_pressed = true
	_release_at = _bot_k
	bug_press(func() -> void: _bot_a = true)


## Перебор ударов по кадрам: грубо по сетке углов и делений шкалы, затем точнее вокруг лучшего.
func _bot_search() -> void:
	var t0 := Time.get_ticks_usec()
	# Слабее `min_power` удара нет: такие деления шкалы бот не берёт.
	var k_min := maxi(ceili(tuning.min_power * _fill_steps), 1)
	if _bot_cands.is_empty():
		if _bot_stage == 0:
			_bot_target = hole.cup_x
			if absf(hole.cup_x - ball.pos.x) > tuning.bot_putt_range:
				var miss := _bot_rng.randf_range(tuning.bot_miss_min, tuning.bot_miss_max)
				_bot_target += miss if _bot_rng.randf() < 0.5 else -miss
			for a in range(tuning.angle_min, tuning.angle_max + 1, tuning.bot_angle_step):
				for k in range(tuning.bot_power_step / 2, _fill_steps + 1, tuning.bot_power_step):
					_bot_cands.append(Vector2i(a, maxi(k, k_min)))
		else:
			for a in range(_bot_best.x - tuning.bot_refine_angle, _bot_best.x + tuning.bot_refine_angle + 1):
				for k in range(_bot_best.y - tuning.bot_refine_power, _bot_best.y + tuning.bot_refine_power + 1):
					if a >= tuning.angle_min and a <= tuning.angle_max and k >= k_min and k <= _fill_steps:
						_bot_cands.append(Vector2i(a, k))
	var n := 0
	while _bot_ci < _bot_cands.size() and n < tuning.bot_sims_per_frame:
		var c := _bot_cands[_bot_ci]
		var score := _bot_eval(c.x, c.y)
		if score < _bot_best_score:
			_bot_best_score = score
			_bot_best = c
		_bot_ci += 1
		n += 1
	bot_usec += Time.get_ticks_usec() - t0
	if _bot_ci < _bot_cands.size():
		return
	_bot_cands.clear()
	_bot_ci = 0
	_bot_stage += 1
	if _bot_stage >= 2 or _bot_best_score < -500.0:
		_bot_angle = _bot_best.x
		_bot_k = _bot_best.y
		_bot_ready = true
		bot_shots += 1


## Оценка удара: та же физика до остановки. Море и аут хуже всего; целит в люк: в лунку лучше
## всего (чем мягче, тем лучше), иначе расстояние до точки цели, лёжа не на палубе дальше на
## `bot_off_deck`; целит мимо: и лунка считается расстоянием до точки цели.
func _bot_eval(a: int, k: int) -> float:
	var b := GolfBall.new()
	b.launch(ball.pos, a, dir, _meter_at(k), tuning)
	while b.moving():
		b.step(hole, tuning, course.sea_y, hole.wind, _dt)
	bot_sims += 1
	match b.mode:
		GolfBall.Mode.CUP:
			if _bot_target == hole.cup_x:
				return -1000.0 + k * 0.01
		GolfBall.Mode.WATER, GolfBall.Mode.OUT:
			return 1.0e6
	var d := absf(b.pos.x - _bot_target)
	if hole.kind_at(b.pos.x) != GolfCourse.Kind.DECK or b.pos.x < hole.green_from:
		d += tuning.bot_off_deck
	return d


# --- Рисование -------------------------------------------------------------------------------

## Точка мира в пикселях демки, округлённая до пикселя экрана.
func _snap(p: Vector2) -> Vector2:
	return (p * scale_px).round() / scale_px


## Спрайт левым верхним углом в `at` (мир); на строке тайлов сверх лимита мерцает.
func _sprite(slot: String, name: String, at: Vector2, size: Vector2, flip := false) -> void:
	if flicker_hidden(int(floor((at.y + size.y / 2.0) / TILE))):
		return
	at = _snap(at)
	if is_pink(slot):
		world.draw_rect(Rect2(at + size * 0.2, size * 0.6), PINK)
	elif flip:
		world.draw_texture_rect(tex[name], Rect2(at + Vector2(size.x, 0.0), Vector2(-size.x, size.y)), false)
	else:
		world.draw_texture(tex[name], at)


func _draw_world() -> void:
	flicker_reset()
	world.draw_texture(_terrain_tex, Vector2.ZERO)
	_draw_sea()
	for p in hole.props:
		_sprite(PROP_SLOTS[p.y], PROP_SPRITES[p.y], Vector2(p.x - 8, roundf(hole.height_at(p.x)) - 16), Vector2(16, 16))
	var deck := roundf(hole.height_at(hole.cup_x))
	var cx := roundf(hole.cup_x)
	_sprite("flag", "golf_flag", Vector2(cx - 3, deck - 22), Vector2(16, 24))
	_sprite("cup", "golf_cup", Vector2(cx - 8, deck - 2), Vector2(16, 8))
	# Матрос стоит на земле у мяча; за спиной стена кормы или пролив: на высоте мяча, перед ней.
	var gy := roundf(hole.height_at(golfer_x))
	var foot := hole.height_at(golfer_x - 0.5 * golfer_dir * TILE)
	var spot := hole.kind_at(golfer_x)
	if spot == GolfCourse.Kind.HULL or spot == GolfCourse.Kind.WATER or absf(foot - gy) > 6.0 \
			or golfer_x < 0.0 or golfer_x > hole.length:
		gy = roundf(last_spot.y + tuning.ball_radius) if phase != Phase.AIM else roundf(ball.pos.y + tuning.ball_radius)
	var frame := 1 if charging else (2 if swing_left > 0.0 or phase == Phase.FLIGHT else 0)
	_sprite("hero", "golf_hero_%d" % frame, Vector2(roundf(golfer_x) - 8, gy - 16), Vector2(16, 16), golfer_dir < 0)
	var hidden := ball.mode == GolfBall.Mode.CUP or ball.mode == GolfBall.Mode.WATER \
			or (phase == Phase.PENALTY and ball.mode == GolfBall.Mode.OUT)
	if not hidden:
		_draw_ball()
	if phase == Phase.STUCK and ball.mode == GolfBall.Mode.AIR:
		# Улетает в космос: след точками за мячом.
		for k in 3:
			var at := (_snap(ball.pos - _eject_vel.normalized() * (7.0 + k * 5.0))).floor()
			world.draw_rect(Rect2(at, Vector2.ONE * (2 if k == 0 else 1)), HUD_INK)
	if _gust != 0 and _gust_t < 1.0 and not hidden:
		# Порыв чиха: черты ветра у мяча бегут по ветру.
		var sx := signf(_gust)
		for i in 3:
			var run := fmod(_gust_t * 90.0 + i * 11.0, 30.0)
			var at := (_snap(ball.pos + Vector2(sx * (run - 18.0) - 3.0, -7.0 + i * 5.0))).floor()
			world.draw_rect(Rect2(at + Vector2(0.5, 0.5), Vector2(6, 1)), HUD_SHADOW)
			world.draw_rect(Rect2(at, Vector2(6, 1)), HUD_INK)
	if phase == Phase.AIM:
		# Прицел точками по углу удара.
		var d := Vector2(cos(deg_to_rad(angle)) * dir, -sin(deg_to_rad(angle)))
		for k: float in [9.0, 13.0, 17.0, 21.0]:
			var p := (_snap(ball.pos + d * k)).floor()
			world.draw_rect(Rect2(p + Vector2(0.5, 0.5), Vector2.ONE), HUD_SHADOW)
			world.draw_rect(Rect2(p, Vector2.ONE), HUD_INK)
	if _splash.z > 0.0:
		_sprite("splash", "golf_splash", Vector2(roundf(_splash.x) - 8, _splash.y - 11), Vector2(16, 16))


## Бочонок 8×8 центром в мяче; катится: поворот четвертями по пройденному пути.
func _draw_ball() -> void:
	var p := _snap(ball.pos)
	if flicker_hidden(int(floor(p.y / TILE))):
		return
	if phase == Phase.STUCK and ball.mode == GolfBall.Mode.REST:
		# Залип: над песком видна только верхняя часть бочонка.
		var vis := clampf(roundf(hole.height_at(_stuck_at.x) - (p.y - 4.0)), 0.0, 8.0)
		if is_pink("ball"):
			world.draw_rect(Rect2(p - Vector2(3, 3), Vector2(6, maxf(vis - 1.0, 0.0))), PINK)
		elif vis > 0.0:
			world.draw_texture_rect_region(tex["golf_ball"], Rect2(p - Vector2(4, 4), Vector2(8, vis)), Rect2(0, 0, 8, vis))
		return
	if is_pink("ball"):
		world.draw_rect(Rect2(p - Vector2(3, 3), Vector2(6, 6)), PINK)
		return
	var quarter := posmod(int(floor(ball.spin / (tuning.ball_radius * PI / 2.0))), 4)
	world.draw_set_transform(p, quarter * PI / 2.0)
	world.draw_texture(tex["golf_ball"], Vector2(-4, -4))
	world.draw_set_transform(Vector2.ZERO)


## Море в проливе: гребни тайлом `golf_sea` по уровню моря, бегут по времени, ниже заливка.
func _draw_sea() -> void:
	if not hole.has_water():
		return
	var y := course.sea_y - 2.0
	world.draw_rect(Rect2(hole.water_from, y + 3.0, hole.water_to - hole.water_from, WORLD_H - y), SEA)
	var shift := int(play_time * 8.0) % TILE
	var x := hole.water_from - shift
	while x < hole.water_to:
		var from := maxf(x, hole.water_from)
		var to := minf(x + TILE, hole.water_to)
		if to > from:
			world.draw_texture_rect_region(tex["golf_sea"], Rect2(from, y, to - from, TILE), Rect2(from - x, 0, to - from, TILE))
		x += TILE


## Запечь лунку в текстуру: столбцы от поверхности вниз тайлами по виду поверхности (верхний
## тайл от поверхности, толща по сетке; под палубой борт на `HULL_DEPTH`, ниже песок), кромка
## чёрной линией, открытые бока тоже.
func _bake_terrain() -> void:
	var img := Image.create_empty(hole.length, WORLD_H, false, Image.FORMAT_RGBA8)
	var sand := _tile_image("golf_sand")
	var sand_in := _tile_image("golf_sand_inner")
	var deck := _tile_image("golf_deck")
	var hull := _tile_image("golf_hull")
	var green_y := int(round(hole.height_at(hole.green_from)))
	var tops := PackedInt32Array()
	tops.resize(hole.length)
	for x in hole.length:
		var water := hole.kind_at(x + 0.5) == GolfCourse.Kind.WATER
		tops[x] = WORLD_H if water else int(round(hole.height_at(x + 0.5)))
	for x in hole.length:
		var top := tops[x]
		if top >= WORLD_H:
			continue
		var kind := hole.kind_at(x + 0.5)
		var left := tops[x - 1] if x > 0 else top
		var right := tops[x + 1] if x < hole.length - 1 else top
		var tx := x % TILE
		for y in range(maxi(top, 0), WORLD_H):
			var depth := y - top
			var c: Color
			if y < left or y < right:
				c = HUD_SHADOW
			elif kind == GolfCourse.Kind.SAND:
				c = sand.get_pixel(tx, depth) if depth < TILE else sand_in.get_pixel(tx, y % TILE)
			elif kind == GolfCourse.Kind.DECK:
				# Палуба и борт под ней на `HULL_DEPTH`, ниже борт ушёл в песок.
				if depth >= HULL_DEPTH:
					c = sand_in.get_pixel(tx, y % TILE)
				else:
					c = deck.get_pixel(tx, depth) if depth < TILE else hull.get_pixel(tx, depth % TILE)
			else:
				# Корма: доски вровень с палубой грина, низ в песке, как у палубы.
				if y >= green_y + HULL_DEPTH:
					c = sand_in.get_pixel(tx, y % TILE)
				else:
					c = HUD_SHADOW if depth == 0 else hull.get_pixel(tx, posmod(y - green_y, TILE))
			img.set_pixel(x, y, c)
	_terrain_tex = ImageTexture.create_from_image(img)


func _tile_image(name: String) -> Image:
	var im := (tex[name] as Texture2D).get_image()
	if im.is_compressed():
		im.decompress()
	im.convert(Image.FORMAT_RGBA8)
	return im


## Статичный фон в координатах экрана из цветов сеттинга, как у платформера: полосы неба,
## светило, острова на горизонте, море с бликами.
func _draw_backdrop() -> void:
	var horizon := roundf(view.y * 0.72)
	var bands := scene_set.sky_bands
	var band_h := horizon / maxi(bands.size(), 1)
	for i in bands.size():
		backdrop.draw_rect(Rect2(0, roundf(i * band_h), view.x, ceilf(band_h) + 1), bands[i])
	var sun := Vector2(view.x - 56.0, 34.0)
	for r in [[Vector2(-6, -12), Vector2(12, 24)], [Vector2(-12, -6), Vector2(24, 12)], [Vector2(-10, -10), Vector2(20, 20)]]:
		backdrop.draw_rect(Rect2(sun + r[0], r[1]), scene_set.sun)
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
	backdrop.draw_rect(Rect2(0, horizon, view.x, view.y - horizon), scene_set.horizon)
	for i in 10:
		var y := horizon + 3 + i * 6
		var bx := fmod(i * 37.0, view.x - 24.0)
		backdrop.draw_rect(Rect2(bx, y, 8 + (i % 3) * 6, 1), scene_set.horizon_light)


## HUD в координатах экрана: лунка «1/3» и пар слева, удары с бочонком, ветер стрелкой и
## делениями справа; в прицеле шкала силы с отметкой прошлого удара и угол внизу слева;
## заставка лунки и результат лунки крупно по центру; мяч над экраном и лунка за краем метками.
func _draw_hud() -> void:
	var top := 3.0
	_draw_icon(FLAG_ICON, Vector2(4, top))
	draw_pixel_text(hud, Vector2(13, top), "%d/%d" % [hole_index + 1, course.holes.size()], HUD_INK, HUD_SHADOW)
	draw_pixel_text(hud, Vector2(48, top), "ПАР %d" % hole.par, HUD_INK, HUD_SHADOW)
	if is_pink("ball"):
		hud.draw_rect(Rect2(98, top + 1, 6, 6), PINK)
	else:
		hud.draw_texture(tex["golf_ball"], Vector2(97, top))
	draw_pixel_text(hud, Vector2(109, top), str(strokes), HUD_INK, HUD_SHADOW)
	if not scores.is_empty():
		var diff := total_strokes() - _par_played()
		draw_pixel_text(hud, Vector2(133, top), "ПАР" if diff == 0 else "%+d" % diff, HUD_INK, HUD_SHADOW)
	_draw_wind(Vector2(view.x - 4.0, top))
	if phase == Phase.AIM:
		_draw_meter(Vector2(4, view.y - 13.0))
	if phase == Phase.INTRO:
		var big := 6.0
		var t1 := "%d/%d" % [hole_index + 1, course.holes.size()]
		draw_pixel_text(hud, (Vector2(view.x / 2.0 - t1.length() * 2.0 * big, view.y * 0.28)).round(), t1, HUD_INK, HUD_SHADOW, big)
		var t2 := "ПАР %d" % hole.par
		draw_pixel_text(hud, (Vector2(view.x / 2.0 - t2.length() * 2.0 * 3.0, view.y * 0.28 + 40.0)).round(), t2, HUD_INK, HUD_SHADOW, 3.0)
	elif phase == Phase.HOLED:
		var diff := strokes - hole.par
		var t := "ПАР" if diff == 0 else "%+d" % diff
		var big := 6.0
		draw_pixel_text(hud, (Vector2(view.x / 2.0 - t.length() * 2.0 * big, view.y * 0.28)).round(), t, HUD_INK, HUD_SHADOW, big)
	var ball_screen := Vector2(ball.pos.x - cam_x, ball.pos.y + _origin_y)
	if ball.moving() and ball_screen.y < 14.0:
		# Мяч над экраном: стрелка вверх над ним.
		var bx := roundf(clampf(ball_screen.x, 4.0, view.x - 4.0))
		for i in 3:
			hud.draw_rect(Rect2(bx - i, 15 + i, 1 + 2 * i, 1), HUD_INK)
	if phase == Phase.AIM:
		var cup_screen := hole.cup_x - cam_x
		if cup_screen > view.x - 2.0 or cup_screen < 2.0:
			# Лунка за краем: флажок со стрелкой у края на её высоте.
			var right := cup_screen > view.x
			var y := roundf(hole.height_at(hole.cup_x) + _origin_y - 14.0)
			var ex := view.x - 12.0 if right else 6.0
			_draw_icon(FLAG_ICON, Vector2(ex, y))
			for i in 3:
				var ax := ex + 8.0 + i if right else ex - 2.0 - i
				hud.draw_rect(Rect2(ax, y + 3 - (2 - i), 1, 1 + 2 * (2 - i)), HUD_INK)


## Ветер у правого края: деления цифрой, стрелка по направлению, длиннее с силой.
func _draw_wind(right_top: Vector2) -> void:
	var w := _wind_now()
	var digit_x := right_top.x - 8.0
	draw_pixel_text(hud, Vector2(digit_x, right_top.y), str(absi(w)), HUD_INK, HUD_SHADOW)
	if w == 0:
		return
	var length := 6.0 + 5.0 * absi(w)
	var x1 := digit_x - 5.0
	var x0 := x1 - length
	var y := right_top.y + 4.0
	for pass_ in 2:
		var off := Vector2(1, 1) if pass_ == 0 else Vector2.ZERO
		var c := HUD_SHADOW if pass_ == 0 else HUD_INK
		hud.draw_rect(Rect2(Vector2(x0, y) + off, Vector2(length, 2)), c)
		for i in 4:
			var hx := x1 - 3 + i if w > 0 else x0 + 3 - i
			hud.draw_rect(Rect2(Vector2(hx, y - 3 + i) + off, Vector2(1, 8 - 2 * i)), c)


## Шкала силы 52×9 и угол в градусах справа от неё.
func _draw_meter(at: Vector2) -> void:
	var w := 52.0
	hud.draw_rect(Rect2(at + Vector2(1, 1), Vector2(w, 9)), HUD_SHADOW)
	hud.draw_rect(Rect2(at, Vector2(w, 9)), HUD_SHADOW)
	hud.draw_rect(Rect2(at + Vector2(1, 1), Vector2(w - 2, 7)), HUD_DIM)
	if charging:
		hud.draw_rect(Rect2(at + Vector2(1, 1), Vector2(roundf((w - 2) * meter), 7)), METER_FILL)
	if last_power >= 0.0:
		hud.draw_rect(Rect2(at + Vector2(1 + roundf((w - 3) * last_power), 0), Vector2(1, 9)), HUD_INK)
	draw_pixel_text(hud, at + Vector2(w + 6.0, 0.0), "%d°" % angle, HUD_INK, HUD_SHADOW)


func _draw_icon(rows: Array[String], pos: Vector2) -> void:
	for pass_ in 2:
		for ry in rows.size():
			for rx in rows[ry].length():
				if rows[ry][rx] == "1":
					var p := pos + Vector2(rx, ry) + (Vector2(1, 1) if pass_ == 0 else Vector2.ZERO)
					hud.draw_rect(Rect2(p, Vector2.ONE), HUD_SHADOW if pass_ == 0 else HUD_INK)
