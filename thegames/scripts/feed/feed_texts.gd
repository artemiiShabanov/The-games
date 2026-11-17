class_name FeedTexts
extends Resource
## Шаблоны ленты (#141), ресурс `res://resources/texts/feed.tres`: твиты по тону, жанру,
## сеттингу и технологии, рецензии и реплики со своим голосом у каждого критика и стримера,
## ники. Подстановки: {title}, {genre}, {setting}, {tech}, {bug}, {tag}, {studio}. Твит без
## {tag} получает тег в конце. Ресурс собирается из списков, руками его лучше не править.

const PATH := "res://resources/texts/feed.tres"

@export var handles: Array[String] = []
@export var tweets_good: Array[String] = []
@export var tweets_bad: Array[String] = []
@export var tweets_viral: Array[String] = []
@export var tweets_quiet: Array[String] = []
## Твиты про жанр, сеттинг и технологию: индекс = `Game.Genre`, `Game.Setting`, `Game.Tech`.
@export var tweets_genre: Array[PackedStringArray] = []
@export var tweets_setting: Array[PackedStringArray] = []
@export var tweets_tech: Array[PackedStringArray] = []
## Голос критика по `PersonDef.id`: списки `warm`, `neutral`, `sour` и `nature` (фраза, когда
## сработал характер). Без голоса берутся общие списки ниже.
@export var critics: Dictionary = {}
## Голос стримера по `PersonDef.id`: списки `bug` и `clean`.
@export var streamers: Dictionary = {}
@export var critic_warm: Array[String] = []
@export var critic_neutral: Array[String] = []
@export var critic_sour: Array[String] = []
## Индекс = `PersonDef.Nature`, фраза добавляется к реплике критика, когда характер сработал.
@export var critic_nature_remarks: Array[String] = []
## Сигнал капа (#62): с капа −3 один критик добавляет к реплике фразу про студию-ветерана.
## Подстановка {studio}: название студии.
@export var critic_veteran: Array[String] = []
@export var clip_bug: Array[String] = []
@export var clip_clean: Array[String] = []
@export var viewers_viral: Array[String] = []
@export var viewers_noticed: Array[String] = []
@export var viewers_quiet: Array[String] = []


static func load_default() -> FeedTexts:
	var t := load(PATH) as FeedTexts
	return t if t != null else FeedTexts.new()
