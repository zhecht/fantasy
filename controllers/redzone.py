from bs4 import BeautifulSoup
from pprint import pprint
import argparse
import json


try:
	from controllers.read_rosters import *
	from controllers.reddit import *
	from controllers.snap_stats import *
except:
	from read_rosters import *
	from snap_stats import *
	from reddit import *
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

def merge_two_dicts(x, y):
	z = x.copy()
	z.update(y)
	return z

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
	elif name == "duke johnson jr":
		return "duke johnson jr."
	elif name == "dj moore":
		return "d.j. moore"
	return name

def write_redzone(curr_week=1):
	redzone_json = {}
	team_total_json = {}

	for link in SNAP_LINKS:
		link = "{}3.php".format(link)
		base_url = "http://subscribers.footballguys.com/teams/"
		team = link.split('-')[1]

		html = urllib.urlopen(base_url+link)
		soup = BeautifulSoup(html.read(), "lxml")
		rows = soup.find('table', class_='datasmall').find_all('tr')

		saw_QB = False
		total_redzone = 0
		team_total_json[team] = {"RB": [], "WR/TE": []}
		team_total_json[team]["RB"] = [0]*17
		team_total_json[team]["WR/TE"] = [0]*17

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
						if which_total.find("RB") > -1:
							team_total_json[team]["RB"][week - 1] += perc
						else:
							team_total_json[team]["WR/TE"][week - 1] += perc
				else:
					redzone_counts.append(perc)

			if full_name:# and full_name not in redzone_json:
				redzone_json[full_name] = {"looks": ','.join(str(x) for x in redzone_counts), "team": team, "looks_perc": ""}
	
	for player in redzone_json:
		
		perc_arr = []
		for week in range(1,17):
			team = redzone_json[player]["team"]
			looks = [int(x) for x in redzone_json[player]["looks"].split(",")]
			team_total_rb = team_total_json[team]["RB"][week - 1]
			team_total_wrte = team_total_json[team]["WR/TE"][week - 1]
			perc = 0 if team_total_rb + team_total_wrte == 0 else (looks[week - 1] / float(team_total_rb + team_total_wrte))
			perc_arr.append(round(perc, 2))

		redzone_json[player]["looks_perc"] = ','.join(str(x) for x in perc_arr)

	new_j = {}
	for player in redzone_json:
		new_name = player.lower().replace("'", "").replace(".", "")
		new_j[new_name] = redzone_json[player].copy()

		if new_name.split(" ")[-1] in ["jr", "iii", "ii", "sr", "v"]:
			new_name = " ".join(new_name.split(" ")[:-1])
			new_j[new_name] = redzone_json[player].copy()

	redzone_json = merge_two_dicts(new_j, redzone_json)

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

# Adds up total redzone looks and then last weeks too
def get_redzone_totals(curr_week, trends, snap_stats, team_total_json, pos="RB"):
	redzone_totals = {}
	for team in trends:
		redzone_totals[team] = {"total": 0, "last_total": 0}
		# only count up to curr_week NOT +1
		for week in range(1, curr_week):
			redzone_totals[team]["last_total"] += team_total_json[team][pos][week - 1]
		redzone_totals[team]["total"] = redzone_totals[team]["last_total"]
		redzone_totals[team]["total"] += team_total_json[team][pos][curr_week - 1]
		for player in trends[team]:
			redzone_totals[player] = {"total": 0, "last_total": 0}
			for week in range(1, curr_week):
				redzone_totals[player]["last_total"] += int(trends[team][player]["looks"].split(",")[week - 1])
			redzone_totals[player]["total"] = redzone_totals[player]["last_total"]
			redzone_totals[player]["total"] += int(trends[team][player]["looks"].split(",")[curr_week - 1])
	#print(redzone_totals[])
	return redzone_totals

def get_target_share_totals(curr_week, target_stats):
	target_totals = {}

def subtract_missed_rz(curr_week, snap_stats, team_total):
	tot = 0
	for week in range(curr_week):
		if int(snap_stats[week]) == 0:
			tot += team_total[week]
	return tot

def get_redzone_trends(rbbc_teams, curr_week=1, requested_pos="RB", is_ui=False):
	redzone_json = read_redzone()
	team_total_json = read_team_total()
	players_on_teams,translations = read_rosters()
	players_on_FA = read_FA()
	snap_stats = read_snap_stats()
	target_stats = read_target_stats()
	#players_on_teams = {**players_on_teams, **players_on_FA}
	players_on_teams = merge_two_dicts(players_on_teams, players_on_FA)
	update_players_on_teams(players_on_teams)

	trends = {}
	for player in redzone_json:
		#print(player)
		if player not in players_on_teams or players_on_teams[player]["position"] == "QB":
			continue
		if not is_ui and (player.find("jr") >= 0 or player.find(".") >= 0 or player.find("ii") >= 0):
			continue
		pos = players_on_teams[player]["position"]
		team = redzone_json[player]["team"]

		if pos in requested_pos.split("/") and (len(rbbc_teams) == 0 or team in rbbc_teams):
			if team not in trends:
				trends[team] = {}
			if player not in trends[team]:

				trends[team][player] = {
					"snaps": snap_stats[player]["perc"],
					"looks": redzone_json[player]["looks"],
					"targets": target_stats[player]["counts"],
					"total_targets": sum(map(int, target_stats[player]["counts"].split(","))),
					"total_looks": sum(map(int, redzone_json[player]["looks"].split(",")))
				}
	
	redzone_totals = get_redzone_totals(curr_week, trends, snap_stats, team_total_json, requested_pos)
	target_aggregates = get_target_aggregate_stats(curr_week)

	#print(redzone_totals)
	for team in trends:
		total_looks = team_total_json[team][requested_pos][curr_week - 1]

		for player in trends[team]:

			rz = int(trends[team][player]["looks"].split(",")[curr_week - 1])
			last_rz = int(trends[team][player]["looks"].split(",")[curr_week - 1])
			snaps = float(trends[team][player]["snaps"].split(",")[curr_week - 1])
			target_share = round(float(target_aggregates[player]["perc"].split(",")[curr_week - 1]) * 100, 1)
			try:
				denom = redzone_totals[team]["total"] - subtract_missed_rz(curr_week, snap_stats[player]["counts"].split(","), team_total_json[team][requested_pos])
				looks_perc = round(float(redzone_totals[player]["total"] / denom) * 100, 1)
			except:
				looks_perc = 0
			if curr_week == 1:
				last_snaps = snaps
				last_looks_perc = looks_perc
				last_target_share = target_share
			else:				
				last_snaps = float(trends[team][player]["snaps"].split(",")[curr_week - 2])
				#print(team, redzone_totals[team])
				try:			
					last_looks_perc = round(float(redzone_totals[player]["last_total"] / redzone_totals[team]["last_total"]) * 100, 1)
				except:
					last_looks_perc = 0
				try:
					last_target_share = round(float(target_aggregates[player]["perc"].split(",")[curr_week - 2]) * 100, 1)
				except:
					last_target_share = 0

			snaps_trend = round(snaps - last_snaps, 1)
			looks_trend = int(trends[team][player]["looks"].split(",")[curr_week - 1])
			target_trend = int(trends[team][player]["targets"].split(",")[curr_week - 1])
			looks_share_trend = round(looks_perc - last_looks_perc, 1)
			target_share_trend = round(target_share - last_target_share, 1)

			trends[team][player]["looks_share"] = looks_perc
			trends[team][player]["snaps"] = snaps
			trends[team][player]["target_share"] = target_share
			if is_ui:
				trends[team][player]["snaps_trend"] = "<b>+{}%</b>".format(snaps_trend) if snaps_trend > 0 else "{}%".format(snaps_trend or '-')
				trends[team][player]["looks_trend"] = "<b>+{}</b>".format(looks_trend) if looks_trend > 0 else "{}".format(looks_trend or '-')
				trends[team][player]["looks_share_trend"] = "<b>+{}%</b>".format(looks_share_trend) if looks_share_trend > 0 else "{}%".format(looks_share_trend or '-')
				trends[team][player]["target_trend"] = "<b>+{}</b>".format(target_trend or '-') if target_trend > 0 else "{}".format(target_trend or '-')
				trends[team][player]["target_share_trend"] = "<b>+{}%</b>".format(target_share_trend) if target_share_trend > 0 else "{}%".format(target_share_trend or '-')
			else:
				trends[team][player]["snaps_trend"] = "**+{}%**".format(snaps_trend) if snaps_trend > 0 else "{}%".format(snaps_trend or '0')
				trends[team][player]["looks_trend"] = "**+{}**".format(looks_trend) if looks_trend > 0 else "{}".format(looks_trend or '-')
				trends[team][player]["looks_share_trend"] = "**+{}%**".format(looks_share_trend) if looks_share_trend > 0 else "{}%".format(looks_share_trend or '0')
				trends[team][player]["target_trend"] = "**+{}**".format(target_trend) if target_trend > 0 else "{}".format(target_trend or '-')
				trends[team][player]["target_share_trend"] = "**+{}%**".format(target_share_trend) if target_share_trend > 0 else "{}%".format(target_share_trend or '0')
	
	if not is_ui:
		return trends
	new_j = {}
	for team in trends:
		players = trends[team]
		new_j[team] = {}
		for player in players:
			# without spaces
			#new_name = player.lower().replace("'", "").replace(".", "").replace(" ", "")
			#if new_name != player:
			#	new_j[team][new_name] = trends[team][player].copy()
			# no puncuation
			new_name = player.lower().replace("'", "").replace(".", "")
			if new_name != player:
				new_j[team][new_name] = trends[team][player].copy()

			if new_name.split(" ")[-1] in ["jr", "iii", "ii", "sr", "v"]:
				new_name = " ".join(new_name.split(" ")[:-1])
				new_j[team][new_name] = trends[team][player].copy()
	for team in new_j:
		for player in new_j[team]:
			trends[team][player] =  new_j[team][player].copy()

	j = {}
	for team in trends:
		for player in trends[team]:
			j[player] = trends[team][player].copy()
	return j

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
	players_on_FA = read_FA()
	snap_stats = read_snap_stats()

	players_on_teams = {**players_on_teams, **players_on_FA}
	top_redzone = []

	for player in redzone_json:
		#player_check = "mark ingram" if player == "mark ingram ii" else player
		player_check = player
		if player == "antonio brown":
			continue
		if player_check not in players_on_teams or players_on_teams[player_check]["position"] == "QB":
			
			#print(player)
			continue

		if player.find("jr") >= 0 or player.find(".") >= 0 or player.find("ii") >= 0:
			#print(player_check)
			continue
		
		if 0:
			try:
				if players_on_teams[player_check]["position"] == "QB":
					#pass
					continue
			except:
				print(player)
				continue

		looks_arr = redzone_json[player]["looks"].split(",")
		looks_perc_arr = redzone_json[player]["looks_perc"].split(",")
		total_player_looks = 0
		total_rb_looks = 0
		total_wrte_looks = 0
		last_total_player_looks = 0
		last_total_rb_looks = 0
		last_total_wrte_looks = 0

		for week in range(1, curr_week + 1):
			if int(snap_stats[player]["counts"].split(",")[week - 1]) == 0:
				continue

			looks = int(looks_arr[week - 1])
			looks_perc = float(looks_perc_arr[week - 1])
			total_rb_looks += team_total_json[redzone_json[player]["team"]]["RB"][week - 1]
			total_wrte_looks += team_total_json[redzone_json[player]["team"]]["WR/TE"][week - 1]
			total_player_looks += looks

		
		total_team_looks = total_rb_looks + total_wrte_looks

		last_total_team_looks = total_team_looks - team_total_json[redzone_json[player]["team"]]["RB"][curr_week - 1] - team_total_json[redzone_json[player]["team"]]["WR/TE"][curr_week - 1]
		
		last_3_total_team_looks = last_total_team_looks - team_total_json[redzone_json[player]["team"]]["RB"][curr_week - 2] - team_total_json[redzone_json[player]["team"]]["WR/TE"][curr_week - 2] - team_total_json[redzone_json[player]["team"]]["RB"][curr_week - 3] - team_total_json[redzone_json[player]["team"]]["WR/TE"][curr_week - 3]
		
		try:
			looks_perc = round((float(total_player_looks) / total_team_looks) * 100, 2)
			if curr_week >= 2:
				last_looks_perc = round((float(total_player_looks - int(looks_arr[curr_week - 1])) / last_total_team_looks) * 100, 2)
			else:
				last_looks_perc = looks_perc if curr_week == 1 else 0
			if curr_week >= 4:
				last_3_looks_perc = round((float(total_player_looks - int(looks_arr[curr_week - 3]) - int(looks_arr[curr_week - 2]) - int(looks_arr[curr_week - 1])) / last_3_total_team_looks) * 100, 2)
			else:
				last_3_looks_perc = looks_perc if curr_week == 1 else 0
		except:
			#print(player, total_team_looks, last_total_team_looks, last_3_total_team_looks)
			continue

		delta = round(looks_perc - last_looks_perc, 2)
		delta = "**+{}%**".format(delta) if delta > 0 else "{}%".format(delta)
		delta3 = round(looks_perc - last_3_looks_perc, 2)
		delta3 = "**+{}%**".format(delta3) if delta3 > 0 else "{}%".format(delta3)

		if int(snap_stats[player]["counts"].split(",")[curr_week - 1]) == 0:
			delta = 0

		if total_team_looks != 0 and total_player_looks != 0:
			top_redzone.append({"name": player_check, "looks": total_player_looks, "looks_perc": looks_perc, "total_team_looks": total_team_looks, "total_rb_looks": total_rb_looks, "total_wrte_looks": total_wrte_looks, "team": redzone_json[player]["team"], "delta": delta, "delta3": delta3})
			if player_check.find("andrew") >= 0:
				print(top_redzone[len(top_redzone) - 1])
	return top_redzone

SNAP_LINKS = [ "teampage-atl-", "teampage-buf-", "teampage-car-", "teampage-chi-", "teampage-cin-", "teampage-cle-", "teampage-clt-", "teampage-crd-", "teampage-dal-", "teampage-den-", "teampage-det-", "teampage-gnb-", "teampage-htx-", "teampage-jax-", "teampage-kan-", "teampage-mia-", "teampage-min-", "teampage-nor-", "teampage-nwe-", "teampage-nyg-", "teampage-nyj-", "teampage-oti-", "teampage-phi-", "teampage-pit-", "teampage-rai-", "teampage-ram-", "teampage-rav-", "teampage-sdg-", "teampage-sea-", "teampage-sfo-", "teampage-tam-", "teampage-was-" ]

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", help="Do Cron job", action="store_true")
	parser.add_argument("-t", "--team", help="Group By Team", action="store_true")
	parser.add_argument("-snaps", "--snaps", help="Snap Trends", action="store_true")
	parser.add_argument("-p", "--pretty", help="Pretty Print", action="store_true")
	parser.add_argument("-teams", "--teams", help="Filter teams")
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
		exit()

	top_redzone = get_player_looks_arr(curr_week)

	if args.snaps:
		team_trans = {"rav": "bal", "htx": "hou", "oti": "ten", "sdg": "lac", "ram": "lar", "rai": "oak", "clt": "ind", "crd": "ari"}
		rbbc_teams = ["crd", "atl", "rav", "buf", "car", "cin", "chi", "cle", "dal", "den", "det", "gnb", "htx", "jax", "clt", "kan", "sdg", "ram", "mia", "min", "nor", "nwe", "nyj", "nyg", "rai", "pit", "phi", "sea", "sfo", "tam", "oti", "was"]
		if args.teams:
			rbbc_teams = args.teams.split(",")
		snap_trends = get_redzone_trends(rbbc_teams, curr_week, "RB")

		for team in rbbc_teams:
			team_display = team_trans[team] if team in team_trans else team
			print("\n#{}".format(team_display))
			print("Player|Snap %|RZ Looks|RZ Looks Share|TGTS|RB Target Share")
			print(":--|:--|:--|:--|:--|:--")
			extra = ""
			for player in snap_trends[team]:
				if snap_trends[team][player]["snaps"] == 0:
					if snap_trends[team][player]["total_looks"] == 0 :
						continue
					extra += "{}|DNP|{}|{}%|{}|{}%\n".format(
						player,
						snap_trends[team][player]["total_looks"],
						snap_trends[team][player]["looks_share"],
						snap_trends[team][player]["total_targets"],
						snap_trends[team][player]["target_share"]
					)
				else:
					if snap_trends[team][player]["total_looks"] == 0 and snap_trends[team][player]["total_targets"] == 0:
						continue
					print("{}|{}% ({})|{} ({})|{}% ({})|{} ({})|{}% ({})".format(
						player,
						snap_trends[team][player]["snaps"], snap_trends[team][player]["snaps_trend"],
						snap_trends[team][player]["total_looks"], snap_trends[team][player]["looks_trend"],
						snap_trends[team][player]["looks_share"], snap_trends[team][player]["looks_share_trend"],
						snap_trends[team][player]["total_targets"], snap_trends[team][player]["target_trend"],
						snap_trends[team][player]["target_share"], snap_trends[team][player]["target_share_trend"]
						)
					)
			# print DNP on bottotm
			print(extra)
			# ranks

	elif args.team:
		
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
		# player | redzone looks RB share | snap count
	else:
		sorted_looks = sorted(top_redzone, key=operator.itemgetter("looks", "looks_perc"), reverse=True)
		sorted_looks_perc = sorted(top_redzone, key=operator.itemgetter("looks_perc"), reverse=True)

		#feelsbad_players = ["amari cooper", "sammy watkins", "stefon diggs", "adam thielen", "calvin ridley", "michael thomas", "odell beckham", "robert woods", "oj howard", "brandin cooks", "robby anderson"]
		feelsbad = {}
		players_on_teams,translations = read_rosters()
		players_on_FA = read_FA()
		players_on_teams = {**players_on_teams, **players_on_FA}
		update_players_on_teams(players_on_teams)

		print("\n#The FeelsBad Table")
		print("\nPlayer|(player looks / team looks)|Team RZ Look Share|3 Week Trend")
		print(":--|:--|:--|:--")
		for player in sorted_looks:
			continue
			if player["looks"] >= 0 and player["name"] in feelsbad_players: #player["team"] == 'rav':
				print("{}|({}/{})|{}%|{}".format(player["name"].title(), player["looks"], player["total_team_looks"], player["looks_perc"], player["delta3"]))
		#exit()

		print("\n#The Julio Jones Table")
		print("\nPlayer|(player looks / team looks)|Team RZ Look Share|3 Week Trend")
		print(":--|:--|:--|:--")
		for player in sorted_looks:
			#continue
			if player["looks"] >= 0 and player["name"] == "julio jones":
				print("{}|({}/{})|{}%|{}".format(player["name"].title(), player["looks"], player["total_team_looks"], player["looks_perc"], player["delta3"]))

		#exit()
		print("\n#Top 30 RB")
		print("\nPlayer|(player looks / team looks)|Team RZ Look Share|3 Week Trend")
		print(":--|:--|:--|:--")
		printed = 0
		for player in sorted_looks:
			#continue
			if printed == 30:
				break
			if player["looks"] >= 0 and players_on_teams[player["name"]]["position"] == "RB":
				printed += 1
				print("{}|({}/{})|{}%|{}".format(player["name"].title(), player["looks"], player["total_team_looks"], player["looks_perc"], player["delta3"]))

		print("\n#Top 45 WR")
		print("\nPlayer|(player looks / team looks)|Team RZ Look Share|3 Week Trend")
		print(":--|:--|:--|:--")
		printed = 0
		for player in sorted_looks:
			#continue
			if printed == 45:
				break
			if player["looks"] >= 0 and players_on_teams[player["name"]]["position"] == "WR":
				printed += 1
				print("{}|({}/{})|{}%|{}".format(player["name"].title(), player["looks"], player["total_team_looks"], player["looks_perc"], player["delta3"]))

		print("\n#Top 20 TE")
		print("\nPlayer|(player looks / team looks)|Team RZ Look Share|3 Week Trend")
		print(":--|:--|:--|:--")
		printed = 0
		for player in sorted_looks:
			#continue
			if printed == 20:
				break
			if player["looks"] >= 0 and (player["name"].find("heuerman") >= 0 or players_on_teams[player["name"]]["position"] == "TE"):
				printed += 1
				print("{}|({}/{})|{}%|{}".format(player["name"].title(), player["looks"], player["total_team_looks"], player["looks_perc"], player["delta3"]))

		
