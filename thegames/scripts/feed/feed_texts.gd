class_name FeedTexts
extends Resource
## Шаблоны ленты, ресурс `res://resources/texts/feed.tres`: твиты по тону, реплики критиков
## по тону и характеру, подписи клипов, ники. Подстановки: {title}, {genre}, {setting},
## {tech}, {bug}, {tag}. Черновые тексты до M5.

const PATH := "res://resources/texts/feed.tres"

@export var handles: Array[String] = []
@export var tweets_good: Array[String] = []
@export var tweets_bad: Array[String] = []
@export var tweets_viral: Array[String] = []
@export var tweets_quiet: Array[String] = []
@export var critic_warm: Array[String] = []
@export var critic_neutral: Array[String] = []
@export var critic_sour: Array[String] = []
## Индекс = `PersonDef.Nature`, фраза добавляется к реплике критика, когда характер сработал.
@export var critic_nature_remarks: Array[String] = []
@export var clip_bug: Array[String] = []
@export var clip_clean: Array[String] = []
@export var viewers_viral: Array[String] = []
@export var viewers_noticed: Array[String] = []
@export var viewers_quiet: Array[String] = []


static func load_default() -> FeedTexts:
	var t := load(PATH) as FeedTexts
	return t if t != null else FeedTexts.new()
