extends Demo
## Демка спорт × low poly, каталог `docs/specs/demos_catalog.md`: «броски в кольцо» (#115,
## решение 2026-11-12, приёмы сложности 2026-11-13, образцы: аркадный автомат с кольцом, NBA
## Jam, конкурс трёхочковых). Вид от первого лица, десять бросков бочонком в кольцо на мачте с
## разных точек; точка меняется после каждого броска. Прицел стрелками, мышью или правым
## стиком: в стороны уводит мяч вбок, вверх и вниз меняет подъём броска; A (или кнопка мыши) зажать, шкала силы идёт туда и обратно, отпустить в
## зелёной зоне. Дальние броски стоят три очка, чистый (ничего не задел) на очко дороже, после
## трёх попаданий подряд бочонок горит и бросок стоит вдвое. В середине дует боковой ветер
## (стрелки сверху, деления на прицеле), на последних трёх бросках кольцо ездит, а пунктир
## показывает, где оно будет к прилёту. Цель: набрать очки не ниже порога.
## План из `HoopPlanGen` по сиду записи. Правила и боты живут в `HoopSim` (без окна, им же
## проверяются сто сидов); демка ведёт его шагами по 1/60 с, рисует и озвучивает его события.
##
## Общие баги (#44) и баг технологии `mesh_holes` живут в `Demo` и `LowpolyScreen`, демка только
## зовёт хуки: фризы `bug_frame`, заикание музыки, ввод с опозданием, розовые заглушки вместо
## бочонка, реквизита и кольца. Баги жанра и баланса для этой демки включит #117.

const PLACEHOLDER_SLOTS: Array[String] = ["ball", "prop", "finish"]
const MELODY := [0, 4, 7, null, 9, 7, 4, null, 5, 9, 12, null, 11, 9, 7, null,
	0, 4, 7, 12, 9, null, 7, 4, 5, 7, 9, 5, 7, null, 0, null]
const BASS := [-12, -12, -5, -5, -7, -7, -5, -5, -12, -12, -3, -3, -7, -7, -5, -5]
const DECOR := ["palm", "palm", "rock", "barrel", "crate", "chest"]
const WHITE := Color(0.95, 0.93, 0.86)
const HOT := Color(1.0, 0.6, 0.2)
const PUFFS := 30

var tuning: SportLowpolyTuning
var plan: HoopPlan
var sim: HoopSim
## Прицел: x радианы вправо от линии на кольцо, y вверх от кольца.
var aim := Vector2.ZERO
## На сколько радиан прицел стоит выше середины кадра.
const AIM_RISE := 0.2
var hoop: LowpolyModel
var ball: LowpolyModel
var hand: LowpolyModel
var ball_shadow: MeshInstance3D
var flag: LowpolyModel

var _time := 0.0
var _popup := ""
var _popup_left := 0.0
var _popup_good := false
var _shake := 0.0
var _rng := RandomNumberGenerator.new()
var _trail := 0.0
var _puffs: Array[MeshInstance3D] = []
var _puff_age := PackedFloat32Array()
var _puff_life := PackedFloat32Array()
var _puff_size := PackedFloat32Array()
var _puff_vel := PackedVector3Array()
var _puff_next := 0
var _puff_tex: Texture2D
var _music: AudioStreamPlayer
var _sfx := {}


func _placeholder_slots() -> Array[String]:
	return PLACEHOLDER_SLOTS


func _on_start() -> void:
	tuning = SportLowpolyTuning.load_default()
	plan = HoopPlanGen.generate(record.seed if record != null else 1, null, tuning)
	sim = HoopSim.create(plan, tuning)
	lowpoly_screen(_draw_hud)
	look_start()
	_build_world()
	_build_puffs()
	_setup_audio()
	_sync(0.0)


func _setup_audio() -> void:
	var quiet := embedded
	_music = Sfx.music(Sfx.tracker_loop(MELODY, BASS, 126.0), tuning.music_db if not quiet else -80.0)
	add_child(_music)
	bug_music = _music
	if not quiet:
		_music.play()
	_sfx["go"] = Sfx.player(Sfx.blip(880.0, 0.3, 0.4, 6.0))
	_sfx["charge"] = Sfx.player(Sfx.blip(300.0, 0.08, 0.25, 18.0))
	_sfx["throw"] = Sfx.player(Sfx.hiss(0.16, 0.16))
	_sfx["rim"] = Sfx.player(Sfx.blip(980.0, 0.1, 0.4, 22.0))
	_sfx["board"] = Sfx.player(Sfx.thud(0.1, 0.45))
	_sfx["score"] = Sfx.player(Sfx.blip(660.0, 0.3, 0.45, 7.0))
	_sfx["clean"] = Sfx.player(Sfx.blip(1320.0, 0.35, 0.4, 6.0))
	_sfx["miss"] = Sfx.player(Sfx.blip(170.0, 0.25, 0.4, 8.0))
	_sfx["finish"] = Sfx.player(Sfx.blip(880.0, 0.5, 0.4, 5.0))
	for p in _sfx.values():
		(p as AudioStreamPlayer).volume_db = tuning.sfx_db if not quiet else -80.0
		add_child(p)


func _play(name: String) -> void:
	bug_play(_sfx[name])


# --- Мир ---------------------------------------------------------------------------------------

func _build_world() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(record.seed if record != null else 1, ":hoop-look"))
	lowpoly.add_plane(Vector3(0.0, -0.5, 0.0), Vector2(520.0, 520.0), lowpoly_texture("water"), 6.0,
			{"uv_scroll": Vector2(0.02, 0.035), "affine": 0.0})
	lowpoly.add_plane(Vector3(0.0, 0.0, -3.0), Vector2(76.0, 76.0), lowpoly_texture("sand"), 3.0)
	# Настил площадки под кольцом и точками.
	lowpoly.add_plane(Vector3(0.0, 0.04, -4.2), Vector2(15.0, 11.0), lowpoly_texture("planks"), 2.0)
	hoop = spawn_model("finish", "hoop")
	hoop.scale = Vector3.ONE * tuning.hoop_scale
	ball = spawn_model("ball", "keg")
	ball.scale = Vector3.ONE * (tuning.ball_r / 0.14)
	ball.visible = false
	ball_shadow = lowpoly.add_shadow(0.16)
	ball_shadow.visible = false
	hand = spawn_model("ball", "keg", lowpoly.camera)
	hand.scale = Vector3.ONE * (tuning.ball_r / 0.14) * 0.8
	# Флаг у мачты показывает ветер.
	flag = spawn_model("prop", "flag")
	flag.position = Vector3(-2.4, 0.0, 0.6)
	flag.scale = Vector3.ONE * 1.5
	var tower := spawn_model("prop", "lighthouse")
	tower.position = Vector3(9.0, 0.0, 22.0)
	# Пальмы, камни и бочки вокруг площадки: не между точками и кольцом.
	var placed := 0
	for tries in 300:
		if placed >= 22:
			break
		var p := Vector3(rng.randf_range(-30.0, 30.0), 0.0, rng.randf_range(-32.0, 26.0))
		var behind := p.z > 2.5 and Vector2(p.x, p.z).length() > 5.0
		var around := absf(p.x) > 9.5 or p.z < -11.5
		if not (behind or around):
			continue
		var prop := spawn_model("prop", DECOR[rng.randi_range(0, DECOR.size() - 1)])
		prop.position = p - Vector3(0.0, 0.05, 0.0)
		prop.rotation.y = rng.randf_range(-PI, PI)
		placed += 1


## Клубы огня за горящим бочонком: квадраты лицом к камере с вырезом по альфе.
func _build_puffs() -> void:
	var img := Image.create(8, 8, false, Image.FORMAT_RGBA8)
	for y in 8:
		for x in 8:
			var d := Vector2(x - 3.5, y - 3.5).length()
			var edge := 3.7 if (x + y) % 2 == 0 else 3.3
			var shade := 0.72 if y > 4 else (1.0 if y < 3 and x < 5 else 0.86)
			img.set_pixel(x, y, Color(shade, shade, shade, 1.0 if d < edge else 0.0))
	_puff_tex = ImageTexture.create_from_image(img)
	var verts := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	for item: Array in [[-0.5, -0.5, 0, 1], [0.5, -0.5, 1, 1], [0.5, 0.5, 1, 0], [-0.5, -0.5, 0, 1], [0.5, 0.5, 1, 0], [-0.5, 0.5, 0, 0]]:
		LowpolyScreen.push(verts, normals, uvs, Vector3(item[0], item[1], 0.0), Vector3(0, 0, 1), Vector2(item[2], item[3]))
	LowpolyScreen.flip_last(verts, normals, uvs, 2)
	var mesh := LowpolyScreen._commit(verts, normals, uvs, _puff_material(WHITE))
	for i in PUFFS:
		var node := MeshInstance3D.new()
		node.mesh = mesh
		node.visible = false
		lowpoly.world.add_child(node)
		_puffs.append(node)
		_puff_age.append(-1.0)
		_puff_life.append(0.4)
		_puff_size.append(0.5)
		_puff_vel.append(Vector3.ZERO)


func _puff_material(color: Color) -> ShaderMaterial:
	return lowpoly.tex_material(_puff_tex, {"lit": 0.0, "fog_amount": 0.0, "tint": color})


func _puff(at: Vector3, vel: Vector3, color: Color, size: float, life: float) -> void:
	var i := _puff_next
	_puff_next = (_puff_next + 1) % _puffs.size()
	_puffs[i].position = at
	_puffs[i].set_surface_override_material(0, _puff_material(color))
	_puff_age[i] = 0.0
	_puff_life[i] = life
	_puff_size[i] = size
	_puff_vel[i] = vel


func _burst(at: Vector3, count: int, color: Color, size: float, speed: float) -> void:
	for k in count:
		var dir := Vector3(_rng.randf_range(-1.0, 1.0), _rng.randf_range(-0.4, 1.0), _rng.randf_range(-1.0, 1.0)).normalized()
		_puff(at, dir * speed * _rng.randf_range(0.5, 1.0), color, size * _rng.randf_range(0.7, 1.1), _rng.randf_range(0.3, 0.5))


# --- Шаг -------------------------------------------------------------------------------------

func _on_tick(delta: float) -> void:
	bug_audio_tick(delta)
	_popup_left = maxf(_popup_left - delta, 0.0)
	# Фризы в полёте мяча с догоном времени (`Demo.bug_frame`).
	bug_frame(delta, sim.phase == HoopSim.Phase.FLIGHT, _step)


func _step(dt: float) -> void:
	_time += dt
	bug_input_tick()
	var left := dt
	while left > 0.0001 and running:
		var h := minf(left, HoopSim.DT)
		left -= h
		var hold := false
		if bot_driven():
			sim.bot(active_bot_mode(), h)
			aim = Vector2(sim.bot_yaw, 0.0)
			hold = sim.bot_hold
		else:
			# Прицел стрелками (с багом управления из прошлого), мышью и правым стиком.
			var axis := bug_axis(GameInput.axis())
			var turn := look_take(h)
			aim += Vector2(axis.x * tuning.aim_speed * h + turn.x, -axis.y * tuning.aim_speed * h - turn.y)
			aim = aim.clamp(Vector2(-tuning.aim_limit, -tuning.aim_limit), Vector2(tuning.aim_limit, tuning.aim_limit))
			hold = GameInput.a_pressed() or look_fire()
		sim.step(h, aim.x, hold, aim.y)
		for ev in sim.events:
			_on_event(ev)
		sim.events.clear()
	_sync(dt)


## Событие правил: звук, эффект, конец демки.
func _on_event(ev: Array) -> void:
	match ev[0] as StringName:
		&"go":
			_play("go")
		&"charge":
			_play("charge")
		&"throw":
			_play("throw")
		&"rim":
			_play("rim")
			_shake = 0.5
		&"board":
			_play("board")
		&"score":
			var pure: bool = ev[2]
			_play("clean" if pure else "score")
			_popup = "+%d%s" % [ev[1], " ЧИСТО" if pure else ""]
			_popup_good = true
			_popup_left = tuning.result_seconds
			_burst(sim.rim_now() - Vector3(0.0, 0.3, 0.0), 8 if pure else 4, HOT if ev[3] else WHITE, 0.45, 2.2)
		&"miss":
			_play("miss")
			_popup = "МИМО"
			_popup_good = false
			_popup_left = tuning.result_seconds
		&"next":
			aim = Vector2.ZERO
		&"finish":
			end_demo(true)
		&"fail":
			end_demo(false)


func _on_end(goal: bool) -> void:
	_music.stop()
	if goal:
		_play("finish")
	if AutoTest.enabled and not embedded:
		AutoTest.note("sport lowpoly: очков %d из %d (%s), попал %d из %d, чисто %d, броски %s, время %.1f с" % [sim.score, tuning.goal,
				"порог взят" if goal else "порог не взят", sim.made, plan.shots.size(), sim.clean, sim.results, sim.time])


func _result_title(goal: bool) -> String:
	return "%d очков" % sim.score if goal else "мало очков"


func _result_caption() -> String:
	return "порог %d · попал %d из %d · чисто %d" % [tuning.goal, sim.made, plan.shots.size(), sim.clean]


# --- Картинка --------------------------------------------------------------------------------

## Курс и наклон камеры на точке броска: на кольцо, чуть ниже него, с поворотом прицела.
func _look() -> Vector2:
	var shot := sim.shot()
	var f := HoopSim.forward(shot, tuning)
	var eye := sim.eye()
	var rim := HoopSim.rim_rest(tuning)
	var rise := atan2(rim.y - eye.y, Vector2(rim.x - eye.x, rim.z - eye.z).length())
	return Vector2(atan2(-f.x, -f.z) - aim.x, rise - AIM_RISE + aim.y)


func _sync(dt: float) -> void:
	var look := _look()
	_shake = maxf(_shake - dt * 4.0, 0.0)
	var basis := Basis.from_euler(Vector3(look.y, look.x, 0.0))
	lowpoly.camera.basis = basis
	lowpoly.camera.position = sim.eye()
	hoop.position = Vector3(sim.shift(), -tuning.hoop_sink, 0.0)
	# Кольцо вздрагивает от удара мяча.
	hoop.rotation.z = sin(_time * 60.0) * _shake * 0.02
	# Бочонок в руке: при замахе уходит вниз и назад.
	var holding := sim.phase == HoopSim.Phase.AIM or sim.phase == HoopSim.Phase.CHARGE or sim.phase == HoopSim.Phase.COUNTDOWN \
			or sim.phase == HoopSim.Phase.MOVE
	hand.visible = holding
	var pull := sim.power if sim.phase == HoopSim.Phase.CHARGE else 0.0
	hand.position = Vector3(0.34, -0.36 - pull * 0.08 + sin(_time * 2.2) * 0.008, -0.8 + pull * 0.12)
	hand.rotation = Vector3(0.3 + pull * 0.5, 0.4, 0.2)
	# Бочонок в полёте.
	var flying := sim.ball != null
	ball.visible = flying
	ball_shadow.visible = flying
	if flying:
		ball.position = sim.ball.pos
		ball.rotation = Vector3(_time * 9.0, 0.0, _time * 4.0)
		ball_shadow.position = Vector3(sim.ball.pos.x, 0.07, sim.ball.pos.z)
		if sim.fire() and sim.phase == HoopSim.Phase.FLIGHT:
			_trail -= dt
			if _trail <= 0.0:
				_trail = 0.03
				_puff(sim.ball.pos, Vector3(0.0, 0.6, 0.0), HOT if _rng.randf() < 0.7 else WHITE, 0.4, 0.35)
	# Флаг: по ветру, без ветра висит.
	var cloth := flag.part(&"cloth") if not flag.pink else null
	if cloth != null:
		var wind := sim.shot().wind
		if wind == 0:
			cloth.rotation = Vector3(0.0, 0.0, -1.25)
		else:
			var dir := HoopSim.right(sim.shot(), tuning) * signf(wind)
			cloth.rotation = Vector3(0.0, atan2(-dir.z, dir.x) + sin(_time * (5.0 + absf(wind) * 2.0)) * 0.2, 0.0)
	# Клубы.
	var face := lowpoly.camera.basis.orthonormalized()
	for i in _puffs.size():
		if _puff_age[i] < 0.0:
			continue
		_puff_age[i] += dt
		var k := _puff_age[i] / _puff_life[i]
		if k >= 1.0:
			_puff_age[i] = -1.0
			_puffs[i].visible = false
			continue
		_puffs[i].position += _puff_vel[i] * dt
		_puff_vel[i] *= maxf(1.0 - 3.0 * dt, 0.0)
		var size := _puff_size[i] * (0.45 + 0.55 * minf(k * 3.0, 1.0)) * (1.0 - maxf(k - 0.6, 0.0) / 0.4)
		_puffs[i].basis = face.scaled(Vector3.ONE * maxf(size, 0.01))
		_puffs[i].visible = true


## Точка мира в пикселях экрана демки; за спиной камеры `Vector2.INF`.
func _px(p: Vector3) -> Vector2:
	var cam := lowpoly.camera
	var local := cam.basis.inverse() * (p - cam.position)
	if local.z > -0.1:
		return Vector2.INF
	var view := lowpoly.view
	var half := tan(deg_to_rad(cam.fov) / 2.0)
	return Vector2(view.x / 2.0 + local.x / -local.z / half * view.y / 2.0, view.y / 2.0 - local.y / -local.z / half * view.y / 2.0)


func _draw_hud(canvas: CanvasItem) -> void:
	if sim == null:
		return
	var dark := lowpoly.ink(LowpolyScreen.DARK).darkened(0.5)
	var red := lowpoly.ink(LowpolyScreen.DANGER)
	var gold := lowpoly.ink(LowpolyScreen.BONUS)
	var white := lowpoly.ink(LowpolyScreen.LIGHT)
	var green := Color(0.35, 0.8, 0.35)
	var view := lowpoly.view
	var shot := sim.shot()
	var aiming := sim.phase == HoopSim.Phase.AIM or sim.phase == HoopSim.Phase.CHARGE
	# Пунктир: где кольцо будет, когда долетит мяч, брошенный сейчас.
	if aiming and shot.move_amp > 0.0:
		var center := HoopSim.rim_rest(tuning) + Vector3(sim.ghost_shift(), 0.0, 0.0)
		var radius := tuning.rim_r * tuning.hoop_scale
		for k in 12:
			if k % 2 == 1:
				continue
			var a := _px(center + Vector3(sin(TAU * k / 12.0), 0.0, cos(TAU * k / 12.0)) * radius)
			var b := _px(center + Vector3(sin(TAU * (k + 1) / 12.0), 0.0, cos(TAU * (k + 1) / 12.0)) * radius)
			if a != Vector2.INF and b != Vector2.INF:
				canvas.draw_line(a, b, dark, 4.0)
				canvas.draw_line(a, b, gold if int(_time * 8.0) % 2 == 0 else white, 2.0)
	# Прицела нет: целятся видом. При ветре на высоте кольца стоят бледные деления, одно
	# деление это поправка на одну стрелку ветра.
	if aiming:
		# Прицел стоит на экране: при прицеле «в ноль» он лежит на кольце.
		var y := roundf(view.y / 2.0 - tan(AIM_RISE) / tan(deg_to_rad(lowpoly.camera.fov) / 2.0) * view.y / 2.0)
		var x := roundf(view.x / 2.0)
		var per := tan(shot.tick) / tan(deg_to_rad(lowpoly.camera.fov) / 2.0) * view.y / 2.0
		for k in range(-3, 4):
			# Деления нужны только при ветре.
			if k == 0 or shot.wind == 0:
				continue
			var tx := roundf(x + k * per)
			# Нужное деление подсвечено: против ветра на число стрелок.
			var want := shot.wind != 0 and k == -shot.wind
			canvas.draw_rect(Rect2(tx - 1.5, y - 5.0, 3.0, 10.0), Color(dark, 0.5))
			canvas.draw_rect(Rect2(tx - 0.5, y - 4.0, 1.0, 8.0), Color(gold if want else white.darkened(0.2), 0.5))
	# Ветер: стрелки сверху по центру.
	if shot.wind != 0 and sim.phase != HoopSim.Phase.DONE:
		var n := absi(shot.wind)
		var dir := signf(shot.wind)
		var text := "ВЕТЕР"
		var tw := PixelFont16.width(text, 1.0)
		var total := tw + 8.0 + n * 10.0
		var left := roundf(view.x / 2.0 - total / 2.0)
		PixelFont16.draw(canvas, Vector2(left, 30.0), text, white, white, dark, 1.0)
		for k in n:
			var cx := left + tw + 12.0 + k * 10.0
			var sway := roundf(sin(_time * 7.0 + k) * 1.0)
			for row in 5:
				var w := 5.0 - absf(row - 2.0) * 2.0
				var px := cx + sway + (w if dir > 0.0 else -w) - 2.0
				canvas.draw_rect(Rect2(px - 1.0, 31.0 + row * 2.0 - 1.0, 4.0, 4.0), dark)
			for row in 5:
				var w := 5.0 - absf(row - 2.0) * 2.0
				var px := cx + sway + (w if dir > 0.0 else -w) - 2.0
				canvas.draw_rect(Rect2(px, 31.0 + row * 2.0, 2.0, 2.0), gold)
	# Очки слева сверху.
	PixelFont16.draw(canvas, Vector2(10.0, 6.0), str(sim.score), white, gold, dark, 3.0)
	PixelFont16.draw(canvas, Vector2(12.0 + PixelFont16.width(str(sim.score), 3.0), 18.0), "/%d" % tuning.goal, white, white, dark, 1.0)
	if sim.fire() and int(_time * 6.0) % 2 == 0:
		PixelFont16.draw(canvas, Vector2(10.0, 44.0), "ГОРИТ X%d" % tuning.fire_mult, white, red, dark, 1.0)
	# Броски сверху по центру: кружки итогов.
	var count := plan.shots.size()
	for i in count:
		var o := Vector2(roundf(view.x / 2.0 - count * 6.0 + i * 12.0), 10.0)
		var color := dark.lightened(0.25)
		if i < sim.results.size():
			color = gold if sim.results[i] > 0 else red
		elif i == sim.index and int(_time * 4.0) % 2 == 0:
			color = white
		canvas.draw_rect(Rect2(o - Vector2.ONE, Vector2(10, 10)), dark)
		canvas.draw_rect(Rect2(o, Vector2(8, 8)), color)
		if plan.shots[i].points == 3:
			canvas.draw_rect(Rect2(o + Vector2(3, 3), Vector2(2, 2)), dark)
	# Шкала силы справа: зелёная зона и бегунок.
	var bar := Rect2(view.x - 26.0, 56.0, 12.0, view.y - 110.0)
	canvas.draw_rect(bar.grow(2.0), dark)
	canvas.draw_rect(bar, dark.lightened(0.2))
	var zone_top := bar.end.y - (shot.zone + shot.zone_half) * bar.size.y
	canvas.draw_rect(Rect2(bar.position.x, roundf(zone_top), bar.size.x, roundf(shot.zone_half * 2.0 * bar.size.y)), green)
	canvas.draw_rect(Rect2(bar.position.x, roundf(zone_top), 3.0, roundf(shot.zone_half * 2.0 * bar.size.y)), green.lightened(0.4))
	if sim.phase == HoopSim.Phase.CHARGE or sim.phase == HoopSim.Phase.FLIGHT or sim.phase == HoopSim.Phase.RESULT:
		var my := roundf(bar.end.y - sim.power * bar.size.y)
		canvas.draw_rect(Rect2(bar.position.x - 5.0, my - 3.0, bar.size.x + 10.0, 6.0), dark)
		canvas.draw_rect(Rect2(bar.position.x - 4.0, my - 2.0, bar.size.x + 8.0, 4.0), white)
	var worth := "%d ОЧК" % shot.points
	PixelFont16.draw(canvas, Vector2(view.x - 10.0 - PixelFont16.width(worth, 1.0), view.y - 44.0), worth, white, gold, dark, 1.0)
	# Отсчёт и итог броска.
	if sim.phase == HoopSim.Phase.COUNTDOWN:
		var text := str(ceili(sim.countdown))
		PixelFont16.draw(canvas, Vector2(roundf(view.x / 2.0 - PixelFont16.width(text, 5.0) / 2.0), roundf(view.y / 2.0 - 40.0)), text,
				white, gold, dark, 5.0)
	elif _popup_left > 0.0:
		var lift := roundf((1.0 - _popup_left / tuning.result_seconds) * 14.0)
		PixelFont16.draw(canvas, Vector2(roundf(view.x / 2.0 - PixelFont16.width(_popup, 2.0) / 2.0), roundf(view.y / 2.0 + 10.0 - lift)), _popup,
				white, gold if _popup_good else red, dark, 2.0)
