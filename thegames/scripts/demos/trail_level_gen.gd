class_name TrailLevelGen
extends RefCounted
## Генератор уровня «тропа» из сида (#98): детерминирован. Земля это ровные участки и склоны
## двух наклонов (1 к 2 и 1 к 1), уровень гуляет холмами. Ловушки одна за другой,
## между ними отдых, начало отдыха это место возврата после потери жизни. Ловушки: холм, яма,
## широкая яма с лианами, арка из корней (пройти только в слайде), краб на ровном, попугай на
## высоте головы, краб на холме, спуск в арку. Первая ловушка всегда яма: без неё бот LOSE не
## проиграет. Одна и та же ловушка не идёт два раза подряд. `validate` проверяет раскладку.

enum Trap { HILL, GAP, VINES, ARCH, CRAB, PARROT, HILL_CRAB, SLOPE_ARCH }
enum Decor { GRASS, TUFT, BUSH, FERN, ROCK, FLOWERS, MUSH }

## Отступ места возврата от начала отдыха.
const CHECKPOINT_IN := 24.0


static func generate(seed_: int, t: PlatformerBit16GenTuning = null) -> TrailLevel:
	if t == null:
		t = PlatformerBit16GenTuning.load_default()
	var g := TrailLevelGen.new()
	g._t = t
	g._rng.seed = hash(str(seed_, ":trail"))
	g._lv.width = t.width
	g._lv.water_y = t.water_y
	g._build()
	return g._lv


var _t: PlatformerBit16GenTuning
var _rng := RandomNumberGenerator.new()
var _lv := TrailLevel.new()
var _x := 0.0
var _y := 0.0
## Участки, где украшений не ставить: под арками и у краёв ям.
var _no_decor := PackedFloat32Array()


func _build() -> void:
	_y = _t.ground_y
	_lv.points.append(Vector2(0.0, _y))
	_lv.start_x = 40.0
	_lv.checkpoints.append(_lv.start_x)
	_flat(_t.start_flat)
	var weights: Array[float] = [_t.weight_hill, _t.weight_gap, _t.weight_vines, _t.weight_arch, _t.weight_crab,
			_t.weight_parrot, _t.weight_hill_crab, _t.weight_slope_arch]
	var last := -1
	while _x < _t.width - _t.end_flat - 360.0:
		var trap := Trap.GAP if last == -1 else _pick(weights, last)
		var k := _x / _t.width
		match trap:
			Trap.HILL:
				_hill(k, false)
			Trap.GAP:
				_gap(k)
			Trap.VINES:
				_vines(k)
			Trap.ARCH:
				_flat(36.0)
				_arch()
			Trap.CRAB:
				_crab(k)
			Trap.PARROT:
				_parrot(k)
			Trap.HILL_CRAB:
				_hill(k, true)
			Trap.SLOPE_ARCH:
				_slope_arch(k)
		last = trap
		# Отдых: место возврата в его начале.
		_lv.checkpoints.append(_x + CHECKPOINT_IN)
		var rest := _rng.randf_range(_t.rest_min, _t.rest_max)
		if _rng.randf() < _t.coin_rest_chance:
			_coin(Vector2(_x + rest * 0.5, _y - 30.0))
		_flat(rest)
	_flat(_t.width - _x)
	_lv.flag_x = _t.width - 120.0
	_decorate()


func _pick(weights: Array[float], last: int) -> Trap:
	var total := 0.0
	for i in weights.size():
		total += weights[i] if i != last else 0.0
	var r := _rng.randf() * total
	for i in weights.size():
		if i == last:
			continue
		r -= weights[i]
		if r <= 0.0:
			return i as Trap
	return Trap.HILL


## Ровный участок длиной `length`; кончается на уровне `_y`.
func _flat(length: float, _rough := true) -> void:
	if length < 1.0:
		return
	_x += length
	_lv.points.append(Vector2(_x, _y))


## Наклон склона: пологий или изредка крутой.
func _slope() -> float:
	return _t.slope_steep_deg if _rng.randf() < _t.steep_chance else _t.slope_gentle_deg


## Склон на `dy` пикселей (минус вверх) с наклоном `deg`; длина по x кратна двум пикселям,
## чтобы ступени рисунка ложились ровно.
func _ramp(dy: float, deg: float) -> void:
	dy = roundf(dy / 2.0) * 2.0
	if dy == 0.0:
		return
	_x += roundf(absf(dy) / tan(deg_to_rad(deg)))
	_y += dy
	_lv.points.append(Vector2(_x, _y))


## Холм: подъём, плато, спуск к новому уровню рядом с прежним. С крабом он ходит по всему холму.
func _hill(k: float, crab: bool) -> void:
	var rise := _rng.randf_range(_t.hill_rise_min, _t.hill_rise_max)
	var up := -1.0 if _y - rise >= _t.ground_min_y else 1.0
	if up > 0.0 and _y + rise > _t.ground_max_y:
		rise = maxf(_t.ground_max_y - _y, 12.0)
	var start := _x
	_ramp(up * rise, _slope())
	var top_y := _y
	_flat(_rng.randf_range(40.0, 90.0))
	if _rng.randf() < _t.coin_trap_chance:
		_coin(Vector2(_x - 30.0, top_y - 36.0))
	var back := clampf(top_y - up * rise + _rng.randf_range(-16.0, 16.0), _t.ground_min_y, _t.ground_max_y)
	_ramp(back - _y, _slope())
	if crab:
		_foe(TrailLevel.FoeKind.CRAB, start + 8.0, _x - 8.0, lerpf(_t.crab_speed_first, _t.crab_speed_last, k))
	_flat(24.0)


## Яма: край, вода, другой край чуть выше или ниже.
func _gap(k: float) -> void:
	_flat(16.0)
	var w := lerpf(_t.gap_first, _t.gap_last, k) + _rng.randf_range(-6.0, 6.0)
	var x0 := _x
	var y0 := _y
	_lv.gaps.append(x0)
	_lv.gaps.append(x0 + w)
	_x = x0 + w
	_y = clampf(_y + roundf(_rng.randf_range(-_t.gap_step, _t.gap_step)), _t.ground_min_y + 20.0, _t.ground_max_y)
	_lv.points.append(Vector2(_x, _y))
	_no_decor.append_array([x0 - 10.0, _x + 10.0])
	if _rng.randf() < _t.coin_trap_chance:
		_coin(Vector2(x0 + w * 0.5, minf(y0, _y) - 46.0))
	_flat(20.0)


## Широкая яма с одной или двумя лианами; низ лианы над краем на `vine_reach`.
func _vines(k: float) -> void:
	_flat(24.0, false)
	var w := _rng.randf_range(_t.vine_gap_min, _t.vine_gap_max) + 10.0 * k
	var x0 := _x
	var y0 := _y
	_lv.gaps.append(x0)
	_lv.gaps.append(x0 + w)
	var spots: Array[float] = []
	if w < 186.0:
		spots.append(0.42)
	else:
		spots.append_array([0.3, 0.68])
	for s in spots:
		var v := TrailLevel.Vine.new()
		v.anchor = Vector2(roundf(x0 + w * s), -8.0)
		v.length = y0 - _t.vine_reach - v.anchor.y
		_lv.vines.append(v)
		if _rng.randf() < _t.coin_trap_chance:
			_coin(Vector2(v.anchor.x, y0 - _t.vine_reach + 6.0))
	_x = x0 + w
	_y = clampf(y0 + roundf(_rng.randf_range(-8.0, 8.0)), _t.ground_min_y + 20.0, _t.ground_max_y)
	_lv.points.append(Vector2(_x, _y))
	_no_decor.append_array([x0 - 10.0, _x + 10.0])
	_flat(24.0, false)


## Арка из корней на ровной земле без неровностей; монеты под ней берутся в слайде.
func _arch() -> void:
	_flat(12.0, false)
	var a := TrailLevel.Arch.new()
	a.from = _x
	a.to = _x + roundf(_rng.randf_range(_t.arch_min, _t.arch_max))
	a.gap = _t.arch_gap
	_lv.arches.append(a)
	_flat(a.to - a.from, false)
	_flat(12.0, false)
	_no_decor.append_array([a.from - 16.0, a.to + 16.0])
	if _rng.randf() < _t.coin_trap_chance:
		_coin(Vector2((a.from + a.to) * 0.5, _y - 8.0))


## Спуск в арку: подъём, короткое плато, спуск круче и сразу арка.
func _slope_arch(_k: float) -> void:
	var rise := _rng.randf_range(_t.hill_rise_min, _t.hill_rise_max)
	if _y - rise < _t.ground_min_y:
		rise = maxf(_y - _t.ground_min_y, 16.0)
	_ramp(-rise, _t.slope_gentle_deg)
	_flat(_rng.randf_range(24.0, 48.0))
	_ramp(clampf(_y + rise + _rng.randf_range(-8.0, 12.0), _t.ground_min_y, _t.ground_max_y) - _y,
			_slope())
	_arch()


func _crab(k: float) -> void:
	var span := _rng.randf_range(_t.crab_span_min, _t.crab_span_max)
	var x0 := _x
	_flat(span + 40.0)
	_foe(TrailLevel.FoeKind.CRAB, x0 + 20.0, x0 + 20.0 + span, lerpf(_t.crab_speed_first, _t.crab_speed_last, k))
	if _rng.randf() < _t.coin_trap_chance:
		_coin(Vector2(x0 + 20.0 + span * 0.5, _y - 52.0))


func _parrot(k: float) -> void:
	var span := _rng.randf_range(_t.parrot_span_min, _t.parrot_span_max)
	var x0 := _x
	_flat(span + 40.0)
	_foe(TrailLevel.FoeKind.PARROT, x0 + 20.0, x0 + 20.0 + span, lerpf(_t.parrot_speed_first, _t.parrot_speed_last, k))
	if _rng.randf() < _t.coin_trap_chance:
		_coin(Vector2(x0 + 20.0 + span * 0.5, _y - 8.0))


func _foe(kind: TrailLevel.FoeKind, from: float, to: float, speed: float) -> void:
	var f := TrailLevel.Foe.new()
	f.kind = kind
	f.from = roundf(from)
	f.to = roundf(to)
	f.speed = roundf(speed)
	f.phase = _rng.randf()
	_lv.foes.append(f)


func _coin(p: Vector2) -> void:
	_lv.coins.append(Vector2(roundf(p.x), roundf(p.y)))


## Украшения переднего плана: трава и кочки перед героем, кусты, папоротники, камни, цветы,
## грибы за ним.
func _decorate() -> void:
	var x := 0.0
	while x < _t.width - 40.0:
		x += _rng.randf_range(_t.decor_every * 0.5, _t.decor_every * 1.5)
		if _lv.height_at(x - 12.0) == INF or _lv.height_at(x + 12.0) == INF or _blocked(x):
			continue
		var r := _rng.randf()
		var kind := Decor.GRASS if r < 0.22 else (Decor.TUFT if r < 0.4 else (Decor.BUSH if r < 0.56 else
				(Decor.FERN if r < 0.7 else (Decor.FLOWERS if r < 0.82 else (Decor.MUSH if r < 0.91 else Decor.ROCK)))))
		# Большие украшения только на ровном: на склоне они висят над землёй.
		if kind in [Decor.BUSH, Decor.FERN, Decor.ROCK] and absf(_lv.slope_at(x)) > 0.01:
			kind = Decor.TUFT
		_lv.decor.append(Vector2i(int(x), kind))


func _blocked(x: float) -> bool:
	for i in range(0, _no_decor.size(), 2):
		if x > _no_decor[i] and x < _no_decor[i + 1]:
			return true
	return false


## Проверка раскладки; пустая строка, если всё в порядке.
static func validate(lv: TrailLevel, t: PlatformerBit16GenTuning) -> String:
	for i in range(1, lv.points.size()):
		var a := lv.points[i - 1]
		var b := lv.points[i]
		if b.x <= a.x:
			return "точки не по порядку у x %.0f" % b.x
		if b.y < t.ground_min_y - 1.0 or b.y > t.ground_max_y + 1.0:
			return "земля у x %.0f на высоте %.0f" % [b.x, b.y]
		var mid := (a.x + b.x) * 0.5
		if not lv.in_gap(mid) and absf(b.y - a.y) / (b.x - a.x) > tan(deg_to_rad(t.slope_steep_deg)) + 0.05:
			return "склон круче %.0f° у x %.0f" % [t.slope_steep_deg, a.x]
	if lv.gaps.is_empty():
		return "нет ям"
	for a in lv.arches:
		if lv.gaps[0] > a.from:
			return "арка раньше первой ямы"
		var h0 := lv.height_at(a.from)
		var x := a.from
		while x <= a.to:
			if absf(lv.height_at(x) - h0) > 0.5:
				return "под аркой у x %.0f земля неровная" % x
			x += 4.0
	for f in lv.foes:
		if lv.gaps[0] > f.from:
			return "враг раньше первой ямы"
		var x := f.from
		while x <= f.to:
			if lv.height_at(x) == INF:
				return "участок врага у x %.0f над ямой" % x
			x += 4.0
	for c in lv.checkpoints:
		if lv.height_at(c) == INF or lv.arch_at(c) != null:
			return "место возврата %.0f не на земле" % c
		for f in lv.foes:
			if c > f.from - 30.0 and c < f.to + 30.0:
				return "место возврата %.0f на пути врага" % c
	for v in lv.vines:
		if not lv.in_gap(v.anchor.x):
			return "лиана %.0f не над ямой" % v.anchor.x
	if lv.height_at(lv.flag_x) == INF:
		return "флаг не на земле"
	return ""
