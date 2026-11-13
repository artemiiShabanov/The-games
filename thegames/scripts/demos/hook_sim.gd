class_name HookSim
extends RefCounted
## Правила демки платформер × «продвинутые» «крюк-кошка» (#121) без окна: свободный бег по
## островам, прыжок, уступы, крюк за кольцо, качание на верёвке, полёт, жизни и боты. Демка
## `platformer_threed.gd` рисует это состояние и озвучивает события `events`; `simulate` гоняет
## бота по сиду целиком (проверки `demo_test`, `debug/tools/dump_hook.gd`).
##
## Герой это точка ступней `pos` со скоростью `vel` в мире. Ход задаётся направлением в мире
## (демка считает его от камеры), герой поворачивается к ходу. Острова и реквизит это столбы:
## на верх можно встать, в бок упираешься. В воздухе герой рулит; долетев до стены острова, чей
## край не выше `climb_reach` над ступнями, цепляется руками и забирается. Зажатый крюк берёт
## ближайшее кольцо впереди по взгляду, до которого достаёт верёвка; на верёвке герой
## качается (верёвка не даёт уйти дальше своей длины, слабину не держит), отпущенный летит по
## касательной. Вода стоит жизни и возвращает на последний остров. Цель: остров с маяком.

const DT := 1.0 / 60.0
## Высота, на которую герой шагает без прыжка; зазор до стены.
const STEP := 0.3
const BODY := 0.3

enum Phase { COUNTDOWN, PLAY, DONE }
enum Mode { GROUND, AIR, SWING, CLIMB, DOWN }

var level: HookLevel
var tuning: PlatformerThreedTuning
var phase := Phase.COUNTDOWN
var countdown := 0.0
var time := 0.0
var mode := Mode.GROUND
var pos := Vector3.ZERO
var vel := Vector3.ZERO
## Куда смотрит герой (курс: 0 это −z) и куда смотрит камера (единичный x, z): крюк выбирает
## кольцо по взгляду.
var facing := 0.0
var aim := Vector2(0.0, -1.0)
## Кольцо, на котором висит герой, и длина верёвки.
var ring := -1
var rope := 5.0
## Последнее кольцо и сколько секунд за него ещё не зацепиться.
var last_ring := -1
var rehook_left := 0.0
## Самый дальний остров, на котором герой стоял, и остров под ногами сейчас.
var islet := 0
var ground := 0
## Куда возвращает вода.
var safe := Vector3.ZERO
var lives := 3
var down_left := 0.0
## Уступ: откуда и куда герой забирается, сколько осталось.
var climb_from := Vector3.ZERO
var climb_to := Vector3.ZERO
var climb_left := 0.0
var ended := false
var finished := false
var hooks := 0
var climbs := 0
var jumps := 0
var falls := 0
var water := -5.0
## События шага для звука и эффектов: `[имя, …]`. `go`, `jump`, `hook(кольцо)`, `release`,
## `grab`, `climb`, `land(остров)`, `splash`, `respawn`, `finish`, `dead`, `timeout`.
var events: Array[Array] = []
## Что бот хочет на этом шаге (`bot`).
var bot_move := Vector2.ZERO
var bot_jump := false
var bot_hook := false

## Баги (#126): множитель прыжка и скорости качания (дикая физика); сколько секунд кольцо
## держит героя, 0 вечно (кольца от чиха отваливаются); какие кольца уже отвалились.
var jump_mult := 1.0
var swing_mult := 1.0
var ring_hold := 0.0
var snapped: Array[int] = []
var hang_time := 0.0

var _armed := true
var _coyote := 0.0
var _jump_buf := 0.0
var _wall := -1
var _bot_wait := false
var _bot_lined := false


static func create(level_: HookLevel, tuning_: PlatformerThreedTuning) -> HookSim:
	var sim := HookSim.new()
	sim.level = level_
	sim.tuning = tuning_
	sim.countdown = tuning_.countdown
	sim.lives = tuning_.lives
	sim.water = level_.water_y(tuning_.water_drop)
	var first := level_.islets[0]
	var dir := level_.gaps[0].dir
	sim.pos = first.pos - Vector3(dir.x, 0.0, dir.y) * first.radius * 0.45
	sim.safe = sim.pos
	sim.facing = atan2(-dir.x, -dir.y)
	sim.aim = dir
	return sim


## Прогон бота без окна до конца уровня.
static func simulate(level_: HookLevel, tuning_: PlatformerThreedTuning, mode_: AutoTest.BotMode) -> HookSim:
	var sim := create(level_, tuning_)
	while not sim.ended:
		sim.bot(mode_)
		sim.step(DT, sim.bot_move, sim.bot_jump, sim.bot_hook)
		sim.events.clear()
	return sim


func progress() -> float:
	var n := level.gaps.size()
	if islet >= n:
		return 1.0
	var a := level.islets[islet].pos
	var b := level.islets[islet + 1].pos
	var ab := Vector2(b.x - a.x, b.z - a.z)
	var k := clampf(Vector2(pos.x - a.x, pos.z - a.z).dot(ab) / maxf(ab.length_squared(), 0.01), 0.0, 0.95)
	return (islet + k) / n


func ring_pos(i: int, at := -1.0) -> Vector3:
	return level.ring_pos(i, time if at < 0.0 else at)


## Кольцо, за которое крюк зацепится сейчас, или −1: в досягаемости верёвки, выше героя, не
## за спиной взгляда; из нескольких ближнее, с поправкой на взгляд.
func target() -> int:
	var best := -1
	var best_score := INF
	for i in level.rings.size():
		if (i == last_ring and rehook_left > 0.0) or snapped.has(i):
			continue
		var p := ring_pos(i)
		var d := p.distance_to(pos)
		if d > tuning.rope_max or p.y < pos.y + 1.0:
			continue
		var flat := Vector2(p.x - pos.x, p.z - pos.z)
		var facing_k := flat.normalized().dot(aim) if flat.length() > 1.0 else 1.0
		if facing_k < -0.2:
			continue
		var score := d * (1.4 - 0.4 * facing_k)
		if score < best_score:
			best = i
			best_score = score
	return best


## Шаг мира: ход (x, z в мире, длина до 1), нажат ли прыжок на этом шаге, зажат ли крюк.
func step(dt: float, move: Vector2, jump: bool, hook: bool) -> void:
	if ended:
		return
	if phase == Phase.COUNTDOWN:
		countdown -= dt
		if countdown <= 0.0:
			phase = Phase.PLAY
			events.append([&"go"])
		return
	time += dt
	rehook_left = maxf(rehook_left - dt, 0.0)
	_jump_buf = tuning.jump_buffer if jump else maxf(_jump_buf - dt, 0.0)
	_coyote = maxf(_coyote - dt, 0.0)
	if not hook:
		_armed = true
	move = move.limit_length(1.0)
	match mode:
		Mode.GROUND:
			_ground(dt, move)
		Mode.AIR:
			_air(dt, move, hook)
		Mode.SWING:
			_swing(dt, move, hook)
		Mode.CLIMB:
			climb_left -= dt
			var k := clampf(1.0 - climb_left / tuning.climb_seconds, 0.0, 1.0)
			# Сначала вверх по стене, потом вперёд на край.
			pos = Vector3(lerpf(climb_from.x, climb_to.x, smoothstep(0.45, 1.0, k)), lerpf(climb_from.y, climb_to.y, smoothstep(0.0, 0.7, k)),
					lerpf(climb_from.z, climb_to.z, smoothstep(0.45, 1.0, k)))
			if climb_left <= 0.0:
				pos = climb_to
				vel = Vector3.ZERO
				events.append([&"climb"])
				_land(_wall)
		Mode.DOWN:
			down_left -= dt
			if down_left <= 0.0:
				pos = safe
				vel = Vector3.ZERO
				mode = Mode.GROUND
				events.append([&"respawn"])
	if not ended and time > tuning.max_seconds:
		ended = true
		phase = Phase.DONE
		events.append([&"timeout"])


## Самый высокий верх под точкой не выше `feet`: остров или вещь. Нет опоры: −INF. Номер
## острова опоры остаётся в `_floor_islet`.
var _floor_islet := -1

func _floor(x: float, z: float, feet: float) -> float:
	var best := -INF
	_floor_islet = -1
	for i in level.islets.size():
		var it := level.islets[i]
		if it.pos.y <= feet and it.pos.y > best and it.holds(x, z):
			best = it.pos.y
			_floor_islet = i
	for p in level.props:
		var top := p.pos.y + p.height
		if top <= feet and top > best and Vector2(x - p.pos.x, z - p.pos.z).length() <= p.radius:
			best = top
			_floor_islet = p.islet
	return best


## Вытолкнуть героя из стен островов и из вещей, верх которых выше ступней. Стена острова,
## в которую герой упёрся, остаётся в `_wall`.
func _push_out(feet: float) -> void:
	_wall = -1
	for i in level.islets.size():
		var it := level.islets[i]
		if feet >= it.pos.y - 0.02:
			continue
		var d := Vector2(pos.x - it.pos.x, pos.z - it.pos.z)
		var edge := it.radius_at(atan2(d.y, d.x)) + BODY
		if d.length() < edge and d.length() > 0.01:
			var n := d.normalized()
			pos.x = it.pos.x + n.x * edge
			pos.z = it.pos.z + n.y * edge
			var inward := vel.x * n.x + vel.z * n.y
			if inward < 0.0:
				vel.x -= n.x * inward
				vel.z -= n.y * inward
			_wall = i
	for p in level.props:
		if feet >= p.pos.y + p.height - 0.02 or feet < p.pos.y - 2.0:
			continue
		var d := Vector2(pos.x - p.pos.x, pos.z - p.pos.z)
		var edge := p.radius + BODY
		if d.length() < edge and d.length() > 0.01:
			var n := d.normalized()
			pos.x = p.pos.x + n.x * edge
			pos.z = p.pos.z + n.y * edge
			var inward := vel.x * n.x + vel.z * n.y
			if inward < 0.0:
				vel.x -= n.x * inward
				vel.z -= n.y * inward


func _turn(dt: float, dir: Vector2) -> void:
	if dir.length() > 0.2:
		facing = rotate_toward(facing, atan2(-dir.x, -dir.y), tuning.turn_speed * dt)


func _ground(dt: float, move: Vector2) -> void:
	var flat := Vector2(vel.x, vel.z).move_toward(move * tuning.run_speed, tuning.run_accel * dt)
	vel = Vector3(flat.x, 0.0, flat.y)
	_turn(dt, move)
	pos.x += vel.x * dt
	pos.z += vel.z * dt
	_push_out(pos.y)
	var top := _floor(pos.x, pos.z, pos.y + STEP)
	if top < pos.y - STEP:
		# Сошёл с края: прыжок ещё доступен мгновение.
		mode = Mode.AIR
		_coyote = tuning.coyote
	else:
		pos.y = top
		if _floor_islet >= 0:
			ground = _floor_islet
	if _jump_buf > 0.0:
		_jump()


func _jump() -> void:
	mode = Mode.AIR
	vel.y = tuning.jump_speed * jump_mult
	_jump_buf = 0.0
	_coyote = 0.0
	jumps += 1
	events.append([&"jump"])


func _air(dt: float, move: Vector2, hook: bool) -> void:
	if _jump_buf > 0.0 and _coyote > 0.0:
		_jump()
	var before := pos.y
	vel.y -= tuning.gravity * dt
	# Руление: быстрее бега (или уже набранной скорости) не разгоняет.
	var flat := Vector2(vel.x, vel.z)
	var cap := maxf(flat.length(), tuning.run_speed)
	flat = (flat + move * tuning.air_accel * dt).limit_length(cap)
	vel.x = flat.x
	vel.z = flat.y
	_turn(dt, move if move.length() > 0.2 else flat.normalized() * minf(flat.length() / 2.0, 1.0))
	pos += vel * dt
	_push_out(maxf(before, pos.y))
	if _wall >= 0 and _grab(_wall):
		return
	if vel.y <= 0.0:
		var top := _floor(pos.x, pos.z, before + 0.05)
		if top > -INF and pos.y <= top:
			pos.y = top
			_land(_floor_islet)
			return
	if pos.y < water:
		_fall()
		return
	if hook and _armed:
		_try_hook(move)


## Край острова `i` в досягаемости рук: герой повисает на нём и забирается.
func _grab(i: int) -> bool:
	var it := level.islets[i]
	var up := it.pos.y - pos.y
	if up < 0.2 or up > tuning.climb_reach or vel.y < -6.5:
		return false
	var inward := Vector2(it.pos.x - pos.x, it.pos.z - pos.z).normalized()
	mode = Mode.CLIMB
	ring = -1
	climb_from = pos
	climb_to = Vector3(pos.x + inward.x * (BODY + 0.7), it.pos.y, pos.z + inward.y * (BODY + 0.7))
	climb_left = tuning.climb_seconds
	vel = Vector3.ZERO
	facing = atan2(-inward.x, -inward.y)
	_wall = i
	climbs += 1
	events.append([&"grab"])
	return true


func _try_hook(move: Vector2) -> void:
	var i := target()
	if i < 0:
		return
	var p := ring_pos(i)
	var to_ring := p - pos
	ring = i
	rope = clampf(to_ring.length(), tuning.rope_min, tuning.rope_max)
	# Скорость вдоль дуги в сторону кольца; если разбега мало, качание добирает её само.
	var up := to_ring.normalized()
	var flat := Vector3(to_ring.x, 0.0, to_ring.z)
	if flat.length() < 0.5:
		flat = Vector3(move.x, 0.0, move.y) if move.length() > 0.2 else Vector3(-sin(facing), 0.0, -cos(facing))
	var forward := flat - up * flat.dot(up)
	if forward.length() > 0.01:
		forward = forward.normalized()
		var tangent := vel - up * vel.dot(up)
		var along := tangent.dot(forward)
		if along < tuning.swing_min * swing_mult:
			tangent += forward * (tuning.swing_min * swing_mult - along)
		vel = tangent
	mode = Mode.SWING
	hang_time = 0.0
	_armed = false
	hooks += 1
	events.append([&"hook", i])


func _swing(dt: float, move: Vector2, hook: bool) -> void:
	var before := pos.y
	var p := ring_pos(ring)
	vel.y -= tuning.gravity * dt
	# Подкачка ходом вдоль дуги.
	var up := (p - pos).normalized()
	var push := Vector3(move.x, 0.0, move.y)
	vel += (push - up * push.dot(up)) * tuning.swing_accel * dt
	pos += vel * dt
	# Верёвка: дальше своей длины не пускает.
	var out := pos - p
	if out.length() > rope:
		var n := out.normalized()
		pos = p + n * rope
		var radial := vel.dot(n)
		if radial > 0.0:
			vel -= n * radial
	var flat := Vector2(vel.x, vel.z)
	_turn(dt, flat.normalized() * minf(flat.length() / 2.0, 1.0))
	_push_out(maxf(before, pos.y))
	if _wall >= 0 and _grab(_wall):
		last_ring = -1
		return
	if vel.y <= 0.0:
		var top := _floor(pos.x, pos.z, before + 0.05)
		if top > -INF and pos.y <= top:
			pos.y = top
			ring = -1
			_land(_floor_islet)
			return
	if pos.y < water:
		ring = -1
		_fall()
		return
	hang_time += dt
	var snap := ring_hold > 0.0 and hang_time >= ring_hold
	if snap:
		# Кольцо от чиха: отваливается под героем и больше не держит.
		snapped.append(ring)
		events.append([&"snap", ring])
	if not hook or snap:
		# Отпустил: летит по касательной.
		last_ring = ring
		rehook_left = tuning.rehook
		ring = -1
		vel *= tuning.release_boost
		mode = Mode.AIR
		events.append([&"release"])


func _land(i: int) -> void:
	mode = Mode.GROUND
	ring = -1
	vel.y = 0.0
	var flat := Vector2(vel.x, vel.z).limit_length(tuning.run_speed)
	vel.x = flat.x
	vel.z = flat.y
	last_ring = -1
	if i < 0:
		return
	if i != ground:
		events.append([&"land", i])
	ground = i
	islet = maxi(islet, i)
	# Вода возвращает сюда: место посадки, сдвинутое от края.
	var it := level.islets[i]
	var d := Vector2(pos.x - it.pos.x, pos.z - it.pos.z)
	var keep := minf(d.length(), maxf(it.radius_at(atan2(d.y, d.x)) - 1.0, 0.0))
	var at := d.normalized() * keep if d.length() > 0.01 else Vector2.ZERO
	safe = Vector3(it.pos.x + at.x, it.pos.y, it.pos.z + at.y)
	if i >= level.islets.size() - 1:
		finished = true
		ended = true
		phase = Phase.DONE
		events.append([&"finish"])


func _fall() -> void:
	falls += 1
	lives -= 1
	events.append([&"splash"])
	if lives <= 0:
		ended = true
		phase = Phase.DONE
		events.append([&"dead"])
		return
	mode = Mode.DOWN
	down_left = tuning.respawn_seconds
	vel = Vector3.ZERO


# --- Боты ------------------------------------------------------------------------------------

## Что будет, если лететь без крюка и руления из точки с такой скоростью: остров, на который
## герой сядет с запасом (номер ≥ 0), или кольцо своей пропасти, до которого дотянется верёвка
## (−2 − номер), или −1.
func flight(p0: Vector3, v0: Vector3, from_ring: int) -> int:
	var p := p0
	var v := v0
	var at := time
	var h := DT * 2.0
	var gap := mini(ground, level.gaps.size() - 1)
	var to := level.islets[gap + 1]
	for k in 150:
		var before := p.y
		v.y -= tuning.gravity * h
		p += v * h
		at += h
		if p.y < water:
			return -1
		for i in level.rings.size():
			if i <= from_ring or level.rings[i].gap != gap:
				continue
			var r := ring_pos(i, at)
			# До кольца достаёт верёвка, герой ниже него и ещё не пролетел.
			var ahead := Vector2(r.x - p.x, r.z - p.z).dot(level.gaps[gap].dir)
			if ahead > -0.6 and r.y - p.y > 1.6 and r.distance_to(p) <= tuning.rope_max - tuning.bot_margin and at - time > tuning.rehook * 0.3:
				return -2 - i
		if to.holds(p.x, p.z, -tuning.bot_margin):
			if v.y <= 0.0 and before >= to.pos.y and p.y <= to.pos.y:
				return gap + 1
		if to.holds(p.x, p.z, BODY) and p.y < to.pos.y:
			return -1
	return -1



## Бот решает на шаг вперёд. WIN: выходит на прямую к отрыву, прыгает с края; простой прыжок
## и уступ дорулит в воздухе, на кольцах цепляется и отпускает в тот миг, когда полёт без
## крюка приведёт на следующий остров или к следующему кольцу цепочки. LOSE бежит вперёд без
## прыжка и крюка и падает.
func bot(mode_: AutoTest.BotMode) -> void:
	bot_move = Vector2.ZERO
	bot_jump = false
	bot_hook = false
	if ended or mode_ == AutoTest.BotMode.OFF or phase != Phase.PLAY:
		return
	var g := mini(ground, level.gaps.size() - 1)
	var gap := level.gaps[g]
	var dir := gap.dir
	aim = dir
	var here := Vector2(pos.x, pos.z)
	var a := Vector2(gap.a.x, gap.a.z)
	if mode_ != AutoTest.BotMode.WIN:
		bot_move = (a + dir * 3.0 - here).normalized()
		return
	var to := level.islets[g + 1]
	var along := (here - a).dot(dir)
	var side := (here - a).dot(Vector2(-dir.y, dir.x))
	match mode:
		Mode.GROUND:
			if ground >= level.islets.size() - 1:
				return
			# Сначала на прямую перед отрывом, потом по ней к краю.
			var line := HookLevelGen.lineup(level, g)
			var line_at := Vector2(line.x, line.z)
			if not _bot_lined and (absf(side) < 0.3 and along > -6.0 or here.distance_to(line_at) < 0.35):
				_bot_lined = true
			if _bot_lined:
				bot_move = (a + dir * 2.0 - here).normalized()
				bot_jump = along >= -0.3
			else:
				bot_move = (line_at - here).normalized()
		Mode.AIR:
			_bot_lined = false
			if gap.kind == HookLevel.Kind.RINGS and last_ring < 0 and along < gap.length() * 0.5:
				# До первого кольца: вперёд, крюк как только достаёт.
				bot_move = dir
			else:
				bot_move = _steer(to, dir)
			# После отпускания кнопка один шаг отпущена, потом снова зажата: крюк берёт кольцо.
			bot_hook = not _bot_wait and gap.kind == HookLevel.Kind.RINGS and target() >= 0
			_bot_wait = false
			# Если полёт и так приведёт на остров, крюк не нужен.
			if bot_hook and flight(pos, vel, 9999) >= 0:
				bot_hook = false
		Mode.SWING:
			bot_hook = true
			bot_move = dir
			var p := ring_pos(ring)
			var past := (here - Vector2(p.x, p.z)).dot(dir)
			if past > 0.5 and vel.y > 0.0:
				var out := flight(pos, vel * tuning.release_boost, ring)
				if out >= 0 or out <= -2:
					bot_hook = false
					_bot_wait = true


## Руление в воздухе к точке посадки на острове `to`: нужная скорость по оставшемуся времени
## полёта.
func _steer(to: HookLevel.Islet, dir: Vector2) -> Vector2:
	var deep := minf(1.4, to.radius * 0.6)
	var spot := Vector2(to.pos.x, to.pos.z) - dir * (to.edge(-dir) - deep)
	var drop := pos.y - to.pos.y
	# Время до высоты острова по баллистике.
	var disc := vel.y * vel.y + 2.0 * tuning.gravity * maxf(drop, 0.0)
	var left := maxf((vel.y + sqrt(disc)) / tuning.gravity, 0.12)
	var want := (spot - Vector2(pos.x, pos.z)) / left
	return ((want - Vector2(vel.x, vel.z)) / 2.5).limit_length(1.0)
