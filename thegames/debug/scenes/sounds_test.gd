extends Control
## Прослушивание общего набора звуков мини-игр (#131): пять звуков `MiniSfx`, выбранных на слух
## 2026-11-14. Клик играет звук, «Лесенка» играет его восемью ступенями вверх, как он звучит в
## игре по этажам и раундам. Громкость как в мини-игре (`Minigame.SFX_TRIM_DB`).
## Запуск: F1 → Сцены → sounds test, или `Godot --path thegames -- --scene=sounds_test`.
## Под автотестом: все звуки собираются, не молчат и не упираются в потолок.

const LADDER: Array[int] = [0, 2, 4, 7, 9, 12, 14, 16]
const LADDER_STEP := 0.24
const BUTTON := Vector2(240, 96)

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
	box.offset_top = 32
	box.offset_bottom = -32
	box.add_theme_constant_override("separation", 10)
	add_child(box)
	box.add_child(_label("Звуки мини-игр: клик играет звук", Style.FONT_H2, Style.INK))
	for kind in MiniSfx.Kind.size():
		box.add_child(_label("%s · %s" % [MiniSfx.KIND_NAMES[kind], MiniSfx.KIND_USE[kind]], Style.FONT_BODY, Style.INK_2))
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 16)
		box.add_child(row)
		var b := Button.new()
		b.text = MiniSfx.KIND_NAMES[kind]
		b.custom_minimum_size = BUTTON
		b.pressed.connect(_pick.bind(kind))
		row.add_child(b)
		var ladder := Button.new()
		ladder.text = "Лесенка"
		ladder.custom_minimum_size = Vector2(160, BUTTON.y)
		ladder.pressed.connect(_ladder.bind(kind))
		row.add_child(ladder)
	if AutoTest.enabled:
		_check()


func _label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	return l


func _pick(kind: int) -> void:
	_ladder_run += 1
	_play(MiniSfx.make(kind as MiniSfx.Kind))


func _play(stream: AudioStream) -> void:
	var p := Sfx.player(stream, Minigame.SFX_TRIM_DB)
	add_child(p)
	p.finished.connect(p.queue_free)
	p.play()


## Звук восемью ступенями вверх; новый клик обрывает лесенку.
func _ladder(kind: int) -> void:
	_ladder_run += 1
	var run := _ladder_run
	for note in LADDER:
		if run != _ladder_run:
			return
		var p := MiniSfx.player(kind as MiniSfx.Kind, 0.0, Minigame.SFX_TRIM_DB, pow(2.0, note / 12.0))
		add_child(p)
		p.finished.connect(p.queue_free)
		p.play()
		await get_tree().create_timer(LADDER_STEP).timeout


func _check() -> void:
	for kind in MiniSfx.Kind.size():
		var wav := MiniSfx.make(kind as MiniSfx.Kind)
		var peak := 0
		for i in wav.data.size() / 2:
			peak = maxi(peak, absi(wav.data.decode_s16(i * 2)))
		if peak < 3000:
			AutoTest.fail("sounds: %s молчит (пик %d)" % [MiniSfx.KIND_NAMES[kind], peak])
		elif peak >= 32767:
			AutoTest.fail("sounds: %s упирается в потолок" % MiniSfx.KIND_NAMES[kind])
		AutoTest.note("sounds: %s пик %d, %.2f с" % [MiniSfx.KIND_NAMES[kind], peak, wav.get_length()])
	AutoTest.fulfill("sounds checks")
