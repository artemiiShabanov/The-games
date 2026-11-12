extends Demo
## Демка шутер × 16/32-bit «до выхода» (#100, решение 2026-11-12, `docs/specs/demos_catalog.md`),
## графика по Doom: вид от первого лица на рейкастинге, текстуры на стенах, полу и потолке,
## свет темнеет с расстоянием ступенями, оружие в руке, лицо героя в HUD. Комнаты и коридоры
## из сида, скелеты-пираты с мушкетами стреляют медленными пулями, с саблями бегут и рубят,
## аптечки, ключ от двери выхода. Управление (плейтест 2026-11-12): WASD бег и стрейф, стрелки
## влево и вправо обзор, A (пробел) выстрел пулей, которую видно.
## Карта из `HoldMapGen` по сиду записи, правила и боты в `HoldSim` (без окна, им же проверяются
## сиды); демка шагает им ровно 60 раз в секунду, рисует и озвучивает события.
##
## Рендер: пол и потолок шейдером на весь экран (луч на каждый пиксель, текстура по месту на
## полу, у каждого зала свой пол по карте клеток), стены высотой `WALL_H` по столбцу на пиксель
## (DDA по клеткам, текстура по месту удара), спрайты от дальних к ближним столбцами с буфером
## глубины. Свет: `1,25 − расстояние / fog`, ступенями по
## восьмушке, как в Doom.
##
## Баги по флагам записи (параметры в `resources/bugs/<id>.tres`). Общие (#44) и баг технологии
## `layer_tear` (разрывы кадра) живут в `Demo` и `Bit16Screen`. Свои проявления: `wild_physics`
## лёд на палубе (героя заносит) и скелеты с пулями быстрее; `through_enemies` каждая вторая пуля
## сквозь врага; `unreachable_coins` враги без конца; `sneeze_enemies` скелет падает с одного
## попадания и от касания; `through_walls` герой ходит сквозь стены.

## Высота нижней панели (здоровье, лицо, побито и ключ).
const STATUS_H := 38.0
const ZOOM := 3
## Высота стены в клетках (глаз на 0,5): потолок выше, залы просторнее (плейтест 2026-11-12).
const WALL_H := 1.5
const FOG := 8.0
const MIN_LIGHT := 0.22
## Сколько ступеней у света.
const LIGHT_STEPS := 8.0
const TEX := 64.0
const PLACEHOLDER_SLOTS: Array[String] = ["skeleton", "key", "medkit"]
const SPRITES: Array[String] = ["wall_planks", "wall_stone", "wall_pillar", "wall_exit", "wall_cabin", "wall_hull",
		"wall_cargo", "floor_planks", "floor_stone", "floor_carpet", "ceiling_beams", "skel_walk", "skel_fire", "skel_die",
		"cut_walk", "cut_slash", "cut_die", "shot", "bullet", "key", "medkit", "pistol", "face", "hold_decor"]
const FLOOR_SHADER := """
shader_type canvas_item;
uniform sampler2D floor_tex : filter_nearest, repeat_enable;
uniform sampler2D floor_stone : filter_nearest, repeat_enable;
uniform sampler2D floor_carpet : filter_nearest, repeat_enable;
uniform sampler2D ceil_tex : filter_nearest, repeat_enable;
uniform sampler2D map_tex : filter_nearest;
uniform vec2 map_size;
uniform float wall_h;
uniform vec2 pos;
uniform vec2 dir;
uniform vec2 plane;
uniform vec2 view;
uniform float proj;
uniform float fog;
uniform float min_light;
uniform float steps;
void fragment() {
	vec2 px = floor(UV * view) + 0.5;
	float p = px.y - view.y * 0.5;
	float ap = abs(p);
	float row = (p > 0.0 ? 0.5 : wall_h - 0.5) * proj / max(ap, 0.5);
	float cam = 2.0 * px.x / view.x - 1.0;
	vec2 w = pos + (dir + plane * cam) * row;
	vec4 c;
	if (p > 0.0) {
		float kind = texture(map_tex, (floor(w) + 0.5) / map_size).r * 255.0;
		c = kind > 1.5 ? texture(floor_carpet, fract(w)) : (kind > 0.5 ? texture(floor_stone, fract(w)) : texture(floor_tex, fract(w)));
	} else {
		c = texture(ceil_tex, fract(w));
	}
	float light = clamp(1.25 - row / fog, min_light, 1.0);
	light = floor(light * steps) / steps;
	COLOR = vec4(c.rgb * light, 1.0);
}
"""
const MELODY := [0, null, 0, 3, null, 0, 6, 5, 0, null, 0, 3, null, 0, 8, 7,
	0, null, 0, 3, null, 0, 6, 5, 3, null, 2, null, 0, null, -2, null]
const BASS := [-12, -12, -12, -12, -9, -9, -6, -6, -12, -12, -12, -12, -4, -4, -5, -5]

var tuning: ShooterBit16Tuning
var map: HoldMap
var sim: HoldSim
var tex := {}
var proj := 277.0
var _zbuf := PackedFloat32Array()
var _floor: ColorRect
var _floor_mat: ShaderMaterial
var _time := 0.0
var _acc := 0.0
var _fire_t := 9.0
var _hurt_t := 9.0
var _grin_t := 9.0
## Звёзды попаданий (`Fx16`) в координатах экрана.
var fx: Fx16
var _foe_fire_t: Dictionary[int, float] = {}
var _slash_t: Dictionary[int, float] = {}
var _music: AudioStreamPlayer
var _sfx := {}


func _on_start() -> void:
	tuning = ShooterBit16Tuning.load_default()
	map = HoldMapGen.generate(record.seed if record != null else 1)
	sim = HoldSim.create(map, tuning)
	look_start()
	if has_bug(&"wild_physics"):
		sim.ice = bug_param(&"wild_physics", &"ice_response", 2.5)
		sim.foe_mult = bug_param(&"wild_physics", &"foe_speed_mult", 1.5)
	if has_bug(&"through_enemies"):
		sim.pass_every = maxi(int(bug_param(&"through_enemies", &"pass_every", 2.0)), 1)
	if has_bug(&"unreachable_coins"):
		sim.extra_per_kill = maxi(int(bug_param(&"unreachable_coins", &"extra_per_kill", 1.0)), 1)
		sim.rise_seconds = bug_param(&"unreachable_coins", &"hold_rise_seconds", 2.0)
	sim.sneeze = has_bug(&"sneeze_enemies")
	sim.walls_open = has_bug(&"through_walls")
	bit16_screen(Callable(), _draw_world, _draw_hud, ZOOM)
	fx = Fx16.create(bit16_set)
	# Стена выше клетки: текстура повторяется по высоте.
	bit16.world.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	for name in SPRITES:
		tex[name] = bit16_set.sprite16(name)
	proj = bit16.view.x * 0.5
	_zbuf.resize(int(bit16.view.x))
	var sh := Shader.new()
	sh.code = FLOOR_SHADER
	_floor_mat = ShaderMaterial.new()
	_floor_mat.shader = sh
	_floor_mat.set_shader_parameter("floor_tex", tex["floor_planks"])
	_floor_mat.set_shader_parameter("floor_stone", tex["floor_stone"])
	_floor_mat.set_shader_parameter("floor_carpet", tex["floor_carpet"])
	var img := Image.create(map.width, map.height, false, Image.FORMAT_R8)
	for y in map.height:
		for x in map.width:
			img.set_pixel(x, y, Color8(map.floor_at(x, y), 0, 0))
	_floor_mat.set_shader_parameter("map_tex", ImageTexture.create_from_image(img))
	_floor_mat.set_shader_parameter("map_size", Vector2(map.width, map.height))
	_floor_mat.set_shader_parameter("wall_h", WALL_H)
	_floor_mat.set_shader_parameter("ceil_tex", tex["ceiling_beams"])
	_floor_mat.set_shader_parameter("view", bit16.view)
	_floor_mat.set_shader_parameter("proj", proj)
	_floor_mat.set_shader_parameter("fog", FOG)
	_floor_mat.set_shader_parameter("min_light", MIN_LIGHT)
	_floor_mat.set_shader_parameter("steps", LIGHT_STEPS)
	_floor = ColorRect.new()
	_floor.size = bit16.view
	_floor.material = _floor_mat
	_floor.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bit16.backdrop.add_child(_floor)
	_setup_audio()


func _setup_audio() -> void:
	_music = Sfx.music(Sfx.tracker_loop(MELODY, BASS, 112.0), tuning.music_db if not embedded else -80.0)
	add_child(_music)
	bug_music = _music
	if not embedded:
		_music.play()
	_sfx["fire"] = Sfx.player(Sfx.thud(0.12, 0.45))
	_sfx["hit"] = Sfx.player(Sfx.blip(220.0, 0.08, 0.3, 30.0))
	_sfx["kill"] = Sfx.player(Sfx.beep(330.0, 0.3, 0.3, 110.0))
	_sfx["foe_fire"] = Sfx.player(Sfx.blip(160.0, 0.12, 0.25, 20.0))
	_sfx["hurt"] = Sfx.player(Sfx.blip(120.0, 0.25, 0.4, 9.0))
	_sfx["medkit"] = Sfx.player(Sfx.blip(988.0, 0.15, 0.3, 14.0))
	_sfx["key"] = Sfx.player(Sfx.beep(660.0, 0.3, 0.3, 1320.0))
	_sfx["locked"] = Sfx.player(Sfx.thud(0.08, 0.2))
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
		AutoTest.note("shooter bit16: %s за %.1f с, здоровье %d, убито %d, выстрелов %d" % [
				"выход" if goal else "гибель", elapsed, sim.health, sim.kills, sim.shots_fired])


func _result_caption() -> String:
	return "здоровье %d · скелетов %d · %d с" % [sim.health, sim.kills, int(round(elapsed))]


# --- Ввод и шаг ------------------------------------------------------------------------------

## Бот ходит внутри шагов мира (`_step`), ровно как в прогоне без окна.
func _bot_step(_delta: float) -> void:
	pass


func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	bug_frame(delta, sim.moving, _step)


func _step(dt: float) -> void:
	_time += dt
	_fire_t += dt
	_hurt_t += dt
	_grin_t += dt
	if fx != null:
		fx.step(dt)
	bug_input_tick()
	_acc = minf(_acc + dt, 0.25)
	while _acc >= HoldSim.DT - 0.0001 and not sim.ended:
		_acc -= HoldSim.DT
		var move := 0.0
		var turn := 0.0
		var strafe := 0.0
		var fire := false
		if bot_driven():
			var b := sim.bot(active_bot_mode())
			move = b.x
			turn = b.y
			strafe = sim.bot_strafe
			fire = sim.bot_fire
		else:
			# WASD бег и стрейф, стрелки обзор (с багом управления с опозданием).
			var walk := bug_axis(GameInput.walk())
			move = walk.y
			strafe = walk.x
			turn = GameInput.look()
			fire = GameInput.a_pressed() or look_fire()
			# Мышь и правый стик (#109): поворот сразу в курс, наклона у рейкастера нет.
			sim.angle = fposmod(sim.angle + look_take(HoldSim.DT).x, TAU)
		sim.step(move, turn, strafe, fire)
		for ev in sim.events:
			_on_event(ev)
		sim.events.clear()
	var d := sim.dir()
	_floor_mat.set_shader_parameter("pos", sim.pos)
	_floor_mat.set_shader_parameter("dir", d)
	_floor_mat.set_shader_parameter("plane", Vector2(-d.y, d.x))


func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"fire":
			_fire_t = 0.0
			_play("fire")
		&"hit", &"kill":
			_play(String(ev[0]))
			var mid := Vector2(bit16.view.x * 0.5, (bit16.view.y - STATUS_H) * 0.5)
			fx.add("star", mid + Vector2(randf_range(-6.0, 6.0), randf_range(-10.0, 6.0)), randf() < 0.5)
			if ev[0] == &"kill":
				_grin_t = 0.0
		&"foe_fire":
			_foe_fire_t[int(ev[1])] = _time
			_play("foe_fire")
		&"slash":
			_slash_t[int(ev[1])] = _time
			_play("hurt")
		&"hurt":
			_hurt_t = 0.0
			_play("hurt")
			if AutoTest.enabled and not embedded and sim.health <= 30:
				AutoTest.note("shooter bit16: здоровье %d на %.1f с" % [sim.health, elapsed])
		&"medkit", &"key":
			_grin_t = 0.0
			_play(String(ev[0]))
		&"locked":
			if _time > 0.0 and fmod(_time, 0.5) < HoldSim.DT * 2.0:
				_play("locked")
		&"win":
			end_demo(true)
		&"lose":
			end_demo(false)


# --- Рендер ------------------------------------------------------------------------------------

func _light(dist: float) -> float:
	return floorf(clampf(1.25 - dist / FOG, MIN_LIGHT, 1.0) * LIGHT_STEPS) / LIGHT_STEPS


func _wall_tex(c: HoldMap.Cell) -> Texture2D:
	match c:
		HoldMap.Cell.STONE:
			return tex["wall_stone"]
		HoldMap.Cell.CABIN:
			return tex["wall_cabin"]
		HoldMap.Cell.HULL:
			return tex["wall_hull"]
		HoldMap.Cell.CARGO:
			return tex["wall_cargo"]
		HoldMap.Cell.EXIT:
			return tex["wall_exit"]
		HoldMap.Cell.PILLAR:
			return tex["wall_pillar"]
	return tex["wall_planks"]


func _draw_world(canvas: CanvasItem) -> void:
	_draw_walls(canvas)
	_draw_sprites(canvas)
	_draw_weapon(canvas)
	fx.draw(canvas, func(p: Vector2) -> Vector2: return p)
	# Боль: красная вспышка, ключ и аптечка: золотая.
	if _hurt_t < 0.3:
		canvas.draw_rect(Rect2(Vector2.ZERO, bit16.view), Color(0.8, 0.05, 0.05, 0.35 * (1.0 - _hurt_t / 0.3)))
	if _grin_t < 0.25:
		canvas.draw_rect(Rect2(Vector2.ZERO, bit16.view), Color(1.0, 0.85, 0.3, 0.18 * (1.0 - _grin_t / 0.25)))


## Стены: луч на столбец, шаг по клеткам до стены (DDA), высота по перпендикулярному
## расстоянию, столбец текстуры по месту удара; стены вдоль y темнее, свет по расстоянию.
func _draw_walls(canvas: CanvasItem) -> void:
	var w := int(bit16.view.x)
	var h := bit16.view.y
	var d := sim.dir()
	var plane := Vector2(-d.y, d.x)
	for x in w:
		var cam := 2.0 * (x + 0.5) / w - 1.0
		var ray := d + plane * cam
		var mx := int(floor(sim.pos.x))
		var my := int(floor(sim.pos.y))
		var ddx := absf(1.0 / ray.x) if ray.x != 0.0 else 1e30
		var ddy := absf(1.0 / ray.y) if ray.y != 0.0 else 1e30
		var step_x := 1 if ray.x >= 0.0 else -1
		var step_y := 1 if ray.y >= 0.0 else -1
		var sx := (mx + 1.0 - sim.pos.x) * ddx if ray.x >= 0.0 else (sim.pos.x - mx) * ddx
		var sy := (my + 1.0 - sim.pos.y) * ddy if ray.y >= 0.0 else (sim.pos.y - my) * ddy
		var side := 0
		var hit := HoldMap.Cell.PLANKS
		for i in 64:
			if sx < sy:
				sx += ddx
				mx += step_x
				side = 0
			else:
				sy += ddy
				my += step_y
				side = 1
			var c := map.cell(mx, my)
			if c != HoldMap.Cell.FLOOR:
				hit = c
				break
		var dist := (sx - ddx) if side == 0 else (sy - ddy)
		dist = maxf(dist, 0.02)
		_zbuf[x] = dist
		var line_h := proj / dist * WALL_H
		var top := h * 0.5 + 0.5 * proj / dist - line_h
		var wall_x := (sim.pos.y + dist * ray.y) if side == 0 else (sim.pos.x + dist * ray.x)
		wall_x -= floorf(wall_x)
		var tx := int(wall_x * TEX)
		if (side == 0 and ray.x > 0.0) or (side == 1 and ray.y < 0.0):
			tx = int(TEX) - tx - 1
		var l := _light(dist) * (0.78 if side == 1 else 1.0)
		canvas.draw_texture_rect_region(_wall_tex(hit), Rect2(x, top, 1.0, line_h), Rect2(tx, 0.0, 1.0, TEX * WALL_H), Color(l, l, l))


## Спрайты: скелеты, пули, ключ, аптечки; от дальних к ближним, по столбцам, которые ближе
## стены в буфере глубины. Низ спрайта на полу.
func _draw_sprites(canvas: CanvasItem) -> void:
	var items: Array[Array] = []
	for i in sim.foes.size():
		var f := sim.foes[i]
		if not f.alive and _time - f.died_at > 30.0:
			continue
		items.append([f.pos, "foe", i])
	for s in sim.shots:
		items.append([s.pos, "bullet" if s.mine else "shot", 0])
	for d in map.decor:
		items.append([Vector2(d.x, d.y), "decor", int(d.z)])
	if not sim.has_key:
		items.append([map.key, "key", 0])
	for i in map.medkits.size():
		if sim.medkit_taken[i] == 0:
			items.append([map.medkits[i], "medkit", i])
	items.sort_custom(func(a: Array, b: Array) -> bool:
		return (a[0] as Vector2).distance_squared_to(sim.pos) > (b[0] as Vector2).distance_squared_to(sim.pos))
	for it in items:
		_draw_billboard(canvas, it)


func _draw_billboard(canvas: CanvasItem, it: Array) -> void:
	var p: Vector2 = it[0]
	var d := sim.dir()
	var plane := Vector2(-d.y, d.x)
	var rel := p - sim.pos
	var inv := 1.0 / (plane.x * d.y - d.x * plane.y)
	var tx := inv * (d.y * rel.x - d.x * rel.y)
	var ty := inv * (-plane.y * rel.x + plane.x * rel.y)
	if ty <= 0.1:
		return
	var sx := bit16.view.x * 0.5 * (1.0 + tx / ty)
	var floor_y := bit16.view.y * 0.5 + 0.5 * proj / ty
	var t: Texture2D
	var frame := 0
	var frames := 1
	var size := 1.0
	var lift := 0.0
	var flip := false
	var slot := ""
	match it[1] as String:
		"foe":
			var f := sim.foes[int(it[2])]
			var cut := f.kind == HoldMap.Foe.CUTLASS
			slot = "skeleton"
			size = 0.9
			if not f.alive:
				t = tex["cut_die" if cut else "skel_die"]
				frames = 3
				frame = mini(int((sim.time - f.died_at) * 8.0), 2)
			elif cut and _time - float(_slash_t.get(int(it[2]), -9.0)) < 0.3:
				t = tex["cut_slash"]
				frames = 2
				frame = 1 if _time - float(_slash_t[int(it[2])]) < 0.15 else 0
			elif not cut and _time - float(_foe_fire_t.get(int(it[2]), -9.0)) < 0.3:
				t = tex["skel_fire"]
				frames = 2
				frame = 1 if _time - float(_foe_fire_t[int(it[2])]) < 0.12 else 0
			else:
				t = tex["cut_walk" if cut else "skel_walk"]
				frames = 10
				var to := sim.pos - f.pos
				var view_rel := wrapf(atan2(to.y, to.x) - f.facing, -PI, PI)
				var a := int(round(absf(view_rel) / (PI / 4.0)))
				flip = view_rel > 0.0
				frame = a * 2 + ((int(_time * 5.0) % 2) if f.walking else 0)
		"shot":
			t = tex["shot"]
			size = 0.18
			lift = 0.45
		"bullet":
			t = tex["bullet"]
			size = 0.12
			lift = 0.42
		"decor":
			t = tex["hold_decor"]
			frames = 6
			frame = int(it[2])
			size = 0.85
		"key":
			t = tex["key"]
			size = 0.35
			lift = 0.25 + sin(_time * 3.0) * 0.05
		"medkit":
			t = tex["medkit"]
			slot = "medkit"
			size = 0.4
	if t == null:
		return
	var fw := float(t.get_width()) / frames
	var fh := float(t.get_height())
	var sh := proj / ty * size
	var sw := sh * fw / fh
	var top := floor_y - sh - lift * proj / ty
	var x0 := int(floor(sx - sw * 0.5))
	var x1 := int(ceil(sx + sw * 0.5))
	var l := _light(ty)
	var pink := slot != "" and is_pink(slot)
	for x in range(maxi(x0, 0), mini(x1, int(bit16.view.x))):
		if ty >= _zbuf[x]:
			continue
		var u := (x - (sx - sw * 0.5)) / sw
		if flip:
			u = 1.0 - u
		var src_x := frame * fw + clampf(floorf(u * fw), 0.0, fw - 1.0)
		if pink:
			canvas.draw_rect(Rect2(x, top, 1.0, sh), Color(1.0, 0.4, 0.8))
		else:
			canvas.draw_texture_rect_region(t, Rect2(x, top, 1.0, sh), Rect2(src_x, 0.0, 1.0, fh), Color(l, l, l))


## Пистоль снизу по центру, качается при ходьбе; после выстрела кадр со вспышкой.
func _draw_weapon(canvas: CanvasItem) -> void:
	var t: Texture2D = tex["pistol"]
	var bob := Vector2(sin(sim.walked * 2.2) * 6.0, absf(cos(sim.walked * 2.2)) * 5.0) if sim.moving else Vector2.ZERO
	var frame := 1 if _fire_t < 0.09 else 0
	var w := 128.0
	var h := float(t.get_height())
	var pos := Vector2(bit16.view.x * 0.5 - w * 0.5, bit16.view.y - h - 30.0 + 18.0) + bob
	if _fire_t < 0.12:
		pos.y += 6.0
	canvas.draw_texture_rect_region(t, Rect2(pos.round(), Vector2(w, h)), Rect2(frame * w, 0.0, w, h))


# --- HUD -------------------------------------------------------------------------------------

## Панель снизу как в Doom: здоровье числом слева, лицо героя по центру (смотрит по сторонам,
## морщится от попадания, ухмыляется от ключа, аптечки и убитого), ключ справа.
func _draw_hud(canvas: CanvasItem) -> void:
	# Панель как у Doom, но в латуни и дереве: доска с фаской, три отсека в рамках (здоровье с
	# полоской, лицо, побито и ключ), подписи пиксельным шрифтом.
	var bar := Rect2(0.0, bit16.view.y - STATUS_H, bit16.view.x, STATUS_H)
	canvas.draw_rect(bar, Color("#4a2c1a"))
	for x in range(0, int(bar.size.x), 24):
		canvas.draw_rect(Rect2(x, bar.position.y + 2.0, 1.0, bar.size.y - 2.0), Color("#2e1a10"))
		canvas.draw_rect(Rect2(x + 1.0, bar.position.y + 2.0, 1.0, bar.size.y - 2.0), Color("#6a4428"))
	canvas.draw_rect(Rect2(bar.position, Vector2(bar.size.x, 1.0)), Fx16.INK)
	canvas.draw_rect(Rect2(bar.position + Vector2(0.0, 1.0), Vector2(bar.size.x, 1.0)), Fx16.BRASS[2])
	var low := sim.health <= 30
	var blink := low and fmod(_time, 0.5) < 0.25
	var hr := Rect2(8.0, bar.position.y + 5.0, 150.0, STATUS_H - 9.0)
	Fx16.frame_box(canvas, hr, blink)
	PixelFont16.draw(canvas, hr.position + Vector2(6.0, 4.0), "ЗДОРОВЬЕ", Color("#d8d0e8"), Color("#9a90b0"), Fx16.INK, 1.0)
	var red: Array[Color] = [Color("#5a1018"), Color("#a8242a"), Color("#e2483a"), Color("#ff9a78")]
	var gold: Array[Color] = [Color("#7a3a10"), Color("#d0781c"), Color("#f8c040"), Color("#fff2a0")]
	var ramp := red if low else gold
	# Полоска сначала, число поверх: иначе рамка полоски закрывала низ цифр.
	Fx16.bar(canvas, Rect2(hr.position + Vector2(6.0, 21.0), Vector2(hr.size.x - 12.0, 3.0)),
			float(sim.health) / tuning.health, ramp, blink)
	PixelFont16.draw(canvas, hr.position + Vector2(98.0, 3.0), str(sim.health), ramp[3], ramp[2], Fx16.INK, 2.0)
	var face := 0
	if _hurt_t < 0.6:
		face = 3
	elif _grin_t < 0.8:
		face = 4
	else:
		face = [0, 0, 1, 0, 0, 2][int(_time * 1.2) % 6]
	var fc := Vector2(bit16.view.x * 0.5, bar.end.y - 1.0)
	Fx16.frame_box(canvas, Rect2(fc - Vector2(21.0, STATUS_H - 3.0), Vector2(42.0, STATUS_H - 4.0)), _hurt_t < 0.2)
	bit16.sprite(canvas, tex["face"], face, fc)
	var kr := Rect2(bit16.view.x - 158.0, bar.position.y + 5.0, 150.0, STATUS_H - 9.0)
	Fx16.frame_box(canvas, kr, _grin_t < 0.2)
	PixelFont16.draw(canvas, kr.position + Vector2(6.0, 4.0), "ПОБИТО", Color("#d8d0e8"), Color("#9a90b0"), Fx16.INK, 1.0)
	PixelFont16.draw(canvas, kr.position + Vector2(8.0, 13.0), "%02d" % sim.kills, Color.WHITE, Color("#b8c0d0"), Fx16.INK, 2.0)
	var key_box := Rect2(kr.end.x - 40.0, kr.position.y + 3.0, 34.0, kr.size.y - 6.0)
	canvas.draw_rect(key_box, Fx16.INK)
	canvas.draw_rect(key_box.grow(-1.0), Color("#4a3a18") if sim.has_key else Color("#2a1c30"))
	if sim.has_key:
		bit16.sprite(canvas, tex["key"], 0, key_box.get_center() + Vector2(0.0, 14.0))
	else:
		PixelFont16.draw(canvas, key_box.position + Vector2(5.0, 9.0), "КЛЮЧ", Color("#6a5a7a"), Color("#4a3e58"), Fx16.INK, 1.0,
				false)
