#!/usr/bin/env python

import json
import logging
import os
import signal
import spotify
import string
import sys
import threading
import time
import urllib2
import yaml

from NFCReader import NFCReader

config = yaml.load(file("config.yml"))

Playing = False

# connect to the web service and get the track link
def get_track_online(id):
  url = config['web_service'] + "/" + id
  res = json.load(urllib2.urlopen(url))
  if res:
    return res[0]['track']
  else:
    return None

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
  Playing = True
  t = threading.Thread(target=timelimit)
  t.start()

def pause():
  session.player.pause()

def timelimit():
  playing.set()
  session.player.play()
  time.sleep(config['entrance_length'])
  pause()
  playing.clear()
  print "Done playing"
  return

def nfc_run(nfcr):
  while nfcr.run():
    time.sleep(0.1)

def exit_gracefully(signum, frame):
  signal.signal(signal.SIGINT, original_sigint)
  sys.exit(1)

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
playing = threading.Event()

if __name__ == '__main__':
    logger = logging.getLogger("cardhandler").info

    # spotify
    session.on(
      spotify.SessionEvent.CONNECTION_STATE_UPDATED, on_connection_state_updated)
    session.on(spotify.SessionEvent.END_OF_TRACK, on_end_of_track)
    session.login(config['spotify']['user'], config['spotify']['pass'] )
    logged_in.wait()
    
    nfcr = NFCReader(logger)
    t = threading.Thread(target=nfc_run,args=(nfcr,))
    t.start()

    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, exit_gracefully)

    print "OK GO"
    while True:
        card_id = nfcr.card_id()
        if card_id != None:
          print "Got back card id:",card_id
          if playing.is_set():
            print "Already playing! Wait your turn!"
          else:
            print "Getting track from db"
            track = get_track_online(card_id)
            if track:
              play(track)
            else: 
              print "Card ID not found"
        time.sleep(0.1)
        pass
