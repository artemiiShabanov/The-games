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


var items: Array[Item] = []
var tag := ""
var critics_avg := 0.0
var sales_first := 0
var streamers_word := ""
var viral := false
var clip_person: PersonDef
