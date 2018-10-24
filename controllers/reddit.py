
from subprocess import call
import sys


# POST 1 is redzone %
def post1(curr_week):
	print("[Top 40] Players with highest percentage of team's total Redzone looks")
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
	print("As most of you already know, /u/PeakedInHighSkool does the Reddit Adjusted Trade Value post, one of my favorite posts on the sub.\n")
	print("I soon realized how much I loved to have a trade reference other than Yahoo's Evaluator. Being pretty well-versed in JavaScript, I decided to create an extension that uses the trade values to help make fair or unfair deals.\n")

	print("&nbsp;\n")

	print("#How To Use\n")
	print("- Right now, the extension **ONLY** works with Yahoo leagues. Other sites coming in the future")
	print("- What it looks like: [Image](https://i.imgur.com/PXnnRC9.png) [Video](https://youtu.be/RvbbNW9hbsY)")
	print("- On any trade page, my extension will be enabled. When you click on it, a table with players from both teams and their values will appear along with a team total")
	print("- Click a player in the table to highlight them and add their trade value to the total")
	print("- Highlighted players are colored in green. The team with a greater total trade value will also be highlighted green")
	print("- Full teams are shown on the initial propose trade page. Evaluate and already offered trades will only select the involved players. *My extension can only see what the current page sees*")

	print("\n#Code - Skip if uninterested\n")
	print("- If you want the .zip file, PM me for a link and then you can adjust the extension to your liking")
	print("- All the extension does is scrape your webpage for a list of players and sends the names to my website zhecht.pythonanywhere.com/extension using a GET request. My site sends the list of players back with their trade values")
	print("- Then I use JavaScript to parse the results and form the trade table")





if __name__ == '__main__':
	curr_week = 7

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