class_name OutpostSim
extends RefCounted
## Правила демки шутер × «продвинутые» «оборона аванпоста» (#123) без окна. Герой стоит на
## настиле вышки, ходит по нему и стреляет из револьвера, куда смотрит; враги волнами идут к
## вышке с трёх сторон, встают у неё и бьют. Демка `shooter_threed.gd` рисует это состояние и
## озвучивает события `events`; `simulate` гоняет бота по сиду целиком (проверки `demo_test`,
## `debug/tools/dump_outpost.gd`).
##
## Выстрел это луч из глаз: попадает в ближайшее из тел, голов, щитов, бутылок и бочек; настил
## под ногами луч не пропускает, поэтому к врагу у вышки надо подойти к краю с его стороны.
## Бегун быстрый и падает с одной пули. Щитоносца спереди закрывает щит: бить в голову над
## щитом или в тело, когда он замахнулся. Метатель встаёт вдалеке и кидает бутылки: бутылку
## можно сбить или отойти от места, куда она летит. Великан держит много пуль, голова на
## замахе его слабое место. Бочка с порохом взрывается от пули и бьёт всех рядом. Барабан на
## шесть, запас при себе конечный, пополняется у ящика на настиле.

const DT := 1.0 / 60.0

enum Phase { COUNTDOWN, PLAY, DONE }
enum State { WALK, ATTACK, DEAD }

class Foe:
	var kind := OutpostPlan.Kind.RUNNER
	var pos := Vector2.ZERO
	var hp := 1
	var state := State.WALK
	var stop := 8.0
	var speed := 4.0
	## До удара; у щитоносца и великана последние `windup` секунд это замах.
	var cooldown := 0.0
	var gap := 2.0
	var windup := 0.0
	var damage := 5
	var scale := 1.0
	var wave := 0
	var walked := 0.0
	## Секунд с гибели и со свежего попадания (картинка).
	var dead_for := 0.0
	var hit_for := 9.0

	func winding() -> bool:
		return state == State.ATTACK and windup > 0.0 and cooldown <= windup


class Bottle:
	var from := Vector3.ZERO
	var to := Vector3.ZERO
	var age := 0.0
	var seconds := 1.9

	## Где бутылка сейчас: дуга от руки метателя к настилу.
	func at() -> Vector3:
		var k := clampf(age / seconds, 0.0, 1.0)
		var p := from.lerp(to, k)
		p.y += 6.0 * 4.0 * k * (1.0 - k)
		return p


var plan: OutpostPlan
var tuning: ShooterThreedTuning
var phase := Phase.COUNTDOWN
var countdown := 0.0
var time := 0.0
## Герой на настиле (x, z), куда смотрит (курс: 0 это −z, плюс влево; наклон плюс вверх).
var pos := Vector2.ZERO
var yaw := 0.0
var pitch := 0.0
var health := 100
var clip := 6
var reserve := 18
var reload_left := 0.0
var fire_wait := 0.0
var crate_left := 0.0
var foes: Array[Foe] = []
var bottles: Array[Bottle] = []
var kegs_alive: Array[bool] = []
var wave := 0
var wave_time := 0.0
var lull := 0.0
var _spawned := 0
var ended := false
var won := false
var shots := 0
var hits := 0
var kills := 0
var blocked := 0
var booms := 0
var popped := 0
var refills := 0
## События шага: `[имя, …]`. `go`, `wave(номер)`, `shot(куда попал луч)`, `hit(враг, в голову
## ли)`, `kill(враг)`, `block(враг)`, `boom(бочка)`, `pop(место)`, `throw(враг)`,
## `splash(место, задело ли)`, `hurt(урон, курс на врага)`, `reload`, `reloaded`, `empty`,
## `refill`, `win`, `dead`, `timeout`.
var events: Array[Array] = []
## Что бот хочет на этом шаге (`bot`).
## Баги (#126): множитель скорости врагов (дикая физика; отдачу прицела делает демка); каждая
## такая по счёту пуля проходит сквозь врагов, 0 нет (сквозь врагов); во сколько раз шире
## попадание по врагу (от чиха: падает от пули рядом); врагов не убить (недостижимая цель).
var foe_speed_mult := 1.0
var pass_every := 0
var near_mult := 1.0
var immortal := false
var bot_move := Vector2.ZERO
var bot_yaw := 0.0
var bot_pitch := 0.0
var bot_fire := false
var bot_reload := false
var _bot_wait := 0.0


static func create(plan_: OutpostPlan, tuning_: ShooterThreedTuning) -> OutpostSim:
	var sim := OutpostSim.new()
	sim.plan = plan_
	sim.tuning = tuning_
	sim.countdown = tuning_.countdown
	sim.health = tuning_.health
	sim.clip = tuning_.clip
	sim.reserve = tuning_.reserve
	sim.yaw = plan_.sides[0]
	sim.bot_yaw = sim.yaw
	for k in plan_.kegs:
		sim.kegs_alive.append(true)
	return sim


## Прогон бота без окна до конца обороны.
static func simulate(plan_: OutpostPlan, tuning_: ShooterThreedTuning, mode: AutoTest.BotMode) -> OutpostSim:
	var sim := create(plan_, tuning_)
	while not sim.ended:
		sim.bot(mode, DT)
		sim.step(DT, sim.bot_move, sim.bot_yaw, sim.bot_pitch, sim.bot_fire, sim.bot_reload)
		sim.events.clear()
	return sim


func eye() -> Vector3:
	return Vector3(pos.x, tuning.deck_height + tuning.eye, pos.y)


static func aim_dir(yaw_: float, pitch_: float) -> Vector3:
	return Vector3(-sin(yaw_) * cos(pitch_), sin(pitch_), -cos(yaw_) * cos(pitch_))


func alive() -> int:
	var n := 0
	for f in foes:
		n += 1 if f.state != State.DEAD else 0
	return n


func left_total() -> int:
	return plan.total() - kills


func body_of(f: Foe) -> Vector3:
	return Vector3(f.pos.x, tuning.body_height * f.scale, f.pos.y)


func head_of(f: Foe) -> Vector3:
	return Vector3(f.pos.x, tuning.head_height * f.scale, f.pos.y)


## Щит: шар перед телом со стороны вышки; на замахе щит убран.
func shield_of(f: Foe) -> Vector3:
	var toward := (pos - f.pos).normalized()
	return Vector3(f.pos.x + toward.x * 0.5, 0.95, f.pos.y + toward.y * 0.5)


func keg_at(i: int) -> Vector3:
	return Vector3(plan.kegs[i].x, 0.5, plan.kegs[i].y)


## Виден ли из глаз героя луч в сторону `dir`: настил под ногами его не пропускает.
func clear_of_deck(from: Vector3, dir: Vector3) -> bool:
	if dir.y >= -0.001:
		return true
	var t := (tuning.deck_height - from.y) / dir.y
	var cross := from + dir * t
	return Vector2(cross.x, cross.z).length() > tuning.deck_radius


static func _ray_sphere(from: Vector3, dir: Vector3, center: Vector3, radius: float) -> float:
	var to := center - from
	var along := to.dot(dir)
	if along <= 0.0:
		return INF
	var miss := to.length_squared() - along * along
	if miss > radius * radius:
		return INF
	return along - sqrt(radius * radius - miss)


## Шаг мира: шаг героя (x стрейф, y вперёд), курс и наклон взгляда, нажат ли выстрел на этом
## шаге, нажата ли перезарядка.
func step(dt: float, move: Vector2, yaw_: float, pitch_: float, fire: bool, reload: bool) -> void:
	if ended:
		return
	yaw = yaw_
	pitch = clampf(pitch_, -1.4, 1.2)
	if phase == Phase.COUNTDOWN:
		countdown -= dt
		if countdown <= 0.0:
			phase = Phase.PLAY
			events.append([&"go"])
			events.append([&"wave", 0])
		return
	time += dt
	fire_wait = maxf(fire_wait - dt, 0.0)
	# Шаг по настилу.
	move = move.limit_length(1.0)
	var fwd := Vector2(-sin(yaw), -cos(yaw))
	pos += (fwd * move.y + Vector2(-fwd.y, fwd.x) * move.x) * tuning.walk_speed * dt
	pos = pos.limit_length(tuning.deck_radius - tuning.deck_margin)
	# Барабан и ящик.
	if reload_left > 0.0:
		reload_left -= dt
		if reload_left <= 0.0:
			var take := mini(tuning.clip - clip, reserve)
			clip += take
			reserve -= take
			events.append([&"reloaded"])
	elif (reload and clip < tuning.clip or clip == 0) and reserve > 0:
		reload_left = tuning.reload_seconds
		events.append([&"reload"])
	if pos.distance_to(plan.crate) <= tuning.crate_reach and reserve < tuning.reserve_max:
		crate_left += dt
		if crate_left >= tuning.crate_seconds:
			crate_left = 0.0
			reserve = tuning.reserve_max
			refills += 1
			events.append([&"refill"])
	else:
		crate_left = 0.0
	if fire and fire_wait <= 0.0 and reload_left <= 0.0:
		if clip > 0:
			_shoot()
		else:
			events.append([&"empty"])
	_step_waves(dt)
	for f in foes:
		_step_foe(f, dt)
	_step_bottles(dt)
	if health <= 0:
		ended = true
		phase = Phase.DONE
		events.append([&"dead"])
	elif wave >= plan.waves.size() - 1 and _spawned >= plan.waves[wave].spawns.size() and alive() == 0 and bottles.is_empty():
		won = true
		ended = true
		phase = Phase.DONE
		events.append([&"win"])
	elif time > tuning.max_seconds:
		ended = true
		phase = Phase.DONE
		events.append([&"timeout"])


func _step_waves(dt: float) -> void:
	var now := plan.waves[wave]
	wave_time += dt
	while _spawned < now.spawns.size() and now.spawns[_spawned].at <= wave_time:
		_spawn(now.spawns[_spawned])
		_spawned += 1
	if _spawned < now.spawns.size() or wave >= plan.waves.size() - 1:
		return
	# Следующая волна: когда эта перебита (с короткой передышкой) или слишком затянулась.
	if alive() == 0:
		lull += dt
	if lull >= tuning.wave_lull or wave_time > now.seconds() + tuning.wave_overlap:
		wave += 1
		wave_time = 0.0
		lull = 0.0
		_spawned = 0
		events.append([&"wave", wave])


func _spawn(s: OutpostPlan.Spawn) -> void:
	var f := Foe.new()
	f.kind = s.kind
	f.pos = OutpostPlan.dir(plan.sides[s.side] + s.spread) * plan.far
	f.stop = s.stop
	f.wave = wave
	match s.kind:
		OutpostPlan.Kind.RUNNER:
			f.hp = tuning.runner_hp
			f.speed = tuning.runner_speed
			f.gap = tuning.runner_gap
			f.damage = tuning.runner_damage
		OutpostPlan.Kind.SHIELD:
			f.hp = tuning.shield_hp
			f.speed = tuning.shield_speed
			f.gap = tuning.shield_gap
			f.windup = tuning.shield_windup
			f.damage = tuning.shield_damage
		OutpostPlan.Kind.THROWER:
			f.hp = tuning.thrower_hp
			f.speed = tuning.thrower_speed
			f.gap = tuning.thrower_gap
			f.damage = tuning.bottle_damage
		OutpostPlan.Kind.BRUTE:
			f.hp = tuning.brute_hp
			f.speed = tuning.brute_speed
			f.gap = tuning.brute_gap
			f.windup = tuning.brute_windup
			f.damage = tuning.brute_damage
			f.scale = tuning.brute_scale
	foes.append(f)


func _step_foe(f: Foe, dt: float) -> void:
	f.hit_for += dt
	match f.state:
		State.DEAD:
			f.dead_for += dt
		State.WALK:
			var left := f.pos.length() - f.stop
			var go := minf(f.speed * foe_speed_mult * dt, maxf(left, 0.0))
			f.pos -= f.pos.normalized() * go
			f.walked += go
			if left <= 0.01:
				f.state = State.ATTACK
				f.cooldown = f.gap * 0.6
		State.ATTACK:
			f.cooldown -= dt
			if f.cooldown <= 0.0:
				f.cooldown = f.gap
				if f.kind == OutpostPlan.Kind.THROWER:
					var b := Bottle.new()
					b.from = Vector3(f.pos.x, 1.9, f.pos.y)
					b.to = Vector3(pos.x, tuning.deck_height, pos.y)
					b.seconds = tuning.bottle_seconds
					bottles.append(b)
					events.append([&"throw", foes.find(f)])
				else:
					_hurt(f.damage, f.pos)
					events.append([&"strike", foes.find(f)])


func _step_bottles(dt: float) -> void:
	var i := 0
	while i < bottles.size():
		var b := bottles[i]
		b.age += dt
		if b.age >= b.seconds:
			var near := Vector2(b.to.x, b.to.z).distance_to(pos) <= tuning.bottle_blast
			events.append([&"splash", b.to, near])
			if near:
				_hurt(tuning.bottle_damage, Vector2(b.from.x, b.from.z))
			bottles.remove_at(i)
		else:
			i += 1


func _hurt(amount: int, from: Vector2) -> void:
	health = maxi(health - amount, 0)
	var to := from - pos
	events.append([&"hurt", amount, atan2(-to.x, -to.y)])


func _shoot() -> void:
	clip -= 1
	shots += 1
	fire_wait = tuning.fire_gap
	var from := eye()
	var dir := aim_dir(yaw, pitch)
	if not clear_of_deck(from, dir):
		events.append([&"shot", from + dir * 2.0, false])
		return
	var best := INF
	var what := -1
	var index := -1
	var through := pass_every > 0 and shots % pass_every == 0
	for i in foes.size():
		var f := foes[i]
		if f.state == State.DEAD or through:
			continue
		if f.kind == OutpostPlan.Kind.SHIELD and not f.winding():
			var t := _ray_sphere(from, dir, shield_of(f), 0.62)
			if t < best:
				best = t
				what = 0
				index = i
		var head := _ray_sphere(from, dir, head_of(f), tuning.head_radius * f.scale * near_mult)
		if head < best:
			best = head
			what = 1
			index = i
		var body := _ray_sphere(from, dir, body_of(f), tuning.body_radius * f.scale * near_mult)
		if body < best:
			best = body
			what = 2
			index = i
	for i in bottles.size():
		var t := _ray_sphere(from, dir, bottles[i].at(), tuning.bottle_radius)
		if t < best:
			best = t
			what = 3
			index = i
	for i in kegs_alive.size():
		if kegs_alive[i]:
			var t := _ray_sphere(from, dir, keg_at(i), 0.7)
			if t < best:
				best = t
				what = 4
				index = i
	events.append([&"shot", from + dir * (best if best < INF else 60.0), what >= 0])
	match what:
		0:
			blocked += 1
			events.append([&"block", index])
		1, 2:
			hits += 1
			var f := foes[index]
			var amount := 1
			if what == 1:
				match f.kind:
					OutpostPlan.Kind.BRUTE:
						amount = tuning.brute_weak if f.winding() else tuning.brute_head
					_:
						amount = 99
			_damage(index, amount, what == 1)
		3:
			popped += 1
			events.append([&"pop", bottles[index].at()])
			bottles.remove_at(index)
		4:
			_explode(index)


func _damage(index: int, amount: int, head: bool) -> void:
	var f := foes[index]
	if f.state == State.DEAD:
		return
	if not immortal:
		f.hp -= amount
	f.hit_for = 0.0
	events.append([&"hit", index, head])
	if f.hp <= 0:
		f.state = State.DEAD
		f.dead_for = 0.0
		kills += 1
		events.append([&"kill", index])


func _explode(index: int) -> void:
	kegs_alive[index] = false
	booms += 1
	var at := plan.kegs[index]
	events.append([&"boom", index])
	for i in foes.size():
		if foes[i].state != State.DEAD and foes[i].pos.distance_to(at) <= tuning.keg_blast:
			_damage(i, tuning.keg_damage, false)
	for i in kegs_alive.size():
		if kegs_alive[i] and plan.kegs[i].distance_to(at) <= tuning.keg_blast:
			_explode(i)


# --- Боты ------------------------------------------------------------------------------------

## Бот: ставит `bot_move`, `bot_yaw`, `bot_pitch`, `bot_fire`, `bot_reload`. WIN выбирает цель
## (летящая в него бутылка, бочка с толпой рядом, враг у вышки, метатель, ближний идущий),
## подходит к краю настила с её стороны, доводит прицел и стреляет; щитоносцу и великану бьёт
## в голову; без запаса идёт к ящику. LOSE стоит и не стреляет.
func bot(mode: AutoTest.BotMode, dt: float) -> void:
	bot_move = Vector2.ZERO
	bot_fire = false
	bot_reload = false
	if ended or mode != AutoTest.BotMode.WIN or phase != Phase.PLAY:
		return
	_bot_wait = maxf(_bot_wait - dt, 0.0)
	var from := eye()
	var target := Vector3.ZERO
	var radius := 0.0
	var found := false
	# Бутылка, которая упадёт рядом.
	for b in bottles:
		if Vector2(b.to.x, b.to.z).distance_to(pos) <= tuning.bottle_blast + 0.4 and b.age > 0.35:
			target = b.at()
			radius = tuning.bottle_radius
			found = true
			break
	# Бочка, у которой собрались.
	if not found:
		for i in kegs_alive.size():
			if not kegs_alive[i]:
				continue
			var near := 0
			for f in foes:
				if f.state != State.DEAD and f.pos.distance_to(plan.kegs[i]) <= tuning.keg_blast * 0.8:
					near += 3 if f.kind == OutpostPlan.Kind.BRUTE else 1
			if near >= 3:
				target = keg_at(i)
				radius = 0.7
				found = true
				break
	if not found:
		var best := INF
		for f in foes:
			if f.state == State.DEAD:
				continue
			var score := f.pos.length() - f.stop
			if f.state == State.ATTACK:
				score = -20.0 + f.cooldown
			if f.kind == OutpostPlan.Kind.THROWER and f.state == State.ATTACK:
				score = -10.0 + f.cooldown
			if score < best:
				best = score
				var head := f.kind == OutpostPlan.Kind.SHIELD or f.kind == OutpostPlan.Kind.BRUTE
				target = head_of(f) if head else body_of(f)
				radius = (tuning.head_radius if head else tuning.body_radius) * f.scale
				found = true
	# Куда встать: к ящику без запаса, иначе к краю со стороны цели.
	var want := Vector2.ZERO
	var dry := reserve == 0 and clip <= 2
	var spare := not found and reserve <= tuning.reserve_max - 12
	if dry or spare:
		want = plan.crate
	elif found:
		want = Vector2(target.x, target.z).normalized() * (tuning.deck_radius - tuning.deck_margin - 0.05)
	var step_to := want - pos
	if step_to.length() > 0.15:
		var fwd := Vector2(-sin(bot_yaw), -cos(bot_yaw))
		var world := step_to.normalized()
		bot_move = Vector2(world.dot(Vector2(-fwd.y, fwd.x)), world.dot(fwd))
	if not found:
		bot_reload = clip < tuning.clip
		return
	var to := target - from
	var want_yaw := atan2(-to.x, -to.z)
	var want_pitch := atan2(to.y, Vector2(to.x, to.z).length())
	bot_yaw = rotate_toward(bot_yaw, want_yaw, tuning.bot_turn * dt)
	bot_pitch = move_toward(bot_pitch, want_pitch, tuning.bot_turn * dt)
	var off := aim_dir(bot_yaw, bot_pitch).angle_to(to.normalized())
	if to.length() <= tuning.bot_range and off <= atan(radius * tuning.bot_tight / maxf(to.length(), 0.5)) and _bot_wait <= 0.0 and reload_left <= 0.0 and clip > 0 \
			and clear_of_deck(from, to.normalized()):
		bot_fire = true
		_bot_wait = tuning.bot_gap
