class_name StudioBackdrop
extends Control
## Пиксельная студия на фоне (#80, STYLE «Студия», спека `docs/specs/studio.md`): одна комната в
## три четверти на весь экран, один цвет `studio-ink` в трёх долях на фоне `bg`. Растёт со
## студией: стол и человечек на каждого из `StudioState.people` (до 12), предмет на каждую
## купленную прокачку (`UpgradeDef.prop`), незнакомый id ставит растение или коробки.
## Человечки копошатся: печатают, потягиваются, ходят за кофе, к соседу, к доске, спят во второй
## половине забега; тестировщик, менеджер и инсайдер заняты своим. Одно и то же состояние даёт
## одну и ту же картинку: раскладка без случайности, занятия от сида состояния.
##
## Как поставить: `var b := StudioBackdrop.new()`, `add_child(b)` первым ребёнком экрана,
## `b.set_anchors_preset(Control.PRESET_FULL_RECT)`, затем `b.set_studio(run.studio, run.release,
## run.start_tech, run.start_genre)` после каждой покупки. Мышь не ловит. Рисует свой фон `bg`.
## Арт в `StudioSprites`, числа в `resources/studio_backdrop.tres`.

## Холст арта: 1920×1080 при пикселе 4.
const ART := Vector2i(480, 270)
## Низ стены, по нему пол. Предметы у стены стоят основанием на `BACK_Y`.
const WALL_Y := 52
const BACK_Y := 58
## Где стоят у предметов у стены, и дорожка вдоль стены.
const SPOT_Y := 64
const TOP_LANE := 70
## Столы: левые края колонок, низы рядов, порядок заполнения [ряд, колонка]: с середины,
## потом вправо, левая группа последней (#77: слева на главном экране столбик релизов).
const DESK_X: Array[int] = [40, 64, 160, 184, 280, 304]
const DESK_BASE: Array[int] = [116, 196]
const DESK_ORDER := [[0, 2], [0, 3], [1, 2], [1, 3], [0, 4], [0, 5], [1, 4], [1, 5], [0, 0], [0, 1], [1, 0], [1, 1]]
const DESK_W := 22
## Стул под столом: низ сидящего ниже низа стола.
const SEAT_DY := 7
## Проходы между группами столов.
const CORRIDORS: Array[int] = [26, 124, 244, 342]
## Стол тестировщика (левый край, низ) справа от групп столов.
const QA_DESK := Vector2i(376, 196)
## Диван в углу, когда людей набралось на полкомнаты (левый край, низ).
const SOFA := Vector2i(398, 250)
const SOFA_FROM_PEOPLE := 6
## Стена: окна, плакаты по `Game.Genre`, часы, доска (левые верхние углы).
const WINDOWS: Array[Vector2i] = [Vector2i(52, 8), Vector2i(148, 8), Vector2i(318, 8)]
const POSTERS: Array[Vector2i] = [Vector2i(92, 14), Vector2i(108, 14), Vector2i(124, 14), Vector2i(190, 14), Vector2i(206, 14)]
const CLOCK := Vector2i(226, 12)
const BOARD := Vector2i(242, 16)
const DOOR := Vector2i(446, 18)
## У стены на полу (левый край): полка, шкаф, кофемашина, стойка с техникой, сервер.
const SHELF_X := 6
const CABINET_X := 26
const COFFEE_X := 296
const TECH_X: Array[int] = [357, 370, 385, 404]
const SERVER_X := 424
## Места для незнакомых прокачек: середина низа, по кругу.
const GENERIC_SLOTS: Array[Vector2i] = [
	Vector2i(468, 252), Vector2i(12, 252), Vector2i(220, 252), Vector2i(468, 140),
	Vector2i(100, 252), Vector2i(12, 150), Vector2i(340, 252), Vector2i(468, 196),
]
## Мелочь на столах по кругу; пустая строка это пустой угол.
const DESK_STUFF: Array[String] = ["mug", "papers", "", "lamp", "mug", "plant_mini", "papers", ""]
const GENERIC_SPRITES: Array[String] = ["plant", "plant_tall", "boxes"]
const TECH_SPRITES: Array[String] = ["tech_ascii", "tech_bit8", "tech_bit16", "tech_lowpoly", "tech_server"]
const POSTER_SPRITES: Array[String] = ["poster_platformer", "poster_racing", "poster_shooter", "poster_sport", "poster_fighting"]
## Возможности со своим предметом; остальные id без `UpgradeDef` идут в общие места.
const KNOWN_CAPS: Array[StringName] = [&"replay", &"replay2", &"sequels", &"remakes", &"qa", &"insider", &"manager"]

enum Role { DESK, TESTER, MANAGER, INSIDER }
enum Act { TYPE, STRETCH, SLEEP, WALK, COFFEE, BOARD, VISIT, POST, TWITCH }

## Анимация. Учитывает и выключатель движения мармелада (`Jelly.enabled`): без него студия стоит
## в спокойной позе (все за столами), раскладка та же.
@export var animate := true:
	set(v):
		animate = v
		queue_redraw()
## Спринт идёт: печатают быстрее.
var busy := false
## Сила чернил: 1 по STYLE, меньше тише (под модальными карточками).
var strength := 1.0:
	set(v):
		strength = clampf(v, 0.0, 1.0)
		queue_redraw()

var tuning: StudioBackdropTuning

## Статичные предметы: на стене (без глубины) и на полу (сортируются с человечками по низу).
var _wall: Array[Item] = []
var _floor: Array[Item] = []
var _desks: Array[Desk] = []
var _workers: Array[Worker] = []
var _signature := ""
var _release := 1
var _time := 0.0
var _react: StringName = &""
var _react_left := 0.0
var _door_spot := Vector2(DOOR.x + 10, SPOT_Y)
var _coffee_spot := Vector2(COFFEE_X + 5, SPOT_Y)
var _board_spot := Vector2(BOARD.x + 19, SPOT_Y)
var _window_spot := Vector2(WINDOWS[2].x + 15, SPOT_Y)
var _has_board := false


class Item:
	var sprite := ""
	var pos := Vector2i.ZERO
	var base := 0
	## Монитор стола: кадр выбирает владелец стола.
	var desk := -1
	## Кадры по кругу (сервер мигает).
	var frames: PackedStringArray = []
	var frame_seconds := 0.0


class Desk:
	var x := 0
	var base := 0
	var seat := Vector2.ZERO
	var lane := 0.0
	var owner: Worker
	var qa := false


class Worker:
	var role := Role.DESK
	var desk := -1
	var home := Vector2.ZERO
	var home_lane := 0.0
	var pos := Vector2.ZERO
	var lane := 0.0
	var path: Array[Vector2] = []
	var act := Act.TYPE
	var after := Act.TYPE
	var after_seconds := 0.0
	var timer := 0.0
	var anim := 0.0
	var cup := false
	var visit_desk := -1
	var visit_len := 0.0
	var jitter := 0
	## Новичок ещё за дверью: секунды до входа.
	var delay := 0.0
	var rng := RandomNumberGenerator.new()

	func seated() -> bool:
		return act == Act.TYPE or act == Act.STRETCH or act == Act.SLEEP or act == Act.TWITCH


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	clip_contents = true
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	tuning = StudioBackdropTuning.load_default()


func _ready() -> void:
	_default_studio.call_deferred()


## Пустая студия, если хозяин так и не позвал `set_studio` в том же кадре.
func _default_studio() -> void:
	if _signature == "":
		set_studio(StudioState.new(), 1)


# --- API -----------------------------------------------------------------------------------

## Студия по состоянию забега. Без изменений состояния ничего не сбрасывает; новые люди входят
## в дверь и идут к своим столам. `start_tech` и `start_genre` (стартовая пара, -1 нет) ставят
## свою технику и плакат, как купленные.
func set_studio(state: StudioState, release := 1, start_tech := -1, start_genre := -1) -> void:
	var sig := "%s|%d|%d|%d" % [state.upgrade_ids, state.people, start_tech, start_genre]
	_release = release
	if sig == _signature:
		return
	var had := _signature != ""
	var old_desk_workers := 0
	for w in _workers:
		if w.role == Role.DESK:
			old_desk_workers += 1
	var old_specials: Array[Role] = []
	for w in _workers:
		if w.role != Role.DESK:
			old_specials.append(w.role)
	_signature = sig
	_build(state, start_tech, start_genre)
	_spawn(sig.hash(), had, old_desk_workers, old_specials)
	queue_redraw()


## Реакция студии на событие (спека): `&"release"` все встают и машут, `&"viral"` прыгают
## (обе на `react_seconds`), `&"broke"` все сидят неподвижно, пока не придёт `&""`.
func react(kind: StringName) -> void:
	_react = kind
	_react_left = tuning.react_seconds
	if kind == &"broke":
		for w in _workers:
			_home_now(w)
	queue_redraw()


## Между спринтами: один из печатающих встаёт и что-нибудь делает.
func nudge() -> void:
	for w in _workers:
		if w.role == Role.DESK and w.act == Act.TYPE:
			_choose(w, true)
			return


func moving() -> bool:
	return animate and Jelly.enabled


func people_count() -> int:
	return _workers.size()


func prop_count() -> int:
	return _wall.size() + _floor.size()


func walking_count() -> int:
	var n := 0
	for w in _workers:
		if w.act == Act.WALK:
			n += 1
	return n


## Снимок раскладки и поз строкой: для проверки одинаковости в тестовой сцене.
func layout_dump() -> String:
	var parts: PackedStringArray = []
	for it in _wall:
		parts.append("%s@%s" % [it.sprite, it.pos])
	for it in _floor:
		parts.append("%s@%s" % [it.sprite, it.pos])
	for w in _workers:
		parts.append("%d:%d@%s" % [w.role, w.act, w.pos.round()])
	return " ".join(parts)


# --- Раскладка -----------------------------------------------------------------------------

func _build(state: StudioState, start_tech: int, start_genre: int) -> void:
	_wall.clear()
	_floor.clear()
	_desks.clear()
	var pool := UpgradePool.load_all()
	var techs := {}
	var genres := {}
	var caps := {}
	var generic: Array[StringName] = []
	if start_tech >= 0:
		techs[start_tech] = true
	if start_genre >= 0:
		genres[start_genre] = true
	for id in state.upgrade_ids:
		var def := UpgradePool.find(pool, id)
		if def != null and def.kind == UpgradeDef.Kind.TECH:
			techs[int(def.tech)] = true
		elif def != null and def.kind == UpgradeDef.Kind.GENRE:
			genres[int(def.genre)] = true
		elif KNOWN_CAPS.has(id):
			caps[id] = true
		else:
			generic.append(id)
	var specials := int(caps.has(&"qa")) + int(caps.has(&"manager")) + int(caps.has(&"insider"))
	var desk_people := clampi(state.people - specials, 1, DESK_ORDER.size())
	_has_board = desk_people >= 3

	# Стена.
	for w in WINDOWS:
		_add_wall("window", w)
	_add_wall("clock", CLOCK)
	_add_wall("door", DOOR)
	if _has_board:
		_add_wall("whiteboard", BOARD)
	for g in genres:
		_add_wall(POSTER_SPRITES[g] if g < POSTER_SPRITES.size() else "poster_any", POSTERS[g % POSTERS.size()])

	# У стены.
	_add_floor("coffee", Vector2i(COFFEE_X, BACK_Y))
	if caps.has(&"sequels"):
		_add_floor("shelf", Vector2i(SHELF_X, BACK_Y))
	if caps.has(&"remakes"):
		_add_floor("cabinet", Vector2i(CABINET_X, BACK_Y))
	var left := 9999
	var right := -1
	for t in techs:
		if t < 4:
			left = mini(left, TECH_X[t] - 1)
			right = maxi(right, TECH_X[t] + _size(TECH_SPRITES[t]).x + 1)
	if right > 0:
		_add_floor("counter:%d" % (right - left), Vector2i(left, BACK_Y))
	if desk_people >= SOFA_FROM_PEOPLE:
		_add_floor("sofa", SOFA)
	for t in techs:
		if t < 4:
			var it := _add_floor(TECH_SPRITES[t], Vector2i(TECH_X[t], BACK_Y - 3))
			it.base = BACK_Y + 1
		elif t < TECH_SPRITES.size():
			var srv := _add_floor("tech_server", Vector2i(SERVER_X, BACK_Y))
			srv.frames = PackedStringArray(["tech_server", "tech_server_b"])
			srv.frame_seconds = 0.9

	# Столы.
	for i in desk_people:
		var rc: Array = DESK_ORDER[i]
		_add_desk(DESK_X[rc[1]], DESK_BASE[rc[0]], false)
	if caps.has(&"qa"):
		_add_desk(QA_DESK.x, QA_DESK.y, true)
	if caps.has(&"replay"):
		var d0 := _desks[0]
		_add_floor("monitor_side_l", Vector2i(d0.x + 0, d0.base - 6)).base = d0.base + 1
	if caps.has(&"replay2"):
		var d0 := _desks[0]
		_add_floor("monitor_side_r", Vector2i(d0.x + 16, d0.base - 6)).base = d0.base + 1

	# Незнакомые прокачки.
	for i in generic.size():
		var slot := GENERIC_SLOTS[i % GENERIC_SLOTS.size()]
		var shift := (i / GENERIC_SLOTS.size()) * 10
		var spr := GENERIC_SPRITES[absi(String(generic[i]).hash()) % GENERIC_SPRITES.size()]
		var size := _size(spr)
		_add_floor(spr, Vector2i(slot.x - size.x / 2 - shift, slot.y))

	_specials.clear()
	if caps.has(&"qa"):
		_specials.append(Role.TESTER)
	if caps.has(&"manager"):
		_specials.append(Role.MANAGER)
	if caps.has(&"insider"):
		_specials.append(Role.INSIDER)
	_desk_people = desk_people


var _specials: Array[Role] = []
var _desk_people := 1


func _add_wall(sprite: String, pos: Vector2i) -> Item:
	var it := Item.new()
	it.sprite = sprite
	it.pos = pos
	_wall.append(it)
	return it


## Предмет на полу: `at` это левый край и низ.
func _add_floor(sprite: String, at: Vector2i) -> Item:
	var it := Item.new()
	it.sprite = sprite
	var s := _size(sprite)
	it.pos = Vector2i(at.x, at.y - s.y)
	it.base = at.y
	_floor.append(it)
	return it


func _add_desk(x: int, base: int, qa: bool) -> void:
	var d := Desk.new()
	d.x = x
	d.base = base
	d.seat = Vector2(x + DESK_W / 2, base + SEAT_DY)
	d.lane = base + SEAT_DY + 8
	d.qa = qa
	_desks.append(d)
	_add_floor("desk", Vector2i(x, base))
	var mon := _add_floor("monitor", Vector2i(x + 6, base - 6))
	mon.base = base + 1
	mon.desk = _desks.size() - 1
	if qa:
		_add_floor("gamepad", Vector2i(x + 16, base - 6)).base = base + 1
	else:
		# Мелочь на столе по номеру стола: одинаковая для одного состояния, разная у соседей.
		var n := _desks.size() - 1
		var stuff: String = DESK_STUFF[(n * 7 + 3) % DESK_STUFF.size()]
		if stuff != "":
			var right := n % 2 == 1
			var sz := _size(stuff)
			var sx := x + DESK_W - 2 - sz.x if right else x + 2
			_add_floor(stuff, Vector2i(sx, base - 5)).base = base + 1


func _size(sprite: String) -> Vector2i:
	var rows := StudioSprites.rows_of(sprite)
	var w := 0
	for r in rows:
		w = maxi(w, (r as String).length())
	return Vector2i(w, rows.size())


# --- Человечки ------------------------------------------------------------------------------

func _spawn(seed_: int, had: bool, old_desk: int, old_specials: Array[Role]) -> void:
	_workers.clear()
	var qa_desk := -1
	for i in _desks.size():
		if _desks[i].qa:
			qa_desk = i
	var n := 0
	for i in _desks.size():
		if _desks[i].qa:
			continue
		var w := _new_worker(Role.DESK, seed_, n)
		w.desk = i
		w.home = _desks[i].seat
		w.home_lane = _desks[i].lane
		_desks[i].owner = w
		_place_new(w, had and n >= old_desk, maxf(0.0, n - old_desk) * 1.5)
		n += 1
	for r in _specials:
		var w := _new_worker(r, seed_, 100 + int(r))
		match r:
			Role.TESTER:
				w.desk = qa_desk
				w.home = _desks[qa_desk].seat
				w.home_lane = _desks[qa_desk].lane
				_desks[qa_desk].owner = w
			Role.MANAGER:
				w.home = _door_spot
				w.home_lane = TOP_LANE
			Role.INSIDER:
				w.home = _window_spot
				w.home_lane = TOP_LANE
		_place_new(w, had and not old_specials.has(r), maxf(0.0, n - old_desk) * 1.5 + 1.0)


func _new_worker(role: Role, seed_: int, index: int) -> Worker:
	var w := Worker.new()
	w.role = role
	w.rng.seed = hash([seed_, index])
	w.anim = w.rng.randf() * 4.0
	_workers.append(w)
	return w


## Поставить на пост; новенький входит в дверь и идёт туда сам.
func _place_new(w: Worker, from_door: bool, delay: float) -> void:
	_home_now(w)
	w.timer = w.rng.randf_range(1.0, tuning.type_max)
	if from_door:
		w.delay = delay
		w.pos = _door_spot
		w.lane = TOP_LANE
		_walk(w, w.home, w.home_lane, _post_act(w), w.timer)


func _post_act(w: Worker) -> Act:
	match w.role:
		Role.TESTER:
			return Act.TWITCH
		Role.MANAGER, Role.INSIDER:
			return Act.POST
	return Act.TYPE


func _home_now(w: Worker) -> void:
	w.pos = w.home
	w.lane = w.home_lane
	w.path.clear()
	w.cup = false
	w.delay = 0.0
	w.act = _post_act(w)
	w.timer = w.rng.randf_range(tuning.type_min, tuning.type_max)


func _process(delta: float) -> void:
	if not moving() or _workers.is_empty():
		return
	_time += delta
	if _react != &"":
		if _react != &"broke":
			_react_left -= delta
			if _react_left <= 0.0:
				_react = &""
		queue_redraw()
		return
	for w in _workers:
		w.anim += delta
		_tick(w, delta)
	queue_redraw()


func _tick(w: Worker, delta: float) -> void:
	if w.delay > 0.0:
		w.delay -= delta
		return
	if w.act == Act.WALK:
		var step := tuning.walk_speed * delta
		while step > 0.0 and not w.path.is_empty():
			var to := w.path[0]
			var d := w.pos.distance_to(to)
			if d <= step:
				w.pos = to
				step -= d
				w.path.remove_at(0)
			else:
				w.pos = w.pos.move_toward(to, step)
				step = 0.0
		if w.path.is_empty():
			w.act = w.after
			w.timer = w.after_seconds
			if w.pos == w.home:
				w.cup = false
		return
	w.timer -= delta
	if w.act == Act.TWITCH:
		if w.rng.randf() < delta * 1.5:
			w.jitter = w.rng.randi_range(-1, 1)
		return
	if w.timer > 0.0:
		return
	match w.act:
		Act.TYPE:
			_choose(w, false)
		Act.STRETCH, Act.SLEEP:
			w.act = Act.TYPE
			w.timer = w.rng.randf_range(tuning.type_min, tuning.type_max)
		Act.COFFEE:
			w.cup = true
			_walk(w, w.home, w.home_lane, Act.TYPE, w.rng.randf_range(tuning.type_min, tuning.type_max))
		Act.BOARD, Act.VISIT:
			_walk(w, w.home, w.home_lane, Act.TYPE, w.rng.randf_range(tuning.type_min, tuning.type_max))
		Act.POST:
			_next_post(w)


## Следующее занятие печатающего, взвешенно по спеке. `away` не даёт снова сесть печатать.
func _choose(w: Worker, away: bool) -> void:
	var others := _desk_neighbours(w)
	var weights := [
		0.0 if away else tuning.w_type,
		tuning.w_stretch,
		tuning.w_coffee,
		tuning.w_visit if not others.is_empty() else 0.0,
		tuning.w_board if _has_board or not _wall_posters().is_empty() else 0.0,
		tuning.w_sleep if _release >= tuning.sleep_from_release and not away else 0.0,
	]
	var total := 0.0
	for x in weights:
		total += x
	var roll := w.rng.randf() * total
	var pick := 0
	for i in weights.size():
		roll -= weights[i]
		if roll <= 0.0:
			pick = i
			break
	match pick:
		0:
			w.act = Act.TYPE
			w.timer = w.rng.randf_range(tuning.type_min, tuning.type_max)
		1:
			w.act = Act.STRETCH
			w.timer = tuning.stretch_seconds
		2:
			_walk(w, _coffee_spot, TOP_LANE, Act.COFFEE, tuning.coffee_seconds)
		3:
			var d: Desk = _desks[others[w.rng.randi_range(0, others.size() - 1)]]
			w.visit_desk = _desks.find(d)
			w.visit_len = tuning.visit_seconds
			var side := -7.0 if DESK_X.find(d.x) % 2 == 0 else 7.0
			_walk(w, Vector2(d.seat.x + side, d.seat.y + 4), d.lane, Act.VISIT, tuning.visit_seconds)
		4:
			var spot := _board_spot
			if not _has_board:
				var posters := _wall_posters()
				var p: Item = posters[w.rng.randi_range(0, posters.size() - 1)]
				spot = Vector2(p.pos.x + 6, SPOT_Y)
			_walk(w, spot, TOP_LANE, Act.BOARD, tuning.board_seconds)
		5:
			w.act = Act.SLEEP
			w.timer = tuning.sleep_seconds


func _desk_neighbours(w: Worker) -> Array[int]:
	var out: Array[int] = []
	for i in _desks.size():
		var o := _desks[i].owner
		if o != null and o != w and o.role == Role.DESK and o.act == Act.TYPE:
			out.append(i)
	return out


func _wall_posters() -> Array[Item]:
	var out: Array[Item] = []
	for it in _wall:
		if it.sprite.begins_with("poster"):
			out.append(it)
	return out


## Менеджер обходит столы и возвращается к двери; инсайдер переминается у окна.
func _next_post(w: Worker) -> void:
	match w.role:
		Role.MANAGER:
			var desk_ids: Array[int] = []
			for i in _desks.size():
				desk_ids.append(i)
			if desk_ids.is_empty() or (w.pos != w.home and w.rng.randf() < 0.25):
				_walk(w, w.home, w.home_lane, Act.POST, tuning.manager_stop_seconds)
				return
			var d := _desks[desk_ids[w.rng.randi_range(0, desk_ids.size() - 1)]]
			_walk(w, Vector2(d.seat.x - 7.0, d.seat.y + 4), d.lane, Act.POST, tuning.manager_stop_seconds)
		Role.INSIDER:
			var x := w.home.x + float(w.rng.randi_range(-3, 3))
			_walk(w, Vector2(x, w.home.y), w.home_lane, Act.POST, w.rng.randf_range(3.0, 7.0))


## Маршрут по дорожкам: вниз на свою дорожку, по ней к проходу, по проходу на дорожку цели, к цели.
func _walk(w: Worker, to: Vector2, to_lane: float, then: Act, seconds: float) -> void:
	var pts: Array[Vector2] = [Vector2(w.pos.x, w.lane)]
	if not is_equal_approx(w.lane, to_lane):
		var best := CORRIDORS[0]
		for c in CORRIDORS:
			if absf(w.pos.x - c) + absf(to.x - c) < absf(w.pos.x - best) + absf(to.x - best):
				best = c
		# Справа от столов пол свободен: проход не нужен.
		if minf(w.pos.x, to.x) > QA_DESK.x + DESK_W:
			best = int(minf(w.pos.x, to.x))
		pts.append(Vector2(best, w.lane))
		pts.append(Vector2(best, to_lane))
	pts.append(Vector2(to.x, to_lane))
	pts.append(to)
	w.path.clear()
	var prev := w.pos
	for p in pts:
		if p.distance_to(prev) > 0.01:
			w.path.append(p)
			prev = p
	w.lane = to_lane
	w.act = Act.WALK
	w.after = then
	w.after_seconds = seconds


# --- Рисование ------------------------------------------------------------------------------

## Целый пиксель арта под размер: 4 на 1920×1080 (STYLE), меньше в превью-сетке.
func _px() -> float:
	return maxf(1.0, floorf(minf(size.x / ART.x, size.y / ART.y)))


func _tex(sprite: String) -> Texture2D:
	return StudioSprites.texture(sprite, tuning.tones, strength, tuning.people_tone)


func _draw() -> void:
	var colors := StudioSprites.tone_colors(tuning.tones, strength, tuning.people_tone)
	draw_rect(Rect2(Vector2.ZERO, size), Style.BG)
	var px := _px()
	var origin := ((size - Vector2(ART) * px) / 2.0).floor()
	draw_set_transform(origin, 0.0, Vector2(px, px))
	# Стена светлым тоном, плинтус средним, линия пола.
	draw_rect(Rect2(-ART.x, -ART.y, ART.x * 3, ART.y + WALL_Y - 3), colors["-"])
	draw_rect(Rect2(-ART.x, WALL_Y - 3, ART.x * 3, 2), colors["+"])
	draw_rect(Rect2(-ART.x, WALL_Y - 1, ART.x * 3, 1), colors["#"])
	# Пол: редкая сетка точек в шахматку.
	for row in range(0, (ART.y - WALL_Y) / 12 + 1):
		var y := WALL_Y + 8 + row * 12
		for col in range(0, ART.x / 16 + 1):
			var x := col * 16 + (8 if row % 2 == 1 else 0) + 4
			draw_rect(Rect2(x, y, 1, 1), colors["+"])
	for it in _wall:
		draw_texture(_tex(it.sprite), Vector2(it.pos) + StudioSprites.offset(it.sprite))
	var list: Array = []
	var order := 0
	for it in _floor:
		list.append([it.base, order, _item_sprite(it), Vector2(it.pos)])
		order += 1
	for w in _workers:
		order = _queue_worker(list, w, order)
	list.sort_custom(func(a: Array, b: Array) -> bool:
		return a[0] < b[0] or (a[0] == b[0] and a[1] < b[1]))
	for e in list:
		if e[2] != "":
			draw_texture(_tex(e[2]), e[3] + StudioSprites.offset(e[2]))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _item_sprite(it: Item) -> String:
	if it.desk >= 0:
		return _monitor_sprite(it.desk)
	if not it.frames.is_empty() and moving():
		return it.frames[int(_time / it.frame_seconds) % it.frames.size()]
	return it.sprite


func _monitor_sprite(desk: int) -> String:
	var d := _desks[desk]
	var w := d.owner
	var game := d.qa
	if not moving() or w == null:
		return "monitor_game_a" if game else "monitor_a"
	var phase := int((_time + w.anim) / tuning.screen_seconds) % 2
	if game:
		return "monitor_game_a" if phase == 0 else "monitor_game_b"
	if w.act == Act.SLEEP:
		return "monitor_off"
	if w.pos != w.home or w.act == Act.STRETCH:
		return "monitor"
	return "monitor_a" if phase == 0 else "monitor_b"


## Поза человечка и мелочь при нём в общий список глубины. Возвращает следующий порядковый.
func _queue_worker(list: Array, w: Worker, order: int) -> int:
	if w.delay > 0.0 and moving() and _react != &"broke":
		if w.desk >= 0:
			var s0 := _desks[w.desk].seat
			list.append([s0.y, order, "chair", Vector2(s0.x - 4, s0.y - 4).floor()])
			order += 1
		return order
	var pose := "stand"
	var extra: Array = []
	var pos := w.pos
	var lift := 0.0
	var at_home := w.pos == w.home
	if not moving() or _react == &"broke":
		pos = w.home
		match w.role:
			Role.DESK, Role.TESTER:
				pose = "sit0"
			Role.MANAGER:
				pose = "stand"
				extra.append(["tablet", Vector2(6, 4)])
			Role.INSIDER:
				pose = "hand_head"
				extra.append(["phone", Vector2(7, -1)])
	elif _react == &"release":
		pose = "wave0" if int((_time + w.anim) / 0.3) % 2 == 0 else "wave1"
	elif _react == &"viral":
		pose = "stand"
		lift = absf(sin((_time + w.anim * 0.1) * PI / tuning.jump_seconds)) * tuning.jump_height
	else:
		var tick := tuning.type_seconds_busy if busy else tuning.type_seconds
		match w.act:
			Act.TYPE:
				pose = "sit1" if int(w.anim / tick) % 2 == 0 else "sit2"
			Act.TWITCH:
				pose = "sit1" if int(w.anim / 0.1) % 2 == 0 else "sit2"
				pos.x += w.jitter
			Act.STRETCH:
				pose = "stretch"
			Act.SLEEP:
				pose = "sleep"
				extra.append(["zz", Vector2(6, -5 - float(int(w.anim / 0.6) % 3))])
			Act.WALK:
				pose = "walk0" if int(w.anim / tuning.step_seconds) % 2 == 0 else "walk1"
			Act.COFFEE:
				pose = "stand"
			Act.BOARD:
				pose = "hand_head"
			Act.VISIT:
				pose = "stand"
				# Говорят по очереди: сначала гость, потом сосед, если он на месте.
				var nd: Desk = _desks[w.visit_desk] if w.visit_desk >= 0 and w.visit_desk < _desks.size() else null
				var there := nd != null and nd.owner != null and nd.owner.pos == nd.seat and nd.owner.seated()
				if w.timer > w.visit_len * 0.5 or not there:
					extra.append(["bubble", Vector2(5, -6)])
				else:
					list.append([nd.seat.y + 0.5, order, "bubble", (nd.seat + Vector2(1, -14)).floor()])
					order += 1
			Act.POST:
				if w.role == Role.MANAGER:
					pose = "stand"
				else:
					pose = "hand_head"
		if w.cup:
			extra.append(["cup", Vector2(7, 4)])
		if w.role == Role.MANAGER:
			extra.append(["tablet", Vector2(6, 4)])
		if w.role == Role.INSIDER and w.act == Act.POST:
			extra.append(["phone", Vector2(7, -1)])
	# Пустой стул, пока хозяин стола не сидит.
	if w.desk >= 0 and not (at_home and w.seated()) and moving() and _react != &"broke":
		var seat := _desks[w.desk].seat
		list.append([seat.y, order, "chair", Vector2(seat.x - 4, seat.y - 4).floor()])
		order += 1
	var s := _size(pose)
	var top := Vector2(roundf(pos.x) - 4, roundf(pos.y - lift) - s.y)
	list.append([pos.y + 0.25, order, pose, top])
	order += 1
	for x in extra:
		list.append([pos.y + 0.3, order, x[0], top + x[1]])
		order += 1
	return order
