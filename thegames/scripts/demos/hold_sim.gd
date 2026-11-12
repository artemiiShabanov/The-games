class_name HoldSim
extends RefCounted
## Правила шутера × 16/32-bit «до выхода» (#100) без окна и звука: герой, скелеты, пули,
## аптечки, ключ, выход, боты. Демка `shooter_bit16.gd` рисует это состояние и озвучивает
## события; `simulate` гоняет бота по сиду целиком (проверки `demo_test`,
## `debug/tools/dump_hold.gd`). Мир шагает ровно 60 раз в секунду. Правила: ход и стрейф с
## упором в стены (скольжение вдоль), поворот; выстрел это пуля героя, быстрая, попадает в
## первого врага на пути (плейтест 2026-11-12: видно, куда летит). Скелет замечает героя в
## пределах видимости и идёт к нему по клеткам; с мушкетом держит дистанцию и стреляет медленной
## пулей, от которой можно уйти стрейфом, с саблей бежит быстрее и рубит вблизи. Аптечка лечит, ключ открывает дверь выхода; вошёл в дверь с ключом: победа,
## здоровье кончилось: поражение. Баги приходят числами: `ice` лёд на палубе (скорость героя
## догоняет ввод медленно, его заносит) и `foe_mult` скелеты и пули быстрее; `sneeze` скелет
## падает с одного попадания и от касания; `pass_every` каждый такой выстрел проходит сквозь
## врага; `extra_per_kill` враги без конца: убитый зовёт новых в дальней комнате;
## `walls_open` герой проходит сквозь стены.

const DT := 1.0 / 60.0

class Foe:
	var kind := HoldMap.Foe.MUSKET
	var pos := Vector2.ZERO
	var hp := 2
	var alive := true
	var active := false
	var cooldown := 0.0
	## Куда смотрит (для ракурса спрайта) и шагает ли.
	var facing := 0.0
	var walking := false
	var path: Array[Vector2i] = []
	var repath := 0.0
	var died_at := 0.0
	var hurt := 0.0

class Shot:
	var pos := Vector2.ZERO
	var vel := Vector2.ZERO
	## Пуля героя (иначе скелета) и сколько врагов она уже прошла насквозь (баг).
	var mine := false
	var passed: Array[int] = []

var tuning: ShooterBit16Tuning
var map: HoldMap
var foe_mult := 1.0
var ice := 0.0
var sneeze := false
var pass_every := 0
var extra_per_kill := 0
var walls_open := false
## Скорость героя (на льду с инерцией).
var vel := Vector2.ZERO

var pos := Vector2.ZERO
var angle := 0.0
var health := 100
var has_key := false
var foes: Array[Foe] = []
var shots: Array[Shot] = []
var medkit_taken := PackedByteArray()
var kills := 0
var hurts := 0
var time := 0.0
var ended := false
var won := false
var cooldown := 0.0
var shots_fired := 0
## Сколько прошёл (для покачивания оружия) и шагает ли сейчас.
var walked := 0.0
var moving := false
## События шага: `[имя, …]`. `fire`, `hit` (индекс врага), `kill` (индекс), `miss`, `foe_fire`
## (индекс), `slash` (индекс, удар саблей), `hurt`, `medkit`, `key`, `locked`, `win`, `lose`.
## Демка читает и чистит.
var events: Array[Array] = []
## Ввод бота на этом шаге.
var bot_fire := false
var bot_strafe := 0.0

var _bot_path: Array[Vector2i] = []
var _bot_foe: Foe = null
var _bot_medkit := -1
var _bot_foe_t := 0.0
## Враги, которых бот на время бросил: враг -> до какого времени.
var _bot_ignore := {}
var _bot_repath := 0.0


static func create(map_: HoldMap, tuning_: ShooterBit16Tuning) -> HoldSim:
	var s := HoldSim.new()
	s.map = map_
	s.tuning = tuning_
	s.pos = map_.start
	s.angle = map_.start_angle
	s.health = tuning_.health
	for k in map_.foes.size():
		var p := map_.foes[k]
		var f := Foe.new()
		f.kind = map_.foe_kinds[k] as HoldMap.Foe if k < map_.foe_kinds.size() else HoldMap.Foe.MUSKET
		f.pos = p
		f.hp = tuning_.foe_health
		f.facing = fposmod(p.x * 1.7 + p.y, TAU)
		s.foes.append(f)
	s.medkit_taken.resize(map_.medkits.size())
	s.medkit_taken.fill(0)
	return s


static func simulate(map_: HoldMap, tuning_: ShooterBit16Tuning, mode: AutoTest.BotMode, setup := Callable()) -> HoldSim:
	var s := create(map_, tuning_)
	if setup.is_valid():
		setup.call(s)
	while not s.ended:
		var input := s.bot(mode)
		s.step(input.x, input.y, s.bot_strafe, s.bot_fire)
		s.events.clear()
	return s


func dir() -> Vector2:
	return Vector2(cos(angle), sin(angle))


## Шаг мира в 1/60 секунды: `move` вперёд −1..1, `turn` поворот −1..1 (плюс вправо),
## `strafe` вбок −1..1, `fire` нажат ли выстрел на этом шаге.
func step(move: float, turn: float, strafe: float, fire: bool) -> void:
	if ended:
		return
	time += DT
	cooldown = maxf(cooldown - DT, 0.0)
	angle = fposmod(angle + turn * tuning.turn_speed * DT, TAU)
	var d := dir()
	var side := Vector2(-d.y, d.x)
	var v := d * move * tuning.move_speed + side * strafe * tuning.strafe_speed
	vel = v if ice <= 0.0 else vel.lerp(v, minf(ice * DT, 1.0))
	moving = vel.length() > 0.1
	_move(vel * DT)
	if fire and cooldown <= 0.0:
		_fire()
	_step_foes()
	_step_shots()
	_pickups()
	if not ended and time >= tuning.max_seconds:
		_end(false)


## Ход с упором в стены: по осям отдельно, вдоль стены скользит. Дверь выхода с ключом это
## победа, без ключа событие «заперто».
func _move(dv: Vector2) -> void:
	walked += dv.length()
	for axis in 2:
		var np := pos
		np[axis] += dv[axis]
		var r := tuning.radius * signf(dv[axis])
		var probe := np
		probe[axis] += r
		var c := Vector2i(floor(probe))
		if c == map.exit:
			if has_key:
				pos = np
				_end(true)
				return
			if dv[axis] != 0.0:
				events.append([&"locked"])
			continue
		if dv[axis] == 0.0 or walls_open and map.cell(c.x, c.y) != HoldMap.Cell.STONE or not map.solid_at(probe):
			pos = np
	if walls_open:
		pos = pos.clamp(Vector2(1.5, 1.5), Vector2(map.width - 1.5, map.height - 1.5))


func _fire() -> void:
	cooldown = tuning.fire_cooldown
	shots_fired += 1
	events.append([&"fire"])
	var b := Shot.new()
	b.mine = true
	b.pos = pos + dir() * 0.3
	b.vel = dir() * tuning.bullet_speed
	shots.append(b)


## Пуля героя попала в скелета `i`.
func _hit_foe(i: int) -> void:
	var f := foes[i]
	f.hp -= f.hp if sneeze else 1
	f.active = true
	f.hurt = 0.25
	if f.hp <= 0:
		f.alive = false
		f.died_at = time
		kills += 1
		events.append([&"kill", i])
		_respawn_extra()
	else:
		events.append([&"hit", i])


func _step_foes() -> void:
	for i in foes.size():
		var f := foes[i]
		if not f.alive:
			continue
		f.hurt = maxf(f.hurt - DT, 0.0)
		var to := pos - f.pos
		var dist := to.length()
		var sees := dist < tuning.foe_sight and map.sight(f.pos, pos)
		if sees and not f.active:
			f.active = true
			f.cooldown = tuning.foe_first_shot
		f.walking = false
		if not f.active:
			continue
		f.facing = atan2(to.y, to.x)
		var cutlass := f.kind == HoldMap.Foe.CUTLASS
		var keep := tuning.melee_reach * 0.8 if cutlass else tuning.foe_keep
		var speed := tuning.melee_speed if cutlass else tuning.foe_speed
		# Подойти: напрямую, если видно, иначе по клеткам.
		if dist > keep or not sees:
			var target := pos
			if not sees:
				f.repath -= DT
				if f.repath <= 0.0 or f.path.is_empty():
					f.path = map.path(Vector2i(floor(f.pos)), Vector2i(floor(pos)))
					f.repath = 0.5
				if not f.path.is_empty():
					target = Vector2(f.path[0]) + Vector2(0.5, 0.5)
					if target.distance_to(f.pos) < 0.2:
						f.path.pop_front()
			var step_v := (target - f.pos).normalized() * speed * foe_mult * DT
			var np := f.pos + step_v
			if not map.solid_at(np):
				f.pos = np
				f.walking = true
		if sneeze and dist < tuning.radius + 0.3:
			f.alive = false
			f.died_at = time
			kills += 1
			events.append([&"kill", i])
			continue
		f.cooldown -= DT
		if cutlass:
			if dist < tuning.melee_reach and f.cooldown <= 0.0:
				f.cooldown = tuning.melee_cooldown / foe_mult
				events.append([&"slash", i])
				_damage(tuning.melee_damage)
				if ended:
					return
			continue
		if sees and f.cooldown <= 0.0:
			f.cooldown = tuning.foe_cooldown / foe_mult
			var s := Shot.new()
			s.pos = f.pos + to.normalized() * 0.3
			s.vel = to.normalized() * tuning.shot_speed * foe_mult
			shots.append(s)
			events.append([&"foe_fire", i])


## Враги без конца: убитый зовёт `extra_per_kill` новых в комнате, дальней от героя.
func _respawn_extra() -> void:
	for k in extra_per_kill:
		var far := map.rooms[0]
		for r in map.rooms:
			if r.center().distance_to(pos) > far.center().distance_to(pos):
				far = r
		var f := Foe.new()
		f.pos = far.center() + Vector2(0.5, 0.5)
		if map.solid_at(f.pos):
			f.pos = far.center()
		f.hp = tuning.foe_health
		foes.append(f)


func _step_shots() -> void:
	for k in range(shots.size() - 1, -1, -1):
		var s := shots[k]
		s.pos += s.vel * DT
		if map.solid_at(s.pos):
			shots.remove_at(k)
			if s.mine:
				events.append([&"miss"])
			continue
		if s.mine:
			var hit := -1
			for i in foes.size():
				if foes[i].alive and not s.passed.has(i) and s.pos.distance_to(foes[i].pos) < tuning.foe_radius:
					hit = i
					break
			if hit < 0:
				continue
			# Пули насквозь (баг): каждая `pass_every`-я пролетает сквозь, попадание не засчитано.
			if pass_every > 0 and shots_fired % pass_every == 0:
				s.passed.append(hit)
				continue
			shots.remove_at(k)
			_hit_foe(hit)
			continue
		if s.pos.distance_to(pos) < tuning.radius + 0.12:
			shots.remove_at(k)
			_damage(tuning.shot_damage)
			if ended:
				return


func _damage(n: int) -> void:
	health -= n
	hurts += 1
	events.append([&"hurt"])
	if health <= 0:
		health = 0
		_end(false)


func _pickups() -> void:
	if not has_key and pos.distance_to(map.key) < 0.5:
		has_key = true
		events.append([&"key"])
	for i in map.medkits.size():
		if medkit_taken[i] == 0 and pos.distance_to(map.medkits[i]) < 0.5 and health < tuning.health:
			medkit_taken[i] = 1
			health = mini(health + tuning.medkit, tuning.health)
			events.append([&"medkit"])


func _end(win: bool) -> void:
	ended = true
	won = win
	events.append([&"win" if win else &"lose"])


# --- Боты --------------------------------------------------------------------------------------

## Бот: возвращает `Vector2(ход, поворот)` и ставит `bot_fire`, `bot_strafe`. WIN идёт по
## клеткам к ключу, потом к двери выхода; видит врага ближе `bot_engage`: встаёт, наводится и
## стреляет; пуля ближе `bot_dodge` летит в него: уходит стрейфом поперёк. Здоровья мало и
## аптечка рядом: сначала к ней. LOSE подходит к ближнему врагу на дистанцию его выстрела,
## стоит и не стреляет.
func bot(mode: AutoTest.BotMode) -> Vector2:
	bot_fire = false
	bot_strafe = 0.0
	if ended:
		return Vector2.ZERO
	if mode != AutoTest.BotMode.WIN:
		# Подойти к ближнему скелету на дистанцию его выстрела и стоять: не касаться (с чихом
		# касание его убивает) и не стрелять.
		var near := _nearest_foe(false)
		if near == null:
			return Vector2(0.0, 0.3)
		var go := _go_to(near.pos, false)
		if near.pos.distance_to(pos) < tuning.foe_keep + 0.8 and map.sight(pos, near.pos):
			go.x = 0.0
		return go
	_dodge()
	var foe := _nearest_foe(true)
	var reach := tuning.bot_engage
	if foe != null and foe.kind == HoldMap.Foe.CUTLASS:
		reach = tuning.bot_engage_melee
	# Гистерезис: начатый бой с этим врагом идёт, пока он жив и виден в пределах дальности с
	# запасом, иначе на границе дальности бот крутится между врагом и путём.
	if foe != null and foe == _bot_foe:
		reach += 1.5
	var was := _bot_foe
	_bot_foe = foe if foe != null and foe.pos.distance_to(pos) < reach else null
	# Бой без попаданий дольше `bot_give_up` (враг за углом колонны): бросить его на время.
	if _bot_foe != null and _bot_foe == was:
		_bot_foe_t += DT
		if _bot_foe.hurt > 0.0:
			_bot_foe_t = 0.0
		if _bot_foe_t > tuning.bot_give_up:
			_bot_ignore[_bot_foe] = time + tuning.bot_give_up * 2.0
			_bot_foe = null
	else:
		_bot_foe_t = 0.0
	if _bot_foe != null:
		var to := foe.pos - pos
		var diff := wrapf(atan2(to.y, to.x) - angle, -PI, PI)
		bot_fire = absf(diff) < 0.06
		# Сабельник близко: пятиться, стреляя (если сзади не стена).
		var back := 0.0
		if foe.kind == HoldMap.Foe.CUTLASS and to.length() < tuning.melee_reach * 2.2 and not map.solid_at(pos - dir() * 0.6):
			back = -1.0
		return Vector2(back, clampf(diff * 6.0, -1.0, 1.0))
	var target := map.key if not has_key else Vector2(map.exit) + Vector2(0.5, 0.5)
	# Аптечка: при здоровье меньше половины ближайшая по пути не дальше 10 клеток; выбранная
	# держится, пока не взята (иначе бот мечется между двумя).
	if _bot_medkit >= 0 and medkit_taken[_bot_medkit] != 0:
		_bot_medkit = -1
	if _bot_medkit < 0 and health < tuning.health * 0.5:
		var best := 11
		for i in map.medkits.size():
			if medkit_taken[i] != 0:
				continue
			var n := map.path(Vector2i(floor(pos)), Vector2i(floor(map.medkits[i]))).size()
			if n > 0 and n < best:
				best = n
				_bot_medkit = i
	if _bot_medkit >= 0:
		target = map.medkits[_bot_medkit]
	return _go_to(target, true)


func _nearest_foe(visible: bool) -> Foe:
	var best: Foe = null
	for f in foes:
		if not f.alive or (visible and not map.sight(pos, f.pos)):
			continue
		if visible and float(_bot_ignore.get(f, -1.0)) > time:
			continue
		if best == null or f.pos.distance_to(pos) < best.pos.distance_to(pos):
			best = f
	return best


## Уйти стрейфом от пули, которая летит в героя.
func _dodge() -> void:
	for s in shots:
		if s.mine:
			continue
		var to := pos - s.pos
		if to.length() > tuning.bot_dodge or s.vel.dot(to) <= 0.0:
			continue
		var side := Vector2(-sin(angle), cos(angle))
		bot_strafe = 1.0 if s.vel.cross(to) > 0.0 else -1.0
		# Стрейф в стену бесполезен: в другую сторону.
		if map.solid_at(pos + side * bot_strafe * 0.6):
			bot_strafe = -bot_strafe
		return


## Идти к точке по клеткам: развернуться к следующей клетке пути и шагать, когда смотрит на неё.
func _go_to(target: Vector2, plan: bool) -> Vector2:
	var aim := target
	_bot_repath -= DT
	if plan:
		if _bot_repath <= 0.0 or _bot_path.is_empty():
			var goal := Vector2i(floor(target))
			_bot_path = map.path(Vector2i(floor(pos)), goal)
			_bot_repath = 0.4
		while not _bot_path.is_empty() and (Vector2(_bot_path[0]) + Vector2(0.5, 0.5)).distance_to(pos) < 0.35:
			_bot_path.pop_front()
		if not _bot_path.is_empty():
			aim = Vector2(_bot_path[0]) + Vector2(0.5, 0.5)
	elif not map.sight(pos, target):
		var p := map.path(Vector2i(floor(pos)), Vector2i(floor(target)))
		if not p.is_empty():
			aim = Vector2(p[0]) + Vector2(0.5, 0.5)
	var to := aim - pos
	var diff := wrapf(atan2(to.y, to.x) - angle, -PI, PI)
	var move := 1.0 if absf(diff) < 0.5 else 0.0
	return Vector2(move, clampf(diff * 5.0, -1.0, 1.0))
