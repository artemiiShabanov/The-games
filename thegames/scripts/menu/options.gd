class_name Options
extends RefCounted
## Настройки игры (#81), `user://settings.cfg`: громкость общая, музыки и звуков (шины
## `Master`, `Music`, `Sfx`), окно или полный экран, движение интерфейса (мармелад и студия,
## `Jelly.enabled`), подписи клавиш (авто, клавиатура, геймпад). Применяются сразу
## (`apply`). Под автотестом файл не читается и не пишется: прогоны идут с умолчаниями и не
## трогают настройки игрока.

const PATH := "user://settings.cfg"
const MUSIC_BUS: StringName = &"Music"
const SFX_BUS: StringName = &"Sfx"

enum Glyphs { AUTO, KEYBOARD, GAMEPAD }

const GLYPH_NAMES: Array[String] = ["авто", "клавиатура", "геймпад"]

static var master := 1.0
static var music := 0.8
static var sfx := 0.9
static var fullscreen := false
static var motion := true
static var glyphs := Glyphs.AUTO


## На старте игры: шины, чтение файла, применение.
static func boot() -> void:
	ensure_buses()
	if not _auto_test():
		load_saved()
	apply()


## Автотест по командной строке: автолоад `UiTheme` стартует раньше `AutoTest`.
static func _auto_test() -> bool:
	return OS.get_cmdline_user_args().has("--auto-test")


## Шины музыки и звуков под `Master`, если их ещё нет.
static func ensure_buses() -> void:
	for bus in [MUSIC_BUS, SFX_BUS]:
		if AudioServer.get_bus_index(bus) < 0:
			AudioServer.add_bus()
			var i := AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, bus)
			AudioServer.set_bus_send(i, &"Master")


static func load_saved() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(PATH) != OK:
		return
	master = clampf(float(cfg.get_value("audio", "master", master)), 0.0, 1.0)
	music = clampf(float(cfg.get_value("audio", "music", music)), 0.0, 1.0)
	sfx = clampf(float(cfg.get_value("audio", "sfx", sfx)), 0.0, 1.0)
	fullscreen = bool(cfg.get_value("video", "fullscreen", fullscreen))
	motion = bool(cfg.get_value("video", "motion", motion))
	glyphs = clampi(int(cfg.get_value("input", "glyphs", glyphs)), 0, Glyphs.size() - 1) as Glyphs


static func save() -> void:
	if _auto_test():
		return
	var cfg := ConfigFile.new()
	cfg.set_value("audio", "master", master)
	cfg.set_value("audio", "music", music)
	cfg.set_value("audio", "sfx", sfx)
	cfg.set_value("video", "fullscreen", fullscreen)
	cfg.set_value("video", "motion", motion)
	cfg.set_value("input", "glyphs", int(glyphs))
	cfg.save(PATH)


static func apply() -> void:
	_volume(&"Master", master)
	_volume(MUSIC_BUS, music)
	_volume(SFX_BUS, sfx)
	if not _auto_test() and DisplayServer.get_name() != "headless":
		var mode := DisplayServer.WINDOW_MODE_FULLSCREEN if fullscreen else DisplayServer.WINDOW_MODE_WINDOWED
		if DisplayServer.window_get_mode() != mode:
			DisplayServer.window_set_mode(mode)
	Jelly.enabled = motion
	match glyphs:
		Glyphs.KEYBOARD:
			GameInput.device = GameInput.Device.KEYBOARD
		Glyphs.GAMEPAD:
			GameInput.device = GameInput.Device.GAMEPAD
		_:
			GameInput.device = GameInput.Device.GAMEPAD if not Input.get_connected_joypads().is_empty() else GameInput.Device.KEYBOARD


static func _volume(bus: StringName, v: float) -> void:
	var i := AudioServer.get_bus_index(bus)
	if i < 0:
		return
	# Автотест глушит `Master` сам; не снимаем его глушение.
	if bus == &"Master" and _auto_test():
		return
	AudioServer.set_bus_mute(i, v <= 0.001)
	AudioServer.set_bus_volume_db(i, linear_to_db(maxf(v, 0.001)))
