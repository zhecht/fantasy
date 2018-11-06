
from bs4 import BeautifulSoup as BS

import json
import operator
import urllib
import re


def write_cron_playbyplay():
	j = {}

	team = "wsh"
	player = "A.Peterson"
	rbs = [
		{"team": "wsh", "player": "A.Peterson"},
		{"team": "wsh", "player": "C.Thompson"},

		{"team": "tb", "player": "P.Barber"},
		{"team": "tb", "player": "R.Jones"},

		{"team": "sf", "player": "M.Breida"},

		{"team": "sea", "player": "C.Carson"},
		{"team": "sea", "player": "M.Davis"},

		{"team": "pit", "player": "J.Conner"},

		{"team": "phi", "player": "C.Clement"},		

		{"team": "oak", "player": "J.Richard"},
		{"team": "oak", "player": "D.Martin"},

		{"team": "nyj", "player": "I.Crowell"},
		{"team": "nyj", "player": "B.Powell"},

		{"team": "nyg", "player": "S.Barkley"},

		{"team": "no", "player": "A.Kamara"},
		{"team": "no", "player": "M.Ingram"},

		{"team": "ne", "player": "J.White"},
		{"team": "ne", "player": "S.Michel"},

		{"team": "min", "player": "D.Cook"},
		{"team": "min", "player": "L.Murray"},

		{"team": "lar", "player": "T.Gurley"},

		{"team": "lac", "player": "M.Gordon"},
		{"team": "lac", "player": "A.Ekeler"},

		{"team": "kc", "player": "K.Hunt"},

		{"team": "jax", "player": "L.Fournette"},
		{"team": "jax", "player": "T.Yeldon"},

		{"team": "ind", "player": "M.Mack"},
		{"team": "ind", "player": "N.Hines"},

		{"team": "hou", "player": "L.Miller"},

		{"team": "gb", "player": "A.Jones"},
		{"team": "gb", "player": "J.Williams"},

		{"team": "det", "player": "K.Johnson"},

		{"team": "den", "player": "P.Lindsay"},
		{"team": "den", "player": "R.Freeman"},

		{"team": "dal", "player": "E.Elliot"},

		{"team": "cle", "player": "N.Chubb"},
		{"team": "cle", "player": "D.Johnson Jr."},

		{"team": "cin", "player": "J.Mixon"},

		{"team": "chi", "player": "T.Cohen"},
		{"team": "chi", "player": "J.Howard"},

		{"team": "car", "player": "C.McCaffrey"},

		{"team": "buf", "player": "L.McCoy"},
		{"team": "buf", "player": "C.Ivory"},

		{"team": "bal", "player": "A.Collins"},
		{"team": "bal", "player": "J.Allen"},

		{"team": "atl", "player": "T.Coleman"},
		{"team": "atl", "player": "I.Smith"},

		{"team": "ari", "player": "D.Johnson"},
		]

	for rb in rbs:
		team = rb["team"]
		player = rb["player"]

		print("Starting {}".format(player))
		game_ids = []
		j[player] = []

		html = urllib.urlopen("http://www.espn.com/nfl/team/schedule/_/name/{}".format(team))
		soup = BS(html.read(), "lxml")
		rows = soup.find_all("tr", class_="Table2__tr")

		for r in rows[2:]:
			tds = r.find_all("td")
			try:
				week = int(tds[0].find("span").text)
			except:
				break

			try:
				game_ids.append(tds[3].find("a").get("href").split("/")[-1])
			except:
				game_ids.append("")
			if week == 7:
				break

		for game_id in game_ids:
			if game_id == "":
				j[player].append([])
				continue

			base_url = "http://www.espn.com/nfl/playbyplay?gameId={}".format(game_id)

			total_yards = 0

			html = urllib.urlopen(base_url)
			soup = BS(html.read(), "lxml")

			rushes = []
			sections = soup.find_all("li", class_="accordion-item")
			for section in sections:
				drive_plays = section.find_all("span", class_="post-play")
				for play in drive_plays:
					regex = re.search(r"{} .* for ([-0-9]+) yard".format(player), play.text)
					if regex and play.text.find("pass") == -1 and play.text.find("No Play") == -1 and play.text.find("punts") == -1:
						rushes.append(int(regex.group(1)))

			j[player].append(rushes)


	with open("static/playbyplay.json", "w") as fh:
		json.dump(j, fh, indent=4)

def read_playbyplay():
	playbyplay = {}
	with open("static/playbyplay.json") as fh:
		playbyplay = json.loads(fh.read())
	
	stats = []

	for player in playbyplay:
		rushes = playbyplay[player]
		j = {"name": player, "negative_rushes": 0, "negative_rushing_yards": 0, "rushes_over_5": 0, "rushes_over_10": 0, "rushes_over_20": 0}
		for weekly_rushes in rushes:
			if len(weekly_rushes) > 0:
				for rush in weekly_rushes:
					if rush >= 5:
						j["rushes_over_5"] += 1
					if rush >= 10:
						j["rushes_over_10"] += 1
					if rush >= 20:
						j["rushes_over_20"] += 1
					if rush < 0:
						j["negative_rushes"] += 1
						j["negative_rushing_yards"] += rush
		stats.append(j)

	for key in ["negative_rushing_yards", "rushes_over_5", "rushes_over_10", "rushes_over_20"]:
		is_reverse = False if key == "negative_rushing_yards" else True
		sort = sorted(stats, key=operator.itemgetter(key), reverse=is_reverse)
		print("\nPlayer|{}".format( ' '.join(key.split("_")).title()) )
		print(":--|:--")
		for stat in sort[:10]:
			print("{}|{}".format(stat["name"], stat[key]))


#write_cron_playbyplay()
read_playbyplay()