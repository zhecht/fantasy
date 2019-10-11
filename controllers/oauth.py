

from yahoo_oauth import OAuth2


class MyOAuth:
  oauth = None
  league_key = "nfl.l.468862"
  from_file = 'controllers/oauth2.json'
  def __init__(self, is_merrick=False):
    if is_merrick:
      self.league_key = "nfl.l.276544"
      self.from_file = 'controllers/oauth_merrick.json'
    self.oauth = OAuth2(None,None,from_file=self.from_file)

    if not self.oauth.token_is_valid():
      self.oauth.refresh_access_token()

  def getData(self,url):
    return self.oauth.session.get(url)
  def postData(self,url,payload={}):
  	return self.oauth.session.post(url,payload)
