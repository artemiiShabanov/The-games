extends Demo
## Демка спорт × 16/32-bit «футбол один на одного» (#101, решение 2026-11-12,
## `docs/specs/demos_catalog.md`), графика по Sensible Soccer: вид сверху, стоящие игроки 24×24
## в восьми направлениях (с плейтеста 2026-11-15 крупнее, бег в четыре кадра), мяч с высотой и тенью, камера за мячом. Два на два с
## вратарями-ботами (плейтест 2026-11-12): в атаке играешь за того, у кого мяч, в защите за
## последнего; над ним жёлтая метка. Стрелки бег (с мячом медленнее), A держать: зарядка удара,
## отпустить: удар, короткое нажатие пас (сразу после удара стрелка поперёк подкручивает мяч),
## B подкат. Матч до трёх голов.
## План соперника из `SoccerPlanGen` по сиду записи, правила и боты в `SoccerSim` (без окна, им же
## проверяются сиды); демка шагает им ровно 60 раз в секунду, рисует и озвучивает события.
##
## Баги по флагам записи (параметры в `resources/bugs/<id>.tres`). Общие (#44) и баг технологии
## `layer_tear` (разрывы кадра) живут в `Demo` и `Bit16Screen`. Свои проявления: `wild_physics`
## мяч скачет, как резиновый; `unreachable_coins` ворота соперника вдвое уже; `sneeze_enemies`
## соперник падает от любого касания; `ball_to_space` мяч раз в несколько секунд взмывает и
## улетает за поле.

const ZOOM := 3
const MARGIN := 48.0
const FRAME := 24.0
## Кадров на направление в ленте игрока (стойка и четыре кадра бега), дальше подкаты и лежащие.
const RUN_FRAMES := 5
## Сетка ворот уходит за линию на столько пикселей; мяч после гола докатывается в неё.
const NET_DEPTH := 18.0
const PLACEHOLDER_SLOTS: Array[String] = ["rival", "ball"]
const KITS: Array[String] = ["soccer_rival_0", "soccer_rival_1", "soccer_rival_2"]
## Песок (или трава, реголит) за линиями до аута.
const APRON := 26.0
## Поле и аут по сеттингу (плейтест 2026-11-12): тайлы `soccer_field_<сеттинг>` и
## `soccer_out_<сеттинг>` (4 кадра), кромка поля: внутренняя тень и линия у аута (у пиратов
## мокрый песок и пена прибоя).
## Сеттинг без своей пары: мягкая тень и светлая линия, читаются на любом поле.
const EDGE_DEFAULT := [Color(0.0, 0.0, 0.0, 0.32), Color("#f4fbff")]
const EDGE := {"pirates": [Color(0.42, 0.3, 0.16, 0.45), Color("#f4fbff")],
		"castles": [Color(0.0, 0.0, 0.0, 0.3), Color("#a8a2ac")],
		"space": [Color(0.0, 0.0, 0.0, 0.35), Color("#7fd8ff")]}
## Цвета формы соперника для табло (как ленты `soccer_rival_*`) и HUD в духе битемапа.
const BRASS: Array[Color] = [Color("#3a240c"), Color("#8a5a1c"), Color("#d8a440"), Color("#fff0a0")]
const INK := Color("#1a1218")
const MELODY := [0, 4, 7, 4, 9, 7, 4, 2, 0, 4, 7, 12, 11, 7, 9, null,
	5, 9, 12, 9, 14, 12, 9, 7, 5, 4, 2, 4, 7, null, 0, null]
const BASS := [-12, -12, -5, -5, -7, -7, -8, -8, -12, -12, -5, -5, -7, -7, -10, -10]

var tuning: SportBit16Tuning
var plan: SoccerPlan
var sim: SoccerSim
var tex := {}
var cam := Vector2.ZERO

var _time := 0.0
var _acc := 0.0
var _slide_pressed := false
var _goal_t := 9.0
## Мяч в сетке после гола: откуда и куда он докатывается, пока матч стоит.
var _net_from := Vector3.ZERO
var _net_to := Vector2.ZERO
var _theme := "pirates"
var _music: AudioStreamPlayer
var _sfx := {}


func _on_start() -> void:
	tuning = SportBit16Tuning.load_default()
	plan = SoccerPlanGen.generate(record.seed if record != null else 1)
	sim = SoccerSim.create(plan, tuning)
	if has_bug(&"wild_physics"):
		sim.bounce_mult = bug_param(&"wild_physics", &"soccer_bounce_mult", 1.9)
	if has_bug(&"unreachable_coins"):
		sim.goal_mult = bug_param(&"unreachable_coins", &"soccer_goal_mult", 0.5)
	sim.sneeze = has_bug(&"sneeze_enemies")
	if has_bug(&"ball_to_space"):
		sim.space_every = bug_param(&"ball_to_space", &"soccer_space_s", 9.0)
	bit16_screen(Callable(), _draw_world, _draw_hud, ZOOM)
	bit16.world.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	for name in ["soccer_hero", "soccer_keeper_hero", "soccer_keeper_rival", "soccer_ball", "soccer_grass"]:
		tex[name] = bit16_set.sprite16(name)
	_theme = String(bit16_set.id)
	tex["field"] = bit16_set.sprite16("soccer_field_" + _theme)
	tex["out"] = bit16_set.sprite16("soccer_out_" + _theme)
	tex["rival"] = bit16_set.sprite16(KITS[plan.rival_kit % KITS.size()])
	cam = _cam_target()
	_setup_audio()


func _setup_audio() -> void:
	_music = Sfx.music(Sfx.tracker_loop(MELODY, BASS, 132.0), tuning.music_db if not embedded else -80.0)
	add_child(_music)
	bug_music = _music
	if not embedded:
		_music.play()
	# Свои звуки футбола (плейтест 2026-11-15, #132): свисток, удар по мячу, сетка, трибуны.
	_sfx["kick"] = Sfx.player(Sfx.ball_kick(1.0))
	_sfx["bounce"] = Sfx.player(Sfx.ball_kick(0.0, 0.22))
	_sfx["tackle"] = Sfx.player(Sfx.scrape())
	_sfx["save"] = Sfx.player(Sfx.glove())
	_sfx["net"] = Sfx.player(Sfx.net())
	_sfx["goal"] = Sfx.player(Sfx.whistle(0.7))
	_sfx["cheer"] = Sfx.player(Sfx.cheer())
	_sfx["out"] = Sfx.player(Sfx.whistle(0.22, 0.24))
	_sfx["start"] = Sfx.player(Sfx.whistle(0.4))
	_sfx["space"] = Sfx.player(Sfx.beep(440.0, 0.6, 0.3, 1760.0))
	_sfx["finish"] = Sfx.player(Sfx.whistles())
	for p in _sfx.values():
		(p as AudioStreamPlayer).volume_db = tuning.sfx_db if not embedded else -80.0
		add_child(p)
	if not embedded:
		_play("start")


func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _play(name: String) -> void:
	bug_play(_sfx[name])


func _on_end(goal: bool) -> void:
	_music.stop()
	_play("finish")
	if AutoTest.enabled and not embedded:
		AutoTest.note("sport bit16: %s %d:%d за %.1f с, ударов %d" % ["победа" if goal else "поражение",
				sim.score[0], sim.score[1], elapsed, sim.kicks])


func _result_caption() -> String:
	return "счёт %d:%d · %d с" % [sim.score[0], sim.score[1], int(round(elapsed))]


# --- Ввод и шаг ------------------------------------------------------------------------------

func _game_input(event: InputEvent) -> void:
	if GameInput.is_b(event):
		bug_press(func() -> void: _slide_pressed = true)
		get_viewport().set_input_as_handled()


## Бот ходит внутри шагов мира (`_step`), ровно как в прогоне без окна.
func _bot_step(_delta: float) -> void:
	pass


func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	bug_frame(delta, true, _step)


func _step(dt: float) -> void:
	_time += dt
	_goal_t += dt
	bug_input_tick()
	_acc = minf(_acc + dt, 0.25)
	while _acc >= SoccerSim.DT - 0.0001 and not sim.ended:
		_acc -= SoccerSim.DT
		var axis := Vector2.ZERO
		var kick := false
		var slide := _slide_pressed
		if bot_driven():
			axis = sim.bot(active_bot_mode())
			kick = sim.bot_kick
			slide = slide or sim.bot_slide
		else:
			axis = GameInput.axis()
			kick = GameInput.a_pressed()
		_slide_pressed = false
		sim.step(bug_axis(axis), kick, slide)
		for ev in sim.events:
			_on_event(ev)
		sim.events.clear()
	cam = cam.lerp(_cam_target(), minf(dt * 5.0, 1.0))


func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"kick", &"bounce", &"save", &"out", &"space":
			_play(String(ev[0]))
		&"tackle":
			_play("save")
		&"slide":
			_play("tackle")
		&"goal":
			_goal_t = 0.0
			# Мяч докатывается в сетку: по ходу полёта, но не дальше её задней стенки и боков.
			var side := -1.0 if sim.ball.x < tuning.pitch_w * 0.5 else 1.0
			var hg := sim.half_goal(SoccerSim.HERO if side < 0.0 else SoccerSim.RIVAL)
			var flight := Vector2(sim.ball_vel.x, sim.ball_vel.y)
			var slope := flight.y / maxf(absf(flight.x), 1.0)
			_net_from = sim.ball
			_net_to = Vector2((0.0 if side < 0.0 else tuning.pitch_w) + side * (NET_DEPTH - 5.0),
					clampf(sim.ball.y + slope * (NET_DEPTH - 5.0), tuning.pitch_h * 0.5 - hg + 5.0, tuning.pitch_h * 0.5 + hg - 5.0))
			_play("net")
			# Свисток чуть позже сетки; трибуны радуются только голу героя.
			get_tree().create_timer(0.25).timeout.connect(func() -> void: _play("goal"))
			if ev[1] == SoccerSim.HERO:
				_play("cheer")
			if AutoTest.enabled and not embedded:
				AutoTest.note("sport bit16: гол %s на %.1f с, счёт %d:%d" % ["героя" if ev[1] == SoccerSim.HERO else "соперника",
						elapsed, sim.score[0], sim.score[1]])
		&"win":
			end_demo(true)
		&"lose":
			end_demo(false)


## Камера за мячом, не дальше края поля с полями вокруг.
func _cam_target() -> Vector2:
	var view := bit16.view
	var want := Vector2(sim.ball.x, sim.ball.y) - view * 0.5
	return want.clamp(Vector2(-MARGIN, -MARGIN), Vector2(tuning.pitch_w + MARGIN, tuning.pitch_h + MARGIN) - view)


# --- Рисование ---------------------------------------------------------------------------------

func _to_screen(p: Vector2) -> Vector2:
	return (p - cam).round()


func _draw_world(canvas: CanvasItem) -> void:
	_draw_pitch(canvas)
	# Игроки по y: кто ниже, тот ближе.
	var order := [0, 1, 2, 3, 4, 5]
	order.sort_custom(func(a: int, b: int) -> bool: return sim.players[a].pos.y < sim.players[b].pos.y)
	var shadow := Color(0.0, 0.0, 0.0, 0.3)
	# После гола матч стоит, а мяч докатывается в сетку и опускается.
	var ball := sim.ball
	if sim.pause > 0.0 or (sim.ended and _goal_t < 3.0):
		var k := 1.0 - pow(1.0 - clampf(_goal_t / 0.35, 0.0, 1.0), 2.0)
		ball = Vector3(lerpf(_net_from.x, _net_to.x, k), lerpf(_net_from.y, _net_to.y, k), _net_from.z * (1.0 - k))
	canvas.draw_rect(Rect2(_to_screen(Vector2(ball.x, ball.y)) - Vector2(3.0, 1.0), Vector2(6.0, 3.0)), shadow)
	for i in order:
		var foot := _to_screen(sim.players[i].pos)
		canvas.draw_rect(Rect2(foot - Vector2(5.0, 1.0), Vector2(10.0, 3.0)), shadow)
		canvas.draw_rect(Rect2(foot - Vector2(3.0, 2.0), Vector2(6.0, 5.0)), shadow)
	for i in order:
		_draw_player(canvas, i)
	var lift := ball.z
	var bp := _to_screen(Vector2(ball.x, ball.y - lift))
	var bt: Texture2D = tex["soccer_ball"]
	if is_pink("ball"):
		canvas.draw_rect(Rect2(bp - Vector2(4.0, 4.0), Vector2(8.0, 8.0)), Color(1.0, 0.4, 0.8))
	else:
		var size := 8.0 + clampf(lift / 30.0, 0.0, 4.0)
		var frame := int(sim.time * 10.0) % 2 if Vector2(sim.ball_vel.x, sim.ball_vel.y).length() > 5.0 else 0
		canvas.draw_texture_rect_region(bt, Rect2(bp - Vector2(size, size) * 0.5, Vector2(size, size)), Rect2(frame * 8.0, 0.0, 8.0, 8.0))
	# Ворота поверх мяча (плейтест 2026-11-15): влетевший мяч виден за сеткой.
	_draw_goal(canvas, 0.0, -1.0, SoccerSim.HERO)
	_draw_goal(canvas, tuning.pitch_w, 1.0, SoccerSim.RIVAL)


## Поле по сеттингу: аут тайлами (у пиратов море с барашками), поле с запасом за линиями
## (песок), на кромке тень внутрь и линия прибоя наружу; разметка белым.
func _draw_pitch(canvas: CanvasItem) -> void:
	var view := bit16.view
	var w := tuning.pitch_w
	var h := tuning.pitch_h
	var out: Texture2D = tex["out"]
	var field: Texture2D = tex["field"]
	if out == null or field == null:
		var grass: Texture2D = tex["soccer_grass"]
		var o := -Vector2(fposmod(cam.x, 64.0), fposmod(cam.y, 64.0))
		canvas.draw_texture_rect(grass, Rect2(o.round(), view + Vector2(128.0, 128.0)), true)
	else:
		# Аут: кадр тайла по времени, плитка привязана к миру.
		var fr := int(_time * 3.0) % 4
		var ox := -fposmod(roundf(cam.x), 64.0)
		var oy := -fposmod(roundf(cam.y), 64.0)
		var y := oy
		while y < view.y:
			var x := ox
			while x < view.x:
				canvas.draw_texture_rect_region(out, Rect2(x, y, 64.0, 64.0), Rect2(fr * 64.0, 0.0, 64.0, 64.0))
				x += 64.0
			y += 64.0
		# Поле с запасом за линиями: тайл по координатам мира (повтор текстуры включён).
		var a := Vector2(-APRON, -APRON)
		var rect := Rect2(_to_screen(a), Vector2(w, h) + Vector2(APRON, APRON) * 2.0)
		canvas.draw_texture_rect_region(field, rect, Rect2(a + Vector2(1024.0, 1024.0), rect.size))
		var edge: Array = EDGE.get(_theme, EDGE_DEFAULT)
		var shade: Color = edge[0]
		canvas.draw_rect(Rect2(rect.position, Vector2(rect.size.x, 3.0)), shade)
		canvas.draw_rect(Rect2(rect.position, Vector2(3.0, rect.size.y)), shade)
		canvas.draw_rect(Rect2(rect.position.x, rect.end.y - 3.0, rect.size.x, 3.0), Color(shade, shade.a * 0.6))
		canvas.draw_rect(Rect2(rect.end.x - 3.0, rect.position.y, 3.0, rect.size.y), Color(shade, shade.a * 0.6))
		# Линия у аута: у пиратов пена прибоя пунктиром, бежит по времени.
		var foam: Color = edge[1]
		var step := 6.0
		var shift := fmod(_time * 8.0, step * 2.0)
		var k := -step * 2.0 + shift
		while k < rect.size.x + step:
			canvas.draw_rect(Rect2(rect.position.x + k, rect.position.y - 2.0, step, 2.0), foam)
			canvas.draw_rect(Rect2(rect.position.x + rect.size.x - k - step, rect.end.y, step, 2.0), foam)
			k += step * 2.0
		k = -step * 2.0 + shift
		while k < rect.size.y + step:
			canvas.draw_rect(Rect2(rect.position.x - 2.0, rect.position.y + rect.size.y - k - step, 2.0, step), foam)
			canvas.draw_rect(Rect2(rect.end.x, rect.position.y + k, 2.0, step), foam)
			k += step * 2.0
	var tl := _to_screen(Vector2.ZERO)
	var br := _to_screen(Vector2(w, h))
	var white := Color(1.0, 1.0, 1.0, 0.9)
	canvas.draw_rect(Rect2(tl, br - tl), white, false, 2.0)
	var mx := _to_screen(Vector2(w * 0.5, 0.0)).x
	canvas.draw_rect(Rect2(mx - 1.0, tl.y, 2.0, br.y - tl.y), white)
	canvas.draw_arc(_to_screen(Vector2(w * 0.5, h * 0.5)), roundf(h * 0.11), 0.0, TAU, 40, white, 2.0)
	canvas.draw_rect(Rect2(_to_screen(Vector2(w * 0.5, h * 0.5)) - Vector2(2.0, 2.0), Vector2(4.0, 4.0)), white)
	for side in [0.0, 1.0]:
		var x0 := 0.0 if side == 0.0 else w - tuning.box_w
		var box := Rect2(_to_screen(Vector2(x0, (h - tuning.box_h) * 0.5)), Vector2(tuning.box_w, tuning.box_h))
		canvas.draw_rect(box, white, false, 2.0)
		var sw := roundf(tuning.box_w / 3.0)
		var sh := roundf(tuning.box_h * 0.47)
		var small := Rect2(_to_screen(Vector2(0.0 if side == 0.0 else w - sw, (h - sh) * 0.5)), Vector2(sw, sh))
		canvas.draw_rect(small, white, false, 2.0)
		var spot := _to_screen(Vector2(tuning.box_w * 0.67 if side == 0.0 else w - tuning.box_w * 0.67, h * 0.5))
		canvas.draw_rect(Rect2(spot - Vector2(2.0, 2.0), Vector2(4.0, 4.0)), white)


## Ворота сверху: сетка за линией, штанги белым; ворота соперника с багом уже.
func _draw_goal(canvas: CanvasItem, x: float, out: float, team: int) -> void:
	var hg := sim.half_goal(team)
	var mid := tuning.pitch_h * 0.5
	var depth := NET_DEPTH
	var a := _to_screen(Vector2(x, mid - hg))
	var net := Rect2(Vector2(a.x if out > 0.0 else a.x - depth, a.y), Vector2(depth, hg * 2.0))
	canvas.draw_rect(net, Color(1.0, 1.0, 1.0, 0.25))
	var line := Color(1.0, 1.0, 1.0, 0.6)
	var k := 0.0
	while k <= depth:
		canvas.draw_line(Vector2(net.position.x + k, net.position.y), Vector2(net.position.x + k, net.end.y), line, 1.0)
		k += 4.0
	k = 0.0
	while k <= hg * 2.0:
		canvas.draw_line(Vector2(net.position.x, net.position.y + k), Vector2(net.end.x, net.position.y + k), line, 1.0)
		k += 4.0
	var white := bit16.ink(Bit16Screen.WHITE)
	canvas.draw_rect(Rect2(a - Vector2(2.0, 2.0), Vector2(4.0, 4.0)), white)
	canvas.draw_rect(Rect2(a + Vector2(-2.0, hg * 2.0 - 2.0), Vector2(4.0, 4.0)), white)


## Игрок: кадр по направлению взгляда и бегу; подкат, лежит; у героя полоска зарядки удара.
func _draw_player(canvas: CanvasItem, i: int) -> void:
	var p := sim.players[i]
	var t: Texture2D
	if p.keeper:
		t = tex["soccer_keeper_hero"] if p.team == SoccerSim.HERO else tex["soccer_keeper_rival"]
	else:
		t = tex["soccer_hero"] if p.team == SoccerSim.HERO else tex["rival"]
	var d := posmod(int(round(atan2(p.facing.y, p.facing.x) / (PI / 4.0))), 8)
	var frame := d * RUN_FRAMES
	if p.down > 0.0:
		frame = 8 * RUN_FRAMES + 8 + d
	elif p.slide > 0.0 or p.dive > 0.0:
		frame = 8 * RUN_FRAMES + (d if p.slide > 0.0 else (2 if p.dive_dir.y > 0.0 else 6))
	elif p.vel.length() > 5.0:
		# Четыре кадра бега; у каждого игрока свой сдвиг, чтобы не шагали в ногу.
		frame = d * RUN_FRAMES + 1 + int(_time * 11.0 + i * 1.7) % 4
	var at := _to_screen(p.pos) - Vector2(FRAME * 0.5, FRAME - 2.0)
	if p.team == SoccerSim.RIVAL and not p.keeper and is_pink("rival"):
		canvas.draw_rect(Rect2(at, Vector2(FRAME, FRAME)), Color(1.0, 0.4, 0.8))
	else:
		canvas.draw_texture_rect_region(t, Rect2(at, Vector2(FRAME, FRAME)), Rect2(frame * FRAME, 0.0, FRAME, FRAME))
	if i == sim.ctrl:
		# Метка того, кем управляешь: треугольник над головой; при зарядке полоска силы.
		# Треугольник попиксельно с чёрной обводкой в 1 пиксель (плейтест 2026-11-12), верхний ряд
		# светлее.
		var top := (at + Vector2(FRAME * 0.5, -4.0)).round()
		var cells: Array[Vector2] = []
		for row in 4:
			for dx in range(-(3 - row), 4 - row):
				cells.append(top + Vector2(dx, row - 3))
		for c in cells:
			for nb: Vector2 in [Vector2.ZERO, Vector2.LEFT, Vector2.RIGHT, Vector2.UP, Vector2.DOWN]:
				canvas.draw_rect(Rect2(c + nb, Vector2.ONE), bit16.ink(Bit16Screen.K))
		for c in cells:
			canvas.draw_rect(Rect2(c, Vector2.ONE), bit16.ink(Bit16Screen.WHITE if c.y == top.y - 3.0 else Bit16Screen.GOLD))
		if p.charge >= 0.0:
			var k := clampf(p.charge / tuning.charge_max, 0.0, 1.0)
			canvas.draw_rect(Rect2(at + Vector2(-2.0, -10.0), Vector2(FRAME + 4.0, 3.0)), bit16.ink(Bit16Screen.K))
			canvas.draw_rect(Rect2(at + Vector2(-2.0, -10.0), Vector2((FRAME + 4.0) * k, 3.0)), bit16.ink(Bit16Screen.RED))


# --- HUD -------------------------------------------------------------------------------------

## Табло в латунной рамке, как HUD битемапа: цвет формы, название, счёт пиксельным шрифтом с
## градиентом; после гола табло вспыхивает и над полем «ГОЛ!».
func _draw_hud(canvas: CanvasItem) -> void:
	var cx := roundf(bit16.view.x * 0.5)
	var flash := _goal_t < 1.2 and fmod(_goal_t, 0.3) < 0.15
	var box := Rect2(cx - 92.0, 6.0, 184.0, 26.0)
	_frame_box(canvas, box, flash)
	var rival_ink := bit16_set.tone(StringName("rival_ink_%d" % (plan.rival_kit % 3)))
	_chip(canvas, Vector2(box.position.x + 8.0, 13.0), bit16_set.tone(&"hero_ink"), bit16_set.tone(&"hero_stripe"))
	_chip(canvas, Vector2(box.end.x - 20.0, 13.0), rival_ink, rival_ink.darkened(0.35))
	PixelFont16.draw(canvas, Vector2(box.position.x + 26.0, 15.0), bit16_set.word(&"team"), Color.WHITE, Color("#b8c8e0"), INK, 1.0)
	PixelFont16.draw(canvas, Vector2(box.end.x - 26.0 - PixelFont16.width("ГОСТИ"), 15.0), "ГОСТИ", Color.WHITE,
			Color("#b8c8e0"), INK, 1.0)
	var score := "%d:%d" % [sim.score[0], sim.score[1]]
	var cell := 2.0
	PixelFont16.draw(canvas, Vector2(cx - roundf(PixelFont16.width(score, cell) * 0.5), 11.0), score, BRASS[3], BRASS[2],
			INK, cell)
	if _goal_t < 1.6:
		var big := 4.0
		var t := "ГОЛ!"
		var k := minf(_goal_t * 5.0, 1.0)
		var y := roundf(lerpf(-40.0, bit16.view.y * 0.35, k))
		PixelFont16.draw(canvas, Vector2(cx - roundf(PixelFont16.width(t, big) * 0.5), y), t, Color.WHITE, BRASS[2], INK, big)


## Квадрат цвета формы с полосой второго цвета и обводкой.
func _chip(canvas: CanvasItem, at: Vector2, a: Color, b: Color) -> void:
	canvas.draw_rect(Rect2(at - Vector2(1.0, 1.0), Vector2(14.0, 14.0)), INK)
	canvas.draw_rect(Rect2(at, Vector2(12.0, 12.0)), a)
	canvas.draw_rect(Rect2(at + Vector2(0.0, 4.0), Vector2(12.0, 2.0)), b)
	canvas.draw_rect(Rect2(at + Vector2(0.0, 8.0), Vector2(12.0, 2.0)), b)
	canvas.draw_rect(Rect2(at, Vector2(12.0, 1.0)), Color(1.0, 1.0, 1.0, 0.5))


## Латунная рамка с фаской и тёмной лункой (как в битемапе); при вспышке светлее.
func _frame_box(canvas: CanvasItem, r: Rect2, bright: bool) -> void:
	canvas.draw_rect(r.grow(1.0), INK)
	canvas.draw_rect(r, BRASS[2] if bright else BRASS[1])
	canvas.draw_rect(Rect2(r.position, Vector2(r.size.x, 1.0)), BRASS[3])
	canvas.draw_rect(Rect2(r.position, Vector2(1.0, r.size.y)), BRASS[3])
	canvas.draw_rect(Rect2(r.position.x, r.end.y - 1.0, r.size.x, 1.0), BRASS[0])
	canvas.draw_rect(Rect2(r.end.x - 1.0, r.position.y, 1.0, r.size.y), BRASS[0])
	canvas.draw_rect(r.grow(-2.0), INK)
	canvas.draw_rect(r.grow(-3.0), Color("#3a2a5a") if bright else Color("#140e1c"))


## Управление для плиток в паузе (`Demo._controls`).
func _controls() -> Array:
	return [["← → ↑ ↓", "бег"], [GameInput.key(GameInput.A), "пас, держать: удар"], [GameInput.key(GameInput.B), "подкат"]]
