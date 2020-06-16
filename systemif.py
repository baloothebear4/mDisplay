#
#  Title :  System.py
#  Purpose: Class definition part of VolumioDisplay to capture system status info for display
#  Author :  baloothebear4    23/09/15
#  Usage :  3 functions to capture and format strings with

import psutil, time


SYS_DEFAULT = {
		'cpu_load' 	 	 : '',
		'mpd_load'       : '',
		'shairport_load' : '',
		'disk_used'      : '',
		'mem_used'       : '',
		'ethernet_status': '',
		'wifi_status'    : '',
		'ip_address'     : '',
		'wlan_strength'  : '' }
FIFO_LENGTH = 5

LOAD_FIFO = ('cpu', 'mpd', 'shp')

HYSTERSIS = 4.0   # If a task is not significantly more busy, then neither are

class SystemStatus:

	def __init__(self):
		self.status = SYS_DEFAULT
		self.cpu_fifo = []
		self.mpd_fifo = []
		self.shp_fifo = []
		self.shairport_type = None

	#Find Volumio thread PID
		try:
			self.pid_names = {}
			self.shairport_pid = 0

			self.get_PIDs()


		except Exception as e:
			print ("Failed to initialise system parameters: %s" % str(e))


	def shairport_type(self):
		print ("Shairport type "+self.shairport_type)
		return  self.shairport_type


	def get_PIDs(self):
		for p in psutil.process_iter():
			self.pid_names[p.pid] = p.name()
			# print "name = %s pid = %d"
			if self.pid_names[p.pid] == 'mpd':
				self.mpd_pid 	   = self.pid_names.keys()[ self.pid_names.values().index('mpd')]

			elif self.pid_names[p.pid] == 'shairport':
				self.shairport_pid = self.pid_names.keys()[ self.pid_names.values().index('shairport')]
				self.shairport_type = 'shairport'   # these has different metadata

			elif self.pid_names[p.pid] == 'shairport-sync':
				self.shairport_pid = self.pid_names.keys()[ self.pid_names.values().index('shairport-sync')]
				self.shairport_type = 'shairport-sync'   # these has different metadata


	def __repr__(self):
		printout = ''
		for k,v in self.status.items():
				printout += '%18s : %s\n' % (k,v)
		return printout

	def grab(self):
		success = True

	#CPU load
		try:
			if self.shairport_pid == 0:
				self.get_PIDs()

			self.status['cpu_load'] = self.smooth( self.cpu_fifo, psutil.cpu_percent(interval = 0.1))
			self.cpu_fifo = self.cpu_fifo[-FIFO_LENGTH:]

			load = psutil.Process(self.mpd_pid)
			self.status['mpd_cpu']  = load.cpu_percent(interval = 0.1)
			self.status['mpd_load'] = self.smooth( self.mpd_fifo, self.status['mpd_cpu'])
			self.mpd_fifo = self.mpd_fifo[-FIFO_LENGTH:]

			load = psutil.Process(self.shairport_pid)
			self.status['shairport_cpu']  = load.cpu_percent(interval = 0.1)
			self.status['shairport_load'] = self.smooth( self.shp_fifo, self.status['shairport_cpu'])
			self.shp_fifo = self.shp_fifo[-FIFO_LENGTH:]

	#Disk & Memory
			self.status['mem_used'] = psutil.virtual_memory().percent
			self.status['disk_used']= psutil.disk_usage('/').percent

	#Network parameters
			# net = psutil.net_connections(kind='inet')
			# for c in net:
			# 	print "%s:%s" % (c.laddr)
			# addr = psutil.net_if_addrs()
			# for interface in addr:
			# 	# if interface == 'wlan':
			# 	print "ID %s : %s " % (interface, addr[interface])

			# stats = psutil.net_if_stats()
			# for nic, addrs in psutil.net_if_addrs().items():
			# 	if nic in stats:
		    #         print("%s (speed=%sMB, duplex=%s, mtu=%s, up=%s):" % (nic, stats[nic].speed, duplex_map[stats[nic].duplex],stats[nic].mtu, "yes" if stats[nic].isup else "no"))
			# 	else:
			# 		print("%s:" % (nic))
			#         for addr in addrs:
			#             print("    %-8s" % af_map.get(addr.family, addr.family), end="")
			#             print(" address   : %s" % addr.address)
			#             if addr.broadcast:
			#                 print("             broadcast : %s" % addr.broadcast)
			#             if addr.netmask:
			#                 print("             netmask   : %s" % addr.netmask)
			#             if addr.ptp:
			#                 print("             p2p       : %s" % addr.ptp)
		    #     print("")

			#self.status['
			# iwconfig wlan0 | grep -i --color quality
			# ifconfig

		except Exception as e:
			print ("Failed to get system status %s" % (str(e)))
			self.status['disk_used']  = 0.0
			self.status['mem_used']   = 0.0
			self.status['cpu_load']   = 0.0
			self.status['shairport_load'] = 0.0
			self.status['mpd_load']   = 0.0
			success = False

		#print self
		return success

	def check_active(self):
		self.grab()

		if self.status['shairport_load'] > self.status['mpd_load'] + HYSTERSIS:
			active = 'airplay'
		elif self.status['mpd_load'] > self.status['shairport_load'] + HYSTERSIS:
			active = 'mpd'
		else:
			active = None
		print ("Shairport %6f: %f MPD ==> %s" % (self.status['shairport_load'], self.status['mpd_load'], active))
		return active

	def smooth(self, fifo, value):
		fifo.append(value)
		#fifo = fifo[-FIFO_LENGTH:]
		sum = 0.0
		for v in fifo:
			sum += v
		ave = sum/len(fifo)
		#print "Val %5d: %5d Smoothed: FIFO len %d" % (value, ave, len(fifo))

		return ave


#
# sys = SystemStatus()
# # while True:
# sys.grab()
# print sys.shairport_active()
