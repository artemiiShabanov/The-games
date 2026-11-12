extends Demo
## Демка платформер × 16/32-bit «тропа» (#98, решение 2026-11-12, `docs/specs/demos_catalog.md`).
## Вид сбоку крупным планом, лес без неба в три слоя и листва над кадром спереди. Бег с
## инерцией по ровной земле и склонам, A прыжок, B (Ctrl) слайд: ниже ростом, под гору
## разгоняется, только так под аркой из корней. Над широкими ямами лианы: схватиться в прыжке,
## раскачаться стрелками, A отпустить. Краб и попугай угроза, убить их нельзя. Три жизни, после
## воды или удара продолжение с места возврата. Цель: флаг справа.
## Уровень из `TrailLevelGen` по сиду записи; правила и боты в `TrailSim` (без окна, им же
## проверяются сиды), демка шагает им ровно 60 раз в секунду, рисует и озвучивает события.
##
## Баги по флагам записи (параметры в `resources/bugs/<id>.tres`). Общие (#44) и баг технологии
## `layer_tear` живут в `Demo`, `Bit16Screen` и `Parallax16`, демка только зовёт хуки: фризы
## `bug_frame`, заикание трекера, стрелка и прыжок с опозданием, залипший прыжок (повторяется
## после приземления), розовые заглушки. Свои проявления: `wild_physics` (баг жанра) прыжок
## втрое выше и враги вдвое быстрее; `unreachable_coins` монеты висят выше любого прыжка;
## `sneeze_enemies` враг падает от касания.

## Крупный план: экран ×3 (554×277). Уровень рассчитан на эту высоту; экран ниже (стрим ленты)
## сдвигает мир и фон вверх, земля остаётся у низа.
const ZOOM := 3
const DESIGN_H := 277.0
const TILE := 32.0
const BACKDROP: Array[String] = ["par3_back", "par3_trees", "par3_bushes"]
const BACKDROP_FACTORS: Array[float] = [0.12, 0.35, 0.6]
const BACKDROP_TOPS: Array[float] = [0.0, 0.0, 128.0]
## Листва над кадром едет быстрее мира: она ближе к зрителю.
const CANOPY_FACTOR := 1.15
const PLACEHOLDER_SLOTS: Array[String] = ["crab", "parrot", "coin", "flag", "bush"]
const SPRITES: Array[String] = ["hero_run", "hero_idle", "hero_leap", "hero_slide", "hero_hang", "crab_walk",
		"parrot_fly", "heart", "coin", "flag", "trail_soil", "trail_edge", "arch_bark", "arch_root", "arch_lip",
		"dec_grass", "dec_tuft", "dec_fern", "dec_bush", "dec_rock", "dec_flowers", "dec_mush", "canopy_front"]
const DECOR_NAMES: Array[String] = ["dec_grass", "dec_tuft", "dec_bush", "dec_fern", "dec_rock", "dec_flowers", "dec_mush"]
const MELODY := [0, null, 3, 5, 7, null, 5, 3, 0, null, 3, 5, 7, 10, 7, null,
	-2, null, 2, 3, 5, null, 3, 2, -2, null, 2, 3, 5, 7, 5, null]
const BASS := [-12, -12, -12, -12, -9, -9, -9, -9, -14, -14, -14, -14, -10, -10, -7, -7]

var tuning: PlatformerBit16Tuning
var level: TrailLevel
var sim: TrailSim
var parallax: Parallax16
var tex := {}
var cam_x := 0.0
## Сдвиг мира по высоте под экран: 0 на полном, минус на низком.
var oy := 0.0

var _time := 0.0
var _acc := 0.0
var _jump_pressed := false
## Упавшие от чиха враги: индекс и секунды с падения.
var _foe_fall: Dictionary[int, float] = {}
## Брызги: место и секунды.
var _splash := Vector3(0.0, 0.0, 9.0)
var _music: AudioStreamPlayer
var _sfx := {}


func _on_start() -> void:
	tuning = PlatformerBit16Tuning.load_default()
	level = TrailLevelGen.generate(record.seed if record != null else 1)
	sim = TrailSim.create(level, tuning)
	# Баги жанра и баланса; общие баги в `Demo` (#44).
	if has_bug(&"wild_physics"):
		sim.jump_mult = maxf(bug_param(&"wild_physics", &"jump_mult", 3.0), 1.0)
		sim.enemy_mult = bug_param(&"wild_physics", &"enemy_speed_mult", 2.0)
	sim.coins_high = has_bug(&"unreachable_coins")
	sim.sneeze = has_bug(&"sneeze_enemies")
	bit16_screen(_draw_backdrop, _draw_world, _draw_hud, ZOOM)
	bit16.world.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	oy = minf(bit16.view.y - DESIGN_H, 0.0)
	parallax = parallax16(BACKDROP, BACKDROP_FACTORS, BACKDROP_TOPS)
	for name in SPRITES:
		tex[name] = bit16_set.sprite16(name)
	cam_x = _cam_target()
	_setup_audio()


func _setup_audio() -> void:
	_music = Sfx.music(Sfx.tracker_loop(MELODY, BASS, 126.0), tuning.music_db if not embedded else -80.0)
	add_child(_music)
	bug_music = _music
	if not embedded:
		_music.play()
	_sfx["jump"] = Sfx.player(Sfx.blip(520.0, 0.12, 0.3, 18.0))
	_sfx["land"] = Sfx.player(Sfx.thud(0.06, 0.25))
	_sfx["slide"] = Sfx.player(Sfx.hiss(0.25, 0.14))
	_sfx["grab"] = Sfx.player(Sfx.blip(330.0, 0.08, 0.25, 30.0))
	_sfx["release"] = Sfx.player(Sfx.blip(660.0, 0.1, 0.25, 22.0))
	_sfx["fall"] = Sfx.player(Sfx.bulp(0.3))
	_sfx["coin"] = Sfx.player(Sfx.blip(1318.0, 0.12, 0.3, 16.0))
	_sfx["hurt"] = Sfx.player(Sfx.blip(196.0, 0.35, 0.4, 7.0))
	_sfx["foe_down"] = Sfx.player(Sfx.blip(392.0, 0.2, 0.3, 12.0))
	_sfx["respawn"] = Sfx.player(Sfx.beep(440.0, 0.15, 0.2, 660.0))
	_sfx["finish"] = Sfx.player(Sfx.blip(880.0, 0.5, 0.45, 5.0))
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
		AutoTest.note("platformer bit16: %s за %.1f с, x %d из %d, жизней %d, монет %d из %d" % [
				"флаг" if goal else "провал", elapsed, int(sim.pos.x), int(level.flag_x), sim.lives, sim.coins_got,
				level.coins.size()])


func _result_caption() -> String:
	return "монеты %d из %d · потеряно жизней %d · %d с" % [sim.coins_got, level.coins.size(), sim.deaths, int(round(elapsed))]


# --- Ввод и шаг ------------------------------------------------------------------------------

func _game_input(event: InputEvent) -> void:
	if GameInput.is_a(event):
		# С багом управления нажатие уходит в очередь с задержкой (`Demo.bug_press`).
		bug_press(_press_jump)
		get_viewport().set_input_as_handled()


func _press_jump() -> void:
	_jump_pressed = true


## Бот ходит внутри шагов мира (`_step`), ровно как в прогоне без окна.
func _bot_step(_delta: float) -> void:
	pass


func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	# Фризы в движении с догоном времени (`Demo.bug_frame`).
	bug_frame(delta, sim.state != TrailSim.State.GROUND or absf(sim.vel.x) > 1.0, _step)


func _step(dt: float) -> void:
	_time += dt
	for i: int in _foe_fall.keys():
		_foe_fall[i] += dt
	_splash.z += dt
	bug_input_tick()
	_acc = minf(_acc + dt, 0.25)
	while _acc >= TrailSim.DT - 0.0001:
		_acc -= TrailSim.DT
		var raw := 0.0
		var jump := _jump_pressed
		var slide := false
		if bot_driven():
			raw = sim.bot(active_bot_mode())
			jump = jump or sim.bot_jump
			slide = sim.bot_slide
		else:
			raw = GameInput.axis().x
			slide = GameInput.b_pressed()
		_jump_pressed = false
		# Стрелка: с багом управления из прошлого на delay_ms (`Demo.bug_axis`).
		sim.step(bug_axis(Vector2(raw, 0.0)).x, jump, slide)
		for ev in sim.events:
			_on_event(ev)
		sim.events.clear()
		if ended_or_closing():
			break
	cam_x = lerpf(cam_x, _cam_target(), minf(dt * 6.0, 1.0))


func ended_or_closing() -> bool:
	return sim.ended


## Камера: герой на трети экрана, с упреждением по скорости.
func _cam_target() -> float:
	var want := sim.pos.x - bit16.view.x * 0.36 + clampf(sim.vel.x * 0.3, -60.0, 80.0)
	return clampf(want, 0.0, maxf(level.width - bit16.view.x, 0.0))


## Событие правил: звук, эффект, заметка автотеста, конец демки.
func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"jump":
			_play("jump")
			# Залипание: прыжок повторится после приземления (`Demo.bug_stick`).
			bug_stick()
		&"land":
			_play("land")
			if bug_take_stick():
				_jump_pressed = true
		&"slide", &"grab", &"release", &"coin", &"respawn":
			_play(String(ev[0]))
		&"fall":
			bug_clear_stick()
			_splash = Vector3(sim.pos.x, level.water_y, 0.0)
			_play("fall")
		&"hurt":
			bug_clear_stick()
			_play("hurt")
			if AutoTest.enabled and not embedded:
				AutoTest.note("platformer bit16: жизнь %d потеряна (%s) у x %d на %.1f с" % [sim.deaths, ev[1], int(sim.pos.x), elapsed])
		&"foe_down":
			_foe_fall[int(ev[1])] = 0.0
			_play("foe_down")
		&"win":
			end_demo(true)
		&"lose":
			end_demo(false)


# --- Рисование -------------------------------------------------------------------------------

func _cam() -> float:
	return roundf(cam_x)


func _sx(world_x: float) -> float:
	return roundf(world_x - _cam())


func _draw_backdrop(canvas: CanvasItem) -> void:
	canvas.draw_set_transform(Vector2(0.0, oy))
	parallax.draw(canvas, Vector2(bit16.view.x, bit16.view.y - oy), _cam(), 0.0, bit16.palette)


func _draw_world(canvas: CanvasItem) -> void:
	canvas.draw_set_transform(Vector2(0.0, oy))
	var view := bit16.view
	var lo := _cam() - 80.0
	var hi := _cam() + view.x + 80.0
	_draw_water(canvas, lo, hi)
	_draw_decor(canvas, lo, hi, false)
	_draw_ground(canvas, lo, hi)
	for a in level.arches:
		if a.to > lo and a.from < hi:
			_draw_arch(canvas, a)
	for i in level.vines.size():
		if absf(level.vines[i].anchor.x - _cam() - view.x * 0.5) < view.x:
			_draw_vine(canvas, i)
	var frame := int(_time * 10.0)
	for i in level.coins.size():
		var c := sim.coin_at(i)
		if sim.coin_taken[i] == 0 and c.x > lo and c.x < hi:
			draw_sprite16(canvas, "coin", tex["coin"], frame, Vector2(_sx(c.x), c.y + 12.0))
	draw_sprite16(canvas, "flag", tex["flag"], int(_time * 8.0), Vector2(_sx(level.flag_x), level.height_at(level.flag_x)))
	_draw_foes(canvas, lo, hi)
	_draw_hero(canvas)
	_draw_decor(canvas, lo, hi, true)
	_draw_canopy(canvas)


## Вода в ямах: тёмная гладь, светлая кромка, блики; брызги, когда герой упал.
func _draw_water(canvas: CanvasItem, lo: float, hi: float) -> void:
	for i in range(0, level.gaps.size(), 2):
		var a := level.gaps[i]
		var b := level.gaps[i + 1]
		if b < lo or a > hi:
			continue
		var x := _sx(a)
		var w := roundf(b - a)
		var y := level.water_y
		# Глубина ямы: темнота от земли до воды, сверху переход шашкой.
		var top := roundf(minf(level.height_at(a - 0.5), level.height_at(b + 0.5))) + 10.0
		canvas.draw_rect(Rect2(x, top, w, y - top), bit16.ink(Bit16Screen.K))
		for k in 3:
			for px in range(0, int(w), 2):
				canvas.draw_rect(Rect2(x + px + (k % 2), top - 2.0 - k * 2.0, 1.0, 1.0), bit16.ink(Bit16Screen.K))
		canvas.draw_rect(Rect2(x, y, w, bit16.view.y - oy - y), bit16.ink(Bit16Screen.NAVY))
		canvas.draw_rect(Rect2(x, y, w, 2.0), bit16.ink(Bit16Screen.SEA))
		for k in 3:
			var gx := fposmod(_time * 14.0 + k * 23.0 + a, maxf(w - 6.0, 1.0))
			canvas.draw_rect(Rect2(x + roundf(gx), y + 5.0 + k * 6.0, 5.0, 1.0), bit16.ink(Bit16Screen.SEA))
	if _splash.z < 0.5:
		var k := _splash.z / 0.5
		for d in [-1.0, 1.0]:
			for j in 3:
				var px: float = _sx(_splash.x) + float(d) * (3.0 + j * 4.0) * (0.5 + k)
				var py := _splash.y - roundf(sin(PI * k) * (14.0 - j * 3.0))
				canvas.draw_rect(Rect2(px, py, 2.0, 2.0), bit16.ink(Bit16Screen.AQUA))


## Земля: булыжный грунт многоугольником по каждому куску между ямами (текстура по
## координатам мира, повторяется), бока обрывов тёмные, кромка травы столбцами по поверхности.
func _draw_ground(canvas: CanvasItem, lo: float, hi: float) -> void:
	var soil: Texture2D = tex["trail_soil"]
	var edge: Texture2D = tex["trail_edge"]
	var bottom := bit16.view.y - oy
	var runs := PackedFloat32Array([0.0])
	runs.append_array(level.gaps)
	runs.append(level.width)
	for r in range(0, runs.size(), 2):
		var from := maxf(runs[r], lo)
		var to := minf(runs[r + 1], hi)
		if to <= from:
			continue
		var pts := PackedVector2Array([Vector2(_sx(from), bottom)])
		pts.append(Vector2(_sx(from), roundf(_h(from, runs[r], runs[r + 1]))))
		for p in level.points:
			if p.x > from and p.x < to:
				pts.append(Vector2(_sx(p.x), p.y))
		pts.append(Vector2(_sx(to), roundf(_h(to, runs[r], runs[r + 1]))))
		pts.append(Vector2(_sx(to), bottom))
		var uvs := PackedVector2Array()
		for p in pts:
			uvs.append(Vector2(p.x + _cam(), p.y) / TILE)
		if is_pink("bush"):
			canvas.draw_colored_polygon(pts, Color(1.0, 0.4, 0.8))
		else:
			canvas.draw_colored_polygon(pts, Color.WHITE, uvs, soil)
		# Бока обрывов у ям.
		for side in [[runs[r], 0.0], [runs[r + 1], -2.0]]:
			var ex: float = side[0]
			if ex > 0.0 and ex < level.width and ex >= lo and ex <= hi:
				var top := roundf(_h(ex, runs[r], runs[r + 1]))
				canvas.draw_rect(Rect2(_sx(ex) + float(side[1]), top + 6.0, 2.0, bottom - top), bit16.ink(Bit16Screen.K))
	# Кромка травы: столбец текстуры на каждый пиксель экрана, поверхность на строке 4.
	for sx in int(bit16.view.x):
		var wx := float(sx) + _cam()
		var h := level.height_at(wx)
		if h == INF:
			continue
		canvas.draw_texture_rect_region(edge, Rect2(sx, roundf(h) - 4.0, 1.0, edge.get_height()),
				Rect2(fposmod(wx, edge.get_width()), 0.0, 1.0, edge.get_height()))


## Высота у края куска земли: на самом краю ямы берётся точка чуть внутри.
func _h(x: float, from: float, to: float) -> float:
	return level.height_at(clampf(x, from + 0.01, to - 0.01))


## Украшения: за героем кусты, папоротники, камни, цветы, грибы; перед ним трава и кочки.
func _draw_decor(canvas: CanvasItem, lo: float, hi: float, front: bool) -> void:
	for d in level.decor:
		var is_front := d.y == TrailLevelGen.Decor.GRASS or d.y == TrailLevelGen.Decor.TUFT
		if is_front != front or d.x < lo or d.x > hi:
			continue
		var t: Texture2D = tex[DECOR_NAMES[d.y]]
		var h := level.height_at(d.x)
		if h == INF:
			continue
		var w := 32.0 if t.get_width() == 64 and is_front else float(t.get_width())
		var frame := int(_time * 1.5 + d.x * 0.01) % 2 if is_front else 0
		canvas.draw_texture_rect_region(t, Rect2(_sx(d.x) - roundf(w / 2.0), roundf(h) - t.get_height() + 1.0, w, t.get_height()),
				Rect2(frame * w, 0.0, w, t.get_height()))


## Арка: ствол корой от верха экрана до просвета, бахрома корней над просветом, корни по краям.
func _draw_arch(canvas: CanvasItem, a: TrailLevel.Arch) -> void:
	var ground := level.height_at(a.from)
	var ceil := ground - a.gap
	var x0 := _sx(a.from)
	var x1 := _sx(a.to)
	var pts := PackedVector2Array([Vector2(x0, -2.0), Vector2(x1, -2.0), Vector2(x1, ceil - 6.0), Vector2(x0, ceil - 6.0)])
	var uvs := PackedVector2Array()
	for p in pts:
		uvs.append(Vector2(p.x + _cam(), p.y) / TILE)
	canvas.draw_colored_polygon(pts, Color.WHITE, uvs, tex["arch_bark"])
	var lip: Texture2D = tex["arch_lip"]
	var x := x0
	while x < x1:
		var w := minf(32.0, x1 - x)
		canvas.draw_texture_rect_region(lip, Rect2(x, ceil - 8.0, w, lip.get_height()), Rect2(0.0, 0.0, w, lip.get_height()))
		x += 32.0
	var root: Texture2D = tex["arch_root"]
	canvas.draw_texture_rect_region(root, Rect2(x0 - 20.0, ground - 47.0, 32.0, 48.0), Rect2(0.0, 0.0, 32.0, 48.0))
	canvas.draw_texture_rect_region(root, Rect2(x1 - 12.0, ground - 47.0, 32.0, 48.0), Rect2(32.0, 0.0, 32.0, 48.0))


## Лиана: верёвка из листвы от подвеса; со схватившимся героем она натянута до рук и висит
## ниже, свободная чуть качается.
func _draw_vine(canvas: CanvasItem, i: int) -> void:
	var v := level.vines[i]
	var angle := sin(_time * 1.3 + i * 1.7) * 0.05
	if sim.state == TrailSim.State.VINE and sim.vine == i:
		angle = sim.vine_angle
	var dir := Vector2(sin(angle), cos(angle))
	var top := Vector2(_sx(v.anchor.x), v.anchor.y)
	var n := int(v.length / 3.0)
	for k in n:
		var p := (top + dir * k * 3.0).round()
		canvas.draw_rect(Rect2(p.x, p.y, 2.0, 3.0), bit16.ink(Bit16Screen.PINE if k % 3 else Bit16Screen.LEAF))
		if k % 4 == 1:
			var side := -3.0 if (k / 4) % 2 == 0 else 2.0
			canvas.draw_rect(Rect2(p.x + side, p.y + 1.0, 3.0, 2.0), bit16.ink(Bit16Screen.LEAF))


## Враги: краб боком по земле, попугай машет крыльями; упавший от чиха валится вниз.
func _draw_foes(canvas: CanvasItem, lo: float, hi: float) -> void:
	for i in level.foes.size():
		var f := sim.foe_at(i, sim.time)
		if f.x < lo or f.x > hi:
			continue
		var drop := 0.0
		if sim.foe_dead.has(i):
			var t := float(_foe_fall.get(i, 9.0))
			if t > 0.7:
				continue
			drop = t * t * 500.0
		var crab := level.foes[i].kind == TrailLevel.FoeKind.CRAB
		var feet := Vector2(_sx(f.x), roundf(f.y + (7.0 if crab else 14.0) + drop))
		if crab:
			draw_sprite16(canvas, "crab", tex["crab_walk"], int(_time * 10.0), feet)
		else:
			draw_sprite16(canvas, "parrot", tex["parrot_fly"], int(_time * 12.0), feet, f.z < 0.0)


## Герой по состоянию: стойка, бег (кадр от пройденного пути), прыжок, слайд, вис на лиане;
## в воде скрыт, после удара мигает.
func _draw_hero(canvas: CanvasItem) -> void:
	if sim.lives <= 0 or sim.state == TrailSim.State.DROWN:
		return
	if sim.invuln > 0.0 and fmod(sim.invuln, 0.16) < 0.08:
		return
	var feet := Vector2(_sx(sim.pos.x), roundf(sim.pos.y) + 1.0)
	var name := "hero_idle"
	var frame := int(_time * 2.0)
	match sim.state:
		TrailSim.State.GROUND:
			if absf(sim.vel.x) > 8.0:
				name = "hero_run"
				frame = int(sim.pos.x / 9.0)
		TrailSim.State.AIR, TrailSim.State.HURT:
			name = "hero_leap"
			frame = 1 if sim.vel.y < -120.0 else (2 if sim.vel.y < 120.0 else 3)
		TrailSim.State.SLIDE:
			name = "hero_slide"
			frame = int(_time * 10.0)
		TrailSim.State.VINE:
			name = "hero_hang"
			frame = 0 if sim.vine_speed >= 0.0 else 1
			feet.y += 9.0
	bit16.sprite(canvas, tex[name], frame, feet, sim.facing < 0)


## Листва над кадром спереди, едет чуть быстрее мира.
func _draw_canopy(canvas: CanvasItem) -> void:
	var t: Texture2D = tex["canopy_front"]
	var w := float(t.get_width())
	var x := -fposmod(roundf(_cam() * CANOPY_FACTOR), w)
	while x < bit16.view.x:
		canvas.draw_texture(t, Vector2(x, 0.0))
		x += w


## HUD: сердца по числу жизней и счёт монет.
func _draw_hud(canvas: CanvasItem) -> void:
	for i in sim.lives:
		bit16.sprite(canvas, tex["heart"], 0, Vector2(20.0 + i * 26.0, 34.0))
	var x := 20.0 + tuning.lives * 26.0 + 12.0
	bit16.sprite(canvas, tex["coin"], 0, Vector2(x, 34.0))
	draw_pixel_text(canvas, Vector2(x + 18.0, 12.0), str(sim.coins_got), bit16.ink(Bit16Screen.WHITE), bit16.ink(Bit16Screen.K), 2.0)
