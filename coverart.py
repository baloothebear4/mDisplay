#!/usr/bin/env python
#
# mVista Project
#
# v0.1	   16.11.15		Baloothebear4
#
# Module : coverart.py.py
# Purpose: Class to manage the interface to MPD capturing the metadata
#          and handling control signals
#
##

from PIL import Image
import mutagen.id3, mutagen.flac, mutagen.mp4
from os import listdir
from os.path import splitext, dirname, getmtime
import time, tempfile, re
import json
import requests, validators
from urllib.request import urlopen, Request
from concurrent.futures import ThreadPoolExecutor

from art_apis import lastFMAPI, TidalArt, Discogs, Musicbrainz

PLAYART_W          	= 250
PLAYART_H          	= 250
ART_W  				= 480
ART_H  				= 480

THREAD_POOL_SIZE	= 4

DEFAULTARTFILE 		= ''
MOODE_METADATA_FILE = '/var/local/www/currentsong.txt'

APIS = (TidalArt,lastFMAPI, Discogs)  #   Musicbrainz )
APIclasses = []


class CoverArtItem():
	covers 		= ['Cover.jpg', 'cover.jpg', 'Cover.jpeg', 'cover.jpeg', 'Cover.png', 'cover.png',
				   'Cover.tif', 'cover.tif', 'Cover.tiff', 'cover.tiff',
	        	   'Folder.jpg', 'folder.jpg', 'Folder.jpeg', 'folder.jpeg', 'Folder.png', 'folder.png',
				   'Folder.tif', 'folder.tif', 'Folder.tiff', 'folder.tiff']
	extensions 	= ['jpg', 'jpeg', 'png', 'tif', 'tiff', 'bmp']

	def __init__(self, ref='', artist='', album='', audio_file=''):
		self.ref			= ref		#unique reference to idenify the song: is a filename for MPD, a string for Airplay
		self.artist			= artist
		self.album			= album
		self.file			= audio_file
		self.coverart_file  = None    #path to the artwork file, could be on a mounted drive
		self.small_bin	 	= None	  #encoded binary (for list display)
		self.large_bin		= None	  #encoded binary for the play page
		self.exists			= False
		self.foundby		= None     #text field to be set by the algoritm that found the art file


		# print ("CoverArtItem : __init__ %s" % self)


	def save(self,image):
		try:
			self.coverart_file = tempfile.NamedTemporaryFile(prefix="image_",suffix=".jpg",delete=True)
			with self.coverart_file as file:
				file.write(image)
				# print ('CoverArt save: %s' % self.coverart_file.name)
				image = Image.open(self.coverart_file.name)
				self.large_image = image.resize((ART_H, ART_W), Image.ANTIALIAS)
				self.small_image = image.resize((PLAYART_H, PLAYART_W), Image.ANTIALIAS)
			self.exists = True

			return True

		except Exception as e:
			print ("CoverArt: save: failed <%s>" % (e))
			return False



	def find_embedded(self, file):
		# print ("CoverArtItem : find_embedded %s" % file)
		try:
			# if 'http' in file:
			# 	raise 'not a file'
			fh = open(file)  # test if the file exists
			fh.close()
			audio = mutagen.File(file)
			try:
				if 'mp3' in audio.mime[0]:
					id3 = mutagen.id3.ID3(file)
					if 'APIC:' in id3:
						found = self.save(id3.getall('APIC:')[0].data)
					else:
						print ("CoverArtItem: find_embedded: MP3 file without art embedded: %s" % file)
						found = False

				elif 'flac' in audio.mime[0]:
					flac = mutagen.flac.FLAC(file)
					if flac.pictures:
						found = self.save(flac.pictures[0].data)
					else:
						print ("CoverArtItem: find_embedded: FLAC file without art embedded: %s" % file)
						found = False

				elif 'mp4' in audio.mime[0]:
					mp4 = mutagen.mp4.MP4(file)
					if 'covr' in mp4:
						found = self.save(mp4['covr'][0])
					else:
						print ("CoverArtItem: find_embedded: M4A file without art embedded: %s" % file)
						found = False
				else:
					print("CoverArtItem: find_embedded: content not recognised>", audio.mime[0])
					found = False

			except Exception as e:
				print ("CoverArtItem: found_embedded : No embedded artwork found in mp3, flac or mp4: error %s" % str(e))
				found = False
		except Exception as e:
			print ("CoverArtItem : found_embedded : file does not exist %s: exception %s" % (file, e))
			found = False

		if found:
			self.foundby = 'embedded'

		return found

	def find_at_url(self, url):
		found = False
		# print ("CoverArtItem : find_at_url: %s" % url)
		try:
			image_on_web = urlopen( url )
			# print ("CoverArtItem : find_at_url type %s" % image_on_web.info()['Content-Type'])
			if 'image' in image_on_web.info()['Content-Type']:
				buf = image_on_web.read()
				found= self.save(buf)

				image_on_web.close()
				# print ("CoverArtItem : FOUND find_at_url : %s" %  url)
			else:
				pass
				# print ("CoverArtItem : find_at_url: Image not found : Content is %s" % image_on_web.info()['Content-Type'])
		except Exception as e:
			# print ("CoverArtItem : find_at_url failed %s" % str(e))
			found = False
		return found


	def find_in_folder(self):
		"""
		Look in the folder containing the audio file, assume its a url
		then check to see if a standard coverart file or file with image extension Exists
		"""
		# print ("CoverArtItem : find_in_folder %s" % self)
		try:

			root_ext = splitext(self.file)
			dir      = dirname(self.file)
			# print ("CoverArtItem : found_in_folder :  %s, %s" % (root_ext, dir))
			""" first look for valid image files """
			for ext in CoverArtItem.extensions:
				if self.find_at_url("%s.%s" % (root_ext[0],ext)):
					self.foundby = 'in folder'
					return True

			""" next, iterate through all the coverart standard files """
			for f in CoverArtItem.covers:
				if self.find_at_url("%s/%s" % (dir, f)):
					self.foundby = 'in folder'
					return True

		except:
			print ("CoverArtItem : found_in_folder : file does not exist %s" % file)
			#raise
			pass
		return False

	def find_in_file(self):
		"""
		Download the audio file at the given URL, save temporarily,
		then check to see if it contains an embedded image
		"""
		found = False
		info  = ''
		# print ("CoverArtItem : find_file_at_url type %s" % self)
		try:
			file_on_web = urlopen( self.file )
			info = file_on_web.info()

			if 'icy-url' in info:
				request = Request(self.file)
				# try:
				request.add_header('Icy-MetaData', 1)
				response = urlopen(request)
				print("CoverArtItem: find_in_file: radio station not handled ",response.info())
				response.close()
				raise Exception ('web radio not a file')


			if 'audio' in info['Content-Type']:
				print ("CoverArtItem: find_in_file downloading audio %s" % self.file)
				buf = file_on_web.read()
				temp_file = tempfile.NamedTemporaryFile(prefix="audio_",suffix=".flac",delete=True)
				with temp_file as file:
					file.write(buf)
					found= self.find_embedded(file.name)
				# print ("CoverArtItem: find_in_file : found = ", found)
				return found
			else:
				raise Exception ('file does not contain image')

			# file_on_web.close()
		except Exception as e:
			print ("CoverArtItem : find_in_file failed %s. URL>%s  : %s" % (str(e), self.file, info))

		if found == False: print ("CoverArtItem : find_in_file failed %s. URL>%s : %s" % (str(e), self.file, info))
		return found

	def find_at_apis(self):
		for api in APIclasses:
			url   = api.find_art(self.artist, self.album, self.file)
			if api.match>150 and url != False:
				# print("Found by %12s with match %3d uri %s" % (api.name, api.match, url))
				self.foundby = 'by ' + api.name
				return self.find_at_url(url)
		return False

	def wait_for_new_metadata(self):
		TIMEOUT   = 10
		WAITDELAY = 0.1
		originalTime = getmtime(MOODE_METADATA_FILE)
		start_time   = time.time()

		while time.time()-start_time < TIMEOUT:
			if getmtime(MOODE_METADATA_FILE) > originalTime:
				print ("CoverArt: wait_for_new_metadata: new file detected")
				time.sleep(WAITDELAY)   #pause to allow write to complete
				return True
			time.sleep(1)
			# print ("CoverArt: wait_for_new_metadata: waiting...", originalTime)

		print ("CoverArt: wait_for_new_metadata: no new file detected")
		return False

	def find_in_moode(self):
		# print("CoverArtItem: find_in_moode ")
		right_album = False
		try:
			handle = open(MOODE_METADATA_FILE)
			line   = handle.readline()

			while line:

				field	 = line.split('=')[0]
				contents = line[line.find("=")+1:-1]
				# print("CoverArtItem: find_in_moode : line[0]: %s, line[1]:%s" % (field,contents))

				if 'album' in field:
					right_album = (self.album == contents)
					# print("CoverArtItem: find_in_moode: album", right_album)

				elif 'coverurl' in field:
					if right_album:
						coverart_url = contents
						print("CoverArtItem: find_in_moode: found url: ", coverart_url, right_album)
						self.foundby = 'by Moode metadata'
						return self.find_at_url(coverart_url)
					else:
						print("CoverArtItem: find_in_moode: metadata not for current album %s %s waiting..." % (self.album, right_album) )
						handle.close()
						if not self.wait_for_new_metadata(): break
						handle = open(MOODE_METADATA_FILE)

				line = handle.readline()
		except Exception as e:
			print("CoverArtItem: find_in_moode: error ", e)

		# print("CoverArtItem: find_in_moode : not found image")
		return False

	def __str__(self):
		text  = 'CoverArt Item for >ref: %s\n' % (self.ref)
		text += "  >Exists %s, " % self.exists
		if self.small_bin != None: text += "  Small binary, "
		if self.large_bin != None: text += "  Large binary, "
		text += '\n  >Album: %-15s  Artist: %s\n' % (self.album, self.artist)
		if self.coverart_file != None: text += '  >ArtFile: %-15s\n' % (self.coverart_file.name)
		text += '  >Audio_file: %-15s\n' % (self.file)
		text += '  >Found by: %-15s\n ' % (self.foundby)
		return text

class CoverArtLib(CoverArtItem):
	"""
	For MPD source the art is embedded in the file or in the same folder
	for shairport the artwork comes across in the pipe
	once artwork is found is is saved a file in the /tmp/metadata/coverart	folder and the name placed in
	metadata.coverart_file variable.  If cannot be found then then is set to None

	For apple music sources the coverart is sent as a binary file

	This class builds a database of coverart files and the compressed, sized images ready
	for fast display.  The caching of coverart files is done to improve display performance, particularly
	needed for list displays.
	"""
	# """ Create some key objects globally to avoid excessive memory load """
	retry = 0
	while retry < 1:
		try:
			for api in APIS:
				print("API init: ", api)
				APIclasses.append(api())
			break
		except Exception as e:
			print("API init: failure ", e)
			retry += 1

	def __init__(self):
		self.art_db  = {}			   #use the song filename as the key
		self.threadpool = ThreadPool(THREAD_POOL_SIZE)

	def find_art(self, audio_file='', artist='', album='', ):
		#take an MPD filename and check first if an image file exists already, then in the folder
		#or if the image is embedded
		# Two versions - single and multi-threaded
		ref = artist + ' ' + album  #lets use the audio_file name as the unique reference for the album art
		# print ("CoverArt: find : ref %s : file=%s" % (ref, audio_file))

		if ref in self.art_db:
			art = self.art_db[ref]

		else:
			art = CoverArtItem(ref, artist, album, audio_file)

			self.art_db.update( {ref : art} )   #mark that  searech has started

			if not self.threadpool.add_task( self.search, art):
				self.search( art )
			# print ("CoverArt: find : took %fs : ref %s, %s : Exists=%s" % ((time.time()-t), artist, album, art.exists))
			# if art.exists == False:
			# 	print ("CoverArt: find: art DB", self.art_db)

		return art

	def search(self, art):
		""" if there is art in the file this is always the best place to know its right_album
		but it takes time, so kick this off and if its found the art gets updated """
		self.t= time.time()

		for find_fn in (art.find_at_apis, art.find_in_folder, art.find_in_moode, art.find_in_file):
			# print("CoverArtLib: search in", find_fn.__name__)
			if find_fn():
				break

		if art.exists:
			print ("CoverArt: search: in %2.2f by %s for %s" % (time.time()-self.t, art.foundby, art.ref))
			self.art_db.update( {art.ref : art} )   # record that artwork does not exist for this song
		else:
			print ("CoverArt: search : No image found for:", art.ref)
			del self.art_db[art.ref]

	def add_art(self, ref, binary):
		art = CoverArtItem(ref=ref)
		art.save(binary)
		self.art_db.update( {ref : art} )
		return art

	def __str__(self):
		text = "Coverart database\n"
		for name in self.art_db:
			text += " : %s\n" % (self.art_db[name])
		return text



class ThreadPool():
    def __init__(self, num_threads):
        # print ("ThreadPool: __init__ : %d threads" % num_threads)
        self.executor    = ThreadPoolExecutor(max_workers=num_threads)
        self.threadcounter = 0

    def count_threads(self):
        self.threadcounter-=1
        # print ("ThreadPool : count_threads : active threads  %d" % self.threadcounter)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        if self.threadcounter < THREAD_POOL_SIZE:
            self.threadcounter+=1
            # print ("ThreadPool : add_task : %s : active threads  %d" % (func.__name__, self.threadcounter))
            handle = self.executor.submit(func, *args, **kargs)
            handle.add_done_callback(lambda f: self.count_threads())
            return handle
        else:
            return False

    def cancel_task(self, handle):
        try:
            handle.cancel()
        except Exception as e:
            print("ThreadPool: cancel_task: failed %s" % e)

    def test(self, t):
        time.sleep(t)
        print("thread test done %d" % t)





#  A couple of utility functions
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



t1 = '/mnt/Music/Example/Playing in the Shadows/01 Skies Dont Lie.mp3'
t2 = '/mnt/Music/Example/Playing in the Shadows/07 Microphone.mp3'
t3 = '/mnt/Music/Kraftwerk/Autobahn (2009 Digital Remaste/1-05 Morgenspaziergang.mp3'
t4 = 'https://cdn.devality.com/station/8476/audiophile.jpg'
if __name__ == '__main__':
	c=CoverArtLib()
	c.find_art(t4)
	# p = ThreadPool(10)
	# p.add_task(p.test, 2)
	# p.add_task(p.test, 4)
	# print("waiting")
