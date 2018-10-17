import operator
from pprint import *


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


csv = open("static/airyards.csv")

indexes = {
	"targets": 0,
	"tgt_share": 0,
	"adot": 0,
	"air_yards": 0,
	"yac": 0,
	#"ppr": 0
	#"wopr": 0
}

stats_arr = []
for idx, line in enumerate(csv):
	split_line = line.split(",")
	if idx == 0:
		for key in indexes:
			if key == "ppr":
				indexes[key] = -1
			else:
				indexes[key] = split_line.index("\"{}\"".format(key))
		continue

	arr = {}
	arr["full_name"] = fix_name(split_line[1][1:-1].lower().replace("'", ""))
	arr["team"] = split_line[3][1:-1]
	arr["air_yards_per_target"] = round(float(split_line[indexes["air_yards"]]) / float(split_line[indexes["targets"]]), 2)
	for key in indexes:
		arr[key] = float(split_line[indexes[key]])
	stats_arr.append(arr)

	if idx >= 75:
		break

#pprint(stats_arr[:10])
# Print sorted players
for stat in ["adot", "air_yards"]:
	sorted_stats_arr = sorted(stats_arr, key=operator.itemgetter(stat), reverse=True)
	print("\nPlayer|{}".format(stat.upper()))
	print(":--|:--")
	for arr in sorted_stats_arr[:20]:
		#print("{}|{}".format(arr["full_name"].title(), arr[stat]))
		pass

"""
#######################################################################
# Split by team and then sort

teams = {}
for arr in stats_arr:
	if arr["team"] not in teams:
		teams[arr["team"]] = {"air_yards": 0, "adot": 0, "targets": 0, "yac": 0}

	for stat in indexes:
		teams[arr["team"]][stat] += arr[stat]

for team in teams:
	#print("{} {}".format(team, teams[team]))
	pass

sorted_teams = sorted(teams.items(), key=lambda kv: kv[1]["targets"], reverse=True)
for team, json in sorted_teams:
	#print(team, json["targets"])
	pass

#######################################################################
"""
for rank in range(4):
	print("#WR{} Players".format(rank + 1))
	totals = {"names": []}
	for i in range(12):
		totals["names"].append(stats_arr[(rank * 12) + i]["full_name"].title())
	print("\n-{}\n".format(', '.join(totals["names"])))

print(" |{}".format('|'.join(sorted(indexes.keys()))))
print(":--|{}".format('|'.join([":--"]*len(indexes.keys()))))
for rank in range(4):
	#print("WR{}".format(rank + 1))
	totals = {}
	for i in range(12):
		for key in sorted(indexes):
			try:
				totals[key] += stats_arr[(rank * 12) + i][key]
			except:
				totals[key] = stats_arr[(rank * 12) + i][key]
	col = []
	for key in sorted(indexes):
		#totals[key] = round(totals[key] / 12.0, 2)
		col.append(str(round(totals[key] / 12.0, 2)))
		#print("\t{}: {}".format(key, round(totals[key] / 12.0, 2)))
	print("**WR{}**|{}".format(rank + 1, '|'.join(col)))
		






