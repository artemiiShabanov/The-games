class_name RunHub
extends Control
## Главный экран забега (плейтест 2026-11-11, #77 и #78), спека `docs/specs/run.md`. Между
## релизами игрок стоит здесь, новый релиз начинается кнопкой «Новая игра», а не сам. Фоном
## студия (её рисует хозяин под экраном), поверх только хром: слева сверху логотип и название,
## под ними пилюли денег и «Прокачка» (и «Прокачаться», если от предложения фазы студии
## отказались), справа столбик карточек релизов, снизу по центру «Новая игра» (плейтест
## 2026-11-11: деньги и прокачка слева, релизы справа).
## - Пилюля денег раскрывает мармеладом окно с историей денег по релизам (`Wallet.history`).
## - «Прокачка» раскрывает окно купленной прокачки по порядку покупки с цветом вида (#79).
## - «Прокачаться» раскрывает отложенное предложение прокачки (`RunState.pending_offer`): одна
##   покупка до старта новой игры, с тем же запасом на следующий релиз, что и в фазе студии.
## - Карточка релиза выдвигает слева на полэкрана ленту этого релиза (`FeedScreen` архивом)
##   с «Играть демку»; демка идёт на весь экран, по её концу панель снова на месте.
## После релиза (#133, `setup_after`): тот же экран, но вместо «Новой игры» кнопка «Итоги
## релиза», а слева под пилюлями столбик карточек отклика. Отклик приходит волнами с небольшим
## перерывом: твиты, стример, критики, продажи; карточка волны открывает ленту релиза с тем, что
## уже пришло. Первой стоит карточка ставки: до прихода критиков можно угадать их оценку
## (`RunTuning.bet_*`). Кнопка внизу, пока волны идут, показывает всё сразу, потом ведёт к
## итогам (`after_finished`). Клик по предмету в студии это второй вход в те же действия:
## хозяин зовёт `open_wave`, `open_offer`, `open_record`.
## Стрелки ходят по экрану (`FocusNav`), наведение мыши переносит фокус, ␣ или клик нажимают,
## колесо и тачпад листают релизы и окна. Esc, Ctrl или клик мимо закрывают окно; без окна Esc
## уходит хозяину (пауза).

signal new_game
signal upgrade_bought(upgrade: UpgradeDef)
## Окно или панель релиза открылись (`true`) или закрылись: хозяин притеняет студию под ними.
signal overlay_changed(on: bool)
## После релиза (#133): пришла волна отклика; ставка на критиков сыграла или нет; игрок
## досмотрел и идёт к итогам релиза.
signal wave_arrived(kind: Wave)
signal bet_resolved(won: bool)
signal after_finished

const RELEASE_CARD := Vector2(400, 116)
const RELEASES_TOP := 12.0
const RELEASES_BOTTOM := 120.0
## Ряд пилюль денег и прокачки под названием студии.
const PILLS_Y := 104.0
const STRIPE := 6.0
const WINDOW_WIDTH := 640.0
const WINDOW_TOP := 176.0
const WINDOW_MAX_HEIGHT := 760.0
const NEW_GAME_SIZE := Vector2(520, 88)
const NEW_GAME_BOTTOM := 104.0
const POP_SECONDS := 0.36
const ROW_GAP := 12
## «Прокачаться»: цвет и как часто кнопка зовёт к себе.
const OFFER_COLOR := Color("#2BB37A")
const OFFER_PULSE_SECONDS := 2.4

enum Pop { NONE, MONEY, UPGRADES, RELEASE, OFFER, BET }
## Волны отклика после релиза по порядку прихода; ставка стоит первой и не приходит.
enum Wave { BET, TWEETS, STREAM, CRITICS, SALES }

const WAVE_CARD := Vector2(400, 96)
const WAVES_TOP := 196.0
const WAVE_NAMES: Array[String] = ["Ставка", "Твиты", "Стрим", "Критики", "Первая неделя"]
const BET_NAMES: Array[String] = ["Разнесут", "Сойдёт", "Полюбят"]
## Как вышло на деле, теми же тремя ступенями.
const VERDICTS: Array[String] = ["разнесли", "сойдёт", "полюбили"]

## Подписи строк истории денег по причине `Wallet`.
const REASONS := {
	"release": "Разработка", "bugfix": "Багфикс", "sales": "Первая неделя", "tail": "Хвосты",
	"share": "Доли по договорам", "upkeep": "Содержание", "upgrade": "Прокачка", "event": "Вставка",
	"bet": "Ставка на критиков",
	"rescue": "Аванс издателя",
}

var run: RunState
var focus := 0
var window := Pop.NONE
var playing := false

var _focusables: Array[Control] = []
var _lifts: Array[JellyLift] = []
var _labels: Array[Label] = []
var _release_count := 0
var _new_index := 0
var _upgrades_index := 0
var _money_index := 0
var _offer_index := -1
var _offer_rows: Array[PanelContainer] = []
var _offer_lifts: Array[JellyLift] = []
var _offer_defs: Array[UpgradeDef] = []
var _offer_focus := 0
var _offer_halo: Panel
var _pills: HBoxContainer
var _chrome: Control
var _hints: HBoxContainer
var _releases_scroll: ScrollContainer
var _window_node: PanelContainer
var _window_scroll: ScrollContainer
var _feed: FeedScreen
var _feed_record: GameRecord
var _demo: Demo
var _catalogs: Array[Catalog] = []
## После релиза (#133): запись и лента свежего релиза, волны, которые ещё придут, и пришедшие.
var after := false
var after_record: GameRecord
var after_content: FeedContent
var _wave_plan: Array[Wave] = []
var _waves_shown: Array[Wave] = []
var _wave_timer := 0.0
var _wave_focus: Dictionary[int, Wave] = {}
var _wave_nodes: Dictionary[Wave, PanelContainer] = {}
var _bet_rows: Array[PanelContainer] = []
var _bet_lifts: Array[JellyLift] = []
var _bet_focus := 1


func setup(run_: RunState) -> void:
	run = run_


## Главный экран после релиза: `record` только что вышла, `content` её лента.
func setup_after(run_: RunState, record: GameRecord, content: FeedContent) -> void:
	run = run_
	after = true
	after_record = record
	after_content = content
	var plan: Array[Wave] = [Wave.TWEETS]
	if content.clip_person != null:
		plan.append(Wave.STREAM)
	plan.append_array([Wave.CRITICS, Wave.SALES])
	if record.bet_done:
		# Слот продолжен после критиков: всё уже видели.
		_waves_shown = plan
		if record.bet >= 0:
			_waves_shown.insert(0, Wave.BET)
	else:
		_waves_shown = [Wave.BET]
		_wave_plan = plan
		_wave_timer = run.tuning.after_first_seconds


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	for k in 3:
		_catalogs.append(Catalog.load_kind(k))
	_build()
	_refresh_focus()
	if not Debug.skip_cards:
		_chrome.modulate.a = 0.0
		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_property(_chrome, "modulate:a", 1.0, Style.SWITCH_SECONDS)


# --- Действия ----------------------------------------------------------------------------------

## «Новая игра»: хозяин ведёт к основе или конструктору.
func start_new_game() -> void:
	if playing:
		return
	_close_window(false)
	_lifts[_new_index].press()
	if after and not _wave_plan.is_empty():
		show_all_waves()
		return
	ShellSounds.play(&"done")
	if after:
		after_finished.emit()
	else:
		new_game.emit()


## После релиза: все оставшиеся волны сразу.
func show_all_waves() -> void:
	if _wave_plan.is_empty():
		return
	ShellSounds.play(&"intro")
	while not _wave_plan.is_empty():
		_arrive(_wave_plan.pop_front(), false)
	_rebuild_keeping_focus()


## После релиза: досмотреть всё и идти к итогам (бот и пропуск).
func finish_after() -> void:
	show_all_waves()
	after_finished.emit()


func waves_left() -> int:
	return _wave_plan.size()


func _process(delta: float) -> void:
	if not after or _wave_plan.is_empty() or window != Pop.NONE or playing or get_tree().paused:
		return
	_wave_timer -= delta
	if _wave_timer > 0.0:
		return
	_wave_timer = run.tuning.after_gap_seconds
	var kind: Wave = _wave_plan.pop_front()
	_arrive(kind, true)
	_rebuild_keeping_focus(kind)


## Волна пришла. С критиками закрывается ставка: сыграла или нет, либо карточка уходит.
func _arrive(kind: Wave, sound: bool) -> void:
	_waves_shown.append(kind)
	if sound:
		ShellSounds.play(&"intro")
	if kind == Wave.CRITICS:
		after_record.bet_done = true
		if after_record.bet < 0:
			_waves_shown.erase(Wave.BET)
		else:
			bet_resolved.emit(bet_won())
	wave_arrived.emit(kind)


## Какой исход ставки соответствует оценке критиков: 0 разнесут, 1 сойдёт, 2 полюбят.
func bet_class() -> int:
	var avg := after_content.critics_avg
	if avg < run.tuning.bet_low:
		return 0
	return 2 if avg >= run.tuning.bet_high else 1


func bet_won() -> bool:
	return after_record.bet >= 0 and after_record.bet == bet_class()


## Сделать ставку: до прихода критиков, один раз.
func place_bet(choice: int) -> bool:
	if not after or after_record.bet_done or after_record.bet >= 0 or choice < 0 or choice > 2:
		ShellSounds.play(&"miss")
		return false
	after_record.bet = choice
	ShellSounds.play(&"done")
	_close_window(false)
	_rebuild_keeping_focus()
	return true


## Открыть волну: ставка окном, остальные лентой релиза с тем, что уже пришло.
func open_wave(kind: Wave) -> void:
	if not after or not _waves_shown.has(kind) or playing:
		return
	if kind == Wave.BET:
		if after_record.bet < 0 and not after_record.bet_done:
			_toggle_window(Pop.BET)
		elif _wave_nodes.has(kind):
			Jelly.poke(_wave_nodes[kind], 1.0)
		return
	var kinds: Array = []
	var first := -1
	var want: FeedContent.Kind = FeedContent.Kind.TWEET
	for w in _waves_shown:
		match w:
			Wave.TWEETS:
				kinds.append(FeedContent.Kind.TWEET)
			Wave.STREAM:
				kinds.append(FeedContent.Kind.CLIP)
			Wave.CRITICS:
				kinds.append(FeedContent.Kind.CRITIC)
			Wave.SALES:
				kinds.append(FeedContent.Kind.NUMBERS)
	match kind:
		Wave.STREAM:
			want = FeedContent.Kind.CLIP
		Wave.CRITICS:
			want = FeedContent.Kind.CRITIC
		Wave.SALES:
			want = FeedContent.Kind.NUMBERS
	var content := after_content.only(kinds)
	for i in content.items.size():
		if content.items[i].kind == want:
			first = i
			break
	_open_feed(after_record, content, first)


func activate(i: int) -> void:
	focus = i
	_refresh_focus()
	if i < _release_count:
		_open_release(i)
	elif i == _new_index:
		start_new_game()
	elif i == _upgrades_index:
		_toggle_window(Pop.UPGRADES)
	elif i == _money_index:
		_toggle_window(Pop.MONEY)
	elif i == _offer_index:
		_toggle_window(Pop.OFFER)
	elif _wave_focus.has(i):
		_lifts[i].press()
		open_wave(_wave_focus[i])


func open_money() -> void:
	_toggle_window(Pop.MONEY)


func open_upgrades() -> void:
	_toggle_window(Pop.UPGRADES)


func open_offer() -> void:
	if _offer_index >= 0:
		_toggle_window(Pop.OFFER)


## Купить пункт отложенного предложения: тот же запас на следующий релиз, что в фазе студии.
## Куплено: предложение сгорает, хром перестраивается с новыми деньгами и счётчиком.
func buy_offer(i: int) -> bool:
	if i < 0 or i >= _offer_defs.size():
		return false
	var def := _offer_defs[i]
	_offer_lifts[i].press()
	if not _offer_affordable(i) or not StudioPhase.buy(def, run.wallet, run.upkeep, run.studio, run.economy):
		_shake(_offer_rows[i])
		ShellSounds.play(&"miss")
		return false
	ShellSounds.play(&"done")
	run.pending_offer.clear()
	upgrade_bought.emit(def)
	_close_window(false)
	_rebuild()
	focus = _upgrades_index
	_refresh_focus()
	Jelly.poke(_focusables[_upgrades_index], 1.2)
	return true


func _offer_affordable(i: int) -> bool:
	return run.wallet.can_afford(_offer_defs[i].price(run.economy) + run.cheapest_next())


func open_release(i: int) -> void:
	_open_release(i)


## Релиз по номеру в забеге с нуля (коробка на полке студии, #133).
func open_record(index: int) -> void:
	if index >= 0 and index < run.records.size() and not playing:
		_open_release(run.records.size() - 1 - index)


# --- Ввод -------------------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if playing:
		return
	var viewport := get_viewport()
	if window == Pop.RELEASE:
		# Лента-архив разбирает ввод сама; сюда доходит клик мимо неё.
		if MouseUi.is_click(event) and _feed != null and not FeedScreen.archive_rect().has_point((event as InputEventMouse).position):
			_close_window()
			MouseUi.consume(viewport)
		return
	if window != Pop.NONE:
		_window_input(event, viewport)
		return
	if MouseUi.is_motion(event):
		var over := _focus_at(event)
		if over >= 0 and over != focus:
			focus = over
			ShellSounds.play(&"tick")
			_refresh_focus()
		return
	var px := MouseUi.scroll_px(event)
	if px != 0.0:
		_releases_scroll.scroll_vertical += int(px)
		MouseUi.consume(viewport)
		return
	if MouseUi.is_click(event):
		var at := _focus_at(event)
		if at >= 0:
			activate(at)
			MouseUi.consume(viewport)
		return
	var dir := FocusNav.dir_of(event)
	if dir != Vector2.ZERO:
		var next := FocusNav.step(_focus_rects(), focus, dir)
		if next != focus:
			focus = next
			ShellSounds.play(&"tick")
			_refresh_focus()
			_scroll_to_focus()
		MouseUi.consume(viewport)
	elif not event.is_echo() and GameInput.is_a(event):
		activate(focus)
		MouseUi.consume(viewport)


func _window_input(event: InputEvent, viewport: Viewport) -> void:
	if window == Pop.BET and _bet_input(event):
		MouseUi.consume(viewport)
		return
	var key := event as InputEventKey
	var esc := key != null and key.pressed and not key.echo and key.keycode == KEY_ESCAPE
	var px := MouseUi.scroll_px(event)
	if px != 0.0:
		_window_scroll.scroll_vertical += int(px)
	elif MouseUi.is_click(event):
		var inside := MouseUi.hit(_window_node, event)
		var on_pill := _pill_at(event)
		if window == Pop.OFFER and inside:
			var row := _offer_row_at(event)
			if row >= 0:
				_offer_focus = row
				_refresh_offer()
				buy_offer(row)
		elif on_pill >= 0:
			activate(on_pill)
		elif not inside:
			_close_window()
	elif window == Pop.OFFER and MouseUi.is_motion(event):
		var row := _offer_row_at(event)
		if row >= 0 and row != _offer_focus:
			_offer_focus = row
			ShellSounds.play(&"tick")
			_refresh_offer()
		return
	elif window == Pop.OFFER and not event.is_echo() and GameInput.is_a(event):
		buy_offer(_offer_focus)
	elif window == Pop.OFFER and (event.is_action_pressed(GameInput.DOWN, true) or event.is_action_pressed(GameInput.UP, true)):
		var next := clampi(_offer_focus + (1 if event.is_action_pressed(GameInput.DOWN, true) else -1), 0, _offer_rows.size() - 1)
		if next != _offer_focus:
			_offer_focus = next
			ShellSounds.play(&"tick")
			_refresh_offer()
	elif esc or GameInput.is_b(event) or (not event.is_echo() and GameInput.is_a(event)):
		_close_window()
	elif event.is_action_pressed(GameInput.DOWN, true):
		_window_scroll.scroll_vertical += 96
	elif event.is_action_pressed(GameInput.UP, true):
		_window_scroll.scroll_vertical -= 96
	elif MouseUi.is_motion(event):
		return
	else:
		return
	MouseUi.consume(viewport)


## Окно ставки: ↑ ↓ или наведение выбирают, ␣ или клик по строке ставят. Правда: событие съедено.
func _bet_input(event: InputEvent) -> bool:
	var over := -1
	for i in _bet_rows.size():
		if MouseUi.hit(_bet_rows[i], event):
			over = i
	if MouseUi.is_motion(event):
		if over >= 0 and over != _bet_focus:
			_bet_focus = over
			ShellSounds.play(&"tick")
			_refresh_bet()
		return false
	if MouseUi.is_click(event):
		if over < 0:
			return false
		_bet_lifts[over].press()
		place_bet(over)
		return true
	if not event.is_echo() and GameInput.is_a(event):
		_bet_lifts[_bet_focus].press()
		place_bet(_bet_focus)
		return true
	var step := int(event.is_action_pressed(GameInput.DOWN, true)) - int(event.is_action_pressed(GameInput.UP, true))
	if step != 0:
		var next := clampi(_bet_focus + step, 0, _bet_rows.size() - 1)
		if next != _bet_focus:
			_bet_focus = next
			ShellSounds.play(&"tick")
			_refresh_bet()
		return true
	return false


## Пилюля шапки под курсором (деньги, прокачка, «Прокачаться»), или -1.
func _pill_at(event: InputEvent) -> int:
	for i in [_money_index, _upgrades_index, _offer_index]:
		if i >= 0 and MouseUi.hit(_focusables[i], event):
			return i
	return -1


func _offer_row_at(event: InputEvent) -> int:
	for i in _offer_rows.size():
		if MouseUi.hit(_offer_rows[i], event):
			return i
	return -1


func _focus_rects() -> Array[Rect2]:
	var rects: Array[Rect2] = []
	for c in _focusables:
		rects.append(MouseUi.rect_of(c))
	return rects


func _focus_at(event: InputEvent) -> int:
	var m := event as InputEventMouse
	if m == null:
		return -1
	for i in _focusables.size():
		var c := _focusables[i]
		if not c.is_visible_in_tree():
			continue
		if i < _release_count and not MouseUi.rect_of(_releases_scroll).has_point(m.position):
			continue
		if MouseUi.rect_of(c).has_point(m.position):
			return i
	return -1


func _scroll_to_focus() -> void:
	if focus < _release_count:
		_releases_scroll.ensure_control_visible(_focusables[focus])


# --- Окна --------------------------------------------------------------------------------------

func _toggle_window(w: Pop) -> void:
	if window == w:
		_close_window()
		return
	_close_window(false)
	window = w
	overlay_changed.emit(true)
	ShellSounds.play(&"intro")
	var pill := _focusables[_money_index]
	var rows: Array[Control] = []
	var title := "Деньги"
	match w:
		Pop.MONEY:
			rows = _money_rows()
		Pop.UPGRADES:
			pill = _focusables[_upgrades_index]
			rows = _upgrade_rows()
			title = "Прокачка студии"
		Pop.OFFER:
			pill = _focusables[_offer_index]
			rows = _offer_window_rows()
			title = "Предложение ещё в силе"
		Pop.BET:
			rows = _bet_window_rows()
			title = "Что скажут критики?"
	_window_node = _make_window(rows, title)
	add_child(_window_node)
	if w == Pop.OFFER:
		_refresh_offer()
	elif w == Pop.BET:
		_refresh_bet()
	# Окно раскрывается из своей пилюли: левый верхний угол под ней.
	var pr := MouseUi.rect_of(pill)
	_window_node.position = Vector2(Style.EDGE, WINDOW_TOP)
	_window_node.pivot_offset = Vector2(pr.get_center().x - _window_node.position.x, 0.0)
	if not Debug.skip_cards:
		_window_node.scale = Vector2(0.6, 0.2)
		_window_node.modulate.a = 0.0
		var tw := create_tween().set_parallel(true).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)
		tw.tween_property(_window_node, "scale", Vector2.ONE, POP_SECONDS)
		tw.tween_property(_window_node, "modulate:a", 1.0, POP_SECONDS * 0.5)


func _close_window(sound := true) -> void:
	if window == Pop.NONE:
		return
	if sound:
		ShellSounds.play(&"tick")
	if window == Pop.RELEASE:
		var f := _feed
		_feed = null
		_feed_record = null
		if f != null:
			if Debug.skip_cards:
				f.queue_free()
			else:
				f.card.drop_card()
				get_tree().create_timer(Style.CARD_DROP_SECONDS + 0.05).timeout.connect(f.queue_free)
	elif _window_node != null:
		var w := _window_node
		_window_node = null
		_window_scroll = null
		_offer_rows.clear()
		_offer_lifts.clear()
		_bet_rows.clear()
		_bet_lifts.clear()
		if Debug.skip_cards:
			w.queue_free()
		else:
			var tw := create_tween().set_parallel(true).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_CUBIC)
			tw.tween_property(w, "scale", Vector2(0.8, 0.4), POP_SECONDS * 0.5)
			tw.tween_property(w, "modulate:a", 0.0, POP_SECONDS * 0.5)
			tw.chain().tween_callback(w.queue_free)
	window = Pop.NONE
	overlay_changed.emit(false)
	_set_new_game_shown(true)


## Панель релиза закрывает левую половину: пилюли, «Новая игра» и подсказки уходят из-под неё.
func _set_new_game_shown(on: bool) -> void:
	for c: Control in [_focusables[_new_index], _hints, _pills]:
		var tw := create_tween()
		tw.tween_property(c, "modulate:a", 1.0 if on else 0.0, Style.SWITCH_SECONDS if not Debug.skip_cards else 0.0)


## Окно справа сверху: заголовок и прокручиваемый столбец строк.
func _make_window(rows: Array[Control], title: String) -> PanelContainer:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.card(true))
	panel.custom_minimum_size = Vector2(WINDOW_WIDTH, 0)
	panel.size = Vector2(WINDOW_WIDTH, 0)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 16)
	panel.add_child(col)
	col.add_child(_label(title, Style.FONT_H2, Style.INK))
	_window_scroll = ScrollContainer.new()
	_window_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_window_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	col.add_child(_window_scroll)
	var list := VBoxContainer.new()
	list.add_theme_constant_override("separation", ROW_GAP)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_window_scroll.add_child(list)
	for r in rows:
		list.add_child(r)
	_window_scroll.custom_minimum_size = Vector2(WINDOW_WIDTH - 2 * Style.PAD_CARD, 0)
	_fit_window.call_deferred(panel, list)
	MouseUi.pass_through(panel)
	Jelly.panel(panel)
	return panel


## Высота окна по содержимому, но не выше `WINDOW_MAX_HEIGHT`: строки с переносом знают свою
## высоту только после раскладки.
func _fit_window(panel: PanelContainer, list: VBoxContainer) -> void:
	await get_tree().process_frame
	if not is_instance_valid(panel) or _window_node != panel:
		return
	_window_scroll.custom_minimum_size.y = minf(list.get_combined_minimum_size().y, WINDOW_MAX_HEIGHT - 120.0)
	panel.reset_size()


## История денег по релизам, свежие сверху: заголовок релиза с итогом, строки операций.
func _money_rows() -> Array[Control]:
	var rows: Array[Control] = []
	var by_release := {}
	for e in run.wallet.history:
		var r := int(e.get("release", 0))
		if not by_release.has(r):
			by_release[r] = []
		(by_release[r] as Array).append(e)
	var releases: Array = by_release.keys()
	releases.sort()
	releases.reverse()
	if releases.is_empty():
		rows.append(_wrap_label("Денег пока никто не трогал. Это ненадолго.", Style.FONT_BODY, Style.INK_2))
		return rows
	for r in releases:
		var net := 0
		for e in by_release[r]:
			net += int(e["delta"])
		rows.append(_money_row("Релиз %d" % r, net, true))
		for e in by_release[r]:
			var reason := str(e.get("reason", ""))
			var text: String = REASONS.get(reason, reason)
			var note := str(e.get("note", ""))
			if note != "":
				text += " · " + note
			rows.append(_money_row(text, int(e["delta"]), false))
	return rows


func _money_row(text: String, delta: int, head: bool) -> Control:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 16)
	var l := _label(text, Style.FONT_H2 if head else Style.FONT_BODY, Style.INK if head else Style.INK_2)
	if head:
		l.add_theme_font_override("font", Jelly.fun_font(800))
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	l.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	l.clip_text = true
	row.add_child(l)
	var sign := "+ " if delta > 0 else ("− " if delta < 0 else "")
	# Итог релиза спокойнее строк: чернилами, цвет только у операций.
	var color := Style.MONEY if delta > 0 else (Style.DANGER if delta < 0 else Style.INK_2)
	var m := _label(sign + Style.format_money(absi(delta)), Style.FONT_BODY, Style.INK if head else color)
	m.add_theme_font_override("font", Style.mono_font())
	row.add_child(m)
	if head:
		var box := VBoxContainer.new()
		box.add_child(_spacer(8))
		box.add_child(row)
		return box
	return row


## Купленная прокачка по порядку покупки: полоса цвета вида, название, вид, релиз покупки.
func _upgrade_rows() -> Array[Control]:
	var rows: Array[Control] = []
	var ids := run.studio.upgrade_ids
	if ids.is_empty():
		rows.append(_wrap_label("Пока ничего не куплено. Студия держится на энтузиазме и одной кофеварке.", Style.FONT_BODY, Style.INK_2))
		return rows
	for i in ids.size():
		var def := UpgradePool.find(run.upgrades, ids[i])
		var row := PanelContainer.new()
		var sb := Style.flat(Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 0)
		sb.content_margin_left = 0
		sb.content_margin_right = 20
		sb.content_margin_top = 14
		sb.content_margin_bottom = 14
		row.add_theme_stylebox_override("panel", sb)
		var h := HBoxContainer.new()
		h.add_theme_constant_override("separation", 16)
		row.add_child(h)
		var kind := int(def.kind) if def != null else int(UpgradeDef.Kind.CAPABILITY)
		var bar := Panel.new()
		bar.custom_minimum_size = Vector2(8, 0)
		bar.add_theme_stylebox_override("panel", Style.flat(Style.kind_color(kind), 4, Color.TRANSPARENT, 0))
		h.add_child(bar)
		var col := VBoxContainer.new()
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(col)
		col.add_child(_label(def.title if def != null else String(ids[i]), Style.FONT_BODY, Style.INK))
		var sub := _label(def.effect_line if def != null else "", Style.FONT_CAPTION, Style.INK_2)
		sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		col.add_child(sub)
		var right := VBoxContainer.new()
		right.alignment = BoxContainer.ALIGNMENT_CENTER
		h.add_child(right)
		right.add_child(_kind_pill(kind, def.kind_name() if def != null else ""))
		var when := run.studio.release_of(i)
		var wl := _label("релиз %d" % when if when > 0 else "", Style.FONT_CAPTION, Style.INK_3)
		wl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		right.add_child(wl)
		rows.append(row)
	return rows


## Отложенное предложение: строки как в списке купленного, справа цена; одна покупка.
func _offer_window_rows() -> Array[Control]:
	var rows: Array[Control] = []
	_offer_defs = run.pending_defs()
	_offer_rows.clear()
	_offer_lifts.clear()
	_offer_focus = 0
	for i in _offer_defs.size():
		if _offer_affordable(i):
			_offer_focus = i
			break
	rows.append(_wrap_label("Отложено в фазе студии. Пока новая игра не начата, одно из этого можно купить.",
			Style.FONT_CAPTION, Style.INK_2))
	for def in _offer_defs:
		var row := PanelContainer.new()
		var h := HBoxContainer.new()
		h.add_theme_constant_override("separation", 16)
		row.add_child(h)
		var kind := int(def.kind)
		var bar := Panel.new()
		bar.custom_minimum_size = Vector2(8, 0)
		bar.add_theme_stylebox_override("panel", Style.flat(Style.kind_color(kind), 4, Color.TRANSPARENT, 0))
		h.add_child(bar)
		var col := VBoxContainer.new()
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(col)
		col.add_child(_label(def.title, Style.FONT_BODY, Style.INK))
		var sub := _label(def.effect_line, Style.FONT_CAPTION, Style.INK_2)
		sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		col.add_child(sub)
		var right := VBoxContainer.new()
		right.alignment = BoxContainer.ALIGNMENT_CENTER
		h.add_child(right)
		right.add_child(_kind_pill(kind, def.kind_name()))
		var price := _label(Style.format_money(def.price(run.economy)), Style.FONT_BODY, Style.INK)
		price.add_theme_font_override("font", Style.mono_font())
		price.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		right.add_child(price)
		rows.append(row)
		_offer_rows.append(row)
		_offer_lifts.append(Jelly.button(row, Style.R_CTL))
	return rows


## Окно ставки (#133): три исхода с границами оценок и выигрыш.
func _bet_window_rows() -> Array[Control]:
	var rows: Array[Control] = []
	_bet_rows.clear()
	_bet_lifts.clear()
	_bet_focus = 1
	var t := run.tuning
	rows.append(_wrap_label("Рецензии ещё не вышли. Угадаешь тон: %s в кассу. Не угадаешь: ничего не теряешь." % Style.format_money(t.bet_bonus),
			Style.FONT_CAPTION, Style.INK_2))
	var ranges: Array[String] = ["ниже %s" % _score(t.bet_low), "от %s до %s" % [_score(t.bet_low), _score(t.bet_high)],
			"от %s и выше" % _score(t.bet_high)]
	for i in 3:
		var row := PanelContainer.new()
		var h := HBoxContainer.new()
		h.add_theme_constant_override("separation", 16)
		row.add_child(h)
		var name := _label(BET_NAMES[i], Style.FONT_BODY, Style.INK)
		name.add_theme_font_override("font", Jelly.fun_font(800))
		name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(name)
		var range_ := _label(ranges[i], Style.FONT_BODY, Style.INK_2)
		range_.add_theme_font_override("font", Style.mono_font())
		h.add_child(range_)
		rows.append(row)
		_bet_rows.append(row)
		_bet_lifts.append(Jelly.button(row, Style.R_CTL))
	return rows


func _refresh_bet() -> void:
	for i in _bet_rows.size():
		var on := i == _bet_focus
		var sb := Style.flat(Style.INK if on else Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 0)
		sb.content_margin_left = 20
		sb.content_margin_right = 20
		sb.content_margin_top = 14
		sb.content_margin_bottom = 14
		_bet_rows[i].add_theme_stylebox_override("panel", sb)
		_bet_lifts[i].focused = on
		var h := _bet_rows[i].get_child(0) as HBoxContainer
		(h.get_child(0) as Label).add_theme_color_override("font_color", Style.SURFACE_SOLID if on else Style.INK)
		(h.get_child(1) as Label).add_theme_color_override("font_color", Style.SURFACE_2 if on else Style.INK_2)


static func _score(v: float) -> String:
	return ("%.1f" % v).replace(".", ",")


## Фокус строки предложения: тёмная подложка; цена красным, если покупка съест запас.
func _refresh_offer() -> void:
	for i in _offer_rows.size():
		var on := i == _offer_focus
		var sb := Style.flat(Style.INK if on else Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 0)
		sb.content_margin_left = 0
		sb.content_margin_right = 20
		sb.content_margin_top = 14
		sb.content_margin_bottom = 14
		_offer_rows[i].add_theme_stylebox_override("panel", sb)
		_offer_lifts[i].focused = on
		var h := _offer_rows[i].get_child(0) as HBoxContainer
		var col := h.get_child(1) as VBoxContainer
		(col.get_child(0) as Label).add_theme_color_override("font_color", Style.SURFACE_SOLID if on else Style.INK)
		(col.get_child(1) as Label).add_theme_color_override("font_color", Style.SURFACE_2 if on else Style.INK_2)
		var price := (h.get_child(2) as VBoxContainer).get_child(1) as Label
		var ok := _offer_affordable(i)
		price.add_theme_color_override("font_color", (Style.SURFACE_SOLID if on else Style.INK) if ok else Style.DANGER)


func _shake(node: Control) -> void:
	if Debug.skip_cards:
		return
	var x := node.position.x
	var tw := create_tween()
	for dx in [10.0, -8.0, 5.0, -2.0, 0.0]:
		tw.tween_property(node, "position:x", x + dx, 0.04)


func _kind_pill(kind: int, text: String) -> PanelContainer:
	var p := PanelContainer.new()
	var sb := Style.flat(Style.kind_tint(kind), Style.R_PILL, Color.TRANSPARENT, 0)
	sb.content_margin_left = 12
	sb.content_margin_right = 12
	sb.content_margin_top = 2
	sb.content_margin_bottom = 2
	p.add_theme_stylebox_override("panel", sb)
	p.add_child(_label(text, Style.FONT_CAPTION, Style.kind_color(kind)))
	return p


## Лента релиза справа на полэкрана.
func _open_release(i: int) -> void:
	var record := run.records[run.records.size() - 1 - i]
	if record.score == null:
		ShellSounds.play(&"miss")
		return
	_lifts[i].press()
	_open_feed(record, run.build_feed(record), -1)


## Панель ленты слева; `at` элемент, на котором она открывается (-1 с начала).
func _open_feed(record: GameRecord, content: FeedContent, at: int) -> void:
	_close_window(false)
	window = Pop.RELEASE
	overlay_changed.emit(true)
	_feed_record = record
	_feed = (load(Main.FEED_PATH) as PackedScene).instantiate() as FeedScreen
	_feed.setup_archive(content, record)
	_feed.finished.connect(_close_window.bind(true))
	_feed.demo_requested.connect(_play_demo)
	add_child(_feed)
	if at > 0:
		_feed.open_at.call_deferred(at)
	_set_new_game_shown(false)


func _play_demo() -> void:
	var record := _feed_record
	if record == null:
		return
	_demo = DemoCatalog.create(record)
	if _demo == null:
		ShellSounds.play(&"miss")
		return
	playing = true
	_chrome.visible = false
	_feed.visible = false
	_demo.setup(record, &"gallery")
	_demo.demo_finished.connect(_on_demo_finished)
	add_child(_demo)
	_demo.start()


func _on_demo_finished(_r: GameRecord, _reached: bool) -> void:
	if _demo != null:
		_demo.queue_free()
		_demo = null
	playing = false
	_chrome.visible = true
	if _feed != null:
		_feed.visible = true


# --- Построение ---------------------------------------------------------------------------------

## Хром заново на месте (после покупки): без появления, фокус хозяин ставит сам.
func _rebuild() -> void:
	_chrome.queue_free()
	_focusables.clear()
	_lifts.clear()
	_labels.clear()
	_offer_index = -1
	_offer_halo = null
	_wave_focus.clear()
	_wave_nodes.clear()
	_build()


## Хром заново, фокус остаётся на том же элементе; новая карточка волны `fresh` вздрагивает.
func _rebuild_keeping_focus(fresh: Wave = Wave.BET) -> void:
	var kept: Wave = _wave_focus.get(focus, Wave.BET)
	var on_wave := _wave_focus.has(focus)
	var release := focus if focus < _release_count else -1
	var on_money := focus == _money_index
	var on_upgrades := focus == _upgrades_index
	_rebuild()
	if on_wave and _wave_nodes.has(kept):
		focus = _wave_focus.find_key(kept)
	elif release >= 0:
		focus = release
	elif on_money:
		focus = _money_index
	elif on_upgrades:
		focus = _upgrades_index
	_refresh_focus()
	if fresh != Wave.BET and _wave_nodes.has(fresh) and not Debug.skip_cards:
		var node := _wave_nodes[fresh]
		node.modulate.a = 0.0
		create_tween().tween_property(node, "modulate:a", 1.0, Style.SWITCH_SECONDS)
		Jelly.poke.call_deferred(node, 1.6)


func _build() -> void:
	_chrome = Control.new()
	_chrome.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_chrome.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_chrome)

	# Слева сверху: логотип и название с номером релиза.
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 16)
	head.position = Vector2(Style.EDGE, Style.HEADER_Y - 28)
	_chrome.add_child(head)
	if run.studio_logo != null:
		var logo := StudioLogoView.new()
		logo.custom_minimum_size = Vector2(56, 56)
		logo.set_logo(run.studio_logo, false)
		head.add_child(logo)
	var title := HintPill.header(ShellHeader.text("Релиз %d" % run.release))
	title.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(title)

	# Справа: релизы этого забега, свежие сверху.
	_releases_scroll = ScrollContainer.new()
	_releases_scroll.position = Vector2(Style.SCREEN.x - Style.EDGE - RELEASE_CARD.x - 24, RELEASES_TOP)
	_releases_scroll.size = Vector2(RELEASE_CARD.x + 48, Style.SCREEN.y - RELEASES_TOP - RELEASES_BOTTOM)
	_releases_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_releases_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	_chrome.add_child(_releases_scroll)
	var margin := MarginContainer.new()
	for side in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 24)
	_releases_scroll.add_child(margin)
	var list := VBoxContainer.new()
	list.add_theme_constant_override("separation", 16)
	margin.add_child(list)
	for i in run.records.size():
		var c := _release_card(run.records[run.records.size() - 1 - i], run.records.size() - i)
		list.add_child(c)
		_add_focusable(c, Jelly.button(c, Style.R_CARD), null)
	_release_count = run.records.size()

	# Под названием: деньги, «Прокачка» и, если предложение отложено, «Прокачаться».
	_pills = HBoxContainer.new()
	_pills.add_theme_constant_override("separation", 16)
	_pills.position = Vector2(Style.EDGE, PILLS_Y)
	_chrome.add_child(_pills)
	_money_index = _focusables.size()
	_pill_button(_pills, Style.format_money(run.wallet.cash), true)
	_upgrades_index = _focusables.size()
	_pill_button(_pills, "Прокачка · %d" % run.studio.upgrade_ids.size(), false)
	if not run.pending_defs().is_empty():
		_offer_index = _focusables.size()
		_offer_button(_pills)

	# Снизу по центру: «Новая игра».
	var b := PanelContainer.new()
	b.custom_minimum_size = NEW_GAME_SIZE
	b.size = NEW_GAME_SIZE
	b.position = Vector2((Style.SCREEN.x - NEW_GAME_SIZE.x) / 2.0, Style.SCREEN.y - NEW_GAME_BOTTOM - NEW_GAME_SIZE.y)
	var caption := "Новая игра"
	if after:
		caption = "Итоги релиза" if _wave_plan.is_empty() else "Показать всё"
	var bl := _label(caption, Style.FONT_H1, Style.INK)
	bl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	bl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	b.add_child(bl)
	_chrome.add_child(b)
	_new_index = _focusables.size()
	_add_focusable(b, Jelly.button(b), bl)
	focus = _new_index

	var hints := HBoxContainer.new()
	hints.alignment = BoxContainer.ALIGNMENT_CENTER
	hints.add_theme_constant_override("separation", 16)
	hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hints.offset_top = -(Style.PILL_HEIGHT + 16)
	hints.offset_bottom = -16
	hints.add_child(HintPill.make("← → ↑ ↓ выбрать"))
	hints.add_child(HintPill.make(GameInput.hint(GameInput.A, "нажать")))
	hints.add_child(HintPill.make("Esc пауза"))
	_chrome.add_child(hints)
	_hints = hints
	if after:
		_build_waves()
	MouseUi.pass_through(self)


## После релиза: столбик карточек отклика слева под пилюлями, по порядку прихода.
func _build_waves() -> void:
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 12)
	col.position = Vector2(Style.EDGE, WAVES_TOP)
	_chrome.add_child(col)
	for kind in _waves_shown:
		var c := _wave_card(kind)
		col.add_child(c)
		_wave_focus[_focusables.size()] = kind
		_wave_nodes[kind] = c
		_add_focusable(c, Jelly.button(c, Style.R_CARD), null)


## Карточка волны: подпись мелко и главное одной строкой.
func _wave_card(kind: Wave) -> PanelContainer:
	var c := PanelContainer.new()
	c.custom_minimum_size = WAVE_CARD
	var sb := Style.flat(Style.SURFACE_SOLID, Style.R_CARD, Color.TRANSPARENT, 0)
	sb.content_margin_left = 20
	sb.content_margin_right = 20
	sb.content_margin_top = 14
	sb.content_margin_bottom = 14
	c.add_theme_stylebox_override("panel", sb)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 4)
	c.add_child(col)
	var caption := WAVE_NAMES[kind]
	var text := ""
	var color := Style.INK
	var mono := false
	match kind:
		Wave.BET:
			if after_record.bet < 0:
				text = "Что скажут критики?"
			elif not after_record.bet_done:
				caption = "Ставка сделана"
				text = BET_NAMES[after_record.bet]
			elif bet_won():
				caption = "Ставка сыграла"
				text = "+ " + Style.format_money(run.tuning.bet_bonus)
				color = Style.MONEY
			else:
				caption = "Ставка не сыграла"
				text = "%s, а вышло «%s»" % [BET_NAMES[after_record.bet], VERDICTS[bet_class()]]
		Wave.TWEETS:
			caption = "Твиты · " + after_content.tag
			for it in after_content.items:
				if it.kind == FeedContent.Kind.TWEET:
					text = it.text
					break
		Wave.STREAM:
			caption = "Стрим · " + after_content.clip_person.name
			text = FeedContent.format_count(after_content.online) + " онлайн" + (" · разлетается" if after_content.viral else "")
		Wave.CRITICS:
			text = _score(after_content.critics_avg) + " · " + VERDICTS[bet_class()]
			mono = true
		Wave.SALES:
			text = Style.format_money(after_content.sales_first)
			color = Style.MONEY
			mono = true
	var cl := _label(caption, Style.FONT_CAPTION, Style.INK_3)
	cl.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	cl.clip_text = true
	col.add_child(cl)
	var tl := _label(text, Style.FONT_BODY, color)
	tl.add_theme_font_override("font", Style.mono_font() if mono else Jelly.fun_font(800))
	tl.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	tl.clip_text = true
	col.add_child(tl)
	return c


## «Прокачаться»: зелёная пилюля, раз в пару секунд вздрагивает и пускает от себя ореол.
func _offer_button(parent: Control) -> void:
	var p := PanelContainer.new()
	p.custom_minimum_size = Vector2(0, Style.PILL_HEIGHT + 16)
	var l := _label("Прокачаться", Style.FONT_BODY, Style.SURFACE_SOLID)
	l.add_theme_font_override("font", Jelly.fun_font(800))
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	p.add_child(l)
	_offer_halo = Panel.new()
	_offer_halo.show_behind_parent = true
	_offer_halo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_offer_halo.add_theme_stylebox_override("panel", Style.flat(OFFER_COLOR, Style.R_PILL, Color.TRANSPARENT, 0))
	_offer_halo.modulate.a = 0.0
	p.add_child(_offer_halo)
	parent.add_child(p)
	_add_focusable(p, Jelly.button(p, Style.R_PILL), l)
	_pulse_offer.call_deferred()


## Ореол расходится от кнопки и гаснет, кнопка вздрагивает; по кругу, пока кнопка жива.
func _pulse_offer() -> void:
	var halo := _offer_halo
	if halo == null or not is_instance_valid(halo) or Debug.skip_cards:
		return
	var host := halo.get_parent() as Control
	halo.position = Vector2.ZERO
	halo.size = host.size
	halo.pivot_offset = host.size / 2.0
	halo.scale = Vector2.ONE
	halo.modulate.a = 0.55
	if window == Pop.NONE:
		Jelly.poke(host, 0.8)
	var tw := halo.create_tween().set_parallel(true).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(halo, "scale", Vector2(1.18, 1.6), 0.9)
	tw.tween_property(halo, "modulate:a", 0.0, 0.9)
	tw.chain().tween_interval(OFFER_PULSE_SECONDS - 0.9)
	tw.chain().tween_callback(_pulse_offer)


func _add_focusable(c: Control, lift: JellyLift, label: Label) -> void:
	_focusables.append(c)
	_lifts.append(lift)
	_labels.append(label)


## Пилюля-кнопка шапки: `surface`, в фокусе тёмная.
func _pill_button(parent: Control, text: String, money: bool) -> void:
	var p := PanelContainer.new()
	p.custom_minimum_size = Vector2(0, Style.PILL_HEIGHT + 16)
	var l := _label(text, Style.FONT_BODY, Style.MONEY if money else Style.INK)
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	if money:
		l.add_theme_font_override("font", Style.mono_font())
		if run.wallet.cash < 0:
			l.add_theme_color_override("font_color", Style.DANGER)
	p.add_child(l)
	parent.add_child(p)
	_add_focusable(p, Jelly.button(p, Style.R_PILL), l)


func _release_card(r: GameRecord, number: int) -> PanelContainer:
	var c := PanelContainer.new()
	c.custom_minimum_size = RELEASE_CARD
	var sb := Style.flat(Style.SURFACE_SOLID, Style.R_CARD, Color.TRANSPARENT, 0)
	sb.content_margin_left = 20
	sb.content_margin_right = 20
	sb.content_margin_top = 16
	sb.content_margin_bottom = 14
	c.add_theme_stylebox_override("panel", sb)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 6)
	c.add_child(col)
	var stripes := HBoxContainer.new()
	stripes.add_theme_constant_override("separation", 6)
	col.add_child(stripes)
	var values := [int(r.genre), int(r.tech), int(r.setting)]
	for k in 3:
		var entry := _catalogs[k].by_value(values[k])
		var bar := Panel.new()
		bar.custom_minimum_size = Vector2(0, STRIPE)
		bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		bar.add_theme_stylebox_override("panel", Style.flat(entry.color if entry != null else Style.INK_3, Style.R_PILL, Color.TRANSPARENT, 0))
		stripes.add_child(bar)
	var t := _label(r.title, Style.FONT_BODY, Style.INK)
	t.add_theme_font_override("font", Jelly.fun_font(800))
	t.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	t.clip_text = true
	col.add_child(t)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	col.add_child(row)
	var critics := _label("%.1f" % r.score.critics if r.score != null else "—", Style.FONT_BODY, Style.INK)
	critics.add_theme_font_override("font", Style.mono_font())
	row.add_child(critics)
	var meta := _label("релиз %d%s" % [number, " · багов %d" % r.bug_ids.size() if not r.bug_ids.is_empty() else ""],
			Style.FONT_CAPTION, Style.INK_3)
	meta.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(meta)
	return c


## Фокус: кнопки и пилюли тёмные с белым текстом, карточки релизов на бортике.
func _refresh_focus() -> void:
	for i in _focusables.size():
		var on := i == focus
		_lifts[i].focused = on
		if i < _release_count or _wave_focus.has(i):
			continue
		var c := _focusables[i] as PanelContainer
		var radius := Style.R_PILL if i != _new_index else Style.R_CTL
		var bg := Style.INK if on else Style.SURFACE_SOLID
		if i == _offer_index:
			bg = OFFER_COLOR.darkened(0.3) if on else OFFER_COLOR
		var sb := Style.flat(bg, radius, Color.TRANSPARENT, 0)
		sb.content_margin_left = 24
		sb.content_margin_right = 24
		c.add_theme_stylebox_override("panel", sb)
		var l := _labels[i]
		var base := Style.INK
		if i == _money_index:
			base = Style.DANGER if run.wallet.cash < 0 else Style.MONEY
		elif i == _offer_index:
			base = Style.SURFACE_SOLID
		l.add_theme_color_override("font_color", Style.SURFACE_SOLID if on else base)


func _label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _wrap_label(text: String, font_size: int, color: Color) -> Label:
	var l := _label(text, font_size, color)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(WINDOW_WIDTH - 2 * Style.PAD_CARD, 0)
	return l


func _spacer(h: int) -> Control:
	var s := Control.new()
	s.custom_minimum_size = Vector2(0, h)
	return s
