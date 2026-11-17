class_name FeedContent
extends RefCounted
## Собранное содержимое ленты одного релиза: элементы по порядку спеки и итоговые числа.
## Собирается `Feed.build`, рисуется `FeedScreen`.

enum Kind { TWEET, CRITIC, CLIP, NUMBERS }


class Item:
	var kind: Kind
	var person: PersonDef
	var handle := ""
	var text := ""
	var score := 0.0
	var reach := 0
	var stamp := ""
	var caption := ""
	## Настроение портрета: −1 кислый, 0 ровный, +1 тёплый (#140).
	var mood := 0


var items: Array[Item] = []
var tag := ""
var critics_avg := 0.0
var sales_first := 0
var streamers_word := ""
var viral := false
## Один из критиков назвал студию ветераном (сигнал капа, #62).
var veteran := false
var clip_person: PersonDef
## Просмотры клипов всего и онлайн на стриме клипа: из охвата с разбросом (плейтест 2026-11-07).
var views := 0
var online := 0


## Та же лента, но только элементы видов `kinds`: главный экран после релиза показывает то, что
## уже пришло (#133).
func only(kinds: Array) -> FeedContent:
	var c := FeedContent.new()
	for it in items:
		if kinds.has(it.kind):
			c.items.append(it)
	c.tag = tag
	c.critics_avg = critics_avg
	c.sales_first = sales_first
	c.streamers_word = streamers_word
	c.viral = viral
	c.veteran = veteran
	c.clip_person = clip_person
	c.views = views
	c.online = online
	return c


## «1,2 млн», «140 тыс.», «640».
static func format_count(n: int) -> String:
	if n >= 1000000:
		return ("%.1f" % (n / 1000000.0)).replace(".", ",") + " млн"
	if n >= 1000:
		return "%d тыс." % int(round(n / 1000.0))
	return str(n)
