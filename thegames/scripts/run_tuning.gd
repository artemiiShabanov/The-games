class_name RunTuning
extends Resource
## Настройки забега, ресурс `res://resources/run.tres`. Стартовая пара разыгрывается (#61):
## жанр из тех, у кого есть демка на стартовой технологии, технология из `start_techs`, не та же
## пара, что в прошлом забеге. `genre` и `tech` стартовая пара автотеста (без розыгрыша, чтобы
## прогоны петли были одинаковыми) и дебага. Кап и его сигналы ниже; от капа и сложность
## мини-игр `t = (релиз − 1) / (кап − 1)`.

const PATH := "res://resources/run.tres"

@export var genre: Game.Genre = Game.Genre.PLATFORMER
@export var tech: Game.Tech = Game.Tech.BIT8
## Технологии розыгрыша старта: с M3 (#104) вектор, 8-bit и 16/32, остальные покупаются.
@export var start_techs: Array[Game.Tech] = [Game.Tech.BIT8]
@export var title := "Зомби на платформах"
## Сеттинги, открытые со старта забега (#139): замки; космос и зомби открывают достижения
## первой и третьей игры (полировка 2026-11-17). Первый из них берёт
## быстрая конфигурация дебага и автотеста.
@export var start_settings: Array[Game.Setting] = [Game.Setting.CASTLES]
@export var sprints := 5
## Сложность мини-игр первого релиза (2026-11-17: старт со средней, раньше с нуля); к последнему
## релизу доходит до 1. Мини-игра, которую игрок видит впервые, идёт на 0 (`Profile`).
@export var t_start := 0.5
## Потолок сложности мини-игр жанра и технологии (2026-11-18): их не упрощает штат, поэтому они
## растут от `t_start` только до этого значения на капе, а не до 1.
@export var t_owner_max := 0.7
## Кап забега (#62): разыгрывается на забег в `cap_min`..`cap_max` релизов, игроку не
## показывается. Сигналы капа считаются от него: «студия-ветеран» у критиков с капа −
## `veteran_left`, реплики «сколько ещё» во вставках с капа − `how_long_left`, покупатель на
## капе − `buyer_left`; все не раньше релиза `signals_from`.
@export var cap_min := 11
@export var cap_max := 13
@export var signals_from := 3
@export var veteran_left := 3
@export var how_long_left := 2
@export var buyer_left := 1
## Пороги концовок (`docs/specs/run.md`, #65; черновые до сверки моделью в #72).
## Корпорация: сиквелов не меньше, игр с живым хвостом не меньше, суммарный тик хвостов от.
@export var corp_sequels := 2
@export var corp_live_tails := 4
@export var corp_tick := 3500
## Легенда: средняя критиков трёх лучших от или вирусных игр не меньше.
@export var legend_critics := 9.0
@export var legend_viral := 3
## Легенда не раньше стольких выпущенных игр (полировка 2026-11-17: приходила после четырёх).
@export var legend_min_games := 8
## После релиза (#133): отклик приходит на главный экран волнами. Первая волна через
## `after_first_seconds`, следующие по одной сверху вниз через `after_gap_seconds` (2026-11-17: 5 с,
## было 3 с, карточки сливались в одно появление). Оценки критиков открываются
## только по нажатию на их карточку, до того ставка ещё принимается. Ставка на критиков: «разнесут»
## ниже `bet_low`, «полюбят» от `bet_high`, между ними «сойдёт»; угадал: `bet_bonus` денег.
@export var after_first_seconds := 1.5
@export var after_gap_seconds := 5.0
## Рецензии критиков открываются по одной с такой паузой.
@export var after_critic_seconds := 0.9
@export var bet_low := 5.0
@export var bet_high := 7.5
@export var bet_bonus := 1500
## Сколько переигровок в релизе (M0: ноль).
@export var replays := 0


static func load_default() -> RunTuning:
	var t := load(PATH) as RunTuning
	return t if t != null else RunTuning.new()
