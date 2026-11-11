class_name RunSave
extends Resource
## Сохранение забега в слоте (#71), `user://slot_N.tres` (под автотестом свои файлы). Пишется
## главной сценой на границах фаз и между спринтами: `stage` говорит, с чего продолжить
## (`release` начало релиза, `sprints` спринт `sprint_index`, `playtest`, `bugfix` предложение
## номер `bugfix_offers`, `feed`, `studio` фаза студии до расчёта). Всё, что меняется внутри фазы,
## сохранено на её начало, поэтому выход посреди фазы возвращает к её началу; выход посреди
## мини-игры возвращает к началу этого спринта, сид мини-игры другой (`resumes`). Записи игр,
## рынок и студия сохраняются ресурсами; кошелёк, содержание, вставки, логотип и план полями.

const VERSION := 1
const SLOTS := 3

static var test_files := false

@export var version := VERSION
@export var saved_at := 0
@export var stage: StringName = &"release"
@export var resumes := 0
## Рынок релиза уже разыгран (сохранение после «Новой студии»): не разыгрывать снова.
@export var prepared := false

@export var release := 1
@export var cap := 12
@export var start_genre: Game.Genre = Game.Genre.PLATFORMER
@export var start_tech: Game.Tech = Game.Tech.BIT8
@export var studio_name := ""
@export var logo := {}
@export var run_number := 1
@export var cash := 0
## История денег (#77): строки `Wallet.history`.
@export var ledger: Array[Dictionary] = []
@export var upkeep_base := 0
@export var upkeep_extras: Dictionary[StringName, int] = {}
@export var market: MarketState
@export var studio: StudioState
@export var records: Array[GameRecord] = []
@export var rng_seed := 0
@export var rng_state := 0
@export var last_first: StringName = &""
@export var reputation_before := 0.0
@export var buyer_came := false
@export var rep_log: Array[float] = []
@export var events := {}

## Текущий релиз: запись, план спринтов, сколько спринтов сыграно, предложений багфикса.
@export var current: GameRecord
@export var plan_ids: Array[StringName] = []
@export var replay_left := 0
@export var sprint_index := 0
@export var bugfix_offers := 0


static func path(slot: int) -> String:
	return "user://%sslot_%d.tres" % ["autotest_" if test_files else "", slot]


static func exists(slot: int) -> bool:
	return ResourceLoader.exists(path(slot))


static func load_slot(slot: int) -> RunSave:
	if not exists(slot):
		return null
	var s := ResourceLoader.load(path(slot), "", ResourceLoader.CACHE_MODE_IGNORE) as RunSave
	if s == null or s.version != VERSION:
		return null
	return s


static func delete_slot(slot: int) -> void:
	if exists(slot):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(path(slot)))


func write(slot: int) -> void:
	version = VERSION
	saved_at = int(Time.get_unix_time_from_system())
	var err := ResourceSaver.save(self, path(slot))
	if err != OK:
		push_warning("RunSave: слот %d не сохранился: %s" % [slot, error_string(err)])


# --- Вставки и логотип полями ------------------------------------------------------------------

static func events_to_dict(s: EventState) -> Dictionary:
	var restrictions: Array = []
	for r in s.restrictions:
		restrictions.append({"kind": int(r.kind), "value": r.value, "by": r.by})
	var shares: Array = []
	for t in s.tail_shares:
		shares.append({"share": t.share, "games": t.games, "by": t.by})
	var bonuses: Array = []
	for b in s.bonuses:
		bonuses.append({"stat": int(b.stat), "value": b.value})
	return {
		"last_event_release": s.last_event_release, "shown": s.shown.duplicate(), "last_shown": s.last_shown.duplicate(),
		"moods": s.moods.duplicate(), "refusals": s.refusals.duplicate(), "flags": s.flags.duplicate(),
		"restrictions": restrictions, "tail_shares": shares, "bonuses": bonuses, "ending": s.ending,
		"sold_tails": s.sold_tails.duplicate(),
	}


static func events_from_dict(d: Dictionary) -> EventState:
	var s := EventState.new()
	if d.is_empty():
		return s
	s.last_event_release = int(d.get("last_event_release", -100))
	for k in d.get("shown", {}):
		s.shown[StringName(k)] = int(d["shown"][k])
	for k in d.get("last_shown", {}):
		s.last_shown[StringName(k)] = int(d["last_shown"][k])
	for k in d.get("moods", {}):
		s.moods[StringName(k)] = int(d["moods"][k])
	for k in d.get("refusals", {}):
		s.refusals[StringName(k)] = int(d["refusals"][k])
	for k in d.get("flags", {}):
		s.flags[StringName(k)] = int(d["flags"][k])
	for r in d.get("restrictions", []):
		var x := EventState.Restriction.new()
		x.kind = int(r["kind"]) as EffectDef.Kind
		x.value = int(r["value"])
		x.by = str(r["by"])
		s.restrictions.append(x)
	for t in d.get("tail_shares", []):
		var x := EventState.TailShare.new()
		x.share = float(t["share"])
		x.games = int(t["games"])
		x.by = str(t["by"])
		s.tail_shares.append(x)
	for b in d.get("bonuses", []):
		var x := EventState.Bonus.new()
		x.stat = int(b["stat"]) as EffectDef.Stat
		x.value = float(b["value"])
		s.bonuses.append(x)
	s.ending = StringName(d.get("ending", ""))
	for i in d.get("sold_tails", []):
		s.sold_tails.append(int(i))
	return s


static func logo_to_dict(l: StudioLogo) -> Dictionary:
	if l == null:
		return {}
	return {"shape": int(l.shape), "color": l.color.to_html(), "symbol": l.symbol}


static func logo_from_dict(d: Dictionary) -> StudioLogo:
	if d.is_empty():
		return null
	var l := StudioLogo.new()
	l.shape = int(d.get("shape", 0)) as StudioLogo.Shape
	l.color = Color(str(d.get("color", "2f5bff")))
	l.symbol = int(d.get("symbol", 0))
	return l
