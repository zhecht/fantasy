import re

YEAR = 2021
CURR_WEEK = 1
curr_week = CURR_WEEK

TEAM_TRANS = {
	"rav": "bal",
	"htx": "hou",
	"oti": "ten",
	"sdg": "lac",
	"ram": "lar",
	"clt": "ind",
	"crd": "ari",
	"gnb": "gb",
	"kan": "kc",
	"nwe": "ne",
	"rai": "lv",
	"sfo": "sf",
	"tam": "tb",
	"nor": "no"
}

SORTED_TEAMS = ['ari', 'atl', 'bal', 'buf', 'car', 'chi', 'cin', 'cle', 'dal', 'den', 'det', 'gnb', 'hou', 'ind', 'jax', 'kan', 'lac', 'lar', 'rai', 'mia', 'min', 'nor', 'nwe', 'nyg', 'nyj', 'phi', 'pit', 'sea', 'sfo', 'tam', 'ten', 'was']

afc_teams = ['rav', 'buf', 'cin', 'cle', 'den', 'htx', 'clt', 'jax', 'kan', 'sdg', 'rai', 'mia', 'nwe', 'nyj', 'pit', 'ten']
nfc_teams = ['crd', 'atl', 'car', 'chi', 'dal', 'det', 'gnb', 'ram', 'min', 'nor', 'nyg', 'phi', 'sea', 'sfo', 'tam', 'was']

RBBC_TEAMS = ['crd', 'atl', 'rav', 'buf', 'car', 'chi', 'cin', 'cle', 'dal', 'den', 'det', 'gnb', 'htx', 'clt', 'jax', 'kan', 'sdg', 'ram', 'rai', 'mia', 'min', 'nor', 'nwe', 'nyg', 'nyj', 'phi', 'pit', 'sea', 'sfo', 'tam', 'oti', 'was']

def fixName(name):
	name = name.lower().replace("'", "")
	name = re.sub(r" (v|iv|iii|ii|jr|sr)(\.?)$", " ", name).replace(".", "").strip()
	if name == "elijah mitchell":
		return "eli mitchell"
	elif name == "off":
		return "OFF"
	elif name == "def":
		return "DEF"
	return name