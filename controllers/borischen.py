import argparse
import json
import re
from sys import platform
from subprocess import call
from bs4 import BeautifulSoup as BS

try:
	from controllers.read_rosters import *
except:
	from read_rosters import *

prefix = ""
borischen_prefix = "/Users/zhecht/Documents/fftiers"
if platform != "darwin":
	# if on linux aka prod
	prefix = "/home/zhecht/fantasy/"
	borischen_prefix = "/home/zhecht/fftiers"

def merge_two_dicts(x, y):
	z = x.copy()
	z.update(y)
	return z

def fix_name(name):
	name = name.lower().replace("'", "")
	if name == "todd gurley":
		return "todd gurley ii"
	elif name == "melvin gordon":
		return "melvin gordon iii"
	elif name == "mitch trubisky":
		return "mitchell trubisky"
	elif name == "willie snead":
		return "willie snead iv"
	elif name == "allen robinson":
		return "allen robinson ii"
	elif name == "ted ginn":
		return "ted ginn jr."
	elif name == "marvin jones":
		return "marvin jones jr."
	elif name == "will fuller":
		return "will fuller v"
	elif name == "paul richardson":
		return "paul richardson jr."
	elif name == "duke johnson":
		return "duke johnson jr."
	elif name == "odell beckham":
		return "odell beckham jr."
	elif name == "odell beckham jr":
		return "odell beckham jr."
	elif name == "mark ingram ii":
		return "mark ingram"
	elif name == "darrell henderson":
		return "darrell henderson jr."
	return name

def read_borischen_rankings(curr_week=1):
	rankings = {}
	for position in ["qb", "rb", "wr", "te"]:
		rankings[position] = {}
		with open("{}static/rankings/{}/{}/borischen.json".format(prefix, curr_week, position)) as fh:
			rankings[position] = json.loads(fh.read())
	return rankings

def read_borischen_tiers(curr_week=1):
	tiers = {}
	for position in ["qb", "rb", "wr", "te"]:
		with open("{}static/borischen/{}_tiers.json".format(prefix, position)) as fh:
			all_tiers = json.loads(fh.read())
		for tier in all_tiers:
			players = all_tiers[tier]
			for player in players:
				tiers[player.lower().replace("'", "").replace(".", "")] = tier
	return tiers

def read_github_borischen_rankings(curr_week=1):
	rankings = {}
	players_on_teams, name_translations = read_rosters()
	players_on_FA = read_FA()
	players_on_teams = merge_two_dicts(players_on_teams, players_on_FA)

	for pos in ["qb", "rb", "wr", "te"]:
		rankings[pos] = {}
		f = open("{}/data/{}/w{}.csv".format(borischen_prefix, pos, curr_week), "r")
		idx = 1

		for line in f:
			split_line = line.split(",")
			name = fix_name(split_line[1].lower().replace("'", ""))

			if name not in players_on_teams:
				continue
			rankings[pos][name] = idx
			idx += 1
		f.close()
	return rankings

def get_short_pos(pos):
	if pos == "wide-receiver":
		return "wr"
	elif pos == "running-back":
		return "rb"
	elif pos == "tight-end":
		return "te"
	elif pos == "quarterback":
		return "qb"

def write_cron_borischen_rankings_api(curr_week=1):
	for pos in ["qb", "rb", "wr", "te"]:
		if not os.path.isdir("{}/data/{}".format(borischen_prefix, pos)):
			os.mkdir("{}/data/{}".format(borischen_prefix, pos))
		call(["python", "{}/src/fp_api.py".format(borischen_prefix), "-j", "{}/data/{}/w{}.json".format(borischen_prefix, pos, curr_week), "-c", "{}/data/{}/w{}.csv".format(borischen_prefix, pos,curr_week), "-y", "2019", "-p", pos, "-w", str(curr_week), "-s", "HALF"])

	rankings = read_github_borischen_rankings(curr_week)
	for pos in ["qb", "rb", "wr", "te"]:
		with open("{}static/rankings/{}/{}/borischen.json".format(prefix, curr_week, pos), "w") as outfile:
			json.dump(rankings[pos], outfile, indent=4)

def write_cron_borischen_rankings_ui(curr_week):
	# write pure html and save
	for pos in ["wide-receiver", "running-back", "quarterback", "tight-end"]:
		short_pos = get_short_pos(pos)
		extra = "-rankings" if short_pos in ["rb", "te", "qb"] else ""
		if short_pos == "qb":
			url = "www.borischen.co/p/{}-tier{}.html".format(pos, extra)
		else:
			url = "www.borischen.co/p/half-05-5-ppr-{}-tier{}.html".format(pos, extra)
		call(["curl", "-k", url, "-o", "{}/data/{}/tiers.html".format(borischen_prefix, short_pos)])

	# read s3-aws links for img and object and dump contents into fantasy/
	for pos in ["wide-receiver", "running-back", "quarterback", "tight-end"]:
		short_pos = get_short_pos(pos)
		soup = BS(open("{}/data/{}/tiers.html".format(borischen_prefix, short_pos)).read(), "lxml")
		img = soup.find("img").get("src")
		obj = soup.find("object").get("data")

		call(["curl", "-k", img, "-o", "{}static/borischen/{}.png".format(prefix, short_pos)])
		call(["curl", "-k", obj, "-o", "{}static/borischen/{}.tiers".format(prefix, short_pos)])
	
	# read tiers and convert to json
	tiers_json = {}
	for pos in ["wide-receiver", "running-back", "quarterback", "tight-end"]:
		short_pos = get_short_pos(pos)
		tiers_json[short_pos] = {}
		tiers = open("{}static/borischen/{}.tiers".format(prefix, short_pos)).readlines()
		for line in tiers:
			m = re.match(r"Tier (\d+):", line)
			tier = m.group(1) if m else 0
			tiers_json[short_pos][tier] = line.rstrip().split(": ")[1].split(", ")
		with open("{}static/borischen/{}_tiers.json".format(prefix, short_pos), "w") as fh:
			json.dump(tiers_json[short_pos], fh, indent=4)


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
		print("WRITING BORISCHEN STATS")
		#write_cron_borischen_rankings(curr_week)
		write_cron_borischen_rankings_ui(curr_week)
	else:
		read_borischen_rankings(curr_week)
