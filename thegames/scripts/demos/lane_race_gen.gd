class_name LaneRaceGen
extends RefCounted
## Генератор заезда гонок × вектор из сида (#91): детерминирован. Ряды препятствий через
## случайный промежуток, в ряду от одного до трёх препятствий и всегда хотя бы одна свободная
## полоса; соперники стоят впереди лесенкой на разных полосах, темп у каждого свой и раздаётся
## по местам случайно. Проходимость дана построением: между рядами хватает места перестроиться
## через всю дорогу; `validate` проверяет раскладку.


static func generate(seed_: int, t: RacingVectorGenTuning = null) -> LaneRace:
	if t == null:
		t = RacingVectorGenTuning.load_default()
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":lanes"))
	var race := LaneRace.new()
	race.lanes = t.lanes
	race.length = t.length
	race.start_lane = rng.randi_range(0, t.lanes - 1)
	var d := t.first_row
	while d < t.length - t.last_clear:
		var r := rng.randf()
		var count := 1
		if r < t.three_chance:
			count = 3
		elif r < t.three_chance + t.two_chance:
			count = 2
		count = mini(count, t.lanes - 1)
		var free: Array[int] = []
		for l in t.lanes:
			free.append(l)
		for i in count:
			var k := rng.randi_range(0, free.size() - 1)
			race.obstacles.append(Vector2(free[k], d))
			free.remove_at(k)
		d += rng.randf_range(t.row_gap_min, t.row_gap_max)
	# Соперники: места на стартовой решётке по порядку, темпы перемешаны, полосы без повторов
	# подряд.
	var paces: Array[float] = []
	for i in t.rivals:
		var k := float(i) / maxf(t.rivals - 1, 1.0)
		paces.append(lerpf(t.rival_pace_min, t.rival_pace_max, k) * rng.randf_range(1.0 - t.rival_pace_jitter, 1.0 + t.rival_pace_jitter))
	var lane := race.start_lane
	for i in t.rivals:
		var rv := LaneRace.Rival.new()
		var k := float(i) / maxf(t.rivals - 1, 1.0)
		rv.head = lerpf(t.rival_head_min, t.rival_head_max, k)
		lane = (lane + rng.randi_range(1, t.lanes - 1)) % t.lanes
		rv.lane = lane
		var pick := rng.randi_range(0, paces.size() - 1)
		rv.pace = paces[pick]
		paces.remove_at(pick)
		rv.phase = rng.randf() * TAU
		race.rivals.append(rv)
	return race


## Проверка раскладки: "" или причина.
static func validate(race: LaneRace, t: RacingVectorGenTuning) -> String:
	if race.lanes != t.lanes or race.lanes < 3:
		return "полос %d" % race.lanes
	if race.obstacles.is_empty():
		return "нет препятствий"
	var row_d := -INF
	var in_row := 0
	for o in race.obstacles:
		if o.x < 0.0 or o.x >= race.lanes:
			return "препятствие вне дороги"
		if o.y < t.first_row - 0.01 or o.y > race.length - t.last_clear + 0.01:
			return "препятствие у старта или финиша"
		if is_equal_approx(o.y, row_d):
			in_row += 1
			if in_row >= race.lanes:
				return "ряд на %.0f перекрыт целиком" % o.y
		else:
			if o.y - row_d < t.row_gap_min - 0.01:
				return "ряды на %.0f слишком близко" % o.y
			row_d = o.y
			in_row = 1
	if race.rivals.size() != t.rivals:
		return "соперников %d" % race.rivals.size()
	for i in race.rivals.size():
		var r := race.rivals[i]
		if r.lane < 0 or r.lane >= race.lanes:
			return "соперник вне дороги"
		if r.head < t.rival_head_min - 0.01 or r.head > t.rival_head_max + 0.01:
			return "фора соперника %.0f" % r.head
		var lo := t.rival_pace_min * (1.0 - t.rival_pace_jitter) - 0.01
		var hi := t.rival_pace_max * (1.0 + t.rival_pace_jitter) + 0.01
		if r.pace < lo or r.pace > hi:
			return "темп соперника %.0f" % r.pace
		if i > 0 and r.lane == race.rivals[i - 1].lane:
			return "соперники стартуют в затылок"
	return ""
