from bs4 import BeautifulSoup as BS
#from dateutil.parser import parse


import argparse
import datetime
import read_rosters
import time

try:
	import urllib2 as urllib
except:
	import urllib.request as urllib

default_twitter_handles = [
	"JPFinlayNBCS",
	"AdamSchefter",
	"RapSheet", # Ian Rapoport
	"Rotoworld_FB",
	"ProFootballDoc", # Dr Chao
	"MatthewBerryTMR",
	"JeffJohnsonFI",
	"KCJoynerTFS",
	"SiriusXMFantasy",
	"johnpboyle",
	"caplannfl",
	"MikeReiss",
	"rydunleavy",
	"CourtneyRCronin",
	"zkeefer",
	"MikeTriplett",
	"APMarkLong"
]

def find_potential_names(tweet):
	words = tweet.split(" ")	
	first_name = words[0]
	try:
		first_capitalized = first_name[0].isupper()
	except:
		return []

	names = []
	for i in range(1,len(words)):
		if words[i] and words[i][0].isupper():
			if first_capitalized:
				name = "{} {}".format(first_name, words[i]).lower().replace("'", "")
				names.append(name)
			else:
				first_name = words[i]
				first_capitalized = True
		else:
			first_capitalized = False
	return names

def cron_write_twitter(twitter_handles=default_twitter_handles):
	for handle in twitter_handles:
		url = "https://twitter.com/{}".format(handle)
		urllib.urlretrieve(url, "static/twitter/{}.html".format(handle))
		time.sleep(3)

def read_twitter(players_on_teams, players_on_FA=read_rosters.read_FA(), twitter_handles=default_twitter_handles):
	all_tweets = []

	for handle in twitter_handles:
		soup = BS(open("static/twitter/{}.html".format(handle)).read(), "lxml")
		tweets = soup.find_all("p", class_="tweet-text")
		times = soup.find_all("span", class_="_timestamp")
		
		for tweet, time in zip(tweets, times):
			for name in find_potential_names(tweet.text):
				date = int(time["data-time"])
				print(name)
				if name not in players_on_teams and name not in players_on_FA:
					continue

				all_tweets.append({"name": name, "date": date, "headline": tweet.text})
	return all_tweets


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")

	args = parser.parse_args()

	if args.cron:
		print("WRITING TWITTER")
		cron_write_twitter()
	else:
		players_on_teams, name_translations = read_rosters.read_rosters()
		read_twitter(players_on_teams)
