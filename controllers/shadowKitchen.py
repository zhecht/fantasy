

from subprocess import call
from bs4 import BeautifulSoup as BS

def downloadHomePage():

	url = "https://www.ubereats.com/api/getFeedV1"

	cacheKey = "JTdCJTIyYWRkcmVzcyUyMiUzQSUyMjI3MTUlMjBMb29rb3V0JTIwQ2lyJTIyJTJDJTIycmVmZXJlbmNlJTIyJTNBJTIyOGFiM2YyZWQtMTI0Ny05YzUyLWNmZTQtNGUwN2NlMTBhNGIyJTIyJTJDJTIycmVmZXJlbmNlVHlwZSUyMiUzQSUyMnViZXJfcGxhY2VzJTIyJTJDJTIybGF0aXR1ZGUlMjIlM0E0Mi4yNDgwMjclMkMlMjJsb25naXR1ZGUlMjIlM0EtODMuNzAxMjMyJTdE/DELIVERY///0/0//JTVCJTVE///////HOME///////"
	call(["curl", "-k", url, "-H", f'cacheKey: {cacheKey}', "-o", "out.html"])

def readHomePageHTML():

	soup = BS(open("out.html").read(), "lxml")

	l = []
	for a in soup.findAll("a"):
		href = a.get("href")
		if "Delivery Fee" in a.findNext("div").text and href.startswith("/store") and "DELIVERY" in href:
			l.append(href)

	print(len(l))

readHomePageHTML()