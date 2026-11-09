extends Demo
## Демка гонки × 8-bit, каталог `docs/specs/demos_catalog.md`: вид сверху, камера едет за
## шлюпкой игрока, спрайт в 8 направлениях по непрерывному курсу, отмель-обочина замедляет,
## один круг против трёх соперников. Влево, вправо поворот, A газ, B тормоз и задний ход.
## Трасса из `RacingTrackGen` по сиду записи: замкнутая петля воды вокруг острова, отмель по
## краям, берег стеной, бочки и рифы у борта, буи по кромке. Цель: первым пройти круг, итог
## «добрался первым»; финишировал не первым или все три соперника финишировали раньше: «не
## добрался». Страховка `max_seconds` тоже кончает гонку провалом. Перед стартом отсчёт 3-2-1.
## Соперники едут по средней линии в своих рядах с разбросом скорости по сиду, сбрасывают
## скорость перед поворотами, объезжают препятствия с другого борта; машины расталкиваются, но
## не проходят друг сквозь друга. Застрявший бот сдаёт назад, а затем встаёт на среднюю линию.
## Виртуальный экран ×4 в карточке (×2 во встроенном режиме), но без SubViewport, как у
## платформера: слои `world` и `hud` увеличены целым масштабом, камера и шлюпки ходят по
## пикселям экрана (плейтест 2026-11-09: фон дёргался шагами по 2-3 пикселя демки). Статичная
## карта и мини-карта запечены в текстуры на старте; `hud` поверх (место, полоса круга,
## мини-карта).
## Спрайты из сеттинга записи (`SettingDef`, слоты гонок пока только у пиратов).
##
## Баги по флагам записи (параметры в `resources/bugs/<id>.tres`). Общие (#44) механикой живут
## в `Demo`: `frame_drops` фризы в движении; `audio_stutter` заикание музыки и звуки с
## задержкой; `sticky_input` руль и газ с опозданием, отпущенный газ сам включается рывками;
## `pink_placeholders` соперники, бочки, рифы, буи или финиш розовыми квадратами;
## `alien_palette` весь слой мира в сдвинутых цветах; `sprite_flicker` спрайты сверх лимита на
## строке тайлов через кадр. Свои проявления: `wild_physics` шлюпки скользят, как по льду, а
## соперники быстрее (`grip_mult`, `rival_speed_mult`); `sneeze_enemies` соперник от касания
## игрока крутится и сходит с трассы на отмель, потом возвращается; `unreachable_coins`
## финишная черта нарисована на берегу, а засчитывается по-прежнему на воде;
## `through_walls` (жанровый баг гонок, #49) шлюпку периодически выносит сквозь берег на
## песок, потом ставит обратно на среднюю линию.

class Car:
	var pos := Vector2.ZERO
	var vel := Vector2.ZERO
	var heading := 0.0
	var speed := 0.0
	## Ближайшая точка средней линии и пройденные точки без свёртки: круг при `track.count()`.
	var idx := 0
	var progress := 0
	var best := 0
	var finished := false
	var place := 0
	var player := false
	## Ряд соперника: боковой сдвиг от средней линии в пикселях.
	var lane := 0.0
	## Предельная скорость как доля игрока.
	var top := 1.0
	var spin := 0.0
	## Баг «сквозь стены»: секунд полёта без столкновений и мигание после возврата на трассу.
	var ghost := 0.0
	var blink := 0.0
	## Баг «чих»: секунд схода с трассы и борт, к которому соперника несёт.
	var offroad := 0.0
	var offroad_side := 1.0
	var stall := 0.0
	var reverse_left := 0.0
	var bump_cd := 0.0
	var wake_timer := 0.0
	var finish_time := 0.0


const SCALE := 4
## Увеличение во встроенном режиме (запись стрима в ленте).
const EMBED_SCALE := 2
const TILE := RacingTrack.TILE
const CARS := 4
const WAKE_LIFE := 0.6
const HUD_INK := Color("#F4EFE6")
const HUD_SHADOW := Color("#161412")
const HUD_DIM := Color(0.086, 0.078, 0.071, 0.55)
const RIVAL_INK := Color("#F2C85A")
const MINIMAP_BOX := Vector2(56.0, 38.0)
## Что может стать розовой заглушкой; своя шлюпка, вода и берег никогда.
const PLACEHOLDER_SLOTS: Array[String] = ["rival", "barrel", "rock", "buoy", "finish"]
const SPRITES: Array[String] = ["race_water", "race_water_1", "race_shallow", "race_sand", "race_sand_1",
	"race_rock", "race_barrel", "race_buoy", "race_finish"]
const MELODY := [0, null, 7, 5, 7, null, 12, null, 10, null, 7, 5, 3, null, 5, null,
	0, null, 7, 5, 7, null, 12, 14, 15, null, 14, 12, 10, null, 7, null]
const BASS := [-12, -12, -5, -5, -9, -9, -7, -7, -12, -12, -5, -5, -4, -4, -7, -7]

var tuning: RacingDemoTuning
var track: RacingTrack
## Виртуальный экран в пикселях демки: внутренность карточки, делённая на `SCALE`.
var view := Vector2(416, 208)
## Увеличение: `SCALE` в карточке, `EMBED_SCALE` в ленте.
var scale_px := SCALE
var tex := {}
var world: Node2D
var hud: Node2D
var cars: Array[Car] = []
var player: Car
var cam := Vector2.ZERO
var count_left := 0.0
var race_time := 0.0
var finish_order := 0
var bots_finished := 0
var bumps := 0
## Сеттинг записи: спрайты.
var scene_set: SettingDef
## Пена за кормой: позиция и остаток жизни.
var _wake: Array[Vector3] = []
var _lead := Vector2.ZERO
var _lead_vel := Vector2.ZERO
## Статичная карта (вода, отмель, берег, финиш) и мини-карта запечены в текстуры на старте.
var _map_tex: ImageTexture
var _minimap_tex: ImageTexture
var _bot_lane := 0.0
var _lane_hold := 0.0
var _last_count := -1
## Залипание газа: газ был нажат, остаток рывка, пауза до следующего.
var _gas_held := false
var _burst := 0.0
var _stick_gap := 0.0
## Замеры времени под автотестом: ключ → (сумма, максимум, число) в микросекундах.
var _perf: Dictionary[String, Vector3i] = {}
var _perf_last := 0

# Звук.
var _music: AudioStreamPlayer
var _sfx := {}

# Баги жанра и баланса; общие баги в `Demo` (#44).
var _grip_mult := 1.0
var _rival_mult := 1.0
## «Сквозь стены»: до следующего вылета и сколько их было.
var _wall_timer := 0.0
var _wall_count := 0
var _finish_on_shore := false


func _on_start() -> void:
	tuning = RacingDemoTuning.load_default()
	scene_set = SettingDef.of(record.setting)
	track = RacingTrackGen.generate(record.seed)
	_setup_bugs()
	for i in 8:
		tex["boat_%d" % i] = scene_set.sprite("boat_%d" % i)
		tex["rival_%d" % i] = scene_set.sprite("rival_%d" % i)
	for name in SPRITES:
		tex[name] = scene_set.sprite(name)
	scale_px = EMBED_SCALE if embedded else SCALE
	var area := embed_size if embedded else CardFrame.inner_size()
	view = (area / scale_px).floor()
	# Сцена без SubViewport: мир и HUD увеличены целым `scale_px` с ближайшим соседом, так арт
	# остаётся чётким, а камера и шлюпки двигаются по пикселям экрана, а не по пикселям демки.
	# На ×4 скорость 125 px/с давала шаги фона то 2, то 3 пикселя демки (8 и 12 экранных) за
	# кадр, по диагонали лесенкой: это и читалось как рывки.
	var stage := Control.new()
	stage.position = ((area - view * scale_px) / 2.0).floor()
	stage.size = view * scale_px
	stage.clip_contents = true
	stage.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	stage.mouse_filter = Control.MOUSE_FILTER_IGNORE
	screen.add_child(stage)
	# Фон под картой: берег за краем, если карта меньше экрана.
	var under := ColorRect.new()
	under.color = Color("#F2C85A")
	under.size = stage.size
	under.mouse_filter = Control.MOUSE_FILTER_IGNORE
	stage.add_child(under)
	world = Node2D.new()
	world.scale = Vector2.ONE * scale_px
	if bug_palette() != null:
		world.material = bug_palette()
	world.draw.connect(_draw_world)
	stage.add_child(world)
	hud = Node2D.new()
	hud.scale = Vector2.ONE * scale_px
	hud.draw.connect(_draw_hud)
	stage.add_child(hud)
	var t0 := Time.get_ticks_usec()
	_bake_map()
	_bake_minimap()
	_perf_add("bake", Time.get_ticks_usec() - t0)
	_spawn_cars()
	count_left = tuning.countdown
	_setup_audio()
	_update_camera(0.0)


## Решётка старта за линией финиша: два ряда по два, игрок последним справа.
func _spawn_cars() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed, ":racers"))
	var n := track.count()
	for slot in CARS:
		var c := Car.new()
		var row := slot / 2
		var side := -1.0 if slot % 2 == 0 else 1.0
		c.idx = n - tuning.grid_back - row * tuning.grid_row_gap
		c.progress = c.idx - n
		c.best = c.progress
		c.lane = side * tuning.bot_lane
		c.pos = (track.points[c.idx] + track.normals[c.idx] * c.lane).round()
		c.heading = track.tangents[c.idx].angle()
		c.vel = Vector2.ZERO
		c.player = slot == CARS - 1
		c.top = 1.0 if c.player else rng.randf_range(tuning.bot_speed_min, tuning.bot_speed_max)
		cars.append(c)
		if c.player:
			player = c
	_bot_lane = player.lane


func _setup_audio() -> void:
	_music = Sfx.player(Sfx.chiptune_loop(MELODY, BASS, 168.0), tuning.music_db if not embedded else -80.0)
	add_child(_music)
	bug_music = _music
	if not embedded:
		_music.play()
	_sfx["count"] = Sfx.player(Sfx.blip(440.0, 0.12, 0.35, 18.0))
	_sfx["go"] = Sfx.player(Sfx.blip(880.0, 0.25, 0.4, 10.0))
	_sfx["bump"] = Sfx.player(Sfx.thud(0.12, 0.45))
	_sfx["spin"] = Sfx.player(Sfx.blip(262.0, 0.2, 0.3, 14.0))
	_sfx["warp"] = Sfx.player(Sfx.blip(1046.0, 0.3, 0.3, 8.0))
	_sfx["finish"] = Sfx.player(Sfx.blip(880.0, 0.5, 0.45, 5.0))
	_sfx["lose"] = Sfx.player(Sfx.blip(196.0, 0.4, 0.45, 6.0))
	for p in _sfx.values():
		(p as AudioStreamPlayer).volume_db = tuning.sfx_db if not embedded else -80.0
		add_child(p)


## Баги жанра и баланса: лёд и быстрые соперники, финиш на берегу; общие ставит `Demo`.
func _setup_bugs() -> void:
	if has_bug(&"wild_physics"):
		_grip_mult = bug_param(&"wild_physics", &"grip_mult", 0.25)
		_rival_mult = bug_param(&"wild_physics", &"rival_speed_mult", 1.6)
	_finish_on_shore = has_bug(&"unreachable_coins")
	# Первый вылет сквозь берег в первые секунды гонки, чтобы баг был виден сразу.
	_wall_timer = bug_param(&"through_walls", &"first_s", 6.0)


func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _play(name: String) -> void:
	bug_play(_sfx[name])


func _on_end(goal: bool) -> void:
	_music.stop()
	_play("finish" if goal else "lose")
	if AutoTest.enabled and not embedded:
		var rivals: PackedStringArray = []
		var lead := track.count() * 2
		for c in cars:
			if not c.player:
				rivals.append("%.1f" % c.finish_time if c.finished else "-")
				lead = mini(lead, player.progress - c.progress)
		AutoTest.note("racing: %s, место %d, %.1f с, соперники %s с, отрыв %d точек, ударов о берег %d, сид %d, трасса %d точек (%.0f px)" % [
				"цель" if goal else "провал", player_place(), race_time, "/".join(rivals), lead, bumps, record.seed,
				track.count(), track.count() * track.step_px])
		AutoTest.note("racing perf (среднее/максимум): " + _perf_text())


func _result_title(goal: bool) -> String:
	return "добрался первым" if goal else "не добрался"


func _result_caption() -> String:
	var t := int(round(race_time))
	if player.finished:
		return "место %d из %d · %d с" % [player.place, CARS, t]
	if bots_finished >= CARS - 1:
		return "все соперники финишировали раньше · %d с" % t
	return "круг не пройден за %d с" % t


# --- Шаг ----------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	var t0 := Time.get_ticks_usec()
	if _perf_last > 0:
		_perf_add("frame", t0 - _perf_last)
	_perf_last = t0
	bug_audio_tick(delta)
	# Фризы в движении с догоном времени (`Demo.bug_frame`).
	if bug_frame(delta, absf(player.speed) > 5.0, _step):
		world.queue_redraw()
		hud.queue_redraw()
	_perf_add("step", Time.get_ticks_usec() - t0)


## Замер под автотестом: сумма, максимум и число замеров по ключу, итог в заметке в конце.
func _perf_add(key: String, usec: int) -> void:
	if not AutoTest.enabled or embedded:
		return
	var v: Vector3i = _perf.get(key, Vector3i.ZERO)
	_perf[key] = Vector3i(v.x + usec, maxi(v.y, usec), v.z + 1)


func _perf_text() -> String:
	var parts: PackedStringArray = []
	for key: String in _perf:
		var v: Vector3i = _perf[key]
		parts.append("%s %.0f/%d мкс" % [key, float(v.x) / maxi(v.z, 1), v.y])
	return ", ".join(parts)


func _step(delta: float) -> void:
	bug_input_tick()
	if count_left > 0.0:
		count_left -= delta
		var shown := _count_digit()
		if shown != _last_count:
			_last_count = shown
			_play("go" if shown == 0 else "count")
		_update_camera(delta)
		return
	race_time += delta
	_through_walls(delta)
	var ctl := _player_controls(delta)
	_drive(player, ctl.x, ctl.y, ctl.z, delta)
	for c in cars:
		if not c.player:
			var a := _ai(c, c.lane, 1.0, delta)
			_drive(c, a.x, a.y, a.z, delta)
	_separate()
	for c in cars:
		_track_progress(c)
		if not running:
			return
	_update_wake(delta)
	_update_camera(delta)
	if race_time >= tuning.max_seconds:
		end_demo(false)


## Цифра отсчёта 3-2-1, 0 после старта.
func _count_digit() -> int:
	return int(ceil(maxf(count_left, 0.0) / (tuning.countdown / 3.0)))


## Руль, газ и тормоз игрока: с клавиатуры или от бота, через баг ввода (`Demo.bug_axis`). Бот
## автотеста и стрима едет тем же `_ai`: WIN полным газом с обгонами, LOSE на `lose_throttle`,
## и соперники финишируют раньше.
func _player_controls(delta: float) -> Vector3:
	var raw := Vector2.ZERO
	if bot_driven():
		var k := 1.0 if active_bot_mode() == AutoTest.BotMode.WIN else tuning.lose_throttle
		var a := _ai(player, _player_lane(delta), k, delta)
		raw = Vector2(a.x, a.y - a.z)
	else:
		var gas := 1.0 if Input.is_action_pressed(GameInput.A) else 0.0
		var brake := 1.0 if Input.is_action_pressed(GameInput.B) else 0.0
		raw = Vector2(GameInput.axis().x, gas - brake)
	var v := bug_axis(raw)
	var gas_now := maxf(v.y, 0.0)
	var brake_now := maxf(-v.y, 0.0)
	if has_bug(&"sticky_input"):
		gas_now = _sticky_gas(gas_now, delta)
	return Vector3(v.x, gas_now, brake_now)


## Залипание газа: отпустил газ, и он сам включается рывками (`Demo.bug_stick`).
func _sticky_gas(gas: float, delta: float) -> float:
	if gas > 0.0:
		if _burst > 0.0 or _stick_gap > 0.0:
			bug_clear_stick()
			_burst = 0.0
			_stick_gap = 0.0
		_gas_held = true
		return gas
	if _gas_held:
		_gas_held = false
		bug_stick()
		_stick_gap = tuning.stick_gap
	if _burst > 0.0:
		_burst -= delta
		if _burst <= 0.0:
			_stick_gap = tuning.stick_gap
		return 1.0
	if _stick_gap > 0.0:
		_stick_gap -= delta
		if _stick_gap <= 0.0 and bug_take_stick():
			_burst = tuning.stick_burst
	return 0.0


func _top_speed(c: Car) -> float:
	return tuning.max_speed * c.top * (1.0 if c.player else _rival_mult)


## Физика шлюпки: газ до доли предельной скорости, тормоз и задний ход, выбег; на отмели
## предел ниже. Поворот растёт со скоростью; скорость догоняет курс по сцеплению.
func _drive(c: Car, steer: float, gas: float, brake: float, delta: float) -> void:
	if c.ghost > 0.0:
		# «Сквозь стены»: летит по инерции без столкновений, руль и газ не слушаются.
		c.pos = (c.pos + c.vel * delta).clamp(Vector2(8, 8), track.size_px() - Vector2(8, 8))
		return
	var limit := _top_speed(c) * (tuning.side_speed_mult if track.tile_at(c.pos) != RacingTrack.Tile.ROAD else 1.0)
	if c.spin > 0.0:
		c.spin -= delta
		c.heading = wrapf(c.heading + tuning.spin_rate * delta, -PI, PI)
		c.speed = move_toward(c.speed, 0.0, tuning.brake * delta)
	else:
		if brake > 0.0:
			if c.speed > 0.0:
				c.speed -= tuning.brake * brake * delta
			else:
				c.speed = maxf(c.speed - tuning.accel * 0.5 * delta, -tuning.reverse_speed)
		elif gas > 0.0:
			var want := limit * gas
			if c.speed < want:
				c.speed = minf(c.speed + tuning.accel * delta, want)
			else:
				c.speed = move_toward(c.speed, want, tuning.coast_drag * delta)
		else:
			c.speed = move_toward(c.speed, 0.0, tuning.coast_drag * delta)
		if c.speed > limit:
			c.speed = move_toward(c.speed, limit, tuning.side_drag * delta)
		var k := clampf(absf(c.speed) / tuning.turn_full_speed, 0.0, 1.0)
		var dir := -1.0 if c.speed < 0.0 else 1.0
		c.heading = wrapf(c.heading + steer * tuning.turn_rate * k * dir * delta, -PI, PI)
	var target := Vector2.from_angle(c.heading) * c.speed
	c.vel = c.vel.lerp(target, 1.0 - exp(-tuning.grip * _grip_mult * delta))
	c.bump_cd = maxf(c.bump_cd - delta, 0.0)
	_move(c, c.vel * delta)


## Сдвиг по осям отдельно: упёрлась ось, скорость по ней отскакивает, шлюпка скользит вдоль.
func _move(c: Car, d: Vector2) -> void:
	var hit := false
	var nx := c.pos + Vector2(d.x, 0.0)
	if _blocked(nx):
		c.vel.x = -c.vel.x * tuning.wall_bounce
		hit = true
	else:
		c.pos = nx
	var ny := c.pos + Vector2(0.0, d.y)
	if _blocked(ny):
		c.vel.y = -c.vel.y * tuning.wall_bounce
		hit = true
	else:
		c.pos = ny
	if hit and c.bump_cd <= 0.0:
		c.speed *= tuning.wall_speed_keep
		c.bump_cd = 0.3
		if c.player:
			bumps += 1
			_play("bump")


func _blocked(p: Vector2) -> bool:
	var r := tuning.car_radius
	for o in [Vector2(-r, -r), Vector2(r, -r), Vector2(-r, r), Vector2(r, r)]:
		if track.tile_at(p + o) == RacingTrack.Tile.WALL:
			return true
	for ob in track.obstacles:
		if p.distance_squared_to(ob.pos) < (r + ob.radius) * (r + ob.radius):
			return true
	return false


## Машины не проходят друг сквозь друга: перекрытие делится пополам. Баг «чих»: соперник,
## которого коснулся игрок, крутится и сходит с трассы на отмель (`_ai`), потом возвращается.
func _separate() -> void:
	var min_d := tuning.car_radius * 2.0 + 1.0
	for i in cars.size():
		for j in range(i + 1, cars.size()):
			var a := cars[i]
			var b := cars[j]
			var d := b.pos - a.pos
			var dist := d.length()
			if dist >= min_d:
				continue
			var push := (d / dist if dist > 0.01 else Vector2.RIGHT) * (min_d - dist) / 2.0
			if not _blocked(a.pos - push):
				a.pos -= push
			if not _blocked(b.pos + push):
				b.pos += push
			if has_bug(&"sneeze_enemies") and (a.player or b.player):
				var other := b if a.player else a
				if other.offroad <= 0.0:
					# Чих: соперник крутится и сходит с трассы на отмель от борта игрока.
					other.spin = bug_param(&"sneeze_enemies", &"spin_s", 0.4)
					other.offroad = bug_param(&"sneeze_enemies", &"off_track_s", 2.5)
					var side := signf(track.lateral(other.pos, other.idx) - track.lateral(player.pos, other.idx))
					other.offroad_side = side if side != 0.0 else 1.0
					_play("spin")
					if AutoTest.enabled and not embedded:
						AutoTest.note("racing: чих, соперник у точки %d сходит с трассы на %.1f с" % [other.idx, race_time])


## Пройденные точки, финиш и застревание.
func _track_progress(c: Car) -> void:
	var j := track.nearest(c.pos, c.idx)
	c.progress += track.wrap_delta(j - c.idx)
	c.idx = j
	# Продвинулся: счёт застревания (`_ai`) сначала.
	if c.progress > c.best:
		c.best = c.progress
		c.stall = 0.0
	if c.finished or c.progress < track.count():
		return
	c.finished = true
	c.finish_time = race_time
	finish_order += 1
	c.place = finish_order
	if c.player:
		end_demo(c.place == 1)
	else:
		bots_finished += 1
		if bots_finished >= CARS - 1 and not player.finished:
			end_demo(false)


## Бот ведёт шлюпку по средней линии со сдвигом `lane`: цель на несколько точек вперёд,
## перед поворотом сброс скорости, препятствие впереди объезжается с другого борта. `k` доля
## предельной скорости. Застрял: задний ход с обратным рулём, потом на среднюю линию.
func _ai(c: Car, lane: float, k: float, delta: float) -> Vector3:
	var n := track.count()
	c.stall += delta
	if c.stall > tuning.respawn_seconds:
		_respawn(c)
	elif c.stall > tuning.stuck_seconds and c.reverse_left <= 0.0 and c.spin <= 0.0:
		c.reverse_left = tuning.reverse_seconds
		c.stall = tuning.stuck_seconds * 0.5 + (c.stall - tuning.stuck_seconds)
	var look := tuning.bot_lookahead + int(absf(c.speed) / tuning.bot_look_speed)
	var ti := (c.idx + look) % n
	# Гоночная линия: перед поворотом сдвиг к его внутренней стороне (нормаль смотрит вправо
	# по ходу, поворот направо положительный).
	var bend := track.tangents[ti].angle_to(track.tangents[(ti + tuning.bot_brake_window) % n])
	var off := clampf(lane + bend * tuning.bot_line_gain, -tuning.bot_line_max, tuning.bot_line_max)
	var side := track.avoid_side[ti]
	if side != 0 and (absf(off) < 1.0 or signf(off) == float(side)):
		off = -side * tuning.avoid_offset
	if c.offroad > 0.0:
		# Чих: курс на отмель у берега, пока не пройдёт; дальше обычный ряд и назад на трассу.
		c.offroad -= delta
		c.stall = 0.0
		off = c.offroad_side * (track.road_half_px + track.side_px * 0.6)
		k = minf(k, bug_param(&"sneeze_enemies", &"off_track_throttle", 0.5))
	var target := track.points[ti] + track.normals[ti] * off
	var diff := wrapf((target - c.pos).angle() - c.heading, -PI, PI)
	var steer := clampf(diff * 2.5, -1.0, 1.0)
	if c.reverse_left > 0.0:
		c.reverse_left -= delta
		return Vector3(-steer, 0.0, 1.0)
	# Скорость в повороте: предел, на котором руль ещё держит дугу впереди (радиус по смене
	# курса на окне), с запасом `bot_corner_grip`; тормозит только в крутых поворотах.
	var turn := 0.0
	for w: int in [maxi(tuning.bot_brake_window / 2, 1), tuning.bot_brake_window]:
		turn = maxf(turn, absf(track.tangents[c.idx].angle_to(track.tangents[(c.idx + w) % n])) / w)
	var top := _top_speed(c)
	var want := k
	if turn > 0.0001:
		want = minf(want, tuning.turn_rate * track.step_px / turn * tuning.bot_corner_grip / top)
	if absf(diff) > 1.0:
		want = minf(want, 0.35)
	if c.speed > top * want + 20.0:
		return Vector3(steer, 0.0, 1.0)
	return Vector3(steer, want, 0.0)


## Баг «сквозь стены» (#49): раз в `period_s` (первый раз через `first_s` после старта)
## шлюпка игрока, а через раз с шансом `rival_chance` соперник, теряет столкновения: её
## выносит вбок со скоростью `kick_speed` (плюс треть своей вдоль трассы) сквозь берег на
## песок на `ghost_s` секунд, потом ставит на среднюю линию у её точки и она мигает
## `blink_s`. Гонку можно закончить.
func _through_walls(delta: float) -> void:
	if not has_bug(&"through_walls"):
		return
	for c in cars:
		c.blink = maxf(c.blink - delta, 0.0)
		if c.ghost > 0.0:
			c.ghost -= delta
			if c.ghost <= 0.0:
				_put_back(c)
	_wall_timer -= delta
	if _wall_timer > 0.0:
		return
	_wall_timer = bug_param(&"through_walls", &"period_s", 12.0) * bug_rng.randf_range(0.8, 1.2)
	var c := player
	if _wall_count % 2 == 1 and bug_rng.randf() < bug_param(&"through_walls", &"rival_chance", 0.5):
		var rivals: Array[Car] = []
		for r in cars:
			if not r.player and r.ghost <= 0.0:
				rivals.append(r)
		if not rivals.is_empty():
			c = rivals[bug_rng.randi_range(0, rivals.size() - 1)]
	_wall_count += 1
	if c.ghost > 0.0:
		return
	var side := signf(track.lateral(c.pos, c.idx))
	if side == 0.0:
		side = 1.0
	c.ghost = bug_param(&"through_walls", &"ghost_s", 1.2)
	c.spin = 0.0
	c.offroad = 0.0
	# Выносит в основном вбок, к ближнему берегу: носом туда же, чтобы вылет читался.
	c.vel = track.tangents[c.idx] * maxf(c.speed, 0.0) * 0.35 \
			+ track.normals[c.idx] * side * bug_param(&"through_walls", &"kick_speed", 220.0)
	c.heading = c.vel.angle()
	_play("warp")
	if AutoTest.enabled and not embedded:
		AutoTest.note("racing: %s вылетает сквозь берег на %.1f с у точки %d" % ["игрок" if c.player else "соперник", race_time, c.idx])


## После вылета: на среднюю линию у своей точки носом по ходу, с половиной скорости, мигает.
func _put_back(c: Car) -> void:
	c.pos = track.points[c.idx].round()
	c.heading = track.tangents[c.idx].angle()
	c.speed *= 0.5
	c.vel = Vector2.from_angle(c.heading) * c.speed
	c.stall = 0.0
	c.blink = bug_param(&"through_walls", &"blink_s", 0.5)


## Бот на средней линии у своей точки, носом по ходу.
func _respawn(c: Car) -> void:
	c.pos = track.points[c.idx].round()
	c.heading = track.tangents[c.idx].angle()
	c.speed = 0.0
	c.vel = Vector2.ZERO
	c.stall = 0.0
	c.reverse_left = 0.0
	c.spin = 0.0
	if AutoTest.enabled and not embedded:
		AutoTest.note("racing: %s застрял у точки %d и встал на среднюю линию" % ["игрок" if c.player else "соперник", c.idx])


## Ряд бота за игрока: по гоночной линии посередине; соперник впереди в этом ряду
## обходится сбоку на `pass_offset` со стороны ближе к середине, ряд держится `pass_hold`
## секунд и плавно возвращается к середине.
func _player_lane(delta: float) -> float:
	_lane_hold -= delta
	for c in cars:
		if c.player:
			continue
		var ahead := c.progress - player.progress
		if ahead <= 0 or ahead >= 6:
			continue
		var their := track.lateral(c.pos, c.idx)
		if absf(their - _bot_lane) < tuning.pass_offset - 2.0:
			var side := -signf(their) if absf(their) > 2.0 else (1.0 if _bot_lane >= 0.0 else -1.0)
			_bot_lane = clampf(their + side * tuning.pass_offset, -tuning.bot_line_max, tuning.bot_line_max)
			_lane_hold = tuning.pass_hold
	if _lane_hold <= 0.0:
		_bot_lane = move_toward(_bot_lane, 0.0, tuning.pass_return * delta)
	return _bot_lane


func _update_wake(delta: float) -> void:
	for i in range(_wake.size() - 1, -1, -1):
		_wake[i].z -= delta
		if _wake[i].z <= 0.0:
			_wake.remove_at(i)
	for c in cars:
		if absf(c.speed) < tuning.wake_speed:
			continue
		c.wake_timer -= delta
		if c.wake_timer <= 0.0:
			c.wake_timer = tuning.wake_every
			var stern := c.pos - Vector2.from_angle(c.heading) * 7.0
			_wake.append(Vector3(stern.x, stern.y, WAKE_LIFE))


## Камера целочисленная: шлюпка игрока по центру с упреждением по скорости.
## Камера: шлюпка игрока плюс упреждение по курсу и скорости, сглаженное критически
## демпфированной пружиной (без рывков от ударов и расталкивания). Округляется один раз за
## кадр до пикселя экрана; берётся от уже округлённой до пикселя экрана шлюпки, так своя
## шлюпка стоит на экране ровно, а фон и соперники едут с ней в одной сетке. Зовётся в конце
## шага, после физики, всегда в одном порядке.
func _update_camera(delta: float) -> void:
	var want := Vector2.from_angle(player.heading) * maxf(player.speed, 0.0) * tuning.camera_lead
	if delta > 0.0:
		var omega := 2.0 / maxf(tuning.camera_smooth, 0.01)
		var x := omega * delta
		var e := 1.0 / (1.0 + x + 0.48 * x * x + 0.235 * x * x * x)
		var change := _lead - want
		var temp := (_lead_vel + omega * change) * delta
		_lead_vel = (_lead_vel - omega * temp) * e
		_lead = want + (change + temp) * e
	var size := track.size_px()
	var c := _snap(player.pos) + _snap(_lead) - (view / 2.0).floor()
	c.x = clampf(c.x, 0.0, maxf(size.x - view.x, 0.0))
	c.y = clampf(c.y, 0.0, maxf(size.y - view.y, 0.0))
	cam = _snap(c)
	world.position = -(cam * scale_px).round()


## Точка в пикселях демки, округлённая до пикселя экрана.
func _snap(p: Vector2) -> Vector2:
	return (p * scale_px).round() / scale_px


## Место игрока: впереди те, кто финишировал раньше или прошёл больше точек.
func player_place() -> int:
	if player.finished:
		return player.place
	var place := 1
	for c in cars:
		if not c.player and (c.finished or c.progress > player.progress):
			place += 1
	return place


# --- Рисование виртуального экрана ---------------------------------------------------------

func _dir_index(heading: float) -> int:
	return posmod(int(round(heading / (PI / 4.0))), 8)


## Спрайт 16×16 центром в `p`; на строке тайлов сверх лимита мерцает (`Demo.flicker_hidden`).
func _sprite(slot: String, name: String, p: Vector2) -> void:
	if flicker_hidden(int(floor(p.y / TILE))):
		return
	var at := _snap(p) - Vector2(8, 8)
	if is_pink(slot):
		world.draw_rect(Rect2(at + Vector2(2, 2), Vector2(12, 12)), PINK)
	else:
		world.draw_texture(tex[name], at)


func _draw_world() -> void:
	var t0 := Time.get_ticks_usec()
	_draw_world_layer()
	_perf_add("world", Time.get_ticks_usec() - t0)


func _draw_world_layer() -> void:
	flicker_reset()
	world.draw_texture(_map_tex, Vector2.ZERO)
	var rect := Rect2(cam - Vector2(16, 16), view + Vector2(32, 32))
	for b in track.buoys:
		if rect.has_point(b):
			_sprite("buoy", "race_buoy", b)
	for o in track.obstacles:
		if rect.has_point(o.pos):
			var rock := o.kind == RacingTrack.Kind.ROCK
			_sprite("rock" if rock else "barrel", "race_rock" if rock else "race_barrel", o.pos)
	for w in _wake:
		var k := w.z / WAKE_LIFE
		world.draw_rect(Rect2(roundf(w.x) - 1.0, roundf(w.y) - 1.0, 1.0 + roundf(2.0 * (1.0 - k)), 1.0 + roundf(2.0 * (1.0 - k))),
				Color(HUD_INK, 0.7 * k))
	for c in cars:
		if not c.player and rect.has_point(c.pos):
			if not _blinked(c):
				_sprite("rival", "rival_%d" % _dir_index(c.heading), c.pos)
	if not _blinked(player):
		_sprite("hero", "boat_%d" % _dir_index(player.heading), player.pos)


## Мигание после возврата на трассу («сквозь стены»): через пару кадров.
func _blinked(c: Car) -> bool:
	return c.blink > 0.0 and Engine.get_process_frames() % 6 < 3


## Запечь статичную карту в текстуру: тайлы по типу (вода из двух тайлов с бликом и их
## отражений по хешу клетки, берег с редкой ракушкой) и финиш. Раньше слой мира каждый кадр
## рисовал сотни тайлов; теперь одна текстура, сверху только буи, препятствия и шлюпки.
func _bake_map() -> void:
	var size := Vector2i(track.size_px())
	var img := Image.create_empty(size.x, size.y, false, Image.FORMAT_RGBA8)
	var water: Array[Image] = []
	for flip: bool in [false, true]:
		for name: String in ["race_water_1", "race_water"]:
			var im := _tile_image(name)
			if flip:
				im.flip_x()
			water.append(im)
	var shallow := _tile_image("race_shallow")
	var sand := _tile_image("race_sand")
	var shell := _tile_image("race_sand_1")
	var full := Rect2i(0, 0, TILE, TILE)
	for row in track.height:
		for col in track.width:
			var h := hash(col * 4096 + row)
			var src := sand
			match track.tile(col, row):
				RacingTrack.Tile.ROAD:
					src = water[h % 4]
				RacingTrack.Tile.SIDE:
					src = shallow
				_:
					src = shell if h % 23 == 0 else sand
			img.blit_rect(src, full, Vector2i(col, row) * TILE)
	_bake_finish(img)
	_map_tex = ImageTexture.create_from_image(img)


func _tile_image(name: String) -> Image:
	var im := (tex[name] as Texture2D).get_image()
	if im.is_compressed():
		im.decompress()
	im.convert(Image.FORMAT_RGBA8)
	return im


## Финиш: шахматная полоса поперёк воды у точки 0 (старт на горизонтальном участке, полоса
## вертикальная). Баг «не достать»: полоса лежит вдоль берега острова у старта,
## засчитывается всё равно на воде. Розовая заглушка запекается сразу.
func _bake_finish(img: Image) -> void:
	var strip := _tile_image("race_finish")
	var full := Rect2i(0, 0, TILE, TILE)
	var pink := is_pink("finish")
	var p0 := track.points[0]
	var col := int(floor(p0.x / TILE))
	var reach := track.road_half_px + track.side_px
	if _finish_on_shore:
		# Берег острова со стороны центра карты: с решётки он в кадре, внешний берег нет.
		var step := -1 if track.size_px().y / 2.0 < p0.y else 1
		var row := int(floor(p0.y / TILE))
		while row > 0 and row < track.height - 1 and track.tile(col, row) != RacingTrack.Tile.WALL:
			row += step
		strip.rotate_90(CLOCKWISE)
		var half := int(ceil(reach / TILE))
		for c in range(maxi(col - half, 0), mini(col + half + 1, track.width)):
			var at := Vector2i(c, row) * TILE
			if pink:
				img.fill_rect(Rect2i(at + Vector2i(0, 4), Vector2i(16, 8)), PINK)
			else:
				img.blend_rect(strip, full, at)
		return
	for row in range(int(floor((p0.y - reach) / TILE)), int(floor((p0.y + reach) / TILE)) + 1):
		if track.tile(col, row) == RacingTrack.Tile.WALL:
			continue
		var at := Vector2i(col, row) * TILE
		if pink:
			img.fill_rect(Rect2i(at + Vector2i(4, 0), Vector2i(8, 16)), PINK)
		else:
			img.blend_rect(strip, full, at)


## Мини-карта: точки средней линии и отметка финиша на тёмной подложке, запечены один раз.
func _bake_minimap() -> void:
	var size := track.size_px()
	var k := minf(MINIMAP_BOX.x / size.x, MINIMAP_BOX.y / size.y)
	var px := Vector2i((size * k).ceil()) + Vector2i(4, 4)
	var img := Image.create_empty(px.x, px.y, false, Image.FORMAT_RGBA8)
	img.fill(HUD_DIM)
	var dot := HUD_DIM.blend(Color(HUD_INK, 0.45))
	for i in range(0, track.count(), 2):
		img.set_pixelv(Vector2i((track.points[i] * k).floor()) + Vector2i(2, 2), dot)
	var f := Vector2i((track.points[0] * k).floor()) + Vector2i(2, 2)
	img.fill_rect(Rect2i(f - Vector2i(0, 2), Vector2i(1, 5)), HUD_INK)
	_minimap_tex = ImageTexture.create_from_image(img)


## HUD в координатах экрана: место слева, полоса круга по центру, мини-карта справа, отсчёт.
func _draw_hud() -> void:
	var t0 := Time.get_ticks_usec()
	_draw_hud_layer()
	_perf_add("hud", Time.get_ticks_usec() - t0)


func _draw_hud_layer() -> void:
	draw_pixel_text(hud, Vector2(5.0, 4.0), "%d/%d" % [player_place(), CARS], HUD_INK, HUD_SHADOW)
	var n := float(track.count())
	var bar := Rect2(roundf(view.x / 2.0 - 60.0), 6.0, 120.0, 3.0)
	hud.draw_rect(bar.grow(1.0), HUD_DIM)
	hud.draw_rect(Rect2(bar.position, Vector2(roundf(bar.size.x * clampf(player.progress / n, 0.0, 1.0)), bar.size.y)), HUD_INK)
	for c in cars:
		if not c.player:
			var x := bar.position.x + roundf(bar.size.x * clampf(c.progress / n, 0.0, 1.0))
			hud.draw_rect(Rect2(x, bar.position.y - 2.0, 1.0, bar.size.y + 4.0), RIVAL_INK)
	_draw_minimap()
	if count_left > 0.0 and _count_digit() > 0:
		var cell := 6.0
		draw_pixel_text(hud, (view / 2.0 - Vector2(1.5 * cell, 2.5 * cell + 24.0)).round(), str(_count_digit()), HUD_INK, HUD_SHADOW, cell)


func _draw_minimap() -> void:
	var size := track.size_px()
	var k := minf(MINIMAP_BOX.x / size.x, MINIMAP_BOX.y / size.y)
	var origin := Vector2(view.x - MINIMAP_BOX.x - 4.0, 4.0)
	hud.draw_texture(_minimap_tex, origin - Vector2(2, 2))
	for c in cars:
		if not c.player:
			hud.draw_rect(Rect2((origin + c.pos * k).floor() - Vector2.ONE, Vector2(2, 2)), RIVAL_INK)
	var p := (origin + player.pos * k).floor()
	hud.draw_rect(Rect2(p - Vector2(1, 1), Vector2(3, 3)), HUD_SHADOW)
	hud.draw_rect(Rect2(p - Vector2(1, 1), Vector2(2, 2)), HUD_INK)
