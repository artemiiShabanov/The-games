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


## Лента целиком: два твита, три критика, клип, два твита, цифры. `rep_delta` сдвигает тон.
static func build(record: GameRecord, score: ReleaseScore, critics: PeopleSet, streamers: PeopleSet,
		texts: FeedTexts, t: SuccessTuning, catalog: BugCatalog, rng: RandomNumberGenerator, rep_delta := 0.0) -> FeedContent:
	var c := FeedContent.new()
	c.tag = hashtag(record.title)
	c.sales_first = score.sales_first
	c.viral = score.viral
	c.streamers_word = score.streamers_word(t)
	var bug := clip_bug(record, catalog)
	var vars := {
		"title": record.title, "genre": Game.genre_name(record.genre), "setting": Game.setting_name(record.setting),
		"tech": Game.tech_name(record.tech), "bug": bug.manifestation.to_lower() if bug != null else "", "tag": c.tag}
	var handles := texts.handles.duplicate()
	handles.shuffle()
	var handle_i := 0

	# Твиты: тон от критиков и вирусности, один твит про баг словами самого бага.
	var tweet_pool: Array[String] = []
	tweet_pool.append_array(texts.tweets_good if score.critics >= t.feed_good_critics else texts.tweets_bad)
	tweet_pool.append_array(texts.tweets_viral if score.viral else texts.tweets_quiet)
	tweet_pool.shuffle()
	var tweets: Array[String] = []
	if bug != null and bug.tweet != "":
		tweets.append(bug.tweet + " " + c.tag)
	for s in tweet_pool:
		if tweets.size() >= 4:
			break
		tweets.append(_fill(s, vars))
	while tweets.size() < 4:
		tweets.append(_fill(texts.tweets_quiet[0] if not texts.tweets_quiet.is_empty() else "{tag}", vars))
	for i in 2:
		c.items.append(_tweet(tweets[i], handles, handle_i))
		handle_i += 1

	# Критики: тон от своей оценки, репутация сдвигает тон на ступень; реплики без повторов.
	var sum := 0.0
	var used: Array[String] = []
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
		var pool: Array[String] = [texts.critic_sour, texts.critic_neutral, texts.critic_warm][tone]
		var line := _pick(pool, rng)
		for attempt in 4:
			if not used.has(line):
				break
			line = _pick(pool, rng)
		used.append(line)
		item.text = _fill(line, vars)
		if critic_nature_fired(p, score, record, t) and p.nature < texts.critic_nature_remarks.size():
			item.text += " " + _fill(texts.critic_nature_remarks[p.nature], vars)
		c.items.append(item)
	c.critics_avg = snappedf(sum / maxi(critics.people.size(), 1), 0.1) if not critics.people.is_empty() else score.critics

	# Клип стримера с самым зрелищным багом или лучшим моментом.
	var streamer := pick_streamer(streamers, score, record, t)
	if streamer != null:
		var clip := FeedContent.Item.new()
		clip.kind = FeedContent.Kind.CLIP
		clip.person = streamer
		clip.reach = streamer_reach(streamer, score, record, t)
		clip.stamp = bug.stamp if bug != null else ""
		clip.text = _fill(_pick(texts.clip_bug if bug != null else texts.clip_clean, rng), vars)
		var viewers: Array[String] = texts.viewers_viral if score.viral else (texts.viewers_noticed if clip.reach >= t.noticed_threshold else texts.viewers_quiet)
		clip.caption = "клип · " + _pick(viewers, rng)
		c.items.append(clip)
		c.clip_person = streamer

	for i in range(2, 4):
		c.items.append(_tweet(tweets[i], handles, handle_i))
		handle_i += 1

	var numbers := FeedContent.Item.new()
	numbers.kind = FeedContent.Kind.NUMBERS
	numbers.score = c.critics_avg
	numbers.reach = score.sales_first
	numbers.text = c.streamers_word
	c.items.append(numbers)
	return c


static func _tweet(text: String, handles: Array[String], i: int) -> FeedContent.Item:
	var item := FeedContent.Item.new()
	item.kind = FeedContent.Kind.TWEET
	item.text = text
	item.handle = handles[i % handles.size()] if not handles.is_empty() else "@anon"
	return item


static func _pick(pool: Array[String], rng: RandomNumberGenerator) -> String:
	if pool.is_empty():
		return ""
	return pool[rng.randi_range(0, pool.size() - 1)]


static func _fill(template: String, vars: Dictionary) -> String:
	var out := template
	for k in vars:
		out = out.replace("{" + k + "}", str(vars[k]))
	return out
