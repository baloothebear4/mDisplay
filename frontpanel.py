#!/usr/bin/env python
#
# mVista Project
#
# v0.1	   Baloothebear4   10/11/15
#
# Module : frontpanel.py
# Purpose: encapsulates the Hardware control device interface and presents the button and rotary
#		devises as virtual controls that trigger events.  The display application manages the
#		context of the controls.
#
##


import time 			     # used for hardware interface and event management
import RPi.GPIO as GPIO


#to translate generic button and rotary control interfaces to the specific implementation as created in HW

GPIO_BUTTON_MAPPING = { 'KnobButton' 	: 11,
						'PanelButton1' 	: 7,
						'PanelButton2' 	: 8,
						'PanelButton3' 	: 10,
						'PanelButton4' 	: 13 }
#						'PanelButton5' 	: 13 }

GPIO_ROTARY_MAPPING = (16, 18)       # left and right pins
KNOBNAME			= 'MainKnob'
										   	 # only the application knows what the button do
BOUNCETIME 	   		= 100
KNOBBOUNCETIME 		= 10

BUTTONDOWN     		= 0
BUTTONUP       		= 1

LONG_PRESS_INTERVAL = 1.0

WARNINGS   			= False


class ButtonSwitch:
	""" Handles the creation and binding of button press events to handlers.
	Provides the low level interface to perform.  Each button is capable of
	generating a short and long press event
	"""

	def __init__(self, pin, ref):
		# could be a detect on FALLING but if long presses are required then this wont work
		self.pin    		= pin
		self.shortevent		= 'shortpress - not assigned'
		self.longevent		= 'longpress - not assigned'
		self.downevent		= 'downpress - not assigned'
		self.short_handler	= self.null_handler   #button presses do nothing until handlers are assigned
		self.long_handler	= self.null_handler
		self.down_handler	= self.null_handler
		self.name			= ref
		self.press_time		= 0.0

		# GPIO setup functions
		GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)   # so ground the switch to activate
		#print ( "new button %s, pin %d " % (self.name, self.pin)

	def name(self):
		return self.name

	def assign(self, callback, type):
		# GPIO event mappings causing  fn callback, when

		if type =='long':
			self.long_handler = callback
			self.longevent = '<<%s-%s>>' % (self.name, 'LongPress')
		elif type == 'short':
			self.short_handler  = callback
			self.shortevent = '<<%s-%s>>' % (self.name, 'ShortPress')
		elif type == 'down':
			self.down_handler  = callback
			self.downevent = '<<%s-%s>>' % (self.name, 'DownPress')
		else:
			print ( "ButtonSwitch: assign : type not known %s " % type)

		GPIO.remove_event_detect(self.pin)
		GPIO.add_event_detect(self.pin, GPIO.BOTH, callback=self.switch_press, bouncetime=BOUNCETIME)
		#print ( "assigned "+ task

	def events(self, type):
		if type == 'long':
			return self.longevent
		elif type == 'short':
			return self.shortevent
		elif type == 'down':
			return self.downevent
		else:
			print ( "ButtonSwitch: events : type not known %s " % type)



	def switch_press(self,event):
		#print ( "Pin %d pressed" % event
		if self.get_switch_state() == BUTTONDOWN:
			self.press_time = time.time()
			self.down_handler(self.downevent)
			#print ( "Start timer event "+str(event)
		else:
			t = time.time() - self.press_time
			#print ( "time "+ str(t)
			if t <= LONG_PRESS_INTERVAL:
				self.short_handler(self.shortevent)
			else:
				self.long_handler(self.longevent)

	# Get a switch state
	def get_switch_state(self):
		state = GPIO.input(self.pin)
		#print ( "ButtonSwitch: Switch state %d" % state
		return  state

	def null_handler(self,event):
		print ( "No handler for event %s" % event)
		pass

	def __str__(self):
		text  = '%25s : %s\n' % ('Button name', self.name)
		text += '%25s : %d\n' % ('Pin', self.pin)
		text += '%25s : %s\n' % ('Short event', self.shortevent)
		text += '%25s : %s\n' % ('Long event', self.longevent)
		text += '%25s : %s\n' % ('Down event', self.downevent)
		text += '%25s : %s\n' % ('Long callback', self.long_handler)
		text += '%25s : %s\n' % ('Short callback', self.short_handler)
		text += '%25s : %s\n' % ('Down callback', self.down_handler)
		return text

class RotaryKnob:

	CLOCKWISE=1
	ANTICLOCKWISE=2

	rotary_a = 0
	rotary_b = 0
	rotary_c = 0
	last_state = 0
	direction = 0
	TURN      = { CLOCKWISE : 'Clockwise', ANTICLOCKWISE : 'Anticlockwise'}

	# Initialise rotary encoder object
	def __init__(self,name, pins):
		self.pinA = pins[0]
		self.pinB = pins[1]
		self.name = name
		self.handler = None
		self.clockwiseevent = '<<%s-%s>>' % (self.name, self.TURN[self.CLOCKWISE])
		self.anticlockwiseevent = '<<%s-%s>>' % (self.name, self.TURN[self.ANTICLOCKWISE])

		# The following lines enable the internal pull-up resistors
		GPIO.setup(self.pinA, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(self.pinB, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	def assign(self, callback, type=''):
		# fast argument is used to change the nature of the rotary -  not implemented
		self.handler = callback
		# Add event detection to the GPIO inputs

		self.unassign()
		GPIO.add_event_detect(self.pinA, GPIO.FALLING, callback=self.turn_event, bouncetime=KNOBBOUNCETIME)
		GPIO.add_event_detect(self.pinB, GPIO.FALLING, callback=self.turn_event, bouncetime=KNOBBOUNCETIME)

	def unassign(self):
		GPIO.remove_event_detect(self.pinA)
		GPIO.remove_event_detect(self.pinB)

	def name(self):
		return self.name

	# Call back routine called by switch events
	def turn_event(self,switch):
		if GPIO.input(self.pinA):
			self.rotary_a = 1
		else:
			self.rotary_a = 0

		if GPIO.input(self.pinB):
			self.rotary_b = 1
		else:
			self.rotary_b = 0

		self.rotary_c = self.rotary_a ^ self.rotary_b
		new_state = self.rotary_a * 4 + self.rotary_b * 2 + self.rotary_c * 1
		delta = (new_state - self.last_state) % 4
		self.last_state = new_state
		event = 0

		if delta == 1:
			if self.direction == self.CLOCKWISE:
				# print ( "Clockwise"
				event = self.direction
			else:
				self.direction = self.CLOCKWISE
		elif delta == 3:
			if self.direction == self.ANTICLOCKWISE:
				# print ( "Anticlockwise"
				event = self.direction
			else:
				self.direction = self.ANTICLOCKWISE
		if event > 0:
			self.handler('<<%s-%s>>' % (self.name, self.TURN[event]) )

	def events(self, long=False):
		if long:
			return self.clockwiseevent
		else:
			return self.anticlockwiseevent

	def __str__(self):
		text  = '%25s : %s\n' % ('Rotary name', self.name)
		text += '%25s : %d\n' % ('Pin A', self.pinA)
		text += '%25s : %d\n' % ('Pin B', self.pinB)
		text += '%25s : %s\n' % ('callback', self.handler)
		return text


class FrontPanel(ButtonSwitch, RotaryKnob):
	"""
	establishes the interface between the Hardware layout of buttons
	and controls, to the virtual controls and event handlers
	"""

	def __init__(self):
		#Create all buttons, mapping them to the correct GPIO pins, in long and short instances
		GPIO.setmode(GPIO.BOARD)  # sets whether absolute or BCM virtual pin channels are used BOARD => physical
		GPIO.setwarnings(WARNINGS)

		self.controls = {}

		# for name, pin in GPIO_BUTTON_MAPPING.iteritems():
		# print("FrontPanel - removed as not compiling")
		for name, pin in GPIO_BUTTON_MAPPING.items():
			new_button = ButtonSwitch(pin, name)
			self.controls.update( {name : new_button } )

		self.controls.update( {KNOBNAME : RotaryKnob(KNOBNAME, GPIO_ROTARY_MAPPING) } )

	def controls(self):
		return self.controls

	def assign(self, name, callback, long_type=False):
		self.controls[name].assign(callback, long_type)

	def assignall(self, callback):
		#bind all the panel events to a display handler (that in turn raises a tk event)
		for name in self.controls:
			self.assign(name, callback, 'long')
			self.assign(name, callback, 'short')
			self.assign(name, callback, 'down')
		return self.events()

	def events(self):
		ev = []
		for name in self.controls:
			ev.append(self.controls[name].events('short'))
			ev.append(self.controls[name].events('long'))
			ev.append(self.controls[name].events('down'))
		return ev

	def __str__(self):
		text  = 'FrontPanel\n'
		for name in self.controls:
			text += str(self.controls[name])
		return text

	def quit(self):

		GPIO.cleanup()


def panelevent(ev):
	print ( "%s" % ev)

if __name__ == '__main__':
	try:
		p = FrontPanel()
		# p.assign('PanelButton1', panelevent)
		# p.assign('PanelButton1', panelevent, long_type=True)
		# p.assign('PanelButton2', panelevent)
		# p.assign('PanelButton3', panelevent)
		# p.assign('PanelButton4', panelevent)
		# p.assign('MainKnob', panelevent)
		# p.assign('KnobButton', panelevent)
		# p.assign('KnobButton', panelevent, long_type=True)
		p.assignall(panelevent)
		print ("Panel assigned\n" + str(p))
		ev = p.events()
		print (ev)

		while True:
			time.sleep(3)
			#print ( b
	except:
		GPIO.cleanup()
		raise
