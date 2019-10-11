import argparse
import operator
import json
from pprint import *
from sys import platform

prefix = ""
if platform != "darwin":
	# if on linux aka prod
	prefix = "/home/zhecht/fantasy/"

def fix_name(name):
	name = name.lower().replace("'", "")
	# Skip Cols
	if name in ["", "\n"] or name[0] == '-':
		return ""
	try:
		# If number, return empty
		name = float(name)
		return ""
	except:
		pass
		
	if name.find("(") != -1:
		name = name.split(" ")[0]
	elif name == "todd gurley":
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

indexes = {
	"targets": 0,
	"rec": 0,
	"tgt_share": 0,
	"adot": 0,
	"air_yards": 0,
	"yac": 0,
	"td": 0,
	"ppr": 0,
	"wopr": 0
}

def write_airyards(curr_week):
	stats, stats_arr = get_airyards()
	with open("{}static/airyards/airyards_wk{}.json".format(prefix, curr_week), "w") as fh:
		json.dump(stats, fh, indent=4)

def read_airyards(curr_week):
	with open("{}static/airyards/airyards_wk{}.json".format(prefix, curr_week)) as fh:
		j = json.loads(fh.read())
	return j

def read_airyards_trends(curr_week):
	with open("{}static/airyards/airyards_wk{}.json".format(prefix, curr_week - 1)) as fh:
		last_airyards = json.loads(fh.read())
	with open("{}static/airyards/airyards_wk{}.json".format(prefix, curr_week)) as fh:
		curr_airyards = json.loads(fh.read())
	airyards_trends = {}
	for player in curr_airyards:
		airyards_trends[player] = curr_airyards[player].copy()
		for stat in ["rec", "targets", "tgt_share", "yac", "td", "adot", "air_yards", "wopr"]:
			curr_stat = curr_airyards[player][stat]
			try:		
				last_stat = last_airyards[player][stat]
			except:
				last_stat = 0
			delta = round(curr_stat - last_stat, 2)
			if stat not in ["tgt_share", "wopr"]:
				curr_stat = int(curr_stat)
				delta = int(delta)
			delta = "+{}".format(delta) if delta > 0 else "{}".format(delta)			
			airyards_trends[player][stat] = "{} ({})".format(curr_stat, delta)
	return airyards_trends

def get_airyards():
	csv = open("{}static/airyards/airyards.csv".format(prefix))
	stats_arr = []
	stats = {}
	for idx, line in enumerate(csv):
		split_line = line.split(",")
		if idx == 0:
			for key in indexes:
				indexes[key] = -1 if key == "ppr" else split_line.index("\"{}\"".format(key))
			continue

		arr = {
			"full_name": fix_name(split_line[1][1:-1]).replace(".", ""),
			"pos": split_line[2][1:-1],
			"team": split_line[3][1:-1]
		}
		for key in indexes:
			if split_line[indexes[key]] == "NA":
				arr[key] = 0
			else:
				arr[key] = float(split_line[indexes[key]])
		stats_arr.append(arr)
		stats[arr["full_name"]] = arr
	return stats, stats_arr


def print_sorted():
	# Print sorted players
	for stat in ["adot", "air_yards"]:
		sorted_stats_arr = sorted(stats_arr, key=operator.itemgetter(stat), reverse=True)
		print("\nPlayer|{}".format(stat.upper()))
		print(":--|:--")
		printed = 0
		for arr in sorted_stats_arr:
			if printed == 20:
				break
			if arr["rec"] > 5:
				print("{}|{}".format(arr["full_name"].title(), arr[stat]))
				printed += 1

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", help="Do Cron job", action="store_true")
	parser.add_argument("-t", "--trends", help="Sort with trends", action="store_true")
	parser.add_argument("-p", "--pretty", help="Pretty Print", action="store_true")
	parser.add_argument("-s", "--start", help="Start Week", type=int)
	parser.add_argument("-e", "--end", help="End Week", type=int)

	args = parser.parse_args()
	
	if args.pretty:
		print_sorted()
		exit()

	curr_week = 3
	if args.start:
		curr_week = args.start

	if args.cron:
		write_airyards(curr_week)


