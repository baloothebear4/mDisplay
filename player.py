#!/usr/bin/env python
#
# mVista Project
#
# v0.1	   30.10.15		Baloothebear4
#
# Module : player.py
# Purpose: Class to manage the interface to various sources eg MPD and shairport capturing the metadata
#          and handling control signals
#
##


from airplay import ShairportSync
from mpdif import MPD
from datactrl import PlayerMetadata, PlayList
import time

PLAY_STATES = ( 'stop','play','pause' )
SOURCE_NAME = ( 'Local files', 'iTunes', 'Apple Music', 'Tidal','Radio')
PLAYERS     = (ShairportSync, MPD)
STAYPAUSED  = 120 #seconds


class Player():
    """ abstraction layer from the actual players themseleves, eg MPS, Shairport event_processor
        handles the control and metadata flows
        """
    def __init__(self, active):
    #    try:
            self.md         = PlayerMetadata('main')
            self.playing    = None
            self.check_active = active
            self.md.status.state   = 'stop'
            self.pausedat   = time.time()

            self.players    = {}
            for P in PLAYERS:  #note this is a prioritised list for playout
                player           = P()
                self.players[P]  = player

    def grab(self):
        """ grabs the Metadata from the the player that is currently running
            Look for state changes
            """

        if self.md.status.state == 'play':
            self.update()
            self.pausedat = time.time()  # get ready in case the next cycle is a pause

        elif self.md.status.state == 'pause': #  DO NOT FORCE a STOP and (time.time() - self.pausedat < STAYPAUSED):
            # keep checking the current player, but after a while timeout and stop
            self.update()
            if self.md.status.state != 'play':
                if self.whats_playing():
                    pass
                    #print "New player %s " % self.playing
                # else:
                #     print "Paused - No players changed"

        else:
        # assume playstate is stop
            #print "No players active, checking PIDs"
            #self.playing  = self.check_active()
            if self.whats_playing():
            #new player found
                pass
                #print "New player %s " % self.playing
            else:
            # assume playstate is still paused

                self.md.status.vol   = self.grab_volume()
                self.md.status.state = 'stop'
                self.playing  = None

        # print ("Player Grab: grab : track %s " % self.md.track)
        return self.md

    def update(self):
        if self.playing != None:
            self.md      = self.players[self.playing].grab()
            self.md.status.vol = self.players[MPD].grab_volume()
            # print( "Player : update : %s >%s %s" % (self.playing, self.md.status, self.md.track))

        else:
            print ("Stopped %s : Unknown player %s" % (self.md.status.state, self.playing))

    def grab_playlist(self):
        """ grabs the Playlist from the the player that is currently running
            Look for state changes
            """
        if self.playing != None:
            self.md.playlist = self.players[self.playing].grab_playlist()
            return self.md.playlist
        else:
            return PlayList()   # nothing going so return an empty playlist

    def grab_volume(self):
        return self.players[MPD].grab_volume()

    def change_state(self, state):
        if self.playing != None:
            return self.players[self.playing].change_state(state)
        else:
            #Try to start MPD if a play command is received and all is Stopped
            self.playing = MPD
            self.players[self.playing].change_song(0)  # start playing from the beginning of the playlist

    def change_volume(self, *args, **kwargs):
        return self.players[MPD].change_volume(self.md.status.vol, *args, **kwargs)

    def change_song(self, pos):
        if self.playing != None:
            return self.players[self.playing].change_song(pos)

    def seek_song(self, pos):
        if self.playing != None:
            return self.players[self.playing].seek_song(pos)

    def whats_playing(self):
        temp_md = PlayerMetadata('main')
        playout = False
        for P in self.players:
            temp_md = self.players[P].grab()
            if temp_md.status.state == 'play':
                self.playing = P
                self.update()
                playout = True
                break
        return playout

    def is_idle( self ):					# work out if the player is playing out or idle
        idle = (self.state == 'stop' or self.state == 'pause')
        return idle

    def quit(self):
        self.players[ShairportSync].quit()

    def __str__(self):
        text = "Player status :\n"
        text += " %20s : %s\n" % ('Player', self.playing)
        text += str(self.md)

        text += "MPD art"+str(self.players[MPD].art)
        text += "airplay art"+str(self.players[ShairportSync].art)
        return text

if __name__ == '__main__':
    try:
        # s = SystemStatus()
        p = Player(None)
        while True:
            md = p.grab()
            #print p.grab_playlist()

            #raise Exception
            time.sleep(3)

            print ("active... %s  %s %s" % (p.playing, p.md.status, p.md.track))
            if p.md.status.state == 'play': print (p)
    except:
        raise
        p.quit()
    # finally:
    #
