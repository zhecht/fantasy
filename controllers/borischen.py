import argparse
import json
from subprocess import call

try:
	from controllers.read_rosters import *
except:
	from read_rosters import *

def merge_two_dicts(x, y):
	z = x.copy()
	z.update(y)
	return z

def fix_name(name):
	if name == "todd gurley":
		return "todd gurley ii"
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
	return name

def read_borischen_rankings(curr_week=1):
	rankings = {}
	for position in ["qb", "rb", "wr", "te"]:
		rankings[position] = {}
		with open("static/rankings/{}/{}/borischen.json".format(curr_week, position)) as fh:
			rankings[position] = json.loads(fh.read())
	return rankings

def read_github_borischen_rankings(curr_week=1):
	rankings = {}
	players_on_teams, name_translations = read_rosters()
	players_on_FA = read_FA()
	players_on_teams = merge_two_dicts(players_on_teams, players_on_FA)

	for pos in ["qb", "rb", "wr", "te"]:
		rankings[pos] = {}
		f = open("/Users/hechtor/Documents/projects/fftiers/data/{}/w{}.csv".format(pos, curr_week), "r")
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


def write_cron_borischen_rankings(curr_week=1):
	for pos in ["qb", "rb", "wr", "te"]:
		call(["python", "/Users/hechtor/Documents/projects/fftiers/src/fp_api.py", "-j", "/Users/hechtor/Documents/projects/fftiers/data/{}/w{}.json".format(pos, curr_week), "-c", "/Users/hechtor/Documents/projects/fftiers/data/{}/w{}.csv".format(pos,curr_week), "-y", "2018", "-p", pos, "-w", str(curr_week), "-s", "HALF"])

	rankings = read_github_borischen_rankings(curr_week)
	for pos in ["qb", "rb", "wr", "te"]:

		with open("static/rankings/{}/{}/borischen.json".format(curr_week, pos), "w") as outfile:
			json.dump(rankings[pos], outfile, indent=4)
	



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
		write_cron_borischen_rankings(curr_week)
	else:
		read_borischen_rankings(curr_week)
