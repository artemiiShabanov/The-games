class_name RunHub
extends Control
## Главный экран забега (плейтест 2026-11-11, #77 и #78), спека `docs/specs/run.md`. Между
## релизами игрок стоит здесь, новый релиз начинается кнопкой «Новая игра», а не сам. Фоном
## студия (её рисует хозяин под экраном), поверх только хром: слева сверху логотип и название,
## под ними пилюли денег, «Штат», «Соискатели» и «Сеттинги» (и зелёная «Жанр или технология», если от предложения фазы студии
## отказались), снизу по центру «Новая игра». Столбика карточек релизов справа нет (полировка
## 2026-11-17): выпущенные игры открываются со статуэток на полке студии.
## - Пилюля денег раскрывает мармеладом окно с историей денег по релизам (`Wallet.history`).
## - «Штат» раскрывает окно нанятых людей (роль, грейд, эффект, зарплата) и купленных жанров и
##   технологий. «Соискатели» раскрывает доску: ↑ ↓ или наведение выбирают, ␣ или клик нанимают,
##   нанимать можно нескольких подряд, пока хватает денег сверх запаса на следующий релиз.
## - «Прокачаться» раскрывает отложенное предложение прокачки (`RunState.pending_offer`): одна
##   покупка до старта новой игры, с тем же запасом на следующий релиз, что и в фазе студии.
## - Статуэтка на полке открывает карточку игры как в галерее: «Играть» (демка на весь экран),
##   «Отклик» (лента этого релиза панелью слева, `FeedScreen` архивом, без стрима), «Стрим»
##   (запись стримера отдельным окном, `StreamScreen`) и «Закрыть». Статуэтки в фокус берут и
##   стрелки: хозяин даёт их прямоугольники (`shelf_rects`), под выбранной пилюля с названием.
## После релиза (#133, `setup_after`): тот же экран, но вместо «Новой игры» кнопка «Итоги
## релиза», а слева под пилюлями столбик карточек отклика. Отклик приходит волнами с небольшим
## перерывом: твиты, стример, критики, продажи; карточка волны открывает ленту релиза с тем, что
## уже пришло, карточка «Стрим» окно стрима. Первой стоит карточка ставки: до прихода критиков можно угадать их оценку
## (`RunTuning.bet_*`). Кнопка внизу «Итоги релиза»: оставшиеся волны приходят сразу, дальше
## рецензии, если не открыты, и итоги (`after_finished`). Клик по предмету в студии это второй вход в те же действия:
## хозяин зовёт `open_offer` (посылка) и `open_record` (коробка на полке).
## Оценки критиков не показываются, пока игрок не нажал на их карточку: тогда рецензии
## открываются по одной с паузой и только после этого попадают в общую ленту; ставка
## принимается, пока они закрыты.
## Стрелки ходят по экрану (`FocusNav`), наведение мыши переносит фокус, ␣ или клик нажимают,
## колесо и тачпад листают окна. Esc, Ctrl или клик мимо закрывают окно; без окна Esc
## уходит хозяину (пауза).

signal new_game
signal upgrade_bought(upgrade: UpgradeDef)
## Нанят человек с доски соискателей (спека `docs/specs/staff.md`).
signal staff_hired(member: StaffMember)
## Окно или панель релиза открылись (`true`) или закрылись: хозяин притеняет студию под ними.
signal overlay_changed(on: bool)
## После релиза (#133): пришла волна отклика; ставка на критиков сыграла или нет; игрок
## досмотрел и идёт к итогам релиза.
signal wave_arrived(kind: Wave)
signal bet_resolved(won: bool)
signal critics_revealed
signal after_finished

## Ряд пилюль денег и прокачки под названием студии.
const PILLS_Y := 104.0
const WINDOW_WIDTH := 640.0
const WINDOW_TOP := 176.0
const WINDOW_MAX_HEIGHT := 760.0
const NEW_GAME_SIZE := Vector2(520, 88)
const NEW_GAME_BOTTOM := 104.0
const POP_SECONDS := 0.36
const ROW_GAP := 12
## «Прокачаться» (цвет `success` палитры): как часто кнопка зовёт к себе.
const OFFER_PULSE_SECONDS := 2.4

enum Pop { NONE, MONEY, UPGRADES, RELEASE, OFFER, BET, GAME, STREAM, BOARD, GAMES }
## Волны отклика после релиза по порядку прихода; ставка стоит первой и не приходит.
enum Wave { BET, TWEETS, STREAM, CRITICS, SALES }

const GAME_CARD_WIDTH := 840.0
const GAME_BUTTON := Vector2(200, 72)
## Поле вокруг статуэтки на полке, в котором она берёт курсор: сама она мелкая.
const BOX_GROW := Vector2(2, 8)
const BOX_TIP_GAP := 4.0
const WAVE_CARD := Vector2(400, 96)
const WAVES_TOP := 196.0
const WAVE_NAMES: Array[String] = ["Ставка", "Твиты", "Стрим", "Критики", "Первая неделя"]
const BET_NAMES: Array[String] = ["Низкая", "Средняя", "Высокая"]
## Как вышло на деле, теми же тремя ступенями.
const VERDICTS: Array[String] = ["низкая", "средняя", "высокая"]

## Подписи строк истории денег по причине `Wallet`.
const REASONS := {
	"release": "Разработка", "bugfix": "Багфикс", "sales": "Первая неделя", "tail": "Продажи прошлых игр",
	"share": "Доли по договорам", "upkeep": "Содержание", "upgrade": "Улучшения", "event": "Вставка",
	"bet": "Ставка на критиков",
	"rescue": "Аванс издателя", "staff": "Наём",
}

var run: RunState
var focus := 0
var window := Pop.NONE
var playing := false
## Тема последней выпущенной игры фоном (#87).
var _bed: MusicBed

var _focusables: Array[Control] = []
var _lifts: Array[JellyLift] = []
var _labels: Array[Label] = []
## Прямоугольники статуэток на полке студии по номеру игры в забеге, на экране: даёт хозяин.
var shelf_rects: Callable
## Статуэтки в списке фокуса: индекс фокуса в номер игры; пилюля с названием над выбранной.
var _box_focus: Dictionary[int, int] = {}
var _box_tip: PanelContainer
var _new_index := 0
var _upgrades_index := 0
var _money_index := 0
var _settings_index := -1
var _settings: SettingsScreen
var _offer_index := -1
## Пилюля «Соискатели» и люди в открытом окне доски, по строкам.
var _board_index := -1
## Карточка студии слева сверху (2026-11-18): открывает список выпущенных игр.
var _studio_index := -1
var _studio_label: Label
## Строки окна игр студии: номер записи забега на строку.
var _games_rows: Array[int] = []
var _board_members: Array[StaffMember] = []
var _offer_rows: Array[PanelContainer] = []
var _offer_lifts: Array[JellyLift] = []
var _offer_defs: Array[UpgradeDef] = []
var _offer_focus := 0
var _offer_halo: Panel
var _pills: HBoxContainer
var _chrome: Control
var _hints: HBoxContainer
var _window_node: PanelContainer
var _window_scroll: ScrollContainer
var _feed: FeedScreen
var _feed_record: GameRecord
var _stream: StreamScreen
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
## Открыта панель рецензий: с её закрытием оценки считаются увиденными.
var _revealing := false
## Карточка игры (статуэтка с полки): кнопки и что каждая делает.
var _game_actions: Array[StringName] = []
var _game_buttons: Array[PanelContainer] = []
var _game_lifts: Array[JellyLift] = []
var _game_focus := 0


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
	if run != null:
		# Заглавная тема Studio Running (2026-11-18), раньше тема последней игры.
		_bed = MusicBed.main(Music.tuning().hub_db)
		add_child(_bed)
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
	# Волны, что ещё не пришли, приходят сразу, и экран идёт дальше (2026-11-18: кнопка всегда
	# «Итоги релиза», «Показать всё» висело, пока открытое окно держало волны).
	if after and not _wave_plan.is_empty():
		show_all_waves()
	if after and not after_record.bet_done:
		# Рецензии ещё не открыты: сначала они, итоги потом.
		open_wave(Wave.CRITICS)
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
	if not after_record.bet_done:
		_reveal_critics()
	after_finished.emit()


func waves_left() -> int:
	return _wave_plan.size()


func _process(delta: float) -> void:
	if _bed != null:
		_bed.active = not playing and _feed == null and _stream == null
	if not after or _wave_plan.is_empty() or window != Pop.NONE or playing or get_tree().paused:
		return
	_wave_timer -= delta
	if _wave_timer > 0.0:
		return
	_wave_timer = run.tuning.after_gap_seconds
	var kind: Wave = _wave_plan.pop_front()
	_arrive(kind, true)
	_rebuild_keeping_focus(kind)


## Волна пришла. Рецензии приходят закрытыми: оценки открывает игрок.
func _arrive(kind: Wave, sound: bool) -> void:
	_waves_shown.append(kind)
	if sound:
		ShellSounds.play(&"intro")
	wave_arrived.emit(kind)


## Рецензии увидены: ставка сыграла или нет (без ставки её карточка уходит), оценка критиков
## теперь видна на карточке и в общей ленте.
func _reveal_critics() -> void:
	if after_record.bet_done:
		return
	after_record.bet_done = true
	if after_record.bet < 0:
		_waves_shown.erase(Wave.BET)
	else:
		bet_resolved.emit(bet_won())
	critics_revealed.emit()
	_rebuild_keeping_focus()


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
	if kind == Wave.STREAM:
		_open_stream(after_record, after_content)
		return
	if kind == Wave.SALES:
		# Продажи только показываются (2026-11-18): лента релиза теперь на экране итогов.
		if _wave_nodes.has(kind):
			Jelly.poke(_wave_nodes[kind], 1.0)
		return
	if kind == Wave.CRITICS and not after_record.bet_done:
		# Первый раз: только рецензии, по одной с паузой.
		_open_feed(after_record, after_content.only([FeedContent.Kind.CRITIC]), -1, run.tuning.after_critic_seconds)
		_revealing = true
		return
	var kinds: Array = []
	var first := -1
	var want: FeedContent.Kind = FeedContent.Kind.TWEET
	var seen := after_record.bet_done
	for w in _waves_shown:
		match w:
			Wave.TWEETS:
				kinds.append(FeedContent.Kind.TWEET)
			Wave.CRITICS:
				if seen:
					kinds.append(FeedContent.Kind.CRITIC)
			Wave.SALES:
				# В итоговых цифрах есть средняя критиков: до рецензий их не показываем.
				if seen:
					kinds.append(FeedContent.Kind.NUMBERS)
	match kind:
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
	if _box_focus.has(i):
		open_record(_box_focus[i])
	elif i == _new_index:
		start_new_game()
	elif i == _upgrades_index:
		_toggle_window(Pop.UPGRADES)
	elif i == _money_index:
		_toggle_window(Pop.MONEY)
	elif i == _settings_index:
		open_settings()
	elif i == _offer_index:
		_toggle_window(Pop.OFFER)
	elif i == _board_index:
		_toggle_window(Pop.BOARD)
	elif i == _studio_index:
		_toggle_window(Pop.GAMES)
	elif _wave_focus.has(i):
		_lifts[i].press()
		open_wave(_wave_focus[i])


func open_money() -> void:
	_toggle_window(Pop.MONEY)


func open_upgrades() -> void:
	_toggle_window(Pop.UPGRADES)


## Список сеттингов и достижений (#139) поверх главного экрана.
func open_settings() -> void:
	if _settings != null:
		return
	_close_window(false)
	_lifts[_settings_index].press()
	_settings = SettingsScreen.new()
	_settings.setup(run.profile, run)
	_settings.closed.connect(func() -> void:
		_settings.queue_free()
		_settings = null
		_hints.visible = true
		overlay_changed.emit(false))
	_hints.visible = false
	overlay_changed.emit(true)
	add_child(_settings)


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
	if window == Pop.GAMES:
		return true
	if window == Pop.BOARD:
		return run.can_hire(_board_members[i])
	return run.wallet.can_afford(_offer_defs[i].price(run.economy) + run.cheapest_next())


func open_board() -> void:
	if _board_index >= 0:
		_toggle_window(Pop.BOARD)


## Нанять соискателя из строки `i` доски. Доска остаётся открытой, пока на ней кто-то есть.
func hire_staff(i: int) -> bool:
	if i < 0 or i >= _board_members.size():
		return false
	var m := _board_members[i]
	_offer_lifts[i].press()
	if not run.hire(m):
		_shake(_offer_rows[i])
		ShellSounds.play(&"miss")
		return false
	ShellSounds.play(&"done")
	staff_hired.emit(m)
	_close_window(false)
	_rebuild()
	if _board_index >= 0:
		focus = _board_index
		_refresh_focus()
		_toggle_window(Pop.BOARD)
	else:
		focus = _upgrades_index
		_refresh_focus()
		Jelly.poke(_focusables[_upgrades_index], 1.2)
	return true


## Нажата строка окна с покупкой: предложение жанра или технологии, либо доска.
func _buy_row(i: int) -> void:
	if window == Pop.GAMES:
		if i >= 0 and i < _games_rows.size():
			_offer_lifts[i].press()
			open_record(_games_rows[i])
	elif window == Pop.BOARD:
		hire_staff(i)
	else:
		buy_offer(i)


## Лента релиза `i` с конца (0 последний).
func open_release(i: int) -> void:
	_open_release(i)


## Релиз по номеру в забеге с нуля (статуэтка на полке студии, #133).
func open_record(index: int) -> void:
	if index >= 0 and index < run.records.size() and not playing:
		_open_game(index)


## Карточка игры по центру, как строка галереи: тройка, название, критики, штампы багов, кадр
## демки; под ней «Играть», «Отклик», «Стрим» (если стример игру показывал) и «Закрыть».
func _open_game(index: int) -> void:
	_close_window(false)
	window = Pop.GAME
	overlay_changed.emit(true)
	ShellSounds.play(&"intro")
	var record := run.records[index]
	_feed_record = record
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.card(true))
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 20)
	panel.add_child(col)
	col.add_child(GalleryScreen.game_card(GalleryEntry.of(record, run.run_number, index + 1, run.studio_name), GAME_CARD_WIDTH))
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 16)
	col.add_child(row)
	_game_buttons.clear()
	_game_lifts.clear()
	_game_focus = 0
	_game_actions = [&"play"]
	var names: Array[String] = ["Играть"]
	if record.score != null:
		_game_actions.append(&"feed")
		names.append("Отклик")
		if run.build_feed(record).clip_person != null:
			_game_actions.append(&"stream")
			names.append("Стрим")
	_game_actions.append(&"close")
	names.append("Закрыть")
	for text in names:
		var b := PanelContainer.new()
		b.custom_minimum_size = GAME_BUTTON
		var l := _label(text, Style.FONT_H2, Style.INK)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		b.add_child(l)
		row.add_child(b)
		_game_buttons.append(b)
		_game_lifts.append(Jelly.button(b, Style.R_CTL))
	_window_node = panel
	add_child(panel)
	MouseUi.pass_through(panel)
	Jelly.panel(panel)
	_refresh_game()
	panel.reset_size()
	panel.position = ((Vector2(Style.SCREEN) - panel.size) / 2.0).floor()
	_place_game.call_deferred(panel)
	if not Debug.skip_cards:
		panel.modulate.a = 0.0
		create_tween().tween_property(panel, "modulate:a", 1.0, POP_SECONDS * 0.5)
	_set_new_game_shown(false)


## Размер карточки известен после раскладки: тогда она встаёт точно по центру.
func _place_game(panel: PanelContainer) -> void:
	await get_tree().process_frame
	if is_instance_valid(panel) and _window_node == panel:
		panel.reset_size()
		panel.position = ((Vector2(Style.SCREEN) - panel.size) / 2.0).floor()
		panel.pivot_offset = panel.size / 2.0


func _refresh_game() -> void:
	for i in _game_buttons.size():
		var on := i == _game_focus
		_game_buttons[i].add_theme_stylebox_override("panel", Style.flat(Style.INK if on else Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 0))
		(_game_buttons[i].get_child(0) as Label).add_theme_color_override("font_color", Style.SURFACE_SOLID if on else Style.INK)
		_game_lifts[i].focused = on


func _press_game(i: int) -> void:
	_game_lifts[i].press()
	var record := _feed_record
	match _game_actions[i]:
		&"play":
			ShellSounds.play(&"done")
			_play_demo()
		&"feed":
			_open_feed(record, _feed_of(record), -1)
		&"stream":
			_open_stream(record, run.build_feed(record))
		_:
			_close_window()


## Карточка игры: ← → или наведение выбирают кнопку, ␣ или клик нажимают, Esc и клик мимо
## закрывают.
func _game_input(event: InputEvent, viewport: Viewport) -> void:
	var over := -1
	for i in _game_buttons.size():
		if MouseUi.hit(_game_buttons[i], event):
			over = i
	if MouseUi.is_motion(event):
		if over >= 0 and over != _game_focus:
			_game_focus = over
			ShellSounds.play(&"tick")
			_refresh_game()
		return
	var key := event as InputEventKey
	var esc := key != null and key.pressed and not key.echo and key.keycode == KEY_ESCAPE
	if MouseUi.is_click(event):
		if over >= 0:
			_press_game(over)
		elif not MouseUi.hit(_window_node, event):
			_close_window()
	elif not event.is_echo() and GameInput.is_a(event):
		_press_game(_game_focus)
	elif esc or GameInput.is_b(event):
		_close_window()
	elif event.is_action_pressed(GameInput.LEFT, true) or event.is_action_pressed(GameInput.RIGHT, true):
		var step := -1 if event.is_action_pressed(GameInput.LEFT, true) else 1
		var next := clampi(_game_focus + step, 0, _game_buttons.size() - 1)
		if next != _game_focus:
			_game_focus = next
			ShellSounds.play(&"tick")
			_refresh_game()
	else:
		return
	MouseUi.consume(viewport)


# --- Ввод -------------------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if playing or _settings != null:
		return
	var viewport := get_viewport()
	if window == Pop.RELEASE:
		# Лента-архив разбирает ввод сама; сюда доходит клик мимо неё.
		if MouseUi.is_click(event) and _feed != null and not FeedScreen.archive_rect().has_point((event as InputEventMouse).position):
			_close_window()
			MouseUi.consume(viewport)
		return
	if window == Pop.STREAM:
		# Окно стрима разбирает ввод само.
		return
	if window == Pop.GAME:
		_game_input(event, viewport)
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
	if MouseUi.is_click(event):
		var at := _focus_at(event)
		if at >= 0:
			activate(at)
			MouseUi.consume(viewport)
		return
	var dir := FocusNav.dir_of(event)
	if dir != Vector2.ZERO:
		var next := _nav_step(dir)
		if next != focus:
			focus = next
			ShellSounds.play(&"tick")
			_refresh_focus()
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
		if window in [Pop.OFFER, Pop.BOARD, Pop.GAMES] and inside:
			var row := _offer_row_at(event)
			if row >= 0:
				_offer_focus = row
				_refresh_offer()
				_buy_row(row)
		elif on_pill >= 0:
			activate(on_pill)
		elif not inside:
			_close_window()
	elif window in [Pop.OFFER, Pop.BOARD, Pop.GAMES] and MouseUi.is_motion(event):
		var row := _offer_row_at(event)
		if row >= 0 and row != _offer_focus:
			_offer_focus = row
			ShellSounds.play(&"tick")
			_refresh_offer()
		return
	elif window in [Pop.OFFER, Pop.BOARD, Pop.GAMES] and not event.is_echo() and GameInput.is_a(event):
		_buy_row(_offer_focus)
	elif window in [Pop.OFFER, Pop.BOARD, Pop.GAMES] and (event.is_action_pressed(GameInput.DOWN, true) or event.is_action_pressed(GameInput.UP, true)):
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
	for i in [_money_index, _upgrades_index, _offer_index, _board_index]:
		if i >= 0 and MouseUi.hit(_focusables[i], event):
			return i
	return -1


func _offer_row_at(event: InputEvent) -> int:
	for i in _offer_rows.size():
		if MouseUi.hit(_offer_rows[i], event):
			return i
	return -1


## Стрелки обходят статуэтки на полке (2026-11-18): они только для мыши.
func _nav_step(dir: Vector2) -> int:
	var ids: Array[int] = []
	var rects: Array[Rect2] = []
	var all := _focus_rects()
	var from := -1
	for i in all.size():
		if _box_focus.has(i) and i != focus:
			continue
		if i == focus:
			from = ids.size()
		ids.append(i)
		rects.append(all[i])
	var next := FocusNav.step(rects, from, dir)
	# Статуэтка в списке только та, на которой фокус (поставила мышь): стрелка уводит с неё.
	return ids[next] if next >= 0 else focus


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
		if MouseUi.rect_of(c).has_point(m.position):
			return i
	return -1


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
			title = "Штат"
		Pop.OFFER:
			pill = _focusables[_offer_index]
			rows = _offer_window_rows()
			title = "Жанр или технология"
		Pop.BOARD:
			pill = _focusables[_board_index]
			rows = _board_window_rows()
			title = "Соискатели"
		Pop.BET:
			rows = _bet_window_rows()
			title = "Оценка критиков"
		Pop.GAMES:
			pill = _focusables[_studio_index]
			rows = _games_window_rows()
			title = "Игры студии"
	_window_node = _make_window(rows, title)
	add_child(_window_node)
	if w == Pop.OFFER or w == Pop.BOARD or w == Pop.GAMES:
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
	elif window == Pop.STREAM:
		if _stream != null:
			_stream.queue_free()
			_stream = null
		_feed_record = null
	elif _window_node != null:
		var w := _window_node
		_window_node = null
		_window_scroll = null
		_offer_rows.clear()
		_offer_lifts.clear()
		_bet_rows.clear()
		_bet_lifts.clear()
		_game_buttons.clear()
		_game_lifts.clear()
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
	_refresh_tip()
	if _revealing:
		_revealing = false
		_reveal_critics()


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
		rows.append(_wrap_label("Расходов ещё не было.", Style.FONT_BODY, Style.INK_2))
		return rows
	for r in releases:
		var net := 0
		for e in by_release[r]:
			net += int(e["delta"])
		rows.append(_money_row(tr("Релиз %d") % r, net, true))
		for e in by_release[r]:
			var reason := str(e.get("reason", ""))
			var text: String = tr(REASONS.get(reason, reason))
			var note := str(e.get("note", ""))
			if note != "":
				text += " · " + tr(note)
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
	var tuning := StaffTuning.load_default()
	if run.studio.staff.is_empty():
		rows.append(_wrap_label("В штате никого. Люди нанимаются с доски соискателей.", Style.FONT_BODY, Style.INK_2))
	for m in run.studio.staff:
		rows.append(_staff_row(m, Staff.effect_line(m.role, m.grade, tuning),
				tr("%s за релиз") % Style.format_money(run.hire_salary(m)), Style.INK_3))
	if not ids.is_empty():
		rows.append(_wrap_label("Жанры и технологии", Style.FONT_CAPTION, Style.INK_3))
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
		var wl := _label(tr("релиз %d") % when if when > 0 else "", Style.FONT_CAPTION, Style.INK_3)
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
	rows.append(_wrap_label("Одну карточку можно купить до начала новой игры.",
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
		var price := _label(Style.format_price(def.price(run.economy)), Style.FONT_BODY, Style.INK)
		price.add_theme_font_override("font", Style.mono_font())
		price.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		right.add_child(price)
		rows.append(row)
		_offer_rows.append(row)
		_offer_lifts.append(Jelly.button(row, Style.R_CTL))
	return rows


## Строка человека: полоса цвета грейда, роль, эффект, справа грейд пилюлей и подпись.
func _staff_row(m: StaffMember, effect: String, note: String, note_color: Color) -> PanelContainer:
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
	# Цвет грейда: джуниор бирюзовый, мидл янтарный, сеньор фиолетовый (цвета видов улучшений).
	var kind := 2 - int(m.grade)
	var bar := Panel.new()
	bar.custom_minimum_size = Vector2(8, 0)
	bar.add_theme_stylebox_override("panel", Style.flat(Style.kind_color(kind), 4, Color.TRANSPARENT, 0))
	h.add_child(bar)
	var col := VBoxContainer.new()
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(col)
	col.add_child(_label(Staff.title(m.role), Style.FONT_BODY, Style.INK))
	var sub := _label(effect, Style.FONT_CAPTION, Style.INK_2)
	sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	col.add_child(sub)
	var right := VBoxContainer.new()
	right.alignment = BoxContainer.ALIGNMENT_CENTER
	h.add_child(right)
	right.add_child(_kind_pill(kind, Staff.GRADE_NAMES[m.grade]))
	var nl := _label(note, Style.FONT_CAPTION if note_color == Style.INK_3 else Style.FONT_BODY, note_color)
	if note_color != Style.INK_3:
		nl.add_theme_font_override("font", Style.mono_font())
	nl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	right.add_child(nl)
	return row


## Игры студии (2026-11-18): все выпущенные в забеге, последняя сверху; строка открывает
## карточку игры, как статуэтка на полке.
func _games_window_rows() -> Array[Control]:
	var rows: Array[Control] = []
	_offer_rows.clear()
	_offer_lifts.clear()
	_games_rows.clear()
	_offer_focus = 0
	if run.records.is_empty():
		rows.append(_wrap_label("Пока ни одной игры.", Style.FONT_CAPTION, Style.INK_2))
		return rows
	for k in run.records.size():
		var i := run.records.size() - 1 - k
		var r := run.records[i]
		var row := PanelContainer.new()
		var h := HBoxContainer.new()
		h.add_theme_constant_override("separation", 16)
		row.add_child(h)
		var bar := Panel.new()
		bar.custom_minimum_size = Vector2(8, 0)
		bar.add_theme_stylebox_override("panel", Style.flat(Style.INK_3, 4, Color.TRANSPARENT, 0))
		h.add_child(bar)
		var col := VBoxContainer.new()
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(col)
		col.add_child(_label(r.title, Style.FONT_BODY, Style.INK))
		col.add_child(_label(tr("Релиз %d · %s × %s × %s") % [i + 1, Game.genre_name(r.genre), Game.tech_name(r.tech),
				Game.setting_name(r.setting)], Style.FONT_CAPTION, Style.INK_2))
		var right := VBoxContainer.new()
		right.alignment = BoxContainer.ALIGNMENT_CENTER
		h.add_child(right)
		right.add_child(_label("критики", Style.FONT_CAPTION, Style.INK_3))
		var score := _label(_score(r.score.critics) if r.score != null else "—", Style.FONT_BODY, Style.INK)
		score.add_theme_font_override("font", Style.mono_font())
		score.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		right.add_child(score)
		rows.append(row)
		_offer_rows.append(row)
		_offer_lifts.append(Jelly.button(row, Style.R_CTL))
		_games_rows.append(i)
	return rows


## Доска соискателей: строки как у предложения, справа цена найма; нанять можно нескольких.
func _board_window_rows() -> Array[Control]:
	var rows: Array[Control] = []
	var tuning := StaffTuning.load_default()
	_board_members = run.board.duplicate()
	_offer_rows.clear()
	_offer_lifts.clear()
	_offer_focus = 0
	rows.append(_wrap_label("Нанятый получает зарплату каждый релиз. Соискатель ждёт недолго.",
			Style.FONT_CAPTION, Style.INK_2))
	for i in _board_members.size():
		var m := _board_members[i]
		# Без счётчика ожидания (2026-11-17): сколько соискатель ещё ждёт, игрок не видит.
		var effect := tr("%s\nЗарплата %s за релиз") % [tr(Staff.effect_line(m.role, m.grade, tuning)),
				Style.format_money(run.hire_salary(m))]
		var row := _staff_row(m, effect, Style.format_money(run.hire_price(m)), Style.INK)
		rows.append(row)
		_offer_rows.append(row)
		_offer_lifts.append(Jelly.button(row, Style.R_CTL))
	for i in _board_members.size():
		if run.can_hire(_board_members[i]):
			_offer_focus = i
			break
	return rows


## Окно ставки (#133): три исхода с границами оценок и выигрыш.
func _bet_window_rows() -> Array[Control]:
	var rows: Array[Control] = []
	_bet_rows.clear()
	_bet_lifts.clear()
	_bet_focus = 1
	var t := run.tuning
	rows.append(_wrap_label(tr("Ставка на оценку критиков. Угадано: +%s. Не угадано: 0.") % Style.format_money(t.bet_bonus),
			Style.FONT_CAPTION, Style.INK_2))
	var ranges: Array[String] = [tr("ниже %s") % _score(t.bet_low), tr("от %s до %s") % [_score(t.bet_low), _score(t.bet_high)],
			tr("от %s и выше") % _score(t.bet_high)]
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
	var s := "%.1f" % v
	return s if Lang.english() else s.replace(".", ",")


## Фокус строки предложения: тёмная подложка; цена красным, если покупка съест запас.
func _refresh_offer() -> void:
	if _window_scroll != null and _offer_focus >= 0 and _offer_focus < _offer_rows.size():
		_window_scroll.ensure_control_visible.call_deferred(_offer_rows[_offer_focus])
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
	var l := _label(text, Style.FONT_CAPTION, Style.kind_color(kind))
	# Пилюля тянется по ширине столбца с ценой: подпись посередине.
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	p.add_child(l)
	return p


## Лента релиза слева на полэкрана.
func _open_release(i: int) -> void:
	var record := run.records[run.records.size() - 1 - i]
	if record.score == null:
		ShellSounds.play(&"miss")
		return
	_open_feed(record, _feed_of(record), -1)


## Лента прошлого релиза без стрима: он открывается отдельным окном.
func _feed_of(record: GameRecord) -> FeedContent:
	return run.build_feed(record).only([FeedContent.Kind.TWEET, FeedContent.Kind.CRITIC, FeedContent.Kind.NUMBERS])


## Стрим релиза отдельным окном по центру.
func _open_stream(record: GameRecord, content: FeedContent) -> void:
	var screen := StreamScreen.new()
	if not screen.setup(record, content):
		screen.free()
		ShellSounds.play(&"miss")
		return
	_close_window(false)
	window = Pop.STREAM
	overlay_changed.emit(true)
	ShellSounds.play(&"intro")
	_feed_record = record
	_stream = screen
	_stream.finished.connect(_close_window.bind(true))
	add_child(_stream)
	_set_new_game_shown(false)
	_refresh_tip()


## Панель ленты слева; `at` элемент, на котором она открывается (-1 с начала).
func _open_feed(record: GameRecord, content: FeedContent, at: int, stagger := -1.0) -> void:
	_close_window(false)
	window = Pop.RELEASE
	overlay_changed.emit(true)
	_feed_record = record
	_feed = (load(Main.FEED_PATH) as PackedScene).instantiate() as FeedScreen
	_feed.setup_archive(content, record)
	if stagger > 0.0:
		_feed.stagger = stagger
	_feed.finished.connect(_close_window.bind(true))
	_feed.demo_requested.connect(_play_demo)
	add_child(_feed)
	if at > 0:
		_feed.open_at.call_deferred(at)
	_set_new_game_shown(false)
	_refresh_tip()


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
	if _feed != null:
		_feed.visible = false
	if _window_node != null:
		_window_node.visible = false
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
	if _window_node != null:
		_window_node.visible = true


# --- Построение ---------------------------------------------------------------------------------

## Хром заново на месте (после покупки): без появления, фокус хозяин ставит сам.
func _rebuild() -> void:
	_chrome.queue_free()
	_focusables.clear()
	_lifts.clear()
	_labels.clear()
	_offer_index = -1
	_board_index = -1
	_studio_index = -1
	_offer_halo = null
	_wave_focus.clear()
	_wave_nodes.clear()
	_box_focus.clear()
	_box_tip = null
	_build()


## Хром заново, фокус остаётся на том же элементе; новая карточка волны `fresh` вздрагивает.
func _rebuild_keeping_focus(fresh: Wave = Wave.BET) -> void:
	var kept: Wave = _wave_focus.get(focus, Wave.BET)
	var on_wave := _wave_focus.has(focus)
	var box: int = _box_focus.get(focus, -1)
	var on_money := focus == _money_index
	var on_upgrades := focus == _upgrades_index
	_rebuild()
	if on_wave and _wave_nodes.has(kept):
		focus = _wave_focus.find_key(kept)
	elif box >= 0 and _box_focus.find_key(box) != null:
		focus = _box_focus.find_key(box)
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
	# Лампа «в эфире» из логотипа Studio Running слева от названия студии.
	var title := HintPill.header(ShellHeader.text(tr("Релиз %d") % run.release), ShellHeader.studio != "")
	title.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(title)
	_studio_label = title.find_children("", "Label", true, false)[0] as Label
	_studio_index = _focusables.size()
	_add_focusable(title, Jelly.button(title, Style.R_PILL), _studio_label)

	# Статуэтки на полке студии: невидимые области фокуса поверх них и пилюля с названием.
	var boxes: Array = shelf_rects.call() if shelf_rects.is_valid() else []
	for i in mini(boxes.size(), run.records.size()):
		var r: Rect2 = boxes[i]
		if not r.has_area():
			continue
		var spot := Control.new()
		spot.position = r.position - BOX_GROW
		spot.size = r.size + 2.0 * BOX_GROW
		_chrome.add_child(spot)
		_box_focus[_focusables.size()] = i
		_add_focusable(spot, null, null)
	if not _box_focus.is_empty():
		_box_tip = HintPill.make("")
		var tip_sb := Style.flat(Style.INK, Style.R_PILL, Color.TRANSPARENT, 0)
		tip_sb.content_margin_left = 20
		tip_sb.content_margin_right = 20
		tip_sb.content_margin_top = 6
		tip_sb.content_margin_bottom = 6
		_box_tip.add_theme_stylebox_override("panel", tip_sb)
		var tip := _box_tip.get_child(0) as Label
		tip.add_theme_color_override("font_color", Style.SURFACE_SOLID)
		tip.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_box_tip.visible = false
		_chrome.add_child(_box_tip)

	# Под названием: деньги, «Прокачка» и, если предложение отложено, «Прокачаться».
	_pills = HBoxContainer.new()
	_pills.add_theme_constant_override("separation", 16)
	_pills.position = Vector2(Style.EDGE, PILLS_Y)
	_chrome.add_child(_pills)
	_money_index = _focusables.size()
	_pill_button(_pills, Style.format_money(run.wallet.cash), true)
	_upgrades_index = _focusables.size()
	_pill_button(_pills, tr("Штат · %d") % run.studio.staff.size(), false)
	if not run.board.is_empty():
		_board_index = _focusables.size()
		_pill_button(_pills, tr("Соискатели · %d") % run.board.size(), false)
	_settings_index = _focusables.size()
	_pill_button(_pills, tr("Сеттинги · %d из %d") % [SettingsScreen.open_count(run.profile, run), Game.Setting.size()], false)
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
		caption = "Итоги релиза"
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
	hints.offset_top = -(Style.PILL_HEIGHT + Style.HINTS_BOTTOM)
	hints.offset_bottom = -Style.HINTS_BOTTOM
	hints.add_child(HintPill.make("← → ↑ ↓ выбрать"))
	hints.add_child(HintPill.make(GameInput.hint(GameInput.A, tr("нажать"))))
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
				text = "Оценка критиков"
			elif not after_record.bet_done:
				caption = "Ставка сделана"
				text = BET_NAMES[after_record.bet]
			elif bet_won():
				caption = "Ставка угадана"
				text = "+ " + Style.format_money(run.tuning.bet_bonus)
				color = Style.MONEY
			else:
				caption = "Ставка не угадана"
				text = tr("Ставка: %s. Оценка: %s") % [tr(BET_NAMES[after_record.bet]), tr(VERDICTS[bet_class()])]
		Wave.TWEETS:
			caption = tr("Твиты · %s") % tr(after_content.tag)
			for it in after_content.items:
				if it.kind == FeedContent.Kind.TWEET:
					text = it.text
					break
		Wave.STREAM:
			caption = tr("Стрим · %s") % tr(after_content.clip_person.name)
			text = (tr("%s онлайн · вирусный") if after_content.viral else tr("%s онлайн")) % FeedContent.format_count(after_content.online)
		Wave.CRITICS:
			if after_record.bet_done:
				text = _score(after_content.critics_avg) + " · " + tr(VERDICTS[bet_class()])
				mono = true
			else:
				caption = "Критики · рецензии вышли"
				text = "Открыть оценки"
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
	var l := _label("Жанр или технология", Style.FONT_BODY, Style.SURFACE_SOLID)
	l.add_theme_font_override("font", Jelly.fun_font(800))
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	p.add_child(l)
	_offer_halo = Panel.new()
	_offer_halo.show_behind_parent = true
	_offer_halo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_offer_halo.add_theme_stylebox_override("panel", Style.flat(Style.SUCCESS, Style.R_PILL, Color.TRANSPARENT, 0))
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


## Фокус: кнопки и пилюли тёмные с белым текстом, карточки волн на бортике, под статуэткой
## пилюля с названием игры.
func _refresh_focus() -> void:
	_refresh_tip()
	for i in _focusables.size():
		var on := i == focus
		if _lifts[i] != null:
			_lifts[i].focused = on
		if _box_focus.has(i) or _wave_focus.has(i):
			continue
		var c := _focusables[i] as PanelContainer
		if i == _studio_index:
			var hs := Style.flat(Style.INK if on else Style.SURFACE, Style.R_PILL, Color.TRANSPARENT, 0)
			hs.content_margin_left = 14 if ShellHeader.studio != "" else 20
			hs.content_margin_right = 20
			hs.content_margin_top = 6
			hs.content_margin_bottom = 6
			c.add_theme_stylebox_override("panel", hs)
			_studio_label.add_theme_color_override("font_color", Style.SURFACE_SOLID if on else Style.INK_2)
			continue
		var radius := Style.R_PILL if i != _new_index else Style.R_CTL
		var bg := Style.INK if on else Style.SURFACE_SOLID
		if i == _offer_index:
			bg = Style.SUCCESS.darkened(0.3) if on else Style.SUCCESS
		elif i == _new_index:
			# Главная кнопка экрана фирменным красным (2026-11-18), в фокусе темнее.
			bg = Style.ACCENT.darkened(0.25) if on else Style.ACCENT
		var sb := Style.flat(bg, radius, Color.TRANSPARENT, 0)
		sb.content_margin_left = 24
		sb.content_margin_right = 24
		c.add_theme_stylebox_override("panel", sb)
		var l := _labels[i]
		var base := Style.INK
		if i == _money_index:
			base = Style.DANGER if run.wallet.cash < 0 else Style.MONEY
		elif i == _offer_index or i == _new_index:
			base = Style.SURFACE_SOLID
		l.add_theme_color_override("font_color", Style.SURFACE_SOLID if on else base)


## Пилюля с названием игры под статуэткой в фокусе; под окном её нет.
func _refresh_tip() -> void:
	if _box_tip == null or not is_instance_valid(_box_tip):
		return
	var on := _box_focus.has(focus) and window == Pop.NONE
	_box_tip.visible = on
	if not on:
		return
	var record := run.records[_box_focus[focus]]
	var text := record.title
	if record.score != null:
		text += " · " + _score(record.score.critics)
	(_box_tip.get_child(0) as Label).text = text
	_box_tip.reset_size()
	var box := MouseUi.rect_of(_focusables[focus])
	# Под полкой: над ней ряд пилюль шапки.
	_box_tip.position = Vector2(box.get_center().x - _box_tip.size.x / 2.0, box.end.y + BOX_TIP_GAP).floor()


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
