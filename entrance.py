#!/usr/bin/env python

import time
import logging
import ctypes
import string
import nfc
import spotify
import threading
import os
import json
import urllib2
from NFCReader import NFCReader

# put these in a config file please
ENTRANCE_LENGTH = 30
WEB_SERVICE = "https://entrancemusic.herokuapp.com/cards/getcard"

# connect to the web service and get the track link
def get_track_online(id):
  url = WEB_SERVICE + "/" + id
  res = json.load(urllib2.urlopen(url))
  print res
  return res[0]['track']

# spotify stuff
def on_connection_state_updated(session):
  if session.connection.state is spotify.ConnectionState.LOGGED_IN:
    logged_in.set()

def on_end_of_track(self):
  end_of_track.set()

def play(track_uri):
  # can move this into initialize for preload
  print "Loading",track_uri
  track = session.get_track(track_uri).load(timeout=30)
  session.player.load(track)
  print "Play"
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

if __name__ == '__main__':
    logger = logging.getLogger("cardhandler").info

    # spotify
    session.on(
      spotify.SessionEvent.CONNECTION_STATE_UPDATED, on_connection_state_updated)
    session.on(spotify.SessionEvent.END_OF_TRACK, on_end_of_track)
    session.login(os.environ["SPOTIFY_USER"], os.environ["SPOTIFY_PASS"] )
    logged_in.wait()
    
    nfcr = NFCReader(logger)

    print "OK GO"
    while nfcr.run():
        card_id = nfcr.card_id()
        if card_id != None:
          print "Got back card id:",card_id
          track = get_track_online(card_id)
          play(track)
        time.sleep(0.1)
        pass
