#!/usr/bin/env python
#
# mVista Project
#
# v0.1	   30.11.15		Baloothebear4
#
# Module : displaydefs.py
# Purpose: Definition of the parameters that defines the display
#
##
from tkinter import * #SUNKEN, Button, CENTER
# import tkinter
# Assume 0,0 is Upper Left corner
#Set overall Screen size
WINDOW_W = 800
WINDOW_H = 480
LR_MARGIN = 0
TOP_MARGIN = 0
DIAL_H   = 150
DIAL_W   = 150
DARK     = '#000020'
MID      = '#9088FF'
LIGHT    = '#0040FF'
TEXTCOL  = 'white'
POSMARK  = LIGHT
SHUFFLECOL = 'orange'
REPEATCOL  = 'yellow'
BLACK    = 'black'
NUMCOL   = MID

#Screen Canvas
SCREEN_W   = WINDOW_W
SCREEN_H   = WINDOW_H

ART_W  	   = SCREEN_H   #note this is duplicated in coverart file!!!
ART_H  	   = ART_W
METADATA_W = SCREEN_W - ART_W
METADATA_H = SCREEN_H

# Linear Track position
TRACK_POS_H= 60
LIN_DIAL_H = 5
LIN_DIAL_W = METADATA_W * 2/3
MARKER_W   = LIN_DIAL_H * 3
MARKER_H   = LIN_DIAL_H * 3

SR_OFFSET_Y  = 16
SR_OFFSET_X  = 10

# Volume Dial sits under the metadata
LIN_VOL_H  = LIN_DIAL_H
LIN_VOL_W  = METADATA_W/2
VOL_POS_H  = 30

#Position of Coverart Frame
BOTTOM_MARGIN = LR_MARGIN


ART_X  = LR_MARGIN
ART_Y  = LR_MARGIN + (SCREEN_H-ART_H)/2

#Other metadata

TEXT_SPACING        = 25
CONTROLS_X          = ART_X + ART_W + LR_MARGIN + (SCREEN_W - (ART_X + ART_W + LR_MARGIN))/2
CONTROLS_Y          = LR_MARGIN


#Position of Track metadata  -  this can span the whole width if necessary and is left justified
TITLE_METADATA_H    = 50
TRACK_TITLE_W       = SCREEN_W - LR_MARGIN - ART_W
TRACK_TITLE_X       = CONTROLS_X
TRACK_TITLE_Y       = CONTROLS_Y
TRACK_METADATA_X    = CONTROLS_X
TRACK_ARTIST_Y      = TRACK_TITLE_Y + TEXT_SPACING *4
TRACK_ALBUM_Y       = TRACK_ARTIST_Y + TEXT_SPACING * 4

#Position of Track Dial
PLAY_X              = CONTROLS_X - DIAL_W/2
PLAY_Y              = TRACK_ALBUM_Y + TEXT_SPACING * 2
PLAY_THK            = 30

#Position of quality metadata
QUALITY_METADATA_X  = TRACK_METADATA_X
QUALITY_METADATA_Y  = SCREEN_H - (2.5*TEXT_SPACING)
SOURCE_METADATA_X   = TRACK_METADATA_X
SOURCE_METADATA_Y   = QUALITY_METADATA_Y + TEXT_SPACING

REPEAT_METADATA_X   = TRACK_METADATA_X
REPEAT_METADATA_Y   = PLAY_Y + DIAL_H - TEXT_SPACING
SHUFFLE_METADATA_X  = TRACK_METADATA_X
SHUFFLE_METADATA_Y  = PLAY_Y + TEXT_SPACING


#Chooser parameters
CHOOSERLEN         = 11   # number of items in the Chooser
CHOOSER_W          = 0
CHOICE_W           = 40
CHOOSER_X          = 300
CHOOSER_Y          = LR_MARGIN
PLAYLIST_ALBUM_Y   = 350
PLAYLIST_ARTIST_Y  = 25
PLAYLIST_ALBUM_X   = CHOOSER_X/2
PLAYLIST_ARTIST_X  = PLAYLIST_ALBUM_X
SELECT_W           = 270
PLAYART_X          = CHOOSER_X/2
PLAYART_Y          = SCREEN_H/2

#Position of 3 control buttons
NUMBUTTONS = 5
BUTTON_W = WINDOW_W
BUTTON_H = WINDOW_H/10
BUTTON_SIZE = 1+BUTTON_W/NUMBUTTONS
BUTTON_EVEN_COLOUR = MID
BUTTON_ODD_COLOUR = DARK
BUTTON_TEXT_COLOUR = LIGHT
BUTREL = SUNKEN

#Backwards compatability
POS_X       = (METADATA_W - LIN_DIAL_W)/2
POS_Y       = (TRACK_POS_H + LIN_DIAL_H)/2
MARK_X      = POS_X - MARKER_W/2
MARK_Y      = POS_Y - (MARKER_H - LIN_DIAL_H)/2

#Other metadata
TEXT_SPACING        = 25
CONTROLS_X          = ART_X + ART_W + LR_MARGIN

TRACK_METADATA_X    = CONTROLS_X + WINDOW_W/4
TRACK_ARTIST_Y      = ART_Y
TRACK_ALBUM_Y       = ART_Y + TEXT_SPACING *2


#Position of Volume control
VOLUME_X            = CONTROLS_X + WINDOW_W/4+LR_MARGIN
VOLUME_Y            = ART_Y + ART_H/3
VOL_THK             = 30    #How thick is the volume knob


#Refresh periods - fast and slow depending on the frequency of change
FAST_UPDATE_TIME    = 100   #ms
SLOW_UPDATE_TIME    = 5     # number of fast update intervals
SEEKIDLETIME        = 5000  # how long to wait if seeking is idle to switch back to volume mode
LONG_PRESS_INTERVAL = 1000
BLANK_TIMEOUT       = (60*1000)*15  #ie 15 mins

CLOCKWISE           = 1
ANTICLOCKWISE       = 2
UP                  = 1
DOWN                = -1
FWDS                = 2
BWDS                = -2

""" Icons """
PLAY_ICON = 'icons/play.ico'
FWD_ICON = 'icons/fwd.ico'
BACK_ICON = 'icons/back.ico'
PAUSE_ICON = 'icons/pause.ico'
STOP_ICON = 'icons/stop.ico'
UP_ICON = 'icons/up.ico'
DOWN_ICON = 'icons/down.ico'
AIRPLAY_ICON = 'icons/airplay.ico'
BLANK_ICON = 'icons/blank.ico'
SCREENSAVER = 'icons/mDisplay_saver.jpg'

TITLE_FONT = ("Helvetica", 18, "bold")

class mButton(Button):
    """ Abstraction class to add the functionality to provide visible feedback to the user
        on the state of button presses, eg press causes highlight, longer press signals
        the long press command. Also assures common look and feel across all buttons.

        Each button can have a short press and long press callback function.  This class
        indicates to the user the progression through the states as the button is held down: ie
            - pressed, button highlighted
            - released, shortpress callback called
            - held, second function title
            - released, longpress callback called
            - return to normal state
    """
    def __init__(self, parent, name, font, config):

        self.name           = name
        self.parent         = parent
        self.short_callback = config['short_callback']
        self.long_callback  = config['long_callback']
        self.short_event    = config['short_event']
        self.long_event     = config['long_event']   # set this to '' to avoid long press activity
        self.down_event     = config['down_event']
        self.short_img      = config['short_img']
        self.long_img       = config['long_img']
        self.short_text     = config['short_text']
        self.long_text      = config['long_text']
        self.down_timer     = None
        #print 'mButton : init : %s : short %s : long %s : down %s' % (self.name, self.short_event, self.long_event, self.down_event)

        if config['even']:
            self.colour = BUTTON_EVEN_COLOUR
        else:
            self.colour = BUTTON_ODD_COLOUR
        Button.__init__(self, parent,text=self.short_text, image=self.short_img, command=self.short_event, compound=CENTER,font=font, fg=BUTTON_TEXT_COLOUR, bg=self.colour, relief=BUTREL, borderwidth=0)


    def set_bindings(self, binder):
        #print 'mButton : set_binds : %s' % self.name
        self.bind('<Button-1>', self.short_callback)  # bind the mouse buttons to the button callbacks
        if self.long_event != '' : self.bind('<Button-3>', self.long_callback)
        binder(self.short_event, self.short_press )
        binder(self.down_event, self.down_press )
        if self.long_event != '' : binder(self.long_event, self.long_press )

    def down_press(self,ev=None):         # called when down press has occured, button is highlighted
        #print 'mButton : down_press : %s : state %s' % (self.name, self.cget('state'))
        if self.cget('state') != 'active':  #if button has bounced button will already be active so ignore
            self.configure(state=ACTIVE)
            if self.long_event != '' : self.down_timer = self.after(LONG_PRESS_INTERVAL,self.indicate_second)
            self.parent.update_idletasks()
        else:
            print ('mButton : down_press : %s : switch bounce' % (self.name))
            self.reset()

    def indicate_second(self):    # called when the down timer expires ie long press happening
        #print 'mButton : indicate_second : %s' % self.name
        self.configure(image=self.long_img, text=self.long_text, state=ACTIVE)
        self.parent.update_idletasks()

    def short_press(self,ev=None):
        #print 'mButton : short_event : %s' % self.name
        self.reset()
        self.short_callback()

    def long_press(self,ev=None):
        #print 'mButton : long_event : %s' % self.name
        self.reset()
        self.long_callback()

    def reset(self):  #  returns the button back to the normal state
        #print 'mButton : reset : %s' % self.name
        self.configure(image=self.short_img, text=self.short_text, state=NORMAL)
        if self.down_timer is not None: self.after_cancel(self.down_timer)
        self.parent.update_idletasks()

class LinDial():
    def __init__(self, base, width, height, frame_height, font):
    # linear track position marker
        self.POS_X       = (METADATA_W - width)/2
        self.POS_Y       = (frame_height + LIN_DIAL_H)/2
        self.MARK_X      = self.POS_X - MARKER_W/2
        self.MARK_Y      = self.POS_Y - (MARKER_H - LIN_DIAL_H)/2
        self.width       = width
        self.height      = height
        self.base        = base
        self.track_base  =  self.base.create_rectangle (self.POS_X, self.POS_Y, self.POS_X+self.width, self.POS_Y+self.height, fill=MID)
        self.track_pos   =  self.base.create_rectangle (self.POS_X, self.POS_Y, self.POS_X, self.POS_Y+self.height, fill=POSMARK)
        self.track_mark  =  self.base.create_oval (self.MARK_X, self.MARK_Y, self.MARK_X+MARKER_W, self.MARK_Y+MARKER_H, fill=POSMARK)
        self.text_left   =  self.base.create_text(self.POS_X, self.POS_Y, font=font, fill=POSMARK, anchor= E)
        self.text_right  =  self.base.create_text(self.POS_X+self.width, self.POS_Y, font=font, fill=NUMCOL, anchor=W)

    def update(self, left, right, show, pc, show_right=True):

        self.base.coords(self.track_base, self.POS_X+pc*self.width, self.POS_Y, self.POS_X+self.width, self.POS_Y+self.height)
        self.base.coords(self.track_pos, self.POS_X, self.POS_Y, self.POS_X+pc*self.width, self.POS_Y+self.height)
        self.base.coords(self.track_mark, self.MARK_X+pc*self.width,self.MARK_Y, self.MARK_X+pc*self.width+MARKER_W, self.MARK_Y+MARKER_H)
        self.base.itemconfigure(self.track_base, state=NORMAL)
        self.base.itemconfigure(self.track_pos, state=NORMAL)
        self.base.itemconfigure(self.track_mark, state=NORMAL)

        if show:
            self.base.itemconfigure(self.text_left, text = left, state=NORMAL)
            if show_right:
                self.base.itemconfigure(self.text_right, text = right, state=HIDDEN)
            else:
                self.base.itemconfigure(self.text_right, text = right, state=NORMAL)
        else:
            self.base.itemconfigure(self.text_left, state=HIDDEN)
            self.base.itemconfigure(self.text_right, state=HIDDEN)
            self.base.itemconfigure(self.track_base, state=HIDDEN)
            self.base.itemconfigure(self.track_pos, state=HIDDEN)
            self.base.itemconfigure(self.track_mark, state=HIDDEN)
