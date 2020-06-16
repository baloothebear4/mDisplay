#!/bin/env python3

from display 	import Screens
from player   	import Player
import datetime, time
# from systemif 	import SystemStatus
from frontpanel import FrontPanel


""" 	Top level function for mDisplay application
	Main control loop to:
	- start the threads to detect button press/knob change events
	- check for changes in player status
	- update the display with changes
	- facilitate user selection and controls
	- handle and report any faults

	Title : mDisplay v02
	Author: baloothebear4  12.12.19, UK
"""

class mDisplay:
	def __init__(self):
		try:
			# self.sys     = SystemStatus()
			# self.player  = Player(self.sys.check_active)
			self.player  = Player(None)
			self.panel   = FrontPanel()
			self.display = Screens(self.player, self.panel.assignall)

			stamp = datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S %D-%M-%Y')
			print("\n*** mDisplay: v15.1 Successful startup at ", stamp, "***\n")
		except:
			self.cleanup()
			raise

	def run(self):
		""" run indefinately a cycle of:
		- update display in response to changes in player status and new metadata
		- respond to user control events
		"""
		self.display.mainloop()    #event driven control based on Tk model
		self.cleanup()

	def cleanup(self):
		self.player.quit()
		self.panel.quit()




if __name__ == "__main__":
	mediacentre = mDisplay()
	mediacentre.run()
