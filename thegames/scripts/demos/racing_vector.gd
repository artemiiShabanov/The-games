extends Demo
## Демка гонки × вектор, каталог `docs/specs/demos_catalog.md`: «полосы» (#91, решение
## 2026-11-11: не машина с инерцией и заносом, а геймплей попроще и под технологию). Вид
## сверху, дорога из четырёх полос едет навстречу, машина внизу экрана. Влево и вправо
## перестроение на соседнюю полосу одним шагом, A газ, пока держишь; без газа машина катится
## медленнее соперников. Препятствие или соперник впереди сбрасывают скорость и на время
## выключают газ. Трое соперников стартуют впереди; цель прийти к финишу первым, а если первым
## финиширует соперник, заезд кончается провалом. Руля, инерции и заноса нет: всё на тайминге
## перестроений и на том, когда отпустить газ.
## Заезд из `LaneRaceGen` по сиду записи: ряды препятствий, полосы, форы и темп соперников.
## Правила, соперники и боты живут в `LaneSim` (без окна, им же проверяются сто сидов); демка
## ведёт его шагами, рисует и озвучивает его события. Рисуется на `VectorScreen` в логических
## пикселях карточки: края дороги и пунктир полос, машины и препятствия контурами слотов
## сеттинга, слева шкала заезда с метками машин, справа место и шкала скорости штрихами.
##
## Баги по флагам записи (параметры в `resources/bugs/<id>.tres`). Общие (#44) и баг технологии
## `beam_lag` живут в `Demo` и `VectorScreen`, демка только зовёт хуки: фризы `bug_frame`,
## заикание пищалки, газ и перестроение с опозданием, залипшее перестроение (повторяется, когда
## машина встала в полосу), розовые заглушки вместо соперников, препятствий или флага. Свои
## проявления: `wild_physics` гололёд, машину проносит лишнюю полосу, соперники быстрее;
## `through_walls` край дороги не держит, можно ехать по обочине, где нет ни препятствий, ни
## соперников; `unreachable_coins` финишная черта нарисована на обочине и раньше настоящей,
## настоящая на дороге не видна; `sneeze_enemies` соперник от касания уходит на обочину и
## сбрасывает ход.

const LANE_W := 140.0
## Центр машины игрока на экране: дорога видна на столько пикселей вперёд.
const CAR_Y := 708.0
## Логических пикселей на пиксель спрайта: машина и препятствие.
const CAR_PX := 6.0
const ROCK_PX := 5.0
const INK_WORLD := 1
const INK_HERO := 2
const INK_DANGER := 3
const DASH := 56.0
const POST_EVERY := 208.0
const FLASH_SECONDS := 0.25
const PLACEHOLDER_SLOTS: Array[String] = ["rival", "obstacle", "finish"]
const MELODY := [0, 0, 12, null, 7, 7, 12, null, 3, 3, 15, null, 10, 10, 15, null,
	5, 5, 17, null, 12, 12, 17, 15, 12, null, 10, null, 7, 5, 3, null]

var tuning: RacingVectorTuning
var race: LaneRace
var sim: LaneSim
var bot_gas := false

var _time := 0.0
var _flash := 0.0
## Залипшее перестроение: в какую сторону повторить, когда машина встанет в полосу.
var _stick_dir := 0
var _was_shifting := false
## Баг баланса: насколько раньше настоящей нарисована финишная черта (на обочине); 0 без бага.
var _finish_early := 0.0
var _music: AudioStreamPlayer
var _sfx := {}


func _on_start() -> void:
	tuning = RacingVectorTuning.load_default()
	race = LaneRaceGen.generate(record.seed if record != null else 1)
	sim = LaneSim.create(race, tuning)
	# Баги жанра и баланса; общие баги в `Demo` (#44).
	if has_bug(&"wild_physics"):
		sim.slide = maxi(int(round(bug_param(&"wild_physics", &"lane_slide", 1.0))), 0)
		sim.rival_mult = bug_param(&"wild_physics", &"lane_rival_mult", 1.12)
	sim.walls_open = has_bug(&"through_walls")
	if has_bug(&"sneeze_enemies"):
		sim.sneeze = true
		sim.sneeze_off_s = bug_param(&"sneeze_enemies", &"off_track_s", 2.5)
		sim.sneeze_throttle = bug_param(&"sneeze_enemies", &"off_track_throttle", 0.5)
	if has_bug(&"unreachable_coins"):
		_finish_early = bug_param(&"unreachable_coins", &"lane_finish_early", 1500.0)
	vector_screen(_draw_vector)
	_setup_audio()


func _setup_audio() -> void:
	_music = Sfx.music(Sfx.beeper_loop(MELODY, 168.0), tuning.music_db if not embedded else -80.0)
	add_child(_music)
	bug_music = _music
	if not embedded:
		_music.play()
	_sfx["shift"] = Sfx.player(Sfx.beep(520.0, 0.05, 0.2, 660.0))
	_sfx["edge"] = Sfx.player(Sfx.beep(150.0, 0.06, 0.25))
	_sfx["crash"] = Sfx.player(Sfx.beep(240.0, 0.3, 0.3, 70.0))
	_sfx["bump"] = Sfx.player(Sfx.beep(200.0, 0.14, 0.3, 110.0))
	_sfx["spin"] = Sfx.player(Sfx.beep(520.0, 0.18, 0.25, 130.0))
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
		AutoTest.note("racing vector: %s за %.1f с, место %d из %d, столкновений %d" % [
				"первый" if goal else "не первый", elapsed, sim.place(), sim.rivals.size() + 1, sim.player.crashes])


func _result_title(goal: bool) -> String:
	return "добрался первым" if goal else "не добрался"


func _result_caption() -> String:
	return "место %d из %d · столкновений %d · %d с" % [sim.place(), sim.rivals.size() + 1, sim.player.crashes,
			int(round(elapsed))]


# --- Ввод ------------------------------------------------------------------------------------

func _game_input(event: InputEvent) -> void:
	# С багом управления нажатие уходит в очередь с задержкой (`Demo.bug_press`).
	if event.is_action_pressed(GameInput.LEFT):
		bug_press(_shift.bind(-1))
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed(GameInput.RIGHT):
		bug_press(_shift.bind(1))
		get_viewport().set_input_as_handled()


## Перестроение; с багом управления оно залипает и повторится, когда машина встанет в полосу.
func _shift(dir: int) -> void:
	if running and sim.shift(dir):
		_stick_dir = dir
		bug_stick()


## Бот `LaneSim`: газ и перестроение через `_shift`, чтобы залипание задело и его.
func _bot_step(_delta: float) -> void:
	bot_gas = sim.bot(active_bot_mode())
	if sim.bot_shift != 0:
		_shift(sim.bot_shift)


# --- Шаг -------------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	# Фризы на ходу с догоном времени (`Demo.bug_frame`).
	bug_frame(delta, true, _step)


func _step(dt: float) -> void:
	_time += dt
	_flash = maxf(_flash - dt, 0.0)
	step_shards(dt)
	bug_input_tick()
	# Газ: с багом управления из прошлого на delay_ms (`Demo.bug_axis`).
	var raw := bot_gas if bot_driven() else Input.is_action_pressed(GameInput.A)
	sim.step(dt, bug_axis(Vector2(1.0 if raw else 0.0, 0.0)).x > 0.5)
	for ev in sim.events:
		_on_event(ev)
	sim.events.clear()
	# Машина встала в полосу: залипшее перестроение повторяется.
	var shifting := absf(sim.player.x - sim.player.lane) > 0.01
	if _was_shifting and not shifting and running and bug_take_stick():
		_shift(_stick_dir)
	_was_shifting = shifting


## Событие правил: звук, эффект, конец демки.
func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"shift":
			_play("shift")
		&"edge":
			_play("edge")
		&"crash":
			_break_obstacle(int(ev[1]))
			_flash = FLASH_SECONDS
			bug_clear_stick()
			_play("crash")
		&"rival_crash":
			_break_obstacle(int(ev[1]))
		&"bump":
			_flash = FLASH_SECONDS
			bug_clear_stick()
			_play("bump")
		&"spin":
			_play("spin")
		&"win":
			end_demo(true)
		&"lose":
			end_demo(false)


## Разбитое препятствие рассыпается на отрезки, они уезжают назад вместе с дорогой.
func _break_obstacle(i: int) -> void:
	var o := race.obstacles[i]
	if is_pink("obstacle"):
		return
	shatter_slot(&"obstacle", Vector2(_lane_x(o.x), _y(o.y)), ROCK_PX, INK_WORLD, false, 0.0,
			Vector2(0.0, sim.player.speed * 0.5))


# --- Рисование -------------------------------------------------------------------------------

func _road_left() -> float:
	return (vector.logical_size.x - race.lanes * LANE_W) / 2.0


## Центр полосы `lane` (дробной: машина в перестроении) на экране.
func _lane_x(lane: float) -> float:
	return _road_left() + (lane + 0.5) * LANE_W


## Расстояние от старта в координату экрана: игрок стоит на `CAR_Y`, впереди вверх.
func _y(dist: float) -> float:
	return CAR_Y - (dist - sim.player.dist)


func _draw_vector(v: VectorScreen) -> void:
	if sim == null:
		return
	var size := v.logical_size
	var left := _road_left()
	var right := left + race.lanes * LANE_W
	var dist := sim.player.dist
	# Края дороги сплошными, полосы пунктиром; пунктир и столбики едут назад со скоростью машины.
	v.line(Vector2(left, 0.0), Vector2(left, size.y), INK_WORLD, 3.0)
	v.line(Vector2(right, 0.0), Vector2(right, size.y), INK_WORLD, 3.0)
	var shift := fposmod(dist, DASH * 2.0)
	for l in range(1, race.lanes):
		var x := left + l * LANE_W
		var y := -DASH * 2.0 + shift
		while y < size.y:
			v.line(Vector2(x, y), Vector2(x, y + DASH), INK_WORLD, 2.0, 0.45)
			y += DASH * 2.0
	var post := -POST_EVERY + fposmod(dist, POST_EVERY)
	while post < size.y:
		v.line(Vector2(left - 54.0, post), Vector2(left - 26.0, post), INK_WORLD, 2.0, 0.5)
		v.line(Vector2(right + 26.0, post), Vector2(right + 54.0, post), INK_WORLD, 2.0, 0.5)
		post += POST_EVERY
	# Старт и финиш. С багом баланса черта нарисована на обочине и раньше настоящей.
	_draw_line_across(v, 0.0, left, right)
	if _finish_early > 0.0:
		_draw_line_across(v, race.length - _finish_early, left - 300.0, left - 70.0)
		_draw_flag(race.length - _finish_early, left - 340.0)
	else:
		_draw_line_across(v, race.length, left, right)
		_draw_flag(race.length, left - 96.0)
		_draw_flag(race.length, right + 96.0)
	# Препятствия, соперники, машина игрока.
	for i in race.obstacles.size():
		var o := race.obstacles[i]
		var y := _y(o.y)
		if sim.broken[i] or y < -60.0 or y > size.y + 60.0:
			continue
		draw_slot(&"obstacle", Vector2(_lane_x(o.x), y), ROCK_PX)
	for r in sim.rivals:
		var y := _y(r.dist)
		if y < -80.0 or y > size.y + 80.0:
			continue
		var angle := -PI / 2.0 + (r.lane - r.x) * 0.3
		if r.off > 0.0:
			angle += sin(_time * 16.0 + r.index) * 0.5
		draw_slot(&"rival", Vector2(_lane_x(r.x), y), CAR_PX, false, angle)
	var p := sim.player
	if p.stun <= 0.0 or fmod(p.stun, 0.16) < 0.08 or not running:
		draw_slot(&"vehicle", Vector2(_lane_x(p.x), CAR_Y), CAR_PX, false, -PI / 2.0 + (p.lane - p.x) * 0.3)
	if _flash > 0.0:
		var c := Vector2(_lane_x(p.x), CAR_Y - 50.0)
		for k in 6:
			var dir := Vector2.from_angle(-PI / 2.0 + (k - 2.5) * 0.45)
			v.line(c + dir * 14.0, c + dir * (34.0 + 20.0 * _flash / FLASH_SECONDS), INK_DANGER, 2.5, _flash / FLASH_SECONDS)
	draw_shards()
	_draw_progress(v, size)
	_draw_hud(v, size, right)


## Поперечная черта старта или финиша: две линии с решёткой крест-накрест между ними.
func _draw_line_across(v: VectorScreen, dist: float, x0: float, x1: float) -> void:
	var y := _y(dist)
	if y < -40.0 or y > v.logical_size.y + 40.0:
		return
	v.line(Vector2(x0, y - 14.0), Vector2(x1, y - 14.0), INK_WORLD, 2.5)
	v.line(Vector2(x0, y + 14.0), Vector2(x1, y + 14.0), INK_WORLD, 2.5)
	var x := x0
	while x < x1 - 1.0:
		var w := minf(28.0, x1 - x)
		v.line(Vector2(x, y - 14.0), Vector2(x + w, y + 14.0), INK_WORLD, 2.0, 0.7)
		v.line(Vector2(x + w, y - 14.0), Vector2(x, y + 14.0), INK_WORLD, 2.0, 0.7)
		x += 28.0


func _draw_flag(dist: float, x: float) -> void:
	var y := _y(dist)
	if y > -80.0 and y < vector.logical_size.y + 80.0:
		draw_slot(&"finish", Vector2(x, y - 30.0), 4.0)


## Шкала заезда слева: старт внизу, финиш наверху, метки машин по пройденному пути.
func _draw_progress(v: VectorScreen, size: Vector2) -> void:
	var x := 120.0
	var y0 := size.y - 96.0
	var y1 := 150.0
	v.line(Vector2(x, y0), Vector2(x, y1), INK_WORLD, 2.0, 0.6)
	v.line(Vector2(x - 18.0, y0), Vector2(x + 18.0, y0), INK_WORLD, 2.0, 0.6)
	v.line(Vector2(x - 18.0, y1), Vector2(x + 18.0, y1), INK_WORLD, 2.5)
	draw_slot(&"finish", Vector2(x, y1 - 44.0), 3.0)
	for r in sim.rivals:
		var y := lerpf(y0, y1, clampf(r.dist / race.length, 0.0, 1.0))
		v.poly(PackedVector2Array([Vector2(x + 10.0, y), Vector2(x + 30.0, y - 9.0), Vector2(x + 30.0, y + 9.0)]),
				INK_DANGER, true, 2.0)
	var py := lerpf(y0, y1, clampf(sim.player.dist / race.length, 0.0, 1.0))
	v.poly(PackedVector2Array([Vector2(x - 10.0, py), Vector2(x - 34.0, py - 11.0), Vector2(x - 34.0, py + 11.0)]),
			INK_HERO, true, 2.5)


## Справа место из числа машин и шкала скорости штрихами: чем больше горит, тем быстрее.
func _draw_hud(v: VectorScreen, size: Vector2, road_right: float) -> void:
	var x := road_right + (size.x - road_right) / 2.0
	var where := "%d/%d" % [sim.place(), sim.rivals.size() + 1]
	v.digits(Vector2(x - VectorScreen.digits_width(where, 72.0) / 2.0, 60.0), where, 72.0, INK_HERO, 3.0)
	var bars := 8
	var lit := int(round(bars * clampf((sim.player.speed - tuning.crash_speed) / (tuning.gas_speed - tuning.crash_speed), 0.0, 1.0)))
	for i in bars:
		var y := size.y - 120.0 - i * 34.0
		var w := 30.0 + i * 7.0
		var on := i < lit
		v.line(Vector2(x - w, y), Vector2(x + w, y), INK_HERO if on else INK_WORLD, 4.0 if on else 2.0, 1.0 if on else 0.3)
