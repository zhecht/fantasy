from bs4 import BeautifulSoup
import argparse
import json

try:
	import controllers.constants as constants
	from controllers.read_rosters import *
	from controllers.snap_stats import *
except:
	import constants
	from read_rosters import *
	from snap_stats import *
try:
	import urllib2 as urllib
except:
	import urllib.request as urllib

full_team_names = {
	"ram": "Rams",
	"nor": "Saints",
	"phi": "Eagles",
	"rai": "Raiders",
	"clt": "Colts",
	"rav": "Ravens",
	"nwe": "Patriots",
	"htx": "Texans",
	"sfo": "49ers",
	"sdg": "Chargers",
	"cin": "Bengals",
	"kan": "Chiefs",
	"atl": "Falcons",
	"pit": "Steelers",
	"den": "Broncos",
	"jax": "Jaguars",
	"det": "Lions",
	"chi": "Bears",
	"gnb": "Packers",
	"nyj": "Jets",
	"nyg": "Giants",
	"oti": "Titans",
	"dal": "Cowboys",
	"min": "Vikings",
	"was": "Redskins",
	"tam": "Buccaneers",
	"cle": "Browns",
	"sea": "Seahawks",
	"car": "Panthers",
	"crd": "Cardinals",
	"mia": "Dolphins",
	"buf": "Bills"
}

def fix_name(name):
	if name == "ted ginn jr":
		return "ted ginn jr."
	elif name == "odell beckham jr":
		return "odell beckham jr."
	elif name == "ben watson":
		return "benjamin watson"
	elif name == "allen robinson":
		return "allen robinson ii"
	elif name == "todd gurley":
		return "todd gurley ii"
	elif name == "marvin jones jr":
		return "marvin jones jr."
	return name

def write_redzone(curr_week=1):
	redzone_json = {}
	team_total_json = {}

	for link in constants.SNAP_LINKS:
		link = "{}3.php".format(link)
		base_url = "http://subscribers.footballguys.com/teams/"
		team = link.split('-')[1]

		html = urllib.urlopen(base_url+link)
		soup = BeautifulSoup(html.read(), "lxml")
		rows = soup.find('table', class_='datasmall').find_all('tr')

		saw_QB = False
		total_redzone = 0
		team_total_json[team] = [0]*17

		for row in rows[1:]:
			tds = row.find_all('td')
			redzone_counts = []
			which_total = ""
			full_name = ""
			if row.get("bgcolor") is not None:
				which_total = tds[0].find("b").text
			else:
				full = tds[0].find('a').text
				full_name = fix_name(full.lower().replace("'", ""))

			for week in range(1,17):
				try:
					perc = int(tds[week].text)
				except:
					perc = 0

				if which_total.find("TOTAL") != -1:
					if which_total.find("QB") == -1:
						team_total_json[team][week - 1] += perc
				else:
					redzone_counts.append(perc)

			if full_name:# and full_name not in redzone_json:
				redzone_json[full_name] = {"looks": ','.join(str(x) for x in redzone_counts), "team": team, "looks_perc": ""}
	
	for player in redzone_json:
		
		perc_arr = []
		for week in range(1,17):
			team = redzone_json[player]["team"]
			looks = [int(x) for x in redzone_json[player]["looks"].split(",")]
			team_total = team_total_json[team][week - 1]
			perc = 0 if team_total == 0 else (looks[week - 1] / float(team_total))
			perc_arr.append(round(perc, 2))

		redzone_json[player]["looks_perc"] = ','.join(str(x) for x in perc_arr)

	with open("static/looks/redzone.json", "w") as outfile:
		json.dump(redzone_json, outfile, indent=4)
	with open("static/looks/team_total.json", "w") as outfile:
		json.dump(team_total_json, outfile, indent=4)


def read_redzone():
	with open("static/looks/redzone.json") as fh:
		returned_json = json.loads(fh.read())
	return returned_json

def read_team_total():
	with open("static/looks/team_total.json") as fh:
		returned_json = json.loads(fh.read())
	return returned_json

def get_player_looks_json(curr_week=1):
	redzone_json = read_redzone()
	team_total_json = read_team_total()
	players_on_teams,translations = read_rosters()

	top_redzone = {}
	for player in redzone_json:
		if player not in players_on_teams or players_on_teams[player]["position"] == "QB":
			continue

		looks_arr = redzone_json[player]["looks"].split(",")
		looks_perc_arr = redzone_json[player]["looks_perc"].split(",")
		total_player_looks = 0
		total_team_looks = 0
		for week in range(1, curr_week + 1):

			looks = int(looks_arr[week - 1])
			looks_perc = float(looks_perc_arr[week - 1])

			total_team_looks += team_total_json[redzone_json[player]["team"]][week - 1]
			total_player_looks += looks

		if total_team_looks != 0 and total_player_looks != 0:
			top_redzone[player] = total_player_looks
	return top_redzone

def get_player_looks_arr(curr_week=1):
	redzone_json = read_redzone()
	team_total_json = read_team_total()
	players_on_teams,translations = read_rosters()
	snap_stats = read_snap_stats()

	top_redzone = []
	for player in redzone_json:
		if player not in players_on_teams or players_on_teams[player]["position"] == "QB":
			continue

		looks_arr = redzone_json[player]["looks"].split(",")
		looks_perc_arr = redzone_json[player]["looks_perc"].split(",")
		total_player_looks = 0
		total_team_looks = 0
		for week in range(1, curr_week + 1):
			if int(snap_stats[player]["counts"].split(",")[week - 1]) == 0:
				continue

			looks = int(looks_arr[week - 1])
			looks_perc = float(looks_perc_arr[week - 1])

			total_team_looks += team_total_json[redzone_json[player]["team"]][week - 1]
			total_player_looks += looks

		if total_team_looks != 0 and total_player_looks != 0:
			top_redzone.append({"name": player, "looks": total_player_looks, "looks_perc": round(float(total_player_looks) / total_team_looks, 2), "total_team_looks": total_team_looks, "team": redzone_json[player]["team"]})
	return top_redzone

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", help="Do Cron job", action="store_true")
	parser.add_argument("-t", "--team", help="Group By Team", action="store_true")
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
		print("WRITING REDZONE")
		write_redzone(curr_week)

	top_redzone = get_player_looks_arr(curr_week)

	if args.team:
		
		# Team
		team_totals = {}
		for arr in top_redzone:
			if arr["team"] not in team_totals:
				team_totals[arr["team"]] = arr["total_team_looks"]
		team_totals = sorted(team_totals.items(), key=lambda x: x[1], reverse=True)

		print("\nTeam|Total Redzone Looks")
		print(":--|:--")
		for team, tot in team_totals:
			print("{}|{}".format(full_team_names[team], tot))
	else:
		sorted_looks = sorted(top_redzone, key=operator.itemgetter("looks"), reverse=True)
		sorted_looks_perc = sorted(top_redzone, key=operator.itemgetter("looks_perc"), reverse=True)

		for player in sorted_looks[:20]:
			continue
			print("{}|{}".format(player["name"].title(), player["looks"]))

		#print("\nMOST LOOKS IN REDZONE (PERCENT OF W/R/T)")
		print("\nPlayer|% of team's redzone looks|(player redzone looks / team redzone looks)")
		print(":--|:--|:--")
		players_on_teams,translations = read_rosters()
		for player in sorted_looks_perc:
			#print("{}\t{}%\t({}/{})".format(player["name"], player["looks_perc"] * 100, player["looks"], int(player["looks"] / player["looks_perc"])))
			if player["looks"] >= 0 and players_on_teams[player["name"]]["position"] == "TE":
				print("{}|{}%|({}/{})".format(player["name"].title(), player["looks_perc"] * 100, player["looks"], player["total_team_looks"]))
				#pass
