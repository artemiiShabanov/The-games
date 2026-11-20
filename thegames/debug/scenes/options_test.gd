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
	# Палитра (2026-11-17): по кругу через все, смысловые цвета и акценты меняются сразу.
	var pal := Options.palette
	var focus := Style.FOCUS
	screen.change(OptionsScreen.Row.PALETTE, 1)
	_expect(Options.palette != pal and Style.palette.id == Options.palette and Style.FOCUS != focus,
			"палитра переключилась: %s" % Options.palette)
	_expect(Style.accents.size() == 5 and Style.accent_name(2) != "", "у палитры пять акцентов с именами")
	for k in Style.PALETTE_IDS.size() - 1:
		screen.change(OptionsScreen.Row.PALETTE, 1)
	_expect(Options.palette == pal and Style.FOCUS == focus, "палитры по кругу")
	# Язык (2026-11-18): по кругу, перевод сразу; на русском английский файл не подмешивается.
	var lang := Lang.current()
	var changed := [0]
	screen.language_changed.connect(func() -> void: changed[0] += 1)
	screen.change(OptionsScreen.Row.LANGUAGE, 1)
	_expect(Options.language == "en" and TranslationServer.get_locale() == "en" and changed[0] == 1,
			"язык: английский, %s" % TranslationServer.get_locale())
	_expect(tr("Настройки") == "Options" and screen.tr("Готово") == "Done", "английский перевод: %s" % tr("Настройки"))
	screen.change(OptionsScreen.Row.LANGUAGE, 1)
	_expect(Lang.current() == lang and tr("Настройки") == "Настройки", "язык по кругу назад, русский без подмеса")
	# Чувствительность обзора (#109): шагом 10 %, полосой по месту, в границах 0..1.
	var look := Options.mouse_look
	screen.change(OptionsScreen.Row.MOUSE_LOOK, 1)
	_expect(is_equal_approx(Options.mouse_look, look + 0.1), "обзор мышью +10 %%: %.2f" % Options.mouse_look)
	screen.set_volume(OptionsScreen.Row.STICK_LOOK, 2.0)
	_expect(is_equal_approx(Options.stick_look, 1.0), "обзор стиком за границей: %.2f" % Options.stick_look)
	Options.mouse_look = look
	Options.stick_look = 0.5
	# Выгрузка статистики мини-игр: пустой журнал не пишет файл, строка журнала уходит в CSV.
	MinigameStats.clear()
	screen.change(OptionsScreen.Row.STATS, 1)
	_expect(screen.stats_file == "", "пустая статистика выгрузилась: %s" % screen.stats_file)
	var f := FileAccess.open(MinigameStats.path(), FileAccess.WRITE)
	f.store_line(JSON.stringify({"minigame": "stack", "t": 0.5, "mistakes": 2, "bug": true, "details": "a, b"}))
	f.close()
	screen.change(OptionsScreen.Row.STATS, 1)
	var csv := FileAccess.get_file_as_string(screen.stats_file).split("\n", false)
	_expect(csv.size() == 2 and csv[0].begins_with("time,session,context") and csv[1].contains("stack")
			and csv[1].contains(",0.5,") and csv[1].contains("\"a, b\""), "выгрузка статистики: %s" % [csv])
	if screen.stats_file != "":
		DirAccess.remove_absolute(screen.stats_file)
	MinigameStats.clear()
	screen.close()
	_expect(_closed, "«Готово» закрывает")
	_expect(not FileAccess.file_exists(Options.PATH) or FileAccess.get_modified_time(Options.PATH) < Time.get_unix_time_from_system() - 5,
			"файл настроек под автотестом не тронут")
	AutoTest.note("options: шины, громкость, тишина, движение, палитра, язык, подписи, обзор мышью и стиком, выгрузка статистики, закрытие")
	AutoTest.fulfill("options checks")


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("options: " + what)
