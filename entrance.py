#!/usr/bin/env python

## Ok so I'm taking the pynfc sample code and putting my own crap in

#  Pynfc is a python wrapper for the libnfc library
#  Copyright (C) 2009  Mike Auty
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import time
import logging
import ctypes
import string
import nfc
import spotify
import threading
import os
from NFCReader import NFCReader

# hardcode some entrance music for now - eventually put this in a db
music = { '91ab290f': 'https://open.spotify.com/track/7c6gwmXP64tmpbmA86wHIk',
          '6d839875': 'https://open.spotify.com/track/35bgx24EQeW7IiA4nFXivH' }
ENTRANCE_LENGTH = 30


# spotify stuff
def on_connection_state_updated(session):
  if session.connection.state is spotify.ConnectionState.LOGGED_IN:
    logged_in.set()

def on_end_of_track(self):
  end_of_track.set()

def play(track_uri):
  # can move this into initialize for preload
  print "Playing",track_uri
  track = session.get_track(track_uri).load(timeout=30)
  session.player.load(track)
  session.player.play()
  # don't play whole track - just let it background play for a predefined amount of time, then stop
  time.sleep(ENTRANCE_LENGTH)
  print "Done playing!"
  pause()

def pause():
  session.player.pause()

# Assuming a spotify_appkey.key in the current dir
session = spotify.Session()

# Process events in the background
loop = spotify.EventLoop(session)
loop.start()

# Connect an audio sink
audio = spotify.PortAudioSink(session)

# Events for coordination
logged_in = threading.Event()
end_of_track = threading.Event()

# nfc stuff

def hex_dump(string):
    """Dumps data as hexstrings"""
    return ' '.join(["%0.2X" % ord(x) for x in string])
if __name__ == '__main__':
    logger = logging.getLogger("cardhandler").info

    # spotify
    session.on(
      spotify.SessionEvent.CONNECTION_STATE_UPDATED, on_connection_state_updated)
    session.on(spotify.SessionEvent.END_OF_TRACK, on_end_of_track)
    session.login(os.environ["SPOTIFY_USER"], os.environ["SPOTIFY_PASS"] )
    logged_in.wait()
    
    nfcr = NFCReader(logger)

    while nfcr.run():
        card_id = nfcr.card_id
        if card_id != None:
          print "Got back card id:",card_id
          play(music[card_id])
          nfcr.card_id = None
        pass
