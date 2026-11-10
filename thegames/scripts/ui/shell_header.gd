class_name ShellHeader
extends RefCounted
## Текст пилюли шапки оболочки (#61): название студии забега перед остальным, «Ленивый Енот ·
## Релиз 3 · Студия». Название ставит главная сцена, когда студия основана; пока его нет
## (тестовые сцены, экран «Новая студия»), шапка без него.

static var studio := ""


static func text(rest: String) -> String:
	return rest if studio == "" else "%s · %s" % [studio, rest]


static func release(n: int, rest: String) -> String:
	return text("Релиз %d · %s" % [n, rest])
