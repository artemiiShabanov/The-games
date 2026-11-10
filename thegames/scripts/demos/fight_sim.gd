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

enum State { IDLE, WALK, CROUCH, BLOCK, STRIKE, HIT, GUARD, KO }
enum Move { NONE, HIGH, LOW }
## Фаза удара: замах, активные шаги (бьёт), восстановление.
enum Part { STARTUP, ACTIVE, RECOVERY }


class Fighter:
	var x := 0.0
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


## Ввод бойца на шаг: ось по экрану (−1, 0, 1), присед, A нажата в этот шаг, B зажата.
class Controls:
	var x := 0
	var down := false
	var a := false
	var b := false


## Событие шага для звука и искр: `hit`, `guard`, `ko`, `swing`, `dodge`.
class Event:
	var kind: StringName
	var pos := Vector2.ZERO
	## Событие у героя (его удар, его блок) или у соперника.
	var by_hero := true


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


func _init(tuning: FightDemoTuning, center: float) -> void:
	t = tuning
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


static func actionable(f: Fighter) -> bool:
	return f.state == State.IDLE or f.state == State.WALK or f.state == State.CROUCH or f.state == State.BLOCK


static func crouched(f: Fighter) -> bool:
	return f.state == State.CROUCH or (f.state == State.STRIKE and f.move == Move.LOW)


## Шаги удара: замах, активные, восстановление.
func frames(move: Move) -> Vector3i:
	if move == Move.LOW:
		return Vector3i(t.low_startup, t.low_active, t.low_recovery)
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


## Прямоугольник по взгляду бойца в мир: `r` задан для взгляда вправо.
static func _world(f: Fighter, r: Rect2) -> Rect2:
	if f.face > 0:
		return Rect2(f.x + r.position.x, r.position.y, r.size.x, r.size.y)
	return Rect2(f.x - r.position.x - r.size.x, r.position.y, r.size.x, r.size.y)


func hurt_rect(f: Fighter) -> Rect2:
	return _world(f, t.crouch_hurt if crouched(f) else t.stand_hurt)


## Кулак или нога в активных шагах, иначе пустой прямоугольник.
func hit_rect(f: Fighter) -> Rect2:
	if f.state != State.STRIKE or part(f) != Part.ACTIVE:
		return Rect2()
	return _world(f, t.low_hit if f.move == Move.LOW else t.high_hit)


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
	if not actionable(f):
		return
	var was := f.state
	if f.buffer > 0:
		f.buffer = 0
		f.state = State.STRIKE
		f.move = Move.LOW if inp.down else Move.HIGH
		f.t = 0
		f.connected = false
		f.dodge_counted = false
		f.move_id += 1
		f.walk_t = 0
		if f.move == Move.LOW:
			f.lows += 1
		else:
			f.highs += 1
		_event(&"swing", Vector2(f.x, -16.0), f == hero)
		return
	if inp.down:
		f.state = State.CROUCH
	elif inp.b:
		f.state = State.BLOCK
	elif inp.x != 0:
		f.state = State.WALK
		var speed := t.walk_forward if inp.x == f.face else t.walk_back
		f.x = clampf(f.x + inp.x * speed / t.physics_hz, left, right)
		f.walk_t += 1
	else:
		f.state = State.IDLE
	if f.state != State.WALK:
		f.walk_t = 0
	if f.state != was:
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
				f.state = State.CROUCH if f.move == Move.LOW else State.IDLE
				f.move = Move.NONE
				f.t = 0
		State.HIT, State.GUARD:
			f.stun -= 1
			f.t += 1
			if f.stun <= 0:
				f.state = State.IDLE
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
			landed.append(att)
			points.append(hb.intersection(hurt_rect(def)).get_center())
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
	var blocked := not low and (def.state == State.BLOCK or def.state == State.GUARD)
	var push: float
	if blocked:
		def.state = State.GUARD
		def.stun = t.high_blockstun
		def.t = 0
		def.blocks += 1
		att.guarded += 1
		push = t.block_push
		_event(&"guard", at, def == hero)
	else:
		var dmg := t.low_damage if low else t.high_damage
		def.health = maxi(def.health - dmg, 0)
		att.landed += 1
		att.damage += dmg
		def.state = State.HIT
		def.stun = t.low_hitstun if low else t.high_hitstun
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
	# Отброс от бьющего; что не влезло до борта, отъезжает бьющий.
	var dir := 1.0 if def.x >= att.x else -1.0
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
static func simulate(plan: FightPlan, tuning: FightDemoTuning, gen: FightGenTuning, mode: AutoTest.BotMode) -> FightSim:
	var sim := FightSim.new(tuning, 0.0)
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
