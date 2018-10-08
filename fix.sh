sed -i 's/from dateutil/#from dateutil/g' controllers/news.py
sed -i 's/from ghost/#from ghost/g' controllers/*.py
sed -i 's/static/\/home\/zhecht\/fantasy\/static/g' controllers/*.py
sed -i 's/static/\/static/g' views/*.html
sed -i 's/from yahoo_oauth/#from yahoo_oauth/g' controllers/oauth.py
