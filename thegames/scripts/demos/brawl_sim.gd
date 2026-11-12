class_name BrawlSim
extends RefCounted
## Правила битемапа × 16/32-bit (#102, графика по Streets of Rage 2) без окна и звука: герой,
## враги по волнам, три экрана улицы, боты. Демка `fighting_bit16.gd` рисует это состояние и
## озвучивает события; `simulate` гоняет бота по сиду целиком (проверки `demo_test`,
## `debug/tools/dump_brawl.gd`). Мир шагает ровно 60 раз в секунду.
## Правила: улица идёт вправо, x вдоль, y вглубь полосы, z высота полёта. Экран встаёт, пока
## не побиты его враги, потом стрелка «вперёд» и следующий. Герой: ход в восьми направлениях;
## A удар, три подряд это комбо (два тычка и пинок, пинок валит); B тяжёлый удар (долгий замах,
## далеко, валит всех перед собой; плейтест 2026-11-12: вместо прыжка); вошёл во врага вплотную
## и постоял: захват, A колено, третье A бросок назад, брошенный сбивает других. Каждое
## попадание останавливает мир на доли секунды (`hitstop`) и заливает белым того, по кому
## попали. Враги идут к герою, в атаке не больше двоих, остальные ждут поодаль; удар с замахом,
## который видно. Боцман на третьем экране: крепче, раз в несколько секунд рывок через экран.
## Здоровье героя кончилось: жизнь минус, неуязвимость и волна, сбивающая врагов рядом.
## Побиты все три экрана: победа; жизни кончились: поражение.
## Баги приходят числами: `launch` от удара летят выше и дальше по дуге; `immortal`
## боцман бессмертен; `sneeze` враг падает от любого удара; `ghost_every` каждый такой удар
## героя проходит сквозь.

const DT := 1.0 / 60.0

enum State { IDLE, WALK, ATTACK, HEAVY, HURT, DOWN, GETUP, GRAB, GRABBED, THROWN, WINDUP, STRIKE, CHARGE, DEAD }

class Fighter:
	var kind := BrawlWaves.Kind.THUG
	var pos := Vector2.ZERO
	var z := 0.0
	var vz := 0.0
	var vx := 0.0
	var facing := 1.0
	var hp := 30
	var max_hp := 30
	var state := State.IDLE
	var state_t := 0.0
	var invuln := 0.0
	var combo := 0
	var combo_t := 9.0
	var hit_done := false
	var cooldown := 0.0
	var touch := 0.0
	var knees := 0
	var name := ""
	var charge_t := 0.0
	var gone := false
	## Белая заливка после попадания, секунды.
	var flash := 0.0

var tuning: FightingBit16Tuning
var waves: BrawlWaves
var launch := 0.0
var immortal := false
var sneeze := false
var ghost_every := 0

var hero := Fighter.new()
var foes: Array[Fighter] = []
var lives := 3
var screen := 0
## Левый край камеры (только вперёд) и встала ли она на экране.
var cam_x := 0.0
var locked := false
var time := 0.0
var ended := false
var won := false
var hits := 0
var kills := 0
var deaths := 0
## Захваченный враг (индекс) или −1.
var held := -1
## Стоп-кадр после попадания: секунды, пока мир стоит.
var hitstop := 0.0
## События шага: `[имя, …]`. `swing` (кто: −1 герой, иначе индекс; вид: jab, kick, heavy, foe),
## `impact` (x, y, z, тяжёлый ли), `hit` (кого, урон), `down` (кого), `kill` (кого), `hurt`,
## `grab`, `knee`, `throw`, `windup` (кто), `charge`, `wave` (экран), `go`, `boss`, `life`,
## `ghost`, `win`, `lose`. Демка читает и чистит.
var events: Array[Array] = []
## Ввод бота на этом шаге.
var bot_a := false
var bot_b := false

var _pending: Array = []
var _spawn_t := 0.0


static func create(waves_: BrawlWaves, tuning_: FightingBit16Tuning) -> BrawlSim:
	var s := BrawlSim.new()
	s.waves = waves_
	s.tuning = tuning_
	s.lives = tuning_.lives
	s.hero.kind = BrawlWaves.Kind.HERO
	s.hero.hp = tuning_.health
	s.hero.max_hp = tuning_.health
	s.hero.pos = Vector2(80.0, tuning_.depth * 0.5)
	return s


static func simulate(waves_: BrawlWaves, tuning_: FightingBit16Tuning, mode: AutoTest.BotMode, setup := Callable()) -> BrawlSim:
	var s := create(waves_, tuning_)
	if setup.is_valid():
		setup.call(s)
	while not s.ended:
		var axis := s.bot(mode)
		s.step(axis, s.bot_a, s.bot_b)
		s.events.clear()
	return s


func width() -> float:
	return tuning.screen_w * waves.screens.size()


## Шаг мира в 1/60 секунды: `axis` стрелки, `a` нажата ли A на этом шаге, `b` нажата ли B.
func step(axis: Vector2, a: bool, b: bool) -> void:
	if ended:
		return
	time += DT
	if time >= tuning.max_seconds:
		_end(false)
		return
	# Стоп-кадр: мир стоит, ввод теряется (нажатие во время стоп-кадра не пропадёт у человека:
	# демка держит его до следующего шага).
	if hitstop > 0.0:
		hitstop -= DT
		return
	for f in [hero] + foes:
		f.flash = maxf(f.flash - DT, 0.0)
	_screen_step()
	_hero_step(axis, a, b)
	for i in foes.size():
		_foe_step(i)
	foes = foes.filter(func(f: Fighter) -> bool: return not f.gone)
	if held >= foes.size():
		held = -1


# --- Экраны и волны ----------------------------------------------------------------------------

func _screen_step() -> void:
	var start := screen * tuning.screen_w
	if not locked:
		# Камера идёт за героем вперёд; на начале экрана встаёт и выпускает волну.
		cam_x = maxf(cam_x, minf(hero.pos.x - tuning.screen_w * 0.4, start))
		if cam_x >= start - 0.5 and screen < waves.screens.size():
			cam_x = start
			locked = true
			_pending = waves.screens[screen].duplicate()
			_spawn_t = 0.0
			events.append([&"wave", screen])
		return
	_spawn_t += DT
	while not _pending.is_empty() and _spawn_t >= (_pending[0] as BrawlWaves.Spawn).delay:
		_spawn(_pending.pop_front())
	if _pending.is_empty() and _alive() == 0:
		locked = false
		screen += 1
		if screen >= waves.screens.size():
			_end(true)
			return
		events.append([&"go"])


func _alive() -> int:
	var n := 0
	for f in foes:
		n += 1 if f.state != State.DEAD else 0
	return n


func _spawn(sp: BrawlWaves.Spawn) -> void:
	var f := Fighter.new()
	f.kind = sp.kind
	match sp.kind:
		BrawlWaves.Kind.KNIFE:
			f.hp = tuning.knife_health
		BrawlWaves.Kind.BOSS:
			f.hp = tuning.boss_health
			events.append([&"boss"])
		_:
			f.hp = tuning.thug_health
	f.max_hp = f.hp
	f.pos = Vector2(cam_x + (tuning.screen_w + 40.0 if sp.side > 0.0 else -40.0), sp.y * tuning.depth / 70.0)
	f.facing = -sp.side
	f.cooldown = 0.6
	f.charge_t = tuning.boss_charge_every
	var idx := 0
	for s in waves.screens.slice(0, screen):
		idx += s.size()
	f.name = waves.names[mini(idx + foes.size() % 3, waves.names.size() - 1)] if sp.kind != BrawlWaves.Kind.BOSS else "Боцман"
	foes.append(f)


# --- Герой -------------------------------------------------------------------------------------

func _hero_step(axis: Vector2, a: bool, b: bool) -> void:
	var h := hero
	h.state_t += DT
	h.combo_t += DT
	h.invuln = maxf(h.invuln - DT, 0.0)
	match h.state:
		State.HURT:
			if h.state_t >= tuning.hurt_seconds:
				_to(h, State.IDLE)
			return
		State.DOWN:
			_fall(h)
			if h.state_t >= tuning.down_seconds:
				_to(h, State.GETUP)
				h.invuln = tuning.getup_seconds + 0.3
			return
		State.GETUP:
			if h.state_t >= tuning.getup_seconds:
				_to(h, State.IDLE)
			return
		State.HEAVY:
			# Замах, удар, долгое восстановление.
			if not h.hit_done and h.state_t >= tuning.heavy_windup:
				h.hit_done = true
				events.append([&"swing", -1, &"heavy"])
				_hero_hits(tuning.heavy_reach, tuning.heavy_damage, true)
			if h.state_t >= tuning.heavy_seconds:
				_to(h, State.IDLE)
			return
		State.ATTACK:
			var kick := h.combo == 2
			var dur := tuning.kick_seconds if kick else tuning.jab_seconds
			var at := tuning.kick_hit if kick else tuning.jab_hit
			if not h.hit_done and h.state_t >= at:
				h.hit_done = true
				events.append([&"swing", -1, &"kick" if kick else &"jab"])
				_hero_hits(tuning.kick_reach if kick else tuning.jab_reach, tuning.kick_damage if kick else tuning.jab_damage, kick)
			if h.state_t >= dur:
				_to(h, State.IDLE)
				h.combo_t = 0.0
			return
		State.GRAB:
			_grab_step(a)
			return
	# Свободен: удар, прыжок, ход, захват.
	if a:
		h.combo = (h.combo + 1) % 3 if h.combo_t < tuning.combo_window else 0
		h.hit_done = false
		_to(h, State.ATTACK)
		return
	if b:
		h.hit_done = false
		h.combo = 0
		_to(h, State.HEAVY)
		events.append([&"windup", -1])
		return
	var v := Vector2(axis.x * tuning.walk_x, axis.y * tuning.walk_y)
	if absf(axis.x) > 0.1:
		h.facing = signf(axis.x)
	h.pos += v * DT
	_clamp(h)
	h.state = State.WALK if v.length() > 1.0 else State.IDLE
	# Захват: вплотную к врагу, который не бьёт и не лежит.
	var near := _grab_target()
	if near >= 0 and v.length() > 1.0:
		h.touch += DT
		if h.touch >= tuning.grab_touch:
			held = near
			h.knees = 0
			_to(h, State.GRAB)
			_to(foes[near], State.GRABBED)
			events.append([&"grab"])
	else:
		h.touch = 0.0


func _grab_target() -> int:
	for i in foes.size():
		var f := foes[i]
		if f.state in [State.IDLE, State.WALK, State.HURT] and f.kind != BrawlWaves.Kind.BOSS \
				and absf(f.pos.x - hero.pos.x) < tuning.grab_reach and absf(f.pos.y - hero.pos.y) < 9.0 \
				and signf(f.pos.x - hero.pos.x) == hero.facing:
			return i
	return -1


## Захват: A колено, третье A или время вышло: бросок назад.
func _grab_step(a: bool) -> void:
	var h := hero
	if held < 0 or held >= foes.size() or foes[held].state != State.GRABBED:
		_to(h, State.IDLE)
		held = -1
		return
	var f := foes[held]
	f.pos = h.pos + Vector2(h.facing * 26.0, 0.0)
	if a and h.knees < 2:
		h.knees += 1
		events.append([&"knee"])
		_damage(f, tuning.knee_damage, false, held)
		return
	if (a and h.knees >= 2) or h.state_t >= tuning.grab_seconds:
		h.facing = -h.facing
		f.vx = h.facing * 220.0
		f.vz = 180.0
		_to(f, State.THROWN)
		_damage(f, tuning.throw_damage, false, held)
		events.append([&"throw"])
		held = -1
		_to(h, State.IDLE)


## Удар героя: все враги в досягаемости перед ним на той же глубине.
func _hero_hits(reach: float, dmg: int, heavy: bool) -> void:
	for i in foes.size():
		var f := foes[i]
		if f.state in [State.DOWN, State.GETUP, State.DEAD, State.THROWN] or f.invuln > 0.0:
			continue
		var dx := (f.pos.x - hero.pos.x) * hero.facing
		if dx < 0.0 or dx > reach or absf(f.pos.y - hero.pos.y) > tuning.hit_depth or f.z > 40.0:
			continue
		hits += 1
		# Призрачные удары: каждый такой проходит сквозь.
		if ghost_every > 0 and hits % ghost_every == 0:
			events.append([&"ghost"])
			continue
		_damage(f, dmg, heavy, i)


## Урон бойцу: оглушение или нокдаун; у врага смерть, у героя потеря жизни.
func _damage(f: Fighter, dmg: int, heavy: bool, index: int) -> void:
	if f.kind == BrawlWaves.Kind.BOSS and immortal:
		dmg = 0
	if sneeze and f != hero:
		dmg = f.hp
	f.hp = maxi(f.hp - dmg, 0)
	events.append([&"hit", index, dmg])
	events.append([&"impact", f.pos.x - (f.facing if f != hero else -hero.facing) * 6.0, f.pos.y, f.z, heavy])
	f.flash = tuning.flash
	hitstop = maxf(hitstop, tuning.hitstop_heavy if heavy else tuning.hitstop)
	if f.hp <= 0:
		if f == hero:
			_lose_life()
			return
		_knock(f)
		_to(f, State.DEAD)
		kills += 1
		events.append([&"kill", index])
		return
	if heavy or f.state == State.THROWN:
		_knock(f)
		events.append([&"down", index])
	elif f.state != State.THROWN:
		_to(f, State.HURT)
		f.pos.x += -f.facing * 4.0 if f != hero else 0.0


func _knock(f: Fighter) -> void:
	var away := signf(f.pos.x - hero.pos.x) if f != hero else -hero.facing
	f.vx = away * (tuning.knock_back + launch)
	f.vz = 200.0 + launch
	_to(f, State.DOWN)


func _lose_life() -> void:
	# Два удара в одном шаге не снимают две жизни, после конца ничего не снимают.
	if ended or hero.invuln > 0.0:
		return
	lives = maxi(lives - 1, 0)
	deaths += 1
	events.append([&"life"])
	if lives <= 0:
		_end(false)
		return
	hero.hp = hero.max_hp
	hero.invuln = tuning.respawn_invuln
	_to(hero, State.IDLE)
	# Волна: враги рядом падают.
	for i in foes.size():
		var f := foes[i]
		if f.state != State.DEAD and f.pos.distance_to(hero.pos) < tuning.respawn_blast:
			_knock(f)


## Падение по дуге после нокдауна или броска.
func _fall(f: Fighter) -> void:
	if f.z > 0.0 or f.vz > 0.0:
		f.vz -= tuning.gravity * DT
		f.z = maxf(f.z + f.vz * DT, 0.0)
		f.pos.x += f.vx * DT
		if f.z <= 0.0:
			f.vz = 0.0
			f.vx = 0.0
	_clamp(f)


func _clamp(f: Fighter) -> void:
	f.pos.y = clampf(f.pos.y, 0.0, tuning.depth)
	if f == hero:
		f.pos.x = clampf(f.pos.x, cam_x + 10.0, cam_x + tuning.screen_w - 10.0 if locked else width() - 10.0)


func _to(f: Fighter, s: State) -> void:
	f.state = s
	f.state_t = 0.0


# --- Враги -------------------------------------------------------------------------------------

func _foe_step(i: int) -> void:
	var f := foes[i]
	f.state_t += DT
	f.invuln = maxf(f.invuln - DT, 0.0)
	f.cooldown = maxf(f.cooldown - DT, 0.0)
	match f.state:
		State.DEAD:
			_fall(f)
			if f.state_t >= 0.9:
				f.gone = true
			return
		State.GRABBED:
			return
		State.THROWN:
			_fall(f)
			# Брошенный сбивает тех, в кого влетел.
			for j in foes.size():
				var o := foes[j]
				if j != i and o.state in [State.IDLE, State.WALK, State.WINDUP] and absf(o.pos.x - f.pos.x) < 26.0 and absf(o.pos.y - f.pos.y) < 14.0:
					_damage(o, tuning.throw_hit_damage, true, j)
			if f.z <= 0.0 and f.state_t > 0.1:
				_to(f, State.DOWN)
			return
		State.HURT:
			if f.state_t >= tuning.hurt_seconds:
				_to(f, State.IDLE)
			return
		State.DOWN:
			_fall(f)
			if f.state_t >= tuning.down_seconds:
				_to(f, State.GETUP)
				f.invuln = tuning.getup_seconds
			return
		State.GETUP:
			if f.state_t >= tuning.getup_seconds:
				_to(f, State.IDLE)
			return
		State.WINDUP:
			if f.state_t >= _windup(f):
				_to(f, State.STRIKE)
				_foe_strike(f)
			return
		State.STRIKE:
			if f.state_t >= 0.25:
				_to(f, State.IDLE)
				f.cooldown = tuning.foe_cooldown
			return
		State.CHARGE:
			f.pos.x += f.facing * tuning.boss_charge_speed * DT
			if not hero.state in [State.DOWN, State.GETUP] and hero.invuln <= 0.0 and absf(hero.pos.x - f.pos.x) < 34.0 \
					and absf(hero.pos.y - f.pos.y) < 16.0 and hero.z < 30.0:
				_hero_hurt(tuning.boss_charge_damage, true)
			if f.pos.x < cam_x + 30.0 or f.pos.x > cam_x + tuning.screen_w - 30.0 or f.state_t > 2.0:
				f.pos.x = clampf(f.pos.x, cam_x + 30.0, cam_x + tuning.screen_w - 30.0)
				_to(f, State.IDLE)
				f.charge_t = tuning.boss_charge_every
			return
	if hero.state == State.DOWN and not locked:
		return
	_foe_ai(i)


func _windup(f: Fighter) -> float:
	match f.kind:
		BrawlWaves.Kind.KNIFE:
			return tuning.knife_windup
		BrawlWaves.Kind.BOSS:
			return tuning.boss_windup
	return tuning.thug_windup


func _foe_damage(f: Fighter) -> int:
	match f.kind:
		BrawlWaves.Kind.KNIFE:
			return tuning.knife_damage
		BrawlWaves.Kind.BOSS:
			return tuning.boss_damage
	return tuning.thug_damage


func _foe_speed(f: Fighter) -> float:
	var s := tuning.thug_speed
	match f.kind:
		BrawlWaves.Kind.KNIFE:
			s = tuning.knife_speed
		BrawlWaves.Kind.BOSS:
			s = tuning.boss_speed
	return s * (1.0 + launch / 400.0)


## Разум врага: в атаке не больше `attackers` ближних, остальные ждут поодаль; встать сбоку от
## героя на его глубине и с замахом ударить; боцман раз в несколько секунд бежит рывком.
func _foe_ai(i: int) -> void:
	var f := foes[i]
	var to := hero.pos - f.pos
	f.facing = signf(to.x) if absf(to.x) > 2.0 else f.facing
	if f.kind == BrawlWaves.Kind.BOSS:
		f.charge_t -= DT
		if f.charge_t <= 0.0 and absf(to.y) < 20.0 and absf(to.x) > 90.0:
			_to(f, State.CHARGE)
			events.append([&"charge"])
			return
	var rank := 0
	for j in foes.size():
		if j != i and foes[j].state != State.DEAD and foes[j].pos.distance_to(hero.pos) < f.pos.distance_to(hero.pos):
			rank += 1
	var side := -1.0 if f.pos.x < hero.pos.x else 1.0
	var spot := hero.pos + Vector2(side * tuning.foe_reach * 0.9, 0.0)
	if rank >= tuning.attackers:
		spot = hero.pos + Vector2(side * tuning.wait_distance, (f.pos.y - hero.pos.y) * 0.5 + (18.0 if i % 2 == 0 else -18.0))
	var d := spot - f.pos
	var aligned := absf(to.y) < 8.0 and absf(absf(to.x) - tuning.foe_reach * 0.9) < 9.0
	if rank < tuning.attackers and aligned and f.cooldown <= 0.0 and hero.state != State.DOWN and hero.invuln <= 0.0:
		_to(f, State.WINDUP)
		events.append([&"windup", i])
		return
	if d.length() > 2.0:
		var v := d.normalized() * _foe_speed(f)
		v.y *= 0.7
		f.pos += v * DT
		f.state = State.WALK
	else:
		f.state = State.IDLE
	f.pos.y = clampf(f.pos.y, 0.0, tuning.depth)


func _foe_strike(f: Fighter) -> void:
	events.append([&"swing", foes.find(f), &"foe"])
	var dx := (hero.pos.x - f.pos.x) * f.facing
	if dx < 0.0 or dx > tuning.foe_reach + 10.0 or absf(hero.pos.y - f.pos.y) > tuning.hit_depth or hero.z > 30.0:
		return
	if hero.invuln > 0.0 or hero.state in [State.DOWN, State.GETUP]:
		return
	_hero_hurt(_foe_damage(f), f.kind == BrawlWaves.Kind.BOSS)


func _hero_hurt(dmg: int, heavy: bool) -> void:
	if held >= 0 and held < foes.size():
		_to(foes[held], State.IDLE)
		held = -1
	events.append([&"hurt"])
	events.append([&"impact", hero.pos.x + hero.facing * 6.0, hero.pos.y, hero.z, heavy])
	hero.flash = tuning.flash
	hitstop = maxf(hitstop, tuning.hitstop_heavy if heavy else tuning.hitstop)
	hero.hp = maxi(hero.hp - dmg, 0)
	if hero.hp <= 0:
		_lose_life()
		return
	if heavy:
		_knock(hero)
	else:
		_to(hero, State.HURT)


func _end(win: bool) -> void:
	ended = true
	won = win
	events.append([&"win" if win else &"lose"])


# --- Боты --------------------------------------------------------------------------------------

## Бот: возвращает стрелки, ставит `bot_a`, `bot_b`. WIN идёт к ближнему врагу, встаёт сбоку на
## его глубине и бьёт комбо; от рывка боцмана уходит вглубь; когда экран пуст, идёт вправо. LOSE
## стоит.
func bot(mode: AutoTest.BotMode) -> Vector2:
	bot_a = false
	bot_b = false
	if ended or mode != AutoTest.BotMode.WIN:
		return Vector2.ZERO
	if hero.state == State.GRAB:
		bot_a = int(time * 60.0) % 12 == 0
		return Vector2.ZERO
	var target: Fighter = null
	for f in foes:
		if f.state == State.DEAD:
			continue
		if f.state == State.CHARGE and absf(f.pos.y - hero.pos.y) < 30.0:
			return Vector2(0.0, -1.0 if hero.pos.y > tuning.depth * 0.5 else 1.0)
		if target == null or f.pos.distance_to(hero.pos) < target.pos.distance_to(hero.pos):
			target = f
	if target == null:
		return Vector2(1.0, 0.0) if not locked else Vector2.ZERO
	var side := -1.0 if hero.pos.x < target.pos.x else 1.0
	var spot := target.pos + Vector2(side * tuning.bot_gap, 0.0)
	var d := spot - hero.pos
	var facing_ok := signf(target.pos.x - hero.pos.x) == hero.facing
	var can_hit := absf(d.y) < 7.0 and absf(d.x) < 12.0 and facing_ok and not target.state in [State.DOWN, State.GETUP, State.THROWN]
	if can_hit and hero.state in [State.IDLE, State.WALK]:
		# Двое и больше перед собой или боцман без замаха: тяжёлый удар, иначе комбо.
		var front := 0
		for f in foes:
			if f.state != State.DEAD and (f.pos.x - hero.pos.x) * hero.facing > 0.0 and absf(f.pos.x - hero.pos.x) < tuning.heavy_reach \
					and absf(f.pos.y - hero.pos.y) < tuning.hit_depth:
				front += 1
		if front >= 2 or (target.kind == BrawlWaves.Kind.BOSS and target.state != State.WINDUP and int(time * 2.0) % 3 == 0):
			bot_b = true
		else:
			bot_a = true
		return Vector2.ZERO
	if absf(d.x) < 12.0 and absf(d.y) < 7.0 and not facing_ok:
		return Vector2(-side, 0.0)
	var v := Vector2(clampf(d.x / 14.0, -1.0, 1.0), clampf(d.y / 8.0, -1.0, 1.0))
	return v
