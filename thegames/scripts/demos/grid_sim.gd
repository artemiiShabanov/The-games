class_name GridSim
extends RefCounted
## Правила демки платформер × 16/32-bit «по клеткам» (#98) без окна и звука: состояние, шаг,
## боты. Демка `platformer_bit16.gd` рисует это состояние и озвучивает события `events`;
## `simulate` гоняет бота по сиду целиком (проверки `demo_test`, `debug/tools/dump_grid.gd`).
## Правила: герой стоит на клетке. Стрелка это шаг на соседнюю клетку за `step_seconds`,
## прыжок переносит через одну клетку в сторону взгляда; посреди шага и прыжка управлять
## нельзя, нажатый заранее прыжок ждёт. Яма под ногами, торчащие шипы, упавший якорь и
## стражник в той же клетке стоят жизни; в воздухе героя достаёт только якорь, под которым он
## пролетает. Плита
## осыпается через `plate_seconds` после первого шага на неё. После потери жизни герой
## продолжает с последней пройденной клетки отдыха, плиты встают на место. Флаг в конце.
## Баги жанра и баланса приходят числами: `jump_over` клеток под прыжком (дикая физика: три
## вместо одной), `enemy_mult` скорость стражников, `coins_high` монеты висят выше прыжка и
## не берутся, `sneeze` стражник падает от касания.

enum Act { IDLE, STEP, JUMP, FALL, HURT }

## Шаг, с которым бот предсказывает стражников: кадр игры.
const BOT_DT := 1.0 / 60.0
## Запас к накопленному времени действия: шаг в 0,2 с это ровно двенадцать кадров, а не тринадцать
## из-за ошибки округления.
const EPS := 0.0005

class GuardState:
	var lo := 0
	var hi := 0
	var cell := 0
	## Положение в клетках (дробное в шаге), откуда и куда идёт.
	var pos := 0.0
	var from_c := 0
	var to_c := 0
	var dir := -1
	var step := 0.45
	var moving := false
	var t := 0.0
	var alive := true

	func copy() -> GuardState:
		var g := GuardState.new()
		g.lo = lo
		g.hi = hi
		g.cell = cell
		g.pos = pos
		g.from_c = from_c
		g.to_c = to_c
		g.dir = dir
		g.step = step
		g.moving = moving
		g.t = t
		g.alive = alive
		return g


var tuning: PlatformerBit16Tuning
var level: GridLevel
var jump_over := 1
var enemy_mult := 1.0
var coins_high := false
var sneeze := false

var act := Act.IDLE
## Клетка героя и его положение в клетках (дробное в шаге и прыжке).
var cell := 1
var x := 1.0
var facing := 1
var act_t := 0.0
var from_cell := 1
var to_cell := 1
var lives := 3
var invuln := 0.0
var coins_got := 0
var deaths := 0
var time := 0.0
var ended := false
var won := false
var guards: Array[GuardState] = []
var coin_taken: Array[bool] = []
## Плиты: секунды с первого шага на клетку и упавшие клетки.
var plate_t: Dictionary[int, float] = {}
var plate_fallen: Dictionary[int, bool] = {}
## События шага для звука и эффектов: `[имя, …]`. `step`, `jump`, `land`, `fall`, `crack`
## (клетка), `crumble` (клетка), `coin`, `hurt` (причина), `respawn`, `guard_down` (индекс),
## `win`, `lose`. Демка читает и чистит.
var events: Array[Array] = []
## Бот хочет прыгнуть на этом шаге (`bot`).
var bot_jump := false

var _progress := 1
var _want_jump := 0.0
var _bot_idle := 0.0
var _bot_skip := 0
## План бота до следующей клетки отдыха: ходы по порядку, у каждого время начала и вид.
var _bot_plan: Array[Array] = []


static func create(level_: GridLevel, tuning_: PlatformerBit16Tuning) -> GridSim:
	var s := GridSim.new()
	s.level = level_
	s.tuning = tuning_
	s.lives = tuning_.lives
	s.cell = level_.start
	s.x = level_.start
	s._progress = level_.start
	for g in level_.guards:
		var gs := GuardState.new()
		gs.lo = g.from
		gs.hi = g.to
		gs.cell = g.start
		gs.pos = g.start
		gs.dir = g.dir
		gs.step = g.step
		s.guards.append(gs)
	s.coin_taken.resize(level_.coins.size())
	s.coin_taken.fill(false)
	return s


## Прогон бота без окна до конца или до `max_seconds`.
static func simulate(level_: GridLevel, tuning_: PlatformerBit16Tuning, mode: AutoTest.BotMode,
		max_seconds := 240.0, setup := Callable()) -> GridSim:
	var s := create(level_, tuning_)
	if setup.is_valid():
		setup.call(s)
	var dt := 1.0 / 60.0
	while not s.ended and s.time < max_seconds:
		var axis := s.bot(mode, dt)
		s.step(dt, axis, s.bot_jump)
		s.events.clear()
	return s


## Сколько клеток перелетает прыжок целиком: через `jump_over` и на следующую.
func jump_span() -> int:
	return jump_over + 1


func jump_time() -> float:
	return tuning.jump_seconds * jump_span() / 2.0


## Фаза шипов клетки 0..1: торчат в начале периода, кончики показываются в его конце.
func spike_phase(c: int, at: float) -> float:
	return fposmod(at / maxf(level.period[c], 0.1) + level.phase[c], 1.0)


func spikes_up(c: int, at: float) -> bool:
	return spike_phase(c, at) < tuning.spike_up


## Якорь клетки внизу (падает или лежит) в начале периода; перед падением дрожит наверху.
func anchor_down(c: int, at: float) -> bool:
	return spike_phase(c, at) < tuning.anchor_down


func is_hole(c: int) -> bool:
	return level.cell(c) == GridLevel.Cell.PIT or plate_fallen.has(c)


## Шаг мира: `axis` стрелка −1..1, `jump` нажат ли прыжок на этом шаге.
func step(dt: float, axis: float, jump: bool) -> void:
	if ended:
		return
	time += dt
	invuln = maxf(invuln - dt, 0.0)
	_want_jump = tuning.jump_buffer if jump else maxf(_want_jump - dt, 0.0)
	for g in guards:
		_step_guard(g, dt)
	_step_plates(dt)
	match act:
		Act.IDLE:
			_progress = maxi(_progress, cell)
			if _want_jump > 0.0:
				_want_jump = 0.0
				_start(Act.JUMP, clampi(cell + facing * jump_span(), 0, level.width - 1))
				events.append([&"jump"])
			elif absf(axis) >= 0.3:
				facing = 1 if axis > 0.0 else -1
				var to := cell + facing
				if to >= 0 and to < level.width:
					_start(Act.STEP, to)
					events.append([&"step"])
		Act.STEP:
			act_t += dt
			var k := clampf((act_t + EPS) / tuning.step_seconds, 0.0, 1.0)
			x = lerpf(from_cell, to_cell, k)
			if k >= 0.5 and cell != to_cell:
				cell = to_cell
				_enter()
			if k >= 1.0 and act == Act.STEP:
				x = to_cell
				act = Act.IDLE
		Act.JUMP:
			act_t += dt
			var k := clampf((act_t + EPS) / jump_time(), 0.0, 1.0)
			x = lerpf(from_cell, to_cell, k)
			if k >= 1.0:
				cell = to_cell
				x = to_cell
				act = Act.IDLE
				events.append([&"land"])
				_enter()
		Act.FALL:
			act_t += dt
			if act_t >= tuning.fall_seconds:
				_die("яма")
		Act.HURT:
			act_t += dt
			if act_t >= tuning.hurt_seconds:
				_respawn()
	if ended:
		return
	if act == Act.IDLE or act == Act.STEP:
		_ground_hazards()
	elif act == Act.JUMP:
		# В воздухе героя достаёт только якорь клетки, над которой он летит.
		var over := roundi(x)
		if over != from_cell and over != to_cell and level.cell(over) == GridLevel.Cell.ANCHOR and anchor_down(over, time) \
				and invuln <= 0.0:
			_die("якорь")
	if ended:
		return
	_collect()
	if cell == level.flag and (act == Act.IDLE or act == Act.STEP):
		ended = true
		won = true
		events.append([&"win"])


func _start(what: Act, to: int) -> void:
	act = what
	act_t = 0.0
	from_cell = cell
	to_cell = to


## Герой встал на клетку: яма роняет, плита начинает осыпаться.
func _enter() -> void:
	if is_hole(cell):
		act = Act.FALL
		act_t = 0.0
		events.append([&"fall"])
	elif level.cell(cell) == GridLevel.Cell.PLATE and not plate_t.has(cell):
		plate_t[cell] = 0.0
		events.append([&"crack", cell])


func _ground_hazards() -> void:
	if invuln > 0.0:
		return
	match level.cell(cell):
		GridLevel.Cell.SPIKES:
			if spikes_up(cell, time):
				_die("шипы")
				return
		GridLevel.Cell.ANCHOR:
			if anchor_down(cell, time):
				_die("якорь")
				return
	for i in guards.size():
		var g := guards[i]
		if not g.alive or g.cell != cell:
			continue
		if sneeze:
			g.alive = false
			events.append([&"guard_down", i])
		else:
			_die("стражник")
			return


func _step_plates(dt: float) -> void:
	for c: int in plate_t.keys():
		if plate_fallen.has(c):
			continue
		plate_t[c] += dt
		if plate_t[c] >= tuning.plate_seconds:
			plate_fallen[c] = true
			events.append([&"crumble", c])
			if cell == c and (act == Act.IDLE or act == Act.STEP):
				act = Act.FALL
				act_t = 0.0
				events.append([&"fall"])


func _step_guard(g: GuardState, dt: float) -> void:
	if not g.alive:
		return
	g.t += dt
	if g.moving:
		var k := clampf((g.t + EPS) / (g.step / enemy_mult), 0.0, 1.0)
		g.pos = lerpf(g.from_c, g.to_c, k)
		if k >= 0.5:
			g.cell = g.to_c
		if k >= 1.0:
			g.pos = g.to_c
			g.moving = false
			g.t = 0.0
		return
	var next := g.cell + g.dir
	if next < g.lo or next > g.hi:
		# Край участка: постоял и повернул.
		if g.t >= tuning.guard_pause / enemy_mult:
			g.dir = -g.dir
			g.t = 0.0
		return
	g.from_c = g.cell
	g.to_c = next
	g.moving = true
	g.t = 0.0


## Монета берётся, когда герой рядом по горизонтали, с земли и в прыжке. Поднятую багом «не
## достать» не взять никак: она выше любого прыжка.
func _collect() -> void:
	if coins_high or act == Act.FALL or act == Act.HURT:
		return
	for i in level.coins.size():
		if coin_taken[i] or absf(x - level.coins[i]) > 0.45:
			continue
		coin_taken[i] = true
		coins_got += 1
		events.append([&"coin"])


func _die(why: String) -> void:
	deaths += 1
	lives -= 1
	events.append([&"hurt", why])
	if lives <= 0:
		ended = true
		won = false
		events.append([&"lose"])
		return
	act = Act.HURT
	act_t = 0.0


## После потери жизни: последняя пройденная клетка отдыха, плиты целы.
func _respawn() -> void:
	var cp := level.start
	for c in level.checkpoints:
		if c <= _progress:
			cp = c
	cell = cp
	x = cp
	from_cell = cp
	to_cell = cp
	facing = 1
	act = Act.IDLE
	act_t = 0.0
	invuln = tuning.invulnerable_seconds
	_want_jump = 0.0
	_bot_plan.clear()
	plate_t.clear()
	plate_fallen.clear()
	events.append([&"respawn"])


# --- Боты ------------------------------------------------------------------------------------

## Бот: возвращает стрелку и ставит `bot_jump`. WIN на клетке отдыха ищет по клеткам и времени
## самый быстрый безопасный путь до следующей клетки отдыха (ждать, шагнуть, прыгнуть) и
## выполняет его целиком по расписанию, не пересчитывая посреди: запас по времени, с которым
## план проверен, не съедается задержками. Не нашёл план за `bot_patience` секунд: идёт
## наудачу. LOSE просто идёт вправо.
func bot(mode: AutoTest.BotMode, dt: float) -> float:
	bot_jump = false
	if ended or act != Act.IDLE:
		return 0.0
	if mode != AutoTest.BotMode.WIN:
		return 1.0
	if not _bot_plan.is_empty():
		if time < float(_bot_plan[0][0]) - 0.001:
			return 0.0
		return _bot_do(int(_bot_plan.pop_front()[1]))
	# Пока бот ждёт план, тот пересчитывается раз в три кадра.
	_bot_skip -= 1
	if _bot_skip > 0:
		return 0.0
	_bot_skip = 3
	_bot_plan = _plan()
	if not _bot_plan.is_empty():
		_bot_idle = 0.0
		_bot_skip = 0
		return bot(mode, dt)
	_bot_idle += dt * 3.0
	if _bot_idle < tuning.bot_patience:
		return 0.0
	# Плана нет слишком долго (такое бывает с багами): наудачу, прыжком через яму.
	_bot_idle = 0.0
	return _bot_do(2 if is_hole(cell + 1) else 1)


func _bot_do(move: int) -> float:
	if move == 2:
		bot_jump = true
		return 0.0
	return 1.0


## Лучший план до следующей клетки отдыха: ходы по порядку, у каждого время начала и вид
## (1 шаг вправо, 2 прыжок); пусто, если плана нет. Время режется на половины шага: шаг это
## два тика (с середины герой на новой клетке), прыжок через клетку четыре.
func _plan() -> Array[Array]:
	var tick := tuning.step_seconds / 2.0
	var horizon := tuning.bot_horizon * 2
	var goal := level.flag
	for c in level.checkpoints:
		if c > cell:
			goal = mini(goal, c)
			break
	# Где стражники будут: клетка каждого покадрово. Шаг предсказания тот же, что у игры: с
	# крупным шагом стражники в плане отстают от настоящих.
	var occupied: Array[Dictionary] = []
	if not sneeze:
		var near: Array[GuardState] = []
		for g in guards:
			if g.alive and g.hi >= cell - 1 and g.lo <= goal + 2:
				near.append(g.copy())
		if not near.is_empty():
			for j in int(ceil((horizon * tick + 2.0 * tuning.bot_margin) / BOT_DT)) + 4:
				var cells := {}
				for g in near:
					cells[g.cell] = true
					_step_guard(g, BOT_DT)
				occupied.append(cells)
	var span := jump_span()
	var jump_ticks := 2 * span
	# Узел это клетка и тик; `came` откуда и каким ходом в него пришли.
	var came := {}
	var buckets: Array[Array] = []
	buckets.resize(horizon + 1)
	for i in buckets.size():
		buckets[i] = []
	buckets[0].append(cell)
	came[cell * 1000] = [-1, -1]
	for i in horizon:
		for c: int in buckets[i]:
			var key := c * 1000 + i
			var stand := _safe(c, i * tick, (i + 1) * tick, occupied)
			if c >= goal and stand:
				var out: Array[Array] = []
				while int(came[key][0]) >= 0:
					var from_key := int(came[key][0])
					if int(came[key][1]) != 0:
						out.push_front([time + (from_key % 1000) * tick, int(came[key][1])])
					key = from_key
				return out
			# Ждать: только на полу; на плите, шипах и под якорем бот не задерживается.
			if stand and level.cell(c) == GridLevel.Cell.FLOOR:
				_reach(came, buckets, c, i + 1, key, 0, horizon)
			# Шаг вправо: первая половина на своей клетке, вторая уже на новой.
			if stand and c + 1 < level.width and not is_hole(c + 1) and _safe(c + 1, (i + 1) * tick, (i + 2) * tick, occupied):
				_reach(came, buckets, c + 1, i + 2, key, 1, horizon)
			# Прыжок вправо: в воздухе мешает только якорь, приземление на пол или плиту.
			var to := c + span
			if facing != 1 or to >= level.width or is_hole(to) or i + jump_ticks > horizon:
				continue
			if level.cell(to) != GridLevel.Cell.FLOOR and level.cell(to) != GridLevel.Cell.PLATE:
				continue
			if not _safe(c, i * tick, i * tick, occupied) or not _safe(to, (i + jump_ticks) * tick, (i + jump_ticks) * tick, occupied):
				continue
			var clear := true
			for over in range(c + 1, to):
				if level.cell(over) == GridLevel.Cell.ANCHOR:
					for k in range(i, i + jump_ticks + 1):
						if anchor_down(over, time + k * tick - tuning.bot_margin) or anchor_down(over, time + k * tick + tuning.bot_margin):
							clear = false
			if clear:
				_reach(came, buckets, to, i + jump_ticks, key, 2, horizon)
	return []


func _reach(came: Dictionary, buckets: Array[Array], c: int, i: int, from_key: int, move: int, horizon: int) -> void:
	if i > horizon or came.has(c * 1000 + i):
		return
	came[c * 1000 + i] = [from_key, move]
	buckets[i].append(c)


## Можно ли стоять на клетке с `from` по `to` секунд от сейчас, с запасом `bot_margin` по краям.
func _safe(c: int, from: float, to: float, occupied: Array[Dictionary]) -> bool:
	if is_hole(c):
		return false
	var t0 := time + from - tuning.bot_margin
	var t1 := time + to + tuning.bot_margin
	var kind := level.cell(c)
	if kind == GridLevel.Cell.SPIKES or kind == GridLevel.Cell.ANCHOR:
		var n := 6
		for k in n + 1:
			var at := lerpf(t0, t1, float(k) / n)
			if (kind == GridLevel.Cell.SPIKES and spikes_up(c, at)) or (kind == GridLevel.Cell.ANCHOR and anchor_down(c, at)):
				return false
	if not occupied.is_empty():
		var j0 := maxi(int(floor((from - tuning.bot_margin) / BOT_DT)), 0)
		var j1 := mini(int(ceil((to + tuning.bot_margin) / BOT_DT)), occupied.size() - 1)
		for j in range(j0, j1 + 1):
			if occupied[j].has(c):
				return false
	return true
