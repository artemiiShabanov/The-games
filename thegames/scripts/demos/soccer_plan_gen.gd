class_name SoccerPlanGen
extends RefCounted
## План соперника футбола из сида (#101): детерминирован. Каждое число в своём разбросе
## (`SportBit16GenTuning`); вратари своего и чужого разные. `validate` проверяет разбросы.


static func generate(seed_: int, t: SportBit16GenTuning = null) -> SoccerPlan:
	if t == null:
		t = SportBit16GenTuning.load_default()
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":soccer"))
	var p := SoccerPlan.new()
	p.rival_speed = roundf(rng.randf_range(t.rival_speed_min, t.rival_speed_max))
	p.rival_shot_range = roundf(rng.randf_range(t.shot_range_min, t.shot_range_max))
	p.rival_charge = snappedf(rng.randf_range(t.charge_min, t.charge_max), 0.01)
	p.rival_tackle = snappedf(rng.randf_range(t.tackle_min, t.tackle_max), 0.01)
	p.rival_react = snappedf(rng.randf_range(t.react_min, t.react_max), 0.01)
	p.keeper_reach = roundf(rng.randf_range(t.keeper_reach_min, t.keeper_reach_max))
	p.keeper_react = snappedf(rng.randf_range(t.keeper_react_min, t.keeper_react_max), 0.01)
	p.rival_keeper_reach = roundf(rng.randf_range(t.keeper_reach_min, t.keeper_reach_max))
	p.rival_keeper_react = snappedf(rng.randf_range(t.keeper_react_min, t.keeper_react_max), 0.01)
	p.rival_kit = rng.randi_range(0, 2)
	p.seed = seed_
	return p


static func validate(p: SoccerPlan, t: SportBit16GenTuning) -> String:
	if p.rival_speed < t.rival_speed_min - 1.0 or p.rival_speed > t.rival_speed_max + 1.0:
		return "скорость соперника %.0f" % p.rival_speed
	if p.rival_shot_range < t.shot_range_min - 1.0 or p.rival_shot_range > t.shot_range_max + 1.0:
		return "дальность удара %.0f" % p.rival_shot_range
	if p.keeper_reach < t.keeper_reach_min - 1.0 or p.rival_keeper_reach > t.keeper_reach_max + 1.0:
		return "прыжок вратаря"
	return ""
