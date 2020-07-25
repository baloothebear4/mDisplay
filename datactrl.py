#!/usr/bin/env python
#
# mVista Project
#
# v0.1       16.11.15		Baloothebear4
#
# Module : datactrl.py
# Purpose: Base class of objects used for metadata & playlists + utilities
#
##


from coverart import CoverArtItem
from urllib.request import urlopen

from time import time, sleep



class PlaylistItem():                    # collect and manage the metadata
    def __init__(self, song):
        self.track   = ''
        self.album   = ''
        self.artist  = ''
        self.itempos = 0
        self.itemid  = 0
        self.file	 = ''

        for k, v in song.items():
            if   'title'  in k: self.track   = v
            elif 'album'  in k: self.album   = v
            elif 'artist' in k: self.artist  = v
            elif 'pos'    in k: self.itempos = int(v)
            elif 'id'     in k: self.itemid  = int(v)
            elif 'file'   in k: self.file	= v

    def add_art(self, art):
        self.coverart= art

    def __str__(self):
        text  = "PlaylistItem:\n"
        text += " %20s : %s\n" % ('track',self.track)
        text += " %20s : %s\n" % ("artist", self.artist)
        text += " %20s : %s\n" % ("album", self.album)
        text += " %20s : %s\n" % ("file",self.file)
        text += " %20s : %d\n" % ("Item pos ",self.itempos)
        text += " %20s : %d\n" % ("Item id ",self.itemid)
        text += " %20s : %s\n" % ("CoverArt",self.coverart)
        return text

class PlayList(PlaylistItem):
    handle     = None
    list       = {}  # dictionary of Playlist items

    def __init__(self):
        self.make_time  = time()

    def add_playlist_length(self, len):
        self.length = len

    def create_duration(self):
        self.make_time = time() - self.make_time
        return self.make_time

    def get_playlist_item(self,song):
        i = PlaylistItem(song)
        self.add(i.itempos, i)
        return i

    def add(self, ref, item):    # ref is the position of the item in the playlist
        PlayList.list.update( {ref : item})
        PlayList.length = len(PlayList.list)

    def item(self, pos):
        i = None
        if pos in PlayList.list:
            i = PlayList.list[pos].item
        return i

    def itemid(self, pos):
        i = None
        if pos in PlayList.list:
            i = PlayList.list[pos].itemid
        return i

    def itemref(self, pos):
        i = None
        if pos in PlayList.list:
            i = PlayList.list[pos].itemref
        return i

    def coverart(self, pos):
        art = None
        if pos in PlayList.list:
            art = PlayList.list[pos].coverart
        return art

    def title(self, pos):
        t = None
        if pos in PlayList.list:
            t = PlayList.list[pos].title
        return t

    def description(self, pos):
        a = None
        if pos in PlayList.list:
            a = PlayList.list[pos].description
        return a

    def __str__(self):
        text  = "Playlist:\n"
        if PlayList.length > 0:
            text += " %20s : %s\n" % ('Playlist length', PlayList.length)
            for i, item in PlayList.list.items():
                try:
                    text += str(item)
                except Exception as e:
                    print ("Playlist : __str__ : coding error %s" % e)
        else:
            text += "Playlist is empty"
        return text

class StatusMetadata():
    def __init__(self):
        self.vol         = 0 #: 0-100
        self.volume      = '' # formated string of volume
        self.repeat      = 0 #: 0 or 1
        self.random      = 0 #: 0 or 1
        self.single      = 0 #: (Introduced with MPD 0.15) 0 or 1
        self.consume     = 0 #: 0 or 1
        self.playlist    =0 #: 31-bit unsigned integer, the playlist version number
        self.playlistlength = 0 #: integer, the length of the playlist
        self.state       = 'stop'  # : play, stop, or pause
        self.songpos     = 0 #: playlist song number of the current song stopped on or playing
        self.songid      = 0 #: playlist songid of the current song stopped on or playing
        self.nextsong    = 0 #: playlist song number of the next song to be played
        self.nextsongid  = 0 #: playlist songid of the next song to be played
        self.time        = 0 #: total time elapsed (of current playing/paused song)
        self.elapsed     = 0 #: (Introduced with MPD 0.16) Total time elapsed within the current song, but with higher resolution.
        self.elapsedpc   = 0
        self.duration    = 0#: (Introduced with MPD 0.20) Duration of the current song in seconds.
        self.bitrate     = 0 # : instantaneous bitrate in kbps
        self.xfade       = 0#: crossfade in seconds
        self.mixrampdb   = 0#: mixramp threshold in dB
        self.mixrampdelay= 0 #: mixrampdelay in seconds
        self.audio       = '0:0:0' #: sampleRate:bits:channels
        self.samplerate  = 44.100
        self.bitsize     = 16
        self.updating_db = 0 #: job id
        self.error       = ''  #: if there is an error, returns message here
        self.shuffle     = 0
        self.repeat      = 0

    def get_status(self, status):
        # print("get_status for %s" % status)
        for k, v in status.items():
            if   'volume' in k: self.check_vol(status)
            elif 'state'  in k: self.state  = v
            elif 'audio' in k:
                audio = v.split(":")
                if  any(i.isdigit() for i in audio[ 1 ] ):  # check for digits
                    self.bitsize = int( audio[ 1 ] )
                else:
                    self.bitsize = 16

                if  any(i.isdigit() for i in audio[ 0 ] ):
                    self.samplerate = float ( audio[ 0 ] ) /1000
                else:
                    self.samplerate = 44.1

            elif 'bitrate' in k: self.bitrate = float( v )

            elif 'elapsed' in k: self.elapsed = float( v )
            elif 'time' in    k:
                self.time = v.split(':')
                self.duration = float(self.time[1])
                if self.duration >0 :
                    self.elapsedpc = float(self.time[0]) / float(self.time[1])
                else:
                    self.elapsedpc = 0.0

            elif 'song'   == k: self.songpos = int(v)
            elif 'songid' == k: self.songid  = int(v)
            elif 'random' in k: self.shuffle = v=='1'
            elif 'repeat' in k: self.repeat  = v=='1'

            elif 'single' in k: self.single  = v
            elif 'playlistlength' in k: self.playlistlength  = int(v)

    def check_vol(self, status):
        if 'volume' in status and int( status['volume'] )>= 0:
            self.vol = int( status['volume'] )
        else:
            self.vol = 0
            self.volume = '%3.0f%%' % self.vol

    def __str__(self):
        text = "StatusMetadata\n"
        text += " %20s : %s\n" % ('State', self.state)
        text += " %20s : %s\n" % ('Volume', self.volume)
        text += " %20s : %s\n" % ("Bitrate", self.bitrate)
        text += " %20s : %s\n" % ("Sample rate", self.samplerate)
        text += " %20s : %s\n" % ("Bitsize", self.bitsize)
        text += " %20s : %s\n" % ("Elapsed",self.elapsed)
        text += " %20s : %f\n" % ("Duration",self.duration)
        text += " %20s : %f\n" % ("elapsedpc", self.elapsedpc)
        text += " %20s : %d\n" % ("Song pos ",self.songpos)
        text += " %20s : %d\n" % ("Song id ",self.songid)
        text += " %20s : %s\n" % ("Shuffle ",self.shuffle)
        text += " %20s : %s\n" % ("Repeat ",self.repeat)
        text += " %20s : %d\n" % ("Playlist length ",self.playlistlength)
        return text


class TrackMetadata(CoverArtItem):                    # collect and manage the metadata
    def __init__(self):
        #print 'metadata clear vol %f volume %s' % (self.vol, self.volume)
        self.state        = 'stop'
        self.last_song    = 'None'
        self.song         = ''
        self.artist       = ''
        self.album        = ''
        self.genre        = ''
        self.file         = ''    #file currently playing or stream
        self.coverart     = CoverArtItem()   #coverart object holding cached binaries
        self.type         = ''     # FLAC, ALAC etc
        self.origin       = ''     # eg Upmpdcli, Web Radio, iTunes, Apple Music etc

    def __str__(self):
        text  = "TrackMetadata:\n"
        text += " %20s : %s\n" % ('Song',self.song)
        text += " %20s : %s\n" % ("Artist", self.artist)
        text += " %20s : %s\n" % ("Album", self.album)
        text += " %20s : %s\n" % ("Genre", self.genre)
        text += " %20s : %s\n" % ("File",self.file)
        text += " %20s : %s\n" % ("Source type",self.type)
        text += " %20s : %s\n" % ("Origin ",self.origin)
        text += " %20s : %s\n" % ("CoverArt ",self.coverart)

        return text

    def find_source_type(self):
        if self.file.endswith('flac'):
            self.type = 'flac'
        elif self.file.endswith('mp3'):
            self.type = 'mp3'
        elif self.file.endswith('m4a'):
            self.type = 'aac'   # could be ALAC
        else:
            try:
                file_type = urlopen( self.file ).info()['Content-Type']
                if 'audio' in file_type:
                    self.type = file_type[6:]
                elif 'application' in file_type:
                    self.type = file_type[14:]
                else:
                    self.type = ''
            except Exception as e:
                print("TrackMetadata: source_type: failed: %s : url: %s" % (e, self.file))
        # print("TrackMetadata: source_type: %s" % self.type)

    def is_tidal_tag(self):
        TIDALTAGS = ['tidal', 'trackid']
        for tag in TIDALTAGS:
            if tag in self.file.lower():
                return True
        else:
            return False

    def find_source_origin(self):
        try:
            file_type = urlopen( self.file ).info()
            if 'icy-url' in file_type:
                self.origin = 'streamed radio'
            elif self.is_tidal_tag():
                self.origin = 'Tidal'
            elif 'audio' in file_type['Content-Type']:
                self.origin = 'local music library'
            else:
                raise Exception ("MPD: source_origin unknown: \nmetadata %s" % (file_type))
            # print("TrackMetadata: source_origin: %s " % (self.origin))
        except Exception as e:
            self.origin = 'unknown'
            print("TrackMetadata: source_origin: failed: %s : url: %s" % (e, self.file))
            pass

    def find_source_and_origin(self):
        try:
            file_type = urlopen( self.file ).info()
            if 'icy-url' in file_type:
                self.origin = 'streamed radio'
            elif self.is_tidal_tag():
                self.origin = 'Tidal'
            elif 'audio' in file_type['Content-Type']:
                self.origin = 'local music library'
            else:
                self.origin = 'unknown'
                print("MPD: source_and_origin unknown: \nmetadata %s" % (file_type))


            if self.file.endswith('flac'):
                self.type = 'flac'
            elif self.file.endswith('mp3'):
                self.type = 'mp3'
            elif self.file.endswith('m4a'):
                self.type = 'aac'   # could be ALAC
            else:
                file_info = file_type['Content-Type']
                if 'audio' in file_info:
                    self.type = file_info[6:]
                elif 'application' in file_info:
                    self.type = file_info[14:]
                else:
                    self.type = ''

        except Exception as e:
            self.origin = 'unknown'
            print("TrackMetadata: source_and_origin: failed: %s : url: %s" % (e, self.file))

    def get_track(self, currentsong):
        # print("get_track for %s" % currentsong)
        for k, v in currentsong.items():
            if   'artist' in k: self.artist = v
            elif 'album'  in k: self.album  = v
            elif 'genre'  in k: self.genre  = v
            elif 'file'   in k: self.file   = v
            elif 'title'  in k: self.song   = v

    def add_coverart(self, art):
        self.coverart = art


class PlayerMetadata():
    def __init__(self, type=''):
        PlayerMetadata.type = type
        if type == 'MPD' :
            self.playlist = PlayList()
        else:
            PlayerMetadata.playlist = None

        self.track    = TrackMetadata()
        self.status   = StatusMetadata()
        # print("PlayerMetadata: startup for", type)


if __name__ == '__main__':
    # s = Station()
    # a = s._type()
    print ("No test" )
