extends Demo
## Демка платформер × вектор, каталог `docs/specs/demos_catalog.md`: «этажи с дырами» (#90,
## решение 2026-11-11: не физика платформера 8-bit, а геймплей попроще и под технологию). Один
## экран, замкнутый по краям: земля и над ней линии-этажи, по линиям едут дыры, по этажам ходят
## враги. Влево и вправо бег, A прыжок вверх: под дырой герой поднимается на этаж, без дыры
## бьётся о потолок и ненадолго оглушён. Враг тоже оглушает. Дыра, проехавшая под ногами,
## роняет на этаж ниже, оглушённого тоже, и каждое падение стоит жизни. Цель: флаг на верхнем
## этаже; три жизни вместо таймера. Физики нет: подъём и падение это короткие переезды между
## этажами, всё держится на тайминге.
## Уровень из `TowerLevelGen` по сиду записи: скорости и направления дыр, враги, монеты, флаг.
## Правила и боты живут в `TowerSim` (без окна, им же проверяются сто сидов); демка ведёт его
## шагами, рисует и озвучивает его события. Рисуется на `VectorScreen` в логических пикселях карточки: линии, контуры слотов сеттинга,
## HUD штрихами; всё, что уходит за край, рисуется второй раз с другой стороны.
##
## Баги по флагам записи (параметры в `resources/bugs/<id>.tres`). Общие (#44) и баг технологии
## `beam_lag` живут в `Demo` и `VectorScreen`, демка только зовёт хуки: фризы `bug_frame`,
## заикание пищалки, ввод с опозданием и залипший прыжок (повторяется после подъёма), розовые
## заглушки вместо врагов, монет или флага. Свои проявления: `wild_physics` (баг жанра) прыжок
## на три этажа вместо одного: сквозь каждую следующую дыру герой летит дальше, а без дыры
## влетает в потолок и возвращается оглушённым надолго, с верхнего этажа улетает за край
## экрана; враги вдвое быстрее. `unreachable_coins` монеты висят под потолком, выше героя.
## `sneeze_enemies` враги рассыпаются от касания и не оглушают.

## Земля и пол верхнего этажа на логическом экране; между ними этажи поровну.
const GROUND_Y := 792.0
const TOP_Y := 168.0
## Логических пикселей на пиксель спрайта: герой, враг и флаг в высоту `TowerSim.BODY_H`.
const PX := TowerSim.BODY_H / 16.0
const BODY_H := TowerSim.BODY_H
const COIN_PX := 2.5
const INK_WORLD := 1
const INK_HERO := 2
const INK_DANGER := 3
const FLASH_SECONDS := 0.3
const PLACEHOLDER_SLOTS: Array[String] = ["enemy", "bonus", "finish"]
const MELODY := [0, null, 7, null, 12, null, 7, null, 3, null, 10, null, 15, null, 10, null,
	5, null, 12, null, 17, null, 12, 10, 7, null, 5, null, 3, 2, 0, null]

var tuning: PlatformerVectorTuning
var tower: TowerLevel
var sim: TowerSim
var bot_dir := 0.0

var _time := 0.0
var _flash := 0.0
var _flash_line := -1
var _flash_x := 0.0
var _music: AudioStreamPlayer
var _sfx := {}


func _on_start() -> void:
	tuning = PlatformerVectorTuning.load_default()
	var seed_ := record.seed if record != null else 1
	tower = TowerLevelGen.generate(seed_)
	sim = TowerSim.create(tower, tuning, (GROUND_Y - TOP_Y) / tower.floors)
	# Баги жанра и баланса; общие баги в `Demo` (#44).
	if has_bug(&"wild_physics"):
		sim.jump_levels = maxi(int(round(bug_param(&"wild_physics", &"jump_mult", 3.0))), 1)
		sim.enemy_mult = bug_param(&"wild_physics", &"enemy_speed_mult", 2.0)
	sim.coins_high = has_bug(&"unreachable_coins")
	sim.sneeze = has_bug(&"sneeze_enemies")
	vector_screen(_draw_vector)
	_setup_audio()


func _setup_audio() -> void:
	_music = Sfx.music(Sfx.beeper_loop(MELODY), tuning.music_db if not embedded else -80.0)
	add_child(_music)
	bug_music = _music
	if not embedded:
		_music.play()
	_sfx["jump"] = Sfx.player(Sfx.beep(440.0, 0.12, 0.25, 880.0))
	_sfx["land"] = Sfx.player(Sfx.beep(330.0, 0.05, 0.22))
	_sfx["fall"] = Sfx.player(Sfx.beep(660.0, 0.22, 0.25, 220.0))
	_sfx["bonk"] = Sfx.player(Sfx.beep(170.0, 0.12, 0.3, 90.0))
	_sfx["hit"] = Sfx.player(Sfx.beep(220.0, 0.35, 0.3, 80.0))
	_sfx["coin"] = Sfx.player(Sfx.beep(988.0, 0.08, 0.25, 1976.0))
	_sfx["pop"] = Sfx.player(Sfx.beep(520.0, 0.1, 0.25, 130.0))
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
		AutoTest.note("platformer vector: %s за %.1f с, этаж %d из %d, жизней %d, падений %d, монет %d из %d" % [
				"флаг" if goal else "провал", elapsed, sim.level, tower.floors, sim.lives, sim.falls, sim.coins_got,
				tower.coins.size()])


func _result_title(goal: bool) -> String:
	return "забрался" if goal else "не забрался"


func _result_caption() -> String:
	return "монеты %d из %d · падений %d · %d с" % [sim.coins_got, tower.coins.size(), sim.falls, int(round(elapsed))]


## Высота над землёй в координату экрана.
func _y(h: float) -> float:
	return GROUND_Y - h


# --- Ввод ------------------------------------------------------------------------------------

func _game_input(event: InputEvent) -> void:
	if GameInput.is_a(event):
		# С багом управления нажатие уходит в очередь с задержкой (`Demo.bug_press`).
		bug_press(_jump)
		get_viewport().set_input_as_handled()


## Прыжок; с багом управления удачный прыжок залипает и повторится после подъёма.
func _jump() -> void:
	if running and sim.jump():
		bug_stick()


## Бот `TowerSim`: ось движения, прыжок через `_jump`, чтобы залипание задело и его.
func _bot_step(delta: float) -> void:
	bot_dir = sim.bot(active_bot_mode(), delta)
	if sim.bot_jump:
		_jump()


# --- Шаг -------------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	# Фризы в движении с догоном времени (`Demo.bug_frame`).
	bug_frame(delta, sim.move_dir != 0.0 or sim.state != TowerSim.State.STAND, _step)


func _step(dt: float) -> void:
	_time += dt
	_flash = maxf(_flash - dt, 0.0)
	step_shards(dt)
	bug_input_tick()
	# Ось движения: с багом управления из прошлого на delay_ms (`Demo.bug_axis`).
	var raw := bot_dir if bot_driven() else GameInput.axis().x
	sim.step(dt, bug_axis(Vector2(raw, 0.0)).x)
	for ev in sim.events:
		_on_event(ev)
	sim.events.clear()


## Событие правил: звук, эффект, заметка автотеста, конец демки.
func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"jump":
			_play("jump")
		&"land":
			_play("land")
		&"arrive":
			_play("land")
			if bug_take_stick():
				_jump()
		&"fall":
			bug_clear_stick()
			_play("fall")
		&"coin":
			_play("coin")
		&"bonk":
			_flash = FLASH_SECONDS
			_flash_line = int(ev[1])
			_flash_x = float(ev[2])
			_play("bonk")
		&"pop":
			var i := int(ev[1])
			var e := tower.enemies[i]
			shatter_slot(&"enemy", Vector2(sim.enemy_x[i], _y(sim.floor_h(e.level)) - BODY_H / 2.0), PX, INK_DANGER, e.speed > 0.0)
			_play("pop")
		&"stunned":
			_play("bonk")
		&"hurt":
			# Провалился: герой рассыпается, пол под ним вспыхивает.
			_play("hit")
			_flash = FLASH_SECONDS
			_flash_line = sim.level
			_flash_x = sim.hero_x
			shatter_slot(&"hero", Vector2(sim.hero_x, _y(sim.hero_h) - BODY_H / 2.0), PX, INK_HERO, sim.facing < 0)
			bug_clear_stick()
			if AutoTest.enabled and not embedded:
				AutoTest.note("platformer vector: жизнь %d потеряна на %.1f с, x %.0f" % [sim.hits, elapsed, sim.hero_x])
		&"win":
			end_demo(true)
		&"lose":
			end_demo(false)


# --- Рисование -------------------------------------------------------------------------------

## Дыры линии как отрезки `от, до` в пределах экрана; дыра на краю разрезана на две.
func _line_gaps(line: int) -> Array[Vector2]:
	var out: Array[Vector2] = []
	var w := tower.width
	for i in sim.hole_x.size():
		var h := tower.holes[i]
		if h.line != line:
			continue
		var a := sim.hole_x[i] - h.width / 2.0
		var b := a + h.width
		if a < 0.0:
			out.append(Vector2(0.0, b))
			out.append(Vector2(a + w, w))
		elif b > w:
			out.append(Vector2(a, w))
			out.append(Vector2(0.0, b - w))
		else:
			out.append(Vector2(a, b))
	out.sort_custom(func(p: Vector2, q: Vector2) -> bool: return p.x < q.x)
	return out


## Слот с копией у противоположного края, когда он пересекает край экрана.
func _slot_wrapped(slot: StringName, center: Vector2, px: float, flip := false, angle := 0.0) -> void:
	draw_slot(slot, center, px, flip, angle)
	var reach := 8.0 * px
	if center.x < reach:
		draw_slot(slot, center + Vector2(tower.width, 0.0), px, flip, angle)
	elif center.x > tower.width - reach:
		draw_slot(slot, center - Vector2(tower.width, 0.0), px, flip, angle)


func _draw_vector(v: VectorScreen) -> void:
	if sim == null:
		return
	var w := tower.width
	# Земля со штриховкой и линии этажей с дырами.
	v.line(Vector2(0.0, GROUND_Y), Vector2(w, GROUND_Y), INK_WORLD, 3.0)
	if _flash_line == 0 and _flash > 0.0:
		v.line(Vector2(_flash_x - 70.0, GROUND_Y), Vector2(_flash_x + 70.0, GROUND_Y), INK_DANGER, 4.0, _flash / FLASH_SECONDS)
	var hx := 16.0
	while hx < w:
		v.line(Vector2(hx, GROUND_Y + 8.0), Vector2(hx - 14.0, GROUND_Y + 26.0), INK_WORLD, 2.0, 0.35)
		hx += 64.0
	for line in range(1, tower.floors + 1):
		var y := _y(sim.floor_h(line))
		var x := 0.0
		for g in _line_gaps(line):
			if g.x > x:
				v.line(Vector2(x, y), Vector2(g.x, y), INK_WORLD, 2.5)
			x = maxf(x, g.y)
		if x < w:
			v.line(Vector2(x, y), Vector2(w, y), INK_WORLD, 2.5)
		if line == _flash_line and _flash > 0.0:
			v.line(Vector2(_flash_x - 70.0, y), Vector2(_flash_x + 70.0, y), INK_DANGER, 4.0, _flash / FLASH_SECONDS)
	# Края дыр: губы вниз. Дыра, в которую сейчас можно прыгнуть, в цвете героя и со стрелкой.
	var open := sim.open_hole() if running else -1
	for i in sim.hole_x.size():
		var h := tower.holes[i]
		var y := _y(sim.floor_h(h.line))
		var half := h.width / 2.0
		var ink_i := INK_HERO if i == open else INK_WORLD
		for shift: float in [-w, 0.0, w]:
			var cx := sim.hole_x[i] + shift
			if cx + half < -20.0 or cx - half > w + 20.0:
				continue
			v.line(Vector2(cx - half, y), Vector2(cx - half + 10.0, y + 14.0), ink_i, 2.5)
			v.line(Vector2(cx + half, y), Vector2(cx + half - 10.0, y + 14.0), ink_i, 2.5)
			if i == open:
				v.poly(PackedVector2Array([Vector2(cx - 16.0, y + 8.0), Vector2(cx, y - 8.0), Vector2(cx + 16.0, y + 8.0)]),
						INK_HERO, false, 2.5, 0.85)
	# Монеты, флаг, враги.
	for i in sim.coin_alive.size():
		if sim.coin_alive[i]:
			var bob := sin(_time * 4.0 + i) * 3.0
			_slot_wrapped(&"bonus", Vector2(tower.coins[i].x, _y(sim.coin_h(i)) + bob), COIN_PX)
	_slot_wrapped(&"finish", Vector2(tower.flag_x, _y(sim.floor_h(tower.floors)) - BODY_H / 2.0), PX)
	for i in sim.enemy_x.size():
		if not sim.enemy_alive[i]:
			continue
		var e := tower.enemies[i]
		var bob := absf(sin(_time * 7.0 + i)) * 4.0
		_slot_wrapped(&"enemy", Vector2(sim.enemy_x[i], _y(sim.floor_h(e.level)) - BODY_H / 2.0 - bob), PX, e.speed > 0.0)
	# Герой: мигает, пока неуязвим; оглушённый качается, над головой кружат крестики.
	var stunned := sim.state == TowerSim.State.STUN
	var feet := _y(sim.hero_h)
	if sim.lives > 0 and (sim.invuln <= 0.0 or fmod(sim.invuln, 0.2) < 0.1):
		var angle := sin(_time * 18.0) * 0.16 if stunned else 0.0
		var bob := absf(sin(_time * 14.0)) * 5.0 if sim.move_dir != 0.0 else 0.0
		_slot_wrapped(&"hero", Vector2(sim.hero_x, feet - BODY_H / 2.0 - bob), PX, sim.facing < 0, angle)
	if stunned and sim.lives > 0:
		for k in 2:
			var a := _time * 7.0 + k * PI
			var c := Vector2(sim.hero_x + cos(a) * 26.0, feet - BODY_H - 12.0 + sin(a) * 6.0)
			v.line(c + Vector2(-5.0, -5.0), c + Vector2(5.0, 5.0), INK_HERO, 2.0, 0.9)
			v.line(c + Vector2(5.0, -5.0), c + Vector2(-5.0, 5.0), INK_HERO, 2.0, 0.9)
	draw_shards()
	# HUD штрихами: жизни иконками героя, монеты, этаж из этажей.
	for i in sim.lives:
		draw_slot(&"hero", Vector2(40.0 + i * 52.0, 44.0), 2.0)
	draw_slot(&"bonus", Vector2(228.0, 44.0), 2.0)
	v.digits(Vector2(258.0, 28.0), "%d" % sim.coins_got, 32.0, INK_HERO)
	var where := "%d/%d" % [sim.level, tower.floors]
	v.digits(Vector2(w - 32.0 - VectorScreen.digits_width(where, 32.0), 28.0), where, 32.0, INK_WORLD)
