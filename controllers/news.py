import datetime
import operator

from bs4 import BeautifulSoup as BS
#from dateutil.parser import parse

try:
	import urllib2 as urllib
except:
	import urllib.request as urllib

try:
	from controllers.read_rosters import *
	from controllers.read_twitter import *
except:
	from read_rosters import *
	from read_twitter import *


epoch = datetime.datetime.utcfromtimestamp(0)
def unix_time_seconds(dt):
	return (dt - epoch).total_seconds()

def read_news(players_on_teams, players_on_FA, team_names):
	headline_url = "http://rotoworld.com/headlines/nfl/0/Football-headlines"

	#html = urllib.urlopen(headline_url).read()
	html = ""
	soup = BS(html, "lxml")

	rows = soup.find_all("div", class_="pb")
	player_info = {}
	twitter_sources = []

	#players_on_teams, translations = read_rosters.read_rosters()
	#players_on_FA = read_rosters.read_FA()
	#team_names = read_rosters.read_standings()
	all_tweets = read_twitter(players_on_teams, players_on_FA)

	for row in rows:
		name_link = row.find("div", class_="player").find("a")
		name = name_link["href"].split("/")[-1].replace("-", " ")
		headline = name_link.text
		report = row.find("div", class_="report").find("p").text
		impact = row.find("div", class_="impact").text
		source = row.find("div", class_="source")
		#date = unix_time_seconds(parse(row.find("div", class_="date").text))
		twitter_name = ""

		if source.find("a"):
			twitter_split = source.find("a")["href"].split("/")
			if "twitter.com" in twitter_split:
				twitter_name = twitter_split[3]
				if twitter_name not in twitter_sources:
					twitter_sources.append(twitter_name)

		fantasy_team = ""
		if name in players_on_teams:
			fantasy_team = team_names[players_on_teams[name]["team_id"] - 1]["name"]
		elif name in players_on_FA:
			fantasy_team = "FA"
		else:
			continue

		if name not in player_info:
			player_info[name] = []

		player_info[name].append({"headline": headline, "report": report, "impact": impact, "date": date, "fantasy_team": fantasy_team, "tweet": False})

	for tweet in all_tweets:
		if tweet["name"] in players_on_teams:
			fantasy_team = team_names[players_on_teams[tweet["name"]]["team_id"] - 1]["name"]
		else:
			fantasy_team = "FA"

		if tweet["name"] not in player_info:
			player_info[tweet["name"]] = []

		player_info[tweet["name"]].append({"headline": tweet["headline"], "date": tweet["date"], "fantasy_team": fantasy_team, "tweet": True})

	for player in player_info:
		player_info[player] = sorted(player_info[player], key=operator.itemgetter("date"), reverse=True)
	return player_info

"""
print("sources ", twitter_sources)
for player in player_info_sorted_date:
	#datetime.datetime.fromtimestamp(player["date"] + 4*60*60)
	print("{} ({}) - {}\n".format(player["name"], player["fantasy_team"], player["headline"]))
"""










