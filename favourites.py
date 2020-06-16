#!/usr/bin/env python
#
# mVista Project
#
# v0.1	   27.11.15		Baloothebear4
#
# Module : favourites.py
# Purpose: Class to manage the interface to the configuration file that holds
#			parameters such as favourite radio stations, the default, WiFi settings etc
#
##



from datactrl 		import RadioStation
from configparser 	import ConfigParser
import stat, os, json

CONFIG_FILE	   	   = "/etc/mVista.conf"
CONFIG_FILE_UMASK  = stat.S_IRWXG | stat.S_IRWXO | stat.S_IRWXU

CONFIG_FILE_HEADER = 	'%s\n%s\n%s\n%s\n' % (
						"mVista is an embedded music player.  Based on a Raspberry pi this\n",
						"provides a user interface to an LCD screen of the music meta data.\n",
						"Also provides some controls, via panel buttons for the user to select\n ",
						"songs from a playlist or web radio stations.  Full interface to Apple music" )
FAV_SECTION				= 'favourite_station'
SEARCH_SECTION			= 'searches'
MAX_FAVOURITES			= 50
MAX_SEARCHES			= 50

""" Sections : ['intro','favourite_station 0'...., 'search stations 0', ....]   """
DefaultSearches 		= [
			{'name' : 'BBC', 			'text' : 'bbc radio',	'description':'A set of BBC radio stations'},
			{'name'	: 'Funky stuff', 	'text' :'funk', 		'description':'Radio stations playing funk music' },
			{'name' : 'UK News', 		'text' : 'GB news',	'description':'UK based radio stations'} ]

class Config(object):
	""" config file structure:
		[intro]   text about the file
		[favourite_station 0]  this then lists a dict of the values which comprise a station
		....						NB station 0 is the default
		[favourite_station n ]
	"""

	def __init__(self):
		self.config 		= ConfigParser( allow_no_value= True )
		self.config_file 	= CONFIG_FILE
		self.config.read( self.config_file )
		self.searches		= self.get_searches()
		self.favourites		= self.get_favourites()

		try:
			fh = open(self.config_file, 'r')
		except:
			self.write_searches(DefaultSearches)

	def create_intro(self, config):
		#print "Config : create: Creating new config header: " + self.config_file
		if not config.has_section('intro'):
			config.add_section( 'intro')
			config.set( 'intro', CONFIG_FILE_HEADER )

	def create(self, new_config, favs_changed=False, searches_changed=False):
		""" Config file is rebuilt every time a write is done some that added, changed, deleted section all apply
			read in the sections that have not changed, the others ar set in the parser,
			then write the lot back out
			"""
		try:
			self.create_intro(new_config)

			if favs_changed:
				self.create_searches(new_config, self.searches)

			if searches_changed:
				self.create_favourites(new_config, self.favourites)

			with open( self.config_file, 'w' ) as configfile:
				new_config.write( configfile )
				chmod = 'sudo chmod o+rw %s' % self.config_file
			self.config = new_config

		except Exception as e:
			print ("Config : build : failed to write to config file %s" % str(e) )

	def write_favourites(self):
		""" Take play list of radio stations and write them to the favourites section
			Note that the station in position 0 is the default
			"""
		new_config = ConfigParser(allow_no_value= True)
		self.create_favourites(new_config, self.favourites)
		self.create(new_config, favs_changed=True)

	def create_favourites(self, new_config, list):
		s = 0
		for i in list:
			section = "%s %d" % (FAV_SECTION, s)
			if not new_config.has_section(section): new_config.add_section( section )
			new_config.set( section, 'name', self.favourites[i].name)
			new_config.set( section, 'country', self.favourites[i].country)
			new_config.set( section, 'radio_id', str(self.favourites[i].radio_id))
			new_config.set( section, 'image_url', self.favourites[i].image_url)
			new_config.set( section, 'streams', json.dumps(self.favourites[i].streams))
			new_config.set( section, 'thumb_url', self.favourites[i].thumb_url)
			new_config.set( section, 'description', self.favourites[i].description)
			new_config.set( section, 'default', str(self.favourites[i].default))
			#print "Config : write_favourites : section %s : %s" % (section, new_config)
			s += 1

	def get_favourites(self):
		self.favourites = {}
		try:
			self.config.read( self.config_file )
			for i in range(MAX_FAVOURITES):
				section = "%s %s" % (FAV_SECTION, i)
				if not self.config.has_section(section): break
				s = RadioStation()
				s.name = self.config.get( section, 'name')
				s.country = self.config.get( section, 'country')
				s.radio_id = self.config.getint( section, 'radio_id')
				s.image_url = self.config.get( section, 'image_url')
				s.streams = json.loads(self.config.get( section, 'streams'))
				s.default = self.config.getboolean( section, 'default')
				self.favourites.update( {s.radio_id : s })
				# print "Config : get_favourites : section %s : %s" % (section, s )
				# for i in s.streams:
				# 	print "Config : get_favourites : stream %s %s" % (i, i['stream'])

		except IOError:
			print ("Config : get_favourites : could not read config file")

		return self.favourites

	def add_favourite(self, stn):
		if not stn.radio_id in self.favourites:
			self.favourites.update( {stn.radio_id : stn })
			print ("Config : add_favourite : %s" % stn)
		else:
			print ("Config : add_favourite : duplicate not added %s" % stn)
		self.write_favourites()

	def remove_favourite(self, id):
		if id in self.favourites: del self.favourites[id]
		print ("Config : remove_favourite : %d" % id)
		if self.get_default_station() == False:
			self.make_default_station( self.favourites.keys()[0] ) # ensure there is a default
		self.write_favourites()

	def get_default_station(self):
		for s in self.favourites:
			if self.favourites[s].default:
				print ("Config : get_default_station : %s" % s)
				return self.favourites[s]
		print ("Config : get_default_station : no default found")
		return False

	def make_default_station(self, id):
		for s in self.favourites:
			if self.favourites[s].radio_id == id:
				self.favourites[s].default = True
				print ("Config : make_default_station : %s" % self.favourites[s])
			else:
				self.favourites[s].default = False
		print ("Config : make_default_station : %s" % id)
		self.write_favourites()

	def write_searches(self, searches):
		""" Take an array of dicts (name, text)
		"""
		new_config = ConfigParser(allow_no_value= True)
		self.create_searches(new_config, searches)
		self.searches = searches
		self.create(new_config, searches_changed=True)

	def create_searches(self, new_config, searches):
		s = 0
		if not new_config.has_section(SEARCH_SECTION):
			 new_config.add_section( SEARCH_SECTION )
		for i in searches:
			ref = "%s %d" % ('search', s)
			new_config.set( SEARCH_SECTION, ref, json.dumps(i))
			#print "Config : write_searches : ref %s : %s" % (SEARCH_SECTION, i)
			s += 1

	def get_searches(self):
		self.searches = []
		try:
			self.config.read( self.config_file )
			for i in range(MAX_SEARCHES):
				option = "%s %s" % ('search', i)
				if not self.config.has_option( SEARCH_SECTION, option): break
				s = json.loads(self.config.get( SEARCH_SECTION, option))
				self.searches.append( s )
				#print "Config : get_searches : search %s " % ( s )
		except IOError:
			print ("Config : get_searches : config does not exist %s" % str(e))

		return self.searches

	def __str__(self):
		#print out the whole config file - for debug purposes
		try:
			with open(self.config_file, 'r') as f:
				config = f.read()
		except:
			config = "Config %s file does not exist" % self.config_file
		return str(config)


if __name__ == '__main__':

	l = []
	for i in range (3):
		ts = RadioStation()
		ts.name          = 'Radio ' + str(i)     # ie item displayed and scrolled
		ts.country       = 'UK'      # ie Main descriptions of items
		ts.radio_id      = (i+1)*5     #unique dirble radio ID
		ts.image_url     = 'filename' # CoverArtItem()
		ts.thumb_url     = 'filename2' # CoverArtItem()
		ts.description   = 'Test radio station'
		ts.streams       = [{u'status': 0, u'stream': u'http://pub8.di.fm:80/di_vocaltrance'}, {u'status': 1, u'stream': u'http://pub8.di.fm:80/di_vocaltrance'}]     #[{u'status': 1, u'stream': u'http://pub8.di.fm:80/di_vocaltrance', u'emptycounter': 0, u'created_at': u'2015-04-11T14:20:24.000+02:00', u'timedout': False, u'updated_at': u'2015-11-27T10:06:07.000+01:00', u'Station_id': 8, u'content_type': u'audio/mpeg', u'bitrate': 96, u'id': 1}]
		ts.default		 = False
		l.append(ts)

	se = [ 	{'name' : 'BBC', 			'text' : 'bbc radio',	'description':'A set of BBC radio stations'},
			{'name'	: 'Funky stuff', 	'text' :'funk', 		'description':'Radio stations playing funk music' },
			{'name' : 'UK News', 		'text' : 'GB news',	'description':'UK based radio stations'} ]

	# for i in l:
	# 	print "Made Test data : %s" % i

	c = Config()

	# c.write_favourites()
	# c.write_searches(se)
	# # a=c.get_searches()
	# # for b in a:
	# # 	print "Search : %s " % (b)
	# l = c.get_favourites()
	# for i in l:
	# 	print "Received  data : %s" % i
	# # # #
	# se = [
	# 		{'name'	: 'Chunky stuff', 	'text' :'chunk' }]
	# #c.write_searches(se)
	# l = []
	# for i in range (2):
	# 	ts = RadioStation()
	# 	ts.name          = 'Radio ' + str(i)     # ie item displayed and scrolled
	# 	ts.country       = 'UK'      # ie Main descriptions of items
	# 	ts.radio_id      = i*10     #unique dirble radio ID
	# 	ts.image_url     = 'filename' # CoverArtItem()
	# 	ts.thumb_url     = 'filename2' # CoverArtItem()
	# 	ts.description   = 'Test radio station'
	# 	ts.streams       = [{u'status': 0, u'stream': u'http://pub8.di.fm:80/di_vocaltrance'}, {u'status': 1, u'stream': u'http://pub8.di.fm:80/di_vocaltrance'}]     #[{u'status': 1, u'stream': u'http://pub8.di.fm:80/di_vocaltrance', u'emptycounter': 0, u'created_at': u'2015-04-11T14:20:24.000+02:00', u'timedout': False, u'updated_at': u'2015-11-27T10:06:07.000+01:00', u'Station_id': 8, u'content_type': u'audio/mpeg', u'bitrate': 96, u'id': 1}]
	# 	ts.default		 = False
	# 	l.append(ts)
	#
	# c.write_favourites(l)
	# c.make_default_station(ts)
	# print "default stn %s" % c.get_default_station()
	ts = RadioStation()
	ts.name          = 'Radio ' + str(i)     # ie item displayed and scrolled
	ts.country       = 'UK'      # ie Main descriptions of items
	ts.radio_id      = 99     #unique dirble radio ID
	ts.image_url     = 'filename' # CoverArtItem()
	ts.thumb_url     = 'filename2' # CoverArtItem()
	ts.description   = 'Test radio station add'
	ts.streams       = [{u'status': 0, u'stream': u'http://pub8.di.fm:80/di_vocaltrance'}, {u'status': 1, u'stream': u'http://pub8.di.fm:80/di_vocaltrance'}]     #[{u'status': 1, u'stream': u'http://pub8.di.fm:80/di_vocaltrance', u'emptycounter': 0, u'created_at': u'2015-04-11T14:20:24.000+02:00', u'timedout': False, u'updated_at': u'2015-11-27T10:06:07.000+01:00', u'Station_id': 8, u'content_type': u'audio/mpeg', u'bitrate': 96, u'id': 1}]
	ts.default		 = False

	# c.add_favourite(ts)
	# ts.radio_id      = 199     #unique dirble radio ID
	# c.add_favourite(ts)
	# ts.radio_id      = 299     #unique dirble radio ID
	# c.add_favourite(ts)
	c.remove_favourite(299)


	a = c.get_favourites()
	for b in a:
		print ("Stream %s %s %s %s" % (a[b]._stream(), a[b]._bitrate(), a[b]._type(), a[b]._name()))
		print ("Stn %s" % a[b])





	#print "Config file \n\n%s" % c
