#!/usr/bin/env python
#
# mVista Project
#
# v0.1	   30.10.15		Baloothebear4
#
# Module : mpd.py
# Purpose: Class to manage the interface to MPD capturing the metadata
#          and handling control signals
#
##

from mpd import MPDClient
from coverart import file_to_text, CoverArtLib, ThreadPool
from datactrl import PlayerMetadata, PlayList
import time                        #format the numerics appropriately

PAUSE_INTERVAL = 7

class MPD(PlayerMetadata):

	def __init__(self, coverart=True):
		try:
			self.coverartlib      = CoverArtLib()
			self.time_paused	  = False
			self.threadpool 	  = ThreadPool(1)
			super().__init__('MPD')
			if coverart:
				self.grab()

		except Exception as e:
			print ("MPD initialisation error "+ str(e))


	def grab(self):
		if self.start():
			status = self.client.status()      # either use the MPD status call or a string
			self.status.get_status(status)
			if self.status.single == '1':
				print ('playing through playlist')
				self.client.single(0)

			if self.isplaying():
				currentsong = self.client.currentsong()
				self.track.get_track(currentsong)
				self.time_paused	  = False
				if self.track.new_track:
					self.track.add_coverart( self.coverartlib.find_art(self.track.file, artist=self.track.artist, album=self.track.album) )
					self.track.find_source_and_origin()
					self.grab_playlist()

					# print("MPD: grab: state=%s, track=%s, album=%s, artist=%s: status %s" %
					# 	(self.status.state, self.track.song, self.track.album, self.track.artist, self.status))
			elif 'pause' in self.status.state:
				if self.time_paused == False:
					self.time_paused	  = time.time()
				self.grab_paused()
			else:
				self.status.check_vol(status)

			self.end()
		return self

	def is_playing(self):   # need to call grab() beforehand
		if self.status.state != 'stop': #and self.md.file.find(UPMP_ID)>=0: #current song is a file
			return True
		else:
			self.status.state = 'stop'
			return False


	def grab_playlist(self):
		length = 0
		if self.playlist is None: print("grab_playlist: player is none")
		if self.playlist.handle is not None: self.threadpool.cancel_task(self.playlist.handle)
		self.playlist = PlayList()
		# if self.start():
		self.playlist.add_playlist_length( self.status.playlistlength )
		length = self.playlist.length
		plist                = self.client.playlistinfo()
		self.playlist.handle = self.threadpool.add_task(self.build_library, plist)
		if self.playlist.handle == False:
			self.build_library(plist)
		print ("MPD: Grab playlist: len %d in %2.4fs" % (length, self.playlist.create_duration() ) )

	def grab_paused(self):
		""" After a while a pause turns into a stop so time this event """
		if time.time() - self.time_paused > PAUSE_INTERVAL:
			self.status.state = 'stop'

	def build_library(self, plist):
		# print("MPD: build_library for", plist)
		try:
			for song in plist:
				i = self.playlist.get_playlist_item(song)
				i.add_art( self.coverartlib.find_art(audio_file=i.file, artist=i.artist, album=i.album) )
		except Exception as e:
			print("MPD: build_library: failed ", e)

	def end(self):
		# print("end")
		self.client.close()                     # send the close command
		self.client.disconnect()                # disconnect from the server


	def start(self):
		try:
			# print("start")
			self.client             = MPDClient()   # persistent connection to the MPD server
			self.client.timeout     = 10            # network timeout in seconds (floats allowed), default: None
			self.client.idletimeout = None          # timeout for fetching the result of the idle command is handled seperately, default: None
			self.client.connect("localhost", 6600)  # connect to localhost:6600
			return True
		except Exception as e:
			print ("MPD: start: failure: "+ str(e))
			return False


	def grab_volume(self):
		if self.start():
			mpd_status      = self.client.status()      # either use the MPD status call or a string
			self.status.check_vol(mpd_status)
			# print ("Volume grabbed %f " % self.status.vol)
			self.end()

		return self.status.vol

	def change_volume(self, vol, amount=1, to=-1):
		if self.start():
			self.status.vol = vol
			# mpd_status      = self.client.status()      # either use the MPD status call or a string
			# self.md.vol     = int( mpd_status[ 'volume' ])
			if to >-1 and to <=100:
				self.client.setvol(int(to))      # either use the MPD status call or a string
			elif to >100:
				self.client.setvol(100)      # either use the MPD status call or a string
			elif amount >0:
				if self.status.vol+amount <=100:
					self.client.setvol(self.status.vol+amount)
				else:
					self.client.setvol(100)
			elif amount <0:
				if self.status.vol+amount >=0:
					self.client.setvol(self.status.vol+amount)
				else:
					self.client.setvol(0)
			else:
				print ("Volume end stop reached")
				pass
			self.end()
			# print ("Volume changed: vol=%d :amount=%d, to=%d " % (self.status.vol, amount, to))

	def change_state(self, state):
		if self.start():
			if state == 'next':
				self.client.next()
			elif state == 'prev':
				self.client.previous()
			elif state == 'stop':
				self.client.stop()
			elif state == 'pause/resume':
				if self.status.state == 'play':
					self.client.pause(1)
				else:
					self.client.pause(0)
			elif state == 'repeat':
				if self.status.repeat:
					self.client.repeat(0)
				else:
					self.client.repeat(1)
			elif state == 'shuffle':
				if self.status.shuffle:
					self.client.random(0)
				else:
					self.client.random(1)
			elif state == 'mute':
				self.client.setvol(0)
			else:
				print ("change_state unknown %s " % state)

			print ("state changed "+state)
			self.end()

	def add_song(self,uri):
		if self.start():
			self.client.add(uri)
			print ("MPD: add_song : song changed to %s" % uri)
			self.end()

	def addAndplay(self, uri):
		if uri != None:
			if self.start():
				self.client.add(uri)
				pos       = int(self.client.status()['playlistlength'])
				self.client.play(pos-1)
				self.end()
			#print "MPD: addAndplay : song changed to %s, %d" % (uri, pos-1)
		else:
			print ("MPD: addAndplay : uri fault- cannot play %s" % (uri))

	def change_song(self,pos):
		if self.start():
			self.client.play(pos)
			print ("song changed to position %d" % pos)
			self.end()

	def seek_song(self,pos):     # NB this is a relative amount +ve forwards by 1%, -ve backwards by 1%
		if self.start():        # not sure what happens when seeking past the end of song
			if (pos >= 0 and pos <=100) or (pos <0 and pos >=-100):
				shift = pos*self.status.duration/100
			else:
				shift = -pos*self.status.duration/100
			self.client.seekcur('%+f' % (shift))
			print ("song seeked to position %f " % shift)
			self.end()


	def file_to_metadata(self, file):
		md = {}
		sections = file_to_text(file).split('/')
		if len(sections)>3:
			md['song']   = sections[len(sections)-1].split('.')[0]
			md['artist'] = sections[len(sections)-3]
			md['album']  = sections[len(sections)-2]
			#print "Song :%s\nArtist : %s\nAlbum:%s\n" % (self.md.song, self.md.artist, self.md.album)
			return md
		else:
			return False




	def print_status(self):
		# print self.mpd_status
		for s,v in self.mpd_status.items():
			print (s+":"+v)

	def isplaying(self):
		return self.status.state == 'play'


""" Test code """

# def vol(dir):
#     if dir == FrontPanel.CLOCKWISE:
#         pass

def test_volume(p):
    print ( "Testing player volume")
    md = p.grab()
    print ( md )
    vol = p.grab_volume()
    print ( "Volume grabbed %d" % vol)
    p.change_volume(31)
    vol = p.grab_volume()
    print ( "Volume up grabbed %d" % vol)
    time.sleep(3)
    p.change_volume(-45)
    vol = p.grab_volume()
    print ( "Volume down grabbed %d" % vol)
    time.sleep(3)
    p.change_volume(to=101)
    vol = p.grab_volume()
    print ( "Volume abs grabbed %d vs %d" % (vol, 101))

def test_state(p):
    print ( "Testing player controls - start playing")
    md = p.grab()
    print ( md)
    p.change_song(md.songpos)

    STATES = ( 'next', 'prev','pause/resume', 'pause/resume', 'repeat','shuffle','repeat','shuffle', 'stop')
    for s in STATES:
        md = p.grab()
        print ( md)
        print ( 'change to state %s' % s)
        p.change_state(s)
        time.sleep(5)

    md = p.grab()
    print ( md)

def test_seek(p):
    print ( "Testing player controls - start playing")
    md = p.grab()
    print ( md)
    p.change_song(md.songpos)
    time.sleep(3)
    p.seek_song(50)
    time.sleep(3)
    p.seek_song(-25)


if __name__ == '__main__':
	try:
		file = []
		u = MPD()

		while True:
			t= time.time()
			md = u.grab()

			# print ("%s" % md.status)
			# print ("%s" % u.track)
			print("Grab time = %f" % (time.time()-t))
			# print ("%s" % u.playlist)
			time.sleep(1)


		# print ( md.coverart
		# print ( md
		# test_volume(u)
		# test_state(u)
		# test_seek(u)
		# u.change_state('stop')

		#p = u.grab_playlist()
		#print ( p


		# while True:
		#     md = u.grab()
		#     #print ( p
		#     time.sleep(3)
		#
		#     print ( "active...  %s" % (md.state)
		#     if md.state == 'play': print ( md


	except Exception as e:
		print(e)
		print (file)
