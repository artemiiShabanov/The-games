extends Demo
## Демка гонки × 16/32-bit «псевдо-3D» (#99, решение 2026-11-12, `docs/specs/demos_catalog.md`):
## игра по мотивам Horizon Chase Turbo, графика по Outrun. Дорога сегментами уходит к
## горизонту, повороты выносят к обочине и сдвигают фон, холмы прячут дорогу за гребнем;
## соперники, пальмы, камни, бочки, знаки и хижины растут по мере приближения. Старт последним
## из двенадцати, цель: финиш в тройке. Влево, вправо руль, A газ, B нитро (три заряда).
## Старт по A: отсчёт 3, 2, 1, до него все стоят. Из-под колёс пыль, на повороте и обочине
## гуще; нитро это пламя сзади и полосы скорости; удар мигает повозкой и сыплет искрами (эффекты
## общие, от сеттинга не зависят).
## Трасса из `RoadTrackGen` по сиду записи, правила и боты в `RoadSim` (без окна, им же
## проверяются сиды); демка шагает им ровно 60 раз в секунду, рисует и озвучивает события.
##
## Баги по флагам записи (параметры в `resources/bugs/<id>.tres`). Общие (#44) и баг технологии
## `layer_tear` живут в `Demo`, `Bit16Screen` и `Parallax16`. Свои проявления: `wild_physics`
## (баг жанра) гололёд: повозку ведёт поперёк с запозданием, соперники быстрее;
## `unreachable_coins` «финиш на пляже»: нарисованная черта стоит на песке, а засчитывают
## невидимую дальше; `sneeze_enemies` соперник от касания крутится и уходит на обочину;
## `through_walls` пропы не держат и обочина не тормозит.

## Экран ×3 (554×277): повозка героя на его глубине пиксель в пиксель.
const ZOOM := 3
const BACKDROP: Array[String] = ["road_sky", "road_islands", "road_sea"]
const BACKDROP_FACTORS: Array[float] = [0.4, 0.8, 1.0]
const PROP_SPRITES: Array[String] = ["palm", "road_rock", "road_barrel", "sign_left", "sign_right", "road_hut"]
const PLACEHOLDER_SLOTS: Array[String] = ["rival", "palm", "coin", "sign"]
const MELODY := [0, null, 4, 7, 12, null, 11, 7, 9, null, 7, 4, 5, 7, 4, 2,
	0, null, 4, 7, 12, 14, 12, 11, 9, 7, 9, 11, 12, null, 7, null]
const BASS := [-12, -12, -5, -5, -7, -7, -3, -3, -10, -10, -5, -5, -7, -7, -5, -5]

var tuning: RacingBit16Tuning
var track: RoadTrack
var sim: RoadSim
var parallax: Parallax16
var tex := {}
var road_ink: Array[Color] = []
## Сдвиг фона на поворотах (пиксели ленты) и глубина камеры.
var bg_shift := 0.0
var depth := 0.84
## Мир на пиксель спрайта: у героя на его глубине пиксель спрайта равен пикселю экрана.
var px_world := 3.6

var _time := 0.0
var _acc := 0.0
var _nitro_pressed := false
var _music: AudioStreamPlayer
var _sfx := {}
var _bounce := 0.0
## Старт: 0 ждём A, 1 отсчёт, 2 гонка; секунды отсчёта и с начала гонки.
var _phase := 0
var _count_t := 0.0
var _go_t := 9.0
## Частицы на экране: пыль и искры. `[позиция, скорость, жизнь, размер, цвет]`.
var _parts: Array[Array] = []
var _dust_acc := 0.0
## Проекции сегментов на этот кадр: экранный x, y, полуширина дороги, масштаб, отсечка.
var _proj: Array[Vector4] = []
var _proj2: Array[Vector4] = []
var _clip := PackedFloat32Array()
## Номер сегмента k-го от камеры (без оборота: до старта отрицательный).
var _seg_no := PackedInt32Array()
## Пропы и монеты по сегментам: номер сегмента -> индексы, чтобы кадр не перебирал все.
var _props_at: Dictionary[int, PackedInt32Array] = {}
var _coins_at: Dictionary[int, PackedInt32Array] = {}


func _on_start() -> void:
	tuning = RacingBit16Tuning.load_default()
	track = RoadTrackGen.generate(record.seed if record != null else 1)
	sim = RoadSim.create(track, tuning)
	if has_bug(&"wild_physics"):
		sim.grip = bug_param(&"wild_physics", &"grip_mult", 0.25)
		sim.rival_mult = bug_param(&"wild_physics", &"road_rival_mult", 1.15)
	if has_bug(&"sneeze_enemies"):
		sim.sneeze = true
		sim.sneeze_seconds = bug_param(&"sneeze_enemies", &"off_track_s", 2.5)
		sim.sneeze_throttle = bug_param(&"sneeze_enemies", &"off_track_throttle", 0.5)
	sim.walls_open = has_bug(&"through_walls")
	if has_bug(&"unreachable_coins"):
		sim.finish_late = bug_param(&"unreachable_coins", &"road_finish_late", 150.0) * RoadTrack.SEG
	bit16_screen(_draw_backdrop, _draw_world, _draw_hud, ZOOM)
	var horizon := bit16.view.y * 0.5
	parallax = parallax16(BACKDROP, BACKDROP_FACTORS, [0.0, horizon - 62.0, horizon - 24.0])
	for name in PROP_SPRITES + ["cart_hero", "cart_0", "cart_1", "cart_2", "cart_3", "palm_b", "coin", "road_colors", "heart"]:
		tex[name] = bit16_set.sprite16(name)
	road_ink = _road_ink(tex["road_colors"])
	for k in track.props.size():
		var seg := int(track.props[k].x)
		if not _props_at.has(seg):
			_props_at[seg] = PackedInt32Array()
		_props_at[seg].append(k)
	for k in track.coins.size():
		var seg := track.seg_at(track.coins[k].y)
		if not _coins_at.has(seg):
			_coins_at[seg] = PackedInt32Array()
		_coins_at[seg].append(k)
	depth = 1.0 / tan(deg_to_rad(tuning.fov * 0.5))
	px_world = tuning.cam_height / (bit16.view.x * 0.5)
	# В стриме ленты гонка идёт сразу, без старта по кнопке.
	if embedded:
		_phase = 2
	_setup_audio()


## Цвета дороги из ленты сеттинга; без ленты серые.
static func _road_ink(t: Texture2D) -> Array[Color]:
	var out: Array[Color] = []
	var img := t.get_image() if t != null else null
	for i in 8:
		out.append(img.get_pixel(i, 0) if img != null and i < img.get_width() else Color(0.5, 0.5, 0.5))
	return out


func _setup_audio() -> void:
	_music = Sfx.music(Sfx.tracker_loop(MELODY, BASS, 140.0), tuning.music_db if not embedded else -80.0)
	add_child(_music)
	bug_music = _music
	if not embedded:
		_music.play()
	_sfx["nitro"] = Sfx.player(Sfx.whirr(0.6, 0.25))
	_sfx["bump"] = Sfx.player(Sfx.thud(0.1, 0.35))
	_sfx["crash"] = Sfx.player(Sfx.thud(0.25, 0.5))
	_sfx["coin"] = Sfx.player(Sfx.blip(1318.0, 0.1, 0.25, 16.0))
	_sfx["pass"] = Sfx.player(Sfx.blip(880.0, 0.08, 0.2, 20.0))
	_sfx["passed"] = Sfx.player(Sfx.blip(330.0, 0.1, 0.2, 20.0))
	_sfx["spin"] = Sfx.player(Sfx.beep(600.0, 0.3, 0.2, 200.0))
	_sfx["finish"] = Sfx.player(Sfx.blip(880.0, 0.5, 0.45, 5.0))
	_sfx["count"] = Sfx.player(Sfx.beep(440.0, 0.18, 0.3))
	_sfx["go"] = Sfx.player(Sfx.beep(880.0, 0.4, 0.35))
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
		AutoTest.note("racing bit16: %s, место %d из %d за %.1f с, ударов %d, аварий %d, нитро %d, монет %d из %d" % [
				"финиш в тройке" if goal else "провал", sim.place, sim.rivals.size() + 1, elapsed, sim.bumps, sim.crashes,
				tuning.nitros - sim.nitros, sim.coins_got, track.coins.size()])


func _result_caption() -> String:
	return "место %d из %d · монеты %d · %d с" % [sim.place, sim.rivals.size() + 1, sim.coins_got, int(round(elapsed))]


# --- Ввод и шаг ------------------------------------------------------------------------------

func _game_input(event: InputEvent) -> void:
	if GameInput.is_a(event) and _phase == 0:
		_start_countdown()
		get_viewport().set_input_as_handled()
	elif GameInput.is_b(event) and _phase == 2:
		bug_press(func() -> void: _nitro_pressed = true)
		get_viewport().set_input_as_handled()


## Бот ходит внутри шагов мира (`_step`), ровно как в прогоне без окна.
func _bot_step(_delta: float) -> void:
	pass


func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	bug_frame(delta, sim.speed > 1.0, _step)


func _start_countdown() -> void:
	_phase = 1
	_count_t = 0.0
	_play("count")


func _step(dt: float) -> void:
	_time += dt
	_go_t += dt
	bug_input_tick()
	_step_parts(dt)
	if _phase == 0:
		# Бот жмёт старт сам.
		if bot_driven() and _time > 0.4:
			_start_countdown()
		return
	if _phase == 1:
		var before := int(_count_t)
		_count_t += dt
		if _count_t >= tuning.countdown:
			_phase = 2
			_go_t = 0.0
			_play("go")
		elif int(_count_t) != before:
			_play("count")
		return
	_acc = minf(_acc + dt, 0.25)
	while _acc >= RoadSim.DT - 0.0001 and not sim.ended:
		_acc -= RoadSim.DT
		var raw := 0.0
		var gas := false
		var nitro := _nitro_pressed
		if bot_driven():
			raw = sim.bot(active_bot_mode())
			gas = sim.bot_gas
			nitro = nitro or sim.bot_nitro
		else:
			raw = GameInput.axis().x
			gas = GameInput.a_pressed()
		_nitro_pressed = false
		var seg := track.seg_at(sim.z)
		sim.step(bug_axis(Vector2(raw, 0.0)).x, gas, nitro)
		# Фон едет против поворота тем быстрее, чем выше скорость.
		bg_shift += track.curve[seg] * sim.speed * RoadSim.DT * tuning.backdrop_shift
		for ev in sim.events:
			_on_event(ev)
		sim.events.clear()
	_bounce = sin(_time * 30.0) * (1.0 if sim.speed > tuning.max_speed * 0.2 else 0.0)
	_spawn_dust(dt)


func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"nitro", &"bump", &"crash", &"coin", &"pass", &"passed", &"spin":
			_play(String(ev[0]))
			if ev[0] == &"bump" or ev[0] == &"crash":
				_sparks(ev[0] == &"crash")
		&"win":
			end_demo(true)
		&"lose":
			end_demo(false)


# --- Проекция ----------------------------------------------------------------------------------

## Камера за героем: позади него на высоте `cam_height`.
func _cam_z() -> float:
	return sim.z - tuning.cam_height * depth


## Проекция точки мира в экран: x, y, полуширина дороги, масштаб.
func _project(wx: float, wy: float, wz: float, cam: Vector3) -> Vector4:
	var cz := wz - cam.z
	var scale := depth / maxf(cz, 1.0)
	var half := bit16.view * 0.5
	return Vector4(roundf(half.x + scale * (wx - cam.x) * half.x), roundf(half.y - scale * (wy - cam.y) * half.y),
			roundf(scale * RoadTrack.ROAD_W * half.x), scale)


func _draw_backdrop(canvas: CanvasItem) -> void:
	parallax.draw(canvas, bit16.view, bg_shift, 0.0, bit16.palette)
	var horizon := bit16.view.y * 0.5
	canvas.draw_rect(Rect2(0.0, horizon, bit16.view.x, bit16.view.y - horizon), road_ink[5])


func _draw_world(canvas: CanvasItem) -> void:
	var view := bit16.view
	var n := tuning.draw_distance
	var cam_z := _cam_z()
	# Сегменты считаются от камеры по номеру без оборота: на старте камера стоит позади нулевого,
	# и сегменты до него это ровная прямая, а не конец трассы (иначе первые секунды один песок).
	var base_no := int(floor(cam_z / RoadTrack.SEG))
	var base_pct := (cam_z - base_no * RoadTrack.SEG) / RoadTrack.SEG
	var cam := Vector3(sim.x * RoadTrack.ROAD_W, track.height_at(maxf(sim.z, 0.0)) + tuning.cam_height, cam_z)
	var maxy := view.y
	var x := 0.0
	var dx := -_curve(base_no) * base_pct
	_proj.resize(n)
	_proj2.resize(n)
	_clip.resize(n)
	_seg_no.resize(n)
	for k in n:
		var no := base_no + k
		var p1 := _project(0.0, _y(no - 1), no * RoadTrack.SEG, Vector3(cam.x - x, cam.y, cam.z))
		var p2 := _project(0.0, _y(no), (no + 1) * RoadTrack.SEG, Vector3(cam.x - x - dx, cam.y, cam.z))
		x += dx
		dx += _curve(no)
		_proj[k] = p1
		_proj2[k] = p2
		_clip[k] = maxy
		_seg_no[k] = no
		if (no + 1) * RoadTrack.SEG - cam.z <= depth or p2.y >= p1.y or p2.y >= maxy:
			continue
		_draw_segment(canvas, posmod(no, track.count()), p1, p2)
		maxy = p2.y
	# Спрайты от дальних к ближним, обрезанные гребнем, который их закрывает.
	for k in range(n - 1, 0, -1):
		_draw_segment_sprites(canvas, k, _seg_no[k])
	_draw_hero(canvas)


## Изгиб и высота сегмента по номеру без оборота: до старта ровная прямая.
func _curve(no: int) -> float:
	return track.curve[no % track.count()] if no >= 0 else 0.0


func _y(no: int) -> float:
	return track.y[no % track.count()] if no >= 0 else 0.0


## Сегмент: обочина полосой на всю ширину, бордюр, дорога, разметка на светлых сегментах.
func _draw_segment(canvas: CanvasItem, i: int, p1: Vector4, p2: Vector4) -> void:
	var light := (i / tuning.band_len) % 2 == 0
	var w := bit16.view.x
	canvas.draw_rect(Rect2(0.0, p2.y, w, p1.y - p2.y), road_ink[5] if light else road_ink[6])
	var r1 := p1.z / 6.0
	var r2 := p2.z / 6.0
	_quad(canvas, p1.x - p1.z - r1, p1.y, p1.x - p1.z, p2.x - p2.z - r2, p2.y, p2.x - p2.z, road_ink[2] if light else road_ink[3])
	_quad(canvas, p1.x + p1.z + r1, p1.y, p1.x + p1.z, p2.x + p2.z + r2, p2.y, p2.x + p2.z, road_ink[2] if light else road_ink[3])
	_quad(canvas, p1.x - p1.z, p1.y, p1.x + p1.z, p2.x - p2.z, p2.y, p2.x + p2.z, road_ink[0] if light else road_ink[1])
	if i == track.finish:
		# Финишная черта шашкой (с багом «финиш на пляже» черта стоит на песке у обочины).
		var off := 2.6 * p1.z if sim.finish_late > 0.0 else 0.0
		for c in 8:
			var a := lerpf(p1.x - p1.z, p1.x + p1.z, c / 8.0) + off
			var b := lerpf(p1.x - p1.z, p1.x + p1.z, (c + 1) / 8.0) + off
			canvas.draw_rect(Rect2(a, p2.y, b - a, maxf(p1.y - p2.y, 1.0)), Color.WHITE if c % 2 == 0 else Color.BLACK)
	elif light:
		for lane: float in [-1.0 / 3.0, 1.0 / 3.0]:
			var lw1 := p1.z / 40.0
			var lw2 := p2.z / 40.0
			var c1 := p1.x + p1.z * lane
			var c2 := p2.x + p2.z * lane
			_quad(canvas, c1 - lw1, p1.y, c1 + lw1, c2 - lw2, p2.y, c2 + lw2, road_ink[4])


func _quad(canvas: CanvasItem, x1a: float, y1: float, x1b: float, x2a: float, y2: float, x2b: float, color: Color) -> void:
	canvas.draw_colored_polygon(PackedVector2Array([Vector2(x1a, y1), Vector2(x1b, y1), Vector2(x2b, y2), Vector2(x2a, y2)]), color)


## Пропы, монеты и соперники сегмента номер `no` (k-й от камеры).
func _draw_segment_sprites(canvas: CanvasItem, k: int, no: int) -> void:
	var p := _proj[k]
	var clip := _clip[k]
	if p.w <= 0.0 or no < 0:
		return
	var i := no % track.count()
	for idx in _props_at.get(i, PackedInt32Array()):
		var pr := track.props[idx]
		var kind := int(pr.z)
		var name := PROP_SPRITES[kind]
		if kind == RoadTrack.Prop.PALM and int(pr.x) % 2 == 1:
			name = "palm_b"
		_sprite(canvas, "sign" if kind == RoadTrack.Prop.SIGN_LEFT or kind == RoadTrack.Prop.SIGN_RIGHT else "palm",
				tex[name], 0, 1, p, pr.y, clip)
	for c in _coins_at.get(i, PackedInt32Array()):
		if sim.coin_taken[c] == 0:
			_sprite(canvas, "coin", tex["coin"], int(_time * 10.0) % 6, 6, p, track.coins[c].x, clip, 2.2)
	for r in sim.rivals:
		if int(floor(r.z / RoadTrack.SEG)) != no or r.z < sim.z - RoadTrack.SEG * 0.2:
			continue
		var lean := 1
		var seg_curve := track.curve[i]
		if seg_curve < -1.0:
			lean = 0
		elif seg_curve > 1.0:
			lean = 2
		var frame := lean * 2 + (int(_time * 12.0) % 2)
		var spin_x := sin(_time * 40.0) * 0.08 if r.spin > 0.0 else 0.0
		# Точное место внутри сегмента: между его ближним и дальним краем, иначе соперник
		# прыгает от сегмента к сегменту.
		var f := fposmod(r.z, RoadTrack.SEG) / RoadTrack.SEG
		var q := _proj[k].lerp(_proj2[k], f)
		_sprite(canvas, "rival", tex["cart_%d" % r.tint], frame, 6, q, r.x + spin_x, clip)


## Спрайт на дороге: низом в точке сегмента `p` со сдвигом поперёк `off_x` (полуширины),
## размер по масштабу сегмента; часть ниже отсечки `clip` (за гребнем) не рисуется.
func _sprite(canvas: CanvasItem, slot: String, t: Texture2D, frame: int, frames: int, p: Vector4, off_x: float,
		clip: float, size := 1.0, lift := 0.0) -> void:
	if t == null:
		return
	var fw := float(t.get_width()) / frames
	var fh := float(t.get_height())
	var k := p.w * bit16.view.x * 0.5 * px_world * size
	var w := fw * k
	var h := fh * k
	if w < 1.0 or h < 1.0:
		return
	var sx := p.x + p.w * off_x * RoadTrack.ROAD_W * bit16.view.x * 0.5
	var top := p.y - h - lift * k
	var visible := minf(h, clip - top)
	if visible <= 0.0:
		return
	var dst := Rect2(roundf(sx - w * 0.5), roundf(top), roundf(w), roundf(visible))
	if is_pink(slot):
		canvas.draw_rect(dst, Color(1.0, 0.4, 0.8))
		return
	canvas.draw_texture_rect_region(t, dst, Rect2(frame * fw, 0.0, fw, fh * visible / h))


## Повозка героя внизу по центру: крен по рулю и повороту, колёса крутятся, подпрыгивает на
## скорости. После удара мигает и трясётся; в нитро сзади пламя, по краям полосы скорости.
func _draw_hero(canvas: CanvasItem) -> void:
	var t: Texture2D = tex["cart_hero"]
	var lean := 1
	var seg := track.seg_at(maxf(sim.z, 0.0))
	var steer := sim.x_vel + track.curve[seg] * 0.3
	if steer < -0.4:
		lean = 0
	elif steer > 0.4:
		lean = 2
	var frame := lean * 2 + (int(sim.z / 300.0) % 2)
	var w := 160.0
	var h := float(t.get_height())
	var x := roundf(bit16.view.x * 0.5 - w * 0.5)
	var y := roundf(bit16.view.y - h - 4.0 + _bounce)
	if sim.hit > 0.0:
		x += roundf(sin(_time * 70.0) * 3.0 * sim.hit / tuning.hit_seconds)
	if sim.nitro_left > 0.0:
		x += roundf(sin(_time * 90.0))
		_draw_speed_lines(canvas)
	_draw_parts(canvas)
	if not (sim.hit > 0.0 and fmod(sim.hit, 0.14) < 0.07):
		canvas.draw_texture_rect_region(t, Rect2(x, y, w, h), Rect2(frame * w, 0.0, w, h))
	if sim.nitro_left > 0.0:
		_draw_flames(canvas, x + w * 0.5, y + h - 34.0)
	# Вспышка на включении нитро.
	var since := tuning.nitro_seconds - sim.nitro_left
	if sim.nitro_left > 0.0 and since < 0.25:
		canvas.draw_rect(Rect2(Vector2.ZERO, bit16.view), Color(1.0, 0.95, 0.7, 0.45 * (1.0 - since / 0.25)))


## Нитро: два языка пламени из-под короба к зрителю, поверх повозки (белое ядро, золото,
## красный край), дрожат.
func _draw_flames(canvas: CanvasItem, cx: float, cy: float) -> void:
	for side in [-1.0, 1.0]:
		var bx: float = cx + side * 34.0
		var flick := 1.0 + 0.3 * sin(_time * 55.0 + side * 2.0)
		for layer in 3:
			var len_: float = (46.0 - layer * 12.0) * flick
			var half: float = 13.0 - layer * 4.0
			var ink: Color = [bit16.ink(Bit16Screen.RED), bit16.ink(Bit16Screen.GOLD), bit16.ink(Bit16Screen.WHITE)][layer]
			canvas.draw_colored_polygon(PackedVector2Array([Vector2(bx - half, cy), Vector2(bx + half, cy),
					Vector2(bx + half * 0.4, cy + len_ * 0.6), Vector2(bx, cy + len_), Vector2(bx - half * 0.4, cy + len_ * 0.6)]), ink)


## Полосы скорости в нитро: белые штрихи от середины экрана к краям.
func _draw_speed_lines(canvas: CanvasItem) -> void:
	var mid := bit16.view * Vector2(0.5, 0.45)
	for k in 26:
		var a := float(k) / 26.0 * TAU + 0.13
		var d := fmod(_time * 1100.0 + k * 83.0, 300.0) + 70.0
		var dir := Vector2(cos(a) * 1.7, sin(a))
		var p0 := mid + dir * d
		canvas.draw_line(p0, p0 + dir * 40.0, Color(1.0, 1.0, 1.0, 0.85), 3.0)


## Пыль из-под колёс: на скорости понемногу, на повороте и на обочине гуще; на песке песочная.
func _spawn_dust(dt: float) -> void:
	var pct := sim.speed / tuning.max_speed
	if pct < 0.15:
		return
	var seg := track.seg_at(maxf(sim.z, 0.0))
	var turning := absf(sim.x_vel) > 0.6 or absf(track.curve[seg]) * pct > 2.0
	var off := absf(sim.x) > 1.0
	var rate := pct * 10.0 * (4.0 if turning else 1.0) * (3.0 if off else 1.0)
	_dust_acc += rate * dt
	var color := road_ink[6] if off else Color(0.85, 0.85, 0.88)
	while _dust_acc >= 1.0:
		_dust_acc -= 1.0
		for side in [-1.0, 1.0]:
			var p := Vector2(bit16.view.x * 0.5 + side * 58.0 + randf_range(-6.0, 6.0), bit16.view.y - 10.0)
			var v := Vector2(side * randf_range(10.0, 50.0) - sim.x_vel * 40.0, randf_range(-30.0, -5.0))
			_parts.append([p, v, randf_range(0.35, 0.7), randf_range(2.0, 4.0), color])


## Искры удара: жёлтые и белые, разлетаются от передка повозки; с аварией больше и с пылью.
func _sparks(big: bool) -> void:
	var at := Vector2(bit16.view.x * 0.5, bit16.view.y - 90.0)
	for k in (22 if big else 12):
		var a := randf_range(-PI, 0.0)
		var v := Vector2(cos(a), sin(a)) * randf_range(60.0, 180.0)
		var ink := bit16.ink(Bit16Screen.GOLD) if k % 2 == 0 else bit16.ink(Bit16Screen.WHITE)
		_parts.append([at + Vector2(randf_range(-40.0, 40.0), 0.0), v, randf_range(0.25, 0.5), 2.0, ink])


func _step_parts(dt: float) -> void:
	for k in range(_parts.size() - 1, -1, -1):
		var p: Array = _parts[k]
		p[2] = float(p[2]) - dt
		if float(p[2]) <= 0.0:
			_parts.remove_at(k)
			continue
		p[0] = (p[0] as Vector2) + (p[1] as Vector2) * dt
		p[1] = (p[1] as Vector2) * (1.0 - dt * 2.0) + Vector2(0.0, 60.0 * dt)
		p[3] = float(p[3]) + dt * 6.0


func _draw_parts(canvas: CanvasItem) -> void:
	for p in _parts:
		var c: Color = p[4]
		c.a = clampf(float(p[2]) * 2.0, 0.0, 1.0)
		var s := roundf(float(p[3]))
		var pos: Vector2 = (p[0] as Vector2).round()
		canvas.draw_rect(Rect2(pos - Vector2(s, s) * 0.5, Vector2(s, s)), c)


# --- HUD -------------------------------------------------------------------------------------

func _draw_hud(canvas: CanvasItem) -> void:
	var white := bit16.ink(Bit16Screen.WHITE)
	var black := bit16.ink(Bit16Screen.K)
	var gold := bit16.ink(Bit16Screen.GOLD)
	draw_pixel_text(canvas, Vector2(14.0, 10.0), "%d/%d" % [sim.place, sim.rivals.size() + 1],
			gold if sim.place <= 3 else white, black, 3.0)
	# Полоса пройденного пути.
	var k := clampf(sim.z / track.finish_z(), 0.0, 1.0)
	canvas.draw_rect(Rect2(14.0, 36.0, 120.0, 4.0), black)
	canvas.draw_rect(Rect2(14.0, 36.0, 120.0 * k, 4.0), gold)
	# Нитро: заряд это яркий жёлтый кружок, потраченный пустое кольцо.
	for n in tuning.nitros:
		var c := Vector2(bit16.view.x - 22.0 - (tuning.nitros - 1 - n) * 18.0, 18.0)
		canvas.draw_circle(c, 7.0, black)
		if n < sim.nitros:
			canvas.draw_circle(c, 5.5, gold)
			canvas.draw_rect(Rect2(c + Vector2(-2.0, -3.0), Vector2(2.0, 2.0)), white)
		else:
			canvas.draw_arc(c, 5.0, 0.0, TAU, 16, gold, 1.5)
			canvas.draw_circle(c, 3.5, black)
	# Монеты под нитро, по правому краю.
	var count := str(sim.coins_got)
	var tx := bit16.view.x - 14.0 - count.length() * 8.0
	draw_pixel_text(canvas, Vector2(tx, 34.0), count, white, black, 2.0)
	bit16.sprite(canvas, tex["coin"], 0, Vector2(tx - 12.0, 56.0))
	_draw_start(canvas)


## Старт: до нажатия мигает клавиша пробела, потом крупные 3, 2, 1, на старт зелёный круг со
## стрелкой.
func _draw_start(canvas: CanvasItem) -> void:
	var mid := bit16.view * Vector2(0.5, 0.36)
	var black := bit16.ink(Bit16Screen.K)
	if _phase == 0:
		if fmod(_time, 1.0) < 0.65:
			var r := Rect2(mid - Vector2(60.0, 14.0), Vector2(120.0, 28.0))
			canvas.draw_rect(r.grow(2.0), black)
			canvas.draw_rect(r, bit16.ink(Bit16Screen.WHITE))
			canvas.draw_rect(Rect2(r.position + Vector2(0.0, r.size.y - 4.0), Vector2(r.size.x, 4.0)), bit16.ink(Bit16Screen.GREY))
			canvas.draw_rect(Rect2(mid + Vector2(-26.0, 2.0), Vector2(52.0, 3.0)), black)
			canvas.draw_rect(Rect2(mid + Vector2(-26.0, -5.0), Vector2(3.0, 9.0)), black)
			canvas.draw_rect(Rect2(mid + Vector2(23.0, -5.0), Vector2(3.0, 9.0)), black)
		return
	if _phase == 1:
		var digit := str(int(tuning.countdown) - int(_count_t))
		var cell := 12.0
		draw_pixel_text(canvas, mid - Vector2(1.5 * cell, 2.5 * cell), digit, bit16.ink(Bit16Screen.GOLD), black, cell)
		return
	if _go_t < 0.8:
		canvas.draw_circle(mid, 30.0, black)
		canvas.draw_circle(mid, 27.0, bit16.ink(Bit16Screen.LEAF))
		canvas.draw_colored_polygon(PackedVector2Array([mid + Vector2(-9.0, -14.0), mid + Vector2(15.0, 0.0),
				mid + Vector2(-9.0, 14.0)]), bit16.ink(Bit16Screen.WHITE))
