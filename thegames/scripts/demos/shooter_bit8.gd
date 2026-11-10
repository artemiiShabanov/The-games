extends Demo
## Демка шутер × 8-bit, каталог `docs/specs/demos_catalog.md`: вид сверху, арена в один экран
## (палуба в борту), враги двух типов: скелет-ходок идёт к герою по палубе в обход пропов,
## канонир держит дистанцию, ходит вбок и стреляет медленной пулей. Цель: уничтожить 30, итог
## «отбился»; жизни кончились или вышла страховка `max_seconds`: «не отбился». Стрелки ход, A
## выстрел ядром по взгляду (зажатая A стреляет очередью), B держать: герой стоит, стрелки
## только поворачивают взгляд, 8 направлений. Ром (аптечка) раз в 20 секунд на свободной
## палубе. Перед стартом отсчёт 3-2-1.
## Арена и волны из `ShooterArenaGen` по сиду записи: трап на каждом борту, по ним враги
## поднимаются на палубу; пропы (бочки, сундуки, пушки) держат и героя, и врагов, и выстрелы.
## Виртуальный экран ×4 в карточке (×2 во встроенном режиме) без SubViewport, как у гонок:
## слои `world` и `hud` увеличены целым масштабом, статичная арена запечена в текстуру на
## старте; арена по центру экрана, во встроенном режиме чуть обрезана по краям борта.
## Спрайты из сеттинга записи (`SettingDef`): ходок берёт слот противника платформера
## (`enemy_0..1`), остальные слоты шутера пока только у пиратов.
##
## Баги по флагам записи (параметры в `resources/bugs/<id>.tres`). Общие (#44) механикой живут
## в `Demo`: `frame_drops` фризы в бою; `audio_stutter` заикание музыки и звуки с задержкой;
## `sticky_input` ход и кнопки с опозданием, отпущенная A ещё стреляет; `pink_placeholders`
## враги, снаряды, ром или пропы розовыми квадратами; `alien_palette` весь слой мира в
## сдвинутых цветах; `sprite_flicker` спрайты сверх лимита на строке тайлов через кадр. Свои
## проявления (#51): `through_enemies` (жанровый баг шутера) каждое второе касание ядра с врагом
## не засчитывается, ядро пролетает сквозь и летит дальше; `sneeze_enemies` враги гибнут с
## одного ядра и от ветра ядра, пролетевшего рядом (ядро летит дальше); `unreachable_coins`
## каждое убийство зовёт на трап лишнего врага и двигает цель на единицу: «1/31», «2/32», цель
## не достать, демку кончают жизни или страховка; `wild_physics` палуба как каток: герой
## разгоняется и тормозит с заносом, враги быстрее.

class Foe:
	var kind := ShooterArena.Enemy.WALKER
	var pos := Vector2.ZERO
	var hp := 1
	## Сошёл с трапа на палубу: до этого идёт прямо внутрь, не стреляет и не попадает под ядра.
	var aboard := false
	var door := 0
	var fire_cd := 0.0
	var strafe := 1.0
	var strafe_cd := 0.0
	var anim := 0.0
	var flash := 0.0
	var face_left := false
	## Скорость за последний шаг, для упреждения бота.
	var vel := Vector2.ZERO

class Shot:
	var pos := Vector2.ZERO
	var vel := Vector2.ZERO
	var hostile := false
	## Баг «сквозь врагов»: враг, сквозь которого ядро сейчас пролетает, его не бьёт.
	var ghost: Foe = null


const SCALE := 4
## Увеличение во встроенном режиме (запись стрима в ленте).
const EMBED_SCALE := 2
const TILE := ShooterArena.TILE
const PUFF_LIFE := 0.35
const HUD_INK := Color("#F4EFE6")
const HUD_SHADOW := Color("#161412")
const HUD_DIM := Color(0.086, 0.078, 0.071, 0.55)
const SEA := Color("#2F6FB5")
## Направления взгляда по часовой от «вправо» (экран, y вниз); кадр героя `_hero_frame`.
const DIRS: Array[Vector2] = [Vector2(1, 0), Vector2(0.70710678, 0.70710678), Vector2(0, 1),
	Vector2(-0.70710678, 0.70710678), Vector2(-1, 0), Vector2(-0.70710678, -0.70710678),
	Vector2(0, -1), Vector2(0.70710678, -0.70710678)]
const HEART: Array[String] = ["01010", "11111", "11111", "01110", "00100"]
## Что может стать розовой заглушкой; герой, палуба и борт никогда.
const PLACEHOLDER_SLOTS: Array[String] = ["walker", "gunner", "ball", "shot", "rum", "barrel", "chest", "cannon"]
const SPRITES: Array[String] = ["enemy_0", "enemy_1", "shoot_gunner_0", "shoot_gunner_1", "shoot_ball",
	"shoot_shot", "shoot_rum", "shoot_deck", "shoot_deck_1", "shoot_rail", "shoot_rail_corner", "shoot_plank",
	"shoot_barrel", "shoot_chest", "shoot_cannon", "shoot_puff"]
const PROP_SPRITES: Array[String] = ["shoot_barrel", "shoot_chest", "shoot_cannon"]
const PROP_SLOTS: Array[String] = ["barrel", "chest", "cannon"]
const MELODY := [0, null, 3, null, 7, null, 3, 5, 7, null, 10, null, 7, 5, 3, null,
	0, null, 3, null, 7, null, 12, 10, 7, null, 5, null, 3, 2, 0, null]
const BASS := [-12, -12, -9, -9, -5, -5, -7, -7, -12, -12, -9, -9, -14, -14, -7, -7]

var tuning: ShooterDemoTuning
var arena: ShooterArena
## Виртуальный экран в пикселях демки: внутренность карточки, делённая на `SCALE`.
var view := Vector2(416, 208)
## Увеличение: `SCALE` в карточке, `EMBED_SCALE` в ленте.
var scale_px := SCALE
var tex := {}
var world: Node2D
var hud: Node2D
## Сеттинг записи: спрайты.
var scene_set: SettingDef
var hero := Vector2.ZERO
## Взгляд героя: индекс в `DIRS`.
var facing := 6
## Кадр героя `shoot_hero_0..3` (вправо, вниз, влево, вверх): по диагонали остаётся прежний
## прямой, если он соседний, иначе боковой.
var _hero_frame := 3
var hp := 5
var invuln := 0.0
var foes: Array[Foe] = []
var shots: Array[Shot] = []
var kills := 0
## Цель по убийствам: `kills_goal`, с багом «не достать» растёт с каждым убийством.
var goal := 30
var count_left := 0.0
var fight_time := 0.0
var hero_moving := false
## Статистика для итога и автотеста.
var kills_walkers := 0
var kills_gunners := 0
var shots_fired := 0
var hits := 0
var damage := 0
var rums := 0
## Случайность боя (ром, канониры) из сида записи.
var rng := RandomNumberGenerator.new()
## Начало арены на экране демки (по центру; во встроенном режиме может быть отрицательным).
var _origin := Vector2.ZERO
var _map_tex: ImageTexture
## Расстояния по палубе до клетки героя для ходьбы врагов (`ShooterArena.distances`).
var _flow: PackedInt32Array = []
var _flow_cell := Vector2i(-1, -1)
var _wave := 0
var _wave_spawned := 0
var _wave_time := 0.0
var _wave_pause := 0.0
var _spawn_cd := 0.0
var _rum_on := false
var _rum := Vector2.ZERO
var _rum_timer := 0.0
var _fire_cd := 0.0
## Кнопки игрока (через `Demo.bug_press`): A зажата, B зажата; прошлое состояние A для залипания.
var _fire_a := false
var _hold_b := false
var _fire_was := false
## Puff: позиция и остаток жизни.
var _puffs: Array[Vector3] = []
var _last_count := -1
## Решение бота на кадр: ход, A, B.
var _bot_move := Vector2.ZERO
var _bot_fire := false
var _bot_hold := false
## Баги жанра и баланса (#51), числа из ресурсов багов читаются один раз в `_setup_bugs`.
## «Сквозь врагов»: каждое `_pass_every`-е касание ядра с врагом сквозь (0 без бага), счёт касаний.
var _pass_every := 0
var _contacts := 0
var passes := 0
## «Чих»: ядро валит врагов ближе `_sneeze_px` к себе (0 без бага); убитых так.
var _sneeze_px := 0.0
var sneeze_kills := 0
## «Не достать»: лишних врагов и прибавки цели на убийство, накопитель и очередь на трап.
var _extra_per_kill := 0.0
var _extra_acc := 0.0
var _extra_left := 0
var _extra_cd := 0.0
var extras := 0
## «Дикая физика»: отклик скорости героя на палубе-катке, 1/с (0 без бага), множитель врагов.
var _ice := 0.0
var _foe_mult := 1.0
var _hero_vel := Vector2.ZERO
## Замеры времени под автотестом: ключ → (сумма, максимум, число) в микросекундах.
var _perf: Dictionary[String, Vector3i] = {}
var _perf_last := 0

# Звук.
var _music: AudioStreamPlayer
var _sfx := {}


func _on_start() -> void:
	tuning = ShooterDemoTuning.load_default()
	scene_set = SettingDef.of(record.setting)
	arena = ShooterArenaGen.generate(record.seed)
	rng.seed = hash(str(record.seed, ":shooter"))
	for i in 4:
		tex["shoot_hero_%d" % i] = scene_set.sprite("shoot_hero_%d" % i)
	for name in SPRITES:
		tex[name] = scene_set.sprite(name)
	scale_px = EMBED_SCALE if embedded else SCALE
	var area := embed_size if embedded else CardFrame.inner_size()
	view = (area / scale_px).floor()
	# Как у гонок: мир и HUD увеличены целым `scale_px` с ближайшим соседом, без SubViewport.
	var stage := Control.new()
	stage.position = ((area - view * scale_px) / 2.0).floor()
	stage.size = view * scale_px
	stage.clip_contents = true
	stage.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	stage.mouse_filter = Control.MOUSE_FILTER_IGNORE
	screen.add_child(stage)
	var under := ColorRect.new()
	under.color = SEA
	under.size = stage.size
	under.mouse_filter = Control.MOUSE_FILTER_IGNORE
	stage.add_child(under)
	_origin = ((view - arena.size_px()) / 2.0).floor()
	world = Node2D.new()
	world.scale = Vector2.ONE * scale_px
	world.position = _origin * scale_px
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
	_perf_add("bake", Time.get_ticks_usec() - t0)
	hero = arena.center_of(arena.start_cell())
	hp = tuning.hero_hp
	goal = tuning.kills_goal
	count_left = tuning.countdown
	_rum_timer = tuning.rum_every
	_setup_bugs()
	_setup_audio()


## Баги жанра и баланса шутера: числа из ресурсов багов один раз; общие ставит `Demo`.
func _setup_bugs() -> void:
	if has_bug(&"through_enemies"):
		_pass_every = maxi(int(bug_param(&"through_enemies", &"pass_every", 2.0)), 1)
	if has_bug(&"sneeze_enemies"):
		_sneeze_px = bug_param(&"sneeze_enemies", &"near_miss_px", 18.0)
	if has_bug(&"unreachable_coins"):
		_extra_per_kill = bug_param(&"unreachable_coins", &"extra_per_kill", 1.0)
	if has_bug(&"wild_physics"):
		_ice = bug_param(&"wild_physics", &"ice_response", 2.5)
		_foe_mult = bug_param(&"wild_physics", &"foe_speed_mult", 1.5)


func _setup_audio() -> void:
	_music = Sfx.player(Sfx.chiptune_loop(MELODY, BASS, 150.0), tuning.music_db if not embedded else -80.0)
	add_child(_music)
	bug_music = _music
	if not embedded:
		_music.play()
	_sfx["count"] = Sfx.player(Sfx.blip(440.0, 0.12, 0.35, 18.0))
	_sfx["go"] = Sfx.player(Sfx.blip(880.0, 0.25, 0.4, 10.0))
	_sfx["shot"] = Sfx.player(Sfx.blip(620.0, 0.06, 0.3, 40.0))
	_sfx["enemy_shot"] = Sfx.player(Sfx.blip(300.0, 0.08, 0.25, 30.0))
	_sfx["hit"] = Sfx.player(Sfx.thud(0.08, 0.35))
	_sfx["kill"] = Sfx.player(Sfx.blip(196.0, 0.15, 0.35, 14.0))
	_sfx["hurt"] = Sfx.player(Sfx.thud(0.18, 0.5))
	_sfx["rum"] = Sfx.player(Sfx.blip(988.0, 0.2, 0.35, 10.0))
	_sfx["finish"] = Sfx.player(Sfx.blip(880.0, 0.5, 0.45, 5.0))
	_sfx["lose"] = Sfx.player(Sfx.blip(196.0, 0.4, 0.45, 6.0))
	for p in _sfx.values():
		(p as AudioStreamPlayer).volume_db = tuning.sfx_db if not embedded else -80.0
		add_child(p)


func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _play(name: String) -> void:
	bug_play(_sfx[name])


func _on_end(goal_: bool) -> void:
	_music.stop()
	_play("finish" if goal_ else "lose")
	if AutoTest.enabled and not embedded:
		AutoTest.note("shooter: %s, уничтожено %d/%d (скелетов %d, канониров %d), жизней %d/%d, урона %d, выстрелов %d, попаданий %d, рома %d, волна %d, %.1f с, сид %d, пропов %d, попыток генератора %d" % [
				"цель" if goal_ else "провал", kills, goal, kills_walkers, kills_gunners, hp, tuning.hero_hp,
				damage, shots_fired, hits, rums, _wave + 1, fight_time, record.seed, arena.props.size(), arena.attempts])
		if not record.bug_ids.is_empty():
			AutoTest.note("shooter bugs: сквозь %d из %d касаний, от чиха %d, лишних врагов %d" % [passes, _contacts, sneeze_kills, extras])
		AutoTest.note("shooter perf (среднее/максимум): " + _perf_text())


func _result_title(goal: bool) -> String:
	return "отбился" if goal else "не отбился"


func _result_caption() -> String:
	var t := int(round(fight_time))
	if kills >= goal:
		return "уничтожено %d · жизней %d из %d · %d с" % [kills, hp, tuning.hero_hp, t]
	if hp <= 0:
		return "уничтожено %d из %d · %d с" % [kills, goal, t]
	return "уничтожено %d из %d · время вышло" % [kills, goal]


# --- Ввод ------------------------------------------------------------------------------------

## A и B идут через `Demo.bug_press`: с багом управления и нажатие, и отпускание с опозданием.
func _game_input(event: InputEvent) -> void:
	if event.is_action_pressed(GameInput.A, false):
		bug_press(func() -> void: _fire_a = true)
		get_viewport().set_input_as_handled()
	elif event.is_action_released(GameInput.A):
		bug_press(func() -> void: _fire_a = false)
	elif event.is_action_pressed(GameInput.B, false):
		bug_press(func() -> void: _hold_b = true)
		get_viewport().set_input_as_handled()
	elif event.is_action_released(GameInput.B):
		bug_press(func() -> void: _hold_b = false)


# --- Шаг ----------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	var t0 := Time.get_ticks_usec()
	if _perf_last > 0:
		_perf_add("frame", t0 - _perf_last)
	_perf_last = t0
	bug_audio_tick(delta)
	# Фризы в бою с догоном времени (`Demo.bug_frame`).
	if bug_frame(delta, hero_moving or not foes.is_empty(), _step):
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
	if not running:
		return
	bug_input_tick()
	if count_left > 0.0:
		count_left -= delta
		var shown := _count_digit()
		if shown != _last_count:
			_last_count = shown
			_play("go" if shown == 0 else "count")
		return
	fight_time += delta
	_hero_step(delta)
	_update_flow()
	_spawn_step(delta)
	_foes_step(delta)
	_separate()
	_shots_step(delta)
	if not running:
		return
	_rum_step(delta)
	for i in range(_puffs.size() - 1, -1, -1):
		_puffs[i].z -= delta
		if _puffs[i].z <= 0.0:
			_puffs.remove_at(i)
	if fight_time >= tuning.max_seconds:
		end_demo(false)


## Цифра отсчёта 3-2-1, 0 после старта.
func _count_digit() -> int:
	return int(ceil(maxf(count_left, 0.0) / (tuning.countdown / 3.0)))


## Герой: ход стрелками (с B на месте, стрелки только поворачивают), выстрел по взгляду.
## Ввод с клавиатуры или от бота, ход через баг ввода (`Demo.bug_axis`).
func _hero_step(delta: float) -> void:
	var raw := _bot_move if bot_driven() else GameInput.axis()
	var axis := bug_axis(raw)
	if not bot_driven() and not has_bug(&"sticky_input"):
		# Отпускание могло уйти в паузу: кнопка не зажата, значит отпущена.
		_fire_a = _fire_a and Input.is_action_pressed(GameInput.A)
		_hold_b = _hold_b and Input.is_action_pressed(GameInput.B)
	var hold := _bot_hold if bot_driven() else _hold_b
	var fire := _bot_fire if bot_driven() else _fire_a
	hero_moving = false
	var want := Vector2.ZERO
	if axis.length() > 0.3:
		facing = _dir_index(axis.angle())
		_update_hero_frame()
		if not hold:
			want = axis.limit_length(1.0) * tuning.hero_speed
	if _ice > 0.0:
		# Палуба-каток: скорость догоняет желаемую с откликом `_ice`, в борт и проп гаснет по оси.
		_hero_vel = _hero_vel.lerp(want, 1.0 - exp(-_ice * delta))
		var before := hero
		hero = _slide(hero, _hero_vel * delta, tuning.hero_radius, false)
		if hero.x == before.x:
			_hero_vel.x = 0.0
		if hero.y == before.y:
			_hero_vel.y = 0.0
		hero_moving = _hero_vel.length() > 4.0
	elif want != Vector2.ZERO:
		hero = _slide(hero, want * delta, tuning.hero_radius, false)
		hero_moving = true
	invuln = maxf(invuln - delta, 0.0)
	_fire_cd -= delta
	# Залипание A: отпустил, и ещё пара выстрелов (`Demo.bug_stick`).
	if _fire_was and not fire:
		bug_stick()
	_fire_was = fire
	if _fire_cd <= 0.0 and (fire or bug_take_stick()):
		_fire()


func _fire() -> void:
	_fire_cd = tuning.fire_cooldown
	var d := DIRS[facing]
	var s := Shot.new()
	s.pos = hero + d * tuning.muzzle
	s.vel = d * tuning.ball_speed
	shots.append(s)
	shots_fired += 1
	_play("shot")


func _hurt(away: Vector2) -> void:
	if invuln > 0.0 or not running:
		return
	hp -= 1
	damage += 1
	invuln = tuning.hurt_invuln
	hero = _slide(hero, away * tuning.knockback, tuning.hero_radius, false)
	_play("hurt")
	if hp <= 0:
		end_demo(false)


## Точка свободна для тела радиуса `r`: борт и пропы держат всех, трап только героя.
func _free(p: Vector2, r: float, doors_ok: bool) -> bool:
	for o: Vector2 in [Vector2(-r, -r), Vector2(r, -r), Vector2(-r, r), Vector2(r, r)]:
		var t := arena.tile_at(p + o)
		if t == ShooterArena.Tile.WALL or t == ShooterArena.Tile.PROP or (t == ShooterArena.Tile.DOOR and not doors_ok):
			return false
	return true


## Сдвиг по осям отдельно: упёрлась ось, тело скользит вдоль.
func _slide(p: Vector2, d: Vector2, r: float, doors_ok: bool) -> Vector2:
	var nx := p + Vector2(d.x, 0.0)
	if _free(nx, r, doors_ok):
		p = nx
	var ny := p + Vector2(0.0, d.y)
	if _free(ny, r, doors_ok):
		p = ny
	return p


func _update_flow() -> void:
	var c := arena.cell_of(hero)
	if c != _flow_cell:
		_flow_cell = c
		_flow = arena.distances(c)


## Волны по очереди: враг из своего трапа раз в `spawn_gap`, пока на палубе меньше
## `max_alive`; следующая волна, когда врагов осталось мало или волна затянулась. Волны
## кончились: повторяется последняя.
func _spawn_step(delta: float) -> void:
	if _extra_left > 0:
		# «Не достать»: лишние враги лезут на палубу мимо волн, своим темпом.
		_extra_cd -= delta
		if _extra_cd <= 0.0 and foes.size() < tuning.max_alive:
			var e := ShooterArena.Spawn.new()
			e.kind = ShooterArena.Enemy.GUNNER if rng.randf() < 0.3 else ShooterArena.Enemy.WALKER
			e.door = rng.randi_range(0, arena.doors.size() - 1)
			_spawn(e)
			_extra_left -= 1
			extras += 1
			_extra_cd = tuning.spawn_gap
	if _wave_pause > 0.0:
		_wave_pause -= delta
		return
	_wave_time += delta
	var wave := arena.waves[mini(_wave, arena.waves.size() - 1)]
	if _wave_spawned < wave.spawns.size():
		_spawn_cd -= delta
		if _spawn_cd <= 0.0 and foes.size() < tuning.max_alive:
			_spawn(wave.spawns[_wave_spawned])
			_wave_spawned += 1
			_spawn_cd = tuning.spawn_gap
		return
	if foes.size() <= tuning.next_wave_alive or _wave_time >= tuning.wave_max:
		_wave += 1
		_wave_spawned = 0
		_wave_time = 0.0
		_wave_pause = tuning.wave_pause


func _spawn(s: ShooterArena.Spawn) -> void:
	var f := Foe.new()
	f.kind = s.kind
	f.door = s.door
	f.pos = arena.center_of(arena.doors[s.door])
	var gunner := s.kind == ShooterArena.Enemy.GUNNER
	f.hp = tuning.gunner_hp if gunner else tuning.walker_hp
	if _sneeze_px > 0.0:
		f.hp = 1
	f.fire_cd = tuning.first_shot
	f.strafe = 1.0 if rng.randf() < 0.5 else -1.0
	f.strafe_cd = tuning.strafe_flip * rng.randf_range(0.6, 1.4)
	foes.append(f)


func _foes_step(delta: float) -> void:
	for f in foes:
		f.anim += delta
		f.flash = maxf(f.flash - delta, 0.0)
		var before := f.pos
		if not f.aboard:
			# С трапа прямо внутрь, пока не встанет на палубу.
			f.pos += Vector2(arena.door_dirs[f.door]) * _speed(f) * delta
			if arena.tile_at(f.pos) == ShooterArena.Tile.FLOOR and _free(f.pos, tuning.enemy_radius, false):
				f.aboard = true
			continue
		var to := hero - f.pos
		var dist := to.length()
		var dir := Vector2.ZERO
		if f.kind == ShooterArena.Enemy.WALKER:
			dir = _chase(f)
		else:
			var los := arena.line_clear(f.pos, hero)
			if not los or dist > tuning.keep_max:
				dir = _chase(f)
			elif dist < tuning.keep_min:
				dir = -to / maxf(dist, 0.01)
			else:
				dir = (to / maxf(dist, 0.01)).orthogonal() * f.strafe
			f.strafe_cd -= delta
			if f.strafe_cd <= 0.0:
				f.strafe = -f.strafe
				f.strafe_cd = tuning.strafe_flip * rng.randf_range(0.6, 1.4)
			f.fire_cd -= delta
			if los and f.fire_cd <= 0.0 and dist < tuning.keep_max * 1.4:
				var s := Shot.new()
				s.hostile = true
				s.pos = f.pos + to / maxf(dist, 0.01) * 6.0
				s.vel = to / maxf(dist, 0.01) * tuning.shot_speed
				shots.append(s)
				f.fire_cd = tuning.fire_every * rng.randf_range(0.8, 1.2)
				f.flash = 0.2
				_play("enemy_shot")
		f.pos = _slide(f.pos, dir * _speed(f) * delta, tuning.enemy_radius, true)
		f.vel = (f.pos - before) / delta if delta > 0.0 else Vector2.ZERO
		if f.kind == ShooterArena.Enemy.GUNNER and dir != Vector2.ZERO and f.vel.length() < _speed(f) * 0.3:
			# Упёрся вбок: в другую сторону.
			f.strafe = -f.strafe
		if absf(to.x) > 1.0:
			f.face_left = to.x < 0.0
		if dist < tuning.hero_radius + tuning.enemy_radius:
			_hurt(-to / maxf(dist, 0.01))
			if not running:
				return


func _speed(f: Foe) -> float:
	return (tuning.gunner_speed if f.kind == ShooterArena.Enemy.GUNNER else tuning.walker_speed) * _foe_mult


## Направление к герою: напрямую, если широкая прямая свободна; иначе на соседнюю клетку
## ближе к герою по палубе (`_flow`), по диагонали только между свободными клетками.
func _chase(f: Foe) -> Vector2:
	var to := hero - f.pos
	if to.length() < 0.5:
		return Vector2.ZERO
	var side := to.normalized().orthogonal() * tuning.enemy_radius
	if arena.line_clear(f.pos, hero) and arena.line_clear(f.pos + side, hero + side) \
			and arena.line_clear(f.pos - side, hero - side):
		return to.normalized()
	var c := arena.cell_of(f.pos)
	var best := c
	var bd := _dist_at(c)
	if bd < 0:
		return to.normalized()
	for o: Vector2i in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1),
			Vector2i(1, 1), Vector2i(1, -1), Vector2i(-1, 1), Vector2i(-1, -1)]:
		if o.x != 0 and o.y != 0 and (_dist_at(c + Vector2i(o.x, 0)) < 0 or _dist_at(c + Vector2i(0, o.y)) < 0):
			continue
		var d := _dist_at(c + o)
		if d >= 0 and d < bd:
			bd = d
			best = c + o
	var target := arena.center_of(best)
	return (target - f.pos).normalized() if target.distance_to(f.pos) > 0.5 else to.normalized()


func _dist_at(c: Vector2i) -> int:
	if c.x < 0 or c.y < 0 or c.x >= arena.width or c.y >= arena.height or _flow.is_empty():
		return -1
	return _flow[c.y * arena.width + c.x]


## Враги не проходят друг сквозь друга: перекрытие делится пополам.
func _separate() -> void:
	var min_d := tuning.enemy_radius * 2.0
	for i in foes.size():
		for j in range(i + 1, foes.size()):
			var a := foes[i]
			var b := foes[j]
			var d := b.pos - a.pos
			var dist := d.length()
			if dist >= min_d:
				continue
			var push := (d / dist if dist > 0.01 else Vector2.RIGHT) * (min_d - dist) / 2.0
			a.pos = _slide(a.pos, -push, tuning.enemy_radius, true)
			b.pos = _slide(b.pos, push, tuning.enemy_radius, true)


## Ядра и пули: летят прямо, гаснут о борт, трап и пропы; ядро бьёт врага на палубе, пуля героя.
func _shots_step(delta: float) -> void:
	for i in range(shots.size() - 1, -1, -1):
		var s := shots[i]
		s.pos += s.vel * delta
		if arena.blocks_shot(s.pos):
			shots.remove_at(i)
			continue
		if s.hostile:
			if invuln <= 0.0 and s.pos.distance_to(hero) < tuning.hit_radius:
				shots.remove_at(i)
				_hurt(s.vel.normalized())
				if not running:
					return
			continue
		var target: Foe = null
		for f in foes:
			if not f.aboard or f == s.ghost or s.pos.distance_to(f.pos) >= tuning.hit_radius:
				continue
			if _pass_every > 0:
				# «Сквозь врагов»: каждое `_pass_every`-е касание, начиная с первого, не засчитано.
				var through := _contacts % _pass_every == 0
				_contacts += 1
				if through:
					s.ghost = f
					passes += 1
					if passes == 1 and AutoTest.enabled and not embedded:
						AutoTest.note("shooter bug: ядро прошло сквозь врага на %.1f с" % fight_time)
					continue
			target = f
			break
		if target != null:
			shots.remove_at(i)
			hits += 1
			target.hp -= 1
			if target.hp <= 0:
				_kill(target)
				if not running:
					return
			else:
				_play("hit")
		elif _sneeze_px > 0.0:
			# «Чих»: ядро валит врагов от ветра, пролетая рядом, и летит дальше.
			for f in foes.duplicate():
				if f.aboard and f != s.ghost and s.pos.distance_to(f.pos) < _sneeze_px:
					sneeze_kills += 1
					if sneeze_kills == 1 and AutoTest.enabled and not embedded:
						AutoTest.note("shooter bug: враг погиб от ветра ядра на %.1f с" % fight_time)
					_kill(f)
					if not running:
						return


func _kill(f: Foe) -> void:
	foes.erase(f)
	kills += 1
	if f.kind == ShooterArena.Enemy.GUNNER:
		kills_gunners += 1
	else:
		kills_walkers += 1
	_puffs.append(Vector3(f.pos.x, f.pos.y, PUFF_LIFE))
	_play("kill")
	if _extra_per_kill > 0.0:
		# «Не достать»: за убийство лишний враг на трап и цель на единицу дальше.
		_extra_acc += _extra_per_kill
		while _extra_acc >= 1.0:
			_extra_acc -= 1.0
			goal += 1
			_extra_left += 1
	if kills >= goal:
		end_demo(true)


## Ром: раз в `rum_every` на свободной клетке палубы, не рядом с героем и трапами, если прежний
## не подобран.
func _rum_step(delta: float) -> void:
	if _rum_on and hero.distance_to(_rum) < tuning.hero_radius + 6.0:
		_rum_on = false
		hp = mini(hp + tuning.rum_heal, tuning.hero_hp)
		rums += 1
		_play("rum")
	_rum_timer -= delta
	if _rum_timer > 0.0:
		return
	_rum_timer = tuning.rum_every
	if _rum_on:
		return
	for k in 60:
		var c := Vector2i(rng.randi_range(2, arena.width - 3), rng.randi_range(2, arena.height - 3))
		var p := arena.center_of(c)
		if arena.tile(c.x, c.y) == ShooterArena.Tile.FLOOR and p.distance_to(hero) > TILE * 3.0:
			_rum = p
			_rum_on = true
			return


# --- Бот ------------------------------------------------------------------------------------

## Бот автотеста и стрима. WIN: увернуться от пули, что вот-вот попадёт; если враг на одной из 8
## линий (с упреждением) и прямая свободна, встать (B), повернуться и стрелять; ходок вплотную:
## отойти; мало жизней и есть ром: к рому; иначе встать на линию с ближайшим врагом, держа
## дистанцию. LOSE: идёт к ближайшему врагу и не стреляет.
func _bot_step(_delta: float) -> void:
	_bot_move = Vector2.ZERO
	_bot_fire = false
	_bot_hold = false
	if count_left > 0.0 or foes.is_empty() and not _rum_on:
		return
	if active_bot_mode() != AutoTest.BotMode.WIN:
		var near := _nearest_foe(false)
		if near != null:
			_bot_move = _path_dir(near.pos)
		return
	var dodge := _bot_dodge()
	if dodge != Vector2.ZERO:
		_bot_move = dodge
		return
	var aim := _bot_aim()
	if aim >= 0:
		_bot_hold = true
		_bot_move = DIRS[aim]
		_bot_fire = facing == aim
		return
	var danger := Vector2.ZERO
	for f in foes:
		if f.aboard and f.kind == ShooterArena.Enemy.WALKER:
			var d := hero - f.pos
			if d.length() < tuning.bot_danger:
				danger += d.normalized() * (1.0 - d.length() / tuning.bot_danger)
	if danger != Vector2.ZERO:
		_bot_move = (danger.normalized() + (arena.size_px() / 2.0 - hero).normalized() * 0.4).normalized()
		return
	if _rum_on and hp < tuning.bot_rum_hp:
		_bot_move = _path_dir(_rum)
		return
	var target := _nearest_foe(true)
	if target == null:
		target = _nearest_foe(false)
	if target == null:
		return
	var r := target.pos - hero
	var best := 0
	var best_perp := INF
	for k in DIRS.size():
		var along := r.dot(DIRS[k])
		if along <= 8.0:
			continue
		var perp := absf(r.cross(DIRS[k]))
		if perp < best_perp:
			best_perp = perp
			best = k
	var d := DIRS[best]
	var along := r.dot(d)
	if not arena.line_clear(hero, target.pos) and best_perp < TILE:
		# На линии, но за пропом: обойти по палубе.
		_bot_move = _path_dir(target.pos)
		return
	var move := r - d * along
	move = move.normalized() if move.length() > 0.5 else Vector2.ZERO
	if along < tuning.bot_range_min:
		move -= d * 0.6
	elif along > tuning.bot_range_max:
		move += d * 0.6
	_bot_move = move.limit_length(1.0)


## Враг на линии выстрела: направление в `DIRS` или -1. С упреждением по шагу врага.
func _bot_aim() -> int:
	var best := -1
	var best_along := INF
	for f in foes:
		if not f.aboard:
			continue
		var lead := f.vel * (hero.distance_to(f.pos) / tuning.ball_speed)
		var r := f.pos + lead - hero
		for k in DIRS.size():
			var along := r.dot(DIRS[k])
			if along < tuning.hero_radius + tuning.muzzle or along >= best_along:
				continue
			if absf(r.cross(DIRS[k])) > tuning.bot_align:
				continue
			if not arena.line_clear(hero + DIRS[k] * tuning.muzzle, f.pos + lead):
				continue
			best = k
			best_along = along
	return best


## Пуля, что пройдёт ближе `bot_dodge` в ближайшие `bot_dodge_time` секунд: шаг поперёк неё,
## от линии полёта.
func _bot_dodge() -> Vector2:
	for s in shots:
		if not s.hostile:
			continue
		var r := hero - s.pos
		var v2 := s.vel.length_squared()
		var t := r.dot(s.vel) / maxf(v2, 0.01)
		if t <= 0.0 or t > tuning.bot_dodge_time:
			continue
		var closest := r - s.vel * t
		if closest.length() < tuning.bot_dodge:
			var side := closest.normalized() if closest.length() > 0.5 else s.vel.normalized().orthogonal()
			# Упёрся бы в борт или проп: в другую сторону.
			if not _free(hero + side * TILE * 0.75, tuning.hero_radius, false):
				side = -side
			return side
	return Vector2.ZERO


func _nearest_foe(aboard_only: bool) -> Foe:
	var best: Foe = null
	var bd := INF
	for f in foes:
		if aboard_only and not f.aboard:
			continue
		var d := f.pos.distance_squared_to(hero)
		if d < bd:
			bd = d
			best = f
	return best


## Шаг героя к точке по палубе: напрямую, если прямая свободна, иначе к соседней клетке ближе
## к цели (расстояния от клетки цели).
func _path_dir(p: Vector2) -> Vector2:
	var to := p - hero
	if to.length() < 1.0:
		return Vector2.ZERO
	if arena.line_clear(hero, p):
		return to.normalized()
	var dist := arena.distances(arena.cell_of(p))
	var c := arena.cell_of(hero)
	var best := c
	var bd := dist[c.y * arena.width + c.x]
	for o in ShooterArena.NEIGHBOURS:
		var n := c + o
		if n.x < 0 or n.y < 0 or n.x >= arena.width or n.y >= arena.height:
			continue
		if arena.tile(n.x, n.y) != ShooterArena.Tile.FLOOR:
			continue
		var d := dist[n.y * arena.width + n.x]
		if d >= 0 and (bd < 0 or d < bd):
			bd = d
			best = n
	var target := arena.center_of(best)
	return (target - hero).normalized() if target.distance_to(hero) > 0.5 else to.normalized()


# --- Рисование виртуального экрана ---------------------------------------------------------

## Прямой взгляд даёт свой кадр; диагональ оставляет прежний, если он соседний, иначе боковой.
func _update_hero_frame() -> void:
	if facing % 2 == 0:
		_hero_frame = facing / 2
	elif absi(wrapi(facing - _hero_frame * 2, -4, 4)) != 1:
		_hero_frame = 0 if DIRS[facing].x > 0.0 else 2


func _dir_index(angle: float) -> int:
	return posmod(int(round(angle / (PI / 4.0))), 8)


## Точка в пикселях демки, округлённая до пикселя экрана.
func _snap(p: Vector2) -> Vector2:
	return (p * scale_px).round() / scale_px


## Спрайт 16×16 центром в `p`; на строке тайлов сверх лимита мерцает (`Demo.flicker_hidden`).
func _sprite(slot: String, name: String, p: Vector2, flip := false, tint := Color.WHITE) -> void:
	if flicker_hidden(int(floor(p.y / TILE))):
		return
	var at := _snap(p) - Vector2(8, 8)
	if is_pink(slot):
		world.draw_rect(Rect2(at + Vector2(3, 3), Vector2(10, 10)), Color(PINK, tint.a))
	elif flip:
		world.draw_texture_rect(tex[name], Rect2(at, Vector2(-TILE, TILE)), false, tint)
	else:
		world.draw_texture(tex[name], at, tint)


func _draw_world() -> void:
	var t0 := Time.get_ticks_usec()
	_draw_world_layer()
	_perf_add("world", Time.get_ticks_usec() - t0)


func _draw_world_layer() -> void:
	flicker_reset()
	world.draw_texture(_map_tex, Vector2.ZERO)
	if _rum_on:
		_sprite("rum", "shoot_rum", _rum + Vector2(0.0, -1.0 if fmod(fight_time, 0.8) < 0.4 else 0.0))
	for p in _puffs:
		_sprite("puff", "shoot_puff", Vector2(p.x, p.y), false, Color(1, 1, 1, p.z / PUFF_LIFE))
	for f in foes:
		if f.kind == ShooterArena.Enemy.GUNNER:
			_sprite("gunner", "shoot_gunner_%d" % (1 if f.flash > 0.0 else 0), f.pos, f.face_left)
		else:
			_sprite("walker", "enemy_%d" % (int(f.anim / 0.25) % 2), f.pos, f.face_left)
	for s in shots:
		_sprite("shot" if s.hostile else "ball", "shoot_shot" if s.hostile else "shoot_ball", s.pos)
	var blink := invuln > 0.0 and fmod(invuln, 0.2) < 0.1
	if not blink:
		_sprite("hero", "shoot_hero_%d" % _hero_frame, hero)
	if (_bot_hold if bot_driven() else _hold_b) and count_left <= 0.0:
		# B зажата: прицел точками по взгляду.
		for k: float in [13.0, 18.0, 23.0]:
			world.draw_rect(Rect2((_snap(hero + DIRS[facing] * k)).floor(), Vector2.ONE), HUD_INK)


## Запечь статичную арену в текстуру: палуба из двух тайлов по хешу клетки, борт повёрнут
## брусом к палубе, углы, трапы поперёк борта, пропы (розовые заглушки запекаются сразу).
func _bake_map() -> void:
	var size := Vector2i(arena.size_px())
	var img := Image.create_empty(size.x, size.y, false, Image.FORMAT_RGBA8)
	var deck := [_tile_image("shoot_deck"), _tile_image("shoot_deck_1")]
	var rail := _turns(_tile_image("shoot_rail"))
	var corner := _turns(_tile_image("shoot_rail_corner"))
	var plank := _turns(_tile_image("shoot_plank"))
	var full := Rect2i(0, 0, TILE, TILE)
	var w := arena.width
	var h := arena.height
	for row in h:
		for col in w:
			var at := Vector2i(col, row) * TILE
			var t := arena.tile(col, row)
			if t == ShooterArena.Tile.FLOOR or t == ShooterArena.Tile.PROP:
				img.blit_rect(deck[1 if hash(col * 4096 + row) % 5 == 0 else 0], full, at)
				continue
			# Сторона борта: 0 верх, 1 право, 2 низ, 3 лево; угол по часовой с левого верхнего.
			var side := 0 if row == 0 else (2 if row == h - 1 else (3 if col == 0 else 1))
			var is_corner := (row == 0 or row == h - 1) and (col == 0 or col == w - 1)
			if is_corner:
				var turn := 0 if row == 0 and col == 0 else (1 if row == 0 else (2 if col == w - 1 else 3))
				img.blit_rect(corner[turn], full, at)
			elif t == ShooterArena.Tile.DOOR:
				img.blit_rect(plank[side], full, at)
			else:
				img.blit_rect(rail[side], full, at)
	for p in arena.props:
		var at := p.cell * TILE
		if is_pink(PROP_SLOTS[p.kind]):
			img.fill_rect(Rect2i(at + Vector2i(3, 3), Vector2i(10, 10)), PINK)
		else:
			img.blend_rect(_tile_image(PROP_SPRITES[p.kind]), full, at)
	_map_tex = ImageTexture.create_from_image(img)


## Тайл и его повороты на 90° по часовой: [0°, 90°, 180°, 270°].
func _turns(im: Image) -> Array[Image]:
	var out: Array[Image] = [im]
	for k in 3:
		var next := out[-1].duplicate() as Image
		next.rotate_90(CLOCKWISE)
		out.append(next)
	return out


func _tile_image(name: String) -> Image:
	var im := (tex[name] as Texture2D).get_image()
	if im.is_compressed():
		im.decompress()
	im.convert(Image.FORMAT_RGBA8)
	return im


## HUD в координатах экрана: жизни сердцами слева, уничтожено «N/30» справа, отсчёт.
func _draw_hud() -> void:
	var t0 := Time.get_ticks_usec()
	_draw_hud_layer()
	_perf_add("hud", Time.get_ticks_usec() - t0)


func _draw_hud_layer() -> void:
	var top := maxf(_origin.y, 0.0) + 3.0
	var left := maxf(_origin.x, 0.0) + 4.0
	for i in tuning.hero_hp:
		_draw_heart(Vector2(left + i * 12.0, top), i < hp)
	var text := "%d/%d" % [mini(kills, goal), goal]
	var right := minf(_origin.x + arena.size_px().x, view.x) - 4.0
	draw_pixel_text(hud, Vector2(right - text.length() * 8.0, top), text, HUD_INK, HUD_SHADOW)
	if count_left > 0.0 and _count_digit() > 0:
		var cell := 6.0
		draw_pixel_text(hud, (view / 2.0 - Vector2(1.5 * cell, 2.5 * cell + 24.0)).round(), str(_count_digit()), HUD_INK, HUD_SHADOW, cell)


## Сердце 5×5 клетками `cell` с тенью на клетку вправо-вниз, как цифры; потерянная жизнь тусклая.
func _draw_heart(pos: Vector2, full: bool, cell := 2.0) -> void:
	for pass_ in 2:
		for ry in HEART.size():
			for rx in 5:
				if HEART[ry][rx] == "1":
					var r := Rect2(pos + Vector2(rx, ry) * cell, Vector2(cell, cell))
					if pass_ == 0:
						hud.draw_rect(Rect2(r.position + Vector2(cell, cell) / 2.0, r.size), HUD_SHADOW)
					else:
						hud.draw_rect(r, HUD_INK if full else HUD_DIM)
