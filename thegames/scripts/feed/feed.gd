class_name Feed
extends RefCounted
## Сборка ленты отклика, спека `docs/specs/success.md`: сдвиги постоянных критиков и
## стримеров поверх общих `C` и `V`, выбор стримера для клипа, тон текстов от знака
## показателя и от движения репутации. Чистые функции от записи, счёта, людей и текстов.


static func hashtag(title: String) -> String:
	var out := ""
	for word in title.split(" ", false):
		out += word.substr(0, 1).to_upper() + word.substr(1)
	return "#" + out


## Оценка критика: общая `C` плюс сдвиг характера, 0..10.
static func critic_score(p: PersonDef, score: ReleaseScore, record: GameRecord, t: SuccessTuning) -> float:
	var c := score.critics
	match p.nature:
		PersonDef.Nature.RETRO:
			c += t.critic_retro_bonus if record.tech <= Game.Tech.BIT8 else -t.critic_retro_penalty
		PersonDef.Nature.BUG_HATER:
			c += t.critic_bug_hater_clean if score.bugs == 0 else -t.critic_bug_hater_per_bug * score.bugs
		PersonDef.Nature.NOVELTY:
			c += t.critic_novelty_weight * (score.novelty - t.novelty_new_setting)
	return clampf(c, 0.0, 10.0)


## Сработал ли характер критика на этом релизе (для реплики).
static func critic_nature_fired(p: PersonDef, score: ReleaseScore, record: GameRecord, t: SuccessTuning) -> bool:
	match p.nature:
		PersonDef.Nature.RETRO:
			return record.tech <= Game.Tech.BIT8
		PersonDef.Nature.BUG_HATER:
			return score.bugs > 0
		PersonDef.Nature.NOVELTY:
			return score.novelty >= t.novelty_new
	return false


## Охват стримера: общий `V` плюс бонус характера, 0..100.
static func streamer_reach(p: PersonDef, score: ReleaseScore, record: GameRecord, t: SuccessTuning) -> int:
	var v := float(score.streamers)
	match p.nature:
		PersonDef.Nature.BUG_LOVER:
			if score.spectacular_bugs > 0:
				v += t.streamer_trait_bonus
		PersonDef.Nature.LOVER_3D:
			if record.tech >= Game.Tech.LOWPOLY:
				v += t.streamer_trait_bonus
		PersonDef.Nature.RETRO:
			if record.tech <= Game.Tech.BIT8:
				v += t.streamer_trait_bonus
	return int(round(clampf(v, 0.0, 100.0)))


## В клип попадает стример с наибольшим охватом.
static func pick_streamer(streamers: PeopleSet, score: ReleaseScore, record: GameRecord, t: SuccessTuning) -> PersonDef:
	var best: PersonDef
	var best_v := -1
	for p in streamers.people:
		var v := streamer_reach(p, score, record, t)
		if v > best_v:
			best_v = v
			best = p
	return best


## Самый зрелищный баг записи (или первый), для клипа и твитов.
static func clip_bug(record: GameRecord, catalog: BugCatalog) -> BugDef:
	var first: BugDef
	for id in record.bug_ids:
		var b := catalog.by_id(id)
		if b == null:
			continue
		if b.spectacular:
			return b
		if first == null:
			first = b
	return first


## Просмотры клипов из охвата с разбросом, чтобы цифры не повторялись (плейтест 2026-11-07).
static func views_for(reach: int, t: SuccessTuning, rng: RandomNumberGenerator) -> int:
	var base := float(reach * reach) * t.views_per_reach_sq
	return int(round(base * rng.randf_range(1.0 - t.views_spread, 1.0 + t.views_spread) / 100.0)) * 100


## Лента целиком: четыре твита, три критика и клип вперемешку, в конце цифры (плейтест
## 2026-11-07: порядок перемешан). `rep_delta` сдвигает тон.
static func build(record: GameRecord, score: ReleaseScore, critics: PeopleSet, streamers: PeopleSet,
		texts: FeedTexts, t: SuccessTuning, catalog: BugCatalog, rng: RandomNumberGenerator, rep_delta := 0.0,
		veteran := false, studio := "", run_key := 0, release_index := 0) -> FeedContent:
	var c := FeedContent.new()
	c.tag = hashtag(record.title)
	c.sales_first = score.sales_first
	c.viral = score.viral
	c.streamers_word = score.streamers_word(t)
	var bug := clip_bug(record, catalog)
	var vars := {
		"title": record.title, "genre": Game.genre_name(record.genre), "setting": Game.setting_name(record.setting),
		"tech": Game.tech_name(record.tech), "bug": bug.manifestation_for(record.genre, record.tech).to_lower() if bug != null else "", "tag": c.tag,
		"studio": studio if studio != "" else "студия"}
	# Без повторов за забег (#141): строка списка выбирается по номеру релиза в порядке,
	# перемешанном от ключа забега, а не случайно. Лента при этом собирается заново одинаково.
	var take := {"run": run_key, "rel": release_index, "n": {}}
	seed(rng.seed + rng.state)  # Array.shuffle использует глобальный генератор: сидим его от rng.
	var handles := texts.handles.duplicate()
	handles.shuffle()
	var handle_i := 0

	# Твиты: твит про баг словами самого бага, тон от критиков, шум от вирусности и один про
	# жанр, сеттинг или технологию (по очереди от релиза).
	var good := score.critics >= t.feed_good_critics
	var tone_pool := texts.tweets_good if good else texts.tweets_bad
	var tone_key := "tw_good" if good else "tw_bad"
	var tweets: Array[String] = []
	if bug != null and bug.tweet_for(record.genre, record.tech) != "":
		tweets.append(_setting_words(bug.tweet_at(record.genre, record.tech, release_index), record.setting))
	tweets.append(_take(tone_pool, tone_key, take, 2))
	tweets.append(_take(texts.tweets_viral if score.viral else texts.tweets_quiet, "tw_viral" if score.viral else "tw_quiet", take))
	var context := _context_tweet(texts, record, take)
	if context != "":
		tweets.append(context)
	while tweets.size() < 4:
		tweets.append(_take(tone_pool, tone_key, take, 2))
	tweets.resize(4)
	for i in tweets.size():
		tweets[i] = _fill(tweets[i] if tweets[i].find("{tag}") >= 0 else tweets[i] + " {tag}", vars)
	tweets.shuffle()
	var mixed: Array[FeedContent.Item] = []
	for i in 4:
		mixed.append(_tweet(tweets[i], handles, handle_i))
		handle_i += 1

	# Критики: тон от своей оценки, репутация сдвигает тон на ступень; реплики без повторов.
	var sum := 0.0
	for p in critics.people:
		var item := FeedContent.Item.new()
		item.kind = FeedContent.Kind.CRITIC
		item.person = p
		item.score = snappedf(critic_score(p, score, record, t), 0.1)
		sum += item.score
		var tone := 1
		if item.score >= t.feed_warm_critics:
			tone = 2
		elif item.score < t.feed_sour_critics:
			tone = 0
		if rep_delta > 0.5:
			tone = mini(tone + 1, 2)
		elif rep_delta < -0.5:
			tone = maxi(tone - 1, 0)
		item.mood = tone - 1
		var voice: Dictionary = texts.critics.get(String(p.id), {})
		var tone_name: String = ["sour", "neutral", "warm"][tone]
		var line := _take(voice.get(tone_name, []), "cr_%s_%s" % [p.id, tone_name], take)
		if line == "":
			var pool: Array[String] = [texts.critic_sour, texts.critic_neutral, texts.critic_warm][tone]
			line = _take(pool, "cr_" + tone_name, take, 3)
		item.text = _fill(line, vars)
		if critic_nature_fired(p, score, record, t):
			var remark := _take(voice.get("nature", []), "crn_%s" % p.id, take)
			if remark == "" and p.nature < texts.critic_nature_remarks.size():
				remark = texts.critic_nature_remarks[p.nature]
			if remark != "":
				item.text += " " + _fill(remark, vars)
		mixed.append(item)
	c.critics_avg = snappedf(sum / maxi(critics.people.size(), 1), 0.1) if not critics.people.is_empty() else score.critics
	# Сигнал капа (#62): один критик называет студию ветераном.
	if veteran and not texts.critic_veteran.is_empty():
		var critic_items: Array[FeedContent.Item] = []
		for it in mixed:
			if it.kind == FeedContent.Kind.CRITIC:
				critic_items.append(it)
		if not critic_items.is_empty():
			var vi := critic_items[rng.randi_range(0, critic_items.size() - 1)]
			vi.text += " " + _fill(_take(texts.critic_veteran, "veteran", take), vars)
			c.veteran = true

	# Клип стримера с самым зрелищным багом или лучшим моментом.
	var streamer := pick_streamer(streamers, score, record, t)
	if streamer != null:
		var clip := FeedContent.Item.new()
		clip.kind = FeedContent.Kind.CLIP
		clip.person = streamer
		clip.mood = 1 if c.viral else 0
		clip.reach = streamer_reach(streamer, score, record, t)
		clip.stamp = bug.stamp_for(record.genre, record.tech, record.setting) if bug != null else ""
		var stream_voice: Dictionary = texts.streamers.get(String(streamer.id), {})
		var clip_kind := "bug" if bug != null else "clean"
		var clip_line := _take(stream_voice.get(clip_kind, []), "cl_%s_%s" % [streamer.id, clip_kind], take)
		if clip_line == "":
			clip_line = _take(texts.clip_bug if bug != null else texts.clip_clean, "cl_" + clip_kind, take)
		clip.text = _fill(clip_line, vars)
		c.views = views_for(score.streamers, t, rng)
		c.online = int(round(c.views / t.online_divisor / 100.0)) * 100
		clip.caption = FeedContent.format_count(c.online) + " онлайн"
		mixed.append(clip)
		c.clip_person = streamer

	# Перемешать так, чтобы лента не начиналась с клипа и критики не шли подряд, если можно.
	for attempt in 12:
		mixed.shuffle()
		if mixed[0].kind != FeedContent.Kind.CLIP and not _adjacent_critics(mixed):
			break
	c.items.append_array(mixed)

	var numbers := FeedContent.Item.new()
	numbers.kind = FeedContent.Kind.NUMBERS
	numbers.score = c.critics_avg
	numbers.reach = c.views
	numbers.text = FeedContent.format_count(c.views)
	c.items.append(numbers)
	return c


static func _adjacent_critics(items: Array[FeedContent.Item]) -> bool:
	for i in range(1, items.size()):
		if items[i].kind == FeedContent.Kind.CRITIC and items[i - 1].kind == FeedContent.Kind.CRITIC:
			return true
	return false


static func _tweet(text: String, handles: Array[String], i: int) -> FeedContent.Item:
	var item := FeedContent.Item.new()
	item.kind = FeedContent.Kind.TWEET
	item.text = text
	item.handle = handles[i % handles.size()] if not handles.is_empty() else "@anon"
	return item


## Слова сеттинга в тексте бага (#141): «{enemies} носятся» даёт «Зомби носятся» или «Пришельцы
## носятся». Слова в именительном падеже, строчными; первая буква текста заглавная.
static func _setting_words(text: String, setting: Game.Setting) -> String:
	if not text.contains("{"):
		return text
	var def := SettingDef.of(setting)
	var out := text
	for key: StringName in SettingDef.WORD_KEYS:
		var mark := "{%s}" % key
		if out.contains(mark):
			out = out.replace(mark, def.word(key).to_lower())
	return out.substr(0, 1).to_upper() + out.substr(1)


## Твит про жанр, сеттинг или технологию: вид меняется от релиза к релизу.
static func _context_tweet(texts: FeedTexts, record: GameRecord, take: Dictionary) -> String:
	var kinds := [
		["tw_g%d" % record.genre, texts.tweets_genre, record.genre],
		["tw_s%d" % record.setting, texts.tweets_setting, record.setting],
		["tw_t%d" % record.tech, texts.tweets_tech, record.tech]]
	for shift in 3:
		var kind: Array = kinds[(int(take["rel"]) + shift) % 3]
		var pools: Array = kind[1]
		var i: int = kind[2]
		if i < pools.size() and not pools[i].is_empty():
			return _take(pools[i], kind[0], take)
	return ""


## Строка списка без повторов за забег: список перемешан от ключа забега и имени списка, релиз
## `rel` берёт из него `stride` строк подряд. Повтор возможен, только когда список исчерпан.
static func _take(pool: Variant, key: String, take: Dictionary, stride := 1) -> String:
	var size: int = pool.size() if pool != null else 0
	if size == 0:
		return ""
	var counts: Dictionary = take["n"]
	var j: int = counts.get(key, 0)
	counts[key] = j + 1
	var order := range(size)
	var mix := RandomNumberGenerator.new()
	mix.seed = hash([take["run"], key])
	for i in range(size - 1, 0, -1):
		var k := mix.randi_range(0, i)
		var tmp: int = order[i]
		order[i] = order[k]
		order[k] = tmp
	return str(pool[order[(int(take["rel"]) * stride + j) % size]])


static func _fill(template: String, vars: Dictionary) -> String:
	var out := template
	for k in vars:
		out = out.replace("{" + k + "}", str(vars[k]))
	return out
