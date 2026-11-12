extends Demo
## Пробная демка 16/32-bit, вид вглубь экрана (#95) для `bit16_test`: не жанр, а проверка
## основы. Матрос бежит со спины по причалу, который уходит к горизонту (`Scaler16`); навстречу
## вырастают дублоны, камни и скелеты. Влево и вправо шаг в сторону, бот собирает дублоны и
## обходит камни. Над горизонтом те же слои неба и берега, что у вида сбоку. Общие баги через
## хуки `Demo`.

const LENGTH := 5200.0
const SPEED := 300.0
const SIDE_SPEED := 150.0
const HALF_ROAD := 150.0
const HERO_Z := 80.0
const MELODY := [0, null, 7, null, 12, null, 7, 5, 3, null, 10, null, 15, null, 10, 7,
	5, null, 12, null, 17, null, 12, 10, 7, null, 5, null, 3, 2, 0, null]
const BASS := [-12, -12, -5, -5, -9, -9, -2, -2, -7, -7, 0, 0, -12, -12, -14, -14]

## Что стоит на пути: x, расстояние от старта, вид (0 дублон, 1 камень, 2 скелет).
var things: Array[Vector3] = []
var taken: Array[bool] = []
var dist := 0.0
var hero_x := 0.0
var collected := 0
var scaler: Scaler16
var parallax: Parallax16
var tex := {}
var _input_x := 0.0
var _t := 0.0
var _coin_sfx: AudioStreamPlayer


func _placeholder_slots() -> Array[String]:
	return ["enemy", "coin", "rock"]


func _on_start() -> void:
	bit16_screen(_draw_backdrop, _draw_world, _draw_hud)
	scaler = Scaler16.make(bit16.view)
	parallax = Parallax16.of(bit16_set)
	for name in ["hero_back", "enemy_front", "coin", "rock", "flag"]:
		tex[name] = bit16_set.sprite16(name)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed if record != null else 1, ":depth"))
	var d := 500.0
	while d < LENGTH - 300.0:
		things.append(Vector3(rng.randf_range(-HALF_ROAD + 30.0, HALF_ROAD - 30.0), d, rng.randi_range(0, 2)))
		taken.append(false)
		d += rng.randf_range(160.0, 300.0)
	var music := Sfx.music(Sfx.tracker_loop(MELODY, BASS, 144.0), -10.0 if not embedded else -80.0)
	add_child(music)
	bug_music = music
	music.play()
	_coin_sfx = Sfx.player(Sfx.blip(1318.0, 0.12, 0.35, 14.0), -6.0 if not embedded else -80.0)
	add_child(_coin_sfx)


func _game_input(event: InputEvent) -> void:
	if event.is_action(GameInput.LEFT) or event.is_action(GameInput.RIGHT):
		_input_x = Input.get_axis(GameInput.LEFT, GameInput.RIGHT)


## Бот: к ближайшему впереди дублону, от ближайшего камня.
func _bot_step(_delta: float) -> void:
	_input_x = 0.0
	if active_bot_mode() == AutoTest.BotMode.LOSE:
		return
	for i in things.size():
		var th := things[i]
		var ahead := th.y - dist - HERO_Z
		if taken[i] or ahead < 0.0 or ahead > 500.0:
			continue
		if int(th.z) == 0:
			_input_x = clampf((th.x - hero_x) / 10.0, -1.0, 1.0)
		elif absf(th.x - hero_x) < 44.0:
			_input_x = -1.0 if th.x > hero_x else 1.0
		return


func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	bug_input_tick()
	bug_frame(delta, true, _step)


func _step(dt: float) -> void:
	_t += dt
	dist += SPEED * dt
	hero_x = clampf(hero_x + bug_axis(Vector2(_input_x, 0.0)).x * SIDE_SPEED * dt, -HALF_ROAD + 20.0, HALF_ROAD - 20.0)
	for i in things.size():
		var th := things[i]
		if not taken[i] and int(th.z) == 0 and absf(th.y - dist - HERO_Z) < 26.0 and absf(th.x - hero_x) < 30.0:
			taken[i] = true
			collected += 1
			bug_play(_coin_sfx)
	if dist >= LENGTH:
		end_demo(true)


func _draw_backdrop(canvas: CanvasItem) -> void:
	parallax.draw(canvas, bit16.view, hero_x * 0.6 + dist * 0.02, scaler.horizon, bit16.palette)


func _draw_world(canvas: CanvasItem) -> void:
	var pal := bit16.palette
	scaler.draw_ground(canvas, dist, pal[Bit16Screen.SEA], pal[Bit16Screen.NAVY])
	scaler.draw_road(canvas, dist, -hero_x * 0.0, HALF_ROAD, pal[Bit16Screen.WOOD], pal[Bit16Screen.GOLD], pal[Bit16Screen.BARK],
			pal[Bit16Screen.BARK], 3)
	var frame := int(_t * 10.0)
	for i in things.size():
		var th := things[i]
		var z := th.y - dist
		if taken[i] or z < scaler.near or z > 2600.0:
			continue
		match int(th.z):
			0:
				scaler.add(tex["coin"], frame, th.x, z, false, is_pink("coin"), 6.0)
			1:
				scaler.add(tex["rock"], 0, th.x, z, false, is_pink("rock"))
			_:
				scaler.add(tex["enemy_front"], frame, th.x, z, false, is_pink("enemy"))
	var flag_z := LENGTH + HERO_Z - dist
	if flag_z < 2600.0:
		scaler.add(tex["flag"], int(_t * 8.0), HALF_ROAD + 30.0, flag_z)
	scaler.add(tex["hero_back"], int(_t * 12.0), hero_x, HERO_Z)
	scaler.flush(bit16, canvas)


func _draw_hud(canvas: CanvasItem) -> void:
	bit16.sprite(canvas, tex["coin"], 0, Vector2(22.0, 38.0))
	draw_pixel_text(canvas, Vector2(42.0, 14.0), str(collected), bit16.ink(Bit16Screen.WHITE), bit16.ink(Bit16Screen.K), 3.0)


func _result_caption() -> String:
	return "дублонов %d" % collected
