class_name StudioBackdrop
extends Control
## Пиксельная студия на фоне (#80, STYLE «Студия», спека `docs/specs/studio.md`): одна комната в
## три четверти на весь экран, мебель одним цветом `studio-ink` в трёх долях на фоне `bg`,
## человечки в своих приглушённых цветах с глазами. Растёт со студией: стол и человечек на
## каждого из `StudioState.people` (до 12), предмет на каждую купленную прокачку
## (`UpgradeDef.prop`), незнакомый id ставит растение или коробки. Человечки копошатся:
## печатают, потягиваются, ходят за кофе, к соседу, к доске, спят во второй половине забега;
## тестировщик, менеджер и инсайдер заняты своим. Одно и то же состояние даёт одну и ту же
## картинку: раскладка и облики без случайности, занятия от сида состояния.
##
## Как поставить: `var b := StudioBackdrop.new()`, `add_child(b)` первым ребёнком экрана,
## `b.set_anchors_preset(Control.PRESET_FULL_RECT)`, затем `b.set_studio(run.studio, run.release,
## run.start_tech, run.start_genre)` после каждой покупки. Как Control мышь не ловит, но сама
## смотрит нажатия: человечка, над которым нет оболочки, можно утащить, а кулер, телевизор и
## часы нажать (раздел «Мышь»). За окнами идут сутки (`StudioDaylight`, раздел «День и ночь»):
## небо, свет из окон на полу, лёгкий оттенок всей комнаты. Рисует свой фон `bg`.
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
const WINDOWS: Array[Vector2i] = [Vector2i(46, 4), Vector2i(142, 4), Vector2i(302, 4)]
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
enum Act { TYPE, STRETCH, SLEEP, WALK, COFFEE, BOARD, VISIT, POST, TWITCH, HELD, WAIT, FALL }
const ACT_NAMES: Array[String] = ["type", "stretch", "sleep", "walk", "coffee", "board", "visit", "post",
		"twitch", "held", "wait", "fall"]
## Нажимаемые предметы (раздел «Мышь»).
const PROPS: Array[StringName] = [&"cooler", &"tv", &"clock"]
## Куда можно поставить: пол без полосы у стены и края.
const FLOOR_RECT := Rect2(6, WALL_Y + 12, ART.x - 12, ART.y - WALL_Y - 14)

## Анимация. Учитывает и выключатель движения мармелада (`Jelly.enabled`): без него студия стоит
## в спокойной позе (все за столами), раскладка та же.
@export var animate := true:
	set(v):
		animate = v
		queue_redraw()
## Спринт идёт: печатают быстрее.
var busy := false
## Человечков можно таскать мышью (плейтест 2026-11-11), если над ними нет оболочки.
var drag_enabled := true
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
var _window_spot := Vector2(WINDOWS[2].x + StudioSprites.WINDOW_SIZE.x / 2, SPOT_Y)
var _has_board := false
## Кого тащат, где курсор (пиксели арта) и где ноги относительно курсора; какой курсор мы
## выставили.
var _drag: Worker
var _drag_at := Vector2.ZERO
var _grab := Vector2.ZERO
var _cursor := Input.CURSOR_ARROW
## Время суток: 0..1 от полуночи стоит на месте (тестовая сцена `--daytime`, дебаг-меню),
## меньше 0 сутки идут от часов студии `_day_clock`. `_day_shift` часы, накрученные нажатием на
## часы, `_spin_left` сколько ещё крутить.
var daytime := -1.0:
	set(v):
		daytime = v
		queue_redraw()
var _day_clock := 0.0
var _day_shift := 0.0
var _spin_left := 0.0
var _drawn_hour := -1.0
## Нажимаемые предметы этой раскладки (null, если нет) и их анимации: возраст пузырей кулера,
## канал телевизора и сколько идёт переключение (меньше 0 не идёт).
var _cooler: Item
var _tv: Item
var _clock: Item
var _bubbles: Array[float] = []
var _tv_channel := 0
var _tv_age := -1.0
var _sounds := {}
static var _streams := {}
## Сетка через пиксель (лучи света, полоса горизонта): рисуется кусками размером с холст арта.
static var _checker: Texture2D
## Цвета мебели и обликов при текущей силе чернил: ключ кеша текстур -> словарь.
var _palettes := {}


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
	## Облик: рубашка, кожа, волосы (индексы в тюнинге; рубашка -1 у менеджера пиджак).
	var look := Vector3i.ZERO
	## Поставлен мышью: стоит, где отпустили (при выключенном движении так и остаётся).
	var placed := false
	## Над полом (пиксели арта), скорость падения вниз, сплющен ещё столько секунд, уже отскочил.
	var lift := 0.0
	var vy := 0.0
	var squash := 0.0
	var bounced := false
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
	_end_drag()
	_build(state, start_tech, start_genre)
	_spawn(sig.hash(), had, old_desk_workers, old_specials)
	queue_redraw()


## Реакция студии на событие (спека): `&"release"` все встают и машут, `&"viral"` прыгают
## (обе на `react_seconds`), `&"broke"` все сидят неподвижно, пока не придёт `&""`.
func react(kind: StringName) -> void:
	_react = kind
	_react_left = tuning.react_seconds
	if kind == &"broke":
		_end_drag()
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
	_cooler = null
	_tv = null
	_clock = null
	_tv_channel = 0
	_tv_age = -1.0
	_bubbles.clear()
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
	_clock = _add_wall("clock", CLOCK)
	_add_wall("door", DOOR)
	if _has_board:
		_add_wall("whiteboard", BOARD)
	for g in genres:
		_add_wall(POSTER_SPRITES[g] if g < POSTER_SPRITES.size() else "poster_any", POSTERS[g % POSTERS.size()])

	# У стены.
	_cooler = _add_floor("coffee", Vector2i(COFFEE_X, BACK_Y))
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
			if TECH_SPRITES[t] == "tech_bit8":
				_tv = it
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
		w.look = _look_for(i)
		w.desk = i
		w.home = _desks[i].seat
		w.home_lane = _desks[i].lane
		_desks[i].owner = w
		_place_new(w, had and n >= old_desk, maxf(0.0, n - old_desk) * 1.5)
		n += 1
	for r in _specials:
		var w := _new_worker(r, seed_, 100 + int(r))
		w.look = _look_for(20 + int(r))
		if r == Role.MANAGER:
			w.look.x = -1
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


## Облик по месту, без случайности: соседи по столам разные, одно место всегда одно лицо.
func _look_for(slot: int) -> Vector3i:
	return Vector3i((slot * 5 + 1) % tuning.shirts.size(), (slot * 7 + slot / 3) % tuning.skins.size(),
			(slot * 3 + 1) % tuning.hairs.size())


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
	w.placed = false
	w.lift = 0.0
	w.vy = 0.0
	w.squash = 0.0
	w.act = _post_act(w)
	w.timer = w.rng.randf_range(tuning.type_min, tuning.type_max)


func _process(delta: float) -> void:
	_day_clock += delta
	var props := _tick_props(delta)
	if not moving() or _workers.is_empty():
		var h := hour()
		if props or absf(fposmod(h - _drawn_hour + 12.0, 24.0) - 12.0) > 0.02:
			queue_redraw()
		return
	_time += delta
	if _drag != null:
		_drag.lift = move_toward(_drag.lift, tuning.lift_height, tuning.lift_height / tuning.lift_seconds * delta)
	for w in _workers:
		if w.act == Act.FALL or w.squash > 0.0:
			_fall(w, delta)
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
	if w.act == Act.HELD or w.act == Act.FALL:
		return
	w.timer -= delta
	if w.act == Act.WAIT:
		if w.timer <= 0.0:
			w.placed = false
			_walk(w, w.home, w.home_lane, _post_act(w), w.rng.randf_range(tuning.type_min, tuning.type_max))
		return
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


## Отпущенный падает на свою тень с ускорением, сплющивается на миг, один раз чуть отскакивает
## (если падал быстро), потом стоит и озирается (`WAIT`, `drop_seconds`).
func _fall(w: Worker, delta: float) -> void:
	if w.squash > 0.0:
		w.squash = maxf(0.0, w.squash - delta)
		if w.squash > 0.0 or w.act != Act.FALL:
			return
	if w.act != Act.FALL:
		return
	w.vy += tuning.gravity * delta
	w.lift -= w.vy * delta
	if w.lift > 0.0:
		return
	w.lift = 0.0
	w.squash = tuning.squash_seconds
	if not w.bounced and w.vy > tuning.bounce_min:
		w.bounced = true
		w.vy = -sqrt(2.0 * tuning.gravity * tuning.bounce_height)
	else:
		w.vy = 0.0
		w.act = Act.WAIT
		w.timer = tuning.drop_seconds


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
			var side := -9.0 if DESK_X.find(d.x) % 2 == 0 else 9.0
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
			_walk(w, Vector2(d.seat.x - 9.0, d.seat.y + 4), d.lane, Act.POST, tuning.manager_stop_seconds)
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


## Цвета мебели (без человечка) или облика человечка и ключ кеша текстур к ним.
func _palette(w: Worker = null) -> Array:
	var key := "f|%.3f" % strength
	if w != null:
		key = "w%s|%.3f" % [w.look, strength]
	if not _palettes.has(key):
		var furniture := StudioSprites.tone_colors(tuning.tones, strength)
		if w == null:
			_palettes[key] = furniture
		else:
			var shirt := tuning.manager_shirt if w.look.x < 0 else tuning.shirts[w.look.x]
			_palettes[key] = StudioSprites.worker_colors(furniture, shirt, tuning.skins[w.look.y],
					tuning.hairs[w.look.z], tuning.people_mix, tuning.pants_tone, tuning.eyes_tone, strength)
	return [_palettes[key], key]


## Для превью-листа: цвета мебели и обликов по рубашкам (кожа и волосы по кругу).
func sheet_image() -> Image:
	var looks: Array[Dictionary] = []
	for i in tuning.shirts.size() + 1:
		var w := Worker.new()
		w.look = Vector3i(i - 1, i % tuning.skins.size(), i % tuning.hairs.size())
		looks.append(_palette(w)[0])
	return StudioSprites.sheet(_palette()[0], looks)


func _tex(sprite: String, w: Worker = null) -> Texture2D:
	var p := _palette(w)
	return StudioSprites.texture(sprite, p[0], p[1])


func _origin() -> Vector2:
	return ((size - Vector2(ART) * _px()) / 2.0).floor()


func _draw() -> void:
	var colors: Dictionary = _palette()[0]
	draw_rect(Rect2(Vector2.ZERO, size), Style.BG)
	var px := _px()
	draw_set_transform(_origin(), 0.0, Vector2(px, px))
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
	var dl := StudioDaylight.at(tuning, hour())
	_drawn_hour = dl.hour
	_draw_sky(dl)
	_draw_light(dl)
	for it in _wall:
		draw_texture(_tex(it.sprite), Vector2(it.pos) + StudioSprites.offset(it.sprite))
	_draw_clock_hands(colors, dl.hour)
	var list: Array = []
	var order := 0
	for it in _floor:
		list.append([it.base, order, _item_sprite(it), Vector2(it.pos), null, it])
		order += 1
	for w in _workers:
		order = _queue_worker(list, w, order)
	list.sort_custom(func(a: Array, b: Array) -> bool:
		return a[0] < b[0] or (a[0] == b[0] and a[1] < b[1]))
	for e in list:
		if e[2] != "":
			draw_texture(_tex(e[2], e[4]), e[3] + StudioSprites.offset(e[2]))
		if e.size() > 5 and e[5] != null:
			if e[5] == _tv:
				_draw_tv(colors)
			elif e[5] == _cooler:
				_draw_bubbles(colors)
	var amb := dl.ambient
	if amb.a > 0.0:
		draw_rect(Rect2(-ART.x, -ART.y, ART.x * 3, ART.y * 3), Color(amb, amb.a * strength))
	_draw_glows(dl)
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


## Поза человечка: [спрайт, ноги, подъём, мелочь [[спрайт, сдвиг от левого верхнего]]].
func _pose(w: Worker) -> Array:
	var pose := "stand"
	var extra: Array = []
	var pos := w.pos
	var lift := 0.0
	var dangle := "held0" if int((_time if moving() else Time.get_ticks_msec() / 1000.0) / 0.22) % 2 == 0 else "held1"
	if w == _drag:
		# Висит над своей тенью, болтает ногами.
		pose = dangle
		pos = _drag_at + _grab
		lift = w.lift
	elif w.squash > 0.0 and moving():
		pose = "land"
	elif w.act == Act.FALL and moving():
		pose = "stand" if w.bounced else dangle
		lift = w.lift
	elif w.placed and not moving():
		pose = "stand"
	elif not moving() or _react == &"broke":
		pos = w.home
		match w.role:
			Role.DESK, Role.TESTER:
				pose = "sit0"
			Role.MANAGER:
				extra.append(["tablet", Vector2(8, 6)])
			Role.INSIDER:
				pose = "hand_head"
				extra.append(["phone", Vector2(9, 0)])
	elif _react == &"release":
		pose = "wave0" if int((_time + w.anim) / 0.3) % 2 == 0 else "wave1"
	elif _react == &"viral":
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
				extra.append(["zz", Vector2(7, -3 - float(int(w.anim / 0.6) % 3))])
			Act.WALK:
				pose = "walk0" if int(w.anim / tuning.step_seconds) % 2 == 0 else "walk1"
			Act.BOARD:
				pose = "hand_head"
			Act.VISIT:
				# Говорят по очереди: сначала гость, потом сосед, если он на месте.
				if w.timer > w.visit_len * 0.5 or _visit_partner(w) == null:
					extra.append(["bubble", Vector2(7, -7)])
			Act.POST:
				if w.role == Role.INSIDER:
					pose = "hand_head"
		if w.cup:
			extra.append(["cup", Vector2(9, 7)])
		if w.role == Role.MANAGER:
			extra.append(["tablet", Vector2(8, 6)])
		if w.role == Role.INSIDER and w.act == Act.POST:
			extra.append(["phone", Vector2(9, 0)])
	return [pose, pos, lift, extra]


## Сосед, к которому пришли, если он сидит на месте.
func _visit_partner(w: Worker) -> Desk:
	if w.visit_desk < 0 or w.visit_desk >= _desks.size():
		return null
	var nd := _desks[w.visit_desk]
	if nd.owner != null and nd.owner.pos == nd.seat and nd.owner.seated():
		return nd
	return null


func _pose_top(pose: String, pos: Vector2, lift: float) -> Vector2:
	var s := _size(pose)
	return Vector2(roundf(pos.x) - s.x / 2, roundf(pos.y - lift) - s.y)


## Поза человечка и мелочь при нём в общий список глубины. Возвращает следующий порядковый.
func _queue_worker(list: Array, w: Worker, order: int) -> int:
	var live := moving() and _react != &"broke"
	var away := not (w.pos == w.home and w.seated()) and (live or w == _drag or w.placed)
	if w.desk >= 0 and (away or (live and w.delay > 0.0)):
		# Пустой стул, пока хозяин стола не сидит.
		var seat := _desks[w.desk].seat
		list.append([seat.y, order, "chair", Vector2(seat.x - 5, seat.y - 5).floor(), null])
		order += 1
	if w.delay > 0.0 and live:
		return order
	var p := _pose(w)
	var pose: String = p[0]
	var pos: Vector2 = p[1]
	var top := _pose_top(pose, pos, p[2])
	var depth := 100000.0 if w == _drag else pos.y + 0.25
	if w == _drag or (w.act == Act.FALL and (p[2] as float) > 0.0):
		# Тень на полу, куда упадёт.
		var ground := _on_floor(pos).round()
		list.append([depth - 1.0, order, "shadow", Vector2(ground.x - 5, ground.y - 2), null])
		order += 1
	elif live and w.act == Act.VISIT and w.timer <= w.visit_len * 0.5:
		var nd := _visit_partner(w)
		if nd != null:
			list.append([nd.seat.y + 0.5, order, "bubble", (nd.seat + Vector2(2, -17)).floor(), null])
			order += 1
	list.append([depth, order, pose, top, w])
	order += 1
	for x in p[3]:
		list.append([depth + 0.05, order, x[0], top + x[1], null])
		order += 1
	return order


# --- Мышь ----------------------------------------------------------------------------------

## Нажатие на человечка, над которым нет оболочки, поднимает его над тенью; он висит за
## курсором, пока кнопку не отпустят, и падает на тень (на ближайшее место пола). Нажатие на
## кулер, телевизор или часы (`poke`) их оживляет. Событие съедается, только когда что-то
## нажали (и пока тащат), так что клики по карточкам сверху работают как раньше.
func _input(event: InputEvent) -> void:
	if not drag_enabled or not is_visible_in_tree() or _workers.is_empty():
		return
	if event is InputEventMouseMotion:
		var at := _to_art((event as InputEventMouseMotion).position)
		if _drag != null:
			_drag_at = at
			queue_redraw()
			get_viewport().set_input_as_handled()
		else:
			var over := _shell_free() and (worker_at(at) >= 0 or prop_at(at) != &"")
			_set_cursor(Input.CURSOR_POINTING_HAND if over else Input.CURSOR_ARROW)
	elif event is InputEventMouseButton and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		var b := event as InputEventMouseButton
		var at := _to_art(b.position)
		if b.pressed and _drag == null:
			if not _shell_free():
				return
			var i := worker_at(at)
			if i >= 0:
				_pick(_workers[i], at)
				get_viewport().set_input_as_handled()
			elif poke(prop_at(at)):
				get_viewport().set_input_as_handled()
		elif not b.pressed and _drag != null:
			_drop(at)
			get_viewport().set_input_as_handled()


func _exit_tree() -> void:
	_end_drag()
	_set_cursor(Input.CURSOR_ARROW)


## Под курсором нет элемента оболочки: ни одного Control, или только сама студия и её хозяин.
func _shell_free() -> bool:
	var hovered := get_viewport().gui_get_hovered_control()
	return hovered == null or hovered == self or hovered == get_parent()


func _to_art(screen: Vector2) -> Vector2:
	var local := get_global_transform_with_canvas().affine_inverse() * screen
	return (local - _origin()) / _px()


func _set_cursor(shape: Input.CursorShape) -> void:
	if shape != _cursor:
		_cursor = shape
		Input.set_default_cursor_shape(shape)


## Индекс человечка под точкой арта (ближний к зрителю первым), -1 нет.
func worker_at(at: Vector2) -> int:
	var best := -1
	var best_y := -INF
	for i in _workers.size():
		if _workers[i].delay > 0.0 and moving():
			continue
		var r := worker_rect(i)
		if r.grow(1.0).has_point(at) and r.end.y > best_y:
			best = i
			best_y = r.end.y
	return best


## Прямоугольник человечка в пикселях арта, как он сейчас нарисован.
func worker_rect(i: int) -> Rect2:
	var p := _pose(_workers[i])
	return Rect2(_pose_top(p[0], p[1], p[2]), Vector2(_size(p[0])))


## Тот же прямоугольник в координатах студии (для тестов и подсказок).
func worker_local_rect(i: int) -> Rect2:
	var r := worker_rect(i)
	return Rect2(_origin() + r.position * _px(), r.size * _px())


## Состояние человечка для тестов: где стоит, где его место, чем занят.
func worker_info(i: int) -> Dictionary:
	var w := _workers[i]
	return {"pos": w.pos, "home": w.home, "act": ACT_NAMES[w.act], "held": w == _drag, "placed": w.placed,
			"lift": w.lift, "squash": w.squash > 0.0}


## Взяли: ноги остаются, где были относительно курсора, и человечек поднимается над своей
## тенью на `lift_height` (плейтест 2026-11-11: раньше съезжал вниз).
func _pick(w: Worker, at: Vector2) -> void:
	var p := _pose(w)
	_grab = (p[1] as Vector2) - at
	_drag = w
	_drag_at = at
	w.path.clear()
	w.act = Act.HELD
	w.placed = false
	w.vy = 0.0
	w.squash = 0.0
	w.bounced = false
	w.lift = (p[2] as float) if moving() else tuning.lift_height
	_set_cursor(Input.CURSOR_DRAG)
	queue_redraw()


## Ближайшая точка пола, куда можно поставить.
func _on_floor(at: Vector2) -> Vector2:
	return Vector2(clampf(at.x, FLOOR_RECT.position.x, FLOOR_RECT.end.x),
			clampf(at.y, FLOOR_RECT.position.y, FLOOR_RECT.end.y))


## Отпустили: падает на свою тень (со стены или из-за края на ближайшее место пола).
func _drop(at: Vector2) -> void:
	var w := _drag
	_drag = null
	var ground := at + _grab
	var feet_y := ground.y - w.lift
	w.pos = _on_floor(ground).round()
	# Ближайшая дорожка: с неё пойдёт к своему делу.
	var lane := float(TOP_LANE)
	for d in _desks:
		if absf(d.lane - w.pos.y) < absf(lane - w.pos.y):
			lane = d.lane
	w.lane = lane
	w.placed = true
	w.cup = false
	w.vy = 0.0
	w.bounced = false
	w.lift = maxf(0.0, w.pos.y - feet_y)
	if moving() and w.lift > 0.5:
		w.act = Act.FALL
	else:
		w.lift = 0.0
		w.act = Act.WAIT
		w.timer = tuning.drop_seconds
	_set_cursor(Input.CURSOR_POINTING_HAND)
	queue_redraw()


## Бросить перетаскивание без места (перестройка студии, реакция «банкротство»).
func _end_drag() -> void:
	if _drag != null:
		_home_now(_drag)
		_drag = null
		_set_cursor(Input.CURSOR_ARROW)


# --- День и ночь ----------------------------------------------------------------------------

## Час суток 0..24: от часов студии (`start_hour`, сутки за `day_seconds`) или стоящий `daytime`,
## плюс накрученное нажатием на часы.
func hour() -> float:
	var base := daytime * 24.0 if daytime >= 0.0 else tuning.start_hour + _day_clock / tuning.day_seconds * 24.0
	return fposmod(base + _day_shift, 24.0)


## Стекло окна (внутри рамы, вместе с переплётом).
func _pane(it: Item) -> Rect2:
	return Rect2(Vector2(it.pos + Vector2i(1, 1)), Vector2(StudioSprites.WINDOW_SIZE - Vector2i(2, 4)))


func _windows() -> Array[Item]:
	var out: Array[Item] = []
	for it in _wall:
		if it.sprite == "window":
			out.append(it)
	return out


## Прямоугольник цветом только там, где он внутри стёкол.
func _fill_in(r: Rect2, c: Color, panes: Array[Rect2]) -> void:
	for p in panes:
		var q := r.intersection(p)
		if q.size.x > 0.0 and q.size.y > 0.0:
			draw_rect(q, c)


## Прямоугольник через пиксель (сеткой): лучи и переходы без размытия.
func _dither(r: Rect2, c: Color) -> void:
	var q := r.intersection(Rect2(Vector2.ZERO, Vector2(ART)))
	if q.size.x <= 0.0 or q.size.y <= 0.0:
		return
	if _checker == null:
		var img := Image.create_empty(ART.x, ART.y, false, Image.FORMAT_RGBA8)
		img.fill(Color(0, 0, 0, 0))
		for y in ART.y:
			for x in range(y % 2, ART.x, 2):
				img.set_pixel(x, y, Color.WHITE)
		_checker = ImageTexture.create_from_image(img)
	draw_texture_rect_region(_checker, q, q, c)


## Небо в окнах: два тона с полосой сеткой у горизонта, облака днём, низкое солнце утром и
## вечером, звёзды и луна ночью, город по низу с огнями ночью. Облака и город общие для всех
## окон (по x комнаты), так что окна смотрят на один вид.
func _draw_sky(dl: StudioDaylight) -> void:
	var wins := _windows()
	if wins.is_empty():
		return
	var bg := Style.BG
	var ink := Style.STUDIO_INK
	var k := strength
	var top := bg.lerp(dl.top, k)
	var low := bg.lerp(dl.low, k)
	var panes: Array[Rect2] = []
	for it in wins:
		panes.append(_pane(it))
	var pane0 := panes[0]
	var horizon := pane0.position.y + floorf(pane0.size.y * 0.6)
	for p in panes:
		draw_rect(Rect2(p.position, Vector2(p.size.x, horizon - p.position.y)), top)
		draw_rect(Rect2(p.position.x, horizon, p.size.x, p.end.y - horizon), low)
		_dither(Rect2(p.position.x, horizon - 2, p.size.x, 2), low)
	# Звёзды мигают по очереди, луна в среднем окне.
	if dl.night > 0.0:
		var star := Color(bg.lerp(top, 0.25), dl.night * k)
		for wi in panes.size():
			var p := panes[wi]
			for i in 7:
				var x := p.position.x + float((i * 17 + wi * 11 + 3) % int(p.size.x))
				var y := p.position.y + float((i * 7 + wi * 5 + 1) % int(horizon - p.position.y - 3))
				if fposmod(_day_clock * 0.37 + i * 0.29 + wi * 0.11, 1.0) > 0.12:
					draw_rect(Rect2(x, y, 1, 1), star)
		var m := panes[mini(1, panes.size() - 1)]
		var mx := m.position.x + 24.0 + floorf(fposmod(dl.hour + 4.0, 24.0) / 2.0)
		var moon := Color(bg.lerp(Color("#F2EBD8"), k), dl.night)
		var mrows: Array = [[1, 2], [0, 1], [0, 1], [1, 2]]
		for r in mrows.size():
			_fill_in(Rect2(mx + float(mrows[r][0]), m.position.y + 4.0 + r, float(mrows[r][1]), 1), moon, panes)
	# Солнце низко: утром в правом окне, вечером в левом; за городом садится.
	if dl.sun_t >= 0.0:
		var sx := roundf(lerpf(330.0, 40.0, dl.sun_t))
		var sy := roundf(horizon + 2.0 - dl.elev * 40.0)
		var sun := bg.lerp(Color("#FBEBC4"), k)
		var srows: Array = [[1, 3], [0, 5], [0, 5], [0, 5], [1, 3]]
		for r in srows.size():
			_fill_in(Rect2(sx + float(srows[r][0]), sy + r, float(srows[r][1]), 1), sun, panes)
	# Облака плывут вправо, ночью их не видно.
	var day := 1.0 - dl.night
	if day > 0.0:
		var cloud := Color(top.lerp(low, 0.4).lerp(bg, 0.55), day * k)
		var crows: Array = [[2, 5], [0, 10], [1, 7]]
		for c in 4:
			var span := float(ART.x + 60)
			var cx := roundf(fposmod(60.0 + c * 121.0 + _day_clock * tuning.cloud_speed * (1.0 + c * 0.3), span) - 30.0)
			var cy := pane0.position.y + 2.0 + float((c * 5) % 11)
			for r in crows.size():
				_fill_in(Rect2(cx + float(crows[r][0]), cy + r, float(crows[r][1]), 1), cloud, panes)
	# Город: дома по шесть пикселей, ночью в окнах свет.
	var town := low.lerp(ink, (tuning.skyline_tone + 0.3 * dl.night) * k)
	var lamp := Color(bg.lerp(Color("#E9CB8E"), k), dl.night * 0.85)
	var floor_y := pane0.end.y
	for b in range(0, ART.x / 6 + 1):
		var h := 3 + (b * 7 + (b * b) % 5) % 7
		if b % 5 == 2:
			h = 2
		var bx := float(b * 6)
		_fill_in(Rect2(bx, floor_y - h, 6, h), town, panes)
		if dl.night > 0.0 and h >= 4:
			for ry in range(int(floor_y) - h + 1, int(floor_y) - 1, 2):
				for cx in [1, 3]:
					if (b * 31 + ry * 7 + cx * 13) % 3 == 0:
						_fill_in(Rect2(bx + cx, ry, 1, 1), lamp, panes)


## Свет из окон, пока солнце над горизонтом: пятно на полу от каждого стекла (переплёт оставляет
## тёмные полосы), сдвинутое вбок и вытянутое тем сильнее, чем ниже солнце; низкое солнце даёт
## ещё лучи в воздухе сеткой через пиксель. Рисуется под мебелью и людьми.
func _draw_light(dl: StudioDaylight) -> void:
	if dl.light.a <= 0.0 or strength <= 0.0:
		return
	var patch := Color(dl.light, dl.light.a * strength)
	var beam := Color(dl.light, dl.beam * strength)
	var f := dl.shaft
	var sl := dl.slant
	var wy := float(WALL_Y)
	for it in _windows():
		var pane := _pane(it)
		var mid := Vector2(it.pos) + Vector2(StudioSprites.WINDOW_SIZE.x / 2, (StudioSprites.WINDOW_SIZE.y - 3) / 2)
		var zt := wy - pane.position.y
		var zb := wy - pane.end.y
		if beam.a > 0.004:
			for y in range(int(pane.end.y), int(wy + zb * f)):
				var yy := float(y)
				var zmin := maxf(zb, maxf(wy - yy, (yy - wy) / f))
				if zmin > zt:
					continue
				var o1 := (yy - wy + zmin) * f * sl / (1.0 + f)
				var o2 := (yy - wy + zt) * f * sl / (1.0 + f)
				var xa := roundf(pane.position.x + minf(o1, o2))
				var xb := roundf(pane.end.x + maxf(o1, o2))
				_dither(Rect2(xa, yy, xb - xa, 1), beam)
		var cols: Array = [[pane.position.x, mid.x], [mid.x + 1.0, pane.end.x]]
		var rows: Array = [[pane.position.y, mid.y], [mid.y + 1.0, pane.end.y]]
		for r in rows:
			var y_from := int(roundf(wy + (wy - float(r[1])) * f))
			var y_to := int(roundf(wy + (wy - float(r[0])) * f))
			for y in range(y_from, y_to):
				var d := float(y) - wy
				for c in cols:
					draw_rect(Rect2(roundf(float(c[0]) + d * sl), y, float(c[1]) - float(c[0]), 1), patch)


## Стрелки часов по времени суток: минутная в два пикселя, часовая в один, восемь направлений.
func _draw_clock_hands(colors: Dictionary, h: float) -> void:
	if _clock == null:
		return
	var c := Vector2(_clock.pos + StudioSprites.CLOCK_CENTER)
	var ink: Color = colors["#"]
	var dm := _dir8(fposmod(h, 1.0))
	var dh := _dir8(fposmod(h, 12.0) / 12.0)
	for q: Vector2 in [c, c + dm, c + dm * 2.0, c + dh]:
		draw_rect(Rect2(q, Vector2.ONE), ink)


func _dir8(turn: float) -> Vector2:
	var a := roundf(turn * 8.0) / 8.0 * TAU
	return Vector2(roundf(sin(a)), -roundf(cos(a)))


## Ночью светятся экраны (у сидящих за столом), лампы и телевизор: поверх общего оттенка, так
## что в тёмной комнате они остаются светлыми.
func _draw_glows(dl: StudioDaylight) -> void:
	var a := dl.night * tuning.glow_alpha * strength
	if a <= 0.01:
		return
	var screen := Color(Color("#EEF1F6"), a)
	var warm := Color(Color("#F6E6C4"), a)
	for it in _floor:
		if it.desk >= 0:
			var spr := _monitor_sprite(it.desk)
			if spr == "monitor_off" or spr == "monitor":
				continue
			draw_rect(Rect2(Vector2(it.pos) + Vector2(1, 1), Vector2(8, 3)), screen)
		elif it.sprite == "lamp":
			draw_rect(Rect2(Vector2(it.pos) + Vector2(1, 1), Vector2(2, 1)), warm)
		elif it == _tv:
			draw_rect(Rect2(Vector2(it.pos + StudioSprites.TV_SCREEN.position), Vector2(StudioSprites.TV_SCREEN.size)), screen)


# --- Нажимаемые предметы ------------------------------------------------------------------

## Нажать предмет: `&"cooler"` в бутыли всплывает пузырь и лопается («бульк»), `&"tv"` помехи и
## следующий канал (шипение), `&"clock"` стрелки прокручивают сутки на `clock_spin_hours`
## (стрёкот). Ложь, если такого предмета в студии нет.
func poke(prop: StringName) -> bool:
	match prop:
		&"cooler":
			if _cooler == null:
				return false
			_bubbles.append(0.0)
			_play(&"bulp")
		&"tv":
			if _tv == null:
				return false
			_tv_channel = (_tv_channel + 1) % StudioSprites.TV_CHANNELS.size()
			_tv_age = 0.0
			_play(&"static")
		&"clock":
			if _clock == null:
				return false
			_spin_left += tuning.clock_spin_seconds
			_play(&"whirr")
		_:
			return false
	queue_redraw()
	return true


## Предмет под точкой арта (`PROPS`) или пусто.
func prop_at(at: Vector2) -> StringName:
	for prop in PROPS:
		var it := _prop_item(prop)
		if it != null and Rect2(Vector2(it.pos), Vector2(_size(it.sprite))).grow(1.0).has_point(at):
			return prop
	return &""


## Прямоугольник предмета в координатах студии (для тестов), пустой, если его нет.
func prop_local_rect(prop: StringName) -> Rect2:
	var it := _prop_item(prop)
	if it == null:
		return Rect2()
	return Rect2(_origin() + Vector2(it.pos) * _px(), Vector2(_size(it.sprite)) * _px())


## Состояние предметов и суток для тестов.
func prop_info() -> Dictionary:
	return {"bubbles": _bubbles.size(), "tv_channel": _tv_channel, "tv_switching": _tv_age >= 0.0,
			"hour": hour(), "spinning": _spin_left > 0.0}


func _prop_item(prop: StringName) -> Item:
	match prop:
		&"cooler":
			return _cooler
		&"tv":
			return _tv
		&"clock":
			return _clock
	return null


## Анимации предметов и прокрутка часов; правда, если что-то идёт (нужна перерисовка).
func _tick_props(delta: float) -> bool:
	var active := not _bubbles.is_empty() or _tv_age >= 0.0 or _spin_left > 0.0
	for i in range(_bubbles.size() - 1, -1, -1):
		_bubbles[i] += delta
		if _bubbles[i] >= tuning.bubble_seconds:
			_bubbles.remove_at(i)
	if _tv_age >= 0.0:
		_tv_age += delta
		if _tv_age >= tuning.tv_switch_seconds:
			_tv_age = -1.0
	if _spin_left > 0.0:
		var step := minf(delta, _spin_left)
		_day_shift = fposmod(_day_shift + tuning.clock_spin_hours * step / tuning.clock_spin_seconds, 24.0)
		_spin_left -= step
	return active


## Пузырь кулера: в бутыли поднимается квадратиком, над крышкой кружком, потом лопается
## брызгами по диагоналям.
func _draw_bubbles(colors: Dictionary) -> void:
	var base := Vector2(_cooler.pos)
	var water := StudioSprites.COOLER_WATER
	for age in _bubbles:
		var u := age / tuning.bubble_seconds
		var wob := float(int(age * 10.0) % 2)
		if u < 0.4:
			var y := float(water.end.y - 2) - floorf(u / 0.4 * float(water.size.y - 1))
			draw_rect(Rect2(base + Vector2(4.0 + wob, y), Vector2(2, 2)), colors["o"])
			continue
		var v := minf(1.0, (u - 0.4) / 0.45)
		var c := base + Vector2(5.0 + wob, roundf(-2.0 - v * 7.0))
		if u < 0.85:
			for d: Vector2 in [Vector2(0, -1), Vector2(-1, 0), Vector2(1, 0), Vector2(0, 1)]:
				draw_rect(Rect2(c + d, Vector2.ONE), colors["#"])
			draw_rect(Rect2(c, Vector2.ONE), colors["o"])
		else:
			for d: Vector2 in [Vector2(-2, -2), Vector2(2, -2), Vector2(-2, 2), Vector2(2, 2)]:
				draw_rect(Rect2(c + d, Vector2.ONE), colors["+"])


## Экран телевизора: при переключении картинка схлопывается в линию, помехи с бегущей полосой,
## новая картинка прокручивается кадром; потом стоит канал (нулевой это картинка спрайта).
func _draw_tv(colors: Dictionary) -> void:
	var base := Vector2(_tv.pos + StudioSprites.TV_SCREEN.position)
	var sz := StudioSprites.TV_SCREEN.size
	if _tv_age >= 0.0:
		var a := _tv_age / tuning.tv_switch_seconds
		if a < 0.1:
			draw_rect(Rect2(base, Vector2(sz)), colors["#"])
			draw_rect(Rect2(base.x, base.y + sz.y / 2, sz.x, 1), colors["o"])
			return
		if a < 0.7:
			var frame := int(_tv_age / 0.04)
			var bar := int(_tv_age * 22.0) % (sz.y + 3) - 1
			for y in sz.y:
				for x in sz.x:
					var n := ((x * 7 + y * 13 + frame * 31) * 2654435761) % 4096 % 10
					var key := "#" if n < 4 else ("+" if n < 7 else ("-" if n < 9 else "o"))
					if y == bar or y == bar + 1:
						key = "#" if key != "o" else "+"
					draw_rect(Rect2(base + Vector2(x, y), Vector2.ONE), colors[key])
			return
		_draw_tv_picture(base, colors, int((1.0 - (a - 0.7) / 0.3) * float(sz.y + 1)))
		return
	if _tv_channel != 0:
		_draw_tv_picture(base, colors, 0)


func _draw_tv_picture(base: Vector2, colors: Dictionary, roll: int) -> void:
	var sz := StudioSprites.TV_SCREEN.size
	var pic: Array = StudioSprites.TV_CHANNELS[_tv_channel]
	if pic.is_empty():
		var rows := StudioSprites.rows_of("tech_bit8")
		pic = []
		for y in sz.y:
			pic.append((rows[StudioSprites.TV_SCREEN.position.y + y] as String).substr(StudioSprites.TV_SCREEN.position.x, sz.x))
	for y in sz.y:
		var src := (y + roll) % (sz.y + 1)
		var row := "#".repeat(sz.x) if src == sz.y else (pic[src] as String)
		for x in sz.x:
			draw_rect(Rect2(base + Vector2(x, y), Vector2.ONE), colors[row[x]])


func _play(sound: StringName) -> void:
	if not _sounds.has(sound):
		if not _streams.has(sound):
			match sound:
				&"bulp":
					_streams[sound] = Sfx.bulp()
				&"static":
					_streams[sound] = Sfx.hiss(tuning.tv_switch_seconds)
				&"whirr":
					_streams[sound] = Sfx.whirr(tuning.clock_spin_seconds)
		var p := Sfx.player(_streams[sound])
		add_child(p)
		_sounds[sound] = p
	(_sounds[sound] as AudioStreamPlayer).play()
