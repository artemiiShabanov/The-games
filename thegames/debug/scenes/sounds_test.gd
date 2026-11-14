extends Control
## Прослушивание общего набора звуков мини-игр (#131): четыре звука (`MiniSfx.Kind`), у каждого
## пять вариантов. Клик по варианту играет его и отмечает выбранным; «Лесенка» играет выбранный
## вариант восемью ступенями вверх, как он звучит в игре по этажам и раундам. Выбор пишется в
## `debug/playtest/sounds_choice.txt`. Громкость как в мини-игре (`Minigame.SFX_TRIM_DB`).
## Запуск: F1 → Сцены → sounds test, или `Godot --path thegames -- --scene=sounds_test`.
## Под автотестом: все двадцать звуков собираются, не молчат и не упираются в потолок.

const VARIANTS := 5
const LADDER: Array[int] = [0, 2, 4, 7, 9, 12, 14, 16]
const LADDER_STEP := 0.24
const CHOICE_PATH := "res://debug/playtest/sounds_choice.txt"
const BUTTON := Vector2(240, 96)

var _choice: Array[int] = [0, 0, 0, 0]
var _buttons: Array[Array] = []
var _players: Array[AudioStreamPlayer] = []
var _footer: Label
var _ladder_run := 0


func _ready() -> void:
	if AutoTest.enabled:
		AutoTest.require("sounds checks")
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var box := VBoxContainer.new()
	box.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	box.offset_left = Style.EDGE
	box.offset_right = -Style.EDGE
	box.offset_top = 48
	box.offset_bottom = -48
	box.add_theme_constant_override("separation", 14)
	add_child(box)
	box.add_child(_label("Звуки мини-игр: клик играет вариант и выбирает его", Style.FONT_H2, Style.INK))
	for kind in MiniSfx.Kind.size():
		box.add_child(_label("%s · %s" % [MiniSfx.KIND_NAMES[kind], MiniSfx.KIND_USE[kind]], Style.FONT_BODY, Style.INK_2))
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 16)
		box.add_child(row)
		var row_buttons: Array[Button] = []
		for v in VARIANTS:
			var b := Button.new()
			b.text = "%d  %s" % [v + 1, MiniSfx.VARIANT_NAMES[kind][v]]
			b.custom_minimum_size = BUTTON
			b.pressed.connect(_pick.bind(kind, v))
			row.add_child(b)
			row_buttons.append(b)
		_buttons.append(row_buttons)
		if kind == MiniSfx.Kind.TAP or kind == MiniSfx.Kind.HIT:
			var ladder := Button.new()
			ladder.text = "Лесенка"
			ladder.custom_minimum_size = Vector2(160, BUTTON.y)
			ladder.pressed.connect(_ladder.bind(kind))
			row.add_child(ladder)
	_footer = _label("", Style.FONT_BODY, Style.INK)
	box.add_child(_footer)
	_load_choice()
	_refresh()
	if AutoTest.enabled:
		_check()


func _label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	return l


func _pick(kind: int, variant: int) -> void:
	_ladder_run += 1
	_choice[kind] = variant
	_play(MiniSfx.make(kind as MiniSfx.Kind, variant))
	_refresh()
	_save_choice()


func _play(stream: AudioStream) -> void:
	var p := Sfx.player(stream, Minigame.SFX_TRIM_DB)
	add_child(p)
	p.finished.connect(p.queue_free)
	p.play()


## Выбранный вариант восемью ступенями вверх; новый клик обрывает лесенку.
func _ladder(kind: int) -> void:
	_ladder_run += 1
	var run := _ladder_run
	for note in LADDER:
		if run != _ladder_run:
			return
		_play(MiniSfx.make(kind as MiniSfx.Kind, _choice[kind], MiniSfx.KIND_FREQ[kind] * pow(2.0, note / 12.0)))
		await get_tree().create_timer(LADDER_STEP).timeout


func _refresh() -> void:
	var parts: Array[String] = []
	for kind in _buttons.size():
		for v in VARIANTS:
			var b: Button = _buttons[kind][v]
			b.modulate = Color.WHITE if v == _choice[kind] else Color(1, 1, 1, 0.55)
		parts.append("%s %d" % [MiniSfx.KIND_NAMES[kind].to_lower(), _choice[kind] + 1])
	_footer.text = "Выбрано: " + " · ".join(parts)


func _save_choice() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(CHOICE_PATH.get_base_dir()))
	var f := FileAccess.open(CHOICE_PATH, FileAccess.WRITE)
	if f != null:
		f.store_string(" ".join(_choice.map(func(v: int) -> String: return str(v + 1))) + "\n")


func _load_choice() -> void:
	if AutoTest.enabled or not FileAccess.file_exists(CHOICE_PATH):
		return
	var parts := FileAccess.get_file_as_string(CHOICE_PATH).strip_edges().split(" ", false)
	for kind in mini(parts.size(), _choice.size()):
		_choice[kind] = clampi(int(parts[kind]) - 1, 0, VARIANTS - 1)


func _check() -> void:
	for kind in MiniSfx.Kind.size():
		for v in VARIANTS:
			var wav := MiniSfx.make(kind as MiniSfx.Kind, v)
			var peak := 0
			for i in wav.data.size() / 2:
				peak = maxi(peak, absi(wav.data.decode_s16(i * 2)))
			if peak < 3000:
				AutoTest.fail("sounds: %s %d молчит (пик %d)" % [MiniSfx.KIND_NAMES[kind], v + 1, peak])
			elif peak >= 32767:
				AutoTest.fail("sounds: %s %d упирается в потолок" % [MiniSfx.KIND_NAMES[kind], v + 1])
			AutoTest.note("sounds: %s %d пик %d, %.2f с" % [MiniSfx.KIND_NAMES[kind], v + 1, peak, wav.get_length()])
	AutoTest.fulfill("sounds checks")
