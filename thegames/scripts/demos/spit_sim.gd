class_name SpitSim
extends RefCounted
## Правила демки платформер × low poly «тропа вглубь экрана» (#112) без окна и звука: состояние,
## шаг, боты. Демка `platformer_lowpoly.gd` рисует это состояние и озвучивает события `events`;
## `simulate` гоняет бота по сиду целиком (проверки `demo_test`, `debug/tools/dump_spit.gd`).
## Правила: герой бежит по косе от камеры, ось ввода как у стрелок (вверх это вперёд, в −Z).
## Прыжок через ямы; вода в яме или сбоку от тропы стоит жизни и возвращает к началу куска.
## Ящик не пускает сбоку; прыжок на него сверху разбивает ящик, даёт дублон и подбрасывает.
## Скелет ходит поперёк тропы, касание стоит жизни. Жизни кончились: провал. Цель: дойти до
## конца тропы у маяка. Баги жанра и баланса приходят числами (их включит #117): `jump_mult`
## высота прыжка, `enemy_mult` скорость скелетов, `coins_high` дублоны над головой, `sneeze`
## скелеты рассыпаются от касания.

const DT := 1.0 / 60.0

var tuning: PlatformerLowpolyTuning
var level: SpitLevel
var jump_mult := 1.0
var enemy_mult := 1.0
var coins_high := false
var sneeze := false

## Ноги героя в мире; вперёд это −Z.
var pos := Vector3.ZERO
var vy := 0.0
var grounded := true
## Курс героя, как `rotation.y`.
var facing := 0.0
var moving := false
## Кусок, на котором герой стоял последним: сюда его возвращает потеря жизни.
var piece := 0
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
## (индекс ящика), `pop` (индекс скелета), `hurt` (причина `fall` или `guard` и место, где это случилось), `win`, `lose`.
## Демка читает и чистит.
var events: Array[Array] = []
## Бот хочет прыгнуть на этом шаге (`bot`); прыгает хозяин, чтобы залипание кнопки задело и бота.
var bot_jump := false
## Где и от чего терялись жизни (заметки автотеста и дамп).
var hurt_log: PackedStringArray = []

var _air := 0.0


static func create(level_: SpitLevel, tuning_: PlatformerLowpolyTuning) -> SpitSim:
	var s := SpitSim.new()
	s.level = level_
	s.tuning = tuning_
	s.lives = tuning_.lives
	s.pos = level_.start
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
		var axis := s.bot(mode)
		if s.bot_jump:
			s.jump()
		s.step(DT, axis)
		s.events.clear()
	return s


func guard_pos(i: int) -> Vector3:
	var g := level.guards[i]
	var x := level.guard_x(i, time * enemy_mult)
	return Vector3(x, level.pieces[g.piece].height(g.z), g.z)


func coin_pos(i: int) -> Vector3:
	return level.coins[i] + (Vector3(0.0, 2.6, 0.0) if coins_high else Vector3.ZERO)


## Прыжок с земли или сразу после схода с края. true, если герой пошёл вверх.
func jump() -> bool:
	if ended or vy > 0.0 or not (grounded or _air < tuning.coyote):
		return false
	vy = tuning.jump_speed * jump_mult
	grounded = false
	_air = tuning.coyote
	events.append([&"jump"])
	return true


## Шаг мира: `axis` как у стрелок, x вбок, y вперёд-назад (вверх это −1 и вперёд).
func step(dt: float, axis: Vector2) -> void:
	if ended:
		return
	time += dt
	invuln = maxf(invuln - dt, 0.0)
	var move := axis.limit_length(1.0)
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
	var floor_y := level.ground_at(pos.x, pos.z)
	if floor_y > -INF and vy <= 0.0 and (grounded or before >= floor_y - 0.25) and pos.y <= floor_y + (0.3 if grounded else 0.0):
		pos.y = floor_y
		vy = 0.0
		if not grounded:
			events.append([&"land"])
		grounded = true
		_air = 0.0
		piece = level.piece_at(pos.z)
	else:
		grounded = false
		_air += dt
	var home := level.pieces[piece]
	if pos.y < minf(home.h0, home.h1) - tuning.fall_depth:
		falls += 1
		_hurt(&"fall")
		return
	_touch_guards()
	if ended:
		return
	_collect()
	var last := level.finish_piece()
	if grounded and piece == level.pieces.size() - 1 and pos.z <= last.z1() + tuning.finish_distance:
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
	var floor_y := level.ground_at(p.x, p.z)
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
			_air = tuning.coyote
			events.append([&"smash", i])
			return true
	return false


func _touch_guards() -> void:
	if invuln > 0.0:
		return
	for i in guard_alive.size():
		if not guard_alive[i]:
			continue
		var g := guard_pos(i)
		if Vector2(g.x - pos.x, g.z - pos.z).length() < tuning.hit_distance and absf(g.y - pos.y) < 1.6:
			if sneeze:
				guard_alive[i] = false
				events.append([&"pop", i])
			else:
				_hurt(&"guard")
				return


func _collect() -> void:
	var chest := pos + Vector3(0.0, 0.9, 0.0)
	for i in coin_alive.size():
		if coin_alive[i] and coin_pos(i).distance_to(chest) < tuning.coin_distance + 0.25:
			coin_alive[i] = false
			coins_got += 1
			events.append([&"coin", i])


func _hurt(why: StringName) -> void:
	hurt_log.append("%s на %.1f с, x %.1f, %s" % [why, time, pos.x, describe_near()])
	hits += 1
	lives -= 1
	events.append([&"hurt", why, pos])
	if lives <= 0:
		ended = true
		won = false
		events.append([&"lose"])
		return
	# Назад к началу куска, на котором стоял последним.
	var home := level.pieces[piece]
	var z := home.z0 - tuning.respawn_inset
	pos = Vector3(home.x, home.height(z), z)
	vy = 0.0
	grounded = true
	_air = 0.0
	invuln = tuning.invulnerable_seconds


## Сколько метров пройдено от старта вперёд.
func progress() -> float:
	return clampf(-pos.z / level.length(), 0.0, 1.0)


## Что рядом с героем, одной строкой: для заметки автотеста о потерянной жизни.
func describe_near() -> String:
	var p := level.pieces[piece]
	var parts: PackedStringArray = ["кусок %d (%s), до края %.1f" % [piece, SpitLevel.Kind.keys()[p.kind], pos.z - p.z1()]]
	for i in guard_alive.size():
		if guard_alive[i] and level.guards[i].piece == piece:
			parts.append("скелет x %.1f, до него %.1f" % [guard_pos(i).x, pos.z - level.guards[i].z])
	return ", ".join(parts)


# --- Боты ------------------------------------------------------------------------------------

## Бот: возвращает ось движения и ставит `bot_jump`. WIN бежит вперёд по безопасной полосе,
## собирает дублоны на пути, прыгает у края ямы и перед ящиком, скелета обходит с той стороны,
## где его не будет, или ждёт; в воздухе не летит дальше, если впереди под ним воды нет, а за
## ней есть. LOSE бежит вперёд и вбок, с тропы в воду.
func bot(mode: AutoTest.BotMode) -> Vector2:
	bot_jump = false
	if ended:
		return Vector2.ZERO
	if mode != AutoTest.BotMode.WIN:
		return Vector2(1.0, -1.0)
	var here := level.piece_at(pos.z)
	var cur := here if here >= 0 else mini(piece + 1, level.pieces.size() - 1)
	var p := level.pieces[cur]
	var next := level.pieces[mini(cur + 1, level.pieces.size() - 1)]
	var margin := tuning.bot_edge_margin
	var lo := p.left() + margin
	var hi := p.right() - margin
	# У конца куска полоса должна годиться и для следующего.
	if cur + 1 < level.pieces.size() and pos.z - p.z1() < 4.0:
		var both_lo := maxf(lo, next.left() + margin)
		var both_hi := minf(hi, next.right() - margin)
		if both_lo <= both_hi:
			lo = both_lo
			hi = both_hi
	var target := clampf(pos.x, lo, hi)
	# Дублон впереди на безопасной полосе.
	var best := INF
	for i in coin_alive.size():
		var c := level.coins[i]
		var ahead := pos.z - c.z
		if coin_alive[i] and not coins_high and ahead > 0.4 and ahead < 7.0 and ahead < best and c.x >= lo and c.x <= hi:
			best = ahead
			target = c.x
	var forward := -1.0
	# Скелет на этом куске впереди: полоса у того борта, где его не будет в момент прохода.
	for i in guard_alive.size():
		var g := level.guards[i]
		var dist := pos.z - g.z
		if not guard_alive[i] or sneeze or g.piece != cur or dist < -0.9:
			continue
		var best_lane := lo
		var best_room := -INF
		for lane: float in [lo, hi]:
			var room := INF
			for extra: float in [-0.3, 0.0, 0.3]:
				var when := time + maxf(dist, 0.0) / tuning.run_speed + extra
				room = minf(room, absf(level.guard_x(i, when * enemy_mult) - lane))
			if room > best_room:
				best_room = room
				best_lane = lane
		target = best_lane
		var aligned := absf(pos.x - best_lane) < 0.4
		if dist > 1.0 and dist < tuning.bot_wait_distance and (best_room < tuning.bot_guard_margin or not aligned):
			forward = 0.0
		break
	var lateral := clampf((target - pos.x) * 3.0, -1.0, 1.0)
	if grounded:
		# Яма впереди: прыжок у края, но только с полосы, с которой долетишь.
		if cur + 1 < level.pieces.size() and next.gap > 0.0 and here == cur and pos.z - p.z1() < tuning.bot_jump_distance:
			if pos.x >= next.left() + margin * 0.6 and pos.x <= next.right() - margin * 0.6:
				bot_jump = true
			else:
				forward = 0.0
		# Ящик впереди на своей полосе.
		for i in crate_alive.size():
			var c := level.crates[i]
			var ahead := pos.z - c.z
			if crate_alive[i] and ahead > 0.0 and ahead < tuning.bot_crate_distance + tuning.crate_half \
					and absf(pos.x - c.x) < tuning.crate_half + tuning.hero_radius + 0.15:
				bot_jump = true
	elif forward < 0.0:
		# В воздухе: если долечу до земли, лечу; если нет, а земля подо мной есть, сажусь здесь.
		var base := level.pieces[piece].height(pos.z)
		var fall := vy * vy + 2.0 * tuning.gravity * maxf(pos.y - base, 0.0)
		var t_land := (vy + sqrt(maxf(fall, 0.0))) / tuning.gravity
		var landing := pos.z - tuning.run_speed * t_land
		if level.ground_at(pos.x, landing) == -INF and level.ground_at(pos.x, pos.z) > -INF:
			forward = 0.0
		# Над водой только вперёд: шаг вбок съедает скорость, и прыжок не дотягивает.
		if level.ground_at(pos.x, pos.z) == -INF:
			lateral = 0.0
	return Vector2(lateral, forward)
