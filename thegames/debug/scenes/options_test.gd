extends Control
## Тестовая сцена настроек (#81): экран настроек на фоне. Под ботом: шины музыки и звуков есть,
## громкость шагом 10 % и до тишины, переключатели, подписи клавиш по кругу, «Готово»
## закрывает. Файл настроек под автотестом не пишется. `--no-checks` держит экран.

var screen: OptionsScreen
var _closed := false


func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	screen = OptionsScreen.new()
	screen.closed.connect(func() -> void: _closed = true)
	add_child(screen)
	var args := AutoTest.parse_args(OS.get_cmdline_user_args())
	if args.has("no-checks"):
		AutoTest.bot_mode = AutoTest.BotMode.OFF
		return
	AutoTest.require("options checks")
	_check.call_deferred()


func _check() -> void:
	_expect(AudioServer.get_bus_index(Options.MUSIC_BUS) > 0 and AudioServer.get_bus_index(Options.SFX_BUS) > 0, "шины")
	var music := Options.music
	screen.change(OptionsScreen.Row.MUSIC, -1)
	_expect(is_equal_approx(Options.music, music - 0.1), "музыка −10 %%: %.2f" % Options.music)
	for i in 12:
		screen.change(OptionsScreen.Row.MUSIC, -1)
	var bus := AudioServer.get_bus_index(Options.MUSIC_BUS)
	_expect(Options.music == 0.0 and AudioServer.is_bus_mute(bus), "музыка до тишины, шина заглушена")
	screen.set_volume(OptionsScreen.Row.SFX, 0.5)
	_expect(is_equal_approx(AudioServer.get_bus_volume_db(AudioServer.get_bus_index(Options.SFX_BUS)), linear_to_db(0.5)),
			"звуки 50 %% в шине")
	var motion := Options.motion
	screen.change(OptionsScreen.Row.MOTION, 1)
	_expect(Options.motion != motion and Jelly.enabled == Options.motion, "движение переключилось")
	screen.change(OptionsScreen.Row.MOTION, 1)
	screen.change(OptionsScreen.Row.GLYPHS, 1)
	_expect(Options.glyphs == Options.Glyphs.KEYBOARD and GameInput.device == GameInput.Device.KEYBOARD, "подписи: клавиатура")
	screen.change(OptionsScreen.Row.GLYPHS, 1)
	_expect(GameInput.device == GameInput.Device.GAMEPAD, "подписи: геймпад")
	screen.change(OptionsScreen.Row.GLYPHS, 1)
	screen.close()
	_expect(_closed, "«Готово» закрывает")
	_expect(not FileAccess.file_exists(Options.PATH) or FileAccess.get_modified_time(Options.PATH) < Time.get_unix_time_from_system() - 5,
			"файл настроек под автотестом не тронут")
	AutoTest.note("options: шины, громкость, тишина, движение, подписи, закрытие")
	AutoTest.fulfill("options checks")


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("options: " + what)
