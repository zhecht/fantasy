from bs4 import BeautifulSoup
import json

try:
	import controllers.constants as constants
	from controllers.read_rosters import *
except:
	import constants
	from read_rosters import *
try:
	import urllib2 as urllib
except:
	import urllib.request as urllib

def fix_name(name):
	if name == "ted ginn jr":
		return "ted ginn jr."
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
	print("WRITIING REDZONE")
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

			if full_name and full_name not in redzone_json:
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
		#redzone_json[player].pop("team", None)
	#print(redzone_json)
	#print(team_total_json)

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

if __name__ == '__main__':
	curr_week = 2

	#write_redzone(curr_week)
	redzone_json = read_redzone()
	team_total_json = read_team_total()
	players_on_teams,translations = read_rosters()

	top_redzone = []
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

		#for i in range(len(player), 20):
			#player += ' '
		if total_team_looks != 0 and total_player_looks != 0:
			top_redzone.append({"name": player, "looks": total_player_looks, "looks_perc": round(float(total_player_looks) / total_team_looks, 2), "total_team_looks": total_team_looks, "team": redzone_json[player]["team"]})		


	sorted_looks = sorted(top_redzone, key=operator.itemgetter("looks"), reverse=True)
	sorted_looks_perc = sorted(top_redzone, key=operator.itemgetter("looks_perc"), reverse=True)

	
	
	print("A Redzone look is a target or rushing attempt within the opponents 20 yard line.")
	for player in sorted_looks[:20]:
		continue
		print("{}\t{}".format(player["name"], player["looks"]))

	#print("\nMOST LOOKS IN REDZONE (PERCENT OF W/R/T)")
	print("\nPlayer|% of team's redzone looks|(redzone looks / total redzone looks)")
	print(":--|:--|:--")
	for player in sorted_looks_perc:
		#print("{}\t{}%\t({}/{})".format(player["name"], player["looks_perc"] * 100, player["looks"], int(player["looks"] / player["looks_perc"])))
		if player["looks"] >= 0 and player["team"].lower() == "det":
			print("{}|{}%|({}/{})".format(player["name"].title(), player["looks_perc"] * 100, player["looks"], player["total_team_looks"]))


