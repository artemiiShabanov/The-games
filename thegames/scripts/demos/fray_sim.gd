class_name FraySim
extends RefCounted
## Правила демки файтинг × «продвинутые» «один против всех» (#125) без окна. Демка
## `fighting_threed.gd` рисует это состояние и озвучивает события `events`; `simulate` гоняет
## бота по сиду целиком (проверки `demo_test`, `debug/tools/dump_fray.gd`).
##
## Герой один на палубе, пираты стоят вокруг и нападают по очереди, а в последней волне
## иногда по двое. Стик ведёт героя по палубе. Удар: герой перелетает к ближнему врагу в
## сторону стика и бьёт, встав ровно на длину своего удара; удары идут цепочкой (левой,
## правой, ногой, с разворота, снизу) и копят серию. Удар по врагу, который замахнулся и вот-вот
## ударит, это контратака: герой кувырком перелетает ему за спину и бьёт ногой в спину. Щитоносца
## обычный удар не берёт: герой отскакивает и теряет серию; щит сбивает сильный удар (кнопку
## надо держать), оглушённого бьют как всех. Замах ножа ни ударом, ни контратакой не сбить: от
## него уходят перекатом (вторая кнопка). Серия от `strong_combo` удваивает урон, каждые
## `special_every` ударов дают добивание: следующий удар укладывает любого. Пропущенный удар,
## отскок от щита и простой сжигают серию.

const DT := 1.0 / 60.0

enum Phase { COUNTDOWN, PLAY, DONE }
enum Hero { READY, DASH, AFTER, HEAVY, COUNTER, DODGE, STUN }
## Удары цепочки по порядку.
enum Blow { LEFT, RIGHT, KICK, SPIN, UPPER }
enum Foe { WALK, WINDUP, RECOVER, STAGGER, DOWN, STUNNED, OUT }

class Pirate:
	var kind := FrayPlan.Kind.THUG
	var pos := Vector2.ZERO
	var hp := 3
	var state := Foe.WALK
	var left := 0.0
	var total := 1.0
	## Угол места в кругу вокруг героя; идёт ли вплотную (выбран нападать).
	var slot := 0.0
	var close := false
	var out_for := 0.0
	var hit_for := 9.0

	func alive() -> bool:
		return state != Foe.OUT

	func winding() -> bool:
		return state == Foe.WINDUP


var plan: FrayPlan
var tuning: FightingThreedTuning
var phase := Phase.COUNTDOWN
var countdown := 0.0
var time := 0.0
var hero_hp := 100
var pos := Vector2.ZERO
## Куда герой смотрит (курс: 0 это −z).
var facing := 0.0
var hero := Hero.READY
var hero_left := 0.0
var safe_left := 0.0
var target := -1
var heavy := false
var held := 0.0
## Номер удара в цепочке (какой удар идёт или был последним) и сколько ударов сделано.
var blow := Blow.LEFT
var chain := 0
var combo := 0
var best := 0
var combo_left := 0.0
var special := false
var foes: Array[Pirate] = []
var wave := -1
var ended := false
var won := false
var landed := 0
var counters := 0
var dodges := 0
var bounces := 0
var taken := 0
var specials := 0
var kos := 0
## События шага: `[имя, …]`. `go`, `wave(номер)`, `dash(враг)`, `hit(враг, сильный ли, удар
## цепочки)`, `bounce(враг)`, `break(враг)` щит сбит, `ko(враг, добивание ли)`, `leap(враг)`
## прыжок за спину, `counter(враг)` удар в спину, `dodge`, `windup(враг)`, `miss(враг)`, `hurt(враг, урон)`, `special` добивание готово,
## `lost` серия сгорела, `win`, `dead`, `timeout`.
var events: Array[Array] = []
var bot_dir := Vector2.ZERO
var bot_a := false
var bot_b := false

var _rng := RandomNumberGenerator.new()
var _attack_left := 1.5
var _pair_left := -1.0
var _was_a := false
var _from := Vector2.ZERO
var _to := Vector2.ZERO
var _bot_hold := 0.0
var _countering := false


static func create(plan_: FrayPlan, tuning_: FightingThreedTuning) -> FraySim:
	var sim := FraySim.new()
	sim.plan = plan_
	sim.tuning = tuning_
	sim.countdown = tuning_.countdown
	sim.hero_hp = tuning_.hero_hp
	sim._rng.seed = plan_.seed
	return sim


## Прогон бота без окна до конца боя.
static func simulate(plan_: FrayPlan, tuning_: FightingThreedTuning, mode: AutoTest.BotMode) -> FraySim:
	var sim := create(plan_, tuning_)
	while not sim.ended:
		sim.bot(mode, DT)
		sim.step(DT, sim.bot_dir, sim.bot_a, sim.bot_b)
		sim.events.clear()
	return sim


func standing() -> int:
	var n := 0
	for f in foes:
		n += 1 if f.alive() else 0
	return n


func left_total() -> int:
	return plan.total() - kos


func now() -> FrayPlan.Wave:
	return plan.waves[clampi(wave, 0, plan.waves.size() - 1)]


## Щит врага сейчас держит обычный удар.
func shielded(f: Pirate) -> bool:
	return f.kind == FrayPlan.Kind.SHIELD and f.state != Foe.STUNNED and f.state != Foe.DOWN


## Удар этого врага можно перехватить контратакой.
func counterable(f: Pirate) -> bool:
	return f.winding() and f.kind != FrayPlan.Kind.KNIFE


## Урон удара героя сейчас.
func power() -> int:
	return tuning.damage * (2 if combo >= tuning.strong_combo else 1)


## Враг, чей замах сейчас можно перехватить ударом, или −1: ближайший к своему удару.
func counter_target() -> int:
	var pick_i := -1
	var soonest := INF
	for i in foes.size():
		var f := foes[i]
		if counterable(f) and f.left <= tuning.counter_window and f.left < soonest and f.pos.distance_to(pos) <= tuning.reach:
			soonest = f.left
			pick_i = i
	return pick_i


## Враг, к которому перелетит удар. Со стиком это ближний из тех, кто в его стороне (конус
## около 60°); если там никого, и без стика, просто ближний.
func pick(dir: Vector2) -> int:
	var best_i := -1
	var best_d := INF
	var aimed_i := -1
	var aimed_d := INF
	for i in foes.size():
		var f := foes[i]
		if not f.alive() or f.state == Foe.DOWN:
			continue
		var to := f.pos - pos
		if to.length() > tuning.reach:
			continue
		if to.length() < best_d:
			best_d = to.length()
			best_i = i
		if dir.length() > 0.3 and to.normalized().dot(dir.normalized()) > 0.5 and to.length() < aimed_d:
			aimed_d = to.length()
			aimed_i = i
	return aimed_i if aimed_i >= 0 else best_i


## Шаг мира: стик (x, z в мире: ход героя и сторона удара), держат ли удар, нажат ли на этом
## шаге перекат.
func step(dt: float, dir: Vector2, a: bool, b: bool) -> void:
	if ended:
		return
	if phase == Phase.COUNTDOWN:
		countdown -= dt
		if countdown <= 0.0:
			phase = Phase.PLAY
			events.append([&"go"])
			_next_wave()
		return
	time += dt
	dir = dir.limit_length(1.0)
	safe_left = maxf(safe_left - dt, 0.0)
	if combo > 0:
		combo_left -= dt
		if combo_left <= 0.0:
			_lose_combo()
	_step_hero(dt, dir, a, b)
	_was_a = a
	held = held + dt if hero == Hero.HEAVY else 0.0
	_director(dt)
	for i in foes.size():
		_step_foe(i, dt)
	if wave < plan.waves.size() - 1 and standing() <= tuning.next_wave_at:
		_next_wave()
	if hero_hp <= 0:
		ended = true
		phase = Phase.DONE
		events.append([&"dead"])
	elif wave >= plan.waves.size() - 1 and standing() == 0:
		won = true
		ended = true
		phase = Phase.DONE
		events.append([&"win"])
	elif time > tuning.max_seconds:
		ended = true
		phase = Phase.DONE
		events.append([&"timeout"])


func _next_wave() -> void:
	wave += 1
	var w := plan.waves[wave]
	for i in w.kinds.size():
		var f := Pirate.new()
		f.kind = w.kinds[i] as FrayPlan.Kind
		f.hp = tuning.foe_hp
		f.pos = Vector2(cos(w.angles[i]), sin(w.angles[i])) * (tuning.arena + 2.5)
		f.slot = w.angles[i]
		foes.append(f)
	events.append([&"wave", wave])


func _lose_combo() -> void:
	if combo > 0:
		events.append([&"lost"])
	combo = 0
	special = false


func _gain_combo() -> void:
	combo += 1
	best = maxi(best, combo)
	combo_left = tuning.combo_seconds
	if combo % tuning.special_every == 0:
		special = true
		events.append([&"special"])


func _step_hero(dt: float, dir: Vector2, a: bool, b: bool) -> void:
	var t := tuning
	if hero != Hero.READY:
		hero_left -= dt
		match hero:
			Hero.DASH:
				var k := clampf(1.0 - hero_left / t.dash, 0.0, 1.0)
				pos = _from.lerp(_to, k)
				if hero_left <= 0.0:
					if heavy and a:
						# Кнопку держат: замах сильного удара.
						hero = Hero.HEAVY
						hero_left = maxf(t.heavy_hold - t.dash, 0.08) + t.heavy_swing
					else:
						heavy = false
						_hit()
			Hero.HEAVY:
				if not a and hero_left > t.heavy_swing:
					# Отпустил раньше: вышел обычный удар.
					heavy = false
					_hit()
				elif hero_left <= 0.0:
					_hit()
			Hero.COUNTER:
				# Кувырок за спину по дуге, в конце удар ногой в спину.
				var k := clampf(1.0 - hero_left / t.counter_seconds, 0.0, 1.0)
				pos = _from.lerp(_to, k)
				if hero_left <= 0.0:
					_counter_hit()
			Hero.DODGE:
				var k := clampf(1.0 - hero_left / t.dodge_seconds, 0.0, 1.0)
				pos = _from.lerp(_to, sin(k * PI / 2.0))
				if hero_left <= 0.0:
					hero = Hero.READY
			_:
				if hero_left <= 0.0:
					hero = Hero.READY
	var free := hero == Hero.READY or hero == Hero.AFTER
	# Перекат: в сторону стика, без стика назад. Доступен и сразу после удара.
	if b and free:
		var away := dir.normalized() if dir.length() > 0.4 else -Vector2(-sin(facing), -cos(facing))
		hero = Hero.DODGE
		hero_left = t.dodge_seconds
		safe_left = t.dodge_safe
		_from = pos
		_to = (pos + away * t.dodge_length).limit_length(t.arena)
		facing = atan2(-away.x, -away.y)
		dodges += 1
		events.append([&"dodge"])
		return
	# Удар по нажатию: перехват замаха, если есть что перехватывать, иначе удар цепочки.
	if a and not _was_a and free:
		_press(dir)
		return
	if hero == Hero.READY and dir.length() > 0.15:
		# Ход по палубе.
		pos = (pos + dir * t.walk_speed * dt).limit_length(t.arena)
		facing = rotate_toward(facing, atan2(-dir.x, -dir.y), 14.0 * dt)
		for f in foes:
			var gap := pos - f.pos
			if f.alive() and f.state != Foe.DOWN and gap.length() < 0.9 and gap.length() > 0.01:
				pos = f.pos + gap.normalized() * 0.9


func _press(dir: Vector2) -> void:
	var t := tuning
	# Перехват: враг в стороне стика, а без стика любой, кто вот-вот ударит.
	var grab := counter_target()
	var aimed := pick(dir)
	if grab >= 0 and (dir.length() <= 0.3 or aimed == grab or (foes[grab].pos - pos).normalized().dot(dir.normalized()) > 0.3):
		var f := foes[grab]
		var through := (f.pos - pos).normalized() if f.pos.distance_to(pos) > 0.05 else Vector2(-sin(facing), -cos(facing))
		target = grab
		hero = Hero.COUNTER
		hero_left = t.counter_seconds
		safe_left = maxf(safe_left, t.counter_seconds + 0.12)
		_from = pos
		_to = (f.pos + through * t.contact[Blow.KICK]).limit_length(t.arena + 0.3)
		# Враг теряет замах: он бьёт туда, где героя уже нет.
		f.state = Foe.RECOVER
		f.left = t.counter_seconds + 0.2
		f.close = false
		events.append([&"leap", grab])
		return
	# Обычный удар ждёт конца прошлого; перехват можно нажать и сразу после удара.
	if hero != Hero.READY:
		return
	target = aimed
	if target < 0:
		return
	var f := foes[target]
	heavy = shielded(f) and not special
	blow = (chain % Blow.size()) as Blow
	var to := f.pos - pos
	var stand: float = t.contact[blow]
	hero = Hero.DASH
	hero_left = t.dash
	_from = pos
	_to = f.pos - to.normalized() * stand if to.length() > 0.05 else pos
	facing = atan2(-to.x, -to.y)
	events.append([&"dash", target])


## Удар в спину после кувырка.
func _counter_hit() -> void:
	var t := tuning
	var f := foes[target]
	hero = Hero.AFTER
	hero_left = t.after_hit
	var to := f.pos - pos
	facing = atan2(-to.x, -to.y)
	blow = Blow.KICK
	chain += 1
	counters += 1
	if not f.alive():
		return
	f.hp -= t.counter_damage * (2 if combo >= t.strong_combo else 1)
	f.hit_for = 0.0
	f.pos = (f.pos + to.normalized() * t.knock * 2.0).limit_length(t.arena + 0.4)
	_gain_combo()
	events.append([&"counter", target])
	if f.hp <= 0:
		_ko(target, false)
	else:
		f.state = Foe.DOWN
		f.left = t.down_seconds


## Удар героя дошёл.
func _hit() -> void:
	var t := tuning
	var f := foes[target]
	hero = Hero.AFTER
	hero_left = t.after_hit
	chain += 1
	if not f.alive():
		return
	var to := f.pos - pos
	if special:
		# Добивание укладывает любого.
		special = false
		specials += 1
		landed += 1
		blow = Blow.SPIN
		_gain_combo()
		_ko(target, true)
		return
	if shielded(f):
		if heavy:
			f.state = Foe.STUNNED
			f.left = t.shield_stun
			f.hit_for = 0.0
			landed += 1
			_gain_combo()
			events.append([&"break", target])
		else:
			bounces += 1
			hero_left = t.bounce
			_lose_combo()
			events.append([&"bounce", target])
		return
	landed += 1
	f.hp -= power()
	f.hit_for = 0.0
	f.pos = (f.pos + to.normalized() * t.knock).limit_length(t.arena + 0.4)
	_gain_combo()
	events.append([&"hit", target, heavy, blow])
	if f.hp <= 0:
		_ko(target, false)
	elif f.state == Foe.WINDUP and f.kind == FrayPlan.Kind.KNIFE:
		# Замах ножа ударом не сбить.
		pass
	elif f.state != Foe.STUNNED:
		f.state = Foe.DOWN if heavy else Foe.STAGGER
		f.left = t.down_seconds if heavy else t.stagger
		f.close = false


func _ko(index: int, finisher: bool) -> void:
	var f := foes[index]
	f.state = Foe.OUT
	f.out_for = 0.0
	f.hit_for = 0.0
	f.hp = 0
	kos += 1
	events.append([&"ko", index, finisher])


## Кто нападает следующим: один из стоящих рядом, а дальше по волнам и второй следом.
func _director(dt: float) -> void:
	_attack_left -= dt
	if _pair_left >= 0.0:
		_pair_left -= dt
		if _pair_left < 0.0:
			_send()
	if _attack_left > 0.0:
		return
	if _send():
		_attack_left = now().gap * _rng.randf_range(0.85, 1.2)
		if _rng.randf() < now().pair:
			_pair_left = tuning.pair_gap
	else:
		_attack_left = 0.25


func _send() -> bool:
	var ready: Array[int] = []
	for i in foes.size():
		var f := foes[i]
		if f.state == Foe.WALK and f.pos.distance_to(pos) <= tuning.strike_range + 1.6:
			ready.append(i)
	if ready.is_empty():
		return false
	var f := foes[ready[_rng.randi_range(0, ready.size() - 1)]]
	f.close = true
	f.state = Foe.WINDUP
	f.left = now().windup
	f.total = f.left
	events.append([&"windup", foes.find(f)])
	return true


func _step_foe(index: int, dt: float) -> void:
	var t := tuning
	var f := foes[index]
	f.hit_for += dt
	if f.state == Foe.OUT:
		f.out_for += dt
		return
	# Место в кругу вокруг героя; замахнувшийся подходит вплотную.
	if f.state == Foe.WALK or f.state == Foe.WINDUP:
		var want := pos + Vector2(cos(f.slot), sin(f.slot)) * (t.ring if f.close else t.ring_far)
		for other in foes:
			if other != f and other.alive() and other.pos.distance_to(f.pos) < 1.3:
				want += (f.pos - other.pos).normalized() * 0.8
		f.pos = f.pos.move_toward(want.limit_length(t.arena + 0.4), t.foe_speed * (1.5 if f.state == Foe.WINDUP else 1.0) * dt)
		var to_hero := f.pos - pos
		if to_hero.length() < 1.0 and to_hero.length() > 0.01:
			f.pos = pos + to_hero.normalized()
	match f.state:
		Foe.WALK:
			pass
		Foe.WINDUP:
			f.left -= dt
			if f.left <= 0.0:
				f.state = Foe.RECOVER
				f.left = t.foe_recover
				f.close = false
				if safe_left > 0.0 or f.pos.distance_to(pos) > t.strike_range:
					events.append([&"miss", index])
				else:
					var amount := t.knife_damage if f.kind == FrayPlan.Kind.KNIFE else (t.shield_damage if f.kind == FrayPlan.Kind.SHIELD else t.thug_damage)
					hero_hp = maxi(hero_hp - amount, 0)
					taken += 1
					hero = Hero.STUN
					hero_left = t.stun
					_lose_combo()
					events.append([&"hurt", index, amount])
		_:
			f.left -= dt
			if f.left <= 0.0:
				f.state = Foe.WALK


# --- Боты ------------------------------------------------------------------------------------

## Бот: ставит `bot_dir`, `bot_a`, `bot_b`. WIN от ножа уходит перекатом, остальные замахи
## перехватывает ударом, в остальное время бьёт: щитоносца сильным ударом (держит кнопку),
## остальных короткими нажатиями; добивание тратит на щитоносца или на того, кто с ножом.
## LOSE стоит.
func bot(mode: AutoTest.BotMode, dt: float) -> void:
	bot_dir = Vector2.ZERO
	bot_b = false
	var was := bot_a
	bot_a = false
	if ended or mode != AutoTest.BotMode.WIN or phase != Phase.PLAY:
		return
	if hero == Hero.DASH or hero == Hero.HEAVY:
		# Сильный удар: кнопка зажата до конца замаха.
		bot_a = heavy
		return
	var free := hero == Hero.READY or hero == Hero.AFTER
	if not free:
		return
	# Угрозы: от ножа перекат, обычный замах перехватить.
	for f in foes:
		if f.winding() and f.kind == FrayPlan.Kind.KNIFE and f.left <= tuning.bot_dodge and f.pos.distance_to(pos) < tuning.strike_range + 1.0:
			bot_dir = (pos - f.pos).normalized()
			if (pos + bot_dir * 2.0).length() > tuning.arena - 0.5:
				bot_dir = Vector2(-bot_dir.y, bot_dir.x)
			bot_b = true
			return
	var grab := counter_target()
	if grab >= 0:
		if foes[grab].left <= tuning.bot_counter:
			bot_a = not was
		return
	# Цель: добивание на щит или нож; иначе ближний без щита, если таких нет, щитоносец.
	var open := -1
	var shield := -1
	var prize := -1
	var near := INF
	for i in foes.size():
		var f := foes[i]
		if not f.alive() or f.state == Foe.DOWN or f.pos.distance_to(pos) > tuning.reach:
			continue
		# Того, кто замахнулся ножом, не трогает: удар его не собьёт.
		if f.winding() and f.kind == FrayPlan.Kind.KNIFE:
			continue
		if shielded(f):
			shield = i
			prize = i
		else:
			if f.kind == FrayPlan.Kind.KNIFE and prize < 0:
				prize = i
			if f.pos.distance_to(pos) < near:
				near = f.pos.distance_to(pos)
				open = i
	var pick_i := prize if special and prize >= 0 else (open if open >= 0 else shield)
	if pick_i < 0:
		return
	bot_dir = (foes[pick_i].pos - pos).normalized()
	bot_a = not was
