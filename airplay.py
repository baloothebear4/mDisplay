#!/usr/bin/env python
#
# mVista Project
#
# v0.1	   30.10.15		Baloothebear4
#
# Module : airplay.py
# Purpose: Class to manage the interface to shairport or shairport-sync apps.
#		   As shairport uses a pipe to pass the metadata, this is checked in a separate Process
#			 to make sure no data is lost and the pipe reading is not blocking
#
##


# from rddaap import Daap
from multiprocessing import Process, Pipe
# import shpdec_dev.decoder as decoder
# import metadata
# from decoder import Processor, Infos
import decoder
from datactrl import PlayerMetadata, PlayList, PlaylistItem
from coverart import CoverArtLib
import time

SHAIRPORT_PIPE    = "/etc/shairport_metadata/now_playing"
SHAIRPORT_ART_DIR = "/etc/shairport_metadata"
SHAIRPORT_DEFAULT = {
	'artist'    : '',
	'album' 	: '',
	'comment' 	: '',
	'title' 	: '',
	'artwork' 	: '',
	'genre'		: ''
	}

SHAIRPORT_SYNC_PIPE = "/tmp/shairport-sync-metadata"


def read_shairport_pipe(file, pipe, type):
# Look for a block, keep reading if one is found
	line      = ''
	#print "looking for airplay metadata in "+file
	while True:
		try:
			# This works but blocks
			fifo = open(file, 'r')    #os.O_RDONLY | os.O_NONBLOCK )
			while True:
				line += fifo.readline() #[:-1]
				#print 'Pipe reader read >>%s<<\n' % (line)

				if type == 'shairport' and line.find('comment=') != -1 and line.find('artist=') != -1:  #shairport metadata
					#print "Block in pipe len %d:chunk >%s<" % (len(line), line)
					pipe.send(line)
					line = ''
				elif type == 'shairport-sync' and line.find('<item>') != -1 and line.find('</item>') != -1: #shairport-sync metadata
					#line = line.replace('\n','')
					#print "Block in pipe len %d:chunk [%s]" % (len(line), line[:80])
					pipe.send(line)
					line = ''
					#save the art to a file
					line = line[line.rfind('</item>')+7:]
					#print "Block residue = [%s]" % (line)

		except Exception as e:
			print ("read_shairport_pipe: Fault reading %s pipe: %s" % (type, str(e)))
			line      = ''
			time.sleep(5)

# needs the shairport classes creating
class Airplay(PlayerMetadata):
	def __init__(self):
		super().__init__('Airplay')
		self.clear()
		self.out_pipe, self.in_pipe = Pipe()
		self.p = Process(target=read_shairport_pipe, args=(self.file, self.in_pipe, 'shairport-sync'))
		self.p.start()

	def __repr__(self):
		printout = 'Airplay metdata: \n'
		for k,v in self.metadata.items():
				printout += '%12s : %s\n' % (k,v)
		return printout

	def is_playing(self):
		return self.status.state == 'play'

	def quit(self):
		self.p.terminate()

	def grab_playlist(self):
		self.playlist = PlayList()
		i  = PlaylistItem()
		#for song in plist:

		#print song
		i.song      = self.track.song
		i.album     = self.track.album
		i.artist    = self.track.artist
		i.songpos   = 0
		i.songid    = 1
		i.genre 	= self.track.genre
		i.songref   = self.track.songref

		i.coverart  = self.covertartlib.find(i.songref)
		#print i
		self.playlist.playlist.add(i.songpos, i)

		return self.playlist

	def clear(self):
		self.block       = ''
		self.art		 = CoverArtLib()
		self.lasttime    = 0.0   # timecode when elapsed last updated
		self.status.samplerate = 44100.0
		self.status.type     = 'aac'
		self.status.bitrate  = 256.0
		self.status.bitsize  = 16
		self.track.songpos  = 0  #info.songtracknumber
		# self.md.playlist.length = 1
		self.track.origin   = "airplay"
		self.status.source  = 'shairport-sync'


	def read_pipe(self):
		if self.out_pipe.poll(0):
			s = True
			self.block = self.out_pipe.recv()
			#print "received block [%s]" % self.block
		else:
			#print "nothing in pipe"
			s = False

		return s

	def isplaying(self):
		return self.status.state == 'play'

#
class ShairportSync(Airplay):
	def __init__(self):
		self.file       = SHAIRPORT_SYNC_PIPE
		Airplay.__init__(self)
		self.decoder 	= decoder.Processor()
		self.decoder.add_listener(self.event_processor)  # function `event_processor` defined bellow.

	def grab(self):
		try:
			# print("Airplay : grab : state", self.md.state)
			found = False
			new_track = self.read_pipe()

			while new_track:
				found = True
				self.decoder.process_line(self.block)
				new_track = self.read_pipe()

			#If nothing found, estimate where in the track the song position is
			# if not found and self.md.duration > 0 and self.md.state == 'play':
			if self.status.duration > 0 and self.status.state == 'play':
				t = time.time()
				# print("Estimating Song position to {last} : {dur}".format(last = self.status.elapsed, dur = self.status.duration))
				self.status.elapsed = self.status.elapsed + t - self.lasttime
				self.lasttime = t
				self.status.elapsedpc = float(self.status.elapsed) / self.status.duration
				# print("{state} Estimated Song position to {pospc} : {pos}".format(state=self.md.state, pospc = self.md.elapsedpc, pos = self.md.elapsed))
			# print ("Shairport duration = %s, state = %s " % (self.md.duration, self.md.state))

			# print("Airplay: grab:", self.status, self.track)
			return self
		except Exception as e:
			print("ShairportSync: grab : failure %s" % e)

	def kick_start(self):
		info = decoder.Infos()
		info.playstate = 'play'
		print ('kickstart')
		self.event_processor(decoder.STATE, info)

	def event_processor(self, event_type, info):
		"""
		This you can use to put into `add_listener(func)`.
		It will then print the events.
		:param event_type:
		:param info:
		:return:
		"""

		assert(isinstance(info, decoder.Infos))
		print ("Handling event %s: code: %s" % (event_type, info.type))
		if event_type == decoder.VOLUME:
			# print("Changed Volume to {vol}.".format(vol = info.volume))
			self.status.vol = info.volume

		elif event_type == decoder.SKIP:
			# print("Changed Song position to {pospc} : {pos} of {dur}".format(pospc = info.elapsedpc, pos = info.elapsed, dur = info.duration))
			self.status.elapsedpc = info.elapsedpc
			self.status.elapsed   = info.elapsed
			self.status.duration  = info.duration
			self.status.state     = 'play'
			self.lasttime     = time.time()

		elif event_type == decoder.STATE:
			print("Changed Play state to {code} : {state}".format(code = info.type, state = info.playstate))
			self.status.state  = info.playstate
			if self.status.state == 'stop':
				Airplay.clear(self)
				# print("ShairportSync: Stopped: duration: %s" % self.status.duration)


		elif event_type == decoder.CLIENT_REMOTE_AVAILABLE:
			print("Remote available {daid}, {acre}: state to {code} : {state}".format(daid = info.dacp_id, acre=info.active_remote, code = info.type, state = info.playstate))

		elif event_type == decoder.COVERART:
			try:
				self.status.songref  = '%s/%s/%s' % (info.songartist, info.songalbum, info.itemname)
				self.track.add_coverart( self.art.add_art(self.status.songref, info.songcoverart.binary) )

				#print "Event processor: Shairport-sync coverart saved with ref %s" % ref
				#print("Captured Coverart, wrote it to {file} .".format(file = cover_file))
			except Exception as e:
				self.track.coverart.exists = False
				print ("Failed to save Coverart: %s" % (str(e)))

		elif event_type == decoder.META:

			if info.itemname is not None: self.track.song   = info.itemname
			if info.songartist is not None: self.track.artist = info.songartist
			if info.songalbum is not None: self.track.album  = info.songalbum
			if info.songgenre is not None: self.track.genre  = info.songgenre
			if info.useragent is not None: self.track.origin = info.useragent
			if info.songformat is not None: self.track.source = info.songformat
			if info.songbitrate is not None: self.status.bitrate = info.songbitrate  #' 256kHz'
			if info.songsamplerate is not None: self.status.samplerate = info.songsamplerate
			if info.songformat is not None: self.status.type    = info.songformat


		else:
			#print "Daap event_processor : event %s" % event_type
			pass



if __name__== '__main__':
	a = ShairportSync()
	while True:
		g = a.grab()
		print (g.status, g.track)
		time.sleep(3)
