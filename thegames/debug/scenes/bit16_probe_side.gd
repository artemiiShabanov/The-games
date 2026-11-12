extends Demo
## Пробная демка 16/32-bit, вид сбоку (#95) для `bit16_test`: не жанр, а проверка основы.
## Матрос бежит вправо по палубе (бот или стрелки), собирает дублоны, мимо ходят скелеты, стоят
## камни и сундуки, у флага итог. Камера едет за героем, за ней фон в три слоя (`Parallax16`).
## Общие баги через хуки `Demo`: фризы, заикание трекера, запоздалый ввод, розовые заглушки,
## чужая палитра на слое мира.

const LENGTH := 2600.0
const SPEED := 120.0
const MELODY := [0, null, 3, null, 7, 7, 5, 3, 2, null, 5, null, 3, 2, 0, null,
	-2, null, 2, null, 5, 5, 3, 2, 0, null, 3, null, 2, 0, -2, null]
const BASS := [-12, -12, -9, -9, -14, -14, -12, -12, -14, -14, -10, -10, -12, -12, -14, -14]

var hero_x := 80.0
var cam_x := 0.0
var collected := 0
var coins: Array[float] = []
## Скелеты: x и направление шага.
var enemies: Array[Vector2] = []
var props: Array[Vector2] = []
var parallax: Parallax16
var tex := {}
var _input_x := 0.0
var _t := 0.0
var _coin_sfx: AudioStreamPlayer


func _placeholder_slots() -> Array[String]:
	return ["enemy", "coin", "flag", "rock", "chest"]


func _on_start() -> void:
	bit16_screen(_draw_backdrop, _draw_world, _draw_hud)
	parallax = parallax16()
	for name in ["hero_run", "hero_jump", "enemy_walk", "coin", "flag", "ground", "ground_inner", "rock", "chest"]:
		tex[name] = bit16_set.sprite16(name)
	for i in 12:
		coins.append(260.0 + i * 190.0)
	for i in 5:
		enemies.append(Vector2(520.0 + i * 430.0, -1.0))
	for i in 6:
		props.append(Vector2(380.0 + i * 400.0, i % 2))
	var music := Sfx.music(Sfx.tracker_loop(MELODY, BASS), -10.0 if not embedded else -80.0)
	add_child(music)
	bug_music = music
	music.play()
	_coin_sfx = Sfx.player(Sfx.blip(1318.0, 0.12, 0.35, 14.0), -6.0 if not embedded else -80.0)
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
	hero_x = clampf(hero_x + dx * SPEED * dt, 20.0, LENGTH)
	cam_x = clampf(hero_x - bit16.view.x * 0.35, 0.0, LENGTH + 120.0 - bit16.view.x)
	for i in range(coins.size() - 1, -1, -1):
		if absf(coins[i] - hero_x) < 14.0:
			coins.remove_at(i)
			collected += 1
			bug_play(_coin_sfx)
	for i in enemies.size():
		var e := enemies[i]
		e.x += e.y * 26.0 * dt
		if fmod(_t, 3.0) < dt:
			e.y = -e.y
		enemies[i] = e
	if hero_x >= LENGTH - 30.0:
		end_demo(true)


## Верх палубы на экране.
func _ground_y() -> float:
	return bit16.view.y - 64.0


func _draw_backdrop(canvas: CanvasItem) -> void:
	parallax.draw(canvas, bit16.view, cam_x, roundf(bit16.view.y * 0.5), bit16.palette)


func _draw_world(canvas: CanvasItem) -> void:
	var view := bit16.view
	var gy := _ground_y()
	var first := int(floor(cam_x / 32.0))
	for col in range(first, first + int(view.x / 32.0) + 2):
		canvas.draw_texture(tex["ground"], Vector2(col * 32.0 - roundf(cam_x), gy))
		canvas.draw_texture(tex["ground_inner"], Vector2(col * 32.0 - roundf(cam_x), gy + 32.0))
	for p in props:
		var slot := "rock" if p.y < 0.5 else "chest"
		draw_sprite16(canvas, slot, tex[slot], 0, Vector2(p.x - roundf(cam_x), gy))
	var frame := int(_t * 10.0)
	for c in coins:
		draw_sprite16(canvas, "coin", tex["coin"], frame, Vector2(c - roundf(cam_x), gy - 26.0))
	for e in enemies:
		draw_sprite16(canvas, "enemy", tex["enemy_walk"], frame, Vector2(roundf(e.x) - roundf(cam_x), gy), e.y > 0.0)
	draw_sprite16(canvas, "flag", tex["flag"], int(_t * 8.0), Vector2(LENGTH - roundf(cam_x), gy))
	var moving := _input_x != 0.0
	bit16.sprite(canvas, tex["hero_run"], int(_t * 12.0) if moving else 0, Vector2(roundf(hero_x) - roundf(cam_x), gy),
			_input_x < 0.0)


func _draw_hud(canvas: CanvasItem) -> void:
	bit16.sprite(canvas, tex["coin"], 0, Vector2(22.0, 38.0))
	draw_pixel_text(canvas, Vector2(42.0, 14.0), str(collected), bit16.ink(Bit16Screen.WHITE), bit16.ink(Bit16Screen.K), 3.0)


func _result_caption() -> String:
	return "монет %d" % collected
