class_name SpitLevel
extends RefCounted
## Уровень демки платформер × low poly «тропа вглубь экрана» (#112, спека
## `docs/specs/demos.md`): песчаная коса из прямоугольных кусков. Кусок смотрит вперёд (−Z),
## влево или вправо: поворот под прямым углом это следующий кусок, пристроенный сбоку к концу
## предыдущего. У куска своя система координат: `s` метров вдоль от ближнего края, `u` вбок от
## середины (плюс вправо по ходу); высота меняется по длине, между кусками бывают уступы и ямы с
## водой. Над широкой водой ходят плоты, по кускам катятся навстречу бочки, с островков
## стреляют поперёк тропы пушки, поперёк ходят скелеты, стоят ряды ящиков. Всё движущееся
## считается от времени по формуле, без состояния: бот и демка видят одно и то же и могут
## заглянуть вперёд. Строится `SpitLevelGen` из сида записи.

enum Kind { START, PLAIN, BRIDGE, GUARD, CRATES, ROLL, FIRE, STONE, END }

const WATER_DROP := 1.7
## Бочки катка падают на тропу за столько метров до дальнего края куска: за этой чертой тихо.
const ROLL_DROP := 3.0
## До ближнего края куска бочки не докатываются на столько: там они разбиваются, вход на каток тихий.
const ROLL_END := 1.5

class Piece:
	var kind := Kind.PLAIN
	## Яма перед куском: расстояние от дальнего края предыдущего; `raft` над ней ходит плот.
	var gap := 0.0
	var raft := -1
	## Середина ближнего края, направление хода, длина и ширина.
	var a := Vector3.ZERO
	var dir := Vector3(0, 0, -1)
	var length := 10.0
	var width := 5.0
	## Высота тропы у ближнего и у дальнего края.
	var h0 := 0.0
	var h1 := 0.0
	## Расстояние по тропе от старта до ближнего края (для полосы пути).
	var along := 0.0

	func right() -> Vector3:
		return Vector3(-dir.z, 0.0, dir.x)

	## Точка мира в координатах куска: x это `s` вдоль, y это `u` вбок.
	func local(p: Vector3) -> Vector2:
		var d := p - a
		return Vector2(d.x * dir.x + d.z * dir.z, d.x * -dir.z + d.z * dir.x)

	func height(s: float) -> float:
		return lerpf(h0, h1, clampf(s / length, 0.0, 1.0))

	func world(s: float, u: float) -> Vector3:
		var p := a + dir * s + right() * u
		return Vector3(p.x, height(s), p.z)

	func far() -> Vector3:
		return world(length, 0.0)

	func contains(p: Vector3) -> bool:
		var q := local(p)
		return q.x >= 0.0 and q.x <= length and absf(q.y) <= width / 2.0

	func low() -> float:
		return minf(h0, h1)

	## Курс куска как `rotation.y`: 0 смотрит в −Z.
	func yaw() -> float:
		return atan2(-dir.x, -dir.z)


class Guard:
	## Кусок, линия `s`, на сколько ходит в стороны, скорость, доля периода.
	var piece := 0
	var s := 0.0
	var reach := 2.0
	var speed := 1.6
	var phase := 0.0


class Roller:
	## Бочки катятся по куску от дальнего края к ближнему: скорость, период, сдвиг и полосы по
	## кругу (у какой бочки какой `u`).
	var piece := 0
	var speed := 6.0
	var period := 2.2
	var offset := 0.0
	var lanes := PackedFloat32Array()


class Cannon:
	## Пушка у куска на линии `s` с борта `side` (1 справа): ядро летит поперёк тропы.
	var piece := 0
	var s := 0.0
	var side := 1.0
	var speed := 9.0
	var period := 2.4
	var offset := 0.0


class Raft:
	## Плот над ямой перед куском `piece`: ходит поперёк тропы на `reach` в стороны.
	var piece := 0
	var s := 0.0
	var reach := 2.5
	var speed := 2.0
	var phase := 0.0
	var half := 1.25
	var y := 0.0


var pieces: Array[Piece] = []
var guards: Array[Guard] = []
var rollers: Array[Roller] = []
var cannons: Array[Cannon] = []
var rafts: Array[Raft] = []
## Ящики: середина дна (стоят на тропе).
var crates: Array[Vector3] = []
## Дублоны: середина в воздухе.
var coins: Array[Vector3] = []
var start := Vector3.ZERO
var total := 1.0


## Кусок под точкой или −1 (вода, яма).
func piece_at(p: Vector3) -> int:
	for i in pieces.size():
		if pieces[i].contains(p):
			return i
	return -1


## Плот под точкой в момент `time` или −1.
func raft_at(p: Vector3, time: float) -> int:
	for i in rafts.size():
		var c := raft_pos(i, time)
		if absf(p.x - c.x) <= rafts[i].half and absf(p.z - c.z) <= rafts[i].half:
			return i
	return -1


## Высота опоры под точкой в момент `time` (тропа или плот) или −INF, если под ней вода.
func ground_at(p: Vector3, time := 0.0) -> float:
	var i := piece_at(p)
	if i >= 0:
		return pieces[i].height(pieces[i].local(p).x)
	var r := raft_at(p, time)
	return rafts[r].y if r >= 0 else -INF


func water_y() -> float:
	var low := INF
	for p in pieces:
		low = minf(low, p.low())
	return low - WATER_DROP


## Ровное хождение туда-сюда: −1..1 от времени и куда идёт.
static func swing(time: float, speed: float, reach: float, phase: float) -> float:
	var k := fposmod(time * speed / (4.0 * reach) + phase, 1.0)
	return 4.0 * absf(k - 0.5) - 1.0


static func swing_dir(time: float, speed: float, reach: float, phase: float) -> float:
	return -1.0 if fposmod(time * speed / (4.0 * reach) + phase, 1.0) < 0.5 else 1.0


## Где скелет `i` поперёк своего куска в момент `time`.
func guard_u(i: int, time: float) -> float:
	var g := guards[i]
	return g.reach * swing(time, g.speed, g.reach, g.phase)


func guard_pos(i: int, time: float) -> Vector3:
	return pieces[guards[i].piece].world(guards[i].s, guard_u(i, time))


func guard_dir(i: int, time: float) -> float:
	var g := guards[i]
	return swing_dir(time, g.speed, g.reach, g.phase)


func raft_u(i: int, time: float) -> float:
	var r := rafts[i]
	return r.reach * swing(time, r.speed, r.reach, r.phase)


func raft_pos(i: int, time: float) -> Vector3:
	var r := rafts[i]
	var p := pieces[r.piece]
	var c := p.a + p.dir * r.s + p.right() * raft_u(i, time)
	return Vector3(c.x, r.y, c.z)


## Бочки катка `i`, что сейчас на куске: `s` вдоль, `u` вбок. Бочка `k` падает на тропу у
## дальнего края (`ROLL_DROP` до него) в момент `offset + k · period` и катится к ближнему.
func barrels(i: int, time: float) -> Array[Vector2]:
	var r := rollers[i]
	var length := pieces[r.piece].length - ROLL_DROP
	var out: Array[Vector2] = []
	var newest := floori((time - r.offset) / r.period)
	var oldest := ceili((time - r.offset - length / r.speed) / r.period)
	for k in range(maxi(oldest, 0), newest + 1):
		var s := length - r.speed * (time - r.offset - k * r.period)
		if s >= ROLL_END and s <= length:
			out.append(Vector2(s, r.lanes[posmod(k, r.lanes.size())]))
	return out


## Откуда пушка стреляет и где ядро падает в воду, вбок от середины куска.
func cannon_from(i: int) -> float:
	return cannons[i].side * (pieces[cannons[i].piece].width / 2.0 + 3.5)


func cannon_to(i: int) -> float:
	return -cannons[i].side * (pieces[cannons[i].piece].width / 2.0 + 4.5)


## Сколько секунд назад пушка выстрелила (ядро летит, пока не упало); −1, если ядра в воздухе нет.
func ball_age(i: int, time: float) -> float:
	var c := cannons[i]
	if time < c.offset:
		return -1.0
	var age := fposmod(time - c.offset, c.period)
	return age if age * c.speed <= absf(cannon_to(i) - cannon_from(i)) else -1.0


## Где ядро пушки `i` поперёк куска в момент `time`; INF, если ядра в воздухе нет.
func ball_u(i: int, time: float) -> float:
	var age := ball_age(i, time)
	return INF if age < 0.0 else cannon_from(i) - cannons[i].side * cannons[i].speed * age


## Следующая бочка катка `i`: через сколько секунд выкатится и по какой полосе.
func next_barrel(i: int, time: float) -> Vector2:
	var r := rollers[i]
	var k := maxi(floori((time - r.offset) / r.period) + 1, 0)
	return Vector2(r.offset + k * r.period - time, r.lanes[posmod(k, r.lanes.size())])


func finish_piece() -> Piece:
	return pieces[pieces.size() - 1]


func gaps() -> int:
	var n := 0
	for p in pieces:
		if p.gap > 0.0:
			n += 1
	return n


func turns() -> int:
	var n := 0
	for i in range(1, pieces.size()):
		if not pieces[i].dir.is_equal_approx(pieces[i - 1].dir):
			n += 1
	return n


## Уступы: стык без ямы с перепадом высоты, который не пройти шагом.
func steps() -> int:
	var n := 0
	for i in range(1, pieces.size()):
		if pieces[i].gap <= 0.0 and absf(pieces[i].h0 - pieces[i - 1].h1) > 0.5:
			n += 1
	return n


## Мест, где игрок рискует жизнью: ямы, плоты, скелеты, катки, пушки, ряды ящиков, уступы вверх.
func risks() -> int:
	var rows := {}
	for c in crates:
		rows[piece_at(c + Vector3(0.0, 0.1, 0.0))] = true
	var ups := 0
	for i in range(1, pieces.size()):
		if pieces[i].gap <= 0.0 and pieces[i].h0 - pieces[i - 1].h1 > 0.5:
			ups += 1
	return gaps() + guards.size() + rollers.size() + cannons.size() + rows.size() + ups


## Подпись для сравнения двух уровней: детерминизм генератора.
func signature() -> String:
	var parts: PackedStringArray = []
	for p in pieces:
		parts.append("p%d,%.2f,%d,%s,%s,%.1f,%.1f,%.2f,%.2f" % [p.kind, p.gap, p.raft, p.a, p.dir, p.length, p.width, p.h0, p.h1])
	for g in guards:
		parts.append("g%d,%.2f,%.2f,%.2f,%.2f" % [g.piece, g.s, g.reach, g.speed, g.phase])
	for r in rollers:
		parts.append("r%d,%.2f,%.2f,%.2f,%s" % [r.piece, r.speed, r.period, r.offset, r.lanes])
	for c in cannons:
		parts.append("f%d,%.2f,%.0f,%.2f,%.2f,%.2f" % [c.piece, c.s, c.side, c.speed, c.period, c.offset])
	for r in rafts:
		parts.append("t%d,%.2f,%.2f,%.2f,%.2f" % [r.piece, r.s, r.reach, r.speed, r.phase])
	for c in crates:
		parts.append("b%s" % c)
	for c in coins:
		parts.append("c%s" % c)
	return "|".join(parts)
