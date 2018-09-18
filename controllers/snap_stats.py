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
	elif name == "ben watson":
		return "benjamin watson"
	elif name == "allen robinson":
		return "allen robinson ii"
	elif name == "todd gurley":
		return "todd gurley ii"
	elif name == "marvin jones jr":
		return "marvin jones jr."
	return name


def read_snap_stats():
	with open("static/snap_counts.json") as fh:
		returned_json = json.loads(fh.read())
	new_json = {}
	for player in returned_json:
		real_name = " ".join(player.split(" ")[:-1])
		new_json[real_name] = {"perc": returned_json[player]["perc"], "counts": returned_json[player]["counts"]}
	#for player in new_json:
	return new_json

if __name__ == '__main__':
	teamnum = 0
	print("WRITING SNAPS")
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
				#file.write("{}\t{}\n".format(full_name,snap_counts))
				#pid = getPlayerID(full, constants.SNAP_TEAMS[teamnum])

				#if pid != None:
				#  pid = pid[0]
				#  updateSnaps(pid,snap_counts)
		teamnum += 1

	with open("static/snap_counts.json", "w") as outfile:
		json.dump(j, outfile, indent=4)
					
					

			



