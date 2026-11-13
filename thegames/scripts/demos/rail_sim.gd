class_name RailSim
extends RefCounted
## Правила демки шутер × low poly «рельсовый тир» (#114) без окна: камера на рельсах, враги по
## расписанию маршрута, выстрелы лучом из камеры через прицел, жизни, обойма и боты. Демка
## `shooter_lowpoly.gd` рисует это состояние и озвучивает события `events`; `simulate` гоняет
## бота по сиду целиком (проверки `demo_test`, `debug/tools/dump_rail.gd`).
##
## Враг живёт по кругу: высунулся, целится (кольцо на экране сжимается), выстрелил и спрятался,
## отсиделся, высунулся снова; убить можно, пока он на виду. Метатель вместо выстрела кидает
## бутылку, её сбивают в полёте. У капитана две жизни. Пленный стоит с поднятыми руками и
## уходит сам; попадание в него стоит жизни. Бегун выбегает в переезде, стреляет раз и уходит.
## Бочка с порохом от выстрела снимает всех врагов рядом. Следующая группа выходит, когда
## перебита текущая; остановка пройдена, когда перебиты все группы.

const DT := 1.0 / 60.0

enum Phase { COUNTDOWN, HOLD, MOVE, DONE }
enum State { WAIT, RISE, OUT, DUCK, REST, DEAD, GONE }

class Actor:
	var state := State.WAIT
	var timer := 0.0
	## Насколько на виду, 0..1.
	var k := 0.0
	var hp := 1
	## Сколько секунд подряд в него можно попасть (реакция бота).
	var seen := 0.0


class Bottle:
	var from := Vector3.ZERO
	var k := 0.0


class Shot:
	## Во что попал бы выстрел: `miss`, `foe`, `bottle`, `keg`, `cover`.
	var kind := &"miss"
	var index := -1
	var point := Vector3.ZERO


var level: RailLevel
var tuning: ShooterLowpolyTuning
var phase := Phase.COUNTDOWN
var countdown := 0.0
var time := 0.0
## Остановка, на которой стоит камера или с которой уехала; в переезде `move_k` 0..1.
var stop := 0
var move_k := 0.0
var group := 0
## Время группы: меньше нуля это пауза перед ней.
var group_time := 0.0
var cam := Vector3.ZERO
var look := Vector2.ZERO
var lives := 3
var ammo := 6
var reload_left := 0.0
var fire_left := 0.0
var mercy_left := 0.0
var actors: Array[Actor] = []
var bottles: Array[Bottle] = []
var kegs_alive: Array[bool] = []
var ended := false
var finished := false
var shots := 0
var hits := 0
var kills := 0
var hostage_hits := 0
var hurts := 0
## События шага для звука и эффектов: `[имя, …]`. `go`, `pop(i)`, `shot(точка, во что)`,
## `kill(i)`, `wound(i)` (капитан ранен), `hostage(i)`, `fire(i)` (враг выстрелил), `throw(i)`,
## `smash(точка)` (бутылка сбита), `boom(бочка)`, `hurt`, `empty`, `reload`, `loaded`, `move`,
## `arrive`, `finish`, `dead`, `timeout`. Демка читает и чистит.
var events: Array[Array] = []
## Что бот хочет на этом шаге (`bot`).
var bot_aim := Vector2.ZERO
var bot_fire := false
var bot_reload := false

var _tan_half := 0.577


static func create(level_: RailLevel, tuning_: ShooterLowpolyTuning) -> RailSim:
	var sim := RailSim.new()
	sim.level = level_
	sim.tuning = tuning_
	sim.countdown = tuning_.countdown
	sim.lives = tuning_.lives
	sim.ammo = tuning_.clip
	sim._tan_half = tan(deg_to_rad(tuning_.fov) / 2.0)
	for foe in level_.foes:
		var actor := Actor.new()
		actor.hp = tuning_.captain_hp if foe.kind == RailLevel.Kind.CAPTAIN else 1
		sim.actors.append(actor)
	for keg in level_.kegs:
		sim.kegs_alive.append(true)
	sim._pose()
	return sim


## Прогон бота без окна до конца маршрута.
static func simulate(level_: RailLevel, tuning_: ShooterLowpolyTuning, mode: AutoTest.BotMode) -> RailSim:
	var sim := create(level_, tuning_)
	while not sim.ended:
		sim.bot(mode, DT)
		sim.step(DT, sim.bot_aim, sim.bot_fire, sim.bot_reload)
		sim.events.clear()
	return sim


func _pose() -> void:
	if phase == Phase.MOVE:
		cam = level.pose_pos(stop + 1, move_k)
		look = level.pose_look(stop + 1, move_k)
	else:
		cam = level.stops[stop].pos
		look = Vector2(level.stops[stop].yaw, level.stops[stop].pitch)


## Доля пути: остановки и переезды поровну.
func progress() -> float:
	var last := level.stops.size() - 1
	return clampf((stop + (move_k if phase == Phase.MOVE else 0.0)) / last, 0.0, 1.0)


## Ступни врага сейчас.
func feet(i: int) -> Vector3:
	var k := actors[i].k
	return level.foes[i].hide.lerp(level.foes[i].out, k * k * (3.0 - 2.0 * k))


func hittable(i: int) -> bool:
	var a := actors[i]
	if a.state != State.RISE and a.state != State.OUT and a.state != State.DUCK:
		return false
	return a.k >= (tuning.runner_hittable if level.foes[i].kind == RailLevel.Kind.RUNNER else tuning.hittable)


## Жив и уже вышел (для взрыва и счёта группы).
func active(i: int) -> bool:
	var s := actors[i].state
	return s == State.RISE or s == State.OUT or s == State.DUCK or s == State.REST


## Сколько осталось до выстрела врага, 0..1 (кольцо на экране); −1, если он не целится.
func ring(i: int) -> float:
	var a := actors[i]
	if a.state != State.OUT or not level.foes[i].hostile():
		return -1.0
	return clampf(1.0 - a.timer / level.foes[i].aim, 0.0, 1.0)


func bottle_pos(b: Bottle) -> Vector3:
	var p := b.from.lerp(cam, b.k)
	return p + Vector3(0.0, tuning.bottle_arc * 4.0 * b.k * (1.0 - b.k), 0.0)


func to_screen(p: Vector3) -> Vector3:
	return RailLevel.project(p, cam, look, _tan_half, tuning.aspect)


## Шаг мира: прицел в кадре (x и y от −1 до 1, y вниз), нажат ли выстрел, нажата ли перезарядка.
func step(dt: float, aim: Vector2, fire: bool, reload: bool) -> void:
	if ended:
		return
	if phase == Phase.COUNTDOWN:
		countdown -= dt
		if countdown <= 0.0:
			phase = Phase.HOLD
			events.append([&"go"])
		return
	time += dt
	mercy_left = maxf(mercy_left - dt, 0.0)
	fire_left = maxf(fire_left - dt, 0.0)
	_step_route(dt)
	_pose()
	if ended:
		return
	for i in actors.size():
		_step_actor(i, dt)
	for i in range(bottles.size() - 1, -1, -1):
		bottles[i].k += dt / tuning.bottle_flight
		if bottles[i].k >= 1.0:
			bottles.remove_at(i)
			_hurt()
	if reload_left > 0.0:
		reload_left -= dt
		if reload_left <= 0.0:
			ammo = tuning.clip
			events.append([&"loaded"])
	elif reload and ammo < tuning.clip:
		_reload()
	elif fire and fire_left <= 0.0:
		if ammo <= 0:
			events.append([&"empty"])
			_reload()
		else:
			_shoot(aim)
	if lives <= 0:
		ended = true
		events.append([&"dead"])
	elif time > tuning.max_seconds:
		ended = true
		events.append([&"timeout"])


func _reload() -> void:
	reload_left = tuning.reload
	events.append([&"reload"])


func _step_route(dt: float) -> void:
	if phase == Phase.MOVE:
		# Пока бегун на виду, камера почти стоит: по плывущей картинке в него не попасть.
		var pace := 1.0
		for i in actors.size():
			if level.foes[i].kind == RailLevel.Kind.RUNNER and level.foes[i].stop == stop + 1 \
					and (actors[i].state == State.RISE or actors[i].state == State.OUT):
				pace = tuning.runner_slow
		move_k += dt * pace / level.stops[stop + 1].travel
		for i in actors.size():
			var foe := level.foes[i]
			if actors[i].state == State.WAIT and foe.kind == RailLevel.Kind.RUNNER and foe.stop == stop + 1 and move_k >= foe.delay:
				_rise(i)
		if move_k >= 1.0:
			stop += 1
			move_k = 0.0
			if stop >= level.stops.size() - 1:
				phase = Phase.DONE
				finished = true
				ended = true
				events.append([&"finish"])
				return
			phase = Phase.HOLD
			group = 0
			group_time = 0.0
			events.append([&"arrive"])
		return
	group_time += dt
	if group_time < 0.0:
		return
	if group >= level.stops[stop].groups:
		phase = Phase.MOVE
		move_k = 0.0
		events.append([&"move"])
		return
	var left := 0
	for i in level.foes_of(stop, group):
		var a := actors[i]
		if a.state == State.WAIT and group_time >= level.foes[i].delay:
			_rise(i)
		if level.foes[i].hostile() and a.state != State.DEAD:
			left += 1
	if left == 0:
		# Группа перебита: пленные уходят, пауза, следующая группа или переезд.
		for i in level.foes_of(stop, group):
			var a := actors[i]
			if not level.foes[i].hostile():
				a.state = State.DUCK if a.state == State.RISE or a.state == State.OUT else (State.GONE if a.state == State.WAIT else a.state)
		group += 1
		group_time = -(tuning.leave_gap if group >= level.stops[stop].groups else tuning.group_gap)


func _rise(i: int) -> void:
	actors[i].state = State.RISE
	actors[i].timer = 0.0
	events.append([&"pop", i])


func _step_actor(i: int, dt: float) -> void:
	var a := actors[i]
	var foe := level.foes[i]
	var runner := foe.kind == RailLevel.Kind.RUNNER
	match a.state:
		State.RISE:
			a.k = minf(a.k + dt / (tuning.runner_run if runner else tuning.pop), 1.0)
			if a.k >= 1.0:
				a.state = State.OUT
				a.timer = 0.0
		State.OUT:
			a.timer += dt
			if a.timer >= foe.aim:
				a.state = State.DUCK
				if foe.kind == RailLevel.Kind.THROWER:
					var bottle := Bottle.new()
					bottle.from = feet(i) + Vector3(0.0, tuning.head_y, 0.0)
					bottles.append(bottle)
					events.append([&"throw", i])
				elif foe.hostile():
					events.append([&"fire", i])
					_hurt()
		State.DUCK:
			a.k = maxf(a.k - dt / (tuning.runner_run if runner else tuning.duck), 0.0)
			if a.k <= 0.0:
				a.state = State.GONE if runner or not foe.hostile() else State.REST
				a.timer = 0.0
		State.REST:
			a.timer += dt
			if a.timer >= tuning.rest:
				_rise(i)
	a.seen = a.seen + dt if hittable(i) else 0.0


func _hurt() -> void:
	if mercy_left > 0.0 or ended:
		return
	lives -= 1
	hurts += 1
	mercy_left = tuning.mercy
	events.append([&"hurt"])


## Во что попадёт выстрел через точку кадра: ближайшее по лучу.
func probe(aim: Vector2) -> Shot:
	var dir := RailLevel.ray(aim, look, _tan_half, tuning.aspect)
	var shot := Shot.new()
	var best := 120.0
	shot.point = cam + dir * 40.0
	for i in level.covers.size():
		var t := RailLevel.hit_box(cam, dir, level.covers[i].box())
		if t >= 0.0 and t < best:
			best = t
			shot.kind = &"cover"
			shot.index = i
	for i in actors.size():
		if not hittable(i):
			continue
		var at := feet(i)
		for part: Vector2 in [Vector2(tuning.torso_y, tuning.torso_r), Vector2(tuning.head_y, tuning.head_r)]:
			var pad := tuning.runner_pad if level.foes[i].kind == RailLevel.Kind.RUNNER else tuning.hit_pad
			var t := RailLevel.hit_sphere(cam, dir, at + Vector3(0.0, part.x, 0.0), part.y + pad)
			if t >= 0.0 and t < best:
				best = t
				shot.kind = &"foe"
				shot.index = i
	for i in bottles.size():
		var t := RailLevel.hit_sphere(cam, dir, bottle_pos(bottles[i]), tuning.bottle_r)
		if t >= 0.0 and t < best:
			best = t
			shot.kind = &"bottle"
			shot.index = i
	for i in level.kegs.size():
		if not kegs_alive[i]:
			continue
		var t := RailLevel.hit_sphere(cam, dir, level.kegs[i].pos + Vector3(0.0, tuning.keg_y, 0.0), tuning.keg_r)
		if t >= 0.0 and t < best:
			best = t
			shot.kind = &"keg"
			shot.index = i
	if shot.kind != &"miss":
		shot.point = cam + dir * best
	return shot


func _shoot(aim: Vector2) -> void:
	ammo -= 1
	shots += 1
	fire_left = tuning.fire_gap
	var shot := probe(aim)
	events.append([&"shot", shot.point, shot.kind])
	match shot.kind:
		&"foe":
			var i := shot.index
			if not level.foes[i].hostile():
				hostage_hits += 1
				actors[i].state = State.DUCK
				lives -= 1
				hurts += 1
				events.append([&"hostage", i])
				return
			hits += 1
			actors[i].hp -= 1
			if actors[i].hp <= 0:
				_kill(i)
			else:
				events.append([&"wound", i])
		&"bottle":
			hits += 1
			events.append([&"smash", bottle_pos(bottles[shot.index])])
			bottles.remove_at(shot.index)
		&"keg":
			hits += 1
			kegs_alive[shot.index] = false
			var keg := level.kegs[shot.index]
			events.append([&"boom", shot.index])
			for i in actors.size():
				if level.foes[i].hostile() and active(i) and level.foes[i].hide.distance_to(keg.pos) <= keg.radius + 1.0:
					_kill(i)


func _kill(i: int) -> void:
	actors[i].state = State.DEAD
	actors[i].timer = 0.0
	kills += 1
	events.append([&"kill", i])


## Сколько врагов бочка сняла бы сейчас.
func keg_reach(k: int) -> int:
	var n := 0
	for i in actors.size():
		if level.foes[i].hostile() and active(i) and level.foes[i].hide.distance_to(level.kegs[k].pos) <= level.kegs[k].radius + 1.0:
			n += 1
	return n


## Бот решает на шаг вперёд. WIN: ведёт прицел к самой срочной цели (бутылка в полёте, бочка с
## порохом рядом с двумя врагами, враг, у которого кольцо сомкнётся раньше), стреляет, когда
## выстрел точно придётся в неё, перезаряжается на пустой обойме и в затишье. В пленных не
## стреляет. LOSE стоит и не стреляет.
func bot(mode: AutoTest.BotMode, dt: float) -> void:
	bot_fire = false
	bot_reload = false
	if ended or mode != AutoTest.BotMode.WIN or phase == Phase.COUNTDOWN:
		return
	# Цели: срочность (секунды до беды), точка в мире, вид, номер.
	var best_urgency := INF
	var best_aim := Vector2.ZERO
	var best_kind := &""
	var best_index := -1
	for i in bottles.size():
		var urgency := (1.0 - bottles[i].k) * tuning.bottle_flight
		var at := to_screen(bottle_pos(bottles[i]))
		if bottles[i].k > 0.12 and urgency < best_urgency and at.z > 0.0:
			best_urgency = urgency
			best_aim = Vector2(at.x, at.y)
			best_kind = &"bottle"
			best_index = i
	for i in level.kegs.size():
		if kegs_alive[i] and phase == Phase.HOLD and level.kegs[i].stop == stop and keg_reach(i) >= 2 and 0.4 < best_urgency:
			var at := to_screen(level.kegs[i].pos + Vector3(0.0, tuning.keg_y, 0.0))
			if probe(Vector2(at.x, at.y)).kind == &"keg":
				best_urgency = 0.4
				best_aim = Vector2(at.x, at.y)
				best_kind = &"keg"
				best_index = i
	for i in actors.size():
		var a := actors[i]
		if not level.foes[i].hostile() or not hittable(i) or a.state == State.DUCK or a.seen < tuning.bot_react:
			continue
		var urgency := level.foes[i].aim - a.timer if a.state == State.OUT else level.foes[i].aim + 0.3
		if level.foes[i].kind == RailLevel.Kind.THROWER:
			urgency += tuning.bottle_flight
		if urgency >= best_urgency:
			continue
		# В туловище, а если оно закрыто, в голову.
		for y: float in [tuning.torso_y, tuning.head_y]:
			var at := to_screen(feet(i) + Vector3(0.0, y, 0.0))
			var shot := probe(Vector2(at.x, at.y))
			# Бочка с порохом на линии огня тоже годится: взрыв снимет врага за ней.
			if at.z > 0.0 and ((shot.kind == &"foe" and shot.index == i) or shot.kind == &"keg"):
				best_urgency = urgency
				best_aim = Vector2(at.x, at.y)
				best_kind = shot.kind
				best_index = shot.index
				break
	if ammo <= 0:
		bot_reload = true
	if best_index < 0:
		bot_reload = bot_reload or ammo < tuning.clip
		bot_aim = bot_aim.move_toward(Vector2.ZERO, tuning.bot_speed * 0.3 * dt)
		return
	bot_aim = bot_aim.move_toward(best_aim, tuning.bot_speed * dt)
	if bot_aim.distance_to(best_aim) <= tuning.bot_tolerance and reload_left <= 0.0 and ammo > 0:
		var shot := probe(bot_aim)
		bot_fire = shot.kind == best_kind and shot.index == best_index and not _hostage_on_line(bot_aim)


## Есть ли на линии огня пленный этой остановки, который на виду или вот-вот высунется.
func _hostage_on_line(aim: Vector2) -> bool:
	var dir := RailLevel.ray(aim, look, _tan_half, tuning.aspect)
	for i in actors.size():
		var foe := level.foes[i]
		if foe.hostile() or foe.stop != stop or foe.group != group or actors[i].state == State.GONE or actors[i].state == State.DEAD:
			continue
		if actors[i].state == State.WAIT and group_time < foe.delay - 0.1:
			continue
		for at: Vector3 in [feet(i), foe.out]:
			for part: Vector2 in [Vector2(tuning.torso_y, tuning.torso_r), Vector2(tuning.head_y, tuning.head_r)]:
				if RailLevel.hit_sphere(cam, dir, at + Vector3(0.0, part.x, 0.0), part.y + tuning.hit_pad + 0.1) >= 0.0:
					return true
	return false
