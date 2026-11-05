extends SceneTree
## Задать мини-игре сцену и линейные кривые параметров от `t` (0 → 1). Потом кривые правятся
## в инспекторе, скрипт только для первого заполнения.
##   Godot --headless --path thegames -s debug/tools/set_params.gd -- fit_frame \
##       tscn=res://scenes/minigames/fit_frame.tscn shapes=6:8 rise=1.0:1.6
## Работа идёт в первом кадре, а не в `_init`: к этому моменту автолоады уже есть и сцены
## мини-игр компилируются.

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	var ok := _apply(OS.get_cmdline_user_args())
	quit(0 if ok else 1)
	return true


func _apply(args: PackedStringArray) -> bool:
	if args.size() < 2:
		push_error("set_params: нужно <id> и хотя бы одна пара key=from:to или tscn=path")
		return false
	var path := MinigamePool.DIR + args[0] + ".tres"
	var def := load(path) as MinigameDef
	if def == null:
		push_error("set_params: нет ресурса " + path)
		return false
	for a in args.slice(1):
		var kv := a.split("=", true, 1)
		if kv.size() != 2:
			continue
		if kv[0] == "tscn":
			def.scene = load(kv[1]) as PackedScene
			continue
		var ft := kv[1].split(":")
		var from := float(ft[0])
		var to := float(ft[1]) if ft.size() > 1 else from
		var curve := Curve.new()
		curve.min_value = minf(from, to)
		curve.max_value = maxf(from, to)
		curve.add_point(Vector2(0.0, from))
		curve.add_point(Vector2(1.0, to))
		def.params[StringName(kv[0])] = curve
	var err := ResourceSaver.save(def, path)
	print("set_params: %s %s" % [path, error_string(err)])
	return err == OK
