class_name MusicBed
extends Node
## Тема игры фоном в оболочке (#87): на главном экране забега тихо и без ударных, в ленте под
## клипом стримера. Появляется и уходит плавно; молчит, пока `active` снят или хозяин скрыт.

var active := true

var _player: AudioStreamPlayer
var _db := -24.0
var _level := 0.0


func _init(record: GameRecord = null, volume_db := -24.0, drums := false) -> void:
	_db = volume_db
	if record != null:
		_player = Music.for_record(record, -80.0, drums)
		add_child(_player)


func _process(delta: float) -> void:
	if _player == null or Music.closing:
		return
	var host := get_parent() as CanvasItem
	var on := active and (host == null or host.is_visible_in_tree())
	var fade := maxf(Music.tuning().hub_fade, 0.01)
	_level = move_toward(_level, 1.0 if on else 0.0, delta / fade)
	if _level > 0.0 and not _player.playing:
		_player.play()
	_player.stream_paused = _level <= 0.0
	_player.volume_db = _db + linear_to_db(maxf(_level, 0.001))
