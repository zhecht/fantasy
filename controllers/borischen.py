import argparse
import json
from subprocess import call

def read_borischen_rankings(curr_week=1):
	rankings = {}
	for position in ["qb", "rb", "wr", "te"]:
		rankings[position] = {}
		with open("static/rankings/{}/{}/borischen.json".format(curr_week, position)) as fh:
			rankings[position] = json.loads(fh.read())
	return rankings

def read_github_borischen_rankings(curr_week=1):
	rankings = {}

	for pos in ["qb", "rb", "wr", "te"]:
		rankings[pos] = {}
		f = open("/Users/hechtor/Documents/projects/fftiers/data/{}/w{}.csv".format(pos, curr_week), "r")
		idx = 0

		for line in f:
			if idx != 0:
				split_line = line.split(",")
				rankings[pos][split_line[1].lower().replace("'", "")] = int(split_line[0])
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
