import requests

login = {
	
}

#url = "https://football.fantasysports.yahoo.com/f1/1000110/players"

with requests.Session() as session:
	page = session.post("https://login.yahoo.com", data={"username": "zhecht7"})
	#print(page.text)
	cookies = dict(page.cookies)
	page = session.post("https://login.yahoo.com", data={"username": "zhecht7", "passwd": ""}, cookies=cookies)
	print(page.text)