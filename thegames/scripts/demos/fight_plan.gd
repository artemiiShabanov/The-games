class_name FightPlan
extends RefCounted
## План соперника файтинга × 8-bit на раунд (#54), из сида (`FightPlanGen`): фазы с профилем
## поведения и паттерном ударов, реакция и промахи соперника, раскладка фона (мачта, пропы).
## Один и тот же сид даёт тот же план в плейтесте, ленте и галерее.


class Phase:
	## Индекс профиля в `FightGenTuning.profiles`.
	var profile := 0
	var seconds := 10.0
	## Удары по кругу: H верхний, L нижний.
	var pattern := "H"


class Prop:
	## У какого борта (знак: −1 левый, 1 правый) и как далеко от него внутрь, px; вид 0 пушка,
	## 1 сундук.
	var x := 0.0
	var kind := 0


var seed := 0
var phases: Array[Phase] = []
## Соперник видит удар героя через столько шагов и с шансом `miss` не отвечает.
var reaction := 15
var miss := 0.2
## Мачта от середины арены, px; пропы фона у бортов.
var mast_x := 0.0
var props: Array[Prop] = []
var attempts := 1
var fallback := false


func total_seconds() -> float:
	var s := 0.0
	for p in phases:
		s += p.seconds
	return s


## Номер фазы в момент `t` секунд боя; после последней фазы план идёт по кругу.
func phase_index(t: float) -> int:
	if phases.is_empty():
		return 0
	var left := fmod(maxf(t, 0.0), maxf(total_seconds(), 0.001))
	for i in phases.size():
		if left < phases[i].seconds:
			return i
		left -= phases[i].seconds
	return phases.size() - 1


## «напор 12 HHL → стена 9 HL → ...» для дампа и заметок.
func describe(gen: FightGenTuning) -> String:
	var parts: PackedStringArray = []
	for p in phases:
		var title := gen.profiles[p.profile].title if p.profile < gen.profiles.size() else str(p.profile)
		parts.append("%s %.0f с %s" % [title, p.seconds, p.pattern])
	return " → ".join(parts)
