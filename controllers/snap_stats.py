from bs4 import BeautifulSoup
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
	return name

if __name__ == '__main__':
	teamnum = 0
	print("WRITING SNAPS")
	file = open('static/snap_counts.txt', 'w')
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
				for week in range(1,17):
					try:
						perc = int(tds[week].find('br').next_sibling[:-1])
					except:
						perc = 0
					snap_counts.append(perc)

				team = link.split('-')[1]
				snap_counts = ','.join(str(x) for x in snap_counts)

				file.write("{}\t{}\n".format(full_name,snap_counts))
				#pid = getPlayerID(full, constants.SNAP_TEAMS[teamnum])

				#if pid != None:
				#  pid = pid[0]
				#  updateSnaps(pid,snap_counts)

		teamnum += 1
					
					

			



