"""
Cover art finder module.  Based on a progressive approach to find the art:
    1. In the folder containing the track
    2. Embedded in the the flac file itself
    3. At a url
    4. In the folder at a url
    5. Look up on last FM (description https://www.last.fm/api/intro)

      mDisplay

    baloothebear4    16/12/19

"""


import requests
import json

class urlget():

    API_URL         = "http://ws.audioscrobbler.com/2.0/"
    API_KEY 	    = "47eb439e80abf97e63a310c45a9715d8"
    API_SECRET      = "2e16ec261cd1b624e5a0f69f7c85e076"
    USERNAME        = "baloothebear4"
    PASSWORD        = "ravenscroft"

    def __init__(self):
        pass

    def get(self, url, payload):
        headers = {'user-agent': 'dataquest'}

        payload['format'] = 'json'
        print("get")
        response = requests.get(url) #, headers=headers, params=payload)
        return response

    def check(self, url):
        # payload = {'artist':artist, 'album':album, 'autocorrect':1 } # fixes misspelt artists
        payload = {}

        return self.get(url, payload)

    # def find_album_art(self, artist, album):
    #     try:
    #         r = self.find_album(artist, album)
    #         coverart_url = r.json()['album']['image'][5]['#text']
    #         if not validators.url(coverart_url): raise
    #         return coverart_url
    #     except:
    #         print ("lastFMAPI : find_album_art >> Cover art not found")
    #         lastFM.jprint(r.json())
    #         return False

    def jprint(self,obj):
        # create a formatted string of the Python JSON object
        text = json.dumps(obj, sort_keys=True, indent=4)
        print(text)




if __name__=="__main__":
	# r = requests.get('https://api.github.com/events')
	# print(r.status_code)

	u = urlget()
	URL = ['http://94.23.222.12:8027/amysfmspiritofsoul', 'http://5.152.208.98:8058']

	for url in URL:
		print("Check url ", url)
		r = requests.get(URL,timeout=5)
		print(r.status_code)
		# r=u.get(url,{})
		# u.jprint(r.json())
		#
	    # print(lastFM.find_album_art("jean michel jarre", "zoolook"))
	    # print(lastFM.find_album_art("carl orff", "carmina burana"))
