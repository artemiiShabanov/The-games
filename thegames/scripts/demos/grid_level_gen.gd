class_name GridLevelGen
extends RefCounted
## Генератор уровня «по клеткам» из сида (#98): детерминирован. Уровень это ловушки одна за
## другой, между ними отдых в две-три клетки пола; первая клетка отдыха это место, откуда герой
## продолжит после потери жизни. Ловушки: яма в клетку, шипы, двое шипов через клетку, якорь,
## плиты над водой подряд, участок со стражником, яма и за ней шипы. Одна и та же ловушка не
## идёт два раза подряд; к концу уровня ритм чаще. `validate` проверяет раскладку.

enum Trap { PIT, SPIKES, SPIKES_PAIR, ANCHOR, PLATES, GUARD, PIT_SPIKES }


static func generate(seed_: int, t: PlatformerBit16GenTuning = null) -> GridLevel:
	if t == null:
		t = PlatformerBit16GenTuning.load_default()
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":grid"))
	var lv := GridLevel.new()
	lv.width = t.width
	lv.cells.resize(t.width)
	lv.cells.fill(GridLevel.Cell.FLOOR)
	lv.period.resize(t.width)
	lv.period.fill(0.0)
	lv.phase.resize(t.width)
	lv.phase.fill(0.0)
	lv.start = 1
	lv.checkpoints.append(1)
	lv.flag = t.width - 3
	var weights: Array[float] = [t.weight_pit, t.weight_spikes, t.weight_spikes_pair, t.weight_anchor, t.weight_plates,
			t.weight_guard, t.weight_pit_spikes]
	var x := t.start_flat
	var last := -1
	var pits := 0
	while true:
		# Первые ловушки это ямы, пока не набралось положенное число: без ямы бот LOSE не проиграет.
		var trap := Trap.PIT if pits < t.pits_min and last != Trap.PIT else _pick(rng, weights, last)
		var k := float(x) / maxf(t.width - 1, 1.0)
		var length := _length(rng, t, trap)
		if x + length + t.rest_min > t.width - t.end_flat:
			break
		match trap:
			Trap.PIT:
				lv.cells[x] = GridLevel.Cell.PIT
				pits += 1
				_coin(lv, rng, x, t.coin_trap_chance)
			Trap.SPIKES:
				_rhythm(lv, x, GridLevel.Cell.SPIKES, lerpf(t.spike_period_first, t.spike_period_last, k), rng.randf())
				_coin(lv, rng, x, t.coin_trap_chance)
			Trap.SPIKES_PAIR:
				var p := lerpf(t.spike_period_first, t.spike_period_last, k)
				var ph := rng.randf()
				_rhythm(lv, x, GridLevel.Cell.SPIKES, p, ph)
				_rhythm(lv, x + 2, GridLevel.Cell.SPIKES, p, ph + 0.5)
			Trap.ANCHOR:
				_rhythm(lv, x, GridLevel.Cell.ANCHOR, lerpf(t.anchor_period_first, t.anchor_period_last, k), rng.randf())
			Trap.PLATES:
				for i in length:
					lv.cells[x + i] = GridLevel.Cell.PLATE
				_coin(lv, rng, x + length / 2, t.coin_trap_chance)
			Trap.GUARD:
				var g := GridLevel.Guard.new()
				g.from = x
				g.to = x + length - 1
				g.start = rng.randi_range(g.from + 1, g.to)
				g.dir = -1 if rng.randf() < 0.5 else 1
				g.step = lerpf(t.guard_step_first, t.guard_step_last, k)
				lv.guards.append(g)
			Trap.PIT_SPIKES:
				lv.cells[x] = GridLevel.Cell.PIT
				pits += 1
				_rhythm(lv, x + 2, GridLevel.Cell.SPIKES, lerpf(t.spike_period_first, t.spike_period_last, k), rng.randf())
		last = trap
		x += length
		lv.checkpoints.append(x)
		var rest := rng.randi_range(t.rest_min, t.rest_max)
		for i in rest:
			_coin(lv, rng, x + i, t.coin_rest_chance)
		x += rest
	return lv


static func _pick(rng: RandomNumberGenerator, weights: Array[float], last: int) -> Trap:
	var total := 0.0
	for i in weights.size():
		if i != last:
			total += weights[i]
	var r := rng.randf() * total
	for i in weights.size():
		if i == last:
			continue
		r -= weights[i]
		if r <= 0.0:
			return i as Trap
	return Trap.SPIKES if last != Trap.SPIKES else Trap.PIT


static func _length(rng: RandomNumberGenerator, t: PlatformerBit16GenTuning, trap: Trap) -> int:
	match trap:
		Trap.SPIKES_PAIR, Trap.PIT_SPIKES:
			return 3
		Trap.PLATES:
			return rng.randi_range(t.plates_min, t.plates_max)
		Trap.GUARD:
			return rng.randi_range(t.guard_min, t.guard_max)
	return 1


static func _rhythm(lv: GridLevel, x: int, kind: GridLevel.Cell, period: float, phase: float) -> void:
	lv.cells[x] = kind
	lv.period[x] = period
	lv.phase[x] = fposmod(phase, 1.0)


static func _coin(lv: GridLevel, rng: RandomNumberGenerator, x: int, chance: float) -> void:
	if rng.randf() < chance and not lv.coins.has(x):
		lv.coins.append(x)


## Проверка раскладки: "" или причина.
static func validate(lv: GridLevel, t: PlatformerBit16GenTuning) -> String:
	if lv.width != t.width or lv.cells.size() != lv.width:
		return "ширина %d" % lv.width
	for x in lv.width:
		var c := lv.cell(x)
		if (x < t.start_flat or x >= lv.width - t.end_flat) and c != GridLevel.Cell.FLOOR:
			return "ловушка на ровном краю, клетка %d" % x
		if c == GridLevel.Cell.PIT:
			# Яму перепрыгивают: с обеих сторон пол, и приземление не в ловушку.
			if lv.cell(x - 1) != GridLevel.Cell.FLOOR or lv.cell(x + 1) != GridLevel.Cell.FLOOR:
				return "яма %d без пола по краям" % x
		if c == GridLevel.Cell.SPIKES or c == GridLevel.Cell.ANCHOR:
			if lv.period[x] < 1.0:
				return "ловушка %d с периодом %.2f" % [x, lv.period[x]]
			if lv.cell(x - 1) != GridLevel.Cell.FLOOR or lv.cell(x + 1) != GridLevel.Cell.FLOOR:
				return "ловушка %d без пола по краям" % x
	if lv.counts()[GridLevel.Cell.PIT] < t.pits_min:
		return "ям %d" % lv.counts()[GridLevel.Cell.PIT]
	if lv.flag < lv.width - t.end_flat or lv.flag >= lv.width:
		return "флаг в клетке %d" % lv.flag
	var prev := -1
	for cp in lv.checkpoints:
		if cp <= prev or lv.cell(cp) != GridLevel.Cell.FLOOR:
			return "место возврата %d не на полу или не по порядку" % cp
		for g in lv.guards:
			if cp >= g.from and cp <= g.to:
				return "место возврата %d на пути стражника" % cp
		prev = cp
	for g in lv.guards:
		if g.to - g.from + 1 < t.guard_min or g.start < g.from or g.start > g.to:
			return "стражник на участке %d..%d" % [g.from, g.to]
		for x in range(g.from, g.to + 1):
			if lv.cell(x) != GridLevel.Cell.FLOOR:
				return "стражник ходит по ловушке, клетка %d" % x
	for c in lv.coins:
		if c < 0 or c >= lv.width:
			return "монета вне уровня"
	return ""
