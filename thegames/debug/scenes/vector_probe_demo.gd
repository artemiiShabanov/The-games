extends Demo
## Пробная векторная демка (#88) для `vector_test`: не жанр, а проверка основы. Земля ломаной
## линией с холмами, герой бежит вправо (бот или стрелки), монеты крутятся, враги ходят, у флага
## итог. Камера едет за героем, за всем движущимся тянется след люминофора. Все слоты сеттинга
## стоят вдоль пути. Общие баги через хуки `Demo`: фризы `bug_frame`, заикание пищалки, запоздалый
## ввод `bug_axis`, розовые кресты `_placeholder_slots`, чужая палитра на экране.

const LENGTH := 5000.0
const SPEED := 260.0
const PX := 4.0
const GROUND_Y := 640.0
const MELODY := [0, null, 3, null, 7, 5, 3, null, 0, null, -2, null, 0, null, null, null]
const PROPS: Array[StringName] = [&"prop_a", &"obstacle", &"vehicle", &"rival", &"ball", &"goal",
		&"enemy_2", &"shot", &"prop_b"]

var hero_x := 120.0
var cam_x := 0.0
var collected := 0
var coins: Array[float] = []
var enemies: Array[Vector2] = []
var _input_x := 0.0
var _coin_sfx: AudioStreamPlayer
var _t := 0.0


func _placeholder_slots() -> Array[String]:
	return ["enemy", "bonus", "finish", "prop_a", "prop_b", "obstacle"]


func _on_start() -> void:
	vector_screen(_draw_vector)
	for i in 14:
		coins.append(500.0 + i * 320.0)
	for i in 5:
		enemies.append(Vector2(900.0 + i * 850.0, -1.0))
	var music := Sfx.music(Sfx.beeper_loop(MELODY), -8.0 if not embedded else -80.0)
	add_child(music)
	bug_music = music
	music.play()
	_coin_sfx = Sfx.player(Sfx.beep(988.0, 0.08, 0.25, 1976.0), -6.0 if not embedded else -80.0)
	add_child(_coin_sfx)


func _game_input(event: InputEvent) -> void:
	if event.is_action(GameInput.LEFT) or event.is_action(GameInput.RIGHT):
		_input_x = Input.get_axis(GameInput.LEFT, GameInput.RIGHT)


func _bot_step(_delta: float) -> void:
	_input_x = 1.0 if active_bot_mode() != AutoTest.BotMode.LOSE else 0.0


func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	bug_input_tick()
	bug_frame(delta, _input_x != 0.0, _step)


func _step(dt: float) -> void:
	_t += dt
	var dx := bug_axis(Vector2(_input_x, 0.0)).x
	hero_x = clampf(hero_x + dx * SPEED * dt, 40.0, LENGTH)
	cam_x = clampf(hero_x - vector.logical_size.x * 0.35, 0.0, LENGTH + 200.0 - vector.logical_size.x)
	for i in range(coins.size() - 1, -1, -1):
		if absf(coins[i] - hero_x) < 24.0:
			coins.remove_at(i)
			collected += 1
			bug_play(_coin_sfx)
	for i in enemies.size():
		var e := enemies[i]
		e.x += e.y * 60.0 * dt
		if fmod(_t, 4.0) < dt:
			e.y = -e.y
		enemies[i] = e
	if hero_x >= LENGTH - 40.0:
		end_demo(true)


func _ground(x: float) -> float:
	return GROUND_Y - 60.0 * maxf(0.0, sin(x / 520.0)) - 30.0 * sin(x / 170.0) * 0.3


func _draw_vector(v: VectorScreen) -> void:
	var view := v.logical_size
	# Земля ломаной, видимая часть.
	var pts := PackedVector2Array()
	var x := floorf(cam_x / 40.0) * 40.0
	while x <= cam_x + view.x + 40.0:
		pts.append(Vector2(x - cam_x, _ground(x)))
		x += 40.0
	v.poly(pts, 1)
	for i in PROPS.size():
		var px := 300.0 + i * 520.0
		if px > cam_x - 100.0 and px < cam_x + view.x + 100.0:
			draw_slot(PROPS[i], Vector2(px - cam_x, _ground(px) - 8.0 * PX), PX)
	for c in coins:
		if c > cam_x - 50.0 and c < cam_x + view.x + 50.0:
			draw_slot(&"bonus", Vector2(c - cam_x, _ground(c) - 120.0), PX * 0.8, false, 0.0)
	for e in enemies:
		if e.x > cam_x - 50.0 and e.x < cam_x + view.x + 50.0:
			draw_slot(&"enemy", Vector2(e.x - cam_x, _ground(e.x) - 8.0 * PX), PX, e.y > 0.0)
	var fx := LENGTH
	draw_slot(&"finish", Vector2(fx - cam_x, _ground(fx) - 8.0 * PX), PX)
	var bob := absf(sin(_t * 10.0)) * 6.0
	draw_slot(&"hero", Vector2(hero_x - cam_x, _ground(hero_x) - 8.0 * PX - bob), PX)
	# HUD штрихами: жизни иконками, монеты, время.
	for i in 2:
		draw_slot(&"hero", Vector2(36.0 + i * 52.0, 40.0), 2.0)
	draw_slot(&"bonus", Vector2(170.0, 40.0), 2.0)
	v.digits(Vector2(200.0, 24.0), "%d" % collected, 32.0, 2)
	var tm := "%d" % int(elapsed)
	v.digits(Vector2(view.x - 30.0 - VectorScreen.digits_width(tm, 32.0), 24.0), tm, 32.0, 1)


func _result_caption() -> String:
	return "монет %d" % collected
