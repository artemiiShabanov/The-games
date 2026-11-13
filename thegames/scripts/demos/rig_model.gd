class_name RigModel
extends Node3D
## Модель на скелете в сцене «продвинутых» (#119): `Skeleton3D` с костями из `RigModelDef` и одна
## сетка со скиннингом. Позы задаются углами суставов (`joint`, `pose`): у всех костей оси в покое
## совпадают с осями модели, поэтому угол вокруг X у плеча или бедра это мах вперёд, как у
## `LowpolyModel`. Заданная поза это цель: суставы идут к ней плавно со скоростью `smooth` (чем
## больше, тем резче; `snap` ставит позу сразу), поэтому смена поз в демке не даёт рывков, а
## удар всё равно выходит быстрым. Пружинные кости (хвост банданы, полы одежды) сами догоняют движение родителя и
## доколебываются; ткань колышется в шейдере по доле `cloth` вершины. Создаёт `make`.

const SHADER := preload("res://scripts/demos/threed.gdshader")

var def: RigModelDef
var skeleton: Skeleton3D
var mesh_node: MeshInstance3D
var material: ShaderMaterial
## Скорость, с которой суставы догоняют позу, 1/с; 0 ставит позу сразу.
var smooth := 14.0
var _ids: Dictionary[StringName, int] = {}
## Цели суставов: поворот и сдвиг таза от места в покое.
var _targets: Dictionary[int, Quaternion] = {}
var _lift := Vector3.ZERO
var _lift_now := Vector3.ZERO
var _flash: ShaderMaterial
## Пружинные кости: номер, направление хвоста в мире сейчас, скорость, числа.
var _springs: Array[Dictionary] = []


static func make(def_: RigModelDef, look: ThreedTuning = null) -> RigModel:
	var m := RigModel.new()
	m.def = def_
	m._build(look if look != null else ThreedTuning.load_default())
	return m


func _build(look: ThreedTuning) -> void:
	skeleton = Skeleton3D.new()
	add_child(skeleton)
	for i in def.bone_names.size():
		skeleton.add_bone(def.bone_names[i])
		_ids[StringName(def.bone_names[i])] = i
	for i in def.bone_names.size():
		var parent := def.bone_parents[i]
		if parent >= 0:
			skeleton.set_bone_parent(i, parent)
		# Покой: кость стоит в своём месте без поворота, место относительно родителя.
		var local := def.bone_rests[i] - (def.bone_rests[parent] if parent >= 0 else Vector3.ZERO)
		skeleton.set_bone_rest(i, Transform3D(Basis.IDENTITY, local))
		skeleton.set_bone_pose_position(i, local)
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = def.vertices
	arrays[Mesh.ARRAY_NORMAL] = def.normals
	arrays[Mesh.ARRAY_TEX_UV] = def.uvs
	# Доля ткани едет во второй развёртке: у сеток уровня её нет, там колыхания не будет.
	var uv2 := PackedVector2Array()
	for c in def.cloth:
		uv2.append(Vector2(c, 0.0))
	arrays[Mesh.ARRAY_TEX_UV2] = uv2
	arrays[Mesh.ARRAY_BONES] = def.bones
	arrays[Mesh.ARRAY_WEIGHTS] = def.weights
	# В файле против часовой стрелки наружу, у Godot лицевая сторона по часовой.
	var indices := PackedInt32Array()
	for t in def.triangles():
		indices.append(def.indices[t * 3])
		indices.append(def.indices[t * 3 + 2])
		indices.append(def.indices[t * 3 + 1])
	arrays[Mesh.ARRAY_INDEX] = indices
	var raw := ArrayMesh.new()
	raw.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	# Касательные для карты рельефа.
	var tool := SurfaceTool.new()
	tool.create_from(raw, 0)
	tool.generate_tangents()
	var mesh := tool.commit()
	material = ShaderMaterial.new()
	material.shader = SHADER
	material.set_shader_parameter("tex", def.texture)
	material.set_shader_parameter("normal_tex", def.normal_map)
	material.set_shader_parameter("normal_strength", look.normal_strength)
	material.set_shader_parameter("cloth_sway", look.cloth_sway)
	material.set_shader_parameter("rim", look.rim)
	material.set_shader_parameter("rough", look.rough)
	mesh.surface_set_material(0, material)
	mesh_node = MeshInstance3D.new()
	mesh_node.mesh = mesh
	skeleton.add_child(mesh_node)
	mesh_node.skin = skeleton.create_skin_from_rest_transforms()
	mesh_node.skeleton = NodePath("..")
	_flash = ShaderMaterial.new()
	_flash.shader = SHADER
	_flash.set_shader_parameter("flash", 1.0)
	for i in def.spring_bones.size():
		var id: int = _ids.get(StringName(def.spring_bones[i]), -1)
		if id >= 0:
			_springs.append({"id": id, "dir": Vector3.DOWN, "vel": Vector3.ZERO, "ready": false, "params": def.spring_params[i]})


func has_joint(name: StringName) -> bool:
	return _ids.has(name)


## Поворот сустава: углы Эйлера в радианах в осях модели.
func joint(name: StringName, euler: Vector3) -> void:
	var id: int = _ids.get(name, -1)
	if id >= 0:
		_targets[id] = Quaternion.from_euler(euler)
		if smooth <= 0.0:
			skeleton.set_bone_pose_rotation(id, _targets[id])


## Поза словарём: сустав → угол вокруг X (мах вперёд) или три угла.
func pose(angles: Dictionary) -> void:
	for name: StringName in angles:
		var value: Variant = angles[name]
		joint(name, value if value is Vector3 else Vector3(float(value), 0.0, 0.0))


## Шаг: ноги и руки в противофазе со сгибом коленей и локтей, корпус и голова слегка
## доворачиваются навстречу. `swing` размах в радианах, 0 ставит ровно.
func walk(phase: float, swing := 0.7) -> void:
	var s := sin(phase) * swing
	var lift := cos(phase)
	var bend := minf(swing / 0.5, 1.0)
	pose({&"leg_l": s, &"leg_r": -s, &"shin_l": -maxf(lift, 0.0) * swing * 1.3 - 0.08 * bend,
			&"shin_r": -maxf(-lift, 0.0) * swing * 1.3 - 0.08 * bend, &"arm_l": -s * 0.8, &"arm_r": s * 0.8,
			&"fore_l": 0.45 * bend + maxf(-s, 0.0) * 0.5, &"fore_r": 0.45 * bend + maxf(s, 0.0) * 0.5,
			&"foot_l": maxf(-s, 0.0) * 0.5, &"foot_r": maxf(s, 0.0) * 0.5})
	joint(&"spine", Vector3(0.04 * bend, -s * 0.12, 0.0))
	joint(&"chest", Vector3(0.0, -s * 0.14, 0.0))
	joint(&"head", Vector3(0.0, s * 0.18, 0.0))
	joint(&"hips", Vector3(0.0, s * 0.1, absf(sin(phase)) * 0.0))
	_lift = Vector3(0.0, absf(lift) * 0.025 * bend, 0.0)


## Белая заливка на кадр попадания.
func flash(on: bool) -> void:
	mesh_node.material_overlay = _flash if on else null


## Поставить заданную позу сразу, без доводки.
func snap() -> void:
	for id: int in _targets:
		skeleton.set_bone_pose_rotation(id, _targets[id])
	_lift_now = _lift
	_place_hips()


func _place_hips() -> void:
	var hips: int = _ids.get(&"hips", -1)
	if hips >= 0:
		skeleton.set_bone_pose_position(hips, def.bone_rests[hips] + _lift_now)


func _process(delta: float) -> void:
	var dt := minf(delta, 0.05)
	if smooth > 0.0:
		# Суставы догоняют цель по кратчайшей дуге: доля пути за кадр не зависит от частоты кадров.
		var k := 1.0 - exp(-smooth * dt)
		for id: int in _targets:
			skeleton.set_bone_pose_rotation(id, skeleton.get_bone_pose_rotation(id).slerp(_targets[id], k))
		_lift_now = _lift_now.lerp(_lift, k)
		_place_hips()
	_step_springs(dt)


## Пружинная кость: её хвост в мире запаздывает за движением родителя, тянется к покою пружиной
## и вниз тяжестью; кость поворачивается так, чтобы смотреть на хвост.
func _step_springs(dt: float) -> void:
	if dt <= 0.0:
		return
	for s in _springs:
		var id: int = s["id"]
		var parent := skeleton.get_bone_parent(id)
		var parent_pose := skeleton.global_transform * (skeleton.get_bone_global_pose(parent) if parent >= 0 else Transform3D.IDENTITY)
		var params: Vector3 = s["params"]
		# В покое хвост висит вниз и чуть назад от кости.
		var rest_dir := (parent_pose.basis * Vector3(0.0, -1.0, 0.35)).normalized()
		var origin := parent_pose * skeleton.get_bone_rest(id).origin
		if not s["ready"]:
			s["ready"] = true
			s["dir"] = rest_dir
			s["tip"] = origin + rest_dir * 0.2
		var tip: Vector3 = s["tip"]
		var vel: Vector3 = s["vel"]
		var want := origin + rest_dir * 0.2
		vel += ((want - tip) * params.x + Vector3.DOWN * params.z * 9.8) * dt
		vel *= maxf(1.0 - params.y * dt, 0.0)
		tip += vel * dt
		# Длина ленты постоянна.
		var dir := (tip - origin).normalized() if tip.distance_to(origin) > 0.001 else rest_dir
		tip = origin + dir * 0.2
		s["tip"] = tip
		s["vel"] = vel
		var local_dir := parent_pose.basis.inverse() * dir
		var base := Vector3(0.0, -1.0, 0.35).normalized()
		skeleton.set_bone_pose_rotation(id, Quaternion(base, local_dir.normalized()))
