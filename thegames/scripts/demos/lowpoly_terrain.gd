class_name LowpolyTerrain
extends RefCounted
## Неровная земля для демок low poly и 3D (#108): сетка высот, грани угловатые (у каждого
## треугольника своя нормаль). Демка задаёт высоты в узлах сетки, спрашивает высоту под точкой
## (`height_at`, по тем же треугольникам, что нарисованы) и строит меш с юбкой-обрывом по краю
## (`build`).

## Угол сетки с меньшими x и z; высоты считаются от `origin.y`.
var origin := Vector3.ZERO
var cell := 1.0
## Клеток по x и z; узлов на один больше.
var nx := 1
var nz := 1
var heights := PackedFloat32Array()


static func make(origin_: Vector3, cell_: float, nx_: int, nz_: int) -> LowpolyTerrain:
	var t := LowpolyTerrain.new()
	t.origin = origin_
	t.cell = cell_
	t.nx = nx_
	t.nz = nz_
	t.heights.resize((nx_ + 1) * (nz_ + 1))
	return t


func size() -> Vector2:
	return Vector2(nx, nz) * cell


func center() -> Vector3:
	return origin + Vector3(nx * cell / 2.0, 0.0, nz * cell / 2.0)


func set_h(ix: int, iz: int, h: float) -> void:
	heights[iz * (nx + 1) + ix] = h


func get_h(ix: int, iz: int) -> float:
	return heights[clampi(iz, 0, nz) * (nx + 1) + clampi(ix, 0, nx)]


func node(ix: int, iz: int) -> Vector3:
	return origin + Vector3(ix * cell, get_h(ix, iz), iz * cell)


func inside(x: float, z: float) -> bool:
	return x >= origin.x and x <= origin.x + nx * cell and z >= origin.z and z <= origin.z + nz * cell


## Высота земли под точкой в мире; снаружи сетки высота ближайшего края.
func height_at(x: float, z: float) -> float:
	var gx := clampf((x - origin.x) / cell, 0.0, nx - 0.0001)
	var gz := clampf((z - origin.z) / cell, 0.0, nz - 0.0001)
	var ix := int(gx)
	var iz := int(gz)
	var fx := gx - ix
	var fz := gz - iz
	var h00 := get_h(ix, iz)
	var h10 := get_h(ix + 1, iz)
	var h01 := get_h(ix, iz + 1)
	var h11 := get_h(ix + 1, iz + 1)
	if fx <= fz:
		return origin.y + h00 + (h11 - h01) * fx + (h01 - h00) * fz
	return origin.y + h00 + (h10 - h00) * fx + (h11 - h10) * fz


## Меш земли с текстурой `top` и обрывом `skirt` по краю вниз до высоты `bottom` в мире.
func build(screen: LowpolyScreen, top: Texture2D, tile := 2.0, skirt: Texture2D = null, bottom := 0.0) -> Node3D:
	var root := Node3D.new()
	var verts := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	for iz in nz:
		for ix in nx:
			var p00 := node(ix, iz)
			var p10 := node(ix + 1, iz)
			var p01 := node(ix, iz + 1)
			var p11 := node(ix + 1, iz + 1)
			for tri: Array in [[p00, p01, p11], [p00, p11, p10]]:
				var n := ((tri[1] as Vector3) - (tri[0] as Vector3)).cross((tri[2] as Vector3) - (tri[0] as Vector3)).normalized()
				for p: Vector3 in tri:
					LowpolyScreen.push(verts, normals, uvs, p, n, Vector2(p.x, p.z) / tile)
			LowpolyScreen.flip_last(verts, normals, uvs, 2)
	var ground := MeshInstance3D.new()
	ground.mesh = LowpolyScreen._commit(verts, normals, uvs, screen.tex_material(top))
	root.add_child(ground)
	if skirt != null:
		var sv := PackedVector3Array()
		var sn := PackedVector3Array()
		var su := PackedVector2Array()
		# Обход края по часовой стрелке, если смотреть сверху: стенка смотрит наружу.
		var rim: Array[Vector2i] = []
		for ix in range(0, nx):
			rim.append(Vector2i(ix, 0))
		for iz in range(0, nz):
			rim.append(Vector2i(nx, iz))
		for ix in range(nx, 0, -1):
			rim.append(Vector2i(ix, nz))
		for iz in range(nz, 0, -1):
			rim.append(Vector2i(0, iz))
		var along := 0.0
		for i in rim.size():
			var a := node(rim[i].x, rim[i].y)
			var b := node(rim[(i + 1) % rim.size()].x, rim[(i + 1) % rim.size()].y)
			var a0 := Vector3(a.x, bottom, a.z)
			var b0 := Vector3(b.x, bottom, b.z)
			var n := (b - a).cross(Vector3.UP).normalized() * -1.0
			var len := Vector2(b.x - a.x, b.z - a.z).length()
			for item: Array in [[a0, 0.0], [a, 0.0], [b, len], [a0, 0.0], [b, len], [b0, len]]:
				var p: Vector3 = item[0]
				LowpolyScreen.push(sv, sn, su, p, n, Vector2(along + float(item[1]), -p.y) / tile)
			LowpolyScreen.flip_last(sv, sn, su, 2)
			along += len
		var wall := MeshInstance3D.new()
		wall.mesh = LowpolyScreen._commit(sv, sn, su, screen.tex_material(skirt))
		root.add_child(wall)
	screen.world.add_child(root)
	return root
