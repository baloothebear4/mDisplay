#!/usr/bin/env python3
#
# mDisplay Project
#
# v0.1	   30.10.15		Baloothebear4
# v0.2      12.12.19
#
# Module : display.py
# Purpose: Class to manage the interface to the display and handle UI
#
##

#from Tkinter import *
from displaydefs import *
from PIL import Image, ImageTk
from datactrl import PlayerMetadata, PlayList
# from tkColorChooser import askcolor
# from chooserpage import ChooserPage


import time



class Screens(Tk):
    #Build a frame for each screen.  Each screen then has sub-frames to hold the canvas

    def __init__(self, player, panel_event_assign):
        Tk.__init__(self)

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.root = container

        self.player  = player
        self.md      = PlayerMetadata()

        self.title("mDisplay")
        self.wm_overrideredirect(True)  # Switch off the menu
        self.configure(background = DARK)

        self.title_font = ("helvetica", 22, "bold")
        self.large_font = ("helvetica", 22, )
        self.mid_font   = ("helvetica", 16)
        self.small_font = ("helvetica", 12)

        # Set up all of the pages

        # F = mDisplayPage
        # frame = mDisplayPage(container, self, player, panel_event_assign)

        # Set up all of the pages
        self.frames = {}
        for F in (mDisplayPage2, ScreenSaver):
            frame = F(container, self, player, panel_event_assign)
            self.frames[F] = frame
            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        # Start displaying from the Play Page
        self.update_interval = SLOW_UPDATE_TIME
        self.current_frame   = ScreenSaver
        frame = self.frames[self.current_frame]
        frame.tkraise()

        self.update_id = self.frames[self.current_frame].after(FAST_UPDATE_TIME, self.update)
        self.frames[self.current_frame].begin(self.player)

    def show_frame(self, c):
        '''Show a frame for the given class'''
        print("Screens: show_frame: switch from %s to %s" % (self.current_frame.__name__, c.__name__))
        self.frames[self.current_frame].after_cancel(self.update_id)
        frame = self.frames[c]
        self.current_frame = c
        frame.tkraise()
        self.frames[self.current_frame].begin(self.player)
        self.update_id = self.frames[c].after(FAST_UPDATE_TIME, self.update)
        self.update_interval = SLOW_UPDATE_TIME


    def update(self):
        if self.update_interval < SLOW_UPDATE_TIME:
            self.frames[self.current_frame].fast_update(self.player)
            self.update_interval += 1
        else:
            self.frames[self.current_frame].fast_update(self.player)
            self.frames[self.current_frame].slow_update(self.player)
            self.update_interval = 0

        self.update_id = self.frames[self.current_frame].after(FAST_UPDATE_TIME, self.update)

    def play_page(self):
        self.show_frame(mDisplayPage2)

    def screensaver_page(self):
        self.show_frame(ScreenSaver)



class ScreenSaver(Frame):
    def __init__(self, parent, controller, player, panel_event_assign):
        Frame.__init__(self, parent)

        self.metadata    = PlayerMetadata()
        self.player      = player
        self.parent      = parent
        self.controller  = controller
        self.panel_event_assign = panel_event_assign

        Panel        = Frame(self, background= BLACK, width=SCREEN_W, height=SCREEN_H)
        Panel.grid()

        self.screensaver = Image.open(SCREENSAVER).resize((SCREEN_W, SCREEN_H), Image.ANTIALIAS)
        self.canvas      = Canvas(Panel, background=BLACK, width=SCREEN_W, height=SCREEN_H, highlightthickness=0)
        self.canvas.grid(row=0, column=0)
        self.art         = self.canvas.create_image(0, 0, anchor = NW)

    def update_art(self):
        self.canvas.image = ImageTk.PhotoImage(self.screensaver)
        self.canvas.itemconfigure(self.art, image = self.canvas.image, state=NORMAL)

    def screen_blank(self):
        self.canvas.itemconfigure(self.art, state=HIDDEN)

    def fast_update(self, player):
        """ start = time.time()   Use this to decide when to go dark """
        self.metadata    = player.grab()
        if self.metadata.status.state != 'stop':
            self.controller.play_page()

    def slow_update(self, player):
        pass

    def begin(self, player):
        self.update_art()
        self.slow_update(player)
        self.fast_update(player)
        self.canvas.after(BLANK_TIMEOUT, self.screen_blank)
        self.update_idletasks()


class mDisplayPage2(Frame):

    def __init__(self, parent, controller, player, panel_event_assign):
        Frame.__init__(self, parent)

        self.large_font = controller.large_font
        self.mid_font   = controller.mid_font
        self.small_font = controller.small_font

        self.metadata    = PlayerMetadata()
        self.player      = player
        self.parent      = parent
        self.controller  = controller
        self.panel_event_assign = panel_event_assign
        self.knob_isvol  = True         #When false the knob is seeking the track position
        self.vol         = 0.0

        playPanel        = Frame(self, background= DARK, width=SCREEN_W, height=SCREEN_H)
        playPanel.grid()
        self._create_playcanvas(playPanel)


    def _create_playcanvas(self, parent):
        self.metadataC=Frame(parent, background=DARK, width=METADATA_W, height=METADATA_H, highlightthickness=0)
        self.canvas   =Canvas(parent, background=DARK, width=ART_W, height=ART_H, highlightthickness=0)
        self.metadataC.grid(row=0, column=1)
        self.canvas.grid(row=0, column=0)

        self.metadataC.rowconfigure(0, weight=10)
        self.metadataC.rowconfigure(1, weight=3)
        self.metadataC.rowconfigure(2, weight=3)
        self.metadataC.rowconfigure(3, weight=0)
        self.metadataC.rowconfigure(4, weight=0)
        self.metadataC.grid(row=0, column=1)
        self.canvas.grid(row=0, column=0)

        #Create the screen elements
        self.create_coverart()
        self.create_track_metadata()
        self.create_trackpos()
        self.create_quality_metadata()

    def create_coverart(self):
    # large square picture to left of screen
        self.cover_art = self.canvas.create_image(ART_X, ART_Y, anchor = NW)

    def update_coverart(self):
    # large square picture to left of screen
        if self.metadata.track.coverart.exists:
            self.canvas.image = ImageTk.PhotoImage(self.metadata.track.coverart.large_image)
            self.canvas.itemconfigure(self.cover_art, image = self.canvas.image, state=NORMAL)
        else:
            self.canvas.itemconfigure(self.cover_art, state=HIDDEN)

    def create_trackpos(self):
    # linear track position marker
        self.trackposC   =  Canvas(self.metadataC, background=DARK, width=METADATA_W, height=TRACK_POS_H, highlightthickness=0)
        self.track_base  =  self.trackposC.create_rectangle (POS_X, POS_Y, POS_X+LIN_DIAL_W, POS_Y+LIN_DIAL_H, fill=MID)
        self.track_pos   =  self.trackposC.create_rectangle (POS_X, POS_Y, POS_X, POS_Y+LIN_DIAL_H, fill=POSMARK)
        self.track_mark  =  self.trackposC.create_oval (MARK_X, MARK_Y, MARK_X+MARKER_W, MARK_Y+MARKER_H, fill=POSMARK)
        self.play_text   =  self.trackposC.create_text(POS_X, POS_Y, font=self.small_font, fill=POSMARK, anchor= E)
        self.play_dur    =  self.trackposC.create_text(POS_X+LIN_DIAL_W, POS_Y, font=self.small_font, fill=NUMCOL, anchor=W)

        self.shuffle_metadata  = self.trackposC.create_text(POS_X+SR_OFFSET_X, POS_Y+SR_OFFSET_Y, font=self.small_font, anchor= E, fill=SHUFFLECOL)
        self.repeat_metadata   = self.trackposC.create_text(POS_X+LIN_DIAL_W-SR_OFFSET_Y, POS_Y+SR_OFFSET_Y, fill=REPEATCOL, anchor=W, font=self.small_font)

        self.trackposC.grid(row=3, column=1,sticky=N)


    def update_trackpos(self):
        p2 = (self.metadata.status.elapsedpc)* LIN_DIAL_W

        self.trackposC.coords(self.track_base, POS_X+p2, POS_Y, POS_X+LIN_DIAL_W, POS_Y+LIN_DIAL_H)
        self.trackposC.coords(self.track_pos, POS_X, POS_Y, POS_X+p2, POS_Y+LIN_DIAL_H)
        self.trackposC.coords(self.track_mark, MARK_X+p2, MARK_Y, MARK_X+p2+MARKER_W, MARK_Y+MARKER_H)
        self.trackposC.itemconfigure(self.track_base, state=NORMAL)
        self.trackposC.itemconfigure(self.track_pos, state=NORMAL)
        self.trackposC.itemconfigure(self.track_mark, state=NORMAL)

        m, s   = divmod(float(self.metadata.status.elapsed), 60)
        dm, ds = divmod(float(self.metadata.status.duration), 60)
        if self.metadata.status.state != 'stop':
            self.trackposC.itemconfigure(self.play_text, text = '%2d:%02d' % (m, s), state=NORMAL)
            if dm == 0:
                self.trackposC.itemconfigure(self.play_dur, text = '%2d:%02d' % (dm, ds), state=HIDDEN)
            else:
                self.trackposC.itemconfigure(self.play_dur, text = '%2d:%02d' % (dm, ds), state=NORMAL)

            # self.canvas.itemconfigure(self.play_title, text = 'Playing song %d of %d' % (self.metadata.status.songpos+1, self.metadata.status.PlayList.length), state=NORMAL)
        else:
            self.trackposC.itemconfigure(self.play_text, state=HIDDEN)
            self.trackposC.itemconfigure(self.play_dur, state=HIDDEN)
            self.trackposC.itemconfigure(self.track_base, state=HIDDEN)
            self.trackposC.itemconfigure(self.track_pos, state=HIDDEN)
            self.trackposC.itemconfigure(self.track_mark, state=HIDDEN)

        if self.metadata.status.shuffle:
            self.trackposC.itemconfigure(self.shuffle_metadata, text = 'Shuffle' )
        else:
            self.trackposC.itemconfigure(self.shuffle_metadata, text = '' )

        if self.metadata.status.repeat:
            self.trackposC.itemconfigure(self.repeat_metadata, text = 'Repeat' )
        else:
            self.trackposC.itemconfigure(self.repeat_metadata, text = '' )

    def create_track_metadata(self):
        self.track_title    = Label(self.metadataC,fg=TEXTCOL, anchor=N, wraplength=METADATA_W, background=DARK, justify = CENTER,  font=self.large_font)#,  fill=TEXTCOL)
        self.track_title.grid(row=0, column=1,sticky=N)

        self.track_artist   = Label(self.metadataC, fg=LIGHT,anchor=N, wraplength=METADATA_W, bg=DARK, justify = CENTER, font=self.mid_font)
        self.track_artist.grid(row=1, column=1)

        self.track_album    = Label(self.metadataC, fg=TEXTCOL, anchor=N, wraplength=METADATA_W, bg=DARK, justify = CENTER, font=self.mid_font)
        self.track_album.grid(row=2, column=1)

    def update_track_metadata(self):
        self.track_title.configure(text =  self.metadata.track.song )
        self.track_artist.configure(text = self.metadata.track.artist)
        self.track_album.configure(text = self.metadata.track.album)

    def create_quality_metadata(self):
        self.source_metadata   = Label(self.metadataC, text="", fg=MID, bg=DARK, font=self.small_font)
        self.source_metadata.grid(row=5, column=1,sticky=S)
        self.quality_metadata  = Label(self.metadataC, text="",fg=MID, bg=DARK, font=self.small_font)
        self.quality_metadata.grid(row=4, column=1,sticky=S)


    def update_quality_metadata(self):
        if self.metadata.status.samplerate > 1000:
            samplerate = float(self.metadata.status.samplerate)/1000
        else:
            samplerate = float(self.metadata.status.samplerate)

        if self.metadata.status.state != 'stop':
            show = "%4.0fkbps   %3.1fkHz   %2dbit   %4s" % (self.metadata.status.bitrate, samplerate, self.metadata.status.bitsize,self.metadata.track.type)
        else:
            show = ''
        self.quality_metadata.configure(text = show )

        if self.metadata.track.origin is None:
            origin = ''
        else:
            origin = ' from %s' % self.metadata.track.origin

        if self.metadata.status.state == 'play':
            status = 'Playing%s' % origin
        elif self.metadata.status.state == 'pause':
            status = 'Paused%s' % origin
        else:
            status = 'Stopped'
            self.controller.screensaver_page()
        self.source_metadata.configure(text = status )

    def fast_update(self, player):
        self.metadata = player.grab()
        self.update_trackpos()
        if self.metadata.track.new_track:
            self.slow_update(player)
        self.update_idletasks()


    def slow_update(self, player):
        self.metadata = player.grab()
        self.update_quality_metadata()
        self.update_track_metadata()
        self.update_coverart()

    def begin(self, player):
        self.slow_update(player)
        self.fast_update(player)

if __name__== '__main__':
    #root=Tk()
    scr=Screens()
    scr.mainloop()
