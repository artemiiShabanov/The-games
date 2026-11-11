extends Demo
## Пробная ASCII-демка (#88) для `ascii_test`: не жанр, а проверка основы. Комната во весь
## экран: борт по краям, палуба снизу, рея посередине, монеты, враги стоят, флаг справа. Герой
## идёт вправо по клетке за шаг (бот или стрелки), собирает монеты, у флага итог. Все общие баги
## идут через хуки `Demo`: фризы `bug_frame`, заикание пищалки `bug_music`, запоздалый ввод
## `bug_axis`, розовые «?» на слотах `_placeholder_slots`, чужая палитра на сетке.

const STEP_SECONDS := 0.06
const MELODY := [0, null, 3, null, 7, 5, 3, null, 0, null, -2, null, 0, null, null, null]

var hero := Vector2i.ZERO
var coins: Array[Vector2i] = []
var enemies: Array[Vector2i] = []
var finish := Vector2i.ZERO
var collected := 0
var _step_left := 0.0
var _input_x := 0.0
var _coin_sfx: AudioStreamPlayer


func _placeholder_slots() -> Array[String]:
	return ["enemy", "bonus", "finish", "prop_a", "prop_b", "platform"]


func _on_start() -> void:
	ascii_screen()
	var floor_y := ascii.rows - 4
	hero = Vector2i(2, floor_y - 1)
	finish = Vector2i(ascii.cols - 3, floor_y - 1)
	for i in 8:
		coins.append(Vector2i(10 + i * 11, floor_y - 1 - (i % 2) * 3))
	for i in 3:
		enemies.append(Vector2i(25 + i * 26, floor_y - 6))
	var music := Sfx.music(Sfx.beeper_loop(MELODY), -8.0 if not embedded else -80.0)
	add_child(music)
	bug_music = music
	music.play()
	_coin_sfx = Sfx.player(Sfx.beep(988.0, 0.08, 0.25, 1976.0), -6.0 if not embedded else -80.0)
	add_child(_coin_sfx)
	_redraw()


func _game_input(event: InputEvent) -> void:
	if event.is_action(GameInput.LEFT) or event.is_action(GameInput.RIGHT):
		_input_x = Input.get_axis(GameInput.LEFT, GameInput.RIGHT)


func _bot_step(_delta: float) -> void:
	_input_x = 1.0 if active_bot_mode() != AutoTest.BotMode.LOSE else 0.0


func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	bug_input_tick()
	if bug_frame(delta, _input_x != 0.0, _step):
		_redraw()


func _step(dt: float) -> void:
	_step_left -= dt
	if _step_left > 0.0:
		return
	_step_left = STEP_SECONDS
	var dx := int(signf(bug_axis(Vector2(_input_x, 0.0)).x))
	if dx == 0:
		return
	hero.x = clampi(hero.x + dx, 1, ascii.cols - 2)
	var i := coins.find(hero)
	if i >= 0:
		coins.remove_at(i)
		collected += 1
		bug_play(_coin_sfx)
	if hero == finish:
		end_demo(true)


func _redraw() -> void:
	ascii.clear()
	var floor_y := ascii.rows - 4
	ascii.text(1, 0, "ДУБЛОНЫ %d" % collected, 1)
	ascii.text(ascii.cols - 14, 0, "ВРЕМЯ %4.1f" % elapsed, 1)
	for x in ascii.cols:
		put_slot(x, floor_y, &"ground")
		put_slot(x, floor_y + 1, &"ground")
	for y in range(1, floor_y):
		put_slot(0, y, &"wall")
		put_slot(ascii.cols - 1, y, &"wall")
	for x in range(20, ascii.cols - 20):
		put_slot(x, floor_y - 5, &"platform")
	put_slot(14, floor_y - 1, &"prop_a")
	put_slot(60, floor_y - 1, &"prop_b")
	for c in coins:
		put_slot(c.x, c.y, &"bonus")
	for e in enemies:
		put_slot(e.x, e.y, &"enemy")
	put_slot(finish.x, finish.y, &"finish")
	put_slot(hero.x, hero.y, &"hero")
	ascii_legend(ascii.rows - 1, [&"hero", &"enemy", &"bonus", &"finish"])


func _result_caption() -> String:
	return "дублонов %d" % collected
