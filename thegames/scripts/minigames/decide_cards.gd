extends Minigame
## «Реши» (decide_cards, баланс), каталог `docs/specs/minigames_catalog.md`. Карточки едут
## слева направо по одной, на каждой число, цвет и многоугольник. Правило вверху крупно и
## без слов, пиктограммой: «≤ 30», только такой цвет, «≤ 5 сторон». Карточка въезжает в зону
## решения по центру и ждёт там `card_seconds`: A принимает, B отклоняет; не дождалась, уезжает
## вправо, это ошибка. Две ошибки: провал.
## С `t` темп выше, карточек больше, правило из двух условий («красные и ≤ 30»), затем правило
## меняется посреди раунда. Параметры в `resources/minigames/decide_cards.tres`: cards,
## card_seconds, two (от 0.5 два условия), change (от 0.5 смена правила на середине).

enum Kind { NUMBER_LE, NUMBER_GE, COLOR, SIDES_LE, SIDES_GE }


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


const COLORS: Array[Color] = [Color("#E0457B"), Color("#2F5BFF"), Color("#2BB37A")]
const COLOR_NAMES: Array[String] = ["красные", "синие", "зелёные"]
const CARD_W := 220.0
const CARD_H := 280.0
const FAIL_AT := 2
const FLY_SECONDS := 0.5
const ENTER_SECONDS := 0.35
const GAP_SECONDS := 0.2
const RULE_FLASH := 0.5
const BOT_REACTION := 0.25

var cards_total := 8
var card_seconds := 2.4
var two_conditions := false
var change_rule := false

var rule: Array[Cond] = []
var cards: Array[Card] = []
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
	spawn_timer = 0.3
	queue_redraw()


# --- Правило и карточки ------------------------------------------------------------------------

## Случайное условие; `avoid` вид, которого не надо (второе условие другого вида).
func _make_cond(avoid: int) -> Cond:
	var c := Cond.new()
	var kinds: Array[int] = [Kind.NUMBER_LE, Kind.NUMBER_GE, Kind.COLOR, Kind.SIDES_LE, Kind.SIDES_GE]
	var family := func(k: int) -> int: return 0 if k <= Kind.NUMBER_GE else (1 if k == Kind.COLOR else 2)
	if avoid >= 0:
		kinds = kinds.filter(func(k: int) -> bool: return family.call(k) != family.call(avoid))
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


## Новая карточка: примерно половина подходит под правило, чтобы ответ не был очевиден.
func _spawn() -> void:
	var c := Card.new()
	var want_fit := rng.randf() < 0.5
	for attempt in 12:
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
	if GameInput.is_a(event):
		_decide(true)
	elif GameInput.is_b(event):
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


# --- Рисование ----------------------------------------------------------------------------

func _draw() -> void:
	if def == null:
		return
	var font := ThemeDB.fallback_font
	var mid := size.y * 0.52
	# Зона решения.
	var zone := Rect2(_zone_x() - CARD_W / 2.0, mid - CARD_H / 2.0, CARD_W, CARD_H)
	Style.focus_ring(Style.R_CARD).draw(get_canvas_item(), zone)
	# Карточки.
	for c in cards:
		var pos := Vector2(c.x, mid - CARD_H / 2.0)
		var alpha := 1.0
		if c.decided:
			var k := clampf(c.age / FLY_SECONDS, 0.0, 1.0)
			alpha = 1.0 - k
			# Решённая улетает вверх (принята) или вниз (отклонена), просроченная уезжает вправо.
			if c.correct or c.wait < card_seconds:
				pos += Vector2(0, (-1.0 if c.accepted else 1.0) * 260.0 * ease(k, 0.5))
			else:
				pos += Vector2(520.0 * ease(k, 0.5), 0)
		else:
			# Полоска ожидания под карточкой тает.
			var left := 1.0 - clampf(c.wait / card_seconds, 0.0, 1.0)
			draw_rect(Rect2(pos.x, pos.y + CARD_H + 14.0, CARD_W * left, 6.0), Style.accent(0) if left > 0.3 else Style.DANGER)
		var card_color := Style.SURFACE_SOLID
		if c.decided:
			card_color = Style.SUCCESS if c.correct else Style.DANGER
		var sb := Style.flat(Color(card_color, alpha), Style.R_CARD, Color.TRANSPARENT, 0)
		sb.shadow_color = Color(0, 0, 0, 0.08 * alpha)
		sb.shadow_size = 10
		sb.draw(get_canvas_item(), Rect2(pos, Vector2(CARD_W, CARD_H)))
		var center := pos + Vector2(CARD_W / 2.0, CARD_H / 2.0 - 20.0)
		_draw_polygon(center, 72.0, c.sides, Color(COLORS[c.color], alpha))
		var txt := str(c.number)
		var w := font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 44).x
		draw_string(font, Vector2(center.x - w / 2.0, pos.y + CARD_H - 28.0), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 44, Color(Style.INK, alpha))
	# Правило сверху пиктограммами.
	_draw_rule(font)
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


func _draw_polygon(center: Vector2, radius: float, sides: int, color: Color) -> void:
	var pts := PackedVector2Array()
	for i in sides:
		var a := -PI / 2.0 + TAU * i / sides
		pts.append(center + Vector2(cos(a), sin(a)) * radius)
	draw_colored_polygon(pts, color)


## Правило: условия пиктограммами в ряд, между двумя знак «+»; при смене вспышка цветом фокуса.
func _draw_rule(font: Font) -> void:
	var y := 150.0
	var ink := Style.INK if rule_flash <= 0.0 else Style.INK.lerp(Style.FOCUS, rule_flash / RULE_FLASH)
	var widths: Array[float] = []
	var total := 0.0
	for c in rule:
		var w := _cond_width(font, c)
		widths.append(w)
		total += w
	total += 64.0 * (rule.size() - 1)
	var x := size.x / 2.0 - total / 2.0
	for i in rule.size():
		_draw_cond(font, rule[i], Vector2(x, y), widths[i], ink)
		x += widths[i]
		if i < rule.size() - 1:
			var plus_w := font.get_string_size("+", HORIZONTAL_ALIGNMENT_LEFT, -1, 56).x
			draw_string(font, Vector2(x + 32.0 - plus_w / 2.0, y + 20.0), "+", HORIZONTAL_ALIGNMENT_LEFT, -1, 56, Style.INK_3)
			x += 64.0


func _cond_width(font: Font, c: Cond) -> float:
	match c.kind:
		Kind.COLOR:
			return 88.0
		Kind.SIDES_LE, Kind.SIDES_GE:
			return 88.0 + 16.0 + font.get_string_size(("≤ " if c.kind == Kind.SIDES_LE else "≥ ") + str(c.value), HORIZONTAL_ALIGNMENT_LEFT, -1, 56).x
	return font.get_string_size(("≤ " if c.kind == Kind.NUMBER_LE else "≥ ") + str(c.value), HORIZONTAL_ALIGNMENT_LEFT, -1, 72).x


func _draw_cond(font: Font, c: Cond, pos: Vector2, w: float, ink: Color) -> void:
	match c.kind:
		Kind.NUMBER_LE, Kind.NUMBER_GE:
			draw_string(font, pos + Vector2(0, 26.0), ("≤ " if c.kind == Kind.NUMBER_LE else "≥ ") + str(c.value), HORIZONTAL_ALIGNMENT_LEFT, -1, 72, ink)
		Kind.COLOR:
			draw_circle(pos + Vector2(44.0, 0.0), 40.0, COLORS[c.value])
		Kind.SIDES_LE, Kind.SIDES_GE:
			# Многоугольник с нужным числом сторон контуром и знак рядом.
			var pts := PackedVector2Array()
			for i in c.value:
				var a := -PI / 2.0 + TAU * i / c.value
				pts.append(pos + Vector2(44.0, 0.0) + Vector2(cos(a), sin(a)) * 40.0)
			pts.append(pts[0])
			draw_polyline(pts, ink, 5.0, true)
			draw_string(font, pos + Vector2(104.0, 20.0), ("≤ " if c.kind == Kind.SIDES_LE else "≥ ") + str(c.value), HORIZONTAL_ALIGNMENT_LEFT, -1, 56, ink)
