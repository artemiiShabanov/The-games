class_name TurretSim
extends RefCounted
## Правила демки шутер × вектор «башня в центре» (#92) без окна и звука: состояние, шаг, боты.
## Демка `shooter_vector.gd` рисует это состояние и озвучивает события `events`; `simulate`
## гоняет бота по сиду целиком (проверки `demo_test`, `debug/tools/dump_turret.gd`).
## Правила: башня стоит в центре, ствол поворачивается влево и вправо, пока держат выстрел,
## пушка стреляет раз в `fire_every`. Враги появляются у края экрана по расписанию
## `TurretWaves` и летят к башне: враг прямо и быстро, глыба медленно и от попадания
## раскалывается на два быстрых осколка, вьюн по спирали (в него надо целить с упреждением
## или подпустить ближе). Каждый уничтоженный идёт в счёт, цель `goal`. Кто долетел до башни,
## стоит жизни и сметает всех рядом; жизни кончились: провал. Расписание повторяется по кругу
## всё быстрее, так что отсидеться нельзя.
## Координаты от башни: `x` вправо, `y` вниз. Баги жанра и баланса приходят числами:
## `pass_every` каждый такой выстрел пролетает сквозь врагов (сквозь врагов), `ice` ствол
## набирает и теряет вращение не сразу (лёд), `foe_mult` скорость врагов, `extra_per_kill`
## цель растёт с каждым убитым (враги без конца), `near_miss` выстрел убивает и пролетев
## рядом, а глыба гибнет целиком (чих).

class Foe:
	var kind := TurretWaves.Kind.ENEMY
	## Направление от башни и расстояние до неё.
	var angle := 0.0
	var r := 0.0
	var speed := 0.0
	var spin := 0.0
	var alive := true
	## Порядковый номер: для рисования (фаза вращения глыбы).
	var id := 0

	func pos() -> Vector2:
		return Vector2.from_angle(angle) * r


class Shot:
	var pos := Vector2.ZERO
	var dir := Vector2.RIGHT
	var alive := true
	## Пролетает сквозь врагов (баг жанра).
	var ghost := false


var tuning: ShooterVectorTuning
var waves: TurretWaves
## Половина поля: враги появляются за его краем, выстрелы за ним гаснут.
var half := Vector2(832, 416)
var pass_every := 0
var ice := 0.0
var foe_mult := 1.0
var extra_per_kill := 0.0
var near_miss := 0.0
var one_hit := false

## Направление ствола, радианы, и его угловая скорость.
var aim := -PI / 2.0
var aim_vel := 0.0
var lives := 3
var kills := 0
var goal := 30.0
var shots_fired := 0
var time := 0.0
var ended := false
var won := false
var foes: Array[Foe] = []
var shots: Array[Shot] = []
## События шага для звука и эффектов: `[имя, …]`. `shot`, `kill` (вид, точка, номер),
## `split` (точка), `swept` (вид, точка, номер: сметён потерей жизни), `hurt`, `win`, `lose`.
## Демка читает и чистит.
var events: Array[Array] = []
## Бот хочет стрелять на этом шаге (`bot`).
var bot_fire := false

var _cooldown := 0.0
var _next := 0
var _loop := 0
var _loop_base := 0.0
var _ids := 0


static func create(waves_: TurretWaves, tuning_: ShooterVectorTuning, half_ := Vector2(832, 416)) -> TurretSim:
	var s := TurretSim.new()
	s.waves = waves_
	s.tuning = tuning_
	s.half = half_
	s.lives = tuning_.lives
	s.goal = tuning_.goal
	return s


## Прогон бота без окна до конца или до `max_seconds`.
static func simulate(waves_: TurretWaves, tuning_: ShooterVectorTuning, mode: AutoTest.BotMode,
		max_seconds := 300.0, setup := Callable()) -> TurretSim:
	var s := create(waves_, tuning_)
	if setup.is_valid():
		setup.call(s)
	var dt := 1.0 / 60.0
	while not s.ended and s.time < max_seconds:
		var axis := s.bot(mode)
		s.step(dt, axis, s.bot_fire)
		s.events.clear()
	return s


func radius(kind: TurretWaves.Kind) -> float:
	match kind:
		TurretWaves.Kind.ROCK:
			return tuning.rock_radius
		TurretWaves.Kind.SMALL:
			return tuning.small_radius
		TurretWaves.Kind.SPINNER:
			return tuning.spinner_radius
	return tuning.enemy_radius


## Расстояние от башни до края поля по направлению `angle`.
func edge(angle: float) -> float:
	var c := absf(cos(angle))
	var s := absf(sin(angle))
	return minf(half.x / maxf(c, 0.001), half.y / maxf(s, 0.001))


## Шаг мира: `axis` поворот ствола −1..1, `fire` держат ли выстрел.
func step(dt: float, axis: float, fire: bool) -> void:
	if ended:
		return
	time += dt
	# Ствол: на льду набирает и теряет вращение не сразу.
	var want := clampf(axis, -1.0, 1.0) * deg_to_rad(tuning.turn_speed)
	aim_vel = lerpf(aim_vel, want, minf(ice * dt, 1.0)) if ice > 0.0 else want
	aim = wrapf(aim + aim_vel * dt, -PI, PI)
	_cooldown = maxf(_cooldown - dt, 0.0)
	if fire and _cooldown <= 0.0:
		_cooldown = tuning.fire_every
		shots_fired += 1
		var sh := Shot.new()
		sh.dir = Vector2.from_angle(aim)
		sh.pos = sh.dir * tuning.muzzle
		sh.ghost = pass_every > 0 and shots_fired % pass_every == 0
		shots.append(sh)
		events.append([&"shot"])
	_spawn_due()
	for f in foes:
		if f.alive:
			f.r -= f.speed * dt
			f.angle = wrapf(f.angle + f.spin * dt, -PI, PI)
	for sh in shots:
		if not sh.alive:
			continue
		sh.pos += sh.dir * tuning.shot_speed * dt
		if absf(sh.pos.x) > half.x + 20.0 or absf(sh.pos.y) > half.y + 20.0:
			sh.alive = false
			continue
		if sh.ghost:
			continue
		# Попадание засчитывается только на экране: за его краем врага не видно.
		for i in foes.size():
			var f := foes[i]
			if not f.alive or f.r > edge(f.angle) + radius(f.kind):
				continue
			if sh.pos.distance_to(f.pos()) < radius(f.kind) + near_miss:
				sh.alive = false
				_kill(f)
				break
	if kills >= goal and not ended:
		ended = true
		won = true
		events.append([&"win"])
		return
	for f in foes:
		if f.alive and f.r <= tuning.turret_radius:
			f.alive = false
			_hurt()
			if ended:
				return
	_sweep()


func _spawn_due() -> void:
	while true:
		var scale := pow(tuning.loop_interval_mult, _loop)
		if _next >= waves.spawns.size():
			_loop_base += waves.seconds * scale
			_loop += 1
			_next = 0
			continue
		var s := waves.spawns[_next]
		if _loop_base + s.time * scale > time:
			return
		_next += 1
		var f := Foe.new()
		f.kind = s.kind
		f.angle = s.angle
		f.r = edge(s.angle) + tuning.spawn_margin
		f.speed = s.speed * foe_mult * pow(tuning.loop_speed_mult, _loop)
		f.spin = s.spin
		_ids += 1
		f.id = _ids
		foes.append(f)


func _kill(f: Foe) -> void:
	f.alive = false
	kills += 1
	goal += extra_per_kill
	events.append([&"kill", f.kind, f.pos(), f.id])
	if f.kind != TurretWaves.Kind.ROCK or one_hit:
		return
	# Глыба раскалывается на два осколка: расходятся в стороны и летят к башне быстрее.
	var off := asin(clampf(tuning.split_offset / maxf(f.r, tuning.split_offset), 0.0, 1.0))
	for side: float in [-1.0, 1.0]:
		var s := Foe.new()
		s.kind = TurretWaves.Kind.SMALL
		s.angle = wrapf(f.angle + off * side, -PI, PI)
		s.r = f.r
		s.speed = f.speed * tuning.small_speed_mult
		_ids += 1
		s.id = _ids
		foes.append(s)
	events.append([&"split", f.pos()])


## Кто-то долетел до башни: минус жизнь, всех рядом сметает (в счёт они не идут).
func _hurt() -> void:
	lives -= 1
	events.append([&"hurt"])
	for f in foes:
		if f.alive and f.r < tuning.blast_radius:
			f.alive = false
			events.append([&"swept", f.kind, f.pos(), f.id])
	if lives <= 0:
		ended = true
		won = false
		events.append([&"lose"])


## Убрать погибших и погасшие выстрелы.
func _sweep() -> void:
	for i in range(foes.size() - 1, -1, -1):
		if not foes[i].alive:
			foes.remove_at(i)
	for i in range(shots.size() - 1, -1, -1):
		if not shots[i].alive:
			shots.remove_at(i)


# --- Боты ------------------------------------------------------------------------------------

## Бот: возвращает поворот ствола и ставит `bot_fire`. WIN целит в того, кто раньше всех
## долетит, с упреждением на вьюна, и стреляет, когда ствол смотрит в цель; LOSE медленно
## крутит ствол и не стреляет.
func bot(mode: AutoTest.BotMode) -> float:
	bot_fire = false
	if ended:
		return 0.0
	if mode != AutoTest.BotMode.WIN:
		return tuning.bot_lose_turn
	var target: Foe = null
	var best := INF
	for f in foes:
		if not f.alive or f.r > edge(f.angle) + radius(f.kind) * 0.5:
			continue
		var ttc := (f.r - tuning.turret_radius) / maxf(f.speed, 1.0)
		if ttc < best:
			best = ttc
			target = f
	if target == null:
		return 0.0
	# Упреждение: за время полёта выстрела цель подлетит и, если она вьюн, уйдёт по дуге.
	var fly := maxf(target.r - tuning.muzzle, 0.0) / (tuning.shot_speed + target.speed)
	var diff := angle_difference(aim, target.angle + target.spin * fly)
	var hit_r := target.r - target.speed * fly
	var tol := atan(radius(target.kind) * tuning.bot_aim / maxf(hit_r, 1.0))
	bot_fire = absf(diff) < tol
	var step_angle := deg_to_rad(tuning.turn_speed) / 60.0
	return clampf(diff / step_angle, -1.0, 1.0)
