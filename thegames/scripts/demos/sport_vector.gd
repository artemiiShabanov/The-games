extends Demo
## Демка спорт × вектор, каталог `docs/specs/demos_catalog.md`: понг против ИИ (#93). Ракетка
## игрока слева, вверх и вниз; соперник справа. Мяч отскакивает от стенок и ракеток, от края
## ракетки под углом круче, с каждым ударом быстрее. Матч до пяти очков: таймера у демок нет
## (решение 2026-11-05), поэтому не «больше очков за минуту», а кто первым наберёт.
## Матч из `PongMatchGen` по сиду записи: скорость, ошибка и запоздание соперника, углы подач.
## Правила, соперник и боты живут в `PongSim` (без окна, им же проверяются сто сидов); демка
## ведёт его шагами, рисует и озвучивает его события. Рисуется на `VectorScreen` в логических
## пикселях карточки: стенки, пунктир сетки, ракетки прямоугольниками, мяч контуром слота с
## хвостом, счёт штрихами; за ракетками стоят герой и враг сеттинга.
##
## Баги по флагам записи (параметры в `resources/bugs/<id>.tres`). Общие (#44) и баг технологии
## `beam_lag` живут в `Demo` и `VectorScreen`, демка только зовёт хуки: фризы `bug_frame`,
## заикание пищалки, ход ракетки с опозданием, залипший ход (ракетка едет ещё, когда кнопку
## отпустили), розовые заглушки вместо врага или мяча. Свои проявления: `ball_to_space` (баг
## жанра) мяч через несколько отскоков залипает в стенке, дрожит и улетает за край поля, это
## аут того, кто бил последним; `wild_physics` попрыгунчик: мяч быстрее от каждой стенки и
## отскакивает под случайным углом; `unreachable_coins` соперник непробиваемый: ракетка выше и
## быстрее, не ошибается, мяч ускоряется без потолка; `sneeze_enemies` ракетка соперника
## рассыпается от первого касания мяча.

const INK_WORLD := 1
const INK_HERO := 2
const INK_DANGER := 3
const BALL_PX := 2.2
const FACE_PX := 2.5
const TRAIL := 10
const FLASH_SECONDS := 0.35
const STICK_SECONDS := 0.25
const PLACEHOLDER_SLOTS: Array[String] = ["enemy", "ball"]
const MELODY := [0, null, null, 7, null, null, 3, null, 0, null, null, 7, null, 5, 3, null,
	-2, null, null, 5, null, null, 2, null, -2, null, null, 5, null, 3, 2, null]

var tuning: SportVectorTuning
var game: PongMatch
var sim: PongSim
var bot_axis := 0.0

var _time := 0.0
## Последние положения мяча: хвост.
var _trail: Array[Vector2] = []
## Вспышка у края поля, куда ушёл мяч: сторона (0 край игрока, 1 край соперника) и остаток.
var _flash_side := 0
var _flash := 0.0
var _hit_flash := [0.0, 0.0]
## Залипший ход ракетки: направление и сколько секунд она ещё едет сама.
var _stuck_dir := 0.0
var _stuck_left := 0.0
var _last_dir := 0.0
var _music: AudioStreamPlayer
var _sfx := {}


func _on_start() -> void:
	tuning = SportVectorTuning.load_default()
	game = PongMatchGen.generate(record.seed if record != null else 1)
	sim = PongSim.create(game, tuning, CardFrame.inner_size())
	# Баги жанра и баланса; общие баги в `Demo` (#44).
	if has_bug(&"ball_to_space"):
		sim.stick_every = maxi(int(bug_param(&"ball_to_space", &"pong_stick_every", 4.0)), 1)
		sim.stuck_seconds = bug_param(&"ball_to_space", &"stuck_s", 1.2)
	if has_bug(&"wild_physics"):
		sim.bounce_gain = bug_param(&"wild_physics", &"pong_bounce_gain", 0.15)
		sim.kick = deg_to_rad(bug_param(&"wild_physics", &"pong_kick_deg", 14.0))
		sim.wild_cap = bug_param(&"wild_physics", &"pong_speed_cap", 2000.0)
	if has_bug(&"unreachable_coins"):
		sim.ai_wall = true
		sim.ai_height_mult = bug_param(&"unreachable_coins", &"pong_ai_height_mult", 1.7)
		sim.ai_speed_mult = bug_param(&"unreachable_coins", &"pong_ai_speed_mult", 3.0)
	sim.ai_frail = has_bug(&"sneeze_enemies")
	vector_screen(_draw_vector)
	_setup_audio()


func _setup_audio() -> void:
	_music = Sfx.music(Sfx.beeper_loop(MELODY, 150.0), tuning.music_db if not embedded else -80.0)
	add_child(_music)
	bug_music = _music
	if not embedded:
		_music.play()
	_sfx["hit"] = Sfx.player(Sfx.beep(660.0, 0.06, 0.28))
	_sfx["hit_ai"] = Sfx.player(Sfx.beep(440.0, 0.06, 0.28))
	_sfx["wall"] = Sfx.player(Sfx.beep(330.0, 0.04, 0.22))
	_sfx["serve"] = Sfx.player(Sfx.beep(520.0, 0.05, 0.2))
	_sfx["point"] = Sfx.player(Sfx.beep(520.0, 0.25, 0.3, 1040.0))
	_sfx["miss"] = Sfx.player(Sfx.beep(260.0, 0.3, 0.3, 90.0))
	_sfx["stuck"] = Sfx.player(Sfx.beep(120.0, 0.3, 0.25, 140.0))
	_sfx["eject"] = Sfx.player(Sfx.beep(300.0, 0.35, 0.28, 1800.0))
	_sfx["shatter"] = Sfx.player(Sfx.beep(520.0, 0.18, 0.25, 130.0))
	_sfx["finish"] = Sfx.player(Sfx.beep(660.0, 0.5, 0.3, 1320.0))
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
		AutoTest.note("sport vector: %s %d:%d за %.1f с, ударов ракеток %d, отскоков от стенок %d" % [
				"выиграл" if goal else "проиграл", sim.score_player, sim.score_ai, elapsed, sim.hits, sim.wall_bounces])


func _result_title(goal: bool) -> String:
	return "выиграл" if goal else "проиграл"


func _result_caption() -> String:
	return "счёт %d:%d · %d с" % [sim.score_player, sim.score_ai, int(round(elapsed))]


# --- Ввод и шаг ------------------------------------------------------------------------------

func _bot_step(_delta: float) -> void:
	bot_axis = sim.bot(active_bot_mode())


func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	# Фризы в розыгрыше с догоном времени (`Demo.bug_frame`).
	bug_frame(delta, sim.state == PongSim.State.PLAY, _step)


func _step(dt: float) -> void:
	_time += dt
	_flash = maxf(_flash - dt, 0.0)
	for i in 2:
		_hit_flash[i] = maxf(float(_hit_flash[i]) - dt, 0.0)
	step_shards(dt)
	# Ход ракетки: с багом управления из прошлого на delay_ms (`Demo.bug_axis`).
	var axis := bug_axis(Vector2(0.0, bot_axis if bot_driven() else GameInput.axis().y)).y
	# Залипание: кнопку отпустили, а ракетка едет дальше ещё четверть секунды.
	var dir := signf(axis) if absf(axis) >= 0.3 else 0.0
	if dir != 0.0 and _last_dir == 0.0:
		bug_stick()
	if dir == 0.0 and _last_dir != 0.0 and bug_take_stick():
		_stuck_dir = _last_dir
		_stuck_left = STICK_SECONDS
	_last_dir = dir
	if _stuck_left > 0.0:
		_stuck_left -= dt
		if dir == 0.0:
			axis = _stuck_dir
	sim.step(dt, axis)
	for ev in sim.events:
		_on_event(ev)
	sim.events.clear()
	if sim.state == PongSim.State.PLAY or sim.state == PongSim.State.EJECT:
		_trail.append(sim.ball)
		if _trail.size() > TRAIL:
			_trail.remove_at(0)
	else:
		_trail.clear()


## Событие правил: звук, эффект, конец демки.
func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"serve":
			_play("serve")
		&"hit":
			_hit_flash[int(ev[1])] = 0.15
			_play("hit" if int(ev[1]) == 0 else "hit_ai")
		&"wall":
			_play("wall")
		&"point":
			# Очко игроку: мяч ушёл за край соперника, и наоборот.
			_flash_side = 1 - int(ev[1])
			_flash = FLASH_SECONDS
			_play("point" if int(ev[1]) == 0 else "miss")
		&"stuck":
			_play("stuck")
		&"eject":
			_play("eject")
		&"ai_shatter":
			shatter_poly(_paddle_rect(sim.ai_face() + tuning.paddle_width / 2.0, sim.ai_y, sim.ai_height()), INK_DANGER)
			_play("shatter")
		&"win":
			end_demo(true)
		&"lose":
			end_demo(false)


# --- Рисование -------------------------------------------------------------------------------

## Контур ракетки с серединой в `(x, y)` и высотой `height`.
func _paddle_rect(x: float, y: float, height: float) -> PackedVector2Array:
	var hw := tuning.paddle_width / 2.0
	var hh := height / 2.0
	return PackedVector2Array([Vector2(x - hw, y - hh), Vector2(x + hw, y - hh), Vector2(x + hw, y + hh), Vector2(x - hw, y + hh)])


func _draw_vector(v: VectorScreen) -> void:
	if sim == null:
		return
	var size := sim.size
	# Стенки и пунктир сетки.
	v.line(Vector2(0.0, sim.top()), Vector2(size.x, sim.top()), INK_WORLD, 3.0)
	v.line(Vector2(0.0, sim.bottom()), Vector2(size.x, sim.bottom()), INK_WORLD, 3.0)
	var y := sim.top() + 14.0
	while y < sim.bottom() - 14.0:
		v.line(Vector2(size.x / 2.0, y), Vector2(size.x / 2.0, y + 22.0), INK_WORLD, 2.0, 0.45)
		y += 44.0
	# Счёт штрихами по обе стороны сетки.
	var mine := "%d" % sim.score_player
	v.digits(Vector2(size.x / 2.0 - 70.0 - VectorScreen.digits_width(mine, 72.0), sim.top() + 28.0), mine, 72.0, INK_HERO, 3.0)
	v.digits(Vector2(size.x / 2.0 + 70.0, sim.top() + 28.0), "%d" % sim.score_ai, 72.0, INK_DANGER, 3.0)
	# Край поля вспыхивает там, куда ушёл мяч.
	if _flash > 0.0:
		var x := 6.0 if _flash_side == 0 else size.x - 6.0
		v.line(Vector2(x, sim.top()), Vector2(x, sim.bottom()), INK_HERO if _flash_side == 1 else INK_DANGER, 5.0, _flash / FLASH_SECONDS)
	# Ракетки и те, кто за ними стоит.
	var px := tuning.paddle_inset
	v.poly(_paddle_rect(px, sim.paddle_y, tuning.paddle_height), INK_HERO, true, 3.0 + 3.0 * float(_hit_flash[0]) / 0.15)
	draw_slot(&"hero", Vector2(30.0, sim.paddle_y), FACE_PX)
	if sim.ai_alive:
		v.poly(_paddle_rect(size.x - px, sim.ai_y, sim.ai_height()), INK_DANGER, true, 3.0 + 3.0 * float(_hit_flash[1]) / 0.15)
	draw_slot(&"enemy", Vector2(size.x - 30.0, sim.ai_y), FACE_PX, false)
	# Мяч: хвост из последних положений; на подаче мигает, в стенке дрожит.
	for i in range(1, _trail.size()):
		v.line(_trail[i - 1], _trail[i], INK_WORLD, 2.0, 0.5 * float(i) / _trail.size())
	var ball := sim.ball
	match sim.state:
		PongSim.State.SERVE:
			if fmod(_time, 0.3) < 0.18:
				draw_slot(&"ball", ball, BALL_PX)
		PongSim.State.STUCK:
			draw_slot(&"ball", ball + Vector2(sin(_time * 70.0) * 4.0, cos(_time * 53.0) * 2.0), BALL_PX)
		_:
			draw_slot(&"ball", ball, BALL_PX)
	draw_shards()
