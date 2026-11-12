class_name SpitLevelGen
extends RefCounted
## Генератор тропы платформера × low poly (#112) из сида. Старт, `pieces` кусков четырёх видов
## (обычный, мостик, со скелетом, с рядом ящиков), финиш у маяка. Перед куском бывает яма:
## дальше по тропе ямы шире. У мостика ям по краям нет: на узкий настил после прыжка не попасть.
## Середина куска уходит вбок от предыдущего, но так, чтобы тропа не рвалась. `validate` это же
## и проверяет: бот и игрок могут пройти любой уровень.

const CRATE := 0.85
const COIN_UP := 0.9
const ATTEMPTS := 40


## Уровень сида: первая из попыток, что проходит `validate` (попытка входит в зерно, так что
## уровень сида всегда один и тот же).
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
	for k in t.pieces:
		var f := float(k) / maxf(t.pieces - 1, 1.0)
		var prev := lv.pieces[lv.pieces.size() - 1]
		var p := SpitLevel.Piece.new()
		p.kind = _pick_kind(rng, t, k, prev.kind)
		match p.kind:
			SpitLevel.Kind.BRIDGE:
				p.length = rng.randi_range(t.bridge_length_min, t.bridge_length_max)
				p.width = t.bridge_width
			SpitLevel.Kind.GUARD:
				p.length = rng.randi_range(t.guard_length_min, t.guard_length_max)
				p.width = t.width_max
			SpitLevel.Kind.CRATES:
				p.length = rng.randi_range(t.crates_length_min, t.crates_length_max)
				p.width = rng.randi_range(t.width_min, t.width_max)
			_:
				p.length = rng.randi_range(t.plain_length_min, t.plain_length_max)
				p.width = rng.randi_range(t.width_min, t.width_max)
		# Яма: не у мостика; обязательно, если иначе не набрать нужного числа ям.
		var may_gap := p.kind != SpitLevel.Kind.BRIDGE and prev.kind != SpitLevel.Kind.BRIDGE and k > 0
		if may_gap and rng.randf() < t.gap_chance:
			p.gap = snappedf(rng.randf_range(t.gap_min, lerpf(t.gap_first, t.gap_last, f)), 0.1)
		# Вбок: куски перекрываются по ширине, через яму с запасом на приземление.
		var room := (prev.width + p.width) / 2.0 - (t.overlap_min if p.gap > 0.0 else 1.5)
		var shift := minf(t.drift, maxf(room, 0.0))
		p.x = snappedf(clampf(prev.x + rng.randf_range(-shift, shift), -6.0, 6.0), 0.5)
		if absf(p.x - prev.x) > shift:
			p.x = prev.x + signf(p.x - prev.x) * floorf(shift * 2.0) / 2.0
		# Середина целая или с половиной так, чтобы края куска стояли на целых метрах сетки земли.
		if int(roundf(p.x * 2.0) + p.width) % 2 != 0:
			p.x += 0.5 if p.x <= prev.x else -0.5
		p.z0 = prev.z1() - p.gap
		p.h0 = clampf(prev.h1 + (rng.randf_range(-t.gap_step, t.gap_step) if p.gap > 0.0 else 0.0), -1.0, 2.5)
		p.h1 = p.h0 if p.kind == SpitLevel.Kind.BRIDGE else clampf(p.h0 + rng.randf_range(-t.slope, t.slope), -1.0, 2.5)
		lv.pieces.append(p)
		_fill(lv, lv.pieces.size() - 1, rng, t, f)
	var last_prev := lv.pieces[lv.pieces.size() - 1]
	var last := SpitLevel.Piece.new()
	last.kind = SpitLevel.Kind.END
	last.length = t.end_length
	last.width = t.end_width
	last.x = last_prev.x + (0.5 if (t.end_width + last_prev.width) % 2 != 0 else 0.0)
	last.z0 = last_prev.z1()
	last.h0 = last_prev.h1
	last.h1 = last_prev.h1
	lv.pieces.append(last)
	return lv


static func _pick_kind(rng: RandomNumberGenerator, t: PlatformerLowpolyGenTuning, k: int, prev: SpitLevel.Kind) -> SpitLevel.Kind:
	if k == 0:
		return SpitLevel.Kind.PLAIN
	for attempt in 8:
		var r := rng.randf() * (t.share_plain + t.share_bridge + t.share_guard + t.share_crates)
		var kind := SpitLevel.Kind.CRATES
		if r < t.share_plain:
			kind = SpitLevel.Kind.PLAIN
		elif r < t.share_plain + t.share_bridge:
			kind = SpitLevel.Kind.BRIDGE
		elif r < t.share_plain + t.share_bridge + t.share_guard:
			kind = SpitLevel.Kind.GUARD
		# Два одинаковых подряд только обычные.
		if kind != prev or kind == SpitLevel.Kind.PLAIN:
			return kind
	return SpitLevel.Kind.PLAIN


## Что стоит на куске: дублоны, скелет, ящики; дублоны дугой над ямой перед ним.
static func _fill(lv: SpitLevel, index: int, rng: RandomNumberGenerator, t: PlatformerLowpolyGenTuning, f: float) -> void:
	var p := lv.pieces[index]
	var prev := lv.pieces[index - 1]
	if p.gap > 0.0:
		var lo := maxf(prev.left(), p.left()) + 1.0
		var hi := minf(prev.right(), p.right()) - 1.0
		var lane := (lo + hi) / 2.0
		for j in t.coins_gap:
			var k := (j + 1.0) / (t.coins_gap + 1.0)
			lv.coins.append(Vector3(lane, maxf(prev.h1, p.h0) + COIN_UP + 0.7 * sin(PI * k), prev.z1() - p.gap * k))
	match p.kind:
		SpitLevel.Kind.PLAIN:
			var lane := p.x + rng.randf_range(-1.0, 1.0) * (p.width / 2.0 - 1.0)
			for j in t.coins_plain:
				var z := p.z0 - 2.5 - j * 1.6
				if z > p.z1() + 1.0:
					lv.coins.append(Vector3(lane, p.height(z) + COIN_UP, z))
		SpitLevel.Kind.BRIDGE:
			for j in 2:
				var z := p.z0 - p.length * (j + 1.0) / 3.0
				lv.coins.append(Vector3(p.x, p.height(z) + COIN_UP, z))
		SpitLevel.Kind.GUARD:
			var g := SpitLevel.Guard.new()
			g.piece = index
			g.z = p.z0 - p.length / 2.0
			g.reach = p.width / 2.0 - 0.5
			g.speed = lerpf(t.guard_speed_first, t.guard_speed_last, f) * rng.randf_range(0.9, 1.1)
			g.phase = rng.randf()
			lv.guards.append(g)
			var z := p.z1() + 2.0
			lv.coins.append(Vector3(p.x, p.height(z) + COIN_UP, z))
		SpitLevel.Kind.CRATES:
			# Ряд ящиков поперёк всей тропы: не обойти, только прыгать.
			var z := p.z0 - roundf(p.length * 0.45)
			for j in p.width:
				lv.crates.append(Vector3(p.left() + 0.5 + j, p.height(z), z))


## Пусто, если уровень проходим по построению; иначе что не так.
static func validate(lv: SpitLevel, t: PlatformerLowpolyGenTuning = null) -> String:
	if t == null:
		t = PlatformerLowpolyGenTuning.load_default()
	if lv.pieces.size() != t.pieces + 2:
		return "кусков %d" % lv.pieces.size()
	if lv.gaps() < t.gaps_min:
		return "ям %d, меньше %d" % [lv.gaps(), t.gaps_min]
	for i in range(1, lv.pieces.size()):
		var p := lv.pieces[i]
		var prev := lv.pieces[i - 1]
		if p.gap < 0.0 or p.gap > t.gap_last + 0.01 or (p.gap > 0.0 and p.gap < t.gap_min - 0.01):
			return "кусок %d: яма %.2f" % [i, p.gap]
		if p.gap > 0.0 and (p.kind == SpitLevel.Kind.BRIDGE or prev.kind == SpitLevel.Kind.BRIDGE):
			return "кусок %d: яма у мостика" % i
		if absf(p.z0 - (prev.z1() - p.gap)) > 0.001:
			return "кусок %d: не стыкуется по длине" % i
		var overlap := minf(prev.right(), p.right()) - maxf(prev.left(), p.left())
		if overlap < (t.overlap_min if p.gap > 0.0 else 1.5) - 0.01:
			return "кусок %d: перекрытие по ширине %.2f" % [i, overlap]
		if absf(p.h0 - prev.h1) > (t.gap_step if p.gap > 0.0 else 0.0) + 0.01 or absf(p.h1 - p.h0) > t.slope + 0.01:
			return "кусок %d: перепад высоты" % i
		if absf(fposmod(p.left(), 1.0)) > 0.001 and absf(fposmod(p.left(), 1.0) - 1.0) > 0.001:
			return "кусок %d: край не на метре, %.2f" % [i, p.left()]
	for g in lv.guards:
		var p := lv.pieces[g.piece]
		if g.reach > p.width / 2.0 - 0.3 or g.z > p.z0 - 4.0 or g.z < p.z1() + 4.0 or g.speed <= 0.0:
			return "скелет на куске %d стоит не там" % g.piece
	for c in lv.crates:
		if lv.ground_at(c.x, c.z) == -INF:
			return "ящик над водой, z %.1f" % c.z
		var i := lv.piece_at(c.z)
		if c.z > lv.pieces[i].z0 - 3.5 or c.z < lv.pieces[i].z1() + 4.5:
			return "ящик у края куска %d" % i
	if lv.coins.is_empty():
		return "нет дублонов"
	return ""
