"""
!/usr/bin/env python3

Consumer Key	lJpmsEmHWqIzcAdycZce
Consumer Secret	eCMLxzYHJxSayoILBAejEpTQzrggNRRK
Request Token URL	https://api.discogs.com/oauth/request_token
Authorize URL	https://www.discogs.com/oauth/authorize
Access Token URL	https://api.discogs.com/oauth/access_token
"""

import musicbrainzngs
from fuzzywuzzy import fuzz


class Musicbrainz():
    def __init__(self):
        musicbrainzngs.set_useragent(
            "python-musicbrainzngs-example",
            "0.1",
            "https://github.com/alastair/python-musicbrainzngs/",
        )
        musicbrainzngs.auth('baloothebear4', 'meWzuh-katfyn-6qadqu')



    def coverart_exists(self, release_id):
        try:
            # print(("look art at ID", release_id)
            data = musicbrainzngs.get_image_list(release_id)
            print(data, '\n')
            for image in data["images"]:
                if "Front" in image["types"] and image["approved"]:
                    print( "%s is an approved front image!" % image["thumbnails"]["large"])
                    return True
            return False
        except Exception as e:
            print( "Musicbrainz: coverart_exists: failed ",e)
            return False

    def find_art(self, artist, album):
        print("Musicbrainz: find_art:", artist, album)
        """ Search for the album and then identify the best match
            Algorithm for chosing the right album:
            put the search results into a table, search and sort the table accordingly
            1. Highest ex-score, highest fuzzy match of album and artist -weighted towards the alnum
            2. Best match on Artist name
            3. Best match on Album
            4. Album type could be used but some will be compilations??  """
        ALBUM_MATCH_WEIGHT = 1.5
        d = musicbrainzngs.search_release_groups(artist + ' ' + album)

        albums = []
        for k in d['release-group-list']:
            a={}

            if 'id' in k and 'title' and 'artist-credit' and 'ext:score':
                print("Musicbrainz: find_art: looking for", k['title'])
                if self.coverart_exists(k['id']):
                    a['id']     = k['id']
                else:
                    continue
                a['score']  = int(k['ext:score'])
                a['title']  = k['title']
                a['match']  = ALBUM_MATCH_WEIGHT*fuzz.token_sort_ratio(a['title'], album) + a['score']


            for n in k['artist-credit']:
                if 'name' in n:
                    a['name']    = n['name']
                    a['match']  += fuzz.token_sort_ratio(a['name'], artist)

            print(a)
            albums.append(a)

        best_match = 0
        best_id    = ''
        for a in albums:
            if a['match'] > best_match:
                best_id = a['id']

        if best_match > 200:
            imagebin = musicbrainzngs.get_image_front(best_id)
            print("Image successfully found, match score was", best_match)
            return imagebin
        else:
            return None

    def print_search(self, d):
        albums = []
        for k in d['release-group-list']:
            e=''
            a={}
            if 'id'                 in k:
                e+=" id %s" % k['id']
                a['id']= k['id']
            if 'ext:score'          in k:
                e+=" ext:score %s" % k['ext:score']
                a['score']=int(k['ext:score'])
            if 'primary-type'       in k: e+=" primary-type %s" % k['primary-type']
            if 'status'             in k: e+=" status %s" % k['status']
            if 'type'               in k: e+=" type %s" % k['type']
            if 'title'              in k:
                e+=" title %s" % k['title']
                a['title'] = k['title']

    # print(type(k['artist-credit']), k['artist-credit'][0])
            name = ''
            for n in k['artist-credit'][0]:
                if 'name' in n:
                    e+=" name %s"  % k['artist-credit'][0][n]
                    a['name'] = k['artist-credit'][0][n]

            # print("\nid %s, ext:score %d, title %s, name %s, \ndata:%s " % (id, score, title, name, e) )

# This illustrates the call-flow required to complete an OAuth request
# against the discogs.com API. The script will download and save a single
# image from the discogs.com API as an example.
# See README.md for further documentation.
#


import sys

import discogs_client
from discogs_client.exceptions import HTTPError

# Your consumer key and consumer secret generated by discogs when an application is created
# and registered . See http://www.discogs.com/settings/developers . These credentials
# are assigned by application and remain static for the lifetime of your discogs application.
# the consumer details below were generated for the 'discogs-oauth-example' application.
# consumer_key    = 'lJpmsEmHWqIzcAdycZce'
# consumer_secret = 'eCMLxzYHJxSayoILBAejEpTQzrggNRRK'


# The following oauth end-points are defined by discogs.com staff. These static endpoints
# are called at various stages of oauth handshaking.
request_token_url = 'https://api.discogs.com/oauth/request_token'
authorize_url     = 'https://www.discogs.com/oauth/authorize'
access_token_url  = 'https://api.discogs.com/oauth/access_token'

# A user-agent is required with Discogs API requests. Be sure to make your user-agent
# unique, or you may get a bad response.
user_agent       = 'mDisplay'

# Your consumer key and consumer secret generated and provided by Discogs.
# See http://www.discogs.com/settings/developers . These credentials
# are assigned by application and remain static for the lifetime of your discogs
# application. the consumer details below were generated for the
# 'discogs-oauth-example' application.
# NOTE: these keys are typically kept SECRET. I have requested these for
# demonstration purposes.

consumer_key    = 'JJCOegYnRLCLRejtcZbo'
consumer_secret = 'UFlGrCViqSkoBNfRTGZyUfmpTGNbFbMM'
consumer_token  = 'jcBQQnBoXKZGLaCcmRYUmCOtpuyyiNVmGZoubGef'

# A user-agent is required with Discogs API requests. Be sure to make your
# user-agent unique, or you may get a bad response.


class Discogs():
    def __init__(self):
        self.discogsclient = discogs_client.Client(user_agent, user_token=consumer_token)
        # fetch the identity object for the current logged in user.
        user = self.discogsclient.identity()

        print()
        print( ' == User ==')
        print( '    * username           = {0}'.format(user.username))



    def OAuth(self):
        # prepare the client with our API consumer data.
        discogsclient.set_consumer_key(consumer_key, consumer_secret)
        token, secret, url = discogsclient.get_authorize_url()

        print( ' == Request Token == ')
        print( '    * oauth_token        = {0}'.format(token))
        print( '    * oauth_token_secret = {0}'.format(secret))
        print()

        accepted = 'n'
        while accepted.lower() == 'n':
            print()
            accepted = input('Have you authorized me at {0} [y/n] :'.format(url))


        # # Waiting for user input. Here they must enter the verifier key that was
        # # provided at the unqiue URL generated above.
        oauth_verifier = input('Verification code :')#, 'utf8')
        #
        try:
            self.access_token, self.access_secret = discogsclient.get_access_token(oauth_verifier)
        except HTTPError:
            print( 'Unable to authenticate.')
            sys.exit(1)

# fetch the identity object for the current logged in user.
        user = discogsclient.identity()

        print()
        print( ' == User ==')
        print( '    * username           = {0}'.format(user.username))
        print( '    * name               = {0}'.format(user.name))
        print( ' == Access Token ==')
        print( '    * oauth_token        = {0}'.format(access_token))
        print( '    * oauth_token_secret = {0}'.format(access_secret))
        print( ' Authentication complete. Future requests will be signed with the above tokens.')

# With an active auth token, we're able to reuse the client object and request
# additional discogs authenticated endpoints, such as database search.
    def test_search(self, album='Oxygene', artist='Jean-Michel Jarre'):

        search_results = self.discogsclient.search('', title=album, type='release', artist=artist)
        print("pages > %s,  releases %s" % (search_results.pages, len(search_results)) )


        print( '\n== Search results for release_title=%s ==' % album)
        items = 0
        for release in search_results:
            # print(release)
            print( '\n\t== discogs-id {id} =='.format(id=release.id))
            print( '\tArtist\t: {artist}'.format(artist=', '.join(artist.name for artist
                                                 in release.artists)))
            print( '\tTitle\t: {title}'.format(title=release.title))
            # print( '\tYear\t: {year}'.format(year=release.year))
            # print( '\tLabels\t: {label}'.format(label=','.join(label.name for label in
            #                                     release.labels)))
            # print( '\tImages\t: {image}'.format(image=','.join(image for image in
            #                                     release.images)))
            print( 'Images %d' % len(release.images) )
            for i in release.images:
                 if i['type'] == 'primary': print( '\tImages\t: {image}'.format(image=i['uri']) )

            if items > LIMIT:
                break
            else:
                items+=1


    def find_art(self, artist, album):
        print("Discogs: find_art for", artist, album)
        """ Search for the album and then identify the best match
            Algorithm for chosing the right album:
            put the search results into a table, search and sort the table accordingly
            1. Highest ex-score, highest fuzzy match of album and artist -weighted towards the alnum
            2. Best match on Artist name
            3. Best match on Album
            4. Album type could be used but some will be compilations??  """
        ALBUM_MATCH_WEIGHT = 1.5
        search_results = self.discogsclient.search(album+" "+artist, type='release', format='cd')
        print("pages > %s,  releases %s" % (search_results.pages, len(search_results)) )

        albums = []
        LIMIT = 25
        for release in search_results:
            a={}
            # m = self.discogsclient.master(release.id)
            # print(m.main_release.title)

            a['album']  = release.title
            a['match']  = ALBUM_MATCH_WEIGHT*fuzz.token_sort_ratio(a['album'], album)

            # print(release)

            for _artist in release.artists:
                # print(_artist.name)
                a['artist'] = _artist.name
                a['match']  += fuzz.token_sort_ratio(a['artist'], artist)


            for i in release.images:
                if 'type' in i and 'uri' and i['type'] == 'primary':
                    a['uri']    = i['uri']

            print(a)
            if 'uri' in a: albums.append(a)   #Dont bother if one could
            if len(albums) > LIMIT: break

        best_match = 0
        for a in albums:
            if a['match'] > best_match:
                best   = a
                print ("Best so far:", a)
                best_match = best['match']

        if best_match > 70:
            print("Image successfully found, match score was %d of %d, uri: %s" % (best['match'], len(albums), best['uri']) )
            return best['uri']
        else:
            return None

"""
    Issues:
    1.  Rather slow
    2.  The title includes the artist?
    3.  Needs to be more robust - retry limiting could happen
    4.  Test out the wrapper class to see if using OAuth improves throughput
    5.  Build out the radio interface
    6.  Winamp/Tidal APIs?
    """


if __name__ == '__main__':

    d = Discogs()
    # d.test_search()
    # print("find art")
    d.find_art('Jean-Michel Jarre', 'Magnetic Fields')
    # # m.find_art('Dire Straits', 'Brothers in Arms')
    # # m.coverart_exists("46a48e90-819b-4bed-81fa-5ca8aa33fbf3")
    # m.find_art('Tim Hughes', '')