class_name TurretWaveGen
extends RefCounted
## Генератор волн шутера × вектор из сида (#92): детерминирован. Появления идут всё чаще;
## большинство сбоку, где экран шире и врага видно дольше, быстрые враги только сбоку; соседние
## по времени появления разведены по направлению, чтобы ствол приходилось поворачивать.
## `validate` проверяет расписание.


static func generate(seed_: int, t: ShooterVectorGenTuning = null) -> TurretWaves:
	if t == null:
		t = ShooterVectorGenTuning.load_default()
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":turret"))
	var w := TurretWaves.new()
	var time := t.first_time
	var prev_angle := INF
	for i in t.count:
		var s := TurretWaves.Spawn.new()
		s.time = time
		var r := rng.randf()
		if i >= t.spinner_from and r < t.spinner_share:
			s.kind = TurretWaves.Kind.SPINNER
			s.speed = rng.randf_range(t.spinner_speed_min, t.spinner_speed_max)
			s.spin = deg_to_rad(rng.randf_range(t.spinner_spin_min, t.spinner_spin_max)) * (1.0 if rng.randf() < 0.5 else -1.0)
		elif r < t.spinner_share + t.rock_share:
			s.kind = TurretWaves.Kind.ROCK
			s.speed = rng.randf_range(t.rock_speed_min, t.rock_speed_max)
		else:
			s.kind = TurretWaves.Kind.ENEMY
			s.speed = rng.randf_range(t.enemy_speed_min, t.enemy_speed_max)
		var side := s.kind == TurretWaves.Kind.ENEMY or rng.randf() < t.side_share
		for attempt in 12:
			s.angle = _angle(rng, t, side)
			if prev_angle == INF or absf(angle_difference(prev_angle, s.angle)) >= deg_to_rad(t.min_turn):
				break
		prev_angle = s.angle
		w.spawns.append(s)
		var k := float(i) / maxf(t.count - 1, 1.0)
		time += lerpf(t.interval_start, t.interval_end, k) * rng.randf_range(1.0 - t.interval_jitter, 1.0 + t.interval_jitter)
	w.seconds = time
	return w


## Направление появления: сбоку (слева или справа в секторе) или сверху и снизу вне секторов.
static func _angle(rng: RandomNumberGenerator, t: ShooterVectorGenTuning, side: bool) -> float:
	var half := deg_to_rad(t.side_angle)
	if side:
		return (0.0 if rng.randf() < 0.5 else PI) + rng.randf_range(-half, half)
	return (PI / 2.0 if rng.randf() < 0.5 else -PI / 2.0) + rng.randf_range(-(PI / 2.0 - half), PI / 2.0 - half)


## Сбоку ли направление: в секторе ±`side_angle` от горизонтали.
static func is_side(angle: float, t: ShooterVectorGenTuning) -> bool:
	return absf(sin(angle)) <= sin(deg_to_rad(t.side_angle)) + 0.001


## Проверка расписания: "" или причина.
static func validate(w: TurretWaves, t: ShooterVectorGenTuning) -> String:
	if w.spawns.size() != t.count:
		return "появлений %d" % w.spawns.size()
	var prev := 0.0
	var lo := t.interval_end * (1.0 - t.interval_jitter) - 0.01
	for i in w.spawns.size():
		var s := w.spawns[i]
		if i > 0 and s.time - prev < lo:
			return "появление %d слишком скоро, через %.2f с" % [i, s.time - prev]
		prev = s.time
		match s.kind:
			TurretWaves.Kind.ENEMY:
				if s.speed < t.enemy_speed_min - 0.01 or s.speed > t.enemy_speed_max + 0.01:
					return "враг со скоростью %.0f" % s.speed
				if not is_side(s.angle, t):
					return "быстрый враг %d появляется не сбоку" % i
			TurretWaves.Kind.ROCK:
				if s.speed < t.rock_speed_min - 0.01 or s.speed > t.rock_speed_max + 0.01:
					return "глыба со скоростью %.0f" % s.speed
			TurretWaves.Kind.SPINNER:
				if i < t.spinner_from:
					return "вьюн раньше времени, появление %d" % i
				if s.speed < t.spinner_speed_min - 0.01 or s.speed > t.spinner_speed_max + 0.01:
					return "вьюн со скоростью %.0f" % s.speed
				if absf(s.spin) < deg_to_rad(t.spinner_spin_min) - 0.001 or absf(s.spin) > deg_to_rad(t.spinner_spin_max) + 0.001:
					return "вьюн кружит со скоростью %.2f" % s.spin
			_:
				return "появление %d неизвестного вида" % i
		if s.kind != TurretWaves.Kind.SPINNER and s.spin != 0.0:
			return "появление %d кружит, а не должно" % i
	if w.seconds <= prev:
		return "длина расписания %.1f" % w.seconds
	return ""
