class_name RailLevelGen
extends RefCounted
## Генератор маршрута «рельсового тира» (#114) из сида. Путь камеры: остановки через 10–14 м с
## поворотами то в одну, то в другую сторону, по дюнам. На остановке камера смотрит чуть в
## сторону от пути, перед ней веером стоят укрытия; враги выходят группами, к концу маршрута
## групп больше и целятся они быстрее. По маршруту раскиданы метатели бутылок, два капитана,
## пленные и бочки с порохом рядом с парой укрытий; в каждом переезде сбоку выбегает бегун.
## Маршрут сида это первая попытка, что проходит `validate`.

const ATTEMPTS := 200
const BARREL := Vector2(0.52, 1.2)
const CRATE := Vector2(0.64, 1.28)
const FOE_HEIGHT := 1.82


static func generate(seed_: int, t: ShooterLowpolyGenTuning = null, rules: ShooterLowpolyTuning = null) -> RailLevel:
	if t == null:
		t = ShooterLowpolyGenTuning.load_default()
	if rules == null:
		rules = ShooterLowpolyTuning.load_default()
	var level: RailLevel = null
	for attempt in ATTEMPTS:
		level = _build(seed_, attempt, t, rules)
		if validate(level, t, rules) == "":
			break
	return level


static func _forward(yaw: float) -> Vector3:
	return Vector3(-sin(yaw), 0.0, -cos(yaw))


static func _right(yaw: float) -> Vector3:
	return Vector3(cos(yaw), 0.0, -sin(yaw))


static func _build(seed_: int, attempt: int, t: ShooterLowpolyGenTuning, rules: ShooterLowpolyTuning) -> RailLevel:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":rail:", attempt))
	var level := RailLevel.new()
	var freq := TAU / t.dune_length
	level.dune = PackedFloat32Array([t.dune_a, t.dune_b, freq, freq * 1.3, rng.randf_range(0.0, TAU), rng.randf_range(0.0, TAU),
			rng.randf_range(0.0, TAU)])
	level.island = t.island_height
	level.shore_from = t.shore_from
	level.shore_slope = t.shore_slope
	level.eye = t.eye
	var tan_half := tan(deg_to_rad(rules.fov) / 2.0)
	# Путь: повороты чаще в разные стороны, курс не уходит от начального дальше предела.
	var heading := 0.0
	var side := 1.0 if rng.randf() < 0.5 else -1.0
	var at := Vector3.ZERO
	var headings := PackedFloat32Array()
	for i in t.stops + 1:
		var stop := RailLevel.Stop.new()
		if i > 0:
			heading = clampf(heading + side * deg_to_rad(rng.randf_range(t.turn_min, t.turn_max)), -deg_to_rad(t.heading_limit),
					deg_to_rad(t.heading_limit))
			if rng.randf() < 0.7:
				side = -side
			var leg := rng.randf_range(t.leg_min, t.leg_max)
			at += _forward(heading) * leg
			stop.travel = leg / t.speed
		stop.pos = at
		headings.append(heading)
		level.stops.append(stop)
	for i in level.stops.size():
		var stop := level.stops[i]
		stop.pos.y = level.height(stop.pos.x, stop.pos.z) + t.eye
		# Взгляд: на следующую остановку с отклонением; на финише по ходу.
		var next := headings[mini(i + 1, headings.size() - 1)]
		stop.yaw = next + (deg_to_rad(rng.randf_range(-t.view_turn, t.view_turn)) if i < t.stops else 0.0)
	# Укрытия веером перед камерой остановки.
	for i in t.stops:
		var stop := level.stops[i]
		var n := rng.randi_range(t.covers_min, t.covers_max)
		var first := level.covers.size()
		for k in n:
			for tries in 18:
				# Своя доля ширины кадра; если там проходит путь камеры, то где найдётся место.
				var x := lerpf(-t.cover_spread, t.cover_spread, (k + rng.randf_range(0.2, 0.8)) / n)
				if tries >= 5:
					x = rng.randf_range(-t.cover_spread, t.cover_spread)
				var angle := atan(x * tan_half * rules.aspect)
				var dir := _forward(stop.yaw) * cos(angle) + _right(stop.yaw) * sin(angle)
				var p := level.ground(stop.pos + dir * rng.randf_range(t.cover_near, t.cover_far))
				var a := Vector2(stop.pos.x, stop.pos.z)
				var b := Vector2(level.stops[i + 1].pos.x, level.stops[i + 1].pos.z)
				var flat := Vector2(p.x, p.z)
				var free := flat.distance_to(Geometry2D.get_closest_point_to_segment(flat, a, b)) > 1.5
				for other in range(first, level.covers.size()):
					free = free and level.covers[other].pos.distance_to(p) > 1.9
				if not free:
					continue
				var cover := RailLevel.Cover.new()
				cover.stop = i
				cover.shape = RailLevel.Shape.CRATE if rng.randf() < 0.45 else RailLevel.Shape.BARREL
				var size := CRATE if cover.shape == RailLevel.Shape.CRATE else BARREL
				cover.half = size.x
				cover.height = size.y
				cover.pos = p
				cover.yaw = atan2(dir.x, dir.z)
				level.covers.append(cover)
				break
		# Наклон взгляда: середина укрытий чуть ниже середины кадра.
		var mid := Vector3.ZERO
		for k in range(first, level.covers.size()):
			mid += level.covers[k].pos + Vector3(0.0, 1.3, 0.0)
		if level.covers.size() > first:
			mid /= level.covers.size() - first
			var to := mid - stop.pos
			stop.pitch = atan2(to.y, Vector2(to.x, to.z).length()) - 0.13
	level.stops[t.stops].pitch = -0.08
	# Группы врагов.
	for i in t.stops:
		var stop := level.stops[i]
		var late := float(i) / maxf(t.stops - 1, 1.0)
		var mine: Array[int] = []
		for k in level.covers.size():
			if level.covers[k].stop == i:
				mine.append(k)
		stop.groups = int(roundf(lerpf(t.groups_first, t.groups_last, late)))
		for g in stop.groups:
			var size := mini(rng.randi_range(t.group_min, t.group_max) + (1 if i >= 2 and g == stop.groups - 1 else 0), mine.size())
			size = mini(size, t.group_max)
			var order := mine.duplicate()
			_shuffle(order, rng)
			for k in size:
				var foe := _foe_at(level, order[k], stop, rng)
				foe.stop = i
				foe.group = g
				foe.delay = k * t.stagger * rng.randf_range(0.6, 1.2)
				foe.kind = RailLevel.Kind.THROWER if i >= t.thrower_from and rng.randf() < t.thrower_share else RailLevel.Kind.SAILOR
				foe.aim = t.windup if foe.kind == RailLevel.Kind.THROWER else lerpf(t.aim_first, t.aim_last, late) * rng.randf_range(0.92, 1.08)
				level.foes.append(foe)
	# Капитаны: один в последней группе последней остановки, остальные на остановках со второй.
	var last := level.foes_of(t.stops - 1, level.stops[t.stops - 1].groups - 1)
	var captains := 0
	if not last.is_empty():
		_promote(level.foes[last[0]], t)
		captains += 1
	for tries in 40:
		if captains >= t.captains:
			break
		var foe := level.foes[rng.randi_range(0, level.foes.size() - 1)]
		if foe.stop >= 2 and foe.stop < t.stops - 1 and foe.kind == RailLevel.Kind.SAILOR:
			_promote(foe, t)
			captains += 1
	# Пленные: в группе за свободным укрытием, высовываются вверх.
	var hostages := rng.randi_range(t.hostages_min, t.hostages_max)
	for tries in 60:
		if hostages <= 0:
			break
		var i := rng.randi_range(0, t.stops - 1)
		var g := rng.randi_range(0, level.stops[i].groups - 1)
		var taken := {}
		var has_hostage := false
		for f in level.foes_of(i, g):
			taken[level.foes[f].cover] = true
			has_hostage = has_hostage or level.foes[f].kind == RailLevel.Kind.HOSTAGE
		var free: Array[int] = []
		for k in level.covers.size():
			if level.covers[k].stop == i and not taken.has(k):
				free.append(k)
		if free.is_empty() or has_hostage:
			continue
		var foe := _foe_at(level, free[rng.randi_range(0, free.size() - 1)], level.stops[i], rng, true)
		foe.kind = RailLevel.Kind.HOSTAGE
		foe.stop = i
		foe.group = g
		foe.delay = rng.randf_range(0.3, 1.4)
		foe.aim = t.hostage_hold
		level.foes.append(foe)
		hostages -= 1
	# Бочки с порохом: между двумя близкими укрытиями, на шаг ближе к камере.
	var keg_stops: Array[int] = []
	for i in range(1, t.stops):
		keg_stops.append(i)
	_shuffle(keg_stops, rng)
	for i in keg_stops:
		if level.kegs.size() >= t.kegs:
			break
		var best := Vector3.ZERO
		var found := false
		for a in level.covers.size():
			for b in range(a + 1, level.covers.size()):
				if found or level.covers[a].stop != i or level.covers[b].stop != i:
					continue
				if level.covers[a].pos.distance_to(level.covers[b].pos) < t.keg_radius * 1.5:
					var mid := (level.covers[a].pos + level.covers[b].pos) / 2.0
					var toward := level.stops[i].pos - mid
					toward.y = 0.0
					best = level.ground(mid + toward.normalized() * 1.3)
					found = true
		if found:
			var keg := RailLevel.Keg.new()
			keg.stop = i
			keg.pos = best
			keg.radius = t.keg_radius
			level.kegs.append(keg)
	# Бегуны: в переезде к каждой остановке со второй, выбегают сбоку в кадр.
	for i in range(1, t.stops + 1):
		# Ставится по кадру, каким он будет, пока бегун на виду (камера в это время почти стоит).
		var cam := level.pose_pos(i, t.runner_at + 0.12)
		var look := level.pose_look(i, t.runner_at + 0.12)
		var from_side := 1.0 if rng.randf() < 0.5 else -1.0
		var angle := atan(from_side * rng.randf_range(0.25, 0.5) * tan_half * rules.aspect)
		var dir := _forward(look.x) * cos(angle) + _right(look.x) * sin(angle)
		var foe := RailLevel.Foe.new()
		foe.kind = RailLevel.Kind.RUNNER
		foe.stop = i
		foe.group = -1
		foe.delay = t.runner_at
		foe.aim = t.aim_runner
		foe.out = level.ground(cam + dir * rng.randf_range(t.runner_near, t.runner_far))
		foe.hide = level.ground(foe.out + _right(look.x) * from_side * 4.5)
		level.foes.append(foe)
	return level


## Враг за укрытием: бочка выпускает вбок или вверх, ящик только вверх.
static func _foe_at(level: RailLevel, cover_i: int, stop: RailLevel.Stop, rng: RandomNumberGenerator, up := false) -> RailLevel.Foe:
	var cover := level.covers[cover_i]
	var away := cover.pos - stop.pos
	away.y = 0.0
	away = away.normalized()
	var behind := cover.pos + away * (cover.half + 0.4)
	var foe := RailLevel.Foe.new()
	foe.cover = cover_i
	var style := rng.randi_range(0, 2)
	if up or cover.shape == RailLevel.Shape.CRATE or style == 2:
		# Вверх: встаёт на приступку за укрытием.
		foe.hide = level.ground(behind) - Vector3(0.0, FOE_HEIGHT - cover.height + 0.15, 0.0)
		foe.out = level.ground(behind) + Vector3(0.0, 0.5, 0.0)
	else:
		var sideways := Vector3(-away.z, 0.0, away.x) * (1.0 if style == 0 else -1.0)
		# У края кадра высовывается к середине, иначе окажется за кадром.
		var lateral := away.dot(_right(stop.yaw))
		if absf(lateral) > 0.25 and sideways.dot(_right(stop.yaw)) * lateral > 0.0:
			sideways = -sideways
		foe.hide = level.ground(behind) - Vector3(0.0, FOE_HEIGHT - cover.height + 0.15, 0.0)
		foe.out = level.ground(behind + sideways * (cover.half + 0.5))
	return foe


static func _promote(foe: RailLevel.Foe, t: ShooterLowpolyGenTuning) -> void:
	foe.kind = RailLevel.Kind.CAPTAIN
	foe.aim = t.aim_captain


static func _shuffle(list: Array, rng: RandomNumberGenerator) -> void:
	for i in range(list.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var swap: Variant = list[i]
		list[i] = list[j]
		list[j] = swap


## Пусто, если маршрут годится; иначе что не так.
static func validate(level: RailLevel, t: ShooterLowpolyGenTuning = null, rules: ShooterLowpolyTuning = null) -> String:
	if t == null:
		t = ShooterLowpolyGenTuning.load_default()
	if rules == null:
		rules = ShooterLowpolyTuning.load_default()
	var tan_half := tan(deg_to_rad(rules.fov) / 2.0)
	for i in level.stops.size():
		for j in range(i + 2, level.stops.size()):
			if level.stops[i].pos.distance_to(level.stops[j].pos) < 9.0:
				return "остановки %d и %d рядом" % [i, j]
	for i in t.stops:
		var n := 0
		for c in level.covers:
			n += 1 if c.stop == i else 0
		if n < t.covers_min:
			return "укрытий на остановке %d: %d" % [i, n]
		if level.foes_of(i, 0).is_empty():
			return "остановка %d без врагов" % i
	# Камера ни в одном переезде не проходит вплотную к укрытию.
	for c in level.covers:
		if level.path_distance(c.pos.x, c.pos.z) < 1.5:
			return "укрытие на пути камеры"
	for i in level.foes.size():
		var foe := level.foes[i]
		var head := foe.out + Vector3(0.0, rules.head_y, 0.0)
		if foe.kind == RailLevel.Kind.RUNNER:
			# Бегун виден, когда добежал и когда стреляет (камера ещё едет или уже встала).
			var travel := level.stops[foe.stop].travel
			for moment: float in [rules.runner_run, rules.runner_run + foe.aim]:
				var k := minf(foe.delay + moment * rules.runner_slow / travel, 1.0)
				var cam := level.pose_pos(foe.stop, k)
				var at := RailLevel.project(head, cam, level.pose_look(foe.stop, k), tan_half, rules.aspect)
				if at.z < 3.0 or absf(at.x) > 0.9 or absf(at.y) > 0.85 or not level.sees(cam, head):
					return "бегун к остановке %d не в кадре" % foe.stop
			continue
		var stop := level.stops[foe.stop]
		var at := RailLevel.project(head, stop.pos, Vector2(stop.yaw, stop.pitch), tan_half, rules.aspect)
		if at.z < 3.0 or absf(at.x) > 0.9 or absf(at.y) > 0.8:
			return "враг %d не в кадре" % i
		if not level.sees(stop.pos, head):
			return "враг %d закрыт" % i
	for k in level.kegs:
		var stop := level.stops[k.stop]
		var mid := k.pos + Vector3(0.0, rules.keg_y, 0.0)
		var at := RailLevel.project(mid, stop.pos, Vector2(stop.yaw, stop.pitch), tan_half, rules.aspect)
		if at.z < 3.0 or absf(at.x) > 0.88 or absf(at.y) > 0.85 or not level.sees(stop.pos, mid):
			return "бочка с порохом не видна"
		# Бочка не заслоняет голову врага своей остановки.
		for foe in level.foes:
			if foe.stop != k.stop or foe.kind == RailLevel.Kind.RUNNER:
				continue
			var to := foe.out + Vector3(0.0, rules.head_y, 0.0) - stop.pos
			var hit := RailLevel.hit_sphere(stop.pos, to.normalized(), mid, rules.keg_r + 0.15)
			if hit >= 0.0 and hit < to.length():
				return "бочка с порохом заслоняет врага"
	if level.kegs.size() < mini(t.kegs, 1):
		return "нет бочек с порохом"
	if level.count(RailLevel.Kind.CAPTAIN) < 1:
		return "нет капитана"
	if level.count(RailLevel.Kind.HOSTAGE) < t.hostages_min:
		return "пленных %d" % level.count(RailLevel.Kind.HOSTAGE)
	if level.hostiles() < 16:
		return "врагов %d" % level.hostiles()
	return ""
