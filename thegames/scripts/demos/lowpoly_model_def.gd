class_name LowpolyModelDef
extends Resource
## Меш слота сеттинга для low poly и 3D (#108): части с точками вращения, треугольники с
## нормалями и развёрткой, атлас модели низкого разрешения. Файл и атлас пишет
## `tools/lowpoly_meshes.py`, руками не правятся. Low poly рисует его шейдером эпохи первой
## PlayStation (`LowpolyScreen`), 3D возьмёт те же треугольники со своим материалом (#118).

## Атлас модели: 64×64 или меньше, без сглаживания.
@export var texture: Texture2D
## Имена частей; `leg_l`, `leg_r`, `arm_l`, `arm_r` качает `LowpolyModel.walk`.
@export var part_names := PackedStringArray()
## Родитель части (индекс) или −1.
@export var part_parents := PackedInt32Array()
## Точка вращения части относительно точки вращения родителя (у корневых от нуля модели).
@export var part_pivots := PackedVector3Array()
## Сколько треугольников у части; идут подряд в `vertices`, `normals` и `uvs`.
@export var part_tris := PackedInt32Array()
## По три вершины на треугольник в координатах части, против часовой стрелки наружу.
@export var vertices := PackedVector3Array()
## Нормаль каждой вершины: округлая у тел, гранёная у ящиков и камней.
@export var normals := PackedVector3Array()
## Развёртка каждой вершины в долях атласа.
@export var uvs := PackedVector2Array()


func triangles() -> int:
	return vertices.size() / 3


func part_index(name: StringName) -> int:
	return part_names.find(String(name))


## Точка вращения части в координатах модели.
func pivot_of(part: int) -> Vector3:
	var p := Vector3.ZERO
	var i := part
	while i >= 0 and i < part_pivots.size():
		p += part_pivots[i]
		i = part_parents[i]
	return p


## Габариты модели в её координатах.
func bounds() -> AABB:
	var box := AABB()
	var first := true
	var v := 0
	for part in part_tris.size():
		var pivot := pivot_of(part)
		for k in part_tris[part] * 3:
			var p := vertices[v] + pivot
			v += 1
			if first:
				box = AABB(p, Vector3.ZERO)
				first = false
			else:
				box = box.expand(p)
	return box
