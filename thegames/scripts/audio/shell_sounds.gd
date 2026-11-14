extends Node
## Звуки оболочки M0 (#17), автолоад `ShellSounds`. Короткие синтетические, без чиптюна, в духе
## оболочки: `intro` карточка интро всплыла, `done` спринт засчитан, `bug` штамп бага упал,
## `hit` и `miss` попадание и промах, общие для мини-игр, `switch` сдвиг сцены в карточке,
## `tick` тихий щелчок выбора элемента UI (плейтест 2026-11-07: `switch` для этого слишком
## резкий).
## Заглушка до настоящих звуков интерфейса в M6: `ShellSounds.play(&"hit")`.

const DONE_SECOND_DELAY := 0.09

var _players := {}
var _done_second: AudioStreamPlayer
var _bug_second: AudioStreamPlayer


func _ready() -> void:
	_add(&"intro", Sfx.blip(440.0, 0.14, 0.22, 14.0))
	_add(&"done", Sfx.blip(660.0, 0.14, 0.3, 14.0))
	_add(&"bug", Sfx.thud(0.26, 0.6))
	_add(&"hit", Sfx.blip(880.0, 0.07, 0.3, 30.0))
	_add(&"miss", Sfx.thud(0.12, 0.4))
	# Мягкий шух, а не стук: стук путался с промахом (плейтест 2026-11-14, #131).
	_add(&"switch", Sfx.swish())
	_add(&"tick", Sfx.blip(1320.0, 0.025, 0.06, 60.0))
	_done_second = Sfx.player(Sfx.blip(990.0, 0.22, 0.3, 9.0))
	add_child(_done_second)
	_bug_second = Sfx.player(Sfx.blip(110.0, 0.4, 0.35, 5.0))
	add_child(_bug_second)


func _add(name: StringName, stream: AudioStream) -> void:
	var p := Sfx.player(stream)
	add_child(p)
	_players[name] = p


func play(name: StringName) -> void:
	var p: AudioStreamPlayer = _players.get(name)
	if p == null:
		push_warning("ShellSounds: нет звука " + String(name))
		return
	p.play()
	if name == &"done":
		get_tree().create_timer(DONE_SECOND_DELAY).timeout.connect(_done_second.play)
	elif name == &"bug":
		_bug_second.play()
