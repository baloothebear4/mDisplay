#!/usr/bin/env python
#
# Volumio Display Project
#
# v0.1	   20.08.15		Baloothebear4
#
# Module : getmetadata.py
# Purpose: Routines to manage the interface to MPD and shairport capturing the metadata for
#          subsequent formatting and display (not done here)
#
##

import math, re, os, sys, time                        #format the numerics appropriately
from mpd import MPDClient
from systemif import SystemStatus
from airplay import Airplay

#For the coverart
import mutagen.id3, mutagen.flac, mutagen.mp4
from os import listdir
from os.path import isfile, join, dirname

MINIMHDR = 'http://192.168.1.113:9790/minimserver/*'
LOCALHDR = '/mnt'
DEFAULTARTFILE = '/etc/metadata/coverart.jpg'


PLAY_STATES = (
	'stop',
	'play',
	'pause',
	'airplay'
	)

class Metadata:                    # collect and manage the metadata

	def clear( self ):
		self.state = 'stop'
		self.volume = ''
		self.song = ''
		self.artist = ''
		self.bitrate = ''
		self.samplerate = ''
		self.bitsize = ''
		self.album = ''
		self.genre = ''
		self.file = ''
		self.duration = '0'
		self.time = ['', '']     # integer elapsed & duration
		self.elapsed = '0.0'
		self.elapsedpc = 0.0
		self.vol = 0.0
		self.songid = 0
		self.songpos = 0
		self.playlistlength = 0
		self.coverart_file = None
		self.type = ''   #String of FLAC, ALAC, M4A, MP3, AAC

	def __init__( self, sys ):
		self.clear()
		try:
			self.client  = MPDClient()   # connect to the MPD server
			self.sys     = sys
			self.airplay = Airplay(sys.shairport_type)
			self.art     = CoverArt()

		except Exception, e:
			print "Metadata initialisation error "+ str(e)

	def __repr__( self ):
		text  = " %20s : %s\n" % ('State', self.state)
		text += " %20s : %s\n" % ('Volume', self.volume)
		text += " %20s : %s\n" % ('Song',self.song)
		text += " %20s : %s\n" % ("Artist", self.artist)
		text += " %20s : %s\n" % ("Bitrate", self.bitrate)
		text += " %20s : %s\n" % ("Sample rate", self.samplerate)
		text += " %20s : %s\n" % ("Bitsize", self.bitsize)
		text += " %20s : %s\n" % ("Album", self.album)
		text += " %20s : %s\n" % ("Genre", self.genre)
		text += " %20s : %s\n" % ("File",self.file)
		text += " %20s : %s\n" % ("State",self.state)
		text += " %20s : %s\n" % ("Elapsed",self.elapsed)
		text += " %20s : %s\n" % ("Duration",self.duration)
		text += " %20s : %s\n" % ("CoverArt File",self.coverart_file)
		text += " %20s : %d\n" % ("elapsedpc", self.elapsedpc)
		text += " %20s : %d\n" % ("Song id ",self.songid)
		text += " %20s : %d\n" % ("Playlist length ",self.playlistlength)
		return ( text )

	def grab( self ):
		# First of all work out if where to get the data from
		if self.is_airplay():            #watch this change for VolumioDisplay compatability, try to avoid checking system statsu too much add delay
			self.grab_Airplay()

		elif self.is_airplay_active():   #in case its just started
			self.grab_Airplay()

		else:
			self.grab_MPD()

	def grab_MPD_song( self ):  # sometimes Minim server fails to get the track right
		try:
			currentsong = self.client.currentsong()
			#print currentsong
			self.song = currentsong[ 'title' ]
			self.artist = currentsong[ 'artist' ]
			self.album = currentsong[ 'album' ]

			#self.genre = currentsong[ 'genre' ]
			self.file = currentsong[ 'file']
		except:
			self.file = currentsong[ 'file']
			if not self.file_to_metadata():
				self.artist = 'Artist unknown'
				self.song   = 'Song unknown'
				self.album  = 'Album unknown'

	def grab_MPD( self ):

		try:
			self.client.timeout = 10                # network timeout in seconds (floats allowed), default: None
			self.client.idletimeout = None          # timeout for fetching the result of the idle command is handled seperately, default: None
			self.client.connect("localhost", 6600)  # connect to localhost:6600
			self.mpd_status  = self.client.status()      # either use the MPD status call or a string
			self.playlist    = self.client.playlistinfo()

			if self.mpd_status[ 'single'] == '1':
				print 'playing through playlist'
				self.client.single( 0 )             # ie keep going through the playlist

			#print self.mpd_status
			#print self.playlist   #-- array of dicts containing song metadata
			self.state = self.mpd_status[ 'state' ]

			if not self.mpd_status[ 'state' ]=='stop' and 'audio' in self.mpd_status:
				self.state = self.mpd_status[ 'state' ]
				audio = self.mpd_status[ 'audio' ].split(":")

				self.grab_MPD_song()

				self.bitrate = '%4.0fkbps' %float( self.mpd_status[ 'bitrate' ] )

				if  self.is_num( audio[ 1 ] ):
					self.bitsize = '%2.0fbit' % float( audio[ 1 ] )
				else:
					self.bitsize = 'n/a bit'

				if  self.is_num( audio[ 0 ] ):
					self.samplerate = '%5.1fkHz' % ( float ( audio[ 0 ] ) /1000 )
				else:
					self.samplerate = 'n/a kHz'

				self.vol = float( self.mpd_status[ 'volume' ])
				self.volume = '%3.0f%%' % self.vol
				self.elapsed = self.mpd_status[ 'elapsed' ]
				self.time = self.mpd_status[ 'time' ].split(':')
				self.duration = str(self.time[1])
				self.elapsedpc = float(self.time[0]) / float(self.time[1])
				#print "Duration %s Time %s + %s & elapsed %f\n" % (self.duration, self.time[0], self.time[1], self.elapsedpc)
				self.playlistlength = int( self.mpd_status[ 'playlistlength' ])
				self.songpos = int( self.mpd_status[ 'song' ])

				self.coverart_file = self.art.find(self.file)
				self.source_type()

			else:
				self.clear()
				self.vol = float( self.mpd_status[ 'volume' ])
				self.volume = '%3.0f%%' % self.vol

			self.client.close()                     # send the close command
			self.client.disconnect()                # disconnect from the server


		except Exception, e:
			print "MPD access failure: "+ str(e)
			raise
			self.state = "fail"

	def is_airplay( self ):			# remember Airplay will override MPD if active
		return self.state == 'airplay'

	def print_status(self):
		# print self.mpd_status
		for s,v in self.mpd_status.iteritems():
			print s+":"+v

	def is_airplay_active( self ):			# remember Airplay will override MPD if active
		if self.sys.shairport_active() != 'no':
			self.state = 'airplay'
			return True
		else:
			self.state = 'stop'
			return False

	def grab_Airplay( self ):
		#need to read the volume
		if self.airplay.grab_metadata(self.sys.shairport_active()):
			self.artist = self.airplay.metadata['artist']
			self.song   = self.airplay.metadata['title']
			self.album  = self.airplay.metadata['album']
			self.genre  = self.airplay.metadata['genre']
			self.coverart_file  = self.airplay.metadata['artwork']
			self.bitrate = '256kHz'
			self.samplerate = '44.1kHz'
			self.bitsize = '16bit'
			self.elapsedpc = 0
			print self

	def source_type(self):
		if self.state == 'airplay':
			self.type = 'AAC'
		elif self.file.endswith('flac'):
			self.type = 'FLAC'
		elif self.file.endswith('mp3'):
			self.type = 'MP3'
		elif self.file.endswith('m4a'):
			self.type = 'ALAC'
		else:
			self.type = self.file[:-3].upper()


	def is_idle( self ):					# work out if the player is playing out or idle
		idle = (self.state == 'stop' or self.state == 'pause')
		return idle

	def file_to_metadata(self):

	    sections = file_to_text(self.file).split('/')
	    if len(sections)>3:
	        self.song = sections[len(sections)-1].split('.')[0]
	        self.artist = sections[len(sections)-3]
	        self.album = sections[len(sections)-2]
	        #print "Song :%s\nArtist : %s\nAlbum:%s\n" % (self.song, self.artist, self.album)
	        return True
	    else:
	        return False

	def is_num(self, s):
		return any(i.isdigit() for i in s)



class CoverArt():
	"""
	For MPD source the art is embedded in the file or in the same folder
	for shairport the artwork comes across in the pipe
	once artwork is found is is saved a file in the /tmp/metdata/coverart	folder and the name placed in
	metadata.coverart_file variable.  If cannot be found then then is set to None
	"""

	def __init__(self):
		self.coverart_file = None
		pass

	def find(self, file):
		#take an MPD filename and check first if an image file exists in the folder
		#or if the image is embedded
		#print "Trying file %s " % file
		file = file_to_text(file)
		file = file.replace( MINIMHDR, LOCALHDR )
		#print "Trying file %s " % file
		if   self.found_in_folder(file) or self.found_embedded(file):
			found = self.coverart_file
		else:
			self.coverart_file = None

		#print "CoverArt file: %s" % (self.coverart_file)
		return self.coverart_file

	def found_in_folder(self, file):
		# list files on folder and see if there any with image types.
		onlyfiles = []
		for f in listdir(dirname(file)):

			if f.endswith('jpg') or f.endswith('png') or f.endswith('bmp'):
				#print "Look at file %s  dir %s" % (f, dirname(file))
				self.coverart_file = "%s/%s" % (dirname(file), f)
				return True
		return False

	def save(self, art):
		try:
			open(DEFAULTARTFILE,'wb').write(art)
			self.coverart_file = DEFAULTARTFILE
			success = True
		except Exception, e:
			print "Failed to write coverart file %s" % str(e)
			success = False

		return success

	def found_embedded(self, file):
		try:
			id3 = mutagen.id3.ID3(file)
			if 'APIC:' in id3:
			#print id3
				found = self.save(id3.getall('APIC:')[0].data)
			else:
				print "MP3 file without art embedded"
				found = False

		except mutagen.id3.ID3NoHeaderError:
			try:
				flac = mutagen.flac.FLAC(file)
				found= self.save(flac.pictures[0].data)

			except: #mutagen.flac.FLACNoHeaderError:
				try:
					mp4 = mutagen.mp4.MP4(file)

					if 'covr' in mp4:
						print mp4
						found= self.save(mp4['covr'][0])
					else:
						print "M4A file without art embedded"
						found = False

				except Exception, e:
					print "No embedded artwork found in mp3, flac or mp4 %s" % str(e)
					found = False

		return found


def hexchar(s):
    hex = '0x'+s.replace('*','')
    return chr(int(hex,16))

def file_to_text(s):
    p=re.compile('\*\d\w')
    found = p.search(s)
    f = s
    while found:
        f = p.sub(hexchar(p.search(f).group()),f,1)
        found = p.search(f)
    return f

if __name__ == "__main__":
	s = SystemStatus()
	m = Metadata(s)
	while True:
		m.grab()
		#time.sleep(3)
		#print m
