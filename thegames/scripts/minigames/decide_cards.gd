extends Minigame
## «Реши» (decide_cards, баланс), каталог `docs/specs/minigames_catalog.md`. Карточки едут
## слева направо по одной, на каждой цветная фигура с числом внутри. Правило вверху крупно
## словами (плейтест 2026-11-11, #86): «≤ 30», «≥ 40», «чётное», «нечётное», цвет словом его
## цвета («синее»); стороны фигуры («≤ 5 сторон») только при `t` выше 0.8. Карточка въезжает в зону решения
## по центру и ждёт там `card_seconds`: ↑ принимает, любая другая стрелка отклоняет; не
## дождалась, уезжает вправо, это ошибка. Две ошибки: провал. Подходящих и неподходящих
## карточек поровну. С `t` темп выше, карточек больше, правило из двух условий («розовое и
## ≤ 30»), затем правило меняется посреди раунда. Параметры в
## `resources/minigames/decide_cards.tres`: cards, card_seconds, two (от 0.5 два условия),
## change (от 0.5 смена правила на середине).
## Мармелад (STYLE «Мармелад»): карточка и фигура на ней мягкие тела, отстают на въезде,
## качаются после остановки и наклоняются, улетая. Зона решения это серое гнездо без рамки;
## карточка в нём поднята на бортик (выделение толщиной, теней нет), решение вдавливает её и
## встряхивает, при смене правила оно вспухает. Верное решение роняет с карточки несколько
## неярких капель цвета успеха.

enum Kind { NUMBER_LE, NUMBER_GE, EVEN, ODD, COLOR, SIDES_LE, SIDES_GE }


class Cond:
	var kind: Kind
	var value := 0


class Card:
	var number := 0
	var color := 0
	var sides := 3
	var x := 0.0
	## Сколько ждёт в зоне решения.
	var wait := 0.0
	var decided := false
	var accepted := false
	var correct := true
	var age := 0.0
	var spawn_i := 0
	## Мармелад, только рисование: тело карточки, фигура на ней, высота бортика пружиной.
	var body: JellyShape
	var figure: JellyShape
	var lift := JellySpring.new()
	var landed := false


const COLORS: Array[Color] = [Color("#E0457B"), Color("#2F5BFF"), Color("#2BB37A")]
## Цвета словами в правиле: средний род, как «чётное» (первый цвет акцентный розовый).
const COLOR_NAMES: Array[String] = ["розовое", "синее", "зелёное"]
const CARD_W := 220.0
const CARD_H := 280.0
const FAIL_AT := 2
const FLY_SECONDS := 0.5
const ENTER_SECONDS := 0.35
const GAP_SECONDS := 0.2
const RULE_FLASH := 0.5
const BOT_REACTION := 0.25
## Условия на число сторон появляются только при `t` выше этого.
const SHAPES_FROM_T := 0.8
const FIGURE_R := 92.0
## Правило словами: крупно, не мельче `RULE_FONT_MIN`, с полями по бокам.
const RULE_FONT := 72
const RULE_FONT_MIN := 48
const RULE_MARGIN := 120.0
## Мармелад: точки контура карточки, наклон улетающей, бортик едущей (вместо тени), вздроги.
const CARD_POINTS := 64
const FLY_TILT := 0.14
const BASE_LIFT := 4.0
const LAND_POKE := 220.0
const DECIDE_POKE := -260.0
const WRONG_PUSH := 320.0
const RULE_POP := 3.0

var cards_total := 8
var card_seconds := 2.4
var two_conditions := false
var change_rule := false

var rule: Array[Cond] = []
var cards: Array[Card] = []
## План: какая по счёту карточка подходит под правило, поровну да и нет вперемешку.
var fit_plan: Array[bool] = []
var spawned := 0
var decided := 0
var errors := 0
var spawn_timer := 0.0
var rule_flash := 0.0
var rule_changed := false
var _bot_timer := 0.0
var _ok: AudioStreamPlayer
var _bad: AudioStreamPlayer
var _swap: AudioStreamPlayer
## Правило вспухает при смене: добавка к масштабу.
var _rule_pop := JellySpring.new()
## Мягкие брызги верного решения.
var _splash := SplashFx.new()


func _on_start() -> void:
	cards_total = maxi(int(round(def.param(&"cards", t, 8.0))), 4)
	card_seconds = def.param(&"card_seconds", t, 2.4)
	two_conditions = def.param(&"two", t, 0.0) >= 0.5
	change_rule = def.param(&"change", t, 0.0) >= 0.5
	_ok = Sfx.player(Sfx.blip(880.0, 0.08, 0.35, 30.0))
	_bad = Sfx.player(Sfx.thud(0.14, 0.5))
	_swap = Sfx.player(Sfx.blip(440.0, 0.15, 0.3, 14.0))
	for p in [_ok, _bad, _swap]:
		add_child(p)
	rule = _make_rule(-1)
	for i in cards_total:
		fit_plan.append(i % 2 == 0)
	fit_plan.shuffle()
	spawn_timer = 0.3
	queue_redraw()


# --- Правило и карточки ------------------------------------------------------------------------

## Семейство условия: 0 число, 1 цвет, 2 стороны; второе условие берётся из другого семейства.
static func _family(k: int) -> int:
	if k <= Kind.ODD:
		return 0
	return 1 if k == Kind.COLOR else 2


## Случайное условие; `avoid` вид, семейства которого не надо.
func _make_cond(avoid: int) -> Cond:
	var c := Cond.new()
	var kinds: Array[int] = [Kind.NUMBER_LE, Kind.NUMBER_GE, Kind.EVEN, Kind.ODD, Kind.COLOR]
	if t > SHAPES_FROM_T:
		kinds.append_array([Kind.SIDES_LE, Kind.SIDES_GE])
	if avoid >= 0:
		kinds = kinds.filter(func(k: int) -> bool: return _family(k) != _family(avoid))
	c.kind = kinds[rng.randi_range(0, kinds.size() - 1)] as Kind
	match c.kind:
		Kind.NUMBER_LE, Kind.NUMBER_GE:
			c.value = rng.randi_range(2, 5) * 10
		Kind.COLOR:
			c.value = rng.randi_range(0, COLORS.size() - 1)
		Kind.SIDES_LE:
			c.value = rng.randi_range(4, 6)
		Kind.SIDES_GE:
			c.value = rng.randi_range(5, 7)
	return c


func _make_rule(avoid_first: int) -> Array[Cond]:
	var out: Array[Cond] = []
	var first := _make_cond(avoid_first)
	out.append(first)
	if two_conditions:
		out.append(_make_cond(first.kind))
	return out


static func _passes(card: Card, cond: Cond) -> bool:
	match cond.kind:
		Kind.NUMBER_LE:
			return card.number <= cond.value
		Kind.NUMBER_GE:
			return card.number >= cond.value
		Kind.EVEN:
			return card.number % 2 == 0
		Kind.ODD:
			return card.number % 2 == 1
		Kind.COLOR:
			return card.color == cond.value
		Kind.SIDES_LE:
			return card.sides <= cond.value
		Kind.SIDES_GE:
			return card.sides >= cond.value
	return false


func _fits(card: Card) -> bool:
	for c in rule:
		if not _passes(card, c):
			return false
	return true


## Новая карточка по плану: подходит или нет решено заранее, поровну и вперемешку.
func _spawn() -> void:
	var c := Card.new()
	var want_fit: bool = fit_plan[spawned] if spawned < fit_plan.size() else rng.randf() < 0.5
	for attempt in 40:
		c.number = rng.randi_range(1, 60)
		c.color = rng.randi_range(0, COLORS.size() - 1)
		c.sides = rng.randi_range(3, 8)
		if _fits(c) == want_fit:
			break
	c.x = -CARD_W
	c.spawn_i = spawned
	spawned += 1
	cards.append(c)


# --- Ввод и шаг -----------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	if event.is_action_pressed(GameInput.UP):
		_decide(true)
	elif event.is_action_pressed(GameInput.DOWN) or event.is_action_pressed(GameInput.LEFT) or event.is_action_pressed(GameInput.RIGHT):
		_decide(false)
	else:
		return
	get_viewport().set_input_as_handled()


func _zone_x() -> float:
	return size.x / 2.0


## Карточка в зоне решения: доехала до центра и ещё не решена.
func _active() -> Card:
	for c in cards:
		if not c.decided and c.x >= _zone_x() - CARD_W / 2.0 - 0.5:
			return c
	return null


func _decide(accept: bool) -> void:
	var c := _active()
	if c == null:
		return
	c.decided = true
	c.accepted = accept
	c.correct = accept == _fits(c)
	c.age = 0.0
	decided += 1
	_jelly_decided(c)
	if c.correct:
		_ok.play()
	else:
		errors += 1
		_bad.play()
		if errors >= FAIL_AT:
			finish(false)
			return
	_after_decision()


func _after_decision() -> void:
	if change_rule and not rule_changed and decided >= cards_total / 2:
		rule_changed = true
		rule = _make_rule(rule[0].kind)
		rule_flash = RULE_FLASH
		_rule_pop.kick(RULE_POP)
		_swap.play()
	if decided >= cards_total:
		finish(errors < FAIL_AT)


func _on_tick(delta: float) -> void:
	rule_flash = maxf(rule_flash - delta, 0.0)
	var zone_left := _zone_x() - CARD_W / 2.0
	var enter_speed := (zone_left + CARD_W) / ENTER_SECONDS
	# Следующая карточка, когда предыдущая решена и улетела.
	var pending := false
	for c in cards:
		if not c.decided:
			pending = true
	if not pending and spawned < cards_total:
		spawn_timer -= delta
		if spawn_timer <= 0.0:
			_spawn()
			spawn_timer = GAP_SECONDS
	for c in cards:
		if c.decided:
			c.age += delta
			continue
		if c.x < zone_left:
			c.x = minf(c.x + enter_speed * delta, zone_left)
			continue
		c.wait += delta
		# Не дождалась решения: уезжает вправо, ошибка.
		if c.wait >= card_seconds:
			c.decided = true
			c.accepted = false
			c.correct = false
			c.age = 0.0
			decided += 1
			errors += 1
			_jelly_decided(c)
			_bad.play()
			if errors >= FAIL_AT:
				finish(false)
				return
			_after_decision()
			if not running:
				return
	while not cards.is_empty() and cards[0].decided and cards[0].age > FLY_SECONDS:
		cards.remove_at(0)
	queue_redraw()


func _on_timeout() -> bool:
	return errors < FAIL_AT and decided >= cards_total


## Бот: WIN отвечает по правилу, LOSE наоборот.
func _bot_step(delta: float) -> bool:
	var c := _active()
	if c == null:
		_bot_timer = 0.0
		return false
	_bot_timer += delta
	if _bot_timer < BOT_REACTION:
		return false
	_bot_timer = 0.0
	var fits := _fits(c)
	_decide(fits if AutoTest.bot_mode == AutoTest.BotMode.WIN else not fits)
	return false


# --- Мармелад ------------------------------------------------------------------------------

## Где карточка по игре: (центр x, y, непрозрачность, наклон). Решённая улетает вверх (принята)
## или вниз (отклонена), просроченная уезжает вправо, и все гаснут.
func _card_pose(c: Card) -> Vector4:
	var at := Vector2(c.x + CARD_W / 2.0, size.y * 0.52)
	if not c.decided:
		return Vector4(at.x, at.y, 1.0, 0.0)
	var k := clampf(c.age / FLY_SECONDS, 0.0, 1.0)
	var e := ease(k, 0.5)
	if c.correct or c.wait < card_seconds:
		var dir := -1.0 if c.accepted else 1.0
		return Vector4(at.x, at.y + dir * 260.0 * e, 1.0 - k, -dir * FLY_TILT * e)
	return Vector4(at.x + 520.0 * e, at.y, 1.0 - k, FLY_TILT * e)


## Решение: карточка вдавливается в бортик и сжимается; ошибка её ещё и встряхивает вбок,
## верное брызгает с верхнего края несколькими каплями цвета успеха.
func _jelly_decided(c: Card) -> void:
	c.lift.value = 0.0
	c.lift.velocity = 0.0
	if c.body == null:
		return
	if c.correct and Jelly.on():
		_splash.pop(Vector2(c.x + CARD_W / 2.0, size.y * 0.52 - CARD_H / 2.0), Style.SUCCESS, 6, 650.0, 0.55)
	c.body.poke(DECIDE_POKE)
	c.figure.poke(DECIDE_POKE * 0.6)
	if not c.correct:
		var side := 1.0 if c.spawn_i % 2 == 0 else -1.0
		c.body.push(Vector2(WRONG_PUSH * side, 0.0))
		c.figure.push(Vector2(-WRONG_PUSH * 0.6 * side, 0.0))


## Средняя точка контура: где тело на самом деле, с отставанием и качанием.
static func _shape_center(shape: JellyShape) -> Vector2:
	var sum := Vector2.ZERO
	for p in shape.blob.points:
		sum += p
	return sum / maxf(shape.blob.points.size(), 1.0)


## Вести фигуру к `at`; без движения мармелада (дебаг-меню) ставится на место.
static func _lead(shape: JellyShape, delta: float, at: Vector2, angle: float) -> void:
	# Тело садится вниз на долю радиуса: цель выше на столько же, контур стоит где игровая точка.
	var target := at - Vector2(0.0, Jelly.tuning().blob_sit * shape.blob.radius)
	if Jelly.on():
		shape.follow(delta, target, angle)
	else:
		shape.blob.angle = angle
		shape.snap(target)


## Мармелад живёт и после финиша, пока сцена на экране; на паузе стоит.
func _process(delta: float) -> void:
	super(delta)
	if paused or def == null:
		return
	var tu := Jelly.tuning()
	_rule_pop.step(delta, tu.spring_stiffness, tu.spring_damping)
	_splash.step(delta, Callable())
	var active := _active()
	for c in cards:
		if c.body == null:
			c.body = JellyShape.rect(Vector2(CARD_W, CARD_H), Style.R_CARD, CARD_POINTS)
			c.figure = JellyShape.polygon(c.sides, FIGURE_R)
			c.lift.value = BASE_LIFT
		# Доехала до зоны и встала: вздрагивает и поднимается на бортик.
		if c == active and not c.landed:
			c.landed = true
			c.body.poke(LAND_POKE)
			c.figure.poke(LAND_POKE * 0.6)
		if not c.decided:
			c.lift.step(delta, tu.spring_stiffness, tu.spring_damping, tu.lift_px if c == active else BASE_LIFT)
		var pose := _card_pose(c)
		_lead(c.body, delta, Vector2(pose.x, pose.y), pose.w)
		_lead(c.figure, delta, _shape_center(c.body), pose.w)
	if not running:
		queue_redraw()


# --- Рисование ----------------------------------------------------------------------------

func _draw() -> void:
	if def == null:
		return
	var font := get_theme_default_font()
	var mid := size.y * 0.52
	# Зона решения: серое гнездо без рамки, карточка встаёт в него на бортике.
	var zone := Rect2(_zone_x() - CARD_W / 2.0, mid - CARD_H / 2.0, CARD_W, CARD_H)
	Style.flat(Style.SURFACE_2, Style.R_CARD).draw(get_canvas_item(), zone)
	# Карточки.
	for c in cards:
		if c.body == null:
			continue
		var pose := _card_pose(c)
		var alpha := pose.z
		var lift := maxf(c.lift.value, 0.0)
		if not c.decided:
			# Полоска ожидания под бортиком карточки тает.
			var left := 1.0 - clampf(c.wait / card_seconds, 0.0, 1.0)
			draw_rect(Rect2(c.x, mid + CARD_H / 2.0 + 14.0 + lift, CARD_W * left, 6.0), Style.accent(0) if left > 0.3 else Style.DANGER)
		var card_color := Style.SURFACE_SOLID
		if c.decided:
			card_color = Style.SUCCESS if c.correct else Style.DANGER
		# Бортик вместо тени; у решённой его нет: вдавлена и гаснет.
		c.body.draw_lifted(self, Color(card_color, alpha), lift if not c.decided else 0.0)
		# Фигура по центру карточки, число внутри фигуры: едет и наклоняется с ней, не гнётся.
		c.figure.draw(self, Color(COLORS[c.color], alpha))
		var center := _shape_center(c.figure)
		var txt := str(c.number)
		var fs := 40
		var w := font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		draw_set_transform(center, pose.w)
		draw_string(font, Vector2(-w / 2.0, fs * 0.36 + (10.0 if c.sides == 3 else 0.0)), txt,
				HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(Style.SURFACE_SOLID, alpha))
		draw_set_transform_matrix(Transform2D.IDENTITY)
	_splash.draw_air(self, Vector2.ZERO)
	# Правило сверху словами, при смене вспухает.
	var pivot := Vector2(size.x / 2.0, 150.0)
	var pop := 1.0 + maxf(_rule_pop.value, -0.5)
	draw_set_transform(pivot * (1.0 - pop), 0.0, Vector2(pop, pop))
	_draw_rule(font)
	draw_set_transform_matrix(Transform2D.IDENTITY)
	# Ошибки крестиками справа сверху, карточки точками.
	var r := 7.0
	var gap := 28.0
	var ex := size.x - 48.0 - (FAIL_AT - 1) * gap
	for j in FAIL_AT:
		var col := Style.DANGER if j < errors else Style.SURFACE_2
		var px := ex + j * gap
		draw_line(Vector2(px - r + 1, 60.0 - r + 1), Vector2(px + r - 1, 60.0 + r - 1), col, 3.0, true)
		draw_line(Vector2(px - r + 1, 60.0 + r - 1), Vector2(px + r - 1, 60.0 - r + 1), col, 3.0, true)
	var dx := size.x - 48.0 - (cards_total - 1) * 20.0
	for j in cards_total:
		draw_circle(Vector2(dx + j * 20.0, 92.0), 5.0, Style.INK if j < decided else Style.SURFACE_2)


## Правило словами в ряд (плейтест 2026-11-11, #86): «чётное», «нечётное», цвет словом своего
## цвета, «≤ 30», «≥ 5 сторон»; два условия через «и». Не влезает в ширину поля: шрифт мельче.
## При смене правила вспышка цветом фокуса.
func _draw_rule(font: Font) -> void:
	var y := 150.0
	var ink := Style.INK if rule_flash <= 0.0 else Style.INK.lerp(Style.FOCUS, rule_flash / RULE_FLASH)
	var parts: Array[String] = []
	var colors: Array[Color] = []
	# Рядом со сторонами голое «≤ 20» читается как про стороны: тогда «число ≤ 20».
	var sides := rule.any(func(c: Cond) -> bool: return _family(c.kind) == 2)
	for i in rule.size():
		if i > 0:
			parts.append(" и ")
			colors.append(Style.INK_3)
		var text := _cond_text(rule[i])
		if sides and (rule[i].kind == Kind.NUMBER_LE or rule[i].kind == Kind.NUMBER_GE):
			text = "число " + text
		parts.append(text)
		colors.append(COLORS[rule[i].value] if rule[i].kind == Kind.COLOR else ink)
	var fs := RULE_FONT
	var total := 0.0
	while true:
		total = 0.0
		for part in parts:
			total += font.get_string_size(part, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		if total <= size.x - 2.0 * RULE_MARGIN or fs <= RULE_FONT_MIN:
			break
		fs -= 8
	var x := size.x / 2.0 - total / 2.0
	for i in parts.size():
		draw_string(font, Vector2(x, y + fs * 0.36), parts[i], HORIZONTAL_ALIGNMENT_LEFT, -1, fs, colors[i])
		x += font.get_string_size(parts[i], HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x


## Условие словами: так его читает игрок.
static func _cond_text(c: Cond) -> String:
	match c.kind:
		Kind.NUMBER_LE:
			return "≤ " + str(c.value)
		Kind.NUMBER_GE:
			return "≥ " + str(c.value)
		Kind.EVEN:
			return "чётное"
		Kind.ODD:
			return "нечётное"
		Kind.COLOR:
			return COLOR_NAMES[c.value]
		Kind.SIDES_LE:
			return "≤ %d сторон" % c.value
		Kind.SIDES_GE:
			return "≥ %d сторон" % c.value
	return ""
