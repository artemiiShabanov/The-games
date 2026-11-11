extends Demo
## Демка шутер × вектор, каталог `docs/specs/demos_catalog.md`: «башня в центре» (#92, решение
## 2026-11-12: не корабль с тягой и инерцией, а геймплей попроще и под технологию). Пушка
## стоит в центре экрана и не ездит: влево и вправо поворот ствола, A выстрел, пока держишь.
## Со всех сторон к башне летят враги: враг прямо и быстро, глыба медленно и от попадания
## раскалывается на два быстрых осколка, вьюн по спирали. Цель уничтожить 30; кто долетел до
## башни, стоит жизни и сметает всех рядом, жизней три. Полёта, тяги и инерции нет: всё на
## том, куда повернуть ствол первым.
## Волны из `TurretWaveGen` по сиду записи: когда, откуда и с какой скоростью летят. Правила и
## боты живут в `TurretSim` (без окна, им же проверяются сто сидов); демка ведёт его шагами,
## рисует и озвучивает его события. Рисуется на `VectorScreen` в логических пикселях
## карточки: башня кольцом с героем внутри и стволом, пунктир прицела, враги контурами слотов
## сеттинга, выстрелы короткими отрезками, HUD штрихами.
##
## Баги по флагам записи (параметры в `resources/bugs/<id>.tres`). Общие (#44) и баг технологии
## `beam_lag` живут в `Demo` и `VectorScreen`, демка только зовёт хуки: фризы `bug_frame`,
## заикание пищалки, поворот и выстрел с опозданием, залипший выстрел (пушка стреляет ещё,
## когда кнопку отпустили), розовые заглушки вместо врагов, вьюнов или глыб. Свои проявления:
## `through_enemies` (баг жанра) каждый второй выстрел пролетает сквозь врагов; `wild_physics`
## лёд, ствол набирает и теряет вращение не сразу, враги быстрее; `unreachable_coins` враги
## без конца, цель растёт с каждым убитым; `sneeze_enemies` выстрел убивает и пролетев рядом,
## глыба гибнет целиком.

const ENEMY_PX := 4.0
const ROCK_PX := 5.5
const SMALL_PX := 3.0
const HERO_PX := 3.0
const INK_WORLD := 1
const INK_HERO := 2
const INK_DANGER := 3
const SHOT_LEN := 24.0
const BLAST_SECONDS := 0.4
const PLACEHOLDER_SLOTS: Array[String] = ["enemy", "enemy_2", "obstacle"]
const SLOTS: Array[StringName] = [&"enemy", &"obstacle", &"obstacle", &"enemy_2"]
const MELODY := [0, null, 0, 3, null, 3, 7, null, 5, null, 5, 8, null, 8, 12, null,
	10, null, 10, 7, null, 7, 3, null, 2, null, 2, 5, null, 3, 0, null]

var tuning: ShooterVectorTuning
var waves: TurretWaves
var sim: TurretSim
var bot_axis := 0.0

var _time := 0.0
var _blast := 0.0
var _hurt_blink := 0.0
## Залипший выстрел: сколько ещё выстрелов пушка сделает сама после отпущенной кнопки.
var _stuck_shots := 0
var _was_firing := false
var _music: AudioStreamPlayer
var _sfx := {}


func _on_start() -> void:
	tuning = ShooterVectorTuning.load_default()
	waves = TurretWaveGen.generate(record.seed if record != null else 1)
	sim = TurretSim.create(waves, tuning, CardFrame.inner_size() / 2.0)
	# Баги жанра и баланса; общие баги в `Demo` (#44).
	if has_bug(&"through_enemies"):
		sim.pass_every = maxi(int(bug_param(&"through_enemies", &"pass_every", 2.0)), 1)
	if has_bug(&"wild_physics"):
		sim.ice = bug_param(&"wild_physics", &"ice_response", 2.5)
		sim.foe_mult = bug_param(&"wild_physics", &"foe_speed_mult", 1.5)
	if has_bug(&"unreachable_coins"):
		sim.extra_per_kill = bug_param(&"unreachable_coins", &"extra_per_kill", 1.0)
	if has_bug(&"sneeze_enemies"):
		sim.near_miss = bug_param(&"sneeze_enemies", &"near_miss_px", 18.0)
		sim.one_hit = true
	vector_screen(_draw_vector)
	_setup_audio()


func _setup_audio() -> void:
	_music = Sfx.music(Sfx.beeper_loop(MELODY, 160.0), tuning.music_db if not embedded else -80.0)
	add_child(_music)
	bug_music = _music
	if not embedded:
		_music.play()
	_sfx["shot"] = Sfx.player(Sfx.beep(880.0, 0.06, 0.2, 440.0))
	_sfx["kill"] = Sfx.player(Sfx.beep(520.0, 0.12, 0.25, 130.0))
	_sfx["split"] = Sfx.player(Sfx.beep(260.0, 0.16, 0.28, 520.0))
	_sfx["hurt"] = Sfx.player(Sfx.beep(220.0, 0.4, 0.3, 70.0))
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
		AutoTest.note("shooter vector: %s за %.1f с, уничтожено %d из %.0f, жизней %d, выстрелов %d" % [
				"отбился" if goal else "не отбился", elapsed, sim.kills, sim.goal, sim.lives, sim.shots_fired])


func _result_title(goal: bool) -> String:
	return "отбился" if goal else "не отбился"


func _result_caption() -> String:
	return "уничтожено %d из %.0f · жизней %d · %d с" % [sim.kills, sim.goal, sim.lives, int(round(elapsed))]


# --- Ввод и шаг ------------------------------------------------------------------------------

func _bot_step(_delta: float) -> void:
	bot_axis = sim.bot(active_bot_mode())


func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	# Фризы на ходу с догоном времени (`Demo.bug_frame`).
	bug_frame(delta, true, _step)


func _step(dt: float) -> void:
	_time += dt
	_blast = maxf(_blast - dt, 0.0)
	_hurt_blink = maxf(_hurt_blink - dt, 0.0)
	step_shards(dt)
	# Поворот и выстрел: с багом управления из прошлого на delay_ms (`Demo.bug_axis`).
	var bot := bot_driven()
	var raw := Vector2(bot_axis if bot else GameInput.axis().x,
			1.0 if (sim.bot_fire if bot else Input.is_action_pressed(GameInput.A)) else 0.0)
	var input := bug_axis(raw)
	var firing := input.y > 0.5
	# Залипание: кнопку отпустили, а пушка делает ещё несколько выстрелов сама.
	if firing and not _was_firing:
		bug_stick()
	if _was_firing and not firing:
		while bug_take_stick():
			_stuck_shots += 1
	_was_firing = firing
	sim.step(dt, input.x, firing or _stuck_shots > 0)
	for ev in sim.events:
		_on_event(ev)
	sim.events.clear()


## Событие правил: звук, эффект, конец демки.
func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"shot":
			if _stuck_shots > 0 and not _was_firing:
				_stuck_shots -= 1
			_play("shot")
		&"kill":
			_burst(int(ev[1]), ev[2], int(ev[3]))
			_play("kill")
		&"split":
			_play("split")
		&"swept":
			_burst(int(ev[1]), ev[2], int(ev[3]))
		&"hurt":
			_blast = BLAST_SECONDS
			_hurt_blink = 1.2
			_stuck_shots = 0
			bug_clear_stick()
			shatter_slot(&"hero", _center(), HERO_PX, INK_HERO)
			_play("hurt")
			if AutoTest.enabled and not embedded:
				AutoTest.note("shooter vector: жизнь потеряна на %.1f с, осталось %d, уничтожено %d" % [elapsed, sim.lives, sim.kills])
		&"win":
			end_demo(true)
		&"lose":
			end_demo(false)


## Враг рассыпается на отрезки там, где его достали.
func _burst(kind: int, at: Vector2, id: int) -> void:
	var slot := SLOTS[kind]
	if is_pink(String(slot)):
		return
	shatter_slot(slot, _center() + at, _px(kind), vector_set.vector_ink(slot) if kind != TurretWaves.Kind.SPINNER else INK_DANGER,
			false, _spin_angle(kind, id))


# --- Рисование -------------------------------------------------------------------------------

func _center() -> Vector2:
	return vector.logical_size / 2.0


func _px(kind: int) -> float:
	match kind:
		TurretWaves.Kind.ROCK:
			return ROCK_PX
		TurretWaves.Kind.SMALL:
			return SMALL_PX
	return ENEMY_PX


## Глыбы и осколки медленно вращаются, каждый со своей фазы.
func _spin_angle(kind: int, id: int) -> float:
	if kind == TurretWaves.Kind.ROCK or kind == TurretWaves.Kind.SMALL:
		return _time * (0.7 if kind == TurretWaves.Kind.ROCK else 1.6) + id * 1.3
	return 0.0


func _draw_vector(v: VectorScreen) -> void:
	if sim == null:
		return
	var c := _center()
	var aim := Vector2.from_angle(sim.aim)
	# Деления вокруг башни и пунктир прицела по стволу.
	for k in 12:
		var d := Vector2.from_angle(TAU * k / 12.0)
		v.line(c + d * 104.0, c + d * (118.0 if k % 3 == 0 else 112.0), INK_WORLD, 2.0, 0.35)
	var reach := 132.0
	while reach < 420.0:
		v.line(c + aim * reach, c + aim * (reach + 8.0), INK_HERO, 2.0, 0.4)
		reach += 30.0
	# Башня: кольцо, внутри герой (мигает после потери жизни), ствол со стрелкой.
	v.poly(_circle(c, tuning.turret_radius, 20), INK_WORLD, true, 2.5)
	if sim.lives > 0 and (_hurt_blink <= 0.0 or fmod(_hurt_blink, 0.2) < 0.1):
		draw_slot(&"hero", c, HERO_PX)
	var side := aim.orthogonal()
	v.line(c + aim * tuning.turret_radius, c + aim * tuning.muzzle, INK_HERO, 4.0)
	v.poly(PackedVector2Array([c + aim * (tuning.muzzle + 14.0), c + aim * tuning.muzzle + side * 9.0,
			c + aim * tuning.muzzle - side * 9.0]), INK_HERO, true, 2.5)
	if _blast > 0.0:
		var k := 1.0 - _blast / BLAST_SECONDS
		v.poly(_circle(c, lerpf(tuning.turret_radius, tuning.blast_radius, k), 32), INK_DANGER, true, 3.0, 1.0 - k)
	# Враги: лицом к башне; глыбы и осколки вращаются.
	for f in sim.foes:
		if not f.alive:
			continue
		var p := c + f.pos()
		var slot := SLOTS[f.kind]
		draw_slot(slot, p, _px(f.kind), p.x < c.x and f.kind != TurretWaves.Kind.ROCK and f.kind != TurretWaves.Kind.SMALL,
				_spin_angle(f.kind, f.id))
	# Выстрелы короткими отрезками.
	for sh in sim.shots:
		if sh.alive:
			v.line(c + sh.pos - sh.dir * SHOT_LEN, c + sh.pos, INK_HERO, 3.0)
	draw_shards()
	# HUD штрихами: жизни иконками героя, счёт уничтоженных из цели.
	for i in sim.lives:
		draw_slot(&"hero", Vector2(40.0 + i * 52.0, 44.0), 2.0)
	var score := "%d/%d" % [sim.kills, int(sim.goal)]
	v.digits(Vector2(v.logical_size.x - 32.0 - VectorScreen.digits_width(score, 36.0), 26.0), score, 36.0, INK_HERO)


static func _circle(center: Vector2, radius: float, points: int) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in points:
		pts.append(center + Vector2.from_angle(TAU * i / points) * radius)
	return pts
