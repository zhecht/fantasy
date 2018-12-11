from string import ascii_lowercase
from bs4 import BeautifulSoup as BS
import operator
import json

try:
	from controllers.read_rosters import *
except:
	from read_rosters import *

try:
	import urllib2 as urllib
except:
	import urllib.request as urllib


def fix_name(name):
	if name == "dj moore wr":
		return "dj moore"
	elif name.split(" ")[0] == "ty":
		return "t.y. "+" ".join(name.split(" ")[1:])
	elif name.split(" ")[0] == "aj":
		return "a.j. "+" ".join(name.split(" ")[1:])
	elif name.split(" ")[0] == "dj":
		return "d.j. "+" ".join(name.split(" ")[1:])
	elif name.split(" ")[0] == "oj":
		return "o.j. "+" ".join(name.split(" ")[1:])
	elif name.split(" ")[0] == "tj":
		return "t.j. "+" ".join(name.split(" ")[1:])
	elif name.split(" ")[0] == "pj":
		return "p.j. "+" ".join(name.split(" ")[1:])
	elif name.split(" ")[0] == "jj":
		return "j.j. "+" ".join(name.split(" ")[1:])
	elif name == "djuan hines":
		return "d'juan hines"
	elif name == "montravious adams":
		return "montravius adams"
	elif name == "sammie coates":
		return "sammie coates jr."
	elif name == "brandon king s":
		return "brandon king"
	elif name == "justin march":
		return "justin march lillard"
	elif name == "odell beckham":
		return "odell beckham jr."
	elif name == "kevin toliver ii":
		return "kevin toliver"
	elif name == "tredavious white":
		return "tre'davious white"
	elif name == "kyle williams dt":
		return "kyle williams"
	elif name == "chris jones dl":
		return "chris jones"
	elif name == "michael johnson db":
		return "michael johnson"
	elif name == "devondre campbell":
		return "de'vondre campbell"
	elif name == "bw webb":
		return "b.w. webb"
	elif name == "jc jackson":
		return "j.c. jackson"
	elif name == "malcom brown dt":
		return "malcom brown"
	elif name == "cj beathard":
		return "c.j. beathard"
	elif name == "john franklin meyers":
		return "john franklin myers"
	elif name == "joe thomas lb":
		return "joe thomas"
	elif name == "justin jackson rb":
		return "justin jackson"
	elif name == "michael badgley":
		return "mike badgley"
	elif name == "chris herndon iv":
		return "chris herndon"
	elif name == "duke johnson":
		return "duke johnson jr."
	elif name == "trevon johnson":
		return "tre'von johnson"
	elif name == "ej gaines":
		return "e.j. gaines"
	elif name == "jmon moore":
		return "j'mon moore"
	elif name == "devante harris":
		return "davontae harris"
	elif name == "james oshaughnessy":
		return "james o'shaughnessy"
	elif name == "foyesade oluokun":
		return "foye oluokun"
	elif name == "antone exum":
		return "antone exum jr."
	elif name == "christopher ivory":
		return "chris ivory"
	elif name == "josh allen qb":
		return "josh allen"
	elif name == "jamie collins":
		return "jamie collins sr."
	elif name == "michael thomas wr":
		return "michael thomas"
	elif name == "adrian peterson min":
		return "adrian peterson"
	elif name == "marvin jones":
		return "marvin jones jr."
	elif name == "will fuller":
		return "will fuller v"
	elif name == "equanimeous st brown":
		return "equanimeous st. brown"
	elif name == "bryan cox":
		return "bryan cox jr."
	elif name == "dante fowler":
		return "dante fowler jr."
	elif name == "kaimi fairbairn":
		return "ka'imi fairbairn"
	elif name == "mitch trubisky":
		return "mitchell trubisky"
	elif name == "todd gurley":
		return "todd gurley ii"
	elif name == "mark ingram":
		return "mark ingram ii"
	elif name == "jessie bates iii":
		return "jessie bates"
	elif name == "steven hauschka":
		return "stephen hauschka"
	elif name == "josh hill te":
		return "josh hill"
	elif name == "mike davis rb":
		return "mike davis"
	elif name == "david johnson rb":
		return "david johnson"
	return name


def write_college():
	base_url = "http://www.espn.com/nfl/college"
	j = {}
	for letter in ascii_lowercase:
		url = base_url + "/_/letter/{}".format(letter)
		html = urllib.urlopen(url)
		soup = BS(html.read(), "lxml")

		trs = soup.find("table", class_="tablehead").find_all("tr")

		college = ""
		for row in trs:
			if row.find("td").text == "PLAYER" or row.find("td").text == "No active players.":
				continue
			if "stathead" in row.get("class"):
				college = row.find("td").text.lower()
				if college.find("nfl players by college") == -1:
					j[college] = []
				continue

			if college.find("nfl players by college") == -1:
				player = " ".join(row.find("a").get("href").split("/")[-1].split("-"))
				j[college].append(player)

	with open("static/colleges.txt", "w") as outfile:
		json.dump(j, outfile, indent=4)

def read_college():
	with open("static/colleges.txt") as fh:
		returned_json = json.loads(fh.read())
	return returned_json


def write_leaders(curr_week=13):
	leaders = {}
	idp_ranks = {"LB": 1, "DT": 1, "DE": 1, "S": 1, "CB": 1}
	for pos in ["qb", "rb", "wr", "te", "k", "idp"]:
		url = "https://www.fantasypros.com/nfl/reports/leaders/{}.php?year=2018&start=1&end={}".format(pos, curr_week)
		html = urllib.urlopen(url)
		soup = BS(html.read(), "lxml")
		trs = soup.find("table", id="data").find("tbody").find_all("tr")

		for row in trs:
			tds = row.find_all("td")
			rank = int(tds[0].text)
			points = float(tds[-3].text)
			name = fix_name(" ".join(tds[1].find("a").get("href").split("/")[-1].split("-"))[:-4])
			team = tds[2].find("a").text

			new_pos = pos
			if pos == "idp":
				new_pos = tds[3].text
				if not new_pos:
					continue
				rank = idp_ranks[new_pos]
				idp_ranks[new_pos] += 1

			leaders[name] = {"rank": rank, "points": points, "team": team, "pos": new_pos}
	
	with open("static/leaders.txt", "w") as outfile:
		json.dump(leaders, outfile, indent=4)

def read_leaders():
	with open("static/leaders.txt") as fh:
		returned_json = json.loads(fh.read())
	return returned_json


if __name__ == '__main__':

	#write_leaders(15) # 12/17/18

	leaders = read_leaders()
	colleges = read_college()

	stats = []
	looked_at = []
	nfl_teams = {}

	for college in colleges:
		players = colleges[college]
		j = {"total_points": 0, "total_top": 0, "top": {}, "college": college}

		for player in players:
			looked_at.append(player)
			try:
				leader_stats = leaders[player]
				
				#if leader_stats["team"] not in nfl_teams:
				#	nfl_teams[leader_stats["team"]] = 0
				#nfl_teams[leader_stats["team"]] += 1
				
				j["total_points"] = round(j["total_points"] + float(leader_stats["points"]), 2)
				if (leader_stats["pos"] in ["rb", "qb", "te", "k"] and leader_stats["rank"] <= 24) or leader_stats["rank"] <= 36:
					j["total_top"] += 1

					if leader_stats["pos"] not in j["top"]:
						j["top"][leader_stats["pos"]] = [{"name": player, "rank": leader_stats["rank"]}]
					else:
						j["top"][leader_stats["pos"]].append({"name": player, "rank": leader_stats["rank"]})
			except:
				pass

		stats.append(j)

	#sorted_stats = sorted(stats, key=operator.itemgetter("total_points"), reverse=True)
	#for stat in sorted_stats[:10]:
	#	print(stat)

	sorted_stats = sorted(stats, key=operator.itemgetter("total_top"), reverse=True)
	print("College|Total Top|Players")
	print(":--|:--|:--")
	for stat in sorted_stats[:30]:
		#print([stat["top"][pos] for pos in stat["top"]])
		players = ["{} ({}{})".format(player["name"].title(), pos.upper(), player["rank"]) for pos in stat["top"] for player in stat["top"][pos]]
		print("{}|{}|{}".format(stat['college'].title(), stat['total_top'], ", ".join(players)))
		





