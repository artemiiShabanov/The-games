class_name BrawlWavesGen
extends RefCounted
## Волны битемапа из сида (#102): детерминированы. С плейтеста 2026-11-15 (#132) до боцмана
## четыре волны и врагов в каждой в полтора раза больше прежнего: первая три-четыре головореза;
## вторая четыре-пять, головорезы и ножовщики; третья четыре-пять, ножовщиков больше; четвёртая
## пять вперемешку; пятый экран: двое-трое и боцман. Выходят с обеих сторон с задержками, на
## разной глубине. `validate` проверяет состав.

const SCREENS := 5
const SCREEN_MAX := 5

const NAMES: Array[String] = ["Хряк", "Сэм Кривой", "Рыжий Ник", "Бочка", "Гнилозуб", "Одноглазый",
		"Шнырь", "Косой Джо", "Бульдог", "Ржавый"]


static func generate(seed_: int, depth := 70.0) -> BrawlWaves:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(seed_, ":brawl"))
	var w := BrawlWaves.new()
	var thug := BrawlWaves.Kind.THUG
	var knife := BrawlWaves.Kind.KNIFE
	var plan: Array[Array] = [
		[thug, thug, thug] + ([thug] if rng.randf() < 0.75 else []),
		[thug, knife, thug, knife if rng.randf() < 0.5 else thug] + ([thug] if rng.randf() < 0.5 else []),
		[knife, thug, knife, thug if rng.randf() < 0.5 else knife] + ([knife] if rng.randf() < 0.5 else []),
		[thug, knife, thug, knife, knife if rng.randf() < 0.5 else thug],
		([thug, knife] if rng.randf() < 0.75 else [thug, knife, knife]) + [BrawlWaves.Kind.BOSS],
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
	if w.screens.size() != SCREENS:
		return "экранов %d" % w.screens.size()  # i18n: skip
	for i in SCREENS:
		if w.screens[i].is_empty() or w.screens[i].size() > SCREEN_MAX:
			return "на экране %d врагов %d" % [i + 1, w.screens[i].size()]  # i18n: skip
	var last: Array = w.screens[SCREENS - 1]
	if (last[last.size() - 1] as BrawlWaves.Spawn).kind != BrawlWaves.Kind.BOSS:
		return "на последнем экране нет боцмана"  # i18n: skip
	return ""
