class_name SpitSim
extends RefCounted
## Правила демки платформер × low poly «тропа вглубь экрана» (#112) без окна и звука: состояние,
## шаг, боты. Демка `platformer_lowpoly.gd` рисует это состояние и озвучивает события `events`;
## `simulate` гоняет бота по сиду целиком (проверки `demo_test`, `debug/tools/dump_spit.gd`).
## Правила: герой бежит по косе, ход задаётся направлением в мире (демка переводит стрелки
## через камеру). Прыжок через ямы, на уступы и на плоты, что ходят поперёк над широкой водой
## и несут героя. Вода стоит жизни. Ящик не пускает сбоку; прыжок на него сверху разбивает
## ящик, даёт дублон и подбрасывает. Скелеты ходят поперёк тропы, бочки катятся навстречу,
## ядра летят поперёк: касание стоит жизни. Потеря жизни возвращает к началу последнего
## длинного куска. Жизни кончились: провал. Цель: дойти до конца косы у маяка. Баги жанра и
## баланса приходят числами (их включит #117): `jump_mult` высота прыжка, `enemy_mult` скорость
## скелетов, `coins_high` дублоны над головой, `sneeze` скелеты рассыпаются от касания.

const DT := 1.0 / 60.0

var tuning: PlatformerLowpolyTuning
var level: SpitLevel
var jump_mult := 1.0
var enemy_mult := 1.0
var coins_high := false
var sneeze := false

## Ноги героя в мире.
var pos := Vector3.ZERO
var vy := 0.0
var grounded := true
## Курс героя, как `rotation.y`.
var facing := 0.0
var moving := false
## Кусок, на котором герой стоял последним, и последний длинный: туда возвращает потеря жизни.
var piece := 0
var safe := 0
## Плот под ногами или −1.
var raft := -1
var lives := 3
var hits := 0
var falls := 0
var coins_got := 0
var crates_got := 0
var invuln := 0.0
var time := 0.0
var ended := false
var won := false
var crate_alive: Array[bool] = []
var coin_alive: Array[bool] = []
var guard_alive: Array[bool] = []
## События шага для звука и эффектов: `[имя, …]`. `jump`, `land`, `coin` (индекс), `smash`
## (индекс ящика), `pop` (индекс скелета), `hurt` (причина `fall`, `guard`, `barrel` или `ball` и
## место, где это случилось), `win`, `lose`. Демка читает и чистит.
var events: Array[Array] = []
## Бот хочет прыгнуть на этом шаге (`bot`); прыгает хозяин, чтобы залипание кнопки задело и бота.
var bot_jump := false
## Где и от чего терялись жизни (заметки автотеста и дамп).
var hurt_log: PackedStringArray = []

var _air := 0.0
var _water := -3.0


static func create(level_: SpitLevel, tuning_: PlatformerLowpolyTuning) -> SpitSim:
	var s := SpitSim.new()
	s.level = level_
	s.tuning = tuning_
	s.lives = tuning_.lives
	s.pos = level_.start
	s._water = level_.water_y()
	s.crate_alive.resize(level_.crates.size())
	s.crate_alive.fill(true)
	s.coin_alive.resize(level_.coins.size())
	s.coin_alive.fill(true)
	s.guard_alive.resize(level_.guards.size())
	s.guard_alive.fill(true)
	return s


## Прогон бота без окна до конца или до `max_seconds`.
static func simulate(level_: SpitLevel, tuning_: PlatformerLowpolyTuning, mode: AutoTest.BotMode, max_seconds := 300.0,
		setup := Callable()) -> SpitSim:
	var s := create(level_, tuning_)
	if setup.is_valid():
		setup.call(s)
	while not s.ended and s.time < max_seconds:
		var move := s.bot(mode)
		if s.bot_jump:
			s.jump()
		s.step(DT, move)
		s.events.clear()
	return s


## Время скелетов: с багом жанра они быстрее.
func guard_time() -> float:
	return time * enemy_mult


func coin_pos(i: int) -> Vector3:
	return level.coins[i] + (Vector3(0.0, 2.6, 0.0) if coins_high else Vector3.ZERO)


## Прыжок с опоры или сразу после схода с края. true, если герой пошёл вверх.
func jump() -> bool:
	if ended or vy > 0.0 or not (grounded or _air < tuning.coyote):
		return false
	vy = tuning.jump_speed * jump_mult
	grounded = false
	raft = -1
	_air = tuning.coyote
	events.append([&"jump"])
	return true


## Шаг мира: `move` направление хода в мире (x и z), длина до 1.
func step(dt: float, move: Vector2) -> void:
	if ended:
		return
	# Плот уносит героя с собой.
	if grounded and raft >= 0:
		pos += level.raft_pos(raft, time + dt) - level.raft_pos(raft, time)
	time += dt
	invuln = maxf(invuln - dt, 0.0)
	move = move.limit_length(1.0)
	moving = move.length() > 0.1
	if moving:
		facing = atan2(-move.x, -move.y)
		# По осям отдельно: вдоль ящика или борта тропы можно скользить.
		var by_x := pos + Vector3(move.x * tuning.run_speed * dt, 0.0, 0.0)
		if not _blocked(by_x):
			pos = by_x
		var by_z := pos + Vector3(0.0, 0.0, move.y * tuning.run_speed * dt)
		if not _blocked(by_z):
			pos = by_z
	var before := pos.y
	vy -= tuning.gravity * dt
	pos.y += vy * dt
	if vy < 0.0 and _stomp(before):
		return
	var floor_y := level.ground_at(pos, time)
	if floor_y > -INF and vy <= 0.0 and (grounded or before >= floor_y - 0.25) and pos.y <= floor_y + (0.3 if grounded else 0.0):
		pos.y = floor_y
		vy = 0.0
		if not grounded:
			events.append([&"land"])
		grounded = true
		_air = 0.0
		var under := level.piece_at(pos)
		raft = level.raft_at(pos, time) if under < 0 else -1
		if under >= 0:
			piece = under
			if level.pieces[under].length >= tuning.safe_length:
				safe = under
	else:
		grounded = false
		raft = -1
		_air += dt
	if pos.y < _water + 0.2:
		falls += 1
		_hurt(&"fall")
		return
	_touch_hazards()
	if ended:
		return
	_collect()
	var last := level.finish_piece()
	if grounded and piece == level.pieces.size() - 1 and last.local(pos).x >= last.length - tuning.finish_distance:
		ended = true
		won = true
		events.append([&"win"])


## Точка упирается в ящик или в борт тропы (герой ниже её края).
func _blocked(p: Vector3) -> bool:
	var reach := tuning.crate_half + tuning.hero_radius
	for i in crate_alive.size():
		var c := level.crates[i]
		if crate_alive[i] and absf(p.x - c.x) < reach and absf(p.z - c.z) < reach and p.y < c.y + 2.0 * tuning.crate_half - 0.15:
			return true
	var floor_y := level.ground_at(p, time)
	return floor_y > -INF and p.y < floor_y - 0.45


## Герой падает на ящик сверху: ящик разбит, дублон, отскок.
func _stomp(before: float) -> bool:
	var reach := tuning.crate_half + tuning.hero_radius * 0.8
	for i in crate_alive.size():
		var c := level.crates[i]
		var top := c.y + 2.0 * tuning.crate_half
		if crate_alive[i] and absf(pos.x - c.x) < reach and absf(pos.z - c.z) < reach and before >= top - 0.05 and pos.y <= top:
			crate_alive[i] = false
			crates_got += 1
			coins_got += 1
			pos.y = top
			vy = tuning.crate_bounce
			grounded = false
			raft = -1
			_air = tuning.coyote
			events.append([&"smash", i])
			return true
	return false


func _touch_hazards() -> void:
	if invuln > 0.0:
		return
	for i in guard_alive.size():
		if not guard_alive[i]:
			continue
		var g := level.guard_pos(i, guard_time())
		if Vector2(g.x - pos.x, g.z - pos.z).length() < tuning.hit_distance and absf(g.y - pos.y) < 1.6:
			if sneeze:
				guard_alive[i] = false
				events.append([&"pop", i])
			else:
				_hurt(&"guard")
				return
	var under := level.piece_at(pos)
	if under < 0:
		return
	var p := level.pieces[under]
	var q := p.local(pos)
	var above := pos.y - p.height(q.x)
	for i in level.rollers.size():
		if level.rollers[i].piece != under or above > 2.0 * tuning.barrel_radius:
			continue
		for b in level.barrels(i, time):
			if absf(b.x - q.x) < tuning.barrel_radius + tuning.hero_radius and absf(b.y - q.y) < tuning.barrel_half + tuning.hero_radius:
				_hurt(&"barrel")
				return
	for i in level.cannons.size():
		var c := level.cannons[i]
		if c.piece != under or above > tuning.ball_height + tuning.ball_radius:
			continue
		var u := level.ball_u(i, time)
		if u < INF and absf(c.s - q.x) < tuning.ball_radius + tuning.hero_radius and absf(u - q.y) < tuning.ball_radius + tuning.hero_radius:
			_hurt(&"ball")
			return


func _collect() -> void:
	var chest := pos + Vector3(0.0, 0.9, 0.0)
	for i in coin_alive.size():
		if coin_alive[i] and coin_pos(i).distance_to(chest) < tuning.coin_distance + 0.25:
			coin_alive[i] = false
			coins_got += 1
			events.append([&"coin", i])


func _hurt(why: StringName) -> void:
	hurt_log.append("%s на %.1f с, %s" % [why, time, describe_near()])
	hits += 1
	lives -= 1
	events.append([&"hurt", why, pos])
	if lives <= 0:
		ended = true
		won = false
		events.append([&"lose"])
		return
	# Назад к началу последнего длинного куска.
	var home := level.pieces[safe]
	pos = home.world(tuning.respawn_inset, 0.0)
	piece = safe
	raft = -1
	vy = 0.0
	grounded = true
	_air = 0.0
	invuln = tuning.invulnerable_seconds


## Доля пути от старта до маяка по тропе.
func progress() -> float:
	var p := level.pieces[piece]
	return clampf((p.along + clampf(p.local(pos).x, 0.0, p.length)) / level.total, 0.0, 1.0)


## Что рядом с героем, одной строкой: для заметки автотеста о потерянной жизни.
func describe_near() -> String:
	var p := level.pieces[piece]
	var q := p.local(pos)
	return "кусок %d (%s), s %.1f из %.0f, u %+.1f" % [piece, SpitLevel.Kind.keys()[p.kind], q.x, p.length, q.y]


# --- Боты ------------------------------------------------------------------------------------

## Бот: возвращает направление хода в мире и ставит `bot_jump`. WIN идёт в координатах куска
## впереди себя: держит безопасную полосу, берёт дублоны на пути, прыгает у края ямы, перед
## уступом и ящиком, плот и ядро пережидает, бочку перепрыгивает, скелета обходит у того
## борта, где его не будет; в воздухе не летит дальше, если не долетит, и над водой не шагает
## вбок. LOSE сбегает с тропы в воду.
func bot(mode: AutoTest.BotMode) -> Vector2:
	bot_jump = false
	if ended:
		return Vector2.ZERO
	var count := level.pieces.size()
	if mode != AutoTest.BotMode.WIN:
		var away := level.pieces[piece]
		var d := away.dir + away.right()
		return Vector2(d.x, d.z)
	# Кусок, в чьих координатах идём: под ногами; на повороте, на плоту и над ямой следующий.
	var here := level.piece_at(pos)
	var cur := here if here >= 0 else mini(piece + 1, count - 1)
	if here >= 0 and here + 1 < count:
		var after := level.pieces[here + 1]
		var mine := level.pieces[here]
		# Весь угловой квадрат уже в координатах следующего куска: иначе на его середине бот мечется.
		if not after.dir.is_equal_approx(mine.dir) and mine.local(pos).x >= mine.length - after.width:
			cur = here + 1
	var p := level.pieces[cur]
	var q := p.local(pos)
	var s := q.x
	var u := q.y
	var has_next := cur + 1 < count
	var next := level.pieces[mini(cur + 1, count - 1)]
	var straight := has_next and next.dir.is_equal_approx(p.dir)
	var margin := minf(tuning.bot_edge_margin, p.width / 2.0 - 0.3)
	var lo := -p.width / 2.0 + margin
	var hi := p.width / 2.0 - margin
	# Полоса следующего куска в этих координатах: у конца держимся в общей.
	var shift := p.local(next.a).y if straight else 0.0
	var next_margin := minf(tuning.bot_edge_margin, next.width / 2.0 - 0.3)
	var next_lo := shift - next.width / 2.0 + next_margin
	var next_hi := shift + next.width / 2.0 - next_margin
	if straight and p.length - s < 4.0 and maxf(lo, next_lo) <= minf(hi, next_hi):
		lo = maxf(lo, next_lo)
		hi = minf(hi, next_hi)
	var target := clampf(u, lo, hi)
	var forward := 1.0
	# Дублон впереди на безопасной полосе.
	var best := INF
	for i in coin_alive.size():
		if not coin_alive[i] or coins_high:
			continue
		var c := p.local(level.coins[i])
		var ahead := c.x - s
		if ahead > 0.4 and ahead < 7.0 and ahead < best and c.y >= lo and c.y <= hi:
			best = ahead
			target = c.y
	# Скелет впереди на этом куске: полоса у того борта, где его не будет в момент прохода.
	for i in guard_alive.size():
		var g := level.guards[i]
		var dist := g.s - s
		if not guard_alive[i] or sneeze or g.piece != cur or dist < -0.9:
			continue
		var best_lane := lo
		var best_room := -INF
		for lane: float in [lo, hi]:
			var room := INF
			for extra: float in [-0.3, 0.0, 0.3]:
				var when := time + maxf(dist, 0.0) / tuning.run_speed + extra
				room = minf(room, absf(level.guard_u(i, when * enemy_mult) - lane))
			if room > best_room:
				best_room = room
				best_lane = lane
		target = best_lane
		if dist > 1.0 and dist < tuning.bot_wait_distance and (best_room < tuning.bot_guard_margin or absf(u - best_lane) > 0.4):
			forward = 0.0
		break
	# Пушка впереди: не выходить на её линию, пока там пролетит ядро.
	for i in level.cannons.size():
		var c := level.cannons[i]
		var dist := c.s - s
		if c.piece != cur or dist < -0.6 or dist > 3.0:
			continue
		var danger := false
		for extra: float in [-0.25, -0.1, 0.05, 0.2, 0.35]:
			var ball := level.ball_u(i, time + maxf(dist, 0.0) / tuning.run_speed + extra)
			if ball < INF and absf(ball - target) < tuning.bot_ball_margin:
				danger = true
		if danger and dist > 1.0:
			forward = 0.0
			break
	var lateral := clampf((target - u) * 3.0, -1.0, 1.0)
	if grounded:
		# Бочка катится навстречу по моей полосе: прыжок так, чтобы она прошла подо мной.
		for i in level.rollers.size():
			var r := level.rollers[i]
			if r.piece != cur:
				continue
			for b in level.barrels(i, time):
				var hit := (b.x - s) / (r.speed + tuning.run_speed * forward)
				if absf(b.y - u) < tuning.barrel_half + tuning.hero_radius + 0.25 and hit > tuning.bot_barrel_min and hit < tuning.bot_barrel_max:
					bot_jump = true
			# У дальнего края бочка выкатывается прямо передо мной: прыжок заранее.
			var coming := level.next_barrel(i, time)
			var drop := p.length - SpitLevel.ROLL_DROP - s
			if drop > -0.8 and drop < (r.speed + tuning.run_speed) * tuning.bot_barrel_max and coming.x < 0.3 \
					and absf(coming.y - u) < tuning.barrel_half + tuning.hero_radius + 0.25:
				bot_jump = true
		# Ящик впереди на своей полосе.
		for i in crate_alive.size():
			var c := p.local(level.crates[i])
			var ahead := c.x - s
			if crate_alive[i] and ahead > 0.0 and ahead < tuning.bot_crate_distance + tuning.crate_half \
					and absf(u - c.y) < tuning.crate_half + tuning.hero_radius + 0.15:
				bot_jump = true
		if raft >= 0 and has_next and here < 0:
			# На плоту: к переднему краю и прыжок, когда плот напротив тропы.
			var on := level.rafts[raft]
			var raft_u := level.raft_u(raft, time)
			var edge := on.s + on.half - 0.35
			forward = 1.0 if s < edge else 0.0
			lateral = clampf((raft_u - u) * 3.0, -1.0, 1.0)
			if s >= edge - 0.15 and u >= -p.width / 2.0 + margin and u <= p.width / 2.0 - margin:
				bot_jump = true
				forward = 1.0
				lateral = 0.0
		elif here == cur and straight and p.length - s < tuning.bot_jump_distance:
			if next.raft >= 0:
				# Плот: ждать, пока в момент приземления он окажется под моей полосой.
				var on := level.rafts[next.raft]
				var fly := (p.length - s + next.gap / 2.0) / tuning.run_speed
				target = shift
				lateral = clampf((target - u) * 3.0, -1.0, 1.0)
				if absf(u - shift) < 0.3 and absf(level.raft_u(next.raft, time + fly) + shift - u) < on.half - tuning.bot_raft_margin:
					bot_jump = true
				else:
					forward = 0.0
			elif next.gap > 0.0:
				# Яма: прыжок у края, но только с полосы, с которой долетишь, и не под бочку.
				if u < next_lo - 0.2 or u > next_hi + 0.2 or _barrel_waits(cur + 1, u - shift):
					forward = 0.0
				else:
					bot_jump = true
			elif next.h0 - p.h1 > 0.45 and p.length - s < tuning.bot_step_distance:
				bot_jump = true
	elif forward > 0.0:
		# В воздухе: ход дозируется так, чтобы приземлиться на опору.
		var below := level.ground_at(pos, time)
		# Самый быстрый ход, при котором приземлюсь на опору: маленький камень на полном ходу
		# перелетается, а в борт уступа повыше можно упереться.
		for pace: float in [1.0, 0.75, 0.5, 0.25, 0.0]:
			if _lands(p.dir * tuning.run_speed * pace):
				forward = pace
				break
		# Не над тропой (над водой или над плотом) только вперёд: шаг вбок съедает скорость и уводит
		# с плота, а полоса следующего куска пока ни при чём.
		if below == -INF or here < 0:
			lateral = 0.0
	var world := p.dir * forward + p.right() * lateral
	return Vector2(world.x, world.z)


## Полёт с текущей скоростью вверх и ходом `run` по земле кончится на опоре: герой опустится
## на неё сверху, а не упрётся в борт и не уйдёт в воду.
func _lands(run: Vector3) -> bool:
	var t := 0.0
	while t < 1.6:
		t += 0.05
		var y := pos.y + vy * t - tuning.gravity * t * t / 2.0
		if y < _water:
			return false
		var spot := pos + run * t
		var floor_y := level.ground_at(spot, time + t)
		if floor_y > -INF and y <= floor_y + 0.05:
			return y >= floor_y - 0.3 and not _barrel_at(spot, time + t)
	return false


## В точке `spot` в момент `when` будет бочка (или вот-вот докатится).
func _barrel_at(spot: Vector3, when: float) -> bool:
	var under := level.piece_at(spot)
	if under < 0:
		return false
	var q := level.pieces[under].local(spot)
	for i in level.rollers.size():
		if level.rollers[i].piece != under:
			continue
		for extra: float in [0.0, 0.15, 0.3]:
			for b in level.barrels(i, when + extra):
				if absf(b.x - q.x) < 1.2 and absf(b.y - q.y) < tuning.barrel_half + tuning.hero_radius + 0.2:
					return true
	return false


## На каток `index` сейчас нельзя прыгать: к моменту приземления у его ближнего края на моей
## полосе `u` окажется бочка.
func _barrel_waits(index: int, u: float) -> bool:
	for i in level.rollers.size():
		var r := level.rollers[i]
		if r.piece != index:
			continue
		for extra: float in [0.5, 0.8, 1.1]:
			for b in level.barrels(i, time + extra):
				if b.x < 3.2 and absf(b.y - u) < tuning.barrel_half + tuning.hero_radius + 0.3:
					return true
	return false
