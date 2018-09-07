import argparse
import datetime
import glob
import operator
import time

from bs4 import BeautifulSoup as BS
#from dateutil.parser import parse
from lxml import etree

try:
  import urllib2 as urllib
except:
  import urllib.request as urllib

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

	for i in range(0,700,25):
		html = oauth.getData("https://fantasysports.yahooapis.com/fantasy/v2/league/{}/players;start={};status=FA".format(oauth.league_key, i)).text
		
		with open("static/players/FA/FA_{}_{}.xml".format(i,i+25), "w") as fh:
			fh.write(html)
		time.sleep(3)

def write_cron_rosters():
	import oauth
	oauth = oauth.MyOAuth()

	for i in range(1,13):
		html = oauth.getData("https://fantasysports.yahooapis.com/fantasy/v2/team/{}.t.{}/roster".format(oauth.league_key, i)).text
		
		with open("static/players/{}/roster.xml".format(i), "w") as fh:
			fh.write(html)
		time.sleep(3)

def write_cron_standings():
	import oauth
	oauth = oauth.MyOAuth()

	xml = oauth.getData("https://fantasysports.yahooapis.com/fantasy/v2/league/{}/standings".format(oauth.league_key)).text
	with open("static/standings.xml", "w") as fh:
		fh.write(xml)

def read_FA():
	files = glob.glob("static/players/FA/*")
	players_on_FA = {}

	for fn in files:
		#f = open(fn)
		tree = etree.parse(fn)
		players_xpath = tree.xpath('.//base:player', namespaces=ns)

		for player in players_xpath:
			full = player.find('.//base:full', namespaces=ns).text
			pid = player.find('.//base:player_id', namespaces=ns).text
			pos = player.find('.//base:display_position', namespaces=ns).text
			nfl_team = player.find('.//base:editorial_team_abbr', namespaces=ns).text

			players_on_FA[full.lower().replace("'", "")] = {"team_id": 0, "position": pos, "pid": pid, "nfl_team": nfl_team}
	return players_on_FA

def read_rosters():
	players_on_teams = {}
	name_translations = {}
	for i in range(1,13):
		tree = etree.parse("static/players/{}/roster.xml".format(i))
		players_xpath = tree.xpath('.//base:player', namespaces=ns)

		for player in players_xpath:
			
			pid = player.find('.//base:player_id', namespaces=ns).text
			first = player.find('.//base:first', namespaces=ns).text
			last = player.find('.//base:last', namespaces=ns).text
			full = player.find('.//base:full', namespaces=ns).text
			pos = player.find('.//base:display_position', namespaces=ns).text
			selected_pos = player.findall('.//base:position', namespaces=ns)[-1].text
			nfl_team = player.find('.//base:editorial_team_abbr', namespaces=ns).text

			players_on_teams[full.lower().replace("'", "")] = {"team_id": i, "position": pos, "pid": pid, "nfl_team": nfl_team, "fantasy_position": position_priority[selected_pos]}
			name_translations["{}. {}".format(first[0], last)] = full.lower().replace("'", "")

	return players_on_teams, name_translations

def read_standings():
	
	tree = etree.parse("static/standings.xml")
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
		pass