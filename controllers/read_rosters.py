import argparse
import datetime
import glob
import json
import os
import operator
import time

from bs4 import BeautifulSoup as BS
#from dateutil.parser import parse
from lxml import etree

try:
  import urllib2 as urllib
except:
  import urllib.request as urllib

prefix = "/home/zhecht/fantasy/"
prefix = ""

ns = {
	'base': "http://fantasysports.yahooapis.com/fantasy/v2/base.rng"
}

position_priority = {
	"QB": 0,
	"RB": 1,
	"WR": 2,
	"TE": 3,
	"W/R/T": 4,
	"K": 5,
	"DEF": 6,
	"BN": 7
}

def write_cron_FA():
	#4murcjs
	import oauth
	oauth = oauth.MyOAuth()

	for i in range(0,1000,25):
		html = oauth.getData("https://fantasysports.yahooapis.com/fantasy/v2/league/{}/players;start={};status=FA".format(oauth.league_key, i)).text
		with open("static/players/FA/FA_{}_{}.xml".format(i,i+25), "w") as fh:
			fh.write(html)
		time.sleep(3)

def write_cron_FA_json():	
	for i in range(0,1000,25):
		j = {}
		tree = etree.parse("{}static/players/FA/FA_{}_{}.xml".format(prefix, i, i+25).format(i,i+25))
		players_xpath = tree.xpath('.//base:player', namespaces=ns)
		for player in players_xpath:
			
			pid = player.find('.//base:player_id', namespaces=ns).text
			first = player.find('.//base:first', namespaces=ns).text
			last = player.find('.//base:last', namespaces=ns).text
			full = player.find('.//base:full', namespaces=ns).text
			pos = player.find('.//base:display_position', namespaces=ns).text
			selected_pos = player.findall('.//base:position', namespaces=ns)[-1].text
			nfl_team = player.find('.//base:editorial_team_abbr', namespaces=ns).text

			if pos == "WR,RB":
				pos = "WR"

			j[full.lower().replace("'", "")] = [nfl_team, pos, pid]
		with open("{}static/players/FA/FA_{}_{}.json".format(prefix, i, i+25), "w") as fh:
			json.dump(j, fh, indent=4)
		os.remove("{}static/players/FA/FA_{}_{}.xml".format(prefix, i, i+25))

def write_cron_rosters():
	import oauth
	oauth = oauth.MyOAuth()

	for i in range(1,13):
		html = oauth.getData("https://fantasysports.yahooapis.com/fantasy/v2/team/{}.t.{}/roster".format(oauth.league_key, i)).text
		with open("{}static/players/{}/roster.xml".format(prefix, i), "w") as fh:
			fh.write(html)

def write_cron_standings():
	import oauth
	oauth = oauth.MyOAuth()

	xml = oauth.getData("https://fantasysports.yahooapis.com/fantasy/v2/league/{}/standings".format(oauth.league_key)).text
	with open("{}static/standings.xml".format(prefix), "w") as fh:
		fh.write(xml)

def read_FA():
	files = glob.glob("{}static/players/FA/*".format(prefix))
	players_on_FA = {}

	for fn in files:
		fa_json = {}
		with open(fn) as fh:
			fa_json = json.loads(fh.read())
		for player in fa_json:
			
			team, position, pid = fa_json[player]
			if position == "WR,RB":
				position = "WR"
			if player in players_on_FA:
				continue

			players_on_FA[player] = {"team_id": 0, "position": position, "pid": 0, "nfl_team": team}

	return players_on_FA

def read_FA_translations():
	files = glob.glob("{}static/players/FA/*".format(prefix))
	players_on_FA = {}
	translations = {}

	for fn in files:
		fa_json = {}
		with open(fn) as fh:
			fa_json = json.loads(fh.read())
		for player in fa_json:
			
			team, position, pid = fa_json[player]
			if position == "WR,RB":
				position = "WR"
			players_on_FA[player] = {"team_id": 0, "position": position, "pid": 0, "nfl_team": team}
			if position == "DEF":
				translations[full] = full
			else:
				translations["{}. {}".format(first[0], last, nfl_team)] = full.lower().replace("'", "")
	return players_on_FA, translations

def read_rosters():
	players_on_teams = {}
	name_translations = {}
	for i in range(1,13):
		tree = etree.parse("{}static/players/{}/roster.xml".format(prefix, i))
		players_xpath = tree.xpath('.//base:player', namespaces=ns)

		for player in players_xpath:
			
			pid = player.find('.//base:player_id', namespaces=ns).text
			first = player.find('.//base:first', namespaces=ns).text
			last = player.find('.//base:last', namespaces=ns).text
			full = player.find('.//base:full', namespaces=ns).text
			pos = player.find('.//base:display_position', namespaces=ns).text
			selected_pos = player.findall('.//base:position', namespaces=ns)[-1].text
			nfl_team = player.find('.//base:editorial_team_abbr', namespaces=ns).text

			if pos == "WR,RB":
				pos = "WR"

			players_on_teams[full.lower().replace("'", "")] = {"team_id": i, "position": pos, "pid": pid, "nfl_team": nfl_team, "fantasy_position": position_priority[selected_pos]}
			if pos == "DEF":				
				name_translations[full] = full
			else:
				name_translations["{}. {} {}".format(first[0], last, nfl_team)] = full.lower().replace("'", "")
				name_translations["{}. {} {}".format(first[0], last, nfl_team.upper())] = full.lower().replace("'", "")

	players_on_teams["duke johnson jr."] = players_on_teams["duke johnson"]
	#players_on_teams["mark ingram"] = players_on_teams["mark ingram ii"]
	return players_on_teams, name_translations

def read_standings():
	
	tree = etree.parse("{}static/standings.xml".format(prefix))
	teams_xpath = tree.xpath('.//base:team', namespaces=ns)

	all_teams = []
	for team in teams_xpath:
		team_id = int(team.find('.//base:team_id', namespaces=ns).text)
		name = team.find('.//base:name', namespaces=ns).text
		all_teams.append({'id': team_id, 'name': name})

	all_teams = sorted(all_teams,key=operator.itemgetter('id'))
	return all_teams

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")

	args = parser.parse_args()

	if args.cron:
		print("WRITING ROSTERS")
		write_cron_standings()
		write_cron_rosters()
		write_cron_FA()
	else:
		write_cron_FA_json()
		pass