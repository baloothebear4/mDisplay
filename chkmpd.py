#!/usr/bin/env python
#
from getmetadata import Metadata
from system import SystemStatus

s = SystemStatus
d = Metadata(s)

while True:
	d.grab_MPD()
	print "song ID %d, Playlist len%d" %(d.songid, d.playlistlength)
	for songdata in d.playlist:
		if int(songdata['id']) == d.songid:
			print songdata['file']

# while True:
# 	d.grab_Airplay()
