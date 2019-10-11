
from subprocess import call
import sys

# GLOBALS



# POST 1 is redzone %
def post1(curr_week):
	print("Players with highest percentage of Team Redzone Looks")
	print("A Redzone look is a target or rushing attempt within the opponents 20 yard line.")
	print("\nReply with a team if you want to see their WR breakdown")

	call(["python", "controllers/redzone.py", "-s", str(curr_week)])

# POST 2 is redzone % by team
def post2(curr_week):
	print("Teams Sorted By Redzone Looks")
	print("A Redzone look is a target or rushing attempt within the opponents 20 yard line.")

	call(["python", "controllers/redzone.py", "-t", "-s", str(curr_week)])	

# POST 3 is my extension
def post3(curr_week):
	print("[Chrome Extension] Reddit Adjusted Trade Value Calculator link=https://chrome.google.com/webstore/detail/trade-value-calculator/menkeeamkaboflpmlachemgcdgemjadh")
	print("Data from /u/PeakedInHighSkool [post]() \n")
	print("Almost 4000 users using the extension, thanks /r/ff. Good luck with the playoff runs / sacko bowls\n")
	print("So in the latest version 0.0.2.0, two big things\n")
	print("- #Works for NFL.com owners\n")
	print("- #Display to show when data was last updated\n")


def defensive_post(curr_week):
	print("ctrl+f for easy look at team")




if __name__ == '__main__':
	curr_week = 4

	if len(sys.argv) > 1:
		if int(sys.argv[1]) == 1:
			post1(curr_week)
		elif int(sys.argv[1]) == 2:
			post2(curr_week)
		if int(sys.argv[1]) == 3:
			post3(curr_week)
	else:
		post1(curr_week)
		post2(curr_week)
		post3(curr_week)
