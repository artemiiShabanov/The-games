class_name FightSim
extends RefCounted
## Бой файтинга × 8-bit (#54) без рисования: два бойца на палубе, шаг ровный (`step`, 1 /
## `physics_hz`), ввод каждого на шаг (`Controls`). Демка рисует его и кормит вводом игрока или
## бота, проверка `demo_test` гоняет его без окна (`simulate`), тот же код.
##
## Правила. Влево, вправо шаг (назад медленнее), вниз присед, B зажать блок стоя (вниз с B это
## присед), A удар: стоя верхний, в приседе нижний. Верхний быстрый и длинный, на уровне лица:
## блок его держит, присед уходит (кулак проходит над головой). Нижний медленнее, короче и
## слабее, у самой палубы: его не держат ни блок, ни присед, спасает только дистанция. Удар
## разбит на замах, активные шаги и восстановление; попадание даёт урон, оглушение и отброс,
## блок оглушение в блоке и отброс без урона. Боец у борта не отъезжает: отъезжает бьющий.
## Бойцы всегда лицом друг к другу, пока свободны; ближе `2 * push_half` не сходятся.
##
## Плейтест #54: в приседе можно идти (медленнее), во время удара ход сохраняется затухающе
## (`strike_move` в начале, к концу удара ноль), вверх прыжок по дуге с ударом ногой в воздухе
## (держит блок стоя, достаёт присевшего на снижении), удары героя под капотом длиннее
## (`hero_reach_mult`), кадры те же.
##
## Баги жанра и баланса (#55) тоже правила боя (`Bugs`): демка задаёт их один раз из ресурсов
## багов, проверка без окна и дамп тем же `Bugs.from_catalog`, так что бой с багами тот же до бита.

enum State { IDLE, WALK, CROUCH, BLOCK, STRIKE, HIT, GUARD, KO, JUMP }
enum Move { NONE, HIGH, LOW, AIR }
## Фаза удара: замах, активные шаги (бьёт), восстановление.
enum Part { STARTUP, ACTIVE, RECOVERY }


class Fighter:
	var x := 0.0
	## Высота над палубой (вверх положительная) и скорости прыжка, px/с.
	var y := 0.0
	var vy := 0.0
	var vx := 0.0
	## Удар ногой в этом прыжке уже был: один на прыжок.
	var air_used := false
	## Взгляд: 1 вправо, −1 влево.
	var face := 1
	var state := State.IDLE
	var move := Move.NONE
	## Шагов в текущем состоянии (у удара шаг удара с единицы).
	var t := 0
	## Осталось шагов оглушения (HIT, GUARD).
	var stun := 0
	var health := 100
	## Отброс, который ещё доедет, px со знаком.
	var slide := 0.0
	## Удар уже попал или ушёл в блок; присед под ним уже засчитан.
	var connected := false
	var dodge_counted := false
	## Номер удара: соперник реагирует на каждый удар один раз.
	var move_id := 0
	## Нажатая A ждёт свободы столько шагов.
	var buffer := 0
	## Шагов ходьбы подряд, для кадра шага.
	var walk_t := 0
	# Счёт для итога и заметок.
	var highs := 0
	var lows := 0
	var landed := 0
	var guarded := 0
	var blocks := 0
	var dodges := 0
	var damage := 0
	## «Мимо хитбокса» (#55): удар уже прошёл сквозь, его хитбокс смещён за спину до конца удара;
	## касаний ударами и сколько из них прошло сквозь.
	var ghost := false
	var contacts := 0
	var ghosts := 0


## Ввод бойца на шаг: ось по экрану (−1, 0, 1), прыжок, присед, A нажата в этот шаг, B зажата.
class Controls:
	var x := 0
	var up := false
	var down := false
	var a := false
	var b := false


## Событие шага для звука и искр: `hit`, `guard`, `ko`, `swing`, `dodge`.
class Event:
	var kind: StringName
	var pos := Vector2.ZERO
	## Событие у героя (его удар, его блок) или у соперника.
	var by_hero := true


## Баги жанра и баланса в правилах боя (#55), спека `docs/specs/demos.md`. Демка заполняет
## один раз в `_setup_bugs`, проверка и дамп тем же `from_catalog`; по умолчанию всё выключено.
class Bugs:
	## «Мимо хитбокса» (`ghost_hits`, жанровый баг файтинга): у каждого бойца каждое
	## `pass_every`-е касание удара с телом соперника, начиная с первого, проходит сквозь: хитбокс
	## удара до его конца смещён за спину бьющего на `ghost_shift` px. 0 без бага.
	var pass_every := 0
	var ghost_shift := 0.0
	## Чих (`sneeze_enemies`): любое касание удара героя с капитаном, и в блок, нокаут с отбросом
	## `sneeze_push` px.
	var sneeze := false
	var sneeze_push := 0.0
	## «Не достать» (`unreachable_coins`): капитан бессмертен, удары по нему без урона.
	var immortal := false
	## Дикая физика (`wild_physics`): тяжесть в `jump_mult` раз меньше (прыжок во столько же выше
	## и дольше), чистое попадание подбрасывает на `launch_speed` и уносит на `fling_speed` от
	## бьющего, px/с. 0 без бага.
	var jump_mult := 1.0
	var launch_speed := 0.0
	var fling_speed := 0.0

	func any() -> bool:
		return pass_every > 0 or sneeze or immortal or launch_speed > 0.0 or jump_mult != 1.0

	## Правила по списку багов записи и параметрам из каталога (`resources/bugs/<id>.tres`).
	static func from_catalog(ids: Array[StringName], catalog: BugCatalog) -> Bugs:
		var b := Bugs.new()
		if catalog == null:
			return b
		var ghost := catalog.by_id(&"ghost_hits")
		if ids.has(&"ghost_hits") and ghost != null:
			b.pass_every = maxi(int(ghost.param(&"pass_every", 2.0)), 1)
			b.ghost_shift = ghost.param(&"ghost_shift", 32.0)
		var sneeze := catalog.by_id(&"sneeze_enemies")
		if ids.has(&"sneeze_enemies") and sneeze != null:
			b.sneeze = true
			b.sneeze_push = sneeze.param(&"fight_ko_push", 72.0)
		b.immortal = ids.has(&"unreachable_coins")
		var wild := catalog.by_id(&"wild_physics")
		if ids.has(&"wild_physics") and wild != null:
			b.jump_mult = maxf(wild.param(&"jump_mult", 3.0), 0.1)
			b.launch_speed = wild.param(&"fight_launch_speed", 120.0)
			b.fling_speed = wild.param(&"fight_fling_speed", 70.0)
		return b


var t: FightDemoTuning
var hero := Fighter.new()
var rival := Fighter.new()
## Пределы положения бойца (середина), px.
var left := 0.0
var right := 0.0
var frame := 0
## Раунд кончился: шаги ещё доигрывают отброс и падение, но время боя (`frame`) стоит.
var stopped := false
## Шагов с начала, для анимации (идёт и после конца раунда).
var ticks := 0
var hitstop := 0
var events: Array[Event] = []
var bugs := Bugs.new()
## Счёт багов для заметок: капитан упал от первого касания, удары по бессмертному, подбросы,
## самый высокий полёт над палубой, px.
var sneezes := 0
var shrugged := 0
var flings := 0
var max_air := 0.0


func _init(tuning: FightDemoTuning, center: float, bugs_: Bugs = null) -> void:
	t = tuning
	if bugs_ != null:
		bugs = bugs_
	left = center - t.arena_width / 2.0 + t.push_half
	right = center + t.arena_width / 2.0 - t.push_half
	hero.x = center - t.start_gap / 2.0
	hero.face = 1
	hero.health = t.health
	rival.x = center + t.start_gap / 2.0
	rival.face = -1
	rival.health = t.health


func seconds() -> float:
	return float(frame) / t.physics_hz


func knocked_out() -> bool:
	return hero.state == State.KO or rival.state == State.KO


## Свободен для нового действия: стоит, идёт, сидит или в блоке и на палубе.
static func actionable(f: Fighter) -> bool:
	return (f.state == State.IDLE or f.state == State.WALK or f.state == State.CROUCH or f.state == State.BLOCK) \
			and not airborne(f)


static func crouched(f: Fighter) -> bool:
	return f.state == State.CROUCH or (f.state == State.STRIKE and f.move == Move.LOW)


## Шаги удара: замах, активные, восстановление.
func frames(move: Move) -> Vector3i:
	if move == Move.LOW:
		return Vector3i(t.low_startup, t.low_active, t.low_recovery)
	if move == Move.AIR:
		return Vector3i(t.air_startup, t.air_active, t.air_recovery)
	return Vector3i(t.high_startup, t.high_active, t.high_recovery)


func total(move: Move) -> int:
	var f := frames(move)
	return f.x + f.y + f.z


static func part_of(f: Fighter, fr: Vector3i) -> Part:
	if f.t <= fr.x:
		return Part.STARTUP
	if f.t <= fr.x + fr.y:
		return Part.ACTIVE
	return Part.RECOVERY


func part(f: Fighter) -> Part:
	return part_of(f, frames(f.move))


## Прямоугольник по взгляду бойца в мир: `r` задан для взгляда вправо, в прыжке поднят на `y`.
static func _world(f: Fighter, r: Rect2) -> Rect2:
	if f.face > 0:
		return Rect2(f.x + r.position.x, r.position.y - f.y, r.size.x, r.size.y)
	return Rect2(f.x - r.position.x - r.size.x, r.position.y - f.y, r.size.x, r.size.y)


static func airborne(f: Fighter) -> bool:
	return f.y > 0.0 or f.vy > 0.0


func hurt_rect(f: Fighter) -> Rect2:
	return _world(f, t.crouch_hurt if crouched(f) else t.stand_hurt)


## Кулак или нога в активных шагах, иначе пустой прямоугольник.
func hit_rect(f: Fighter) -> Rect2:
	if f.state != State.STRIKE or part(f) != Part.ACTIVE:
		return Rect2()
	var r := t.strike_rect(f.move)
	if f == hero:
		# Удар героя длиннее, чем нарисован: дальний край дальше в `hero_reach_mult` раз.
		r.size.x = (r.position.x + r.size.x) * t.hero_reach_mult - r.position.x
	if f.ghost:
		# «Мимо хитбокса»: удар прошёл сквозь, его хитбокс за спиной бьющего.
		r.position.x -= bugs.ghost_shift
	return _world(f, r)


func other(f: Fighter) -> Fighter:
	return rival if f == hero else hero


## Шаг боя. Порядок: ввод, отброс, расталкивание, взгляд, счёт шагов, попадания.
func step(hero_in: Controls, rival_in: Controls) -> void:
	events.clear()
	ticks += 1
	if hitstop > 0:
		hitstop -= 1
		return
	if not stopped:
		frame += 1
	_control(hero, hero_in)
	_control(rival, rival_in)
	_air(hero)
	_air(rival)
	_slide(hero)
	_slide(rival)
	_separate()
	for f: Fighter in [hero, rival]:
		if actionable(f):
			var d := other(f).x - f.x
			if absf(d) > 0.01:
				f.face = 1 if d > 0.0 else -1
	_tick(hero)
	_tick(rival)
	_strikes()


func _control(f: Fighter, inp: Controls) -> void:
	if f.state == State.KO:
		return
	if inp.a:
		f.buffer = t.buffer
	elif f.buffer > 0:
		f.buffer -= 1
	if f.state == State.STRIKE and not airborne(f) and inp.x != 0:
		# Ход во время удара затухает к его концу.
		var k := 1.0 - float(f.t) / float(total(f.move))
		f.x = clampf(f.x + inp.x * _walk_speed(f, inp.x) * t.strike_move * k / t.physics_hz, left, right)
	if f.state == State.JUMP and f.buffer > 0 and not f.air_used:
		f.air_used = true
		_start_strike(f, Move.AIR)
		return
	if not actionable(f):
		return
	var was := f.state
	if f.buffer > 0:
		_start_strike(f, Move.LOW if inp.down else Move.HIGH)
		return
	if inp.up and not inp.down:
		f.state = State.JUMP
		f.t = 0
		f.walk_t = 0
		f.vy = t.jump_speed
		f.vx = inp.x * t.jump_drift
		f.air_used = false
		return
	if inp.down:
		f.state = State.CROUCH
		if inp.x != 0:
			f.x = clampf(f.x + inp.x * t.crouch_walk / t.physics_hz, left, right)
	elif inp.b:
		f.state = State.BLOCK
	elif inp.x != 0:
		f.state = State.WALK
		f.x = clampf(f.x + inp.x * _walk_speed(f, inp.x) / t.physics_hz, left, right)
		f.walk_t += 1
	else:
		f.state = State.IDLE
	if f.state != State.WALK:
		f.walk_t = 0
	if f.state != was:
		f.t = 0


func _walk_speed(f: Fighter, dir: int) -> float:
	return t.walk_forward if dir == f.face else t.walk_back


func _start_strike(f: Fighter, move: Move) -> void:
	f.buffer = 0
	f.state = State.STRIKE
	f.move = move
	f.t = 0
	f.connected = false
	f.dodge_counted = false
	f.ghost = false
	f.move_id += 1
	f.walk_t = 0
	if f.move == Move.LOW:
		f.lows += 1
	else:
		f.highs += 1
	_event(&"swing", Vector2(f.x, -16.0 - f.y), f == hero)


## Прыжок по дуге: снос вбок задан при отрыве, на палубе прыжок и удар в воздухе кончаются.
func _air(f: Fighter) -> void:
	if not airborne(f):
		return
	f.x = clampf(f.x + f.vx / t.physics_hz, left, right)
	f.vy -= t.jump_gravity / bugs.jump_mult / t.physics_hz
	f.y += f.vy / t.physics_hz
	if f.y > 0.0:
		max_air = maxf(max_air, f.y)
		return
	f.y = 0.0
	f.vy = 0.0
	f.vx = 0.0
	if f.state == State.JUMP or (f.state == State.STRIKE and f.move == Move.AIR):
		f.state = State.IDLE
		f.move = Move.NONE
		f.t = 0


func _slide(f: Fighter) -> void:
	if absf(f.slide) < 0.01:
		f.slide = 0.0
		return
	var d := signf(f.slide) * minf(absf(f.slide), maxf(absf(f.slide) * 0.3, 0.5))
	f.x = clampf(f.x + d, left, right)
	f.slide -= d


## Ближе `2 * push_half` бойцы расходятся поровну; у борта отходит второй.
func _separate() -> void:
	var gap := 2.0 * t.push_half
	var d := rival.x - hero.x
	if absf(d) >= gap:
		return
	var s := 1.0 if d >= 0.0 else -1.0
	var mid := (hero.x + rival.x) / 2.0
	mid = clampf(mid, left + gap / 2.0, right - gap / 2.0)
	hero.x = mid - s * gap / 2.0
	rival.x = mid + s * gap / 2.0


func _tick(f: Fighter) -> void:
	match f.state:
		State.STRIKE:
			f.t += 1
			if f.t > total(f.move):
				if f.move == Move.AIR:
					f.state = State.JUMP if airborne(f) else State.IDLE
				else:
					f.state = State.CROUCH if f.move == Move.LOW else State.IDLE
				f.move = Move.NONE
				f.t = 0
		State.HIT, State.GUARD:
			f.stun -= 1
			f.t += 1
			if f.stun <= 0:
				# Оглушили в прыжке: падает дальше в позе прыжка, без удара ногой.
				f.state = State.JUMP if airborne(f) else State.IDLE
				f.air_used = true
				f.t = 0
		_:
			f.t += 1


## Попадания этого шага: оба удара проверяются до того, как применяются (размен бывает).
func _strikes() -> void:
	var landed: Array[Fighter] = []
	var points: Array[Vector2] = []
	for att: Fighter in [hero, rival]:
		var def := other(att)
		if att.state != State.STRIKE or att.connected or def.state == State.KO:
			continue
		var hb := hit_rect(att)
		if hb.size == Vector2.ZERO:
			continue
		if hb.intersects(hurt_rect(def)):
			var at := hb.intersection(hurt_rect(def)).get_center()
			if bugs.pass_every > 0:
				# «Мимо хитбокса»: каждое `pass_every`-е касание, начиная с первого, сквозь.
				var through := att.contacts % bugs.pass_every == 0
				att.contacts += 1
				if through:
					att.ghost = true
					att.ghosts += 1
					_event(&"ghost", at, att == hero)
					continue
			landed.append(att)
			points.append(at)
		elif att.move == Move.HIGH and crouched(def) and not att.dodge_counted \
				and hb.intersects(_world(def, t.stand_hurt)):
			# Кулак прошёл над головой присевшего.
			att.dodge_counted = true
			def.dodges += 1
			_event(&"dodge", Vector2(def.x, -20.0), def == hero)
	for i in landed.size():
		_apply(landed[i], other(landed[i]), points[i])


func _apply(att: Fighter, def: Fighter, at: Vector2) -> void:
	att.connected = true
	var low := att.move == Move.LOW
	var air := att.move == Move.AIR
	# Чих: любое касание удара героя валит капитана, и в блок.
	var fragile := bugs.sneeze and def == rival
	var blocked := not low and (def.state == State.BLOCK or def.state == State.GUARD) and not fragile
	var dir := 1.0 if def.x >= att.x else -1.0
	var push: float
	if blocked:
		def.state = State.GUARD
		def.stun = t.air_blockstun if air else t.high_blockstun
		def.t = 0
		def.blocks += 1
		att.guarded += 1
		push = t.block_push
		_event(&"guard", at, def == hero)
	else:
		var dmg := t.low_damage if low else (t.air_damage if air else t.high_damage)
		if fragile:
			dmg = def.health
			sneezes += 1
		if bugs.immortal and def == rival:
			# «Не достать»: удар засчитан, урона нет.
			dmg = 0
			shrugged += 1
		def.health = maxi(def.health - dmg, 0)
		att.landed += 1
		att.damage += dmg
		def.state = State.HIT
		def.stun = t.low_hitstun if low else (t.air_hitstun if air else t.high_hitstun)
		def.move = Move.NONE
		def.t = 0
		def.buffer = 0
		push = t.hit_push
		if def.health <= 0:
			def.state = State.KO
			push = t.ko_push
			_event(&"ko", at, att == hero)
		else:
			_event(&"hit", at, att == hero)
		if fragile:
			push = bugs.sneeze_push
		if bugs.launch_speed > 0.0:
			# Дикая физика: попадание подбрасывает и уносит по дуге вместо отброса.
			def.vy = bugs.launch_speed
			def.vx = dir * bugs.fling_speed
			def.slide = 0.0
			flings += 1
			hitstop = t.hitstop
			return
	# Отброс от бьющего; что не влезло до борта, отъезжает бьющий.
	var room := (right - def.x) if dir > 0.0 else (def.x - left)
	def.slide = dir * minf(push, room)
	if push > room:
		att.slide = -dir * (push - room)
	hitstop = t.hitstop


func _event(kind: StringName, pos: Vector2, by_hero: bool) -> void:
	var e := Event.new()
	e.kind = kind
	e.pos = pos
	e.by_hero = by_hero
	events.append(e)


## Раунд без окна: бот героя в режиме `mode` против соперника по плану до нокаута или конца
## времени. Для проверки в `demo_test` и дампа `dump_fight.gd`.
static func simulate(plan: FightPlan, tuning: FightDemoTuning, gen: FightGenTuning, mode: AutoTest.BotMode,
		bugs_: Bugs = null) -> FightSim:
	var sim := FightSim.new(tuning, 0.0, bugs_)
	var ai := FightAi.new(sim, plan, gen)
	var bot := FightBot.new(sim, mode, plan.seed)
	var limit := int(round(tuning.round_seconds * tuning.physics_hz))
	var guard := 0
	while sim.frame < limit and not sim.knocked_out() and guard < limit * 3:
		sim.step(bot.think(), ai.think())
		guard += 1
	return sim


## Победа героя: у соперника меньше здоровья (нокаут тоже).
func hero_won() -> bool:
	return hero.health > rival.health


## Сводка боя одной строкой для заметок автотеста и дампа.
func summary() -> String:
	return "здоровье %d:%d, %s на %.1f с; герой: ударов %d (верхних %d, нижних %d), попал %d, в блок %d, блоков %d, уклонов %d; соперник: ударов %d, попал %d, в блок %d, блоков %d, уклонов %d" % [
			hero.health, rival.health, "нокаут" if knocked_out() else "время", seconds(),
			hero.highs + hero.lows, hero.highs, hero.lows, hero.landed, hero.guarded, hero.blocks, hero.dodges,
			rival.highs + rival.lows, rival.landed, rival.guarded, rival.blocks, rival.dodges]


## Счёт багов одной строкой (#55), пусто без багов правил боя.
func bug_summary() -> String:
	if not bugs.any():
		return ""
	return "сквозь хитбокс у героя %d из %d касаний, у капитана %d из %d; от чиха %d; ударов без урона %d; подбросов %d, выше всего %.0f px" % [
			hero.ghosts, hero.contacts, rival.ghosts, rival.contacts, sneezes, shrugged, flings, max_air]
