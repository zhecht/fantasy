from bs4 import BeautifulSoup
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

def write_reception_stats():
	base_url = "http://subscribers.footballguys.com/teams/"
	j = {}
	for link in constants.SNAP_LINKS:
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


def write_snap_stats():
	j = {}
	for link in constants.SNAP_LINKS:
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


if __name__ == '__main__':
	print("WRITING SNAPS")
	write_snap_stats()
	write_reception_stats()