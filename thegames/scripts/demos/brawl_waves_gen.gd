class_name BrawlWavesGen
extends RefCounted
## Волны битемапа из сида (#102): детерминированы. Первый экран: двое-трое головорезов; второй:
## трое, головорезы и ножовщики вперемешку; третий: один-двое и боцман. Выходят с обеих сторон
## с задержками, на разной глубине. `validate` проверяет состав.

const NAMES: Array[String] = ["Хряк", "Сэм Кривой", "Рыжий Ник", "Бочка", "Гнилозуб", "Одноглазый",
		"Шнырь", "Косой Джо", "Бульдог", "Ржавый"]


static func generate(seed_: int, depth := 70.0) -> BrawlWaves:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":brawl"))
	var w := BrawlWaves.new()
	var plan: Array[Array] = [
		[BrawlWaves.Kind.THUG, BrawlWaves.Kind.THUG] + ([BrawlWaves.Kind.THUG] if rng.randf() < 0.5 else []),
		[BrawlWaves.Kind.THUG, BrawlWaves.Kind.KNIFE, BrawlWaves.Kind.KNIFE if rng.randf() < 0.5 else BrawlWaves.Kind.THUG],
		([BrawlWaves.Kind.KNIFE] if rng.randf() < 0.5 else [BrawlWaves.Kind.THUG, BrawlWaves.Kind.KNIFE]) + [BrawlWaves.Kind.BOSS],
	]
	for kinds in plan:
		var screen: Array = []
		var delay := 0.3
		for k in kinds:
			var sp := BrawlWaves.Spawn.new()
			sp.kind = k
			sp.side = -1.0 if rng.randf() < 0.35 and k != BrawlWaves.Kind.BOSS else 1.0
			sp.delay = delay
			sp.y = roundf(rng.randf_range(8.0, depth - 8.0))
			delay += rng.randf_range(0.6, 1.6) if k != BrawlWaves.Kind.BOSS else 1.0
			screen.append(sp)
		w.screens.append(screen)
	var pool := NAMES.duplicate()
	for i in w.count():
		w.names.append(pool[rng.randi_range(0, pool.size() - 1)])
	return w


static func validate(w: BrawlWaves) -> String:
	if w.screens.size() != 3:
		return "экранов %d" % w.screens.size()
	for i in 3:
		if w.screens[i].is_empty() or w.screens[i].size() > 3:
			return "на экране %d врагов %d" % [i + 1, w.screens[i].size()]
	var last: Array = w.screens[2]
	if (last[last.size() - 1] as BrawlWaves.Spawn).kind != BrawlWaves.Kind.BOSS:
		return "на третьем экране нет боцмана"
	return ""
