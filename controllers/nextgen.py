import argparse
import operator
import json
from bs4 import BeautifulSoup as BS
from sys import platform

prefix = ""
if platform != "darwin":
	# if on linux aka prod
	prefix = "/home/zhecht/fantasy"

def merge_two_dicts(x, y):
	z = x.copy()
	z.update(y)
	return z

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

def write_nextgen(curr_week):
	for which in ["receiving", "rushing"]:
		soup = BS(open("{}static/nextgen/{}.html".format(prefix, which)).read(), "lxml")
		headers = soup.find("table", class_="el-table__header").find_all("th")
		indexes = {}
		for idx, th in enumerate(headers):
			txt = th.text
			if th.find("div", class_="tooltip-column"):
				txt = th.find("span").find("span").text
			indexes[idx] = txt.lower()
		stats = {}
		rows = soup.find_all("tr", class_="el-table__row")
		for tr in rows:
			data = tr.find_all("td")
			name = fix_name(data[0].text).replace(".", "")
			stats[name] = {}
			idx = 1
			for td in data[1:]:
				stats[name][indexes[idx]] = td.text
				idx += 1
			if "pos" not in stats[name]:
				stats[name]["pos"] = "RB"
		with open("{}static/nextgen/{}_wk{}.json".format(prefix, which, curr_week), "w") as fh:
			json.dump(stats, fh, indent=4)

def read_nextgen(curr_week):
	j = {}
	for which in ["receiving", "rushing"]:
		with open("static/nextgen/{}_wk{}.json".format(which, curr_week)) as fh:
			returned = json.loads(fh.read())
		j = merge_two_dicts(j, returned)
	return j

def read_nextgen_trends(curr_week):
	last_nextgen = read_nextgen(curr_week - 1)
	curr_nextgen = read_nextgen(curr_week)
	
	receiving_headers = ["cush", "sep", "tay", "tay%", "ctch%"]
	rushing_headers = ["eff", "8+d%", "tlos", "avg"]
	nextgen_trends = {}
	for player in curr_nextgen:
		nextgen_trends[player] = curr_nextgen[player].copy()
		headers = receiving_headers if curr_nextgen[player]["pos"] in ["WR", "TE"] else rushing_headers
		for stat in headers:
			try:
				curr_stat = float(curr_nextgen[player][stat])
				last_stat = float(last_nextgen[player][stat])
			except:
				curr_stat = 0
				last_stat = 0
			delta = round(curr_stat - last_stat, 2)
			delta = "+{}".format(delta) if delta > 0 else "{}".format(delta)
			nextgen_trends[player][stat] = "{} ({})".format(curr_stat, delta)
	return nextgen_trends

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", help="Do Cron job", action="store_true")
	parser.add_argument("-t", "--trends", help="Sort with trends", action="store_true")
	parser.add_argument("-p", "--pretty", help="Pretty Print", action="store_true")
	parser.add_argument("-s", "--start", help="Start Week", type=int)
	parser.add_argument("-e", "--end", help="End Week", type=int)

	args = parser.parse_args()
	
	curr_week = 3
	if args.start:
		curr_week = args.start

	if args.cron:
		write_nextgen(curr_week)


