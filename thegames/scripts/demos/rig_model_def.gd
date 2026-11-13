class_name RigModelDef
extends Resource
## Модель «продвинутых» на скелете (#119): цельная сетка с общими вершинами, у каждой вершины до
## четырёх костей с весами и доля ткани; скелет (имена, родители, места костей в покое в
## координатах модели); пружинные кости; текстура цвета и карта рельефа. Пишет
## `tools/rig_models.py`, в сцену собирает `RigModel`.

@export var texture: Texture2D
@export var normal_map: Texture2D
@export var bone_names := PackedStringArray()
@export var bone_parents := PackedInt32Array()
## Место кости в покое в координатах модели (не родителя).
@export var bone_rests := PackedVector3Array()
## Пружинные кости и их числа: жёсткость, затухание, тяжесть.
@export var spring_bones := PackedStringArray()
@export var spring_params := PackedVector3Array()
## Куда в покое смотрит хвост пружинной кости, в осях модели.
@export var spring_dirs := PackedVector3Array()
@export var vertices := PackedVector3Array()
@export var normals := PackedVector3Array()
@export var uvs := PackedVector2Array()
## Доля ткани у вершины, 0..1: колыхание в шейдере.
@export var cloth := PackedFloat32Array()
## По четыре на вершину.
@export var bones := PackedInt32Array()
@export var weights := PackedFloat32Array()
## Треугольники: против часовой стрелки наружу.
@export var indices := PackedInt32Array()


func triangles() -> int:
	return indices.size() / 3


func bounds() -> AABB:
	if vertices.is_empty():
		return AABB()
	var box := AABB(vertices[0], Vector3.ZERO)
	for v in vertices:
		box = box.expand(v)
	return box
