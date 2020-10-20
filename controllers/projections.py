
from bs4 import BeautifulSoup as BS
import argparse
import json
import os

def fix_team(team):
	if team == "ari":
		return "crd"
	elif team == "bal":
		return "rav"
	elif team == "hou":
		return "htx"
	elif team == "ind":
		return "clt"
	elif team == "kc":
		return "kan"
	elif team == "lac":
		return "sdg"
	elif team == "la":
		return "ram"
	elif team == "lv":
		return "rai"
	elif team == "ten":
		return "oti"
	elif team == "tb":
		return "tam"
	elif team == "no":
		return "nor"
	elif team == "gb":
		return "gnb"
	elif team == "sf":
		return "sfo"
	elif team == "ne":
		return "nwe"
	return team

def get_team_abbr(name):
	if "falcons" in name:
		return "atl"
	elif "bills" in name:
		return "buf"
	elif "panthers" in name:
		return "car"
	elif "bears" in name:
		return "chi"
	elif "bengals" in name:
		return "cin"
	elif "browns" in name:
		return "cle"
	elif "colts" in name:
		return "clt"
	elif "cardinals" in name:
		return "crd"
	elif "cowboys" in name:
		return "dal"
	elif "broncos" in name:
		return "den"
	elif "lions" in name:
		return "det"
	elif "packers" in name:
		return "gnb"
	elif "texans" in name:
		return "htx"
	elif "jag" in name:
		return "jax"
	elif "chiefs" in name:
		return "kan"
	elif "dolphins" in name:
		return "mia"
	elif "vikings" in name:
		return "min"
	elif "saints" in name:
		return "nor"
	elif "patriots" in name:
		return "nwe"
	elif "giants" in name:
		return "nyg"
	elif "jets" in name:
		return "nyj"
	elif "titans" in name:
		return "oti"
	elif "eagles" in name:
		return "phi"
	elif "steelers" in name:
		return "pit"
	elif "raiders" in name:
		return "rai"
	elif "rams" in name:
		return "ram"
	elif "ravens" in name:
		return "rav"
	elif "chargers" in name:
		return "sdg"
	elif "seahawks" in name:
		return "sea"
	elif "san fran" in name:
		return "sfo"
	elif "bucc" in name:
		return "tam"
	elif "washington" in name:
		return "was"

def fix_name(name, team, stats):
	if name == "bisi johnson":
		return "olabisi johnson"
	elif name == "ronald jones":
		return "ronald jones ii"
	elif name == "gardner minshew":
		return "gardner minshew ii"
	elif name == "mike badgley":
		return "michael badgley"
	elif name == "jon brown":
		return "jonathan brown"
	elif team == "off":
		return get_team_abbr(name)
	elif name+" jr" in stats[team]:
		name += " jr"
	return name

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
	prefix = "/home/zhecht/fantasy/"

def write_projections(week, stats, force=False):
	url = f"https://fantasy.nfl.com/research/projections?position=O&sort=projectedPts&statCategory=projectedStats&statSeason=2020&statType=weekProjectedStats&statWeek={week}&offset=0"
	projections = {}
	offsets = {"O": 1026, "7": 54, "8": 32}
	for pos in ["O", "7", "8"]: # offense / kicker / dst
		if pos == "7":
			url = url.replace("position=O", f"position={pos}")
		elif pos == "8":
			url = url.replace("position=7", f"position={pos}")
		offset = 1
		while offset < offsets[pos]:
			path = f"static/projections/{week}/projections{pos}_{offset}_{offset+25}.html"
			if not os.path.exists(path) or force:
				url = url.split("offset=")[0]+f"offset={offset}"
				os.system(f"curl -k \"{url}\" -o {path}")
			with open(path) as fh:
				soup = BS(fh.read(), "lxml")
			offset += 25
			headers = []
			for idx, row in enumerate(soup.find("thead").find_all("tr")):
				for header_idx, th in enumerate(row.find_all("th")):
					val = th.text.strip().lower()
					if idx == 0:
						headers.append(val)
					else:
						headers[header_idx] += "_"+val
					if th.get("colspan"):
						for j in range(0, int(th.get("colspan")) - 1):
							if idx == 0:
								headers.append(val)
							else:
								headers[header_idx] += "_"+val
			for row in soup.find("tbody").find_all("tr"):
				name = row.find("a").text.strip().lower().replace("'", "").replace(".", "")
				sp = row.find("a").findNext("em").text.split(" - ")
				if sp[0] == "DEF":
					sp = ["", "OFF"]
				elif len(sp) == 1:
					continue
				team = sp[1].lower()
				team = fix_team(team)
				name = fix_name(name, team, stats)
				if name == "aldrick rosas":
					print(team)
				if team != "off" and name not in stats[team]:
					#print(team, name)
					pass
				projections[name] = {}
				for idx, col in enumerate(row.find_all("td")):
					if headers[idx].split("_")[0]:
						if "." in col.text:
							projections[name][headers[idx]] = float(col.text)
						else:
							projections[name][headers[idx]] = 0
	with open(f"static/projections/{week}/projections.json", "w") as fh:
		json.dump(projections, fh, indent=4)

def get_points(projections):
	if "pat_made" in projections:
		return (projections["pat_made"] * 1) + (projections["fg made_0-19"] * 3) + (projections["fg made_20-29"] * 3) + (projections["fg made_30-39"] * 3) + (projections["fg made_40-49"] * 4) + (projections["fg made_50+"] * 5)
	if "passing_yds" not in projections:
		return 0
	passing_pts = (projections["passing_yds"] / 25.0) + (projections["passing_td"] * 4) + (projections["passing_int"] * -2)
	rushing_pts = (projections["rushing_yds"] / 10.0) + (projections["rushing_td"] * 6)
	receiving_pts = (projections["receiving_rec"] * 0.5) + (projections["receiving_yds"] / 10.0) + (projections["receiving_td"] * 6)
	misc_pts = (projections["misc_2pt"] * 2) + (projections["fum_lost"] * -2)
	return passing_pts + rushing_pts + receiving_pts + misc_pts

def fix_projections(all_projections):
	all_projections["justin herbert"]["wk2"] = 14.92 #tyrod
	if "aldrick rosas" not in all_projections:
		all_projections["aldrick rosas"] = {}
	all_projections["aldrick rosas"]["wk4"] = 1.99 + 0.04*3 + 0.47*3 + 0.69*3 + 0.48*4

def parse_projections():
	all_projections = {}
	for week in os.listdir("static/projections"):
		if "json" in week:
			continue
		with open(f"static/projections/{week}/projections.json") as fh:
			projections = json.load(fh)
		for player in projections:
			if player not in all_projections:
				all_projections[player] = {}
			rec = 0
			if "receiving_rec" in projections[player]:
				rec = projections[player]["receiving_rec"]
			pts = projections[player]["fantasy_points"]
			if not pts:
				pts = get_points(projections[player])
			elif rec:
				pts -= (rec * 0.5)
			all_projections[player]["wk"+week] = round(pts, 2)
	fix_projections(all_projections)
	with open(f"static/projections/projections.json", "w") as fh:
		json.dump(all_projections, fh, indent=4)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-p", "--parse", action="store_true", help="Loop through each week and aggregate")
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-f", "--force", action="store_true")
	parser.add_argument("-w", "--week", help="Week", type=int)
	args = parser.parse_args()

	if args.parse:
		parse_projections()
		exit()

	if not args.week:
		print("need week")
		exit()

	if not os.path.exists(f"static/projections/{args.week}"):
		os.mkdir(f"static/projections/{args.week}")

	stats = {}
	teams = os.listdir("{}static/profootballreference".format(prefix))
	for team in teams:
		if not os.path.exists(f"{prefix}static/profootballreference/{team}/stats.json"):
			continue
		with open(f"{prefix}static/profootballreference/{team}/stats.json") as fh:
			stats[team] = json.load(fh)
	write_projections(args.week, stats, args.force)