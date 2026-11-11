class_name TowerSim
extends RefCounted
## Правила демки платформер × вектор «этажи с дырами» (#90) без окна и звука: состояние, шаг,
## боты. Демка `platformer_vector.gd` рисует это состояние и озвучивает события `events`;
## `simulate` гоняет бота по сиду целиком (проверки `demo_test`, `debug/tools/dump_tower.gd`).
## Правила: герой бегает по этажу, экран замкнут по краям. Прыжок под дырой линии над головой
## поднимает на этаж; без дыры герой бьётся о потолок и ненадолго оглушён. Касание врага тоже
## оглушает, после него враг какое-то время проходит сквозь героя. Дыра своего этажа под ногами
## роняет на этаж ниже, оглушённого тоже: падение стоит жизни (пролёт сквозь несколько этажей
## подряд, пока герой оглушён падением, это одно падение и одна жизнь), жизни кончились: провал.
## Дыра, сквозь которую герой только что поднялся, не роняет, пока он из неё не вышел. Флаг на
## верхнем этаже. Баги жанра и баланса приходят числами:
## `jump_levels` этажей за прыжок (дикая физика: сквозь каждую следующую дыру герой летит
## дальше, без дыры влетает в потолок и возвращается оглушённым надолго),
## `enemy_mult` скорость врагов, `coins_high` монеты под потолком, `sneeze` враги гибнут от
## касания.

enum State { STAND, RISE, BONK, FALL, STUN }

## Высота героя в пикселях логического экрана и шаг этажей (ставит демка по своей раскладке).
const BODY_H := 64.0

var tuning: PlatformerVectorTuning
var tower: TowerLevel
var gap := 104.0
var jump_levels := 1
var enemy_mult := 1.0
var coins_high := false
var sneeze := false

var state := State.STAND
## Этаж, на котором герой стоит; в подъёме и падении этаж отправления.
var level := 0
var hero_x := 0.0
## Высота низа героя над землёй, пикселей (вверх плюс).
var hero_h := 0.0
var facing := 1
var move_dir := 0.0
var lives := 3
## Потерянные жизни (они же падения в дыры) и оглушения врагом и потолком.
var hits := 0
var falls := 0
var stuns := 0
var coins_got := 0
var stun := 0.0
var invuln := 0.0
var time := 0.0
var ended := false
var won := false
## Положение дыр и врагов сейчас, по индексам `tower.holes` и `tower.enemies`.
var hole_x: Array[float] = []
var enemy_x: Array[float] = []
var enemy_alive: Array[bool] = []
var coin_alive: Array[bool] = []
## События шага для звука и эффектов: `[имя, …]`. `jump`, `land`, `arrive` (поднялся и встал),
## `fall`, `bonk` (линия, x), `stunned` (врагом), `hurt` (потеряна жизнь), `pop` (индекс врага),
## `coin`, `win`, `lose`. Демка читает и чистит.
var events: Array[Array] = []
## Бот хочет прыгнуть на этом шаге (`bot`); прыгает хозяин, чтобы залипание кнопки задело и бота.
var bot_jump := false

var _move_t := 0.0
var _from_h := 0.0
var _to_h := 0.0
var _rise_left := 0
var _bonk_stun := 0.5
var _bonk_bump := 40.0
var _bonk_hit := false
## Дыра своего этажа, сквозь которую герой пришёл: не роняет, пока он из неё не вышел.
var _safe_hole := -1
## Герой оглушён падением: следующая дыра уронит его дальше, но жизнь уже снята.
var _tumbling := false


static func create(tower_: TowerLevel, tuning_: PlatformerVectorTuning, gap_ := 104.0) -> TowerSim:
	var s := TowerSim.new()
	s.tower = tower_
	s.tuning = tuning_
	s.gap = gap_
	s.lives = tuning_.lives
	s.hero_x = tower_.start_x
	for h in tower_.holes:
		s.hole_x.append(h.x)
	for e in tower_.enemies:
		s.enemy_x.append(e.x)
		s.enemy_alive.append(true)
	for c in tower_.coins:
		s.coin_alive.append(true)
	return s


## Прогон бота без окна до конца или до `max_seconds`.
static func simulate(tower_: TowerLevel, tuning_: PlatformerVectorTuning, mode: AutoTest.BotMode,
		max_seconds := 300.0, setup := Callable()) -> TowerSim:
	var s := create(tower_, tuning_)
	if setup.is_valid():
		setup.call(s)
	var dt := 1.0 / 60.0
	while not s.ended and s.time < max_seconds:
		var axis := s.bot(mode, dt)
		if s.bot_jump:
			s.jump()
		s.step(dt, axis)
		s.events.clear()
	return s


func floor_h(l: int) -> float:
	return l * gap


func delta(a: float, b: float) -> float:
	return TowerLevel.wrap_delta(a, b, tower.width)


## Индекс дыры линии `line`, в которой стоит точка `x`; `grow` расширяет дыру с каждой стороны
## (отрицательный сужает). −1, если дыры нет.
func hole_over(line: int, x: float, grow: float) -> int:
	for i in hole_x.size():
		var h := tower.holes[i]
		if h.line == line and absf(delta(hole_x[i], x)) <= h.width / 2.0 + grow:
			return i
	return -1


## Высота монеты над землёй: у пола этажа, а с багом баланса под его потолком, выше героя.
func coin_h(i: int) -> float:
	return floor_h(int(tower.coins[i].y)) + (gap - 26.0 if coins_high else 30.0)


## Дыра, в которую герой может прыгнуть прямо сейчас, или −1.
func open_hole() -> int:
	if ended or state != State.STAND or level >= tower.floors:
		return -1
	return hole_over(level + 1, hero_x, tuning.jump_margin)


## Прыжок вверх: под дырой подъём на этаж, без дыры удар о потолок и оглушение. true, если
## герой пошёл вверх.
func jump() -> bool:
	if ended or state != State.STAND or level >= tower.floors:
		return false
	events.append([&"jump"])
	_from_h = hero_h
	_move_t = 0.0
	if hole_over(level + 1, hero_x, tuning.jump_margin) >= 0:
		_rise_left = jump_levels
		_to_h = floor_h(level + 1)
		state = State.RISE
		return true
	_start_bonk(tuning.bonk_stun, gap - BODY_H)
	return false


func _start_bonk(stun_seconds: float, bump: float) -> void:
	state = State.BONK
	_from_h = hero_h
	_move_t = 0.0
	_bonk_stun = stun_seconds
	_bonk_bump = bump
	_bonk_hit = false


## Шаг мира: `axis` ось движения −1..1.
func step(dt: float, axis: float) -> void:
	if ended:
		return
	time += dt
	invuln = maxf(invuln - dt, 0.0)
	var w := tower.width
	for i in hole_x.size():
		hole_x[i] = fposmod(hole_x[i] + tower.holes[i].speed * dt, w)
	for i in enemy_x.size():
		enemy_x[i] = fposmod(enemy_x[i] + tower.enemies[i].speed * enemy_mult * dt, w)
	move_dir = 0.0
	match state:
		State.STAND:
			if absf(axis) >= 0.3:
				move_dir = signf(axis)
				facing = int(move_dir)
				hero_x = fposmod(hero_x + move_dir * tuning.run_speed * dt, w)
			_check_floor_hole()
		State.STUN:
			stun -= dt
			if stun <= 0.0:
				state = State.STAND
				_tumbling = false
			_check_floor_hole()
		State.RISE:
			_move_t += dt
			var k := clampf(_move_t / tuning.jump_seconds, 0.0, 1.0)
			hero_h = lerpf(_from_h, _to_h, 1.0 - (1.0 - k) * (1.0 - k))
			if k >= 1.0:
				_arrive_up()
		State.BONK:
			_move_t += dt
			var k := clampf(_move_t / tuning.bonk_seconds, 0.0, 1.0)
			hero_h = _from_h + _bonk_bump * sin(PI * k)
			if k >= 0.5 and not _bonk_hit:
				_bonk_hit = true
				stuns += 1
				events.append([&"bonk", level + 1, hero_x])
			if k >= 1.0:
				hero_h = _from_h
				state = State.STUN
				stun = _bonk_stun
		State.FALL:
			_move_t += dt
			var k := clampf(_move_t / tuning.fall_seconds, 0.0, 1.0)
			hero_h = lerpf(_from_h, _to_h, k * k)
			if k >= 1.0:
				level -= 1
				hero_h = _to_h
				state = State.STUN
				stun = tuning.stun_seconds
				# Оглушённый после падения ничего не может: враг его в это время не трогает.
				invuln = maxf(invuln, tuning.stun_seconds + tuning.touch_grace)
				events.append([&"land"])
				# Провалился: минус жизнь, одна на весь пролёт.
				if not _tumbling:
					_tumbling = true
					_hurt()
	if ended:
		return
	_collect()
	_touch_enemies()
	if not ended and level >= tower.floors and (state == State.STAND or state == State.STUN) \
			and absf(delta(tower.flag_x, hero_x)) < tuning.flag_distance:
		ended = true
		won = true
		events.append([&"win"])


func _arrive_up() -> void:
	level += 1
	hero_h = floor_h(level)
	_rise_left -= 1
	_safe_hole = hole_over(level, hero_x, 0.0)
	if _rise_left > 0:
		if level < tower.floors and hole_over(level + 1, hero_x, tuning.jump_margin) >= 0:
			_from_h = hero_h
			_to_h = floor_h(level + 1)
			_move_t = 0.0
			return
		# Дикая физика: в потолок следующего этажа и обратно, с верхнего этажа за край экрана.
		_rise_left = 0
		_start_bonk(tuning.wild_stun, gap - BODY_H if level < tower.floors else gap * 1.6)
		return
	state = State.STAND
	events.append([&"arrive"])


func _check_floor_hole() -> void:
	if level <= 0:
		return
	if _safe_hole >= 0 and absf(delta(hole_x[_safe_hole], hero_x)) > tower.holes[_safe_hole].width / 2.0:
		_safe_hole = -1
	for i in hole_x.size():
		var h := tower.holes[i]
		if h.line != level or i == _safe_hole:
			continue
		if absf(delta(hole_x[i], hero_x)) <= h.width / 2.0 - tuning.fall_inset:
			state = State.FALL
			_from_h = hero_h
			_to_h = floor_h(level - 1)
			_move_t = 0.0
			_safe_hole = -1
			if not _tumbling:
				falls += 1
			events.append([&"fall"])
			return


func _touch_enemies() -> void:
	if invuln > 0.0 or not (state == State.STAND or state == State.STUN):
		return
	for i in enemy_x.size():
		var e := tower.enemies[i]
		if not enemy_alive[i] or e.level != level or absf(delta(enemy_x[i], hero_x)) >= tuning.hit_distance:
			continue
		if sneeze:
			enemy_alive[i] = false
			events.append([&"pop", i])
		else:
			# Враг оглушает и какое-то время проходит сквозь героя.
			state = State.STUN
			stun = tuning.enemy_stun
			invuln = tuning.enemy_stun + tuning.touch_grace
			stuns += 1
			events.append([&"stunned"])
			return


func _collect() -> void:
	var mid := hero_h + BODY_H / 2.0
	for i in coin_alive.size():
		if not coin_alive[i]:
			continue
		if absf(delta(tower.coins[i].x, hero_x)) < tuning.coin_distance and absf(coin_h(i) - mid) < BODY_H * 0.6:
			coin_alive[i] = false
			coins_got += 1
			events.append([&"coin"])


func _hurt() -> void:
	hits += 1
	lives -= 1
	events.append([&"hurt"])
	if lives <= 0:
		ended = true
		won = false
		events.append([&"lose"])
		return
	invuln = maxf(invuln, tuning.invulnerable_seconds)


## Что рядом с героем, одной строкой: для заметки автотеста о потерянной жизни.
func describe_near() -> String:
	var parts: PackedStringArray = []
	for i in enemy_x.size():
		if enemy_alive[i] and tower.enemies[i].level == level:
			parts.append("враг %.0f%s" % [enemy_x[i], "→" if tower.enemies[i].speed > 0.0 else "←"])
	for i in hole_x.size():
		var h := tower.holes[i]
		if h.line == level or h.line == level + 1:
			parts.append("%s %.0f%s" % ["пол" if h.line == level else "верх", hole_x[i], "→" if h.speed > 0.0 else "←"])
	return ", ".join(parts)


# --- Боты ------------------------------------------------------------------------------------

## Бот: возвращает ось движения и ставит `bot_jump`. WIN встаёт под дыру следующего этажа и
## прыгает; дыры своего этажа обходит по кругу, врага пропускает через себя (оглушение), но не
## рядом с дырой своего этажа. LOSE забирается на этаж и идёт в дыру, пока не кончатся жизни.
func bot(mode: AutoTest.BotMode, dt: float) -> float:
	bot_jump = false
	if ended or state != State.STAND:
		return 0.0
	if mode != AutoTest.BotMode.WIN and level >= 1:
		return _bot_to_floor_hole()
	var w := tower.width
	var top := level >= tower.floors
	if not top and hole_over(level + 1, hero_x, -tuning.bot_jump_inset) >= 0:
		bot_jump = true
		return 0.0
	# Цели: флаг наверху, иначе дыры линии над головой: середина и оба края с запасом (край
	# выручает, когда под серединой дыра своего этажа); x и скорость.
	var targets: Array[Vector2] = []
	if top:
		targets.append(Vector2(tower.flag_x, 0.0))
	else:
		for i in hole_x.size():
			var h := tower.holes[i]
			if h.line == level + 1:
				var side := maxf(h.width / 2.0 - tuning.bot_jump_inset - 6.0, 0.0)
				for off: float in [0.0, -side, side]:
					targets.append(Vector2(fposmod(hole_x[i] + off, w), h.speed))
	var best_cost := INF
	var best_d := 0.0
	var best_dir := 0.0
	for tg in targets:
		for dir: float in [-1.0, 1.0]:
			# Погоня по кругу: зазор до цели закрывается с разницей скоростей героя и цели.
			var gap_x := fposmod((tg.x - hero_x) * dir, w)
			var d := tuning.run_speed * gap_x / maxf(tuning.run_speed - tg.y * dir, 1.0)
			var cost := _bot_path_cost(dir, d)
			if cost < best_cost:
				best_cost = cost
				best_d = d
				best_dir = dir
	if best_cost < INF:
		return best_dir if best_d > 6.0 else 0.0
	return _bot_flee_dir()


## Цена пути длиной `d` в сторону `dir`, в пикселях бега: сам путь плюс оглушение за каждого
## врага на нём. INF, если на пути дыра своего этажа или враг стоит у такой дыры (оглушённого
## рядом с дырой она уронит). Дыра, что едет навстречу, считается ближе на свой ход за время пути.
func _bot_path_cost(dir: float, d: float) -> float:
	var w := tower.width
	var seconds := d / tuning.run_speed
	var cost := d
	if level >= 1:
		for i in hole_x.size():
			var h := tower.holes[i]
			if h.line != level or i == _safe_hole:
				continue
			var half := h.width / 2.0 + tuning.bot_hole_margin
			var f := fposmod((hole_x[i] - hero_x) * dir, w)
			if f > w - half:
				continue
			var closing := minf(h.speed * dir, 0.0) * seconds
			if f + closing - half < d:
				return INF
	for i in enemy_x.size():
		var e := tower.enemies[i]
		if not enemy_alive[i] or e.level != level or sneeze or invuln > seconds:
			continue
		var f := fposmod((enemy_x[i] - hero_x) * dir, w)
		if f > w - tuning.hit_distance:
			f -= w
		# Встреча: зазор до врага закрывается с разницей скоростей; враг, что уходит быстрее
		# героя или дальше цели, не мешает.
		var rate := tuning.run_speed - e.speed * enemy_mult * dir
		if rate <= 1.0:
			continue
		var meet := maxf(f - tuning.hit_distance, 0.0) / rate
		if meet > seconds:
			continue
		if not _bot_stun_safe(hero_x + dir * tuning.run_speed * meet, meet):
			return INF
		cost += tuning.enemy_stun * tuning.run_speed
	return cost


## Оглушение в точке `x` своего этажа через `after` секунд безопасно: за его время туда не
## доедет дыра этого этажа.
func _bot_stun_safe(x: float, after := 0.0) -> bool:
	if level <= 0:
		return true
	for i in hole_x.size():
		var h := tower.holes[i]
		if h.line != level:
			continue
		var reach := h.width / 2.0 + tuning.bot_hole_margin + absf(h.speed) * (tuning.enemy_stun + 0.5)
		if absf(delta(x, hole_x[i] + h.speed * after)) < reach:
			return false
	return true


## Куда отойти от дыры своего этажа, 0 если она далеко. От врага бот отходит, только когда
## оглушение здесь опасно: рядом дыра.
func _bot_flee_dir() -> float:
	var side := 0.0
	var best := INF
	if level >= 1:
		for i in hole_x.size():
			var h := tower.holes[i]
			if h.line != level or i == _safe_hole:
				continue
			var dx := delta(hero_x, hole_x[i])
			var g := absf(dx) - h.width / 2.0 - tuning.bot_hole_margin * 2.0
			if g < 0.0 and g < best:
				best = g
				side = signf(dx) if dx != 0.0 else 1.0
	if side != 0.0:
		return -side
	if not _bot_stun_safe(hero_x):
		for i in enemy_x.size():
			var e := tower.enemies[i]
			if enemy_alive[i] and e.level == level and absf(delta(hero_x, enemy_x[i])) < tuning.bot_enemy_margin:
				return -signf(delta(hero_x, enemy_x[i]))
	return 0.0


## Бот LOSE на этаже выше земли: идёт в ближайшую дыру своего этажа; из той, сквозь которую
## поднялся, сначала выходит, иначе она его не уронит.
func _bot_to_floor_hole() -> float:
	if _safe_hole >= 0:
		return 1.0 if tower.holes[_safe_hole].speed < 0.0 else -1.0
	var nearest := INF
	for i in hole_x.size():
		if tower.holes[i].line == level:
			var dx := delta(hero_x, hole_x[i])
			if absf(dx) < absf(nearest):
				nearest = dx
	return signf(nearest) if nearest < INF and absf(nearest) > 4.0 else 0.0
