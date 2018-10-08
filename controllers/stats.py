import sys
import argparse
from ghost import Ghost
from bs4 import BeautifulSoup
import read_rosters
import json
import glob
import constants
import operator
import os
try:
  import urllib2 as urllib
except:
  import urllib.request as urllib

def merge_two_dicts(x, y):
	z = x.copy()
	z.update(y)
	return z

def write_cron_yahoo_FA():
	ghost = Ghost()
	logged_in = False
	with ghost.start() as session:
		session.wait_timeout = 100

		for count in range(0,100,25):
			fa_json = {}
			page, extra_resources = session.open("https://football.fantasysports.yahoo.com/f1/1000110/players?sort=PTS&count={}".format(count))

			if page.http_status == 200:
				if not logged_in:
					#SIGN IN
					result, extra = session.evaluate("document.getElementById('login-username').value = '{}';".format(constants.YAHOO_USERNAME))
					page, extra = session.evaluate("document.getElementById('login-signin').click();", expect_loading=True)	
					session.wait_for_selector('#login-passwd')
					result, extra = session.evaluate("document.getElementById('login-passwd').value = '{}';".format(constants.YAHOO_PWD))
					page, extra = session.evaluate("document.getElementById('login-signin').click();", expect_loading=True)
					logged_in = True

			with open('out.html', 'w') as f:
				f.write(page.content)
			f = open('out.html')
			soup = BeautifulSoup(f.read(), "lxml")
			f.close()

			table = soup.find("table", class_="Table")
			rows = table.find_all("tr")

			for player_row in rows[2:]:
				name_div = player_row.find('div',class_='ysf-player-name')
				full_name = name_div.find('a').text.lower().replace("'", "")
				span = name_div.find('span').text
				team = span.split(" - ")[0]
				position = span.split(" - ")[1]
				fa_json[full_name] = [team, position]

			with open("static/players/FA/FA_{}_{}.json".format(count, count + 25), "w") as outfile:
					json.dump(fa_json, outfile, indent=4)
		return

def write_cron_yahoo_FA_actual(start_week, end_week):
	ghost = Ghost()
	logged_in = False
	week = start_week
	with ghost.start() as session:
		session.wait_timeout = 100

		for count in range(0,100,25):
			actuals_json = {}
			page, extra_resources = session.open("https://football.fantasysports.yahoo.com/f1/1000110/players?sort=PTS&stat1=S_W_{}&count={}".format(week, count))
		
			if page.http_status == 200:
				if not logged_in:
					#SIGN IN
					result, extra = session.evaluate("document.getElementById('login-username').value = '{}';".format(constants.YAHOO_USERNAME))
					page, extra = session.evaluate("document.getElementById('login-signin').click();", expect_loading=True)	
					session.wait_for_selector('#login-passwd')
					result, extra = session.evaluate("document.getElementById('login-passwd').value = '{}';".format(constants.YAHOO_PWD))
					page, extra = session.evaluate("document.getElementById('login-signin').click();", expect_loading=True)
					logged_in = True

			with open('out.html', 'w') as f:
				f.write(page.content)
			f = open('out.html')
			soup = BeautifulSoup(f.read(), "lxml")
			f.close()

			table = soup.find("table", class_="Table")
			rows = table.find_all("tr")

			for player_row in rows[2:]:
				name_div = player_row.find('div',class_='ysf-player-name')
				full_name = name_div.find('a').text.lower().replace("'", "")				
				#actual = player_row.find_all("td")[7].find("div").text
				actual = player_row.find_all("td", class_="Ta-end")[0].find("div").text

				if actual == "-" or actual == u'\u2013':
					actual = 0
				else:
					actual = float(actual)

				actuals_json[full_name] = actual

			if os.path.isdir("static/projections/{}".format(week)) is False:
				os.mkdir("static/projections/{}".format(week))

			if os.path.isdir("static/projections/{}/FA".format(week)) is False:
				os.mkdir("static/projections/{}/FA".format(week))

			with open("static/projections/{}/FA/actual_{}_{}.json".format(week, count, count + 25), "w") as outfile:
					json.dump(actuals_json, outfile, indent=4)
		return

def write_cron_yahoo_FA_proj(start_week, end_week):
	ghost = Ghost()
	logged_in = False
	week = start_week
	with ghost.start() as session:
		session.wait_timeout = 100

		for count in range(0,100,25):
			projections_json = {}
			page, extra_resources = session.open("https://football.fantasysports.yahoo.com/f1/1000110/players?sort=PTS&stat1=S_PW_{}&count={}".format(week, count))
		
			if page.http_status == 200:
				if not logged_in:
					#SIGN IN
					result, extra = session.evaluate("document.getElementById('login-username').value = '{}';".format(constants.YAHOO_USERNAME))
					page, extra = session.evaluate("document.getElementById('login-signin').click();", expect_loading=True)	
					session.wait_for_selector('#login-passwd')
					result, extra = session.evaluate("document.getElementById('login-passwd').value = '{}';".format(constants.YAHOO_PWD))
					page, extra = session.evaluate("document.getElementById('login-signin').click();", expect_loading=True)
					logged_in = True

			with open('out.html', 'w') as f:
				f.write(page.content)
			f = open('out.html')
			soup = BeautifulSoup(f.read(), "lxml")
			f.close()

			table = soup.find("table", class_="Table")
			rows = table.find_all("tr")

			for player_row in rows[2:]:
				name_div = player_row.find('div',class_='ysf-player-name')
				full_name = name_div.find('a').text.lower().replace("'", "")
				#proj = player_row.find_all("td")[7].find("div").text
				proj = player_row.find_all("td", class_="Ta-end")[0].find("div").text

				if proj == "-" or proj == u'\u2013':
					proj = 0
				else:
					proj = float(proj)
				projections_json[full_name] = proj
			
			if os.path.isdir("static/projections/{}".format(week)) is False:
				os.mkdir("static/projections/{}".format(week))

			if os.path.isdir("static/projections/{}/FA".format(week)) is False:
				os.mkdir("static/projections/{}/FA".format(week))

			with open("static/projections/{}/FA/proj_{}_{}.json".format(week, count, count + 25), "w") as outfile:
					json.dump(projections_json, outfile, indent=4)
		return

def write_cron_yahoo_stats(start_week, end_week):
	ghost = Ghost()
	logged_in = False
	players_on_teams, name_translations = read_rosters.read_rosters()
	projections_json = {}
	actuals_json = {}
	with ghost.start() as session:
		session.wait_timeout = 100
		for week in range(start_week,start_week + 1):
			for team in range(1,12,2):
				team1 = team
				team2 = team + 1
				page, extra_resources = session.open("https://football.fantasysports.yahoo.com/f1/1000110/matchup?week={}&mid1={}&mid2={}".format(week, team1, team2))
			
				if page.http_status == 200:
					if not logged_in:
						#SIGN IN
						result, extra = session.evaluate("document.getElementById('login-username').value = '{}';".format(constants.YAHOO_USERNAME))
						page, extra = session.evaluate("document.getElementById('login-signin').click();", expect_loading=True)	
						session.wait_for_selector('#login-passwd')
						result, extra = session.evaluate("document.getElementById('login-passwd').value = '{}';".format(constants.YAHOO_PWD))
						page, extra = session.evaluate("document.getElementById('login-signin').click();", expect_loading=True)
						logged_in = True
				
				with open('out.html', 'w') as f:
					f.write(page.content)
				f = open('out.html')
				soup = BeautifulSoup(f.read(), "lxml")
				f.close()
				
				challenge = soup.find("input", attrs={"name": "challengeIndexes"})
				if challenge:
					page, extra = session.evaluate("document.getElementsByName('index')[0].click();", expect_loading=True)
					with open('out.html', 'w') as f:
						f.write(page.content)
					exit()

				stattable = soup.find("table", id="statTable1").find("tbody")
				stattable_trs = stattable.find_all('tr')
				stattable2 = soup.find("table", id="statTable2").find("tbody")
				stattable2_trs = stattable2.find_all('tr')
				all_rows = stattable_trs[:-1]+stattable2_trs[:-1]
				for row in all_rows:
					all_tds = row.find_all('td')
					try:
						p1_id = all_tds[1].find('a',class_='playernote')['data-ys-playerid']
						name_div = all_tds[1].find('div',class_='ysf-player-name')
						p1_team = name_div.find('span').text.split(" - ")[0]
						p1_name = name_div.find('a').text
						p1_full_name = name_translations[p1_name+" "+p1_team]
						
						p1_proj = all_tds[2].find('div').text
						p1_act = all_tds[3].find('a')
						p1_act = "-" if p1_act is None else all_tds[3].find('a').text
					except:
						p1_id = None

					try:
						p2_id = all_tds[9].find('a',class_='playernote')['data-ys-playerid']
						name_div = all_tds[9].find('div',class_='ysf-player-name')
						p2_team = name_div.find('span').text.split(" - ")[0]
						p2_name = name_div.find('a').text
						p2_full_name = name_translations[p2_name+" "+p2_team]
						
						p2_proj = all_tds[8].find('div').text
						p2_act = all_tds[7].find('a')
						p2_act = "-" if p2_act is None else all_tds[7].find('a').text
					except:
						p2_id = None

					if p1_proj == u'\u2013':
						p1_proj = 0
					if p2_proj == u'\u2013':
						p2_proj = 0

					#print(p2_full_name, p2_act, p2_proj)
					if p1_full_name not in projections_json:
						projections_json[p1_full_name] = float(p1_proj)
						actuals_json[p1_full_name] = p1_act
					
					if p2_full_name not in projections_json:
						projections_json[p2_full_name] = float(p2_proj)
						actuals_json[p2_full_name] = p2_act
					
					#print(p1_name,p1_proj,p1_act)
					#print(p2_name,p2_proj,p2_act)
		if os.path.isdir("static/projections/{}".format(week)) is False:
			os.mkdir("static/projections/{}".format(week))
			
		with open("static/projections/{}/yahoo.json".format(week), "w") as outfile:
			json.dump(projections_json, outfile, indent=4)

		with open("static/projections/{}/actual.json".format(week), "w") as outfile:
			json.dump(actuals_json, outfile, indent=4)

		return

def read_yahoo_stats(curr_week, end_week):
	yahoo_json = {}
	for week in range(curr_week, end_week):
		with open("static/projections/{}/yahoo.json".format(week)) as fh:
			returned_json = json.loads(fh.read())
			yahoo_json = merge_two_dicts(returned_json, yahoo_json)
		FA_proj_files = glob.glob("static/projections/{}/FA/proj*".format(week))
		for filename in FA_proj_files:
			with open(filename) as fh:
				returned_json = json.loads(fh.read())
				yahoo_json = merge_two_dicts(returned_json, yahoo_json)
	return yahoo_json

def read_yahoo_rankings(curr_week, players_on_teams):
	yahoo_json = read_yahoo_stats(curr_week, curr_week + 1)
	yahoo_list = {"qb": [], "rb": [], "wr": [], "te": []}
	for player in yahoo_json:
		if player in players_on_teams:
			position = players_on_teams[player]["position"].lower()

			if position in ["qb", "rb", "wr", "te"]:
				yahoo_list[position].append({"name": player, "proj": yahoo_json[player]})

	yahoo_json = {}
	for position in ["qb", "rb", "wr", "te"]:
		yahoo_list[position] = sorted(yahoo_list[position], key=operator.itemgetter("proj"), reverse=True)
		yahoo_json[position] = {}
		for idx, player_json in enumerate(yahoo_list[position]):
			yahoo_json[position][player_json["name"]] = idx + 1
	return yahoo_json

def read_actual_stats(curr_week, end_week):
	actual_json = {}
	with open("static/projections/{}/actual.json".format(curr_week)) as fh:
		returned_json = json.loads(fh.read())
		actual_json = merge_two_dicts(returned_json, actual_json)

	FA_actual_files = glob.glob("static/projections/{}/FA/actual*".format(curr_week))
	for filename in FA_actual_files:
		with open(filename) as fh:
			returned_json = json.loads(fh.read())
			actual_json = merge_two_dicts(returned_json, actual_json)
	return actual_json

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", help="Do Cron job", action="store_true")
	parser.add_argument("-s", "--start", help="Start Week", type=int)
	parser.add_argument("-e", "--end", help="End Week", type=int)

	args = parser.parse_args()

	curr_week = 1
	end_week = 2

	if args.start:
		curr_week = args.start
		end_week = curr_week + 1
		if args.end:
			end_week = args.end

	if args.cron:
		print("WRITING YAHOO STATS")
		write_cron_yahoo_stats(curr_week, end_week)
		#write_cron_yahoo_FA()
		#write_cron_yahoo_FA_actual(curr_week, end_week)
		#write_cron_yahoo_FA_proj(curr_week, end_week)
	else:
		read_yahoo_stats(curr_week, end_week)






