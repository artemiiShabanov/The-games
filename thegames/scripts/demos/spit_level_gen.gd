class_name SpitLevelGen
extends RefCounted
## Генератор тропы платформера × low poly (#112) из сида. Старт, `pieces` кусков (обычный,
## мостик, со скелетами, с рядом ящиков, каток с бочками, обстрел из пушек, россыпь
## камней-ступенек), финиш у маяка. Между кусками яма, широкая вода с плотом или уступ; после
## куска коса может свернуть под прямым углом и через один-два куска вернуться к ходу вперёд,
## так что назад она не идёт и сама себя не пересекает. Дальше по косе всё быстрее и шире.
## Уровень сида это первая попытка, что проходит `validate`: там и число ям, плотов, уступов и
## поворотов, и то, что каждый стык берётся прыжком.

const COIN_UP := 0.9
const ATTEMPTS := 60
const FORWARD := Vector3(0, 0, -1)
const TURNABLE: Array[int] = [SpitLevel.Kind.PLAIN, SpitLevel.Kind.GUARD, SpitLevel.Kind.CRATES, SpitLevel.Kind.FIRE]
## Конец куска перед поворотом пуст на столько метров: туда пристроен следующий.
const CORNER := 6.0


static func generate(seed_: int, t: PlatformerLowpolyGenTuning = null) -> SpitLevel:
	if t == null:
		t = PlatformerLowpolyGenTuning.load_default()
	var lv: SpitLevel = null
	for attempt in ATTEMPTS:
		lv = _build(seed_, attempt, t)
		if validate(lv, t) == "":
			break
	return lv


static func _build(seed_: int, attempt: int, t: PlatformerLowpolyGenTuning) -> SpitLevel:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":spit:", attempt))
	var lv := SpitLevel.new()
	var first := SpitLevel.Piece.new()
	first.kind = SpitLevel.Kind.START
	first.length = t.start_length
	first.width = t.width_max
	lv.pieces.append(first)
	lv.start = Vector3(0.0, 0.0, -1.5)
	# Курс: 0 вперёд, −1 влево, 1 вправо; сколько кусков подряд идём вбок; пристроен ли следующий сбоку.
	var heading := 0
	var side_run := 0
	var turn_into := false
	for k in t.pieces:
		var f := float(k) / maxf(t.pieces - 1, 1.0)
		var prev := lv.pieces[lv.pieces.size() - 1]
		var kind := _pick_kind(rng, t, k, prev.kind)
		if heading != 0 and side_run >= 1 and not TURNABLE.has(kind):
			kind = SpitLevel.Kind.PLAIN
		if kind == SpitLevel.Kind.STONE and not turn_into:
			_add_stones(lv, rng, t)
			if heading != 0:
				side_run += 1
			continue
		if kind == SpitLevel.Kind.STONE:
			kind = SpitLevel.Kind.PLAIN
		var p := SpitLevel.Piece.new()
		p.kind = kind
		match kind:
			SpitLevel.Kind.BRIDGE:
				p.length = rng.randi_range(t.bridge_length_min, t.bridge_length_max)
				p.width = t.bridge_width
			SpitLevel.Kind.GUARD:
				p.length = rng.randi_range(t.guard_length_min, t.guard_length_max)
				p.width = t.width_max
			SpitLevel.Kind.CRATES:
				p.length = rng.randi_range(t.crates_length_min, t.crates_length_max)
				p.width = rng.randi_range(t.width_min, t.width_max)
			SpitLevel.Kind.ROLL:
				p.length = rng.randi_range(t.roll_length_min, t.roll_length_max)
				p.width = t.roll_width
			SpitLevel.Kind.FIRE:
				p.length = rng.randi_range(t.fire_length_min, t.fire_length_max)
				p.width = rng.randi_range(t.width_min, t.width_max)
			_:
				p.length = rng.randi_range(t.plain_length_min, t.plain_length_max)
				p.width = rng.randi_range(t.width_min, t.width_max)
		# Свернёт ли коса после этого куска: вбок идём один-два куска и возвращаемся вперёд.
		var turn_after := false
		if TURNABLE.has(kind) and k < t.pieces - 1:
			turn_after = (side_run >= 1 or rng.randf() < 0.6) if heading != 0 else rng.randf() < t.turn_chance
		if turn_after:
			p.length += CORNER
		if turn_into:
			p.dir = FORWARD if heading == 0 else Vector3(heading, 0, 0)
			p.a = prev.far() - prev.dir * (p.width / 2.0) + p.dir * (prev.width / 2.0)
			p.h0 = prev.h1
		else:
			p.dir = prev.dir
			var shift := 0.0
			var may_gap := kind != SpitLevel.Kind.BRIDGE and prev.kind != SpitLevel.Kind.BRIDGE and k > 0
			if may_gap and rng.randf() < t.gap_chance:
				if f >= t.raft_from and kind != SpitLevel.Kind.ROLL and rng.randf() < t.raft_chance:
					p.gap = 2.0 * t.raft_hop + 2.0 * t.raft_half
					p.raft = lv.rafts.size()
				else:
					p.gap = snappedf(rng.randf_range(t.gap_min, lerpf(t.gap_first, t.gap_last, f)), 0.1)
			if p.raft < 0:
				var room := (prev.width + p.width) / 2.0 - (t.overlap_min if p.gap > 0.0 else 1.5)
				var limit := minf(t.drift, maxf(room, 0.0))
				shift = snappedf(rng.randf_range(-limit, limit), 0.5)
				# Края куска на целых метрах сетки земли.
				if int(roundf(shift * 2.0) + prev.width + p.width) % 2 != 0:
					shift += 0.5 if shift < 0.0 else -0.5
			p.a = prev.far() + prev.dir * p.gap + prev.right() * shift
			if p.raft >= 0:
				p.h0 = prev.h1
			elif p.gap > 3.0:
				p.h0 = prev.h1 - rng.randf_range(0.0, t.gap_step)
			elif p.gap > 0.0:
				p.h0 = prev.h1 + rng.randf_range(-t.gap_step, t.gap_step)
			elif kind != SpitLevel.Kind.BRIDGE and prev.kind != SpitLevel.Kind.BRIDGE and prev.kind != SpitLevel.Kind.STONE \
					and rng.randf() < t.step_chance:
				var up := rng.randf() < (0.3 if prev.h1 > 2.0 else 0.6)
				p.h0 = prev.h1 + rng.randf_range(t.step_min, t.step_max) * (1.0 if up else -1.0)
			else:
				p.h0 = prev.h1
		p.h0 = clampf(p.h0, t.height_min, t.height_max)
		if kind == SpitLevel.Kind.BRIDGE or turn_after:
			p.h1 = p.h0
		elif kind == SpitLevel.Kind.ROLL:
			# Каток идёт в горку: бочки катятся под уклон навстречу.
			p.h1 = clampf(p.h0 + rng.randf_range(0.4, t.slope), t.height_min, t.height_max)
		else:
			p.h1 = clampf(p.h0 + rng.randf_range(-t.slope, t.slope), t.height_min, t.height_max)
		p.along = prev.along + prev.length + p.gap
		lv.pieces.append(p)
		var index := lv.pieces.size() - 1
		if p.raft >= 0:
			var raft := SpitLevel.Raft.new()
			raft.piece = index
			raft.s = -p.gap / 2.0
			raft.half = t.raft_half
			raft.reach = t.raft_reach
			raft.speed = lerpf(t.raft_speed_first, t.raft_speed_last, f) * rng.randf_range(0.9, 1.1)
			raft.phase = rng.randf()
			raft.y = p.h0
			lv.rafts.append(raft)
		_fill(lv, index, rng, t, f, p.length - (CORNER if turn_after else 0.0))
		if heading != 0:
			side_run += 1
		if turn_after:
			if heading == 0:
				heading = (-1 if p.a.x > 5.0 else (1 if p.a.x < -5.0 else (1 if rng.randf() < 0.5 else -1)))
				side_run = 0
			else:
				heading = 0
				side_run = 0
		turn_into = turn_after
	var before := lv.pieces[lv.pieces.size() - 1]
	var last := SpitLevel.Piece.new()
	last.kind = SpitLevel.Kind.END
	last.length = t.end_length
	last.width = t.end_width
	if turn_into:
		last.dir = FORWARD if heading == 0 else Vector3(heading, 0, 0)
		last.a = before.far() - before.dir * (last.width / 2.0) + last.dir * (before.width / 2.0)
	else:
		last.dir = before.dir
		last.a = before.far() + before.right() * (0.5 if int(before.width + last.width) % 2 != 0 else 0.0)
	last.h0 = before.h1
	last.h1 = before.h1
	last.along = before.along + before.length
	lv.pieces.append(last)
	lv.total = last.along + last.length
	return lv


static func _pick_kind(rng: RandomNumberGenerator, t: PlatformerLowpolyGenTuning, k: int, prev: SpitLevel.Kind) -> SpitLevel.Kind:
	if k == 0:
		return SpitLevel.Kind.PLAIN
	var shares := {SpitLevel.Kind.PLAIN: t.share_plain, SpitLevel.Kind.BRIDGE: t.share_bridge, SpitLevel.Kind.GUARD: t.share_guard,
			SpitLevel.Kind.CRATES: t.share_crates, SpitLevel.Kind.ROLL: t.share_roll, SpitLevel.Kind.FIRE: t.share_fire,
			SpitLevel.Kind.STONE: t.share_stone}
	var sum := 0.0
	for kind: int in shares:
		sum += float(shares[kind])
	for attempt in 8:
		var r := rng.randf() * sum
		var picked := SpitLevel.Kind.PLAIN
		for kind: int in shares:
			r -= float(shares[kind])
			if r <= 0.0:
				picked = kind as SpitLevel.Kind
				break
		# Два одинаковых подряд не бывает.
		if picked != prev:
			return picked
	return SpitLevel.Kind.PLAIN


## Россыпь камней-ступенек: несколько маленьких кусков с ямами между ними.
static func _add_stones(lv: SpitLevel, rng: RandomNumberGenerator, t: PlatformerLowpolyGenTuning) -> void:
	var count := rng.randi_range(t.stone_count_min, t.stone_count_max)
	for j in count:
		var prev := lv.pieces[lv.pieces.size() - 1]
		var p := SpitLevel.Piece.new()
		p.kind = SpitLevel.Kind.STONE
		p.length = t.stone_size
		p.width = t.stone_size
		p.dir = prev.dir
		p.gap = snappedf(rng.randf_range(t.stone_gap_min, t.stone_gap_max), 0.1)
		var shift := snappedf(rng.randf_range(-t.stone_jitter, t.stone_jitter), 0.5) if j > 0 else 0.0
		if int(roundf(shift * 2.0) + prev.width + p.width) % 2 != 0:
			shift += 0.5 if shift <= 0.0 else -0.5
		p.a = prev.far() + prev.dir * p.gap + prev.right() * shift
		p.h0 = clampf(prev.h1 + rng.randf_range(-0.3, 0.3), t.height_min, t.height_max)
		p.h1 = p.h0
		p.along = prev.along + prev.length + p.gap
		lv.pieces.append(p)
		if j == count / 2:
			lv.coins.append(p.world(p.length / 2.0, 0.0) + Vector3(0.0, COIN_UP, 0.0))


## Что стоит на куске в пределах первых `usable` метров; дублоны дугой над ямой перед ним.
static func _fill(lv: SpitLevel, index: int, rng: RandomNumberGenerator, t: PlatformerLowpolyGenTuning, f: float, usable: float) -> void:
	var p := lv.pieces[index]
	var prev := lv.pieces[index - 1]
	var up := Vector3(0.0, COIN_UP, 0.0)
	if p.gap > 0.0 and p.raft < 0:
		for j in t.coins_gap:
			var k := (j + 1.0) / (t.coins_gap + 1.0)
			var at := p.world(-p.gap * (1.0 - k), 0.0)
			lv.coins.append(Vector3(at.x, maxf(prev.h1, p.h0) + COIN_UP + 0.7 * sin(PI * k), at.z))
	match p.kind:
		SpitLevel.Kind.PLAIN:
			var lane := rng.randf_range(-1.0, 1.0) * (p.width / 2.0 - 1.0)
			for j in t.coins_plain:
				var s := 2.5 + j * 1.6
				if s < usable - 1.0:
					lv.coins.append(p.world(s, lane) + up)
		SpitLevel.Kind.BRIDGE:
			for j in 2:
				lv.coins.append(p.world(usable * (j + 1.0) / 3.0, 0.0) + up)
		SpitLevel.Kind.GUARD:
			var pair := f >= t.guard_pair_from
			var phase := rng.randf()
			for j in (2 if pair else 1):
				var g := SpitLevel.Guard.new()
				g.piece = index
				g.s = usable / 2.0 + ((j - 0.5) * 3.2 if pair else 0.0)
				g.reach = p.width / 2.0 - 0.5
				g.speed = lerpf(t.guard_speed_first, t.guard_speed_last, f) * rng.randf_range(0.9, 1.1)
				g.phase = fposmod(phase + 0.5 * j, 1.0)
				lv.guards.append(g)
			lv.coins.append(p.world(usable - 2.0, 0.0) + up)
		SpitLevel.Kind.CRATES:
			# Ряд ящиков поперёк всей тропы: не обойти, только прыгать.
			var s := roundf(usable * 0.45)
			for j in int(p.width):
				lv.crates.append(p.world(s, -p.width / 2.0 + 0.5 + j))
		SpitLevel.Kind.ROLL:
			var r := SpitLevel.Roller.new()
			r.piece = index
			r.speed = lerpf(t.roll_speed_first, t.roll_speed_last, f)
			r.period = lerpf(t.roll_period_first, t.roll_period_last, f)
			r.offset = rng.randf_range(0.0, r.period)
			var options: Array[float] = [-1.2, 0.0, 1.2]
			var before := -1
			for j in 7:
				var pick := rng.randi_range(0, options.size() - 1)
				if pick == before:
					pick = (pick + 1) % options.size()
				before = pick
				r.lanes.append(options[pick])
			lv.rollers.append(r)
			for j in 2:
				lv.coins.append(p.world(usable * (j + 1.0) / 3.0, 0.0) + up)
		SpitLevel.Kind.FIRE:
			var count := roundi(lerpf(t.fire_cannons_first, t.fire_cannons_last, f))
			var period := lerpf(t.fire_period_first, t.fire_period_last, f)
			var side := 1.0 if rng.randf() < 0.5 else -1.0
			for j in count:
				var c := SpitLevel.Cannon.new()
				c.piece = index
				c.s = 3.0 + j * (usable - 6.0) / maxf(count - 1, 1.0)
				c.side = side
				c.speed = t.fire_speed
				c.period = period
				c.offset = rng.randf_range(0.0, period)
				lv.cannons.append(c)
				side = -side
			lv.coins.append(p.world(usable / 2.0, 0.0) + up)


## Прямоугольник куска на земле: углы по x и z.
static func _rect(p: SpitLevel.Piece) -> Rect2:
	var a := p.world(0.0, -p.width / 2.0)
	var b := p.world(p.length, p.width / 2.0)
	return Rect2(Vector2(minf(a.x, b.x), minf(a.z, b.z)), Vector2(absf(a.x - b.x), absf(a.z - b.z)))


## Пусто, если уровень проходим по построению; иначе что не так.
static func validate(lv: SpitLevel, t: PlatformerLowpolyGenTuning = null) -> String:
	if t == null:
		t = PlatformerLowpolyGenTuning.load_default()
	if lv.gaps() < t.gaps_min:
		return "ям %d, меньше %d" % [lv.gaps(), t.gaps_min]
	if lv.rafts.size() < t.rafts_min:
		return "плотов %d" % lv.rafts.size()
	if lv.turns() < t.turns_min:
		return "поворотов %d" % lv.turns()
	if lv.steps() < t.steps_min:
		return "уступов %d" % lv.steps()
	if lv.guards.is_empty() or lv.rollers.is_empty() or lv.cannons.is_empty():
		return "нет скелетов, катка или пушек"
	var raft_gap := 2.0 * t.raft_hop + 2.0 * t.raft_half
	for i in range(1, lv.pieces.size()):
		var p := lv.pieces[i]
		var prev := lv.pieces[i - 1]
		var turned := not p.dir.is_equal_approx(prev.dir)
		if p.raft >= 0:
			if absf(p.gap - raft_gap) > 0.01 or absf(p.h0 - prev.h1) > 0.01 or turned:
				return "кусок %d: плот над ямой %.2f" % [i, p.gap]
		elif p.gap < 0.0 or p.gap > t.gap_last + 0.01 or (p.gap > 0.0 and p.gap < minf(t.gap_min, t.stone_gap_min) - 0.01):
			return "кусок %d: яма %.2f" % [i, p.gap]
		if p.gap > 0.0 and (turned or p.kind == SpitLevel.Kind.BRIDGE or prev.kind == SpitLevel.Kind.BRIDGE):
			return "кусок %d: яма на повороте или у мостика" % i
		if p.gap > 0.0 and p.h0 - prev.h1 > t.gap_step + 0.01:
			return "кусок %d: яма с подъёмом %.2f" % [i, p.h0 - prev.h1]
		if p.gap <= 0.0 and absf(p.h0 - prev.h1) > t.step_max + 0.01:
			return "кусок %d: уступ %.2f" % [i, p.h0 - prev.h1]
		if p.gap <= 0.0 and absf(p.h0 - prev.h1) > 0.01 and (prev.kind == SpitLevel.Kind.STONE or prev.kind == SpitLevel.Kind.BRIDGE):
			return "кусок %d: уступ сразу за камнем или мостиком" % i
		if not turned:
			var shift := absf(prev.local(p.a).y)
			var overlap := (prev.width + p.width) / 2.0 - shift
			if overlap < (t.overlap_min if p.gap > 0.0 and p.kind != SpitLevel.Kind.STONE else 1.5) - 0.01:
				return "кусок %d: перекрытие по ширине %.2f" % [i, overlap]
		elif absf(prev.h1 - prev.h0) > 0.01 or prev.length < p.width + 3.0:
			return "кусок %d: поворот с наклонного или короткого куска" % i
		if p.h0 < t.height_min - 0.01 or p.h1 > t.height_max + 0.01:
			return "кусок %d: высота" % i
		# Коса не пересекает сама себя: кусок не задевает никакой раньше предыдущего.
		var mine := _rect(p).grow(0.5)
		for j in i - 1:
			if mine.intersects(_rect(lv.pieces[j])):
				return "кусок %d задевает кусок %d" % [i, j]
	for g in lv.guards:
		var p := lv.pieces[g.piece]
		if g.reach > p.width / 2.0 - 0.3 or g.s < 3.5 or g.s > p.length - 3.5 or g.speed <= 0.0:
			return "скелет на куске %d стоит не там" % g.piece
	for c in lv.cannons:
		if c.s < 2.5 or c.s > lv.pieces[c.piece].length - 2.5:
			return "пушка у края куска %d" % c.piece
	for c in lv.crates:
		var i := lv.piece_at(c + Vector3(0.0, 0.01, 0.0))
		if i < 0:
			return "ящик над водой"
		var s := lv.pieces[i].local(c).x
		if s < 3.5 or s > lv.pieces[i].length - 4.5:
			return "ящик у края куска %d" % i
	if lv.coins.is_empty():
		return "нет дублонов"
	return ""
