extends Control
## Тестовая сцена демки: запускает платформер × 8-bit с сидом и набором багов из раздела
## «Демки» дебаг-меню (`Debug.demo_seed`, `Debug.demo_bugs`). После экрана итога показывает,
## куда «вернулись», A запускает снова. Под ботом: WIN добегает до флага, LOSE стоит и
## проваливает по таймеру.

const DEMO := preload("res://scenes/demos/platformer_bit8.tscn")

var demo: Demo
var record: GameRecord
var _label: Label
var _phase := 0
var _started := 0


func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	_label = Label.new()
	_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	_label.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_label.grow_vertical = Control.GROW_DIRECTION_BOTH
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.add_theme_font_size_override("font_size", Style.FONT_H2)
	_label.visible = false
	add_child(_label)
	Debug.watch("демка", func() -> String:
		return "сид %d, баги %s" % [record.seed, record.bug_ids] if record else "")
	if AutoTest.enabled and not AutoTest.parse_args(OS.get_cmdline_user_args()).has("no-checks"):
		AutoTest.require("demo checks")
	_launch()


func _launch() -> void:
	_label.visible = false
	record = GameRecord.create(Game.Genre.PLATFORMER, Game.Tech.BIT8, Debug.demo_seed, "Тест демки")
	for id in Debug.demo_bugs:
		record.add_bug(id)
	demo = DEMO.instantiate() as Demo
	demo.setup(record, &"debug")
	demo.demo_started.connect(func(_r: GameRecord, _s: StringName) -> void: _started += 1)
	demo.demo_finished.connect(_on_finished)
	add_child(demo)
	demo.start()


func _on_finished(r: GameRecord, reached: bool) -> void:
	demo.queue_free()
	demo = null
	_label.text = "Вернулись из демки: %s\n%s\n\nA снова, F1 меню" % ["добежал" if reached else "не добежал", r]
	_label.visible = true
	if AutoTest.enabled:
		_check(reached)


func _unhandled_input(event: InputEvent) -> void:
	if demo == null and GameInput.is_a(event):
		_launch()


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("demo: " + what)


func _check(reached: bool) -> void:
	match _phase:
		0:
			_expect(reached, "WIN: бот не добежал до флага на сиде %d" % record.seed)
			_expect(_started == 1, "WIN: demo_started %d раз" % _started)
			_phase = 1
			AutoTest.bot_mode = AutoTest.BotMode.LOSE
			_launch()
		1:
			_expect(not reached, "LOSE: стоя на месте добежал")
			_phase = 2
			AutoTest.bot_mode = AutoTest.BotMode.WIN
			AutoTest.fulfill("demo checks")
			AutoTest.note("demo checks done: seed %d" % record.seed)
