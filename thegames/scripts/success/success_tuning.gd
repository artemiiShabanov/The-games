class_name SuccessTuning
extends Resource
## Коэффициенты успеха, ресурс `res://resources/success.tres`, спека `docs/specs/success.md`,
## числа из `success_model.md` и `tools/model_run.py`. Индексы массивов: `Game.Tech`,
## `Game.Genre`, `Game.Setting`; таблицы синергии развёрнуты в строку: технология × жанр по
## `tech * 5 + genre`, жанр × сеттинг по `setting * 5 + genre`.

const PATH := "res://resources/success.tres"

@export var p_base := 6000.0
@export var tech_sales: Array[float] = [0.62, 0.7, 0.85, 1.0, 1.2]
@export var tech_critics: Array[float] = [0.6, 0.3, 0.1, 0.0, -0.3]
@export var tech_spectacle: Array[float] = [0.5, 0.6, 0.68, 0.9, 1.0]
@export var setting_hype: Array[float] = [0.5, 0.7, 0.6, 0.5, 0.7, 0.6, 0.5, 0.6, 0.7, 0.5]
@export var syn_tech_genre: Array[float] = [
	1.00, 0.90, 1.10, 0.85, 0.85,
	1.20, 1.00, 1.05, 1.00, 0.95,
	1.10, 1.15, 1.10, 1.05, 1.20,
	1.00, 1.05, 1.00, 0.95, 0.90,
	1.00, 1.15, 1.20, 1.10, 1.05]
@export var syn_genre_setting: Array[float] = [
	1.03, 1.05, 1.00, 0.97, 1.00,
	1.00, 1.00, 1.05, 0.95, 0.97,
	1.00, 0.95, 0.97, 1.00, 1.05,
	1.03, 1.05, 1.00, 0.97, 1.00,
	1.03, 0.95, 1.00, 0.97, 1.05,
	1.05, 0.95, 1.00, 0.97, 1.03,
	1.05, 1.03, 0.95, 1.00, 0.97,
	1.05, 0.97, 0.97, 0.96, 1.05,
	1.03, 1.05, 1.00, 0.97, 0.95,
	0.97, 0.95, 1.00, 1.05, 1.03]
## Скрытый шум синергии на пару, разыгрывается на забег.
@export var syn_jitter := 0.05

@export_group("Критики")  # i18n: skip
@export var critics_base := 2.0
@export var critics_quality := 6.0
@export var critics_novelty := 1.5
@export var critics_synergy := 5.0
## Синергия, при которой вклад сочетания нулевой: ниже критики снимают, выше добавляют
## (полировка 2026-11-17: сочетание жанра с технологией и сеттингом весит больше).
@export var critics_synergy_center := 1.0
## Качество выше `critics_quality_knee` прибавляет критикам уже по `critics_quality_top` за
## единицу: одной чистой игрой 10 не взять, нужно удачное сочетание или везение.
@export var critics_quality_knee := 1.0
@export var critics_quality_top := 6.0
@export var critics_bug := 0.4
@export var critics_fatigue := 1.0
@export var critics_noise := 0.5


## Вклад качества в оценку критиков: до колена по `critics_quality`, выше по `critics_quality_top`.
func quality_points(q: float) -> float:
	return critics_quality * minf(q, critics_quality_knee) + critics_quality_top * maxf(q - critics_quality_knee, 0.0)


@export_group("Новизна")  # i18n: skip
@export var novelty_new := 1.0
@export var novelty_new_setting := 0.6
@export var novelty_repeat := 0.2
@export var novelty_remake := 0.3

@export_group("Продажи")  # i18n: skip
@export var sales_critics_base := 0.6
@export var sales_critics := 0.08
@export var sales_reputation := 0.05
@export var sales_saturation := 0.5
@export var sales_trend := 0.1
@export var sales_noise := 0.15
@export var mood_min := 0.85
@export var mood_max := 1.15
@export var demand_spread := 0.15

@export_group("Стримеры")  # i18n: skip
@export var streamers_base := 0.3
@export var streamers_hype := 0.4
@export var streamers_quality := 0.3
@export var streamers_spectacular_bug := 15.0
@export var streamers_noise := 0.15
@export var noticed_threshold := 35.0
@export var viral_threshold := 70.0
@export var viral_mult := 1.5

@export_group("Хвост")  # i18n: skip
@export var tail_base := 0.45
@export var tail_quality := 0.25
@export var tail_bug := 0.05
@export var tail_bug_cap := 3
@export var tail_max_ticks := 8
@export var tail_min_share := 0.02
## Хвост «живой» для концовок, пока тик не меньше этой доли от P0.
@export var tail_alive_share := 0.05

@export_group("Репутация и насыщение")  # i18n: skip
@export var reputation_viral_bonus := 1.0
@export var saturation_keep := 0.6
@export var saturation_add := 0.35
@export var saturation_add_bad := 0.15
@export var saturation_noise := 0.05
@export var saturation_recent := 0.3
@export var saturation_bored := 0.6

@export_group("Франшиза")  # i18n: skip
## Индекс = номер части − 1; дальше последнего значения 1.0.
@export var sequel_boost: Array[float] = [1.0, 1.3, 1.15]
@export var fatigue_from_part := 4
@export var remake_boost := 0.3

@export_group("Критики и стримеры с характером")  # i18n: skip
@export var critic_retro_bonus := 0.6
@export var critic_retro_penalty := 0.3
@export var critic_bug_hater_per_bug := 0.5
@export var critic_bug_hater_clean := 0.4
@export var critic_novelty_weight := 1.5
@export var streamer_trait_bonus := 10.0
## Пороги тона в ленте: твиты хвалят от этой `C`, критик тёплый от своей оценки, язвит ниже.
@export var feed_good_critics := 6.5
@export var feed_warm_critics := 7.0
@export var feed_sour_critics := 4.0
## Просмотры клипов: охват² × это, разброс ±доля; онлайн стримера это просмотры / делитель.
@export var views_per_reach_sq := 120.0
@export var views_spread := 0.25
@export var online_divisor := 40.0

@export_group("Ступени продаж")  # i18n: skip
## Удались ли продажи (`SalesGrade`): постоянные пороги первой недели в долларах. Ниже
## первого провал, дальше слабо, неплохо, хит, суперхит.
@export var sales_grades: Array[int] = [4000, 6000, 10000, 20000]

@export_group("Оценка студии")  # i18n: skip
@export var valuation_tail := 4.0
@export var valuation_reputation := 1500.0
@export var valuation_franchise := 3000.0
@export var valuation_round := 500


static func load_default() -> SuccessTuning:
	var t := load(PATH) as SuccessTuning
	return t if t != null else SuccessTuning.new()


func synergy_tech_genre(tech: Game.Tech, genre: Game.Genre) -> float:
	return syn_tech_genre[tech * Game.Genre.size() + genre]


func synergy_genre_setting(genre: Game.Genre, setting: Game.Setting) -> float:
	return syn_genre_setting[setting * Game.Genre.size() + genre]


func franchise_boost(part: int) -> float:
	return sequel_boost[part - 1] if part >= 1 and part <= sequel_boost.size() else 1.0
