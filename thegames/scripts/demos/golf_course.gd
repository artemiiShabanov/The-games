class_name GolfCourse
extends RefCounted
## Поле гольфа × 8-bit (#52) из `GolfCourseGen`: две-три лунки вида сбоку. Лунка это карта высот
## поверхности (y вниз, точки через `step` px, между ними прямая) и вид каждого отрезка: песок
## острова, палуба (ти и грин), корма (стена за грином), море пролива. Мир лунки высотой в экран
## демки, по ширине камера едет.

enum Kind { SAND, DECK, HULL, WATER }

class Hole:
	var length := 0
	var step := 8
	## Высота поверхности в точке `i` (x = i * step); у моря дно пролива ниже экрана.
	var heights: PackedFloat32Array = []
	## Вид отрезка `i` (от точки `i` до `i + 1`), значения `Kind`.
	var kinds: PackedByteArray = []
	## Мяч на ти: x середины помоста.
	var tee_x := 0.0
	var cup_x := 0.0
	## Грин (палуба корабля) и пролив по x; пролива нет: `water_from` < 0.
	var green_from := 0.0
	var green_to := 0.0
	var water_from := -1.0
	var water_to := -1.0
	var par := 3
	## Ветер целыми делениями, плюс дует вправо.
	var wind := 0
	## Пропы на песке: x середины и вид (0 пушка, 1 сундук).
	var props: Array[Vector2i] = []

	func height_at(x: float) -> float:
		var f := clampf(x, 0.0, float(length)) / step
		var i := mini(int(f), heights.size() - 2)
		return lerpf(heights[i], heights[i + 1], f - i)

	## Наклон поверхности dy/dx в точке (плюс: вправо вниз).
	func slope_at(x: float) -> float:
		var i := clampi(int(x / step), 0, heights.size() - 2)
		return (heights[i + 1] - heights[i]) / step

	func kind_at(x: float) -> Kind:
		return kinds[clampi(int(x / step), 0, kinds.size() - 1)] as Kind

	func has_water() -> bool:
		return water_from >= 0.0


var holes: Array[Hole] = []
## Уровень моря в проливах (y).
var sea_y := 150.0
## Попыток генератора до годного поля; запасное поле без пролива и холмов.
var attempts := 1
var fallback := false


func total_par() -> int:
	var p := 0
	for h in holes:
		p += h.par
	return p
