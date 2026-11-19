class_name CoverBaker
extends Node
## Плоские слепки моделей для стикеров обложки: свой маленький 3D-вьюпорт с прозрачным фоном,
## модель в три четверти под ровным светом, кадр обрезается по непрозрачному и кладётся в
## готовую текстуру стикера. Очередь по одной модели, узел живёт в корне дерева.

## Модели смотрят на −Z: камера спереди и чуть сбоку.
const YAW := PI - 0.62
const PITCH := -0.3

var _queue: Array[Dictionary] = []
var _busy := false
var _viewport: SubViewport
var _camera: Camera3D
var _holder: Node3D


## Слепок жёсткой модели слота; `smooth` это «продвинутые»: гладкая текстура, рельеф, блик.
func add(model: LowpolyModelDef, target: ImageTexture, px: int, pad: int, smooth: bool) -> void:
	_queue.append({"mesh": _mesh(model, smooth), "bounds": model.bounds(), "target": target, "px": px, "pad": pad})


## Слепок модели на скелете («продвинутые», #119) в позе покоя: та же, что в игре.
func add_rig(rig: RigModelDef, target: ImageTexture, px: int, pad: int) -> void:
	_queue.append({"mesh": _rig_mesh(rig), "bounds": rig.bounds(), "target": target, "px": px, "pad": pad})


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_viewport = SubViewport.new()
	_viewport.own_world_3d = true
	_viewport.transparent_bg = true
	_viewport.msaa_3d = Viewport.MSAA_4X
	_viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED
	add_child(_viewport)
	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color.WHITE
	env.ambient_light_energy = 0.75
	var world := WorldEnvironment.new()
	world.environment = env
	_viewport.add_child(world)
	var sun := DirectionalLight3D.new()
	sun.rotation = Vector3(-0.7, -0.6, 0.0)
	sun.light_energy = 0.7
	_viewport.add_child(sun)
	_camera = Camera3D.new()
	_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	_viewport.add_child(_camera)
	_holder = Node3D.new()
	_viewport.add_child(_holder)


func _process(_delta: float) -> void:
	if not _busy and not _queue.is_empty():
		_run(_queue.pop_front())


func _run(job: Dictionary) -> void:
	_busy = true
	var px: int = job["px"]
	_viewport.size = Vector2i(px, px)
	for child in _holder.get_children():
		child.queue_free()
	var node := MeshInstance3D.new()
	node.mesh = job["mesh"]
	_holder.add_child(node)
	var box: AABB = job["bounds"]
	var center := box.get_center()
	var radius := maxf(box.size.length() * 0.5, 0.05)
	var dir := Vector3(sin(YAW) * cos(PITCH), -sin(PITCH), cos(YAW) * cos(PITCH))
	_camera.size = radius * 2.0
	_camera.near = 0.01
	_camera.far = radius * 6.0
	_camera.position = center + dir * radius * 3.0
	_camera.look_at(center, Vector3.UP)
	_viewport.render_target_update_mode = SubViewport.UPDATE_ONCE
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var img := _viewport.get_texture().get_image()
	var target: ImageTexture = job["target"]
	if img != null and not img.is_empty() and is_instance_valid(target):
		img.convert(Image.FORMAT_RGBA8)
		var used := img.get_used_rect()
		if used.has_area():
			var pad: int = job["pad"]
			var out := Image.create_empty(used.size.x + pad * 2, used.size.y + pad * 2, false, Image.FORMAT_RGBA8)
			out.blit_rect(img, used, Vector2i(pad, pad))
			target.set_image(out)
			target.emit_changed()
	_busy = false


## Меш модели одной поверхностью: части сдвинуты на свои точки вращения, поза покоя.
func _mesh(def: LowpolyModelDef, smooth: bool) -> ArrayMesh:
	var verts := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var t := 0
	for part in def.part_tris.size():
		var pivot := def.pivot_of(part)
		for i in def.part_tris[part]:
			# В файле против часовой стрелки наружу, у Godot лицевая сторона по часовой.
			for k: int in [0, 2, 1]:
				verts.append(def.vertices[t * 3 + k] + pivot)
				normals.append(def.normals[t * 3 + k])
				uvs.append(def.uvs[t * 3 + k])
			t += 1
	return _commit(verts, normals, uvs, PackedInt32Array(), def.texture, _normal_map(def.texture) if smooth else null, smooth)


func _rig_mesh(rig: RigModelDef) -> ArrayMesh:
	var indices := PackedInt32Array()
	for t in rig.triangles():
		indices.append(rig.indices[t * 3])
		indices.append(rig.indices[t * 3 + 2])
		indices.append(rig.indices[t * 3 + 1])
	return _commit(rig.vertices, rig.normals, rig.uvs, indices, rig.texture, rig.normal_map, true)


## Карта рельефа плотной модели лежит рядом с атласом: `<имя>_n.png`.
func _normal_map(tex: Texture2D) -> Texture2D:
	if tex == null or tex.resource_path == "":
		return null
	var path := tex.resource_path.get_basename() + "_n." + tex.resource_path.get_extension()
	return load(path) as Texture2D if ResourceLoader.exists(path) else null


func _commit(verts: PackedVector3Array, normals: PackedVector3Array, uvs: PackedVector2Array, indices: PackedInt32Array,
		tex: Texture2D, normal_map: Texture2D, smooth: bool) -> ArrayMesh:
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	if not indices.is_empty():
		arrays[Mesh.ARRAY_INDEX] = indices
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	if normal_map != null:
		# Касательные для карты рельефа.
		var tool := SurfaceTool.new()
		tool.create_from(mesh, 0)
		tool.generate_tangents()
		mesh = tool.commit()
	var mat := StandardMaterial3D.new()
	mat.albedo_texture = tex
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS if smooth else BaseMaterial3D.TEXTURE_FILTER_NEAREST
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	if smooth:
		# «Продвинутые»: рельеф, блик и свет по краю, чтобы слепок не путался с 3D эпохи PS1.
		mat.roughness = 0.55
		mat.rim_enabled = true
		mat.rim = 0.35
		if normal_map != null:
			mat.normal_enabled = true
			mat.normal_texture = normal_map
	else:
		mat.roughness = 1.0
		mat.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	mesh.surface_set_material(0, mat)
	return mesh
