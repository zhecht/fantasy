

from yahoo_oauth import OAuth2


class MyOAuth:
  oauth = None
  league_key = "nfl.l.468862"
  def __init__(self):
    self.oauth = OAuth2(None,None,from_file='controllers/oauth2.json')

    if not self.oauth.token_is_valid():
      self.oauth.refresh_access_token()

  def getData(self,url):
    return self.oauth.session.get(url)
  def postData(self,url,payload={}):
  	return self.oauth.session.post(url,payload)
