extends Demo
## Демка файтинг × 16/32-bit «битемап» (#102, решение 2026-11-12, `docs/specs/demos_catalog.md`),
## графика по Streets of Rage 2: портовая улица (первые этажи домов, тротуар, мостовая), идёшь
## вправо, экран встаёт, пока не побиты его враги, потом стрелка «вперёд». Враги группами по
## двое-трое, на третьем экране боцман. Стрелки ход в восьми направлениях, A удар (три подряд
## комбо, пинок валит), B тяжёлый удар (долгий замах, валит всех перед собой); вплотную к врагу
## захват, A колено, третье A бросок. Каждое попадание: мир встаёт на доли секунды, того, по кому
## попали, заливает белым, искра и тряска (у тяжёлого ударная волна); взмахи видно серпом, падения
## поднимают пыль. HUD: лица в рамках, полоски с градиентом и «хвостом» урона, пиксельный шрифт.
## Волны из `BrawlWavesGen` по сиду записи, правила и боты в `BrawlSim` (без окна, им же
## проверяются сиды); демка шагает им ровно 60 раз в секунду, рисует и озвучивает события.
##
## Баги по флагам записи (параметры в `resources/bugs/<id>.tres`). Общие (#44) и баг технологии
## `layer_tear` живут в `Demo`, `Bit16Screen` и `Parallax16`. Свои проявления: `wild_physics`
## палуба как на Луне: от удара бойцы улетают высоко и далеко; `unreachable_coins` враги
## бессмертны (удар валит, полоска не убывает, экран не открывается); `sneeze_enemies` враг падает от любого удара; `ghost_hits` каждый второй удар
## героя проходит сквозь.

const ZOOM := 2
## Улица нарисована под экран 416 в высоту: на этой строке у неё верх полосы, по которой ходят.
const STREET_FLOOR := 262.0
## Ступни бойца стоят на столько выше низа кадра.
const FOOT := 4.0
const PLACEHOLDER_SLOTS: Array[String] = ["thug", "knife", "boss"]
## Первые кадры анимаций в лентах (как в `tools/pixel_brawl16.py`).
const HERO := {"idle": 0, "walk": 4, "jab": 12, "cross": 15, "kick": 18, "heavy": 22, "hurt": 27, "fall": 29,
		"down": 30, "getup": 31, "grab": 33, "knee": 34, "throw": 35}
const FOE := {"idle": 0, "walk": 4, "windup": 12, "strike": 14, "hurt": 16, "fall": 18, "down": 19, "getup": 20,
		"grabbed": 22, "charge": 23}
## Эффекты: лента, кадров, ширина кадра, кадров в секунду.
const FX := {"hit": ["brawl_fx_hit", 4, 40, 24.0], "heavy": ["brawl_fx_heavy", 5, 80, 20.0],
		"whoosh": ["brawl_fx_whoosh", 3, 64, 24.0], "dust": ["brawl_fx_dust", 5, 56, 14.0]}
## Белая заливка: модуляция с перебором, любой цвет спрайта уходит в белый.
const FLASH := Color(14.0, 14.0, 14.0)
## HUD: золото полоски героя, красная полоска врага, латунь рамок, тёмная лунка.
const GOLD_RAMP: Array[Color] = [Color("#7a3a10"), Color("#d0781c"), Color("#f8c040"), Color("#fff2a0")]
const RED_RAMP: Array[Color] = [Color("#5a1018"), Color("#a8242a"), Color("#e2483a"), Color("#ff9a78")]
const BRASS: Array[Color] = [Color("#3a240c"), Color("#8a5a1c"), Color("#d8a440"), Color("#fff0a0")]
const WELL := Color("#140e1c")
const INK := Color("#1a1218")
const MELODY := [0, null, 0, 3, 5, null, 3, 0, -2, null, 0, null, 3, 5, 7, null,
	0, null, 0, 3, 5, null, 7, 8, 7, null, 5, 3, 0, null, null, null]
const BASS := [-12, -12, -12, -9, -7, -7, -9, -12, -14, -14, -12, -12, -9, -9, -5, -5]

var tuning: FightingBit16Tuning
var waves: BrawlWaves
var sim: BrawlSim
var tex := {}

var _time := 0.0
## Часы анимации: стоят во время стоп-кадра.
var _anim := 0.0
var _acc := 0.0
var _a := false
var _b := false
var _throw_t := 9.0
var _knee_t := 9.0
## Враг, которого бьёшь (полоска с именем) и сколько ещё её показывать.
var _target: BrawlSim.Fighter
var _target_t := 0.0
## «Хвост» урона на полосках: доля здоровья, которая тает следом за настоящей.
var _hero_lag := 1.0
var _target_lag := 1.0
var _lag_wait := 0.0
## Фаза шага каждого бойца (пройденный путь) и прошлое положение.
var _walk := {}
var _last := {}
## Эффекты: [вид, x мира, y экрана, секунды, зеркало].
var _fx: Array[Array] = []
var _shake := 0.0
var _shake_power := 0.0
var _banner := ""
var _banner_t := 0.0
var _music: AudioStreamPlayer
var _sfx := {}


func _on_start() -> void:
	tuning = FightingBit16Tuning.load_default()
	waves = BrawlWavesGen.generate(record.seed if record != null else 1, tuning.depth)
	sim = BrawlSim.create(waves, tuning)
	if has_bug(&"wild_physics"):
		sim.launch = bug_param(&"wild_physics", &"fight_launch_speed", 180.0)
	sim.immortal = has_bug(&"unreachable_coins")
	sim.sneeze = has_bug(&"sneeze_enemies")
	if has_bug(&"ghost_hits"):
		sim.ghost_every = maxi(int(bug_param(&"ghost_hits", &"pass_every", 2.0)), 1)
	bit16_screen(_draw_backdrop, _draw_world, _draw_hud, ZOOM)
	for name in ["brawl_hero", "brawl_thug", "brawl_knife", "brawl_boss", "brawl_street", "brawl_go",
			"brawl_face_hero", "brawl_face_thug", "brawl_face_knife", "brawl_face_boss"]:
		tex[name] = bit16_set.sprite16(name)
	for k: String in FX:
		tex[FX[k][0]] = bit16_set.sprite16(FX[k][0])
	_setup_audio()


func _setup_audio() -> void:
	_music = Sfx.music(Sfx.tracker_loop(MELODY, BASS, 116.0), tuning.music_db if not embedded else -80.0)
	add_child(_music)
	bug_music = _music
	if not embedded:
		_music.play()
	_sfx["swing"] = Sfx.player(Sfx.hiss(0.08, 0.12))
	_sfx["hit"] = Sfx.player(Sfx.thud(0.08, 0.45))
	_sfx["heavy"] = Sfx.player(Sfx.thud(0.22, 0.6))
	_sfx["windup"] = Sfx.player(Sfx.blip(180.0, 0.18, 0.2, 40.0))
	_sfx["down"] = Sfx.player(Sfx.thud(0.2, 0.5))
	_sfx["kill"] = Sfx.player(Sfx.beep(220.0, 0.35, 0.3, 110.0))
	_sfx["hurt"] = Sfx.player(Sfx.blip(150.0, 0.2, 0.4, 10.0))
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
	_knee_t += dt
	_target_t = maxf(_target_t - dt, 0.0)
	_banner_t = maxf(_banner_t - dt, 0.0)
	_shake = maxf(_shake - dt, 0.0)
	if sim.hitstop <= 0.0:
		_anim += dt
		for k in range(_fx.size() - 1, -1, -1):
			_fx[k][3] = float(_fx[k][3]) + dt
			var spec: Array = FX[_fx[k][0]]
			if float(_fx[k][3]) * float(spec[3]) >= int(spec[1]):
				_fx.remove_at(k)
	_tick_lag(dt)
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
		# Во время стоп-кадра нажатие ждёт, пока мир не пойдёт снова.
		if sim.hitstop <= 0.0:
			_a = false
			_b = false
		sim.step(bug_axis(axis), a, b)
		for ev in sim.events:
			_on_event(ev)
		sim.events.clear()
		_track_feet()


## Хвост урона: стоит полсекунды после удара, потом тает к настоящему здоровью.
func _tick_lag(dt: float) -> void:
	_lag_wait = maxf(_lag_wait - dt, 0.0)
	var hero_k := float(sim.hero.hp) / sim.hero.max_hp
	var tk := float(_target.hp) / _target.max_hp if _target != null else 0.0
	_hero_lag = maxf(_hero_lag, hero_k)
	_target_lag = maxf(_target_lag, tk)
	if _lag_wait <= 0.0:
		_hero_lag = move_toward(_hero_lag, hero_k, dt * 0.8)
		_target_lag = move_toward(_target_lag, tk, dt * 0.8)


## Шаг бойцов (для кадров ходьбы) и пыль, когда упавший касается земли.
func _track_feet() -> void:
	var all: Array[BrawlSim.Fighter] = [sim.hero]
	all.append_array(sim.foes)
	for f in all:
		var now := Vector3(f.pos.x, f.pos.y, f.z)
		var was: Vector3 = _last.get(f, now)
		_walk[f] = float(_walk.get(f, 0.0)) + Vector2(now.x - was.x, now.y - was.y).length()
		if was.z > 2.0 and now.z <= 0.01 and f.state in [BrawlSim.State.DOWN, BrawlSim.State.DEAD, BrawlSim.State.THROWN]:
			_add_fx("dust", f.pos.x - f.facing * 14.0, _floor_y() + f.pos.y - 10.0, f.facing < 0.0)
			_kick(0.12, 2.0)
		_last[f] = now


func _add_fx(kind: String, x: float, y: float, flip := false) -> void:
	_fx.append([kind, x, y, 0.0, flip])


func _kick(seconds: float, power: float) -> void:
	_shake = maxf(_shake, seconds)
	_shake_power = maxf(power if _shake <= seconds else _shake_power, power)


func _fighter_of(who: int) -> BrawlSim.Fighter:
	if who < 0:
		return sim.hero
	return sim.foes[who] if who < sim.foes.size() else null


func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"grab", &"down", &"kill", &"go":
			_play(String(ev[0]))
		&"boss":
			_play("boss")
			_banner = "БОЦМАН"
			_banner_t = 2.2
		&"swing":
			_play("swing")
			var f := _fighter_of(int(ev[1]))
			if f != null:
				var heavy: bool = ev.size() > 2 and ev[2] == &"heavy"
				_add_fx("whoosh", f.pos.x + f.facing * (34.0 if heavy else 26.0), _floor_y() + f.pos.y - f.z - 66.0, f.facing < 0.0)
				if heavy:
					_add_fx("dust", f.pos.x - f.facing * 10.0, _floor_y() + f.pos.y - 10.0, f.facing < 0.0)
		&"windup":
			if int(ev[1]) < 0:
				_play("windup")
		&"impact":
			var heavy := bool(ev[4])
			var y := _floor_y() + float(ev[2]) - float(ev[3]) - 62.0
			_add_fx("hit", float(ev[1]), y)
			if heavy:
				_add_fx("heavy", float(ev[1]), y)
			_kick(0.18 if heavy else 0.1, 4.0 if heavy else 2.0)
			_lag_wait = 0.5
			_play("heavy" if heavy else "hit")
		&"hit":
			var i := int(ev[1])
			if i >= 0 and i < sim.foes.size():
				if _target != sim.foes[i]:
					_target_lag = 1.0
				_target = sim.foes[i]
				_target_t = 2.5
		&"hurt":
			_play("hurt")
		&"knee":
			_knee_t = 0.0
		&"throw":
			_throw_t = 0.0
			_play("throw")
		&"life":
			_banner = "ЕЩЁ РАЗ!"
			_banner_t = 1.4
			if AutoTest.enabled and not embedded:
				AutoTest.note("fighting bit16: жизнь потеряна на %.1f с, экран %d" % [elapsed, sim.screen + 1])
		&"win":
			end_demo(true)
		&"lose":
			end_demo(false)


# --- Рисование ---------------------------------------------------------------------------------

func _sx(x: float) -> float:
	return roundf(x - sim.cam_x)


## Верх полосы, по которой ходят, на экране: улица прижата к низу экрана.
func _floor_y() -> float:
	return bit16.view.y - 416.0 + STREET_FLOOR


func _shake_offset() -> Vector2:
	if _shake <= 0.0:
		return Vector2.ZERO
	var p := roundf(_shake_power * minf(_shake / 0.1, 1.0))
	return Vector2(p if int(_time * 60.0) % 2 == 0 else -p, (p * 0.5) if int(_time * 45.0) % 2 == 0 else 0.0).round()


## Улица: первые этажи, тротуар, мостовая одной лентой, едет вместе с камерой.
func _draw_backdrop(canvas: CanvasItem) -> void:
	var view := bit16.view
	canvas.draw_set_transform(_shake_offset())
	var t: Texture2D = tex["brawl_street"]
	var top := view.y - 416.0
	if top > 0.0:
		canvas.draw_rect(Rect2(-8.0, -8.0, view.x + 16.0, top + 8.0), Color("#5e4a3c"))
	if t == null:
		canvas.draw_rect(Rect2(Vector2.ZERO, view), Color("#33363f"))
		return
	var w := float(t.get_width())
	var x := -fposmod(roundf(sim.cam_x), w)
	while x < view.x + 8.0:
		canvas.draw_texture(t, Vector2(x, top))
		x += w


func _draw_world(canvas: CanvasItem) -> void:
	canvas.draw_set_transform(_shake_offset())
	var all: Array[BrawlSim.Fighter] = [sim.hero]
	all.append_array(sim.foes)
	all.sort_custom(func(a: BrawlSim.Fighter, b: BrawlSim.Fighter) -> bool: return a.pos.y < b.pos.y)
	var fy := _floor_y()
	for f in all:
		if f.gone:
			continue
		_shadow(canvas, Vector2(_sx(f.pos.x), fy + f.pos.y), (34.0 if f.kind == BrawlWaves.Kind.BOSS else 26.0) / (1.0 + f.z / 120.0))
	for f in all:
		if not f.gone:
			_draw_fighter(canvas, f)
	for e in _fx:
		var spec: Array = FX[e[0]]
		var t: Texture2D = tex[spec[0]]
		if t == null:
			continue
		var fw := float(spec[2])
		var fh := float(t.get_height())
		var frame := mini(int(float(e[3]) * float(spec[3])), int(spec[1]) - 1)
		var dst := Rect2(roundf(_sx(float(e[1])) - fw * 0.5), roundf(float(e[2]) - fh * 0.5), fw, fh)
		if e[4]:
			dst.size.x = -fw
		canvas.draw_texture_rect_region(t, dst, Rect2(frame * fw, 0.0, fw, fh))
	# Экран побит: стрелка «вперёд» справа качается, подпись над ней.
	if not sim.locked and sim.screen > 0 and not sim.ended:
		var g: Texture2D = tex["brawl_go"]
		var bob := roundf(absf(sin(_time * 7.0)) * 8.0)
		var at := Vector2(bit16.view.x - 108.0 + bob, 96.0)
		if g != null:
			canvas.draw_texture_rect_region(g, Rect2(at, Vector2(72.0, 44.0)), Rect2((int(_time * 4.0) % 2) * 72.0, 0.0, 72.0, 44.0))
		PixelFont16.draw(canvas, at + Vector2(-6.0, -22.0), "ВПЕРЁД!", GOLD_RAMP[3], GOLD_RAMP[1], INK, 2.0)


## Тень под ногами: пиксельный овал, меньше, когда боец в воздухе.
func _shadow(canvas: CanvasItem, c: Vector2, rx: float) -> void:
	var ry := maxf(roundf(rx * 0.26), 2.0)
	var col := Color(0.04, 0.02, 0.08, 0.42)
	for k in range(-int(ry), int(ry) + 1):
		var w := roundf(rx * sqrt(maxf(1.0 - pow(k / (ry + 0.5), 2.0), 0.0)))
		canvas.draw_rect(Rect2(c.x - w, c.y + k, w * 2.0, 1.0), col)


func _windup_seconds(f: BrawlSim.Fighter) -> float:
	match f.kind:
		BrawlWaves.Kind.KNIFE:
			return tuning.knife_windup
		BrawlWaves.Kind.BOSS:
			return tuning.boss_windup
	return tuning.thug_windup


## Кадр бойца по состоянию и времени в нём (раскладка лент в `tools/pixel_brawl16.py`).
func _frame(f: BrawlSim.Fighter) -> int:
	var t := f.state_t
	var idle := int(_anim * 5.5) % 4
	var walk := int(float(_walk.get(f, 0.0)) / 7.0) % 8
	if f.kind == BrawlWaves.Kind.HERO:
		match f.state:
			BrawlSim.State.WALK:
				return HERO["walk"] + walk
			BrawlSim.State.ATTACK:
				if f.combo == 2:
					var k := 0 if t < tuning.kick_hit * 0.5 else 1 if t < tuning.kick_hit + 0.1 else 2 if t < tuning.kick_seconds - 0.08 else 3
					return HERO["kick"] + k
				var at := tuning.jab_hit
				var k2 := 0 if t < at * 0.7 else 1 if t < at + 0.08 else 2
				return (HERO["jab"] if f.combo == 0 else HERO["cross"]) + k2
			BrawlSim.State.HEAVY:
				var w := tuning.heavy_windup
				var k3 := 0 if t < w * 0.5 else 1 if t < w else 2 if t < w + 0.12 else 3 if t < w + 0.24 else 4
				return HERO["heavy"] + k3
			BrawlSim.State.HURT:
				return HERO["hurt"] + (0 if t < 0.12 else 1)
			BrawlSim.State.DOWN, BrawlSim.State.DEAD, BrawlSim.State.THROWN:
				return HERO["fall"] if f.z > 2.0 else HERO["down"]
			BrawlSim.State.GETUP:
				return HERO["getup"] + (0 if t < tuning.getup_seconds * 0.5 else 1)
			BrawlSim.State.GRAB:
				return HERO["knee"] if _knee_t < 0.2 else HERO["grab"]
		if _throw_t < 0.3:
			return HERO["throw"] + (0 if _throw_t < 0.14 else 1)
		return HERO["idle"] + idle
	match f.state:
		BrawlSim.State.WALK:
			return FOE["walk"] + walk
		BrawlSim.State.WINDUP:
			return FOE["windup"] + (0 if t < _windup_seconds(f) * 0.45 else 1)
		BrawlSim.State.STRIKE:
			return FOE["strike"] + (0 if t < 0.12 else 1)
		BrawlSim.State.HURT:
			return FOE["hurt"] + (0 if t < 0.12 else 1)
		BrawlSim.State.GRABBED:
			return FOE["grabbed"]
		BrawlSim.State.DOWN, BrawlSim.State.DEAD, BrawlSim.State.THROWN:
			return FOE["fall"] if f.z > 2.0 else FOE["down"]
		BrawlSim.State.GETUP:
			return FOE["getup"] + (0 if t < tuning.getup_seconds * 0.5 else 1)
		BrawlSim.State.CHARGE:
			return FOE["charge"] + int(_anim * 14.0) % 4 if f.kind == BrawlWaves.Kind.BOSS else FOE["walk"] + walk
	return FOE["idle"] + idle


func _draw_fighter(canvas: CanvasItem, f: BrawlSim.Fighter) -> void:
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
	var fw := 128.0 if boss else 96.0
	var fh := 136.0 if boss else 112.0
	# Неуязвимость и смерть: мигает (белая заливка поверх мигания не гаснет).
	if f.flash <= 0.0 and (f.invuln > 0.0 or f.state == BrawlSim.State.DEAD) and fmod(_time, 0.12) < 0.06:
		return
	var feet := Vector2(_sx(f.pos.x), _floor_y() + f.pos.y - f.z)
	var dst := Rect2(roundf(feet.x - fw * 0.5), roundf(feet.y - fh + FOOT), fw, fh)
	if slot != "" and is_pink(slot) or t == null:
		canvas.draw_rect(Rect2(dst.position + Vector2(fw * 0.3, fh * 0.2), Vector2(fw * 0.4, fh * 0.8)), Demo.PINK)
		return
	if f.facing < 0.0:
		dst = Rect2(dst.position.x, dst.position.y, -fw, fh)
	canvas.draw_texture_rect_region(t, dst, Rect2(_frame(f) * fw, 0.0, fw, fh), FLASH if f.flash > 0.0 else Color.WHITE)


# --- HUD -------------------------------------------------------------------------------------

## Как в Streets of Rage 2, только сочнее: лицо в латунной рамке, имя пиксельным шрифтом с
## градиентом, полоска с фаской, градиентом и тающим «хвостом» урона, жизни «×N». Под героем тот
## враг, кого бьёшь; у боцмана полоска всегда, пока он жив. Посередине плашка «БОЦМАН» при выходе.
func _draw_hud(canvas: CanvasItem) -> void:
	var show := _target if _target_t > 0.0 and _target != null and not _target.gone else null
	for f in sim.foes:
		if f.kind == BrawlWaves.Kind.BOSS and f.state != BrawlSim.State.DEAD and not f.gone:
			if show != f:
				_target_lag = maxf(_target_lag, float(f.hp) / f.max_hp) if show == null else _target_lag
			show = f
	var low := sim.hero.hp < sim.hero.max_hp * 0.3 and fmod(_time, 0.5) < 0.25
	_plate(canvas, Vector2(10.0, 8.0), "brawl_face_hero", "МАТРОС", float(sim.hero.hp) / sim.hero.max_hp, _hero_lag,
			GOLD_RAMP, low, sim.hero.flash > 0.0)
	PixelFont16.draw(canvas, Vector2(216.0, 32.0), "×%d" % sim.lives, Color.WHITE, GOLD_RAMP[2], INK, 2.0)
	if show != null:
		var face := "brawl_face_thug"
		match show.kind:
			BrawlWaves.Kind.KNIFE:
				face = "brawl_face_knife"
			BrawlWaves.Kind.BOSS:
				face = "brawl_face_boss"
		_plate(canvas, Vector2(10.0, 58.0), face, show.name, float(show.hp) / show.max_hp, _target_lag, RED_RAMP, false,
				show.flash > 0.0)
	if _banner_t > 0.0:
		var cell := 4.0
		var w := PixelFont16.width(_banner, cell)
		var slide := minf((2.2 - _banner_t) * 6.0, 1.0) if _banner_t > 0.4 else _banner_t / 0.4
		var y := roundf(bit16.view.y * 0.32)
		var band := Rect2(0.0, y - 10.0, bit16.view.x, 7.0 * cell + 20.0)
		canvas.draw_rect(band, Color(0.05, 0.02, 0.08, 0.55 * slide))
		canvas.draw_rect(Rect2(0.0, band.position.y, bit16.view.x, 2.0), Color(BRASS[2], slide))
		canvas.draw_rect(Rect2(0.0, band.end.y - 2.0, bit16.view.x, 2.0), Color(BRASS[1], slide))
		var x := roundf(lerpf(-w, (bit16.view.x - w) * 0.5, slide))
		PixelFont16.draw(canvas, Vector2(x, y), _banner, Color.WHITE, RED_RAMP[3], INK, cell)


## Плашка бойца: лицо в рамке, имя, полоска здоровья.
func _plate(canvas: CanvasItem, at: Vector2, face: String, label: String, k: float, lag: float, ramp: Array[Color],
		blink: bool, flash: bool) -> void:
	_frame_box(canvas, Rect2(at, Vector2(40.0, 40.0)))
	var t: Texture2D = tex.get(face)
	if t != null:
		canvas.draw_texture(t, at + Vector2(4.0, 4.0), FLASH if flash else Color.WHITE)
	PixelFont16.draw(canvas, at + Vector2(48.0, 2.0), label.to_upper(), Color.WHITE, ramp[2], INK, 2.0)
	_bar(canvas, Rect2(at + Vector2(46.0, 22.0), Vector2(148.0, 14.0)), k, lag, ramp, blink)


## Латунная рамка с фаской и тёмной лункой внутри.
func _frame_box(canvas: CanvasItem, r: Rect2) -> void:
	canvas.draw_rect(r.grow(1.0), INK)
	canvas.draw_rect(r, BRASS[1])
	canvas.draw_rect(Rect2(r.position, Vector2(r.size.x, 1.0)), BRASS[3])
	canvas.draw_rect(Rect2(r.position, Vector2(1.0, r.size.y)), BRASS[3])
	canvas.draw_rect(Rect2(r.position + Vector2(1.0, 1.0), Vector2(r.size.x - 2.0, 1.0)), BRASS[2])
	canvas.draw_rect(Rect2(r.position + Vector2(1.0, 1.0), Vector2(1.0, r.size.y - 2.0)), BRASS[2])
	canvas.draw_rect(Rect2(r.position.x, r.end.y - 1.0, r.size.x, 1.0), BRASS[0])
	canvas.draw_rect(Rect2(r.end.x - 1.0, r.position.y, 1.0, r.size.y), BRASS[0])
	canvas.draw_rect(r.grow(-3.0), INK)
	canvas.draw_rect(r.grow(-4.0), WELL)
	# Заклёпки по углам.
	for c: Vector2 in [r.position, Vector2(r.end.x - 2.0, r.position.y), Vector2(r.position.x, r.end.y - 2.0), r.end - Vector2(2.0, 2.0)]:
		canvas.draw_rect(Rect2(c, Vector2(2.0, 2.0)), BRASS[3])


## Полоска: рамка, лунка, белый «хвост» урона, заливка рядами от светлого к тёмному с бликом,
## насечки; при малом здоровье мигает.
func _bar(canvas: CanvasItem, r: Rect2, k: float, lag: float, ramp: Array[Color], blink: bool) -> void:
	_frame_box(canvas, r.grow(3.0))
	var inner := r
	var fill := roundf(inner.size.x * clampf(k, 0.0, 1.0))
	var tail := roundf(inner.size.x * clampf(lag, 0.0, 1.0))
	if tail > fill:
		canvas.draw_rect(Rect2(inner.position + Vector2(fill, 0.0), Vector2(tail - fill, inner.size.y)), Color("#f4f0f8"))
		canvas.draw_rect(Rect2(inner.position + Vector2(fill, inner.size.y - 3.0), Vector2(tail - fill, 3.0)), Color("#b8a8c8"))
	if fill > 0.0:
		var rows: Array[Color] = [ramp[3], ramp[2], ramp[2], ramp[2], ramp[1], ramp[1], ramp[0]]
		var h := inner.size.y
		for y in int(h):
			var c: Color = rows[mini(int(y * rows.size() / h), rows.size() - 1)]
			if blink:
				c = c.lightened(0.45)
			canvas.draw_rect(Rect2(inner.position.x, inner.position.y + y, fill, 1.0), c)
		canvas.draw_rect(Rect2(inner.position + Vector2(2.0, 2.0), Vector2(maxf(fill - 4.0, 0.0), 1.0)), Color(1.0, 1.0, 1.0, 0.55))
		var x := 8.0
		while x < fill:
			canvas.draw_rect(Rect2(inner.position.x + x, inner.position.y + 1.0, 1.0, h - 2.0), Color(ramp[0], 0.35))
			x += 8.0
		canvas.draw_rect(Rect2(inner.position.x + fill - 1.0, inner.position.y, 1.0, h), ramp[3])
