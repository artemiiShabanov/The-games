class_name StudioScreen
extends Control
## Экран фазы студии (#28), спека `docs/specs/studio.md`. В большой карточке `CardFrame`
## поверх студии: слева ведомость, строки появляются по одной (продажи первой недели нового
## релиза, тики хвостов, содержание, банкротство и аванс), деньги в пилюле над карточкой
## прокручиваются за каждой строкой; справа оценка студии; внизу «Что улучшим?» с карточками
## прокачки по правилу состава. Влево-вправо фокус, A купить, B и Esc отказ. Недоступное по
## деньгам красным с нехваткой, фокус на него встаёт, A трясёт карточку. Пул пуст: «студия
## укомплектована». Забег окончен банкротством: вместо предложения «студия закрывается», A
## дальше. Деньги уже посчитаны `StudioPhase.settle` до показа, экран лишь анимирует отчёт;
## покупка идёт через `StudioPhase.buy` по A.

signal offer_shown(options: Array[UpgradeDef])
signal upgrade_bought(upgrade: UpgradeDef)
signal offer_skipped
signal finished

const STEP_SECONDS := 0.4
const AFTER_BUY_SECONDS := 0.6
const BOT_PAUSE := 0.4
const LEDGER_WIDTH := 760
const VALUATION_WIDTH := 480
const OFFER_Y := 420
const OFFER_CARD := Vector2(520, 336)
const MAX_TAIL_ROWS := 4
const LIFT_PX := 6

var report: StudioPhase.Report
var wallet: Wallet
var upkeep: Upkeep
var state: StudioState
var economy: EconomyTuning
var index := 0
var ready_for_input := false
## Что куплено в этой фазе, null при отказе.
var bought: UpgradeDef

var card: CardFrame
var _money_label: Label
var _shown_money := 0.0
var _ledger: VBoxContainer
var _valuation_block: VBoxContainer
var _valuation_label: Label
var _offer_title: Label
var _offer_caption: Label
var _cards: Array[PanelContainer] = []
var _kind_pills: Array[PanelContainer] = []
var _kind_labels: Array[Label] = []
var _focus_ring: Panel
var _hints: Control
var _closing := false
var _bot_timer := 0.0


func setup(report_: StudioPhase.Report, wallet_: Wallet, upkeep_: Upkeep, state_: StudioState, economy_: EconomyTuning) -> void:
	report = report_
	wallet = wallet_
	upkeep = upkeep_
	state = state_
	economy = economy_


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()
	await card.raise_card()
	_run()


func offer() -> Array[UpgradeDef]:
	return report.offer


func affordable(i: int) -> bool:
	return i >= 0 and i < report.offer.size() and wallet.can_afford(report.offer[i].price(economy))


# --- Ввод ----------------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if event.is_echo() or not ready_for_input or _closing:
		return
	if event.is_action_pressed(GameInput.LEFT):
		move(-1)
	elif event.is_action_pressed(GameInput.RIGHT):
		move(1)
	elif GameInput.is_a(event):
		confirm()
	elif GameInput.is_b(event) or _is_escape(event):
		skip()
	else:
		return
	get_viewport().set_input_as_handled()


static func _is_escape(event: InputEvent) -> bool:
	var key := event as InputEventKey
	return key != null and key.pressed and not key.echo and key.keycode == KEY_ESCAPE


func move(dir: int) -> void:
	if report.offer.size() < 2:
		return
	var next := clampi(index + dir, 0, report.offer.size() - 1)
	if next == index:
		return
	index = next
	ShellSounds.play(&"tick")
	_refresh_focus(true)


## A: купить выбранное; без предложения просто дальше.
func confirm() -> void:
	if not ready_for_input or _closing:
		return
	if report.game_over or report.offer.is_empty():
		proceed()
		return
	var def := report.offer[index]
	if not StudioPhase.buy(def, wallet, upkeep, state, economy):
		_shake(_cards[index])
		ShellSounds.play(&"miss")
		return
	bought = def
	ShellSounds.play(&"done")
	upgrade_bought.emit(def)
	_mark_bought(index)
	_roll_money(wallet.cash)
	_refresh_prices()
	_close_after(AFTER_BUY_SECONDS)


## B или Esc: отказ бесплатен.
func skip() -> void:
	if not ready_for_input or _closing:
		return
	if report.game_over or report.offer.is_empty():
		proceed()
		return
	ShellSounds.play(&"tick")
	offer_skipped.emit()
	_close_after(0.0)


## Дальше без предложения: пул пуст или забег окончен.
func proceed() -> void:
	if not ready_for_input or _closing:
		return
	ShellSounds.play(&"done" if not report.game_over else &"bug")
	_close_after(0.0)


func _close_after(seconds: float) -> void:
	_closing = true
	if seconds > 0.0 and not Debug.skip_cards:
		await get_tree().create_timer(seconds).timeout
	await card.drop_card()
	finished.emit()


func _process(delta: float) -> void:
	if not AutoTest.bot_active() or not ready_for_input or _closing:
		return
	_bot_timer += delta
	if _bot_timer < BOT_PAUSE:
		return
	_bot_timer = -INF
	if report.game_over or report.offer.is_empty():
		proceed()
	elif AutoTest.bot_mode == AutoTest.BotMode.WIN:
		var pick := -1
		for i in report.offer.size():
			if affordable(i):
				pick = i
				break
		if pick < 0:
			skip()
		else:
			index = pick
			_refresh_focus(false)
			confirm()
	else:
		skip()


# --- Шаги фазы -----------------------------------------------------------------------------

func _run() -> void:
	_set_money(report.cash_start)
	await _step()
	var money := report.cash_start
	if report.current != null:
		money += report.first_week
		await _add_row("Первая неделя · %s" % report.current.title, report.first_week, Style.MONEY, money)
	var tails := report.tails.duplicate()
	tails.sort_custom(func(a: StudioPhase.Tail, b: StudioPhase.Tail) -> bool: return a.tick > b.tick)
	var shown := 0
	var rest := 0
	var rest_sum := 0
	for t in tails:
		if t.tick <= 0:
			continue
		if shown < MAX_TAIL_ROWS:
			shown += 1
			money += t.tick
			await _add_row("Хвост · %s" % t.record.title, t.tick, Style.MONEY, money)
		else:
			rest += 1
			rest_sum += t.tick
	if rest > 0:
		money += rest_sum
		await _add_row("Ещё хвостов: %d" % rest, rest_sum, Style.MONEY, money)
	money -= report.upkeep
	await _add_row("Содержание студии", -report.upkeep, Style.INK, money)
	if report.bankrupt:
		await _add_row("Меньше, чем дешёвый релиз (%s)" % Style.format_money(report.cheapest), 0, Style.DANGER, money)
		if report.rescue > 0:
			money += report.rescue
			await _add_row("Аванс издателя, второго не будет", report.rescue, Style.MONEY, money)
		elif report.game_over:
			await _add_row("Второго аванса нет: банкротство", 0, Style.DANGER, money)
	_fade_in(_valuation_block)
	_roll_label(_valuation_label, float(report.cash), float(report.stats.valuation if report.stats else report.cash))
	await _step()
	_show_offer()
	ready_for_input = true
	_fade_in(_hints)
	if not report.game_over:
		offer_shown.emit(report.offer)


func _step() -> void:
	if Debug.skip_cards:
		await get_tree().process_frame
	else:
		await get_tree().create_timer(STEP_SECONDS).timeout


## Строка ведомости: подпись слева, сумма справа моноширинным; деньги в шапке едут к `money`.
func _add_row(text: String, amount: int, color: Color, money: int) -> void:
	var row := HBoxContainer.new()
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var l := _label(text, Style.FONT_BODY, Style.INK if color != Style.DANGER else Style.DANGER)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	l.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	row.add_child(l)
	if amount != 0:
		var m := _label(("+ " if amount > 0 else "") + Style.format_money(amount), Style.FONT_BODY, color)
		m.add_theme_font_override("font", Style.mono_font())
		m.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		row.add_child(m)
	_ledger.add_child(row)
	_fade_in(row)
	if amount != 0:
		_roll_money(money)
	await _step()


func _show_offer() -> void:
	if report.game_over:
		_offer_title.text = "Студия закрывается"
		_offer_title.add_theme_color_override("font_color", Style.DANGER)
		_offer_caption.text = "Денег на самый дешёвый релиз нет, и издатель уже помогал. Забег окончен."
		_fade_in(_offer_title)
		_fade_in(_offer_caption)
		_hints.add_child(HintPill.make("A дальше"))
		return
	if report.offer.is_empty():
		_offer_title.text = "Студия укомплектована"
		_offer_caption.text = "Всё, что можно было купить, уже куплено."
		_fade_in(_offer_title)
		_fade_in(_offer_caption)
		_hints.add_child(HintPill.make("A дальше"))
		return
	_offer_title.text = "Что улучшим?"
	_fade_in(_offer_title)
	index = 0
	for i in report.offer.size():
		if affordable(i):
			index = i
			break
	for i in _cards.size():
		_fade_in(_cards[i], i * 0.08)
	_refresh_prices()
	_refresh_focus(false)
	_hints.add_child(HintPill.make("← → выбрать"))
	_hints.add_child(HintPill.make("A купить"))
	_hints.add_child(HintPill.make("B пропустить"))


# --- Построение ---------------------------------------------------------------------------------

func _build() -> void:
	var header := HintPill.header("Релиз %d · Студия" % report.release)
	header.position = Vector2(Style.EDGE, Style.HEADER_Y - Style.PILL_HEIGHT / 2.0)
	add_child(header)
	var right := HBoxContainer.new()
	right.alignment = BoxContainer.ALIGNMENT_END
	right.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	right.offset_left = Style.EDGE
	right.offset_right = -Style.EDGE
	right.offset_top = Style.HEADER_Y - Style.PILL_HEIGHT / 2.0
	right.offset_bottom = right.offset_top + Style.PILL_HEIGHT
	right.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(right)
	var money := HintPill.header(Style.format_money(report.cash_start))
	_money_label = money.get_child(0) as Label
	_money_label.add_theme_font_override("font", Style.mono_font())
	_money_label.add_theme_color_override("font_color", Style.MONEY)
	right.add_child(money)

	card = CardFrame.new()
	add_child(card)
	var inner := CardFrame.inner_size()
	var content := card.content

	_ledger = VBoxContainer.new()
	_ledger.position = Vector2.ZERO
	_ledger.size = Vector2(LEDGER_WIDTH, OFFER_Y - 24)
	_ledger.add_theme_constant_override("separation", 2)
	_ledger.mouse_filter = Control.MOUSE_FILTER_IGNORE
	content.add_child(_ledger)
	_ledger.add_child(_label("Итоги релиза", Style.FONT_H2, Style.INK))
	_ledger.add_child(_spacer(8))

	_valuation_block = VBoxContainer.new()
	_valuation_block.position = Vector2(inner.x - VALUATION_WIDTH, 0)
	_valuation_block.size = Vector2(VALUATION_WIDTH, 160)
	_valuation_block.add_theme_constant_override("separation", 4)
	_valuation_block.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_valuation_block.modulate.a = 0.0
	content.add_child(_valuation_block)
	var vc := _label("Оценка студии", Style.FONT_CAPTION, Style.INK_2)
	vc.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_valuation_block.add_child(vc)
	_valuation_label = _label(Style.format_money(report.cash), Style.FONT_H1, Style.INK)
	_valuation_label.add_theme_font_override("font", Style.mono_font())
	_valuation_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_valuation_block.add_child(_valuation_label)
	var vd := _label("деньги, хвосты, репутация, франшизы", Style.FONT_CAPTION, Style.INK_2)
	vd.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_valuation_block.add_child(vd)

	_offer_title = _label("", Style.FONT_H2, Style.INK)
	_offer_title.position = Vector2(0, OFFER_Y)
	_offer_title.size = Vector2(inner.x, 44)
	_offer_title.modulate.a = 0.0
	content.add_child(_offer_title)
	_offer_caption = _label("", Style.FONT_BODY, Style.INK_2)
	_offer_caption.position = Vector2(0, OFFER_Y + 52)
	_offer_caption.size = Vector2(inner.x, 40)
	_offer_caption.modulate.a = 0.0
	content.add_child(_offer_caption)

	_focus_ring = Panel.new()
	_focus_ring.add_theme_stylebox_override("panel", Style.focus_ring(Style.R_CARD))
	_focus_ring.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_focus_ring.visible = false
	content.add_child(_focus_ring)
	var n := report.offer.size()
	var row_width := n * OFFER_CARD.x + maxi(n - 1, 0) * Style.GAP_CARDS
	var x0 := (inner.x - row_width) / 2.0
	for i in n:
		var c := _make_card(report.offer[i])
		c.position = Vector2(x0 + i * (OFFER_CARD.x + Style.GAP_CARDS), OFFER_Y + 64)
		c.modulate.a = 0.0
		content.add_child(c)
		_cards.append(c)

	_hints = HBoxContainer.new()
	(_hints as HBoxContainer).alignment = BoxContainer.ALIGNMENT_CENTER
	_hints.add_theme_constant_override("separation", 16)
	_hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	_hints.offset_top = -(Style.PILL_HEIGHT + 16)
	_hints.offset_bottom = -16
	_hints.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hints.modulate.a = 0.0
	add_child(_hints)


## Карточка прокачки: вид пилюлей, название, строка эффекта, цена и надбавка к содержанию.
func _make_card(def: UpgradeDef) -> PanelContainer:
	var c := PanelContainer.new()
	c.add_theme_stylebox_override("panel", Style.card(true))
	c.custom_minimum_size = OFFER_CARD
	c.size = OFFER_CARD
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 10)
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.add_child(column)
	var pill_row := HBoxContainer.new()
	pill_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(pill_row)
	var pill := PanelContainer.new()
	pill.add_theme_stylebox_override("panel", _pill_style(Style.SURFACE_2))
	pill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var pl := _label(def.kind_name(), Style.FONT_CAPTION, Style.INK_2)
	pill.add_child(pl)
	pill_row.add_child(pill)
	_kind_pills.append(pill)
	_kind_labels.append(pl)
	column.add_child(_label(def.title, Style.FONT_H2, Style.INK))
	var effect := _label(def.effect_line, Style.FONT_BODY, Style.INK_2)
	effect.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	effect.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(effect)
	var price := _label(Style.format_money(def.price(economy)), Style.FONT_H2, Style.INK)
	price.add_theme_font_override("font", Style.mono_font())
	price.name = "Price"
	column.add_child(price)
	var note := _label("", Style.FONT_CAPTION, Style.INK_2)
	note.name = "Note"
	column.add_child(note)
	return c


func _pill_style(color: Color) -> StyleBoxFlat:
	var sb := Style.flat(color, Style.R_PILL, Color.TRANSPARENT, 0)
	sb.content_margin_left = 14
	sb.content_margin_right = 14
	sb.content_margin_top = 4
	sb.content_margin_bottom = 4
	return sb


## Цена и подпись: доступно «+ надбавка к содержанию», иначе `danger` с нехваткой.
func _refresh_prices() -> void:
	for i in _cards.size():
		var def := report.offer[i]
		var price := _cards[i].find_child("Price", true, false) as Label
		var note := _cards[i].find_child("Note", true, false) as Label
		var ok := affordable(i) or def == bought
		price.add_theme_color_override("font_color", Style.INK if ok else Style.DANGER)
		if ok:
			note.text = "+ %s к содержанию за релиз" % Style.format_money(def.upkeep(economy))
			note.add_theme_color_override("font_color", Style.INK_2)
		else:
			note.text = "не хватает %s" % Style.format_money(def.price(economy) - wallet.cash)
			note.add_theme_color_override("font_color", Style.DANGER)


func _mark_bought(i: int) -> void:
	_kind_pills[i].add_theme_stylebox_override("panel", _pill_style(Style.SUCCESS))
	_kind_labels[i].text = "куплено"
	_kind_labels[i].add_theme_color_override("font_color", Style.SURFACE_SOLID)


func _refresh_focus(animate: bool) -> void:
	for i in _cards.size():
		var y := OFFER_Y + 64 - (LIFT_PX if i == index else 0)
		_animate(_cards[i], "position:y", float(y), animate)
	if _cards.is_empty():
		_focus_ring.visible = false
		return
	var c := _cards[index]
	var rect := Rect2(Vector2(c.position.x, OFFER_Y + 64 - LIFT_PX), OFFER_CARD)
	var was := _focus_ring.visible
	_focus_ring.visible = true
	_animate(_focus_ring, "position", rect.position, animate and was)
	_animate(_focus_ring, "size", rect.size, animate and was)


# --- Анимации -----------------------------------------------------------------------------------

func _set_money(v: int) -> void:
	_shown_money = float(v)
	_money_label.text = Style.format_money(v)


func _roll_money(to: int) -> void:
	if Debug.skip_cards or is_equal_approx(_shown_money, float(to)):
		_set_money(to)
		return
	var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_method(func(v: float) -> void:
		_shown_money = v
		_money_label.text = Style.format_money(int(round(v))), _shown_money, float(to), Style.SWITCH_SECONDS)


func _roll_label(label: Label, from: float, to: float) -> void:
	if Debug.skip_cards or is_equal_approx(from, to):
		label.text = Style.format_money(int(round(to)))
		return
	var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_method(func(v: float) -> void:
		label.text = Style.format_money(int(round(v))), from, to, Style.SWITCH_SECONDS)


func _fade_in(node: CanvasItem, delay := 0.0) -> void:
	if Debug.skip_cards:
		node.modulate.a = 1.0
		return
	node.modulate.a = 0.0
	var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	if delay > 0.0:
		tw.tween_interval(delay)
	tw.tween_property(node, "modulate:a", 1.0, Style.SWITCH_SECONDS)


func _animate(node: Object, prop: String, value: Variant, animate: bool) -> void:
	if animate and not Debug.skip_cards:
		create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC).tween_property(node, prop, value, Style.FOCUS_MOVE_SECONDS)
	else:
		node.set_indexed(prop, value)


func _shake(node: Control) -> void:
	var x0 := node.position.x
	var tw := create_tween()
	for i in range(4):
		tw.tween_property(node, "position:x", x0 + Style.SHAKE_PX * (1 if i % 2 == 0 else -1), 0.04)
	tw.tween_property(node, "position:x", x0, 0.04)


func _label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _spacer(h: int) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(0, h)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c
