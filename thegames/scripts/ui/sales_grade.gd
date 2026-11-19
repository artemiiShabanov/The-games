class_name SalesGrade
extends RefCounted
## Удались ли продажи игры (2026-11-19): пять ступеней по сумме первой недели, пороги
## постоянные, в долларах, `SuccessTuning.sales_grades`. Ступень задаёт цвет, размер, жирность
## и анимацию числа (`SalesFigure`) везде, где игрок видит продажи игры.
## Под автотестом `--sales-grade=0..4` ставит ступень всем числам, в дебаг-меню «Продажи».

enum { FLOP, WEAK, FINE, HIT, SMASH }

const WORDS: Array[String] = ["провал", "слабо", "неплохо", "хит", "суперхит"]
## Размер числа относительно обычного.
const SCALES: Array[float] = [0.92, 0.92, 1.0, 1.14, 1.3]
## Жирность: утолщение контура моноширинного шрифта.
const EMBOLDEN: Array[float] = [-0.25, -0.35, 0.0, 0.45, 0.8]
## Доля цвета денег в цвете числа.
const GREEN: Array[float] = [0.0, 0.35, 0.7, 1.0, 1.0]
const SECTION: StringName = &"Продажи"  # i18n: skip

## Ступень для всех чисел: −1 считать по записи.
static var forced := -1
static var _tuning: SuccessTuning
static var _fonts: Dictionary = {}
static var _args_read := false


static func of(sales: int) -> int:
	_read_args()
	if forced >= 0:
		return clampi(forced, FLOP, SMASH)
	if _tuning == null:
		_tuning = load(SuccessTuning.PATH) as SuccessTuning
	var g := FLOP
	for edge in _tuning.sales_grades:
		if sales >= edge:
			g += 1
	return mini(g, SMASH)


static func of_record(r: GameRecord) -> int:
	return of(r.score.sales_first if r != null and r.score != null else 0)


static func word(g: int) -> String:
	return Lang.t(WORDS[g])


## От нейтрального серого к цвету денег: провал серый, хит и суперхит зелёные в полную силу.
## Красного нет (решение 2026-11-19): плохие продажи это тихо, а не тревога.
static func color(g: int) -> Color:
	return Style.INK_3.lerp(Style.INK_2, 0.4).lerp(Style.MONEY, GREEN[g])


static func font(g: int) -> Font:
	if not _fonts.has(g):
		var f := FontVariation.new()
		f.base_font = Style.mono_font()
		f.variation_embolden = EMBOLDEN[g]
		_fonts[g] = f
	return _fonts[g]


static func font_size(g: int, base: int) -> int:
	return int(round(base * SCALES[g]))


static func register_debug() -> void:
	Debug.add_action(SECTION, "Ступень: следующая (−1 по записи)", func() -> void:
		forced = forced + 1 if forced < SMASH else -1)


static func _read_args() -> void:
	if _args_read:
		return
	_args_read = true
	if AutoTest.enabled:
		var args := AutoTest.parse_args(OS.get_cmdline_user_args())
		if args.has("sales-grade"):
			forced = int(str(args["sales-grade"]))
