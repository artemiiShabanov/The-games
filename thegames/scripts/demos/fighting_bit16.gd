extends Demo
## Демка файтинг × 16/32-bit «битемап» (#102, решение 2026-11-12, `docs/specs/demos_catalog.md`),
## графика по Streets of Rage 2: портовая улица с глубиной, идёшь вправо, экран встаёт, пока не
## побиты его враги, потом стрелка «вперёд». Враги группами по двое-трое, на третьем экране
## боцман. Стрелки ход в восьми направлениях, A удар (три подряд комбо, пинок валит), B прыжок
## (A в прыжке удар ногой); вплотную к врагу захват, A колено, третье A бросок. Полоски здоровья:
## героя с жизнями и того врага, кого бьёшь, с именем.
## Волны из `BrawlWavesGen` по сиду записи, правила и боты в `BrawlSim` (без окна, им же
## проверяются сиды); демка шагает им ровно 60 раз в секунду, рисует и озвучивает события.
##
## Баги по флагам записи (параметры в `resources/bugs/<id>.tres`). Общие (#44) и баг технологии
## `layer_tear` живут в `Demo`, `Bit16Screen` и `Parallax16`. Свои проявления: `wild_physics`
## палуба как на Луне: прыжок втрое выше, от удара бойцы летят по дуге; `unreachable_coins`
## боцман бессмертен; `sneeze_enemies` враг падает от любого удара; `ghost_hits` каждый второй
## удар героя проходит сквозь.

const ZOOM := 3
## Верх полосы, по которой ходят (глубина 0), на экране.
const FLOOR_TOP := 190.0
const FAR_FACTOR := 0.3
const PLACEHOLDER_SLOTS: Array[String] = ["thug", "knife", "boss"]
const HERO_FRAMES := {"idle0": 0, "idle1": 1, "walk0": 2, "jab0": 6, "jab1": 7, "kick": 8, "jump": 9, "jumpkick": 10,
		"hurt": 11, "down": 12, "grab": 13, "throw": 14}
const FOE_FRAMES := {"idle0": 0, "idle1": 1, "walk0": 2, "windup": 6, "strike": 7, "hurt": 8, "down": 9}
const MELODY := [0, null, 0, 3, 5, null, 3, 0, -2, null, 0, null, 3, 5, 7, null,
	0, null, 0, 3, 5, null, 7, 8, 7, null, 5, 3, 0, null, null, null]
const BASS := [-12, -12, -12, -9, -7, -7, -9, -12, -14, -14, -12, -12, -9, -9, -5, -5]

var tuning: FightingBit16Tuning
var waves: BrawlWaves
var sim: BrawlSim
var tex := {}

var _time := 0.0
var _acc := 0.0
var _a := false
var _b := false
var _throw_t := 9.0
## Враг, которого бьёшь (полоска с именем) и сколько ещё её показывать.
var _target: BrawlSim.Fighter
var _target_t := 0.0
## Искры ударов: место на экране мира и секунды.
var _sparks: Array[Vector3] = []
var _music: AudioStreamPlayer
var _sfx := {}


func _on_start() -> void:
	tuning = FightingBit16Tuning.load_default()
	waves = BrawlWavesGen.generate(record.seed if record != null else 1, tuning.depth)
	sim = BrawlSim.create(waves, tuning)
	if has_bug(&"wild_physics"):
		sim.jump_mult = maxf(bug_param(&"wild_physics", &"jump_mult", 3.0), 1.0)
		sim.launch = bug_param(&"wild_physics", &"fight_launch_speed", 120.0)
	sim.immortal = has_bug(&"unreachable_coins")
	sim.sneeze = has_bug(&"sneeze_enemies")
	if has_bug(&"ghost_hits"):
		sim.ghost_every = maxi(int(bug_param(&"ghost_hits", &"pass_every", 2.0)), 1)
	bit16_screen(_draw_backdrop, _draw_world, _draw_hud, ZOOM)
	for name in ["brawl_hero", "brawl_thug", "brawl_knife", "brawl_boss", "brawl_far", "brawl_facade", "brawl_floor"]:
		tex[name] = bit16_set.sprite16(name)
	_setup_audio()


func _setup_audio() -> void:
	_music = Sfx.music(Sfx.tracker_loop(MELODY, BASS, 116.0), tuning.music_db if not embedded else -80.0)
	add_child(_music)
	bug_music = _music
	if not embedded:
		_music.play()
	_sfx["swing"] = Sfx.player(Sfx.hiss(0.08, 0.12))
	_sfx["hit"] = Sfx.player(Sfx.thud(0.08, 0.45))
	_sfx["down"] = Sfx.player(Sfx.thud(0.2, 0.5))
	_sfx["kill"] = Sfx.player(Sfx.beep(220.0, 0.35, 0.3, 110.0))
	_sfx["hurt"] = Sfx.player(Sfx.blip(150.0, 0.2, 0.4, 10.0))
	_sfx["jump"] = Sfx.player(Sfx.blip(440.0, 0.1, 0.2, 20.0))
	_sfx["grab"] = Sfx.player(Sfx.blip(260.0, 0.06, 0.25, 30.0))
	_sfx["throw"] = Sfx.player(Sfx.hiss(0.3, 0.2))
	_sfx["go"] = Sfx.player(Sfx.beep(660.0, 0.3, 0.3, 990.0))
	_sfx["boss"] = Sfx.player(Sfx.beep(110.0, 0.6, 0.35, 90.0))
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
		AutoTest.note("fighting bit16: %s за %.1f с, экран %d, жизней %d, здоровье %d, побито %d" % [
				"победа" if goal else "поражение", elapsed, sim.screen + 1, sim.lives, sim.hero.hp, sim.kills])


func _result_caption() -> String:
	return "побито %d · жизней %d · %d с" % [sim.kills, sim.lives, int(round(elapsed))]


# --- Ввод и шаг ------------------------------------------------------------------------------

func _game_input(event: InputEvent) -> void:
	if GameInput.is_a(event):
		bug_press(func() -> void: _a = true)
		get_viewport().set_input_as_handled()
	elif GameInput.is_b(event):
		bug_press(func() -> void: _b = true)
		get_viewport().set_input_as_handled()


## Бот ходит внутри шагов мира (`_step`), ровно как в прогоне без окна.
func _bot_step(_delta: float) -> void:
	pass


func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	bug_frame(delta, true, _step)


func _step(dt: float) -> void:
	_time += dt
	_throw_t += dt
	_target_t = maxf(_target_t - dt, 0.0)
	for k in range(_sparks.size() - 1, -1, -1):
		_sparks[k].z += dt
		if _sparks[k].z > 0.25:
			_sparks.remove_at(k)
	bug_input_tick()
	_acc = minf(_acc + dt, 0.25)
	while _acc >= BrawlSim.DT - 0.0001 and not sim.ended:
		_acc -= BrawlSim.DT
		var axis := Vector2.ZERO
		var a := _a
		var b := _b
		if bot_driven():
			axis = sim.bot(active_bot_mode())
			a = a or sim.bot_a
			b = b or sim.bot_b
		else:
			axis = GameInput.axis()
		_a = false
		_b = false
		sim.step(bug_axis(axis), a, b)
		for ev in sim.events:
			_on_event(ev)
		sim.events.clear()


func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"swing", &"jump", &"grab", &"down", &"kill", &"go", &"boss":
			_play(String(ev[0]))
		&"hit":
			_play("hit")
			var i := int(ev[1])
			if i >= 0 and i < sim.foes.size():
				_target = sim.foes[i]
				_target_t = 2.0
				var f := _target
				_sparks.append(Vector3(f.pos.x - f.facing * 6.0, FLOOR_TOP + f.pos.y - 40.0 - f.z, 0.0))
		&"hurt":
			_play("hurt")
			_sparks.append(Vector3(sim.hero.pos.x, FLOOR_TOP + sim.hero.pos.y - 40.0 - sim.hero.z, 0.0))
		&"throw":
			_throw_t = 0.0
			_play("throw")
		&"life":
			if AutoTest.enabled and not embedded:
				AutoTest.note("fighting bit16: жизнь потеряна на %.1f с, экран %d" % [elapsed, sim.screen + 1])
		&"win":
			end_demo(true)
		&"lose":
			end_demo(false)


# --- Рисование ---------------------------------------------------------------------------------

func _sx(x: float) -> float:
	return roundf(x - sim.cam_x)


## Даль и фасады: даль едет медленнее, фасады вместе с улицей.
func _draw_backdrop(canvas: CanvasItem) -> void:
	var view := bit16.view
	canvas.draw_rect(Rect2(Vector2.ZERO, view), bit16.ink(Bit16Screen.SKY))
	_strip(canvas, tex["brawl_far"], sim.cam_x * FAR_FACTOR, 0.0)
	_strip(canvas, tex["brawl_facade"], sim.cam_x, FLOOR_TOP - 150.0)
	var fl: Texture2D = tex["brawl_floor"]
	var x := -fposmod(roundf(sim.cam_x), float(fl.get_width()))
	while x < view.x:
		canvas.draw_texture(fl, Vector2(x, FLOOR_TOP - 4.0))
		x += fl.get_width()
	canvas.draw_rect(Rect2(0.0, FLOOR_TOP - 4.0 + fl.get_height(), view.x, view.y), bit16.ink(Bit16Screen.BARK))


func _strip(canvas: CanvasItem, t: Texture2D, shift: float, y: float) -> void:
	if t == null:
		return
	var w := float(t.get_width())
	var x := -fposmod(roundf(shift), w)
	while x < bit16.view.x:
		canvas.draw_texture(t, Vector2(x, y))
		x += w


func _draw_world(canvas: CanvasItem) -> void:
	var all: Array[BrawlSim.Fighter] = [sim.hero]
	all.append_array(sim.foes)
	all.sort_custom(func(a: BrawlSim.Fighter, b: BrawlSim.Fighter) -> bool: return a.pos.y < b.pos.y)
	for f in all:
		canvas.draw_rect(Rect2(_sx(f.pos.x) - 12.0, FLOOR_TOP + f.pos.y - 3.0, 24.0, 5.0), Color(0.0, 0.0, 0.0, 0.3))
	for f in all:
		_draw_fighter(canvas, f)
	for s in _sparks:
		var c := Vector2(_sx(s.x), s.y)
		var r := 4.0 + s.z * 40.0
		for k in 8:
			var a := k * TAU / 8.0
			canvas.draw_line(c + Vector2(cos(a), sin(a)) * r * 0.4, c + Vector2(cos(a), sin(a)) * r, bit16.ink(Bit16Screen.GOLD if k % 2 else Bit16Screen.WHITE), 2.0)
	# Экран побит: стрелка «вперёд» справа мигает.
	if not sim.locked and sim.screen > 0 and not sim.ended and fmod(_time, 0.6) < 0.4:
		var p := Vector2(bit16.view.x - 60.0, 70.0)
		canvas.draw_colored_polygon(PackedVector2Array([p, p + Vector2(30.0, 0.0), p + Vector2(30.0, -10.0), p + Vector2(48.0, 8.0),
				p + Vector2(30.0, 26.0), p + Vector2(30.0, 16.0), p + Vector2(0.0, 16.0)]), bit16.ink(Bit16Screen.GOLD))


func _draw_fighter(canvas: CanvasItem, f: BrawlSim.Fighter) -> void:
	var hero := f.kind == BrawlWaves.Kind.HERO
	var name := "brawl_hero"
	var slot := ""
	match f.kind:
		BrawlWaves.Kind.THUG:
			name = "brawl_thug"
			slot = "thug"
		BrawlWaves.Kind.KNIFE:
			name = "brawl_knife"
			slot = "knife"
		BrawlWaves.Kind.BOSS:
			name = "brawl_boss"
			slot = "boss"
	var t: Texture2D = tex[name]
	var boss := f.kind == BrawlWaves.Kind.BOSS
	var fw := 64.0 if boss else 48.0
	var fh := 80.0 if boss else 64.0
	var key := "idle0" if int(_time * 2.0) % 2 == 0 else "idle1"
	var walk := 2 + int(absf(f.pos.x + f.pos.y) / 9.0) % 4
	var frame := -1
	match f.state:
		BrawlSim.State.WALK, BrawlSim.State.CHARGE:
			frame = walk if f.state == BrawlSim.State.WALK else 2 + int(_time * 16.0) % 4
		BrawlSim.State.ATTACK:
			key = ["jab0", "jab1", "kick"][clampi(f.combo, 0, 2)]
		BrawlSim.State.JUMP:
			key = "jumpkick" if f.combo >= 9 else "jump"
		BrawlSim.State.HURT, BrawlSim.State.GRABBED:
			key = "hurt"
		BrawlSim.State.DOWN, BrawlSim.State.DEAD, BrawlSim.State.THROWN:
			key = "down"
		BrawlSim.State.GRAB:
			key = "grab"
		BrawlSim.State.WINDUP:
			key = "windup"
		BrawlSim.State.STRIKE:
			key = "strike"
	if hero and f.state == BrawlSim.State.IDLE and _throw_t < 0.3:
		key = "throw"
	if frame < 0:
		frame = int(HERO_FRAMES.get(key, 0) if hero else FOE_FRAMES.get(key, 0))
	# Неуязвимость и смерть: мигает.
	if (f.invuln > 0.0 or f.state == BrawlSim.State.DEAD) and fmod(_time, 0.12) < 0.06:
		return
	var feet := Vector2(_sx(f.pos.x), FLOOR_TOP + f.pos.y - f.z)
	var dst := Rect2(roundf(feet.x - fw * 0.5), roundf(feet.y - fh + 2.0), fw, fh)
	if slot != "" and is_pink(slot):
		canvas.draw_rect(Rect2(dst.position + Vector2(fw * 0.25, 0.0), Vector2(fw * 0.5, fh)), Color(1.0, 0.4, 0.8))
		return
	if f.facing < 0.0:
		dst = Rect2(dst.position.x, dst.position.y, -fw, fh)
	canvas.draw_texture_rect_region(t, dst, Rect2(frame * fw, 0.0, fw, fh))


# --- HUD -------------------------------------------------------------------------------------

## Как в Streets of Rage 2: полоска героя с жизнями слева сверху, под ней полоска врага, которого
## бьёшь, с именем; у боцмана полоска всегда, пока он жив.
func _draw_hud(canvas: CanvasItem) -> void:
	var black := bit16.ink(Bit16Screen.K)
	var font := ThemeDB.fallback_font
	var show := _target if _target_t > 0.0 and _target != null and not _target.gone else null
	for f in sim.foes:
		if f.kind == BrawlWaves.Kind.BOSS and f.state != BrawlSim.State.DEAD:
			show = f
	# Тёмная плашка под HUD: подписи читаются на светлом небе.
	canvas.draw_rect(Rect2(6.0, 4.0, 150.0, 62.0 if show != null else 32.0), Color(0.05, 0.05, 0.1, 0.6))
	_bar(canvas, Vector2(12.0, 10.0), float(sim.hero.hp) / sim.hero.max_hp, bit16.ink(Bit16Screen.GOLD))
	canvas.draw_string(font, Vector2(12.0, 30.0), "МАТРОС", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, bit16.ink(Bit16Screen.WHITE))
	draw_pixel_text(canvas, Vector2(130.0, 8.0), str(sim.lives), bit16.ink(Bit16Screen.WHITE), black, 2.0)
	if show != null:
		_bar(canvas, Vector2(12.0, 38.0), float(show.hp) / show.max_hp, bit16.ink(Bit16Screen.RED))
		canvas.draw_string(font, Vector2(12.0, 58.0), show.name.to_upper(), HORIZONTAL_ALIGNMENT_LEFT, -1, 8, bit16.ink(Bit16Screen.WHITE))


func _bar(canvas: CanvasItem, at: Vector2, k: float, ink: Color) -> void:
	canvas.draw_rect(Rect2(at - Vector2(1.0, 1.0), Vector2(112.0, 10.0)), bit16.ink(Bit16Screen.K))
	canvas.draw_rect(Rect2(at, Vector2(110.0, 8.0)), bit16.ink(Bit16Screen.NAVY))
	canvas.draw_rect(Rect2(at, Vector2(110.0 * clampf(k, 0.0, 1.0), 8.0)), ink)
