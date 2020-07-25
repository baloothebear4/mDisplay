#!/usr/bin/env python3
"""
#
# v0.1     14.01.20  Baloothebear4
#
# Module : art_apis.py
# Purpose: Set of classes to you internet databases and services to find Cover Art includes:
    1. Tidal
    2. discogs
    3. LastFM
    4. Musicbrainz
    5. SHOUTCast (more for radio stations)

    Each class has similar search apis so can be called from a list
    NB: Note that fuzzy matching is used to determine the best match of album/artist to the release item found
"""

import musicbrainzngs
from   fuzzywuzzy import fuzz
import sys, time

import discogs_client
from   discogs_client.exceptions import HTTPError

import json
import requests, validators
from   urllib.request import urlopen, Request

import tidalapi



class Keys():
    file   = '.env'
    passes = {}

    def __init__(self):
        try:
            with open(Keys.file, 'r') as f:
                text = ' '
                while text:
                    text = f.readline().replace("'","").replace('"',"").split()
                    if len(text) == 3:
                        Keys.passes.update({text[0]: text[2]})
        except Exception as error:
            print("Keys.__init__> environment file with passwords and tokens not found: ", Keys.file, error)

        print("Keys.__init__> key file %s: key passes %s " % (Keys.file, Keys.passes) )

#https://resources.tidal.com/images/dec9ac03/1474/449d/8b2f/b65a3209069b/320x320.jpg

ALBUM_MATCH_WEIGHT = 1.0
ALBUM_LIMIT        = 30
MATCH_THRESHOLD    = 140
MAX_MATCH_SCORE    = 200


class lastFMAPI():

    API_URL         = "http://ws.audioscrobbler.com/2.0/"
    name            = 'lastFMAPI'
    match           = 0

    def __init__(self, keys):
        self.keys = keys

    def get(self,payload):
        headers = {'user-agent': 'dataquest'}

        payload['api_key'] = self.keys.passes['lastFMAPI.API_KEY']
        payload['format'] = 'json'

        response = requests.get(lastFMAPI.API_URL, headers=headers, params=payload)
        return response

    def find_album(self, artist, album):
        payload = {'artist': artist, 'album': album, 'autocorrect': 1  }  # fixes misspelt artists
        payload['method'] = 'album.getInfo'

        return self.get(payload)

    def find_art(self, artist, album, file=''):
        try:
            r = self.find_album(artist, album)
            coverart_url = r.json()['album']['image'][5]['#text']
            if not validators.url(coverart_url): raise Exception ('url not valid')
            # print ("lastFMAPI: find_art >> ", coverart_url)
            lastFMAPI.match = MAX_MATCH_SCORE
            return coverart_url
        except:
            # print ("lastFMAPI : find_album_art >> Cover art not found at url:", r.json()['album']['url'])
            lastFMAPI.match = 0
            return False

    def jprint(self, obj):
        # create a formatted string of the Python JSON object
        text = json.dumps(obj, sort_keys=True, indent=4)
        print(text)

    def scrobble(self, artist, album, track):
        print ("lastFMAPI : scrobble >> not written")

class Musicbrainz():
    name            = 'Musicbrainz'
    match           = 0

    def __init__(self, keys):
        musicbrainzngs.set_useragent(
            "mDisplay",
            "0.1",
            "https://github.com/baloothebear4/mVista/",)
        musicbrainzngs.auth(keys.passes['musicBrainz.USERNAME'], keys.passes['musicBrainz.TOKEN'])

    def get_image_uri(self, release_id):
        try:
            # print(("look art at ID", release_id)
            data = musicbrainzngs.get_image_list(release_id)
            print(data, '\n')
            for image in data["images"]:
                if "Front" in image["types"] and image["approved"]:
                    print( "%s is an approved front image!" % image["thumbnails"]["large"])
                    return image["thumbnails"]["large"]
            return False
        except Exception as e:
            # print( "Musicbrainz: get_image_uri: failed ",e)
            return False

    def find_art(self, artist, album, file=''):
        """ Search for the album and then identify the best match
            Algorithm for chosing the right album:
            put the search results into a table, search and sort the table accordingly
            1. Highest ex-score, highest fuzzy match of album and artist -weighted towards the alnum
            2. Best match on Artist name
            3. Best match on Album
            4. Album type could be used but some will be compilations??  """

        d = musicbrainzngs.search_release_groups(artist + ' ' + album)
        # print("Musicbrainz: find_art: for %30s/%s, releases %s" % (artist, album,  len(d['release-group-list'])))

        albums = []
        for k in d['release-group-list']:
            a={}

            if 'id' in k and 'title' and 'artist-credit' and 'ext:score':
                # print("Musicbrainz: find_art: looking for", k['title'])
                uri = self.get_image_uri(k['id'])
                if uri:
                    a['id']     = k['id']
                    a['uri']    = uri
                else:
                    continue
                a['score']  = int(k['ext:score'])
                a['title']  = k['title']
                a['match']  = ALBUM_MATCH_WEIGHT*fuzz.token_sort_ratio(a['title'], album) + a['score']

            for n in k['artist-credit']:
                if 'name' in n:
                    a['name']    = n['name']
                    a['match']  += fuzz.token_sort_ratio(a['name'], artist)

            # print(a)
            albums.append(a)

        Musicbrainz.match = 0
        for a in albums:
            if a['match'] > Musicbrainz.match:
                best = a

        if Musicbrainz.match > MATCH_THRESHOLD:
            # print("Musicbrainz: find_art: Image successfully found, match score was", best_match)
            return best['uri']
        else:
            return False

"""
    Discogs data base API

"""
request_token_url = 'https://api.discogs.com/oauth/request_token'
authorize_url     = 'https://www.discogs.com/oauth/authorize'
access_token_url  = 'https://api.discogs.com/oauth/access_token'
user_agent       = 'mDisplay'

# consumer_key    = 'JJCOegYnRLCLRejtcZbo'
# consumer_secret = 'UFlGrCViqSkoBNfRTGZyUfmpTGNbFbMM'


class Discogs():
    name            = 'Discogs'
    match           = 0

    def __init__(self, keys):
        self.discogsclient = discogs_client.Client(user_agent, user_token=keys.passes['Discogs.consumer_token'])
        # fetch the identity object for the current logged in user.
        user = self.discogsclient.identity()


    def find_art(self, artist, album, file=''):

        """ Search for the album and then identify the best match
            Algorithm for chosing the right album:
            put the search results into a table, search and sort the table accordingly
            1. Highest ex-score, highest fuzzy match of album and artist -weighted towards the alnum
            2. Best match on Artist name
            3. Best match on Album
            4. Album type could be used but some will be compilations??  """

        try:
            search_results = self.discogsclient.search(album+" "+artist, type='release', format='cd')
            # print("Discogs: find_art: for %30s/%s, pages > %s,  releases %s" % (artist, album, search_results.pages, len(search_results)))

            albums = []
            for release in search_results:
                a={}
                # m = self.discogsclient.master(release.id)
                # print(m.main_release.title)

                try:
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
                except Exception as e:
                    continue

                # print(a)
                if 'uri' in a: albums.append(a)   #Dont bother if one could
                if len(albums) > ALBUM_LIMIT: break

            Discogs.match = 0
            for a in albums:
                if a['match'] > Discogs.match:
                    best   = a
                    # print ("Best so far:", a)
                    Discogs.match = best['match']

            if Discogs.match > MATCH_THRESHOLD:
                # print("Discogs: find_art: Image successfully found, match score was %d of %d, uri: %s" % (best['match'], len(albums), best['uri']) )
                return best['uri']
            else:
                return False
        except:
            return False

"""
    Issues:
    1.  Rather slow
    2.  The title includes the artist?
    3.  Needs to be more robust - retry limiting could happen
    4.  Test out the wrapper class to see if using OAuth improves throughput
    5.  Build out the radio interface
    6.  Winamp/Tidal APIs?
    """

"""
    Tidal service API (NB: this is unpublished but has a well written python API)
    see https://pythonhosted.org/tidalapi/index.html
"""


class TidalArt():
    name            = 'TidalArt'
    match           = 0

    def __init__(self, keys):

        self.session = tidalapi.Session()
        self.session.login(keys.passes['tidal_username'], keys.passes['tidal_password'])


    def get_track(self, track_id):
        return self.session._map_request('tracks/%s' % track_id, params={'limit': 100}, ret='tracks')

    def find_art(self, artist, album, file=''):

        """ Search for the album and then identify the best match
            Algorithm for chosing the right album:
            put the search results into a table, search and sort the table accordingly
            1. Highest ex-score, highest fuzzy match of album and artist -weighted towards the alnum
            2. Best match on Artist name
            3. Best match on Album
            4. Album type could be used but some will be compilations??  """
        albums = []
        if 'tidal' in file and 'trackId':

            try:
                track_id = file[file.find('trackId'):].split('=')[1]
                track = self.get_track(track_id)

                # print("found    %30s/%-30s for track id %s, %s" % (track.album.name, track.artist.name, track_id, track ))
                a  = {'album' : track.album.name,
                      'match' : MAX_MATCH_SCORE,
                      'artist': track.artist.name,
                      'uri'   : track.album.image }

                if 'uri' in a: albums.append(a)   #Dont bother if one could

            except Exception as e:
                print('TidalArt: find_art: track id search failure:', e)
                return False
        else:
            search_results = self.session.search('album', album)

            # print("Tidal: find_art: for %30s:%30s >%d albums found" % (album, artist,len(search_results.albums) ))

            for release in search_results.albums:
                # print("release ", release)
                a={}
                try:
                    a['album']  = release.name
                    a['match']  = ALBUM_MATCH_WEIGHT*fuzz.token_sort_ratio(a['album'], album)

                    a['artist'] = release.artist.name
                    a['match']  += fuzz.token_sort_ratio(a['artist'], artist)

                    a['uri']    = release.image

                except Exception as e:
                    print('TidalArt: find_art: failure:', e)

                print(a)
                if 'uri' in a: albums.append(a)   #Dont bother if one could
                if len(albums) > ALBUM_LIMIT: break

        TidalArt.match = 0
        for a in albums:
            if a['match'] > TidalArt.match:
                # print (a)
                best   = a
                TidalArt.match = best['match']

        if TidalArt.match >  MATCH_THRESHOLD:
            # print("Image successfully found, match score was %d of %d albums found, artist/album: %s/%s, uri: %s" % (best['match'], len(albums), best['artist'],best['artist'],best['uri']) )
            return best['uri']
        else:
            return False

    def find_test_tracks(self, test_playlist_name='Test'):
        # search_results = self.session.search('playlist', 'jazz')
        search_results = self.session.get_user_playlists(self.session.user.id)
        # print("#playlists > %s, user %s" % (len(search_results), self.session.user.id) )
        test_playlist = 0
        for playlist in search_results:
            # print("%30s:%-30s" % (playlist.name, ""))
            if test_playlist_name in playlist.name:
                test_playlist = playlist.id
                name = playlist.name
        print("\nCreating test data from playlist: %s\n" % name)
        search_results = self.session.get_playlist_tracks(test_playlist)
        self.test_albums=[]
        for track in search_results:
            self.test_albums.append({'artist':track.artist.name, 'album':track.album.name})
            print("'%s'/'%s' > %s" % (track.artist.name, track.album.name, track.name ))
        return self.test_albums

test_albums = { 'Jean-Michel Jarre', 'Magnetic Fields'}


if __name__ == '__main__':

    k = Keys()
    d = TidalArt(k)
    print("Found >",d.find_art('The City Of Prague Philharmonic Orchestra', '100 Greatest Classical Pieces', 'http://192.168.1.239:49149/tidal/track?version=1&trackId=20741754') )

    APIS = (lastFMAPI, TidalArt, Discogs, Musicbrainz, )
    APIclasses = []
    for api in APIS:
        APIclasses.append(api(k))

    for test in d.find_test_tracks('Cover Art Test'):
        print("\n>>> %s/%-40s" % (test['artist'], test['album']) )
        art = ''
        for api in APIclasses:

            start = time.time()
            art   = api.find_art(test['artist'], test['album'])
            found = art != False

            print("Found=%5s in %fs: by %12s with match %3d uri %s" % (found, time.time()-start, api.name, api.match, art))



    # d.test_search()
    # print("find art")
    # d.find_art('Eric Alexander', 'Eric Alexander')
    # d.find_art('Eric Alexander', 'Gently')


    # # m.find_art('Dire Straits', 'Brothers in Arms')
    # # m.coverart_exists("46a48e90-819b-4bed-81fa-5ca8aa33fbf3")
    # m.find_art('Tim Hughes', '')

"""
'Miles Davis'/'Hail To The Real Chief' > Hail To The Real Chief
'Joey Alexander'/'Warna' > Warna
'Charles Lloyd'/'Requiem (Live From The Lobero)' > Requiem
'Carla Bley'/'Life Goes On: Life Goes On' > Life Goes On: Life Goes On
'Jeremy Pelt'/'The Art of Intimacy, Vol. 1' > Always on My Mind
'Pat Metheny'/'America Undefined' > America Undefined
'Works For Me'/'Reach Within' > Mr. M
'Bill Laurance Trio'/'The Pines' > The Pines
'Sasha Berliner'/'Azalea' > Midori
'Eric Alexander'/'Gently' > Gently
'Buddy Rich'/'Just in Time' > Just in Time
'Wynton Marsalis'/'Motherless Brooklyn (Original Motion Picture Soundtrack)' > Motherless Brooklyn Theme (feat. Willie Jones III, Philip Norris, Isaiah J. Thompson, Ted Nash, & Daniel Pemberton)
'Lee Konitz Nonet'/'Old Songs New' > Blues
'Erroll Garner'/'Campus Concert (Octave Remastered Series)' > Mambo Erroll (Live)
'Eri Yamamoto Trio'/'Goshu Ondo Suite' > Echo of Echo
'Hal Galper'/'The Zone: Live at the Yardbird Suite' > Scufflin'
'Gary Bartz'/'April in Paris' > April in Paris
'Kyle Eastwood'/'Cinematic' > Taxi Driver – Theme
'Keith Jarrett'/'Munich 2016 (Live)' > Somewhere Over The Rainbow
'Jeff Goldblum & the Mildred Snitzer Orchestra'/'I Shouldn’t Be Telling You This' > The Sidewinder / The Beat Goes On
'Jon Batiste'/'Chronology Of A Dream: Live At The Village Vanguard' > KENNER
'Joey Alexander'/'Downtime' > Downtime
'Buddy Rich'/'Wind Machine' > Wind Machine
'Brad Mehldau'/'Mon chien Stupide (Bande originale du film)' > Henri's Lament
'Gerald Cleaver'/'Live At Firehouse 12' > Pilgrim's Progress
'Lafayette Harris Jr.'/'He's My Guy' > He's My Guy
'Pat Metheny'/'You Are' > You Are
'Pasquale Grasso'/'Solo Monk' > Epistrophy
'The New York All-Stars'/'Second Impressions' > Second Impressions
'Michael Dease'/'Never More Here' > Blue Jay
'Julia Hülsmann Quartet'/'This Is Not America' > This Is Not America
'Vincent Herring'/'Bird-ish' > Bird-ish
'Randy Brecker'/'SACRED BOND - BRECKER PLAYS ROVATTI' > The Other Side of the Coin
'Echoes of Swing'/'Winter Days at Schloss Elmau' > Winter Moon
'Joey Alexander'/'Freedom Jazz Dance' > Freedom Jazz Dance
'Laszlo Gardony'/'La Marseillaise' > Misty
'Wynton Marsalis'/'Motherless Brooklyn (Original Motion Picture Soundtrack)' > Jump Monk (feat. Joe Farnsworth, Russell Hall, Isaiah J. Thompson & Jerry Weldon)
'Jon Batiste'/'SOULFUL (Live)' > SOULFUL
'Nicholas Payton'/'C' > C
'Rastko Obradovic Quartet'/'Lake by the Forest' > Lake by the Forest
'Rodney Whitaker'/'All Too Soon: The Music of Duke Ellington' > Harlem Air Shaft
'Erroll Garner'/'A Night at the Movies (Octave Remastered Series)' > How Deep is the Ocean
'Hakan Başar'/'On Top of the Roof' > On Top of The Roof
'Marc Copland'/'And I Love Her' > And I Love Her
'Barney Wilen'/'Live in Tokyo ‘91' > Bass Blues
'Stephane Belmondo'/'It's Real' > It's Real
'Théo Ceccaldi'/'Manoir de mes rêves' > Manoir de mes rêves
'Ron Carter'/'Foursight - Stockholm, Vol. 1' > Cominando
'Chick Corea'/'Trilogy 2 (Live)' > All Blues
'Keith Jarrett'/'Part III (Live)' > Part III
'Hiromi'/'Spectrum' > Yellow Wurlitzer Blues
'Chris Minh Doky'/'Cinematique' > My Favorite Things
'John Coltrane'/'Blue World' > Naima
'Nicholas Payton'/'Relaxin' with Nick' > Relaxin' with Nick
'Keith Jarrett'/'It's A Lonesome Old Town (Live)' > It's A Lonesome Old Town
'Jacky Terrasson'/'53' > The Call
'Jon Batiste'/'HIGHER (Live)' > HIGHER
'Poncho Sanchez'/'Trane's Delight' > Blue Train
'Ethan Iverson Quartet'/'Common Practice (Live At The Village Vanguard / 2017)' > Jed From Teaneck
'Art Pepper'/'Promise Kept: The Complete Artists House Recordings' > Blues For Blanche (Alternate A)
'Johnny Costa'/'Plays Mister Rogers' Neighborhood Jazz' > Won't You Be My Neighbor?
'Eric Wyatt'/'The Golden Rule: For Sonny' > The Golden Rule (For Sonny Rollins)
'Ahmad Jamal'/'Ballades' > So Rare
'John Coltrane'/'Blue World' > Blue World
'Miles Davis'/'Rubberband' > Carnival Time
'Avishai Cohen'/'Playing The Room' > Ralph's New Blues
'Enrico Rava'/'Roma (Live)' > Secrets
'Chick Corea'/'Crepuscule With Nellie (Live)' > Crepuscule With Nellie
'Chrissie Hynde'/'Valve Bone Woe' > Naima
'Hendrik Meurkens'/'Polka Dots and Moonbeams' > Polka Dots and Moonbeams
'Wynton Marsalis'/'Daily Battles (From Motherless Brooklyn: Original Motion Picture Soundtrack)' > Daily Battles (feat. Joe Farnsworth, Russell Hall, Isaiah J. Thompson & Jerry Weldon)
'Miguel Zenón'/'Sonero: The Music of Ismael Rivera' > Las Tumbas
'Jacky Terrasson'/'The Call' > The Call
'Kjetil Mulelid Trio'/'What You Thought Was Home' > What You Thought Was Home
'Triosence'/'Arabian Princess' > Arabian Princess
'George Coleman'/'When I Fall in Love' > When I Fall in Love
'Jazzmeia Horn'/'Love And Liberation' > No More
'Quentin Collins'/'The Hill' > The Hill
'Kevin Hays'/'Violeta' > Violeta
'Laurent Coulondre'/'Michel on My Mind' > Michel on My Mind
'Ethan Iverson Quartet'/'The Man I Love (Live At The Village Vanguard / 2017)' > The Man I Love
'The Kenyatta Beasley Septet'/'The Frank Foster Songbook by the Kenyatta Beasley Septet' > Cidade Alta
'Jimmy Cobb'/'This I Dig of You' > Full House
'Hiromi'/'Blackbird' > Blackbird
'Avishai Cohen'/'Shir Eres (Lullaby)' > Shir Eres (Lullaby)
'Ted Nash, Steve Cardenas & Ben Allison'/'Somewhere Else: West Side Story Songs' > America
'Kjetil Mulelid Trio'/'Homecoming' > Homecoming
'Corey Christiansen'/'La Proxima' > Ambedo
'Pasquale Grasso'/'Solo Ballads, Vol. 1' > Someone to Watch Over Me
'Tim Ries'/'For Elis' > For Elis
'Art Pepper'/'Straight, No Chaser (Take 2)' > Straight, No Chaser (Take 2)
'Matthew Whitaker'/'Now Hear This' > Yardbird Suite
'Diego Rivera'/'Connections' > Connections
'Mike Holober & The Gotham Jazz Orchestra'/'Hiding Out' > Caminhos Cruzados [Radio Edit]
'Jazz at Lincoln Center Orchestra'/'Jazz and Art' > Stuart Davis for the Masses: Garage Lights
'Leo Richardson Quartet'/'Nice - The Best of Jazz to Hit the Road' > Blues for Joe
'Jon Batiste'/'Anatomy Of Angels: Live At The Village Vanguard' > Round Midnight
'Marilyn Mazur'/'Night Travel' > NIGHT TRAVEL
'Abdullah Ibrahim'/'The Balance' > Song for Sathima
'Jenny Scheinman & Allison Miller’s Parlour Game'/'Parlour Game' > The Right Fit
'Paul Booth'/'Seattle Fall' > Seattle Fall
'Jimmy Cobb'/'Blood Wolf Moon Blues' > Blood Wolf Moon Blues
'John Clark'/'Faces' > Silver Rain, pt. III
'Kjetil Mulelid Trio'/'Wedding March' > Wedding March
'The Tubby Hayes Quartet'/'Grits, Beans And Greens' > Grits, Beans And Greens
'Bill Evans'/'Some Other Time: The Lost Session From The Black Forest' > In A Sentimental Mood
'Steve Kuhn'/'Non-Fiction' > The Fruit Fly
"""
