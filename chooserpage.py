#!/usr/bin/env python
#
# mVista Project
#
# v0.1	   30.11.15		Baloothebear4
#
# Module : chooserpage.py
# Purpose: Base classes to handle the UI interactions for choosing and selecting
#
##
from displaydefs import *
#from Tkinter import *
from PIL import Image, ImageTk


class ChooserPage(Frame):
    """ base class used for list based screens """

    def __init__(self, parent, controller, player, panel_event_assign, buttons):
        Frame.__init__(self, parent)

        self.large_font = controller.large_font
        self.mid_font   = controller.mid_font
        self.small_font = controller.small_font
        self.largemid_font   = ("helvetica", 18)

        self.selectpos = 0   # this is where
        self.player    = player
        self.selection_made = False
        self.panel_event_assign = panel_event_assign
        self.controller = controller
        self.parent     = parent
        self.seektimer  = None
        self.buttons    = {}
        self.button_config = buttons

        buttonPanel = Frame(self, width=BUTTON_W, height=BUTTON_H)
        playPanel = Frame(self, width=SCREEN_W, height=SCREEN_H)
        buttonPanel.pack(side="bottom", fill="y", expand=True)
        playPanel.pack(side="top", fill="both", expand=True)

        # fill in these two areas:
        self._create_choosercanvas(playPanel)
        self._create_chooserbuttons(buttonPanel,controller)

    def set_bindings(self):
        panel_events = self.panel_event_assign(self.panel_event)
        self.bind('<<KnobButton-ShortPress>>', self.select )
        self.bind('<<MainKnob-Clockwise>>', self.fwd )
        self.bind('<<MainKnob-Anticlockwise>>', self.back )
        for n in self.buttons:
            self.buttons[n].set_bindings(self.bind)
            self.buttons[n].reset()

    def _create_chooserbuttons(self, parent,controller):
        for button_name in self.button_config:
            self.buttons.update( {button_name : mButton(parent, button_name, self.mid_font, self.button_config[button_name]) } )
            self.buttons[button_name].grid(row = 0,column = self.button_config[button_name]['position'], sticky = W+E)
            parent.grid_columnconfigure(self.button_config[button_name]['position'], weight=1, minsize=BUTTON_SIZE)

    def panel_event(self, ev):
        #print "ChoosePage: Panel event %s" % ev
        self.event_generate(ev)

    def back(self,ev=None):
        #print "ChoosePage : back : selectpos %d : playlistlen %d" % (self.selectpos, self.playlist.length)
        if self.selectpos >0:
            self.selection_made = True
            self.selectpos -= 1
            self.update_selection(self.selectpos)

    def fwd(self, ev=None):
        #print "ChoosePage : fwd : selectpos %d : playlistlen %d" % (self.selectpos, self.playlist.length)
        if self.selectpos < self.playlist.length-1:
            self.selection_made = True
            self.selectpos += 1
            self.update_selection(self.selectpos)

    def start_list(self, plist, pos, player):
        self.selection_made = False
        self.playlist  = plist
        self.selectpos = pos
        self.set_bindings()

    def _create_choosercanvas(self, parent):
        self.canvas=Canvas(parent, background=DARK, width=SCREEN_W, height=SCREEN_H)
        self.canvas.grid(row=1, column=1, sticky="nsew")

        #Create the screen elements
        self.create_selection()

        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

    def create_selection(self):
        self.listitem = []
        line_col            = DARK
        self.title          = self.canvas.create_text(PLAYLIST_ARTIST_X, PLAYLIST_ARTIST_Y, text='Building list', justify = CENTER, width = SELECT_W, font=self.largemid_font, anchor=N, fill=TEXTCOL)
        self.description    = self.canvas.create_text(PLAYLIST_ARTIST_X, PLAYLIST_ALBUM_Y, text='', justify = CENTER, width = SELECT_W, font=self.mid_font, anchor=N, fill=LIGHT)
        self.cover_art      = self.canvas.create_image(PLAYART_X, PLAYART_Y, anchor = CENTER)
        for id in range(CHOOSERLEN):
            self.listitem.append( self.canvas.create_text(CHOOSER_X, CHOOSER_Y+id*CHOICE_W, text='', justify = LEFT, width = CHOOSER_W, font=self.largemid_font, anchor=W, fill=MID) )

    def update_selection(self, pos):
        if self.playlist.length > 0:
            if not self.selection_made:    # this is so that the playlist page will update whilst playing, but not lose any selection that has been made
                self.selectpos = pos
            start_item = self.selectpos - CHOOSERLEN/2
            self.canvas.itemconfigure(self.title, text='%s' % (self.playlist.title(self.selectpos)), state=NORMAL )
            self.canvas.itemconfigure(self.description, text='%s' % (self.playlist.description(self.selectpos)), state=NORMAL )
            self.update_coverart(self.playlist.coverart(self.selectpos))
        else:
            start_item = CHOOSERLEN/2
            self.canvas.itemconfigure(self.title, text='No playlist available', state=NORMAL )
            self.canvas.itemconfigure(self.description, state=HIDDEN )
            self.update_coverart(self.playlist.coverart(self.selectpos))
        #print "ChooserPage : update_selection : select pos %d : start_item %d " % (self.selectpos, start_item)
        for id in range(CHOOSERLEN):
            if start_item + id < 0:
                self.canvas.itemconfigure(self.listitem[id], text='' )
            elif start_item + id ==  self.selectpos:
                line = "%-3d %s" % (start_item+id+1, self.playlist.item(start_item+id))
                self.canvas.itemconfigure(self.listitem[id], text=line, fill=TEXTCOL)
            elif start_item + id >= self.playlist.length:
                self.canvas.itemconfigure(self.listitem[id], text='' )
            else:
                line = "%-3d %s" % (start_item+id+1, self.playlist.item(start_item+id))
                self.canvas.itemconfigure(self.listitem[id], text=line, fill=MID)

    def slow_update(self, player):
        pass

    def update_coverart(self, art):
        if art != None and art.exists:
            self.canvas.image = ImageTk.PhotoImage(art.small_image)
            self.canvas.itemconfigure(self.cover_art, image = self.canvas.image, state=NORMAL)
        else:
            self.canvas.itemconfigure(self.cover_art, state=HIDDEN)
