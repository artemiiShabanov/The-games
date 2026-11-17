class_name Music
extends RefCounted
## Музыка игр студии (#87): тема = мелодия сеттинга × аранжировка технологии, жанр даёт темп
## и рисунок ударных. Дорожки пишет `tools/music.py --write` в `res://assets/music/`: 50 тем
## `theme_<сеттинг>_<технология>.ogg` и 25 ударных `drums_<жанр>_<технология>.ogg`, все одной
## длины. Игра складывает пару синхронно, темп жанра это скорость проигрывания.

const DIR := "res://assets/music/"
const GENRE_IDS: Array[String] = ["platformer", "racing", "shooter", "sport", "fighting"]
const TECH_IDS: Array[String] = ["vector", "bit8", "bit16", "lowpoly", "threed"]

## Игра выходит: фоновая тема больше не запускается (автотест останавливает плееры).
static var closing := false


static func tuning() -> MusicTuning:
	return load(MusicTuning.PATH)


static func theme_path(setting: Game.Setting, tech: Game.Tech) -> String:
	return "%stheme_%s_%s.ogg" % [DIR, SettingDef.of(setting).id, TECH_IDS[tech]]


static func drums_path(genre: Game.Genre, tech: Game.Tech) -> String:
	return "%sdrums_%s_%s.ogg" % [DIR, GENRE_IDS[genre], TECH_IDS[tech]]


## Тема игры: мелодия и ударные одной петлёй. `drums = false` для тихих мест оболочки.
static func stream(setting: Game.Setting, tech: Game.Tech, genre: Game.Genre, drums := true) -> AudioStream:
	var parts: Array[AudioStream] = [_loop(theme_path(setting, tech))]
	if drums:
		parts.append(_loop(drums_path(genre, tech)))
	var sync := AudioStreamSynchronized.new()
	sync.stream_count = parts.size()
	for i in parts.size():
		sync.set_sync_stream(i, parts[i])
	return sync


## Скорость проигрывания жанра.
static func rate(genre: Game.Genre) -> float:
	var rates := tuning().genre_rate
	return rates[genre] if genre < rates.size() else 1.0


## Плеер темы на шине музыки; играть и добавлять в дерево хозяину.
static func player(setting: Game.Setting, tech: Game.Tech, genre: Game.Genre, volume_db := 0.0, drums := true) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.stream = stream(setting, tech, genre, drums)
	p.pitch_scale = rate(genre)
	p.volume_db = volume_db
	p.bus = Options.MUSIC_BUS
	return p


static func for_record(record: GameRecord, volume_db := 0.0, drums := true) -> AudioStreamPlayer:
	return player(record.setting, record.tech, record.genre, volume_db, drums)


static func _loop(path: String) -> AudioStream:
	var s: AudioStreamOggVorbis = load(path)
	s.loop = true
	return s
