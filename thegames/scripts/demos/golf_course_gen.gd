class_name GolfCourseGen
extends RefCounted
## Генератор поля гольфа × 8-bit (#52) из сида: детерминирован. Две-три лунки; в каждой слева
## ти (помост из палубы), песчаный остров с холмами по косинусной кривой через опорные точки,
## иногда пролив с морем поперёк фарвея, грин на палубе корабля (приподнята над песком) с люком
## и флагом, за грином корма стеной. Ветер, пар (по расстоянию от ти до лунки) и пропы на песке
## тоже из сида. `validate()` проверяет размеры, ровные ти и палубу, люк на палубе с отступом,
## крутизну песка вне кромок, пролив по ширине и отступам, пар и ветер в пределах. Не прошла:
## повтор с производным сидом, после `MAX_ATTEMPTS` поле без пролива и холмов.

const MAX_ATTEMPTS := 16


static func generate(seed_: int, tuning: GolfGenTuning = null) -> GolfCourse:
	if tuning == null:
		tuning = GolfGenTuning.load_default()
	for attempt in MAX_ATTEMPTS:
		var rng := RandomNumberGenerator.new()
		rng.seed = hash(str(seed_, ":golf:", attempt))
		var c := _build(rng, tuning, false)
		if validate(c, tuning) == "":
			c.attempts = attempt + 1
			return c
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":golf:fallback"))
	var c := _build(rng, tuning, true)
	c.attempts = MAX_ATTEMPTS + 1
	c.fallback = true
	var why := validate(c, tuning)
	if why != "":
		push_warning("GolfCourseGen: запасное поле сида %d не прошло проверку: %s" % [seed_, why])
	return c


static func _build(rng: RandomNumberGenerator, t: GolfGenTuning, plain: bool) -> GolfCourse:
	var c := GolfCourse.new()
	c.sea_y = t.sea_y
	var n := rng.randi_range(t.holes_min, t.holes_max)
	for i in n:
		c.holes.append(_hole(rng, t, plain))
	return c


static func _snap(v: int, step: int) -> int:
	return int(round(float(v) / step)) * step


static func _hole(rng: RandomNumberGenerator, t: GolfGenTuning, plain: bool) -> GolfCourse.Hole:
	var h := GolfCourse.Hole.new()
	var st := t.step
	h.step = st
	h.length = _snap(rng.randi_range(t.length_min, t.length_max), st)
	var points := h.length / st + 1
	h.heights.resize(points)
	h.kinds.resize(points - 1)
	var tee_from := _snap(t.tee_from, st)
	var tee_to := tee_from + _snap(t.tee_width, st)
	var green_to := h.length - _snap(t.stern_width, st)
	var green_from := green_to - _snap(rng.randi_range(t.green_min, t.green_max), st)
	h.tee_x = (tee_from + tee_to) / 2.0
	h.green_from = green_from
	h.green_to = green_to
	var tee_y := roundf(rng.randf_range(t.ground_top + 16.0, t.ground_bottom - 8.0))
	var lift := roundf(rng.randf_range(t.deck_lift_min, t.deck_lift_max))
	var deck_y := roundf(rng.randf_range(t.ground_top + 8.0, t.ground_bottom - 8.0))
	# Пролив выбирается до холмов: берега у него выше моря.
	var wf := -1
	var w := 0
	var room := green_from - tee_to - 2 * t.water_gap
	if not plain and room >= t.water_min and rng.randf() < t.water_chance:
		w = _snap(rng.randi_range(t.water_min, mini(t.water_max, room)), st)
		wf = _snap(rng.randi_range(tee_to + t.water_gap, green_from - t.water_gap - w), st)
	# Фарвей: опорные точки от края ти до края грина, между ними косинус; у пролива опорные
	# точки на самих берегах, не ниже `sea_y - bank_above`, холмы рядом убраны.
	var xs: Array[float] = [float(tee_to)]
	var ys: Array[float] = [tee_y + 4.0]
	var hills := 1 if plain else rng.randi_range(t.hills_min, t.hills_max)
	for k in range(1, hills):
		var x := lerpf(tee_to, green_from, float(k) / hills) + rng.randf_range(-0.15, 0.15) * (green_from - tee_to) / hills
		var y := rng.randf_range(t.ground_top, t.ground_bottom)
		if wf >= 0 and x > wf - t.water_gap / 2.0 and x < wf + w + t.water_gap / 2.0:
			continue
		xs.append(x)
		ys.append(y)
	if wf >= 0:
		var bank_low := t.sea_y - t.bank_above
		var at := 0
		while at < xs.size() and xs[at] < wf:
			at += 1
		xs.insert(at, float(wf + w))
		ys.insert(at, rng.randf_range(t.ground_top, bank_low))
		xs.insert(at, float(wf))
		ys.insert(at, rng.randf_range(t.ground_top, bank_low))
	xs.append(float(green_from))
	ys.append(minf(deck_y + lift, t.ground_bottom))
	for i in points:
		var x := float(i * st)
		var y := 0.0
		if x < tee_from:
			# Дюна слева от ти: песок поднимается к краю.
			y = tee_y - 4.0 * (tee_from - x) / st
		elif x <= tee_to:
			y = tee_y
		elif x < green_from:
			var k := 0
			while k < xs.size() - 2 and x > xs[k + 1]:
				k += 1
			var f := clampf((x - xs[k]) / (xs[k + 1] - xs[k]), 0.0, 1.0)
			y = lerpf(ys[k], ys[k + 1], (1.0 - cos(f * PI)) / 2.0)
		elif x <= green_to:
			y = deck_y
		else:
			# Корма: стена вверх на два шага, дальше ровно.
			y = deck_y - t.stern_height * minf((x - green_to) / (2.0 * st), 1.0)
		h.heights[i] = roundf(y)
	for i in points - 1:
		var x0 := i * st
		var kind := GolfCourse.Kind.SAND
		if x0 >= tee_from and x0 < tee_to:
			kind = GolfCourse.Kind.DECK
		elif x0 >= green_from and x0 < green_to:
			kind = GolfCourse.Kind.DECK
		elif x0 >= green_to:
			kind = GolfCourse.Kind.HULL
		h.kinds[i] = kind
	# Пролив: дно ниже экрана, отрезки моря.
	if wf >= 0:
		h.water_from = wf
		h.water_to = wf + w
		for i in points:
			if i * st > wf and i * st < wf + w:
				h.heights[i] = t.sea_floor
		for i in points - 1:
			if i * st >= wf and i * st < wf + w:
				h.kinds[i] = GolfCourse.Kind.WATER
	h.cup_x = rng.randi_range(green_from + t.cup_margin, green_to - t.cup_margin)
	h.par = 3 if h.cup_x - h.tee_x < t.par4_from else 4
	h.wind = rng.randi_range(-t.wind_max, t.wind_max)
	var props := rng.randi_range(t.props_min, t.props_max)
	var tries := 0
	while h.props.size() < props and tries < 40:
		tries += 1
		var x := rng.randi_range(tee_to + t.prop_gap, green_from - t.prop_gap)
		if h.has_water() and x > h.water_from - t.prop_gap and x < h.water_to + t.prop_gap:
			continue
		if absf(h.height_at(x - 6) - h.height_at(x + 6)) > 3.0:
			continue
		var crowded := false
		for p in h.props:
			if absi(p.x - x) < 24:
				crowded = true
		if not crowded:
			h.props.append(Vector2i(x, rng.randi_range(0, 1)))
	return h


## Пустая строка, если поле годится, иначе причина.
static func validate(c: GolfCourse, t: GolfGenTuning) -> String:
	if c.holes.size() < t.holes_min or c.holes.size() > t.holes_max:
		return "лунок %d" % c.holes.size()
	for n in c.holes.size():
		var why := _validate_hole(c.holes[n], t)
		if why != "":
			return "лунка %d: %s" % [n + 1, why]
	return ""


static func _validate_hole(h: GolfCourse.Hole, t: GolfGenTuning) -> String:
	if h.length < t.length_min - h.step or h.length > t.length_max + h.step or h.length % h.step != 0:
		return "длина %d" % h.length
	if h.heights.size() != h.length / h.step + 1 or h.kinds.size() != h.heights.size() - 1:
		return "размер карты высот"
	var tee := h.height_at(h.tee_x)
	if absf(h.height_at(h.tee_x - 12) - tee) > 0.01 or absf(h.height_at(h.tee_x + 12) - tee) > 0.01:
		return "ти не ровный"
	if h.kind_at(h.tee_x) != GolfCourse.Kind.DECK:
		return "ти не на палубе"
	var deck := h.height_at(h.green_from)
	for x in range(int(h.green_from), int(h.green_to) + 1, h.step):
		if absf(h.height_at(x) - deck) > 0.01 or (x < h.green_to and h.kind_at(x) != GolfCourse.Kind.DECK):
			return "палуба грина не ровная"
	if h.cup_x < h.green_from + t.cup_margin or h.cup_x > h.green_to - t.cup_margin:
		return "люк у края палубы"
	for i in h.kinds.size():
		if h.kinds[i] != GolfCourse.Kind.SAND:
			continue
		var x := i * h.step
		var edge := (i > 0 and h.kinds[i - 1] != GolfCourse.Kind.SAND) or (i < h.kinds.size() - 1 and h.kinds[i + 1] != GolfCourse.Kind.SAND)
		if (x > h.tee_x and h.heights[i] < t.ground_top - 0.5) or h.heights[i] > t.ground_bottom + 0.5:
			return "песок вне высот на x %d" % x
		if not edge and absf(h.heights[i + 1] - h.heights[i]) > t.max_rise:
			return "крутой склон на x %d" % x
	if h.has_water():
		var w := h.water_to - h.water_from
		if w < t.water_min - h.step or w > t.water_max + h.step:
			return "пролив шириной %d" % int(w)
		if h.water_from < h.tee_x + t.water_gap or h.water_to > h.green_from - t.water_gap + h.step:
			return "пролив у ти или грина"
		if h.height_at(h.water_from - 0.5) > t.sea_y - t.bank_above + 0.5 or h.height_at(h.water_to + 0.5) > t.sea_y - t.bank_above + 0.5:
			return "берег пролива ниже моря"
	if h.par != (3 if h.cup_x - h.tee_x < t.par4_from else 4):
		return "пар %d" % h.par
	if absi(h.wind) > t.wind_max:
		return "ветер %d" % h.wind
	return ""
