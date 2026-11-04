class_name Screenshot
extends RefCounted
## Сохранение кадра вьюпорта в PNG. Вызывать после `await RenderingServer.frame_post_draw`.
## Относительный путь считается от корня проекта (`res://`).


static func save(viewport: Viewport, path: String) -> Error:
	var abs_path := path
	if path.is_relative_path():
		abs_path = ProjectSettings.globalize_path("res://" + path)
	elif path.begins_with("res://") or path.begins_with("user://"):
		abs_path = ProjectSettings.globalize_path(path)
	var dir_err := DirAccess.make_dir_recursive_absolute(abs_path.get_base_dir())
	if dir_err != OK:
		return dir_err
	var image := viewport.get_texture().get_image()
	if image == null or image.is_empty():
		return ERR_UNAVAILABLE
	return image.save_png(abs_path)


static func absolute(path: String) -> String:
	if path.is_relative_path():
		return ProjectSettings.globalize_path("res://" + path)
	return ProjectSettings.globalize_path(path)
