from bs4 import BeautifulSoup
import argparse
import json
try:
	import controllers.constants as constants
except:
	import constants
try:
	import urllib2 as urllib
except:
	import urllib.request as urllib

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
	return name


def read_reception_stats():
	with open("static/reception_counts.json") as fh:
		returned_json = json.loads(fh.read())
	new_json = {}
	for player in returned_json:
		real_name = " ".join(player.split(" ")[:-1])
		new_json[real_name] = returned_json[player]
	return new_json

def read_snap_stats():
	with open("static/snap_counts.json") as fh:
		returned_json = json.loads(fh.read())
	new_json = {}
	for player in returned_json:
		real_name = " ".join(player.split(" ")[:-1])
		new_json[real_name] = {"perc": returned_json[player]["perc"], "counts": returned_json[player]["counts"]}
	#for player in new_json:
	return new_json

def read_target_stats():
	with open("static/target_counts.json") as fh:
		returned_json = json.loads(fh.read())
	new_json = {}
	for player in returned_json:
		real_name = " ".join(player.split(" ")[:-1])
		new_json[real_name] = {"perc": returned_json[player]["perc"], "counts": returned_json[player]["counts"], "pos": returned_json[player]["pos"]}
	return new_json

def read_team_target_stats():
	with open("static/team_target_total.json") as fh:
		returned_json = json.loads(fh.read())
	return returned_json

def write_reception_stats():
	base_url = "http://subscribers.footballguys.com/teams/"
	j = {}
	for link in SNAP_LINKS:
		link = "{}1.php".format(link)
		team = link.split('-')[1]
		
		html = urllib.urlopen(base_url+link)
		soup = BeautifulSoup(html.read(), "lxml")
		all_tables = soup.find_all('table', class_='data')

		# RB / WR
		for table in all_tables[1:3]:
			rows = table.find_all("tr")
			for row in rows[1:]:
				tds = row.find_all('td')
				full = tds[0].find('a').text
				full_name = fix_name(full.lower().replace("'", ""))

				try:
					j[full_name+" "+team] = int(tds[2].text) + int(tds[7].text)
				except:
					print(tds[2], tds[7])
		# TE
		rows = all_tables[3].find_all("tr")
		for row in rows[1:]:
			tds = row.find_all('td')
			full = tds[0].find('a').text
			full_name = fix_name(full.lower().replace("'", ""))

			j[full_name+" "+team] = int(tds[3].text)

	with open("static/reception_counts.json", "w") as outfile:
		json.dump(j, outfile, indent=4)

def write_team_target_stats():
	base_url = "http://subscribers.footballguys.com/teams/"
	j = {}
	for link in SNAP_LINKS:
		link = "{}2.php".format(link)
		team = link.split('-')[1]

		j[team] = {}
		
		html = urllib.urlopen(base_url+link)
		soup = BeautifulSoup(html.read(), "lxml")
		rows = soup.find('table', class_='datasmall').find_all('tr')

		for row in rows[1:]:
			if row.get("bgcolor") is not None:
				# Totals row
				curr_pos = row.find("b").text.split(" ")[0]
				tds = row.find_all('td')
				target_counts = []
				for week in range(1,17):
					try:
						targets = int(tds[week].text)
					except:
						targets = 0

					target_counts.append(targets)

				j[team][curr_pos] = ','.join(str(x) for x in target_counts)
		# aggregate WR/TE
		TE_totals = j[team]["TE"].split(",")
		WR_totals = j[team]["WR"].split(",")
		for idx, tot in enumerate(TE_totals):
			WR_totals[idx] = int(WR_totals[idx]) + int(TE_totals[idx])
		j[team]["WR/TE"] = ','.join(str(x) for x in WR_totals)
		del j[team]["WR"]
		del j[team]["TE"]
	with open("static/team_target_total.json", "w") as outfile:
		json.dump(j, outfile, indent=4)


def write_target_stats():
	base_url = "http://subscribers.footballguys.com/teams/"
	j = {}
	team_targets = read_team_target_stats()

	for link in SNAP_LINKS:
		link = "{}2.php".format(link)
		team = link.split('-')[1]
		
		html = urllib.urlopen(base_url+link)
		soup = BeautifulSoup(html.read(), "lxml")
		rows = soup.find('table', class_='datasmall').find_all('tr')
		totals = {}
		curr_pos = "WR TOTAL"
		new_pos = "WR TOTAL"

		for row in rows[1:]:
			if row.get("bgcolor") is None:
				tds = row.find_all('td')

				full = tds[0].find('a').text
				full_name = fix_name(full.lower().replace("'", ""))

				target_counts = []
				target_counts_perc = []
				for week in range(1,17):
					try:
						targets = int(tds[week].find("a").text)
					except:
						targets = 0
					target_counts.append(targets)

					p = "RB" if new_pos.find("RB") >= 0 else "WR/TE"
					total_targets = float(team_targets[team][p].split(",")[week - 1])
					if total_targets == 0:
						target_counts_perc.append(0)
					else:
						target_counts_perc.append(round(targets / total_targets, 3))

				team = link.split('-')[1]
				target_counts = ','.join(str(x) for x in target_counts)
				target_counts_perc = ','.join(str(x) for x in target_counts_perc)

				j[full_name+" "+team] = {"perc": target_counts_perc, "counts": target_counts, "pos": new_pos}
			else:
				# Total row
				curr_pos = row.find("b").text
				if curr_pos == "WR TOTAL":
					new_pos = "TE TOTAL"
				elif curr_pos == "TE TOTAL":
					new_pos = "RB TOTAL"

	with open("static/target_counts.json", "w") as outfile:
		json.dump(j, outfile, indent=4)

# total teams targets up to each week
def get_team_targets_to_week(team_targets):
	j = {}
	for team in team_targets:
		j[team] = {"RB": [], "WR/TE": []}
		rb_total = 0
		wr_total = 0
		for week in range(16):
			rb_total += int(team_targets[team]["RB"].split(",")[week])
			wr_total += int(team_targets[team]["WR/TE"].split(",")[week])
			j[team]["RB"].append(str(rb_total))
			j[team]["WR/TE"].append(str(wr_total))
		j[team]["RB"] = ','.join(j[team]["RB"])
		j[team]["WR/TE"] = ','.join(j[team]["WR/TE"])

	return j


def get_target_aggregate_stats(curr_week=1):
	# these take the weekly target stats and adds up target share throughout season
	team_targets = read_team_target_stats()
	team_targets_aggregate = get_team_targets_to_week(team_targets)

	target_stats = {}
	with open("static/target_counts.json") as fh:
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
		for week, target in enumerate(targets_arr):
			total_targets += int(target)
			try:
				target_share = round(total_targets / int(team_targets_aggregate[team][pos].split(",")[week]), 3)
			except:
				target_share = 0
			
			targets.append(total_targets)
			target_shares.append(target_share)
		j[name_team] = {
			"perc": ','.join(str(x) if idx < curr_week else '0' for idx, x in enumerate(target_shares)),
			"counts": ','.join(str(x) if idx < curr_week else '0' for idx, x in enumerate(targets)),
			"pos": target_stats[name_team]["pos"]
		}

	new_json = {}
	for player in j:
		real_name = " ".join(player.split(" ")[:-1])
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
				full_name = fix_name(full.lower().replace("'", ""))

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

	with open("static/snap_counts.json", "w") as outfile:
		json.dump(j, outfile, indent=4)


SNAP_LINKS = [ "teampage-atl-", "teampage-buf-", "teampage-car-", "teampage-chi-", "teampage-cin-", "teampage-cle-", "teampage-clt-", "teampage-crd-", "teampage-dal-", "teampage-den-", "teampage-det-", "teampage-gnb-", "teampage-htx-", "teampage-jax-", "teampage-kan-", "teampage-mia-", "teampage-min-", "teampage-nor-", "teampage-nwe-", "teampage-nyg-", "teampage-nyj-", "teampage-oti-", "teampage-phi-", "teampage-pit-", "teampage-rai-", "teampage-ram-", "teampage-rav-", "teampage-sdg-", "teampage-sea-", "teampage-sfo-", "teampage-tam-", "teampage-was-" ]

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", help="Do Cron job", action="store_true")
	#parser.add_argument("-t", "--team", help="Group By Team", action="store_true")
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
		print("WRITING SNAPS")
		write_snap_stats()
		write_team_target_stats()
		write_target_stats()
		exit()
	#write_team_target_stats()
	#write_target_stats()
	#get_target_aggregate_stats(curr_week)


