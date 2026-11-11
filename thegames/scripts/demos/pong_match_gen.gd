class_name PongMatchGen
extends RefCounted
## Генератор матча понга из сида (#93): детерминирован. Соперник получает скорость ракетки,
## размах ошибки и запоздание из своих пределов; подачи чередуют верх и низ со случайным углом.


static func generate(seed_: int, t: SportVectorGenTuning = null) -> PongMatch:
	if t == null:
		t = SportVectorGenTuning.load_default()
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":pong"))
	var m := PongMatch.new()
	m.ai_speed = rng.randf_range(t.ai_speed_min, t.ai_speed_max)
	m.ai_error = rng.randf_range(t.ai_error_min, t.ai_error_max)
	m.ai_react = rng.randf_range(t.ai_react_min, t.ai_react_max)
	m.noise_seed = rng.randi()
	var up := rng.randf() < 0.5
	for i in t.serves:
		var a := deg_to_rad(rng.randf_range(t.serve_angle_min, t.serve_angle_max))
		m.serves.append(-a if up else a)
		up = not up if rng.randf() < 0.7 else up
	return m


## Проверка матча: "" или причина.
static func validate(m: PongMatch, t: SportVectorGenTuning) -> String:
	if m.ai_speed < t.ai_speed_min - 0.01 or m.ai_speed > t.ai_speed_max + 0.01:
		return "скорость соперника %.0f" % m.ai_speed
	if m.ai_error < t.ai_error_min - 0.01 or m.ai_error > t.ai_error_max + 0.01:
		return "ошибка соперника %.0f" % m.ai_error
	if m.ai_react < t.ai_react_min - 0.001 or m.ai_react > t.ai_react_max + 0.001:
		return "запоздание соперника %.2f" % m.ai_react
	if m.serves.size() != t.serves:
		return "подач %d" % m.serves.size()
	for a in m.serves:
		var deg := absf(rad_to_deg(a))
		if deg < t.serve_angle_min - 0.01 or deg > t.serve_angle_max + 0.01:
			return "подача под углом %.0f" % deg
	return ""
