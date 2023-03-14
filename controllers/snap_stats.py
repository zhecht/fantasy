from bs4 import BeautifulSoup
import argparse
import os
import json

try:
	from controllers.functions import *
except:
	from functions import *

try:
	import urllib2 as urllib
except:
	import urllib.request as urllib

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
    # if on linux aka prod
    prefix = "/home/zhecht/fantasy/"
elif os.path.exists("/home/playerprops/fantasy"):
	# if on linux aka prod
	prefix = "/home/playerprops/fantasy/"

def merge_two_dicts(x, y):
	z = x.copy()
	z.update(y)
	return z

def read_reception_stats():
	with open(f"{prefix}static/reception_counts.json") as fh:
		returned_json = json.loads(fh.read())
	new_json = {}
	for player in returned_json:
		real_name = " ".join(player.split(" ")[:-1])
		new_json[real_name] = returned_json[player]

	new_j = {}
	for player in new_json:
		new_name = player.lower().replace("'", "").replace(".", "")
		new_j[new_name] = new_json[player].copy()

		if new_name.split(" ")[-1] in ["jr", "iii", "ii", "sr", "v"]:
			new_name = " ".join(new_name.split(" ")[:-1])
			new_j[new_name] = new_json[player].copy()

	new_json = merge_two_dicts(new_j, new_json)
	return new_json

def read_nfl_trades():
	with open("{}static/nfl_trades.json".format(prefix)) as fh:
		returned_json = json.loads(fh.read())
	return returned_json

def read_snap_stats(curr_week):
	teams = ['crd', 'atl', 'rav', 'buf', 'car', 'chi', 'cin', 'cle', 'dal', 'den', 'det', 'gnb', 'htx', 'clt', 'jax', 'kan', 'sdg', 'ram', 'rai', 'mia', 'min', 'nor', 'nwe', 'nyg', 'nyj', 'phi', 'pit', 'sea', 'sfo', 'tam', 'oti', 'was']
	trades = read_nfl_trades()
	res = {}
	for team in teams:
		with open(f"{prefix}static/profootballreference/{team}/stats.json") as fh:
			stats = json.load(fh)
		for name in stats:
			if name == "OFF":
				continue
			perc = []
			counts = []
			for week in range(curr_week):
				p = 0
				c = 0
				try:
					p = stats[name][f"wk{week+1}"]["snap_perc"]
					c = stats[name][f"wk{week+1}"]["snap_counts"]
				except:
					pass

				perc.append(str(p))
				counts.append(str(c))

			if name in trades:
				if trades[name]["team"] == team:
					res[name] = {"perc": ",".join(perc), "counts": ",".join(counts)}
			else:
				res[name] = {"perc": ",".join(perc), "counts": ",".join(counts)}
	return res

def read_snap_stats2():
	with open("static/snap_counts.json") as fh:
		returned_json = json.loads(fh.read())
	new_json = {}
	for player in returned_json:
		real_name = " ".join(player.split(" ")[:-1])
		if real_name in new_json:
			perc = returned_json[player]["perc"].split(",")
			perc = [ str(int(val) + int(perc[idx])) for idx, val in enumerate(new_json[real_name]["perc"].split(",")) ]
			counts = returned_json[player]["counts"].split(",")
			counts = [ str(int(val) + int(counts[idx])) for idx, val in enumerate(new_json[real_name]["counts"].split(",")) ]
			new_json[real_name] = {"perc": ','.join(perc), "counts": ','.join(counts)}
		else:
			new_json[real_name] = {"perc": returned_json[player]["perc"], "counts": returned_json[player]["counts"]}
	new_j = {}
	for player in new_json:
		new_name = player.lower().replace("'", "").replace(".", "")
		new_j[new_name] = new_json[player].copy()

		if new_name.split(" ")[-1] in ["jr", "iii", "ii", "sr", "v"]:
			new_name = " ".join(new_name.split(" ")[:-1])
			new_j[new_name] = new_json[player].copy()

	new_json = merge_two_dicts(new_j, new_json)
	return new_json

def read_target_stats():
	with open(f"{prefix}static/target_counts.json") as fh:
		returned_json = json.loads(fh.read())

	trades = read_nfl_trades()
	new_json = {}
	for player in returned_json:
		team = player.split(" ")[-1]
		real_name = " ".join(player.split(" ")[:-1])
		if real_name in trades:
			if trades[real_name]["team"] == team:
				new_json[real_name] = {"perc": returned_json[player]["perc"], "counts": returned_json[player]["counts"], "pos": returned_json[player]["pos"]}	
		else:
			new_json[real_name] = {"perc": returned_json[player]["perc"], "counts": returned_json[player]["counts"], "pos": returned_json[player]["pos"]}
	return new_json

def read_team_target_stats():
	with open(f"{prefix}static/team_target_total.json") as fh:
		returned_json = json.loads(fh.read())
	return returned_json

def write_reception_stats():
	j = {}
	for team in SNAP_LINKS:
		link = f"http://www.footballguys.com/stats/targets/teams?team={team}&year={YEAR}"
		
		html = urllib.urlopen(link)
		soup = BeautifulSoup(html.read(), "lxml")
		tbodys = soup.find("div", id="stats_targets_data").findAll("tbody")

		# RB / WR
		positions = ["RB", "WR", "TE"]
		for table in tbodys:
			rows = table.find_all("tr")
			for row in rows:
				tds = row.find_all('td')
				full = tds[0].find('a').text
				full_name = fixName(full.lower().replace("'", ""))

				try:
					targets = int(tds[-1].txt)
				except:
					targets = 0
				j[f"{full_name} {team}"] = targets

	with open(f"{prefix}static/reception_counts.json", "w") as outfile:
		json.dump(j, outfile, indent=4)

def write_team_target_stats():
	import profootballreference
	j = {}
	for team in SNAP_LINKS:
		link = f"http://www.footballguys.com/stats/targets/teams?team={team.upper()}&year={YEAR}"

		opps = profootballreference.get_opponents(team)
		html = urllib.urlopen(link)
		soup = BeautifulSoup(html.read(), "lxml")
		rows = soup.find("div", id="stats_targets_data").findAll("tr")[1:]

		j[team] = {"RB": [], "WR/TE": []}
		for idx, row in enumerate(rows):
			tds = row.find_all('td')
			if not tds[0].text.strip().lower().endswith("totals"):
				continue

			total_targets = [0]*curr_week
			pos = tds[0].text.strip().split(" ")[0]
			for week in range(curr_week):
				try:
					if opps[week] != "BYE":
						total_targets[week] = int(tds[week+1].text.strip())
				except:
					pass

			j[team][pos] = ",".join(str(x) for x in total_targets)
		# aggregate WR/TE
		TE_totals = j[team]["TE"].split(",")
		WR_totals = j[team]["WR"].split(",")
		for idx, tot in enumerate(TE_totals):
			WR_totals[idx] = int(WR_totals[idx]) + int(TE_totals[idx])
		j[team]["WR/TE"] = ','.join(str(x) for x in WR_totals)
		del j[team]["WR"]
		del j[team]["TE"]
	with open(f"{prefix}static/team_target_total.json", "w") as outfile:
		json.dump(j, outfile, indent=4)


def write_target_stats():
	import profootballreference
	base_url = "http://subscribers.footballguys.com/teams/"
	j = {}
	team_targets = read_team_target_stats()

	for team in SNAP_LINKS:
		link = f"http://www.footballguys.com/stats/targets/teams?team={team.upper()}&year={YEAR}"
		opps = profootballreference.get_opponents(team)
		html = urllib.urlopen(link)
		soup = BeautifulSoup(html.read(), "lxml")
		rows = soup.find("div", id="stats_targets_data").findAll("tr")[1:]
		totals = {}

		currPos = 0
		positions = ["RB", "WR", "TE"]
		for idx, row in enumerate(rows):
			tds = row.find_all('td')

			if tds[0].text.strip().lower().endswith("totals"):
				currPos += 1
				continue

			full = tds[0].find('a').text
			full_name = fixName(full.lower().replace("'", ""))

			targets = []
			target_counts_perc = []
			for week in range(curr_week):
				t = 0
				try:
					if opps[week] != "BYE":
						t = int(tds[week+1].text.strip())
				except:
					pass

				targets.append(t)

				pos = "RB" if positions[currPos] == 0 else "WR/TE"
				total_targets = float(team_targets[team][pos].split(",")[week])
				if total_targets == 0:
					target_counts_perc.append(0)
				else:
					target_counts_perc.append(round(t / total_targets, 3))

			target_counts = ','.join(str(x) for x in targets)
			target_counts_perc = ','.join(str(x) for x in target_counts_perc)
			j[f"{full_name} {team}"] = {"perc": target_counts_perc, "counts": target_counts, "pos": positions[currPos]}

	with open("static/target_counts.json", "w") as outfile:
		json.dump(j, outfile, indent=4)

# total teams targets up to each week. 
def get_team_targets_to_week(snap_stats, team_targets):
	j = {}
	for team in team_targets:
		j[team] = {"RB": [], "WR/TE": []}
		rb_total = 0
		wr_total = 0
		for week in range(curr_week):
			rb_total += int(team_targets[team]["RB"].split(",")[week])
			wr_total += int(team_targets[team]["WR/TE"].split(",")[week])
			j[team]["RB"].append(str(rb_total))
			j[team]["WR/TE"].append(str(wr_total))
		j[team]["RB"] = ','.join(j[team]["RB"])
		j[team]["WR/TE"] = ','.join(j[team]["WR/TE"])

	return j

# skip counting if snaps == 0
def get_player_target_aggregate(aggregates, snaps):
	targets = map(int, aggregates.split(","))
	diff = []
	curr = 0
	for target in targets:
		curr = abs(target - curr)
		diff.append(curr)
		curr = target
	j = []
	curr = 0
	targets = map(int, aggregates.split(","))
	for week, target in enumerate(targets):
		if week < len(snaps["counts"].split(",")) and int(snaps["counts"].split(",")[week]) != 0:
			curr += diff[week]
		j.append(curr)
	return j

def get_target_aggregate_stats(curr_week=1):
	# these take the weekly target stats and adds up target share throughout season
	snap_stats = read_snap_stats(curr_week)
	team_targets = read_team_target_stats()
	team_targets_aggregate = get_team_targets_to_week(snap_stats, team_targets)

	target_stats = {}
	with open(f"{prefix}static/target_counts.json") as fh:
		target_stats = json.loads(fh.read())
	j = {}
	for name_team in target_stats:
		player = " ".join(name_team.split(" ")[:-1])		
		team = name_team.split(" ")[-1]
		targets_arr = target_stats[name_team]["counts"].split(",")
		pos = "RB" if target_stats[name_team]["pos"].find("RB") >= 0 else "WR/TE"
		total_targets = 0
		target_shares = []
		targets = []
		if player not in snap_stats:
			continue
		player_targets_aggregate = get_player_target_aggregate(team_targets_aggregate[team][pos], snap_stats[player])
		for week, target in enumerate(targets_arr):
			total_targets += int(target)
			try:
				target_share = round(total_targets / player_targets_aggregate[week], 3)
			except:
				target_share = 0
			
			targets.append(total_targets)
			target_shares.append(target_share)
		j[name_team] = {
			"perc": ','.join(str(x) if idx < curr_week else '0' for idx, x in enumerate(target_shares)),
			"counts": ','.join(str(x) if idx < curr_week else '0' for idx, x in enumerate(targets)),
			"pos": target_stats[name_team]["pos"]
		}

	trades = read_nfl_trades()
	new_json = {}
	for player in j:
		team = player.split(" ")[-1]
		real_name = " ".join(player.split(" ")[:-1])
		if real_name in trades:
			if trades[real_name]["team"] == team:
				new_json[real_name] = {"perc": j[player]["perc"], "counts": j[player]["counts"], "pos": j[player]["pos"]}
		else:
			new_json[real_name] = {"perc": j[player]["perc"], "counts": j[player]["counts"], "pos": j[player]["pos"]}
	return new_json



def write_snap_stats():
	j = {}
	for link in SNAP_LINKS:
		link = "{}6.php".format(link)
		base_url = "http://subscribers.footballguys.com/teams/"
		html = urllib.urlopen(base_url+link)
		soup = BeautifulSoup(html.read(), "lxml")
		rows = soup.find('table', class_='datasmall').find_all('tr')

		for row in rows[1:]:
			if row.get("class") is None:
				tds = row.find_all('td')

				full = tds[0].find('a').text
				full_name = fixName(full.lower().replace("'", ""))

				snap_counts = []
				snap_counts_perc = []
				for week in range(1,17):
					try:
						snaps, br, snaps_perc = tds[week].contents
						snaps_perc = int(snaps_perc[:-1])
						snaps = int(snaps)
						#perc = int(tds[week].find('br').next_sibling[:-1])
					except:
						snaps_perc = 0
						snaps = 0

					snap_counts.append(snaps)
					snap_counts_perc.append(snaps_perc)

				team = link.split('-')[1]
				snap_counts = ','.join(str(x) for x in snap_counts)
				snap_counts_perc = ','.join(str(x) for x in snap_counts_perc)


				j[full_name+" "+team] = {"perc": snap_counts_perc, "counts": snap_counts}

	with open(f"{prefix}static/snap_counts.json", "w") as outfile:
		json.dump(j, outfile, indent=4)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", help="Do Cron job", action="store_true")
	#parser.add_argument("-t", "--team", help="Group By Team", action="store_true")
	parser.add_argument("-s", "--start", help="Start Week", type=int)
	parser.add_argument("-e", "--end", help="End Week", type=int)

	args = parser.parse_args()
	end_week = 2

	if args.start:
		curr_week = args.start
		end_week = curr_week + 1
		if args.end:
			end_week = args.end
	if args.cron:
		print("WRITING SNAPS")
		#write_snap_stats()
		write_team_target_stats()
		write_target_stats()
		exit()
	#write_team_target_stats()
	#write_target_stats()
	#get_target_aggregate_stats(curr_week)


