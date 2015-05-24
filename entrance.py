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
  loading.clear()
  print "Play"
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

def pi_monitor():
  import RPi.GPIO as GPIO
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(config['platform']['red'], GPIO.OUT)
  GPIO.setup(config['platform']['green'], GPIO.OUT)

  while True:
    if playing.is_set():
      GPIO.output(config['platform']['red'], True)
      GPIO.output(config['platform']['green'], False)
    elif loading.is_set():
      GPIO.output(config['platform']['green'], False)
      while loading.is_set():
        GPIO.output(config['platform']['red'], True)
        time.sleep(0.1)
        GPIO.output(config['platform']['red'], False)
        time.sleep(0.1)
    else:
      GPIO.output(config['platform']['red'], False)
      GPIO.output(config['platform']['green'], True)

# Assuming a spotify_appkey.key in the current dir
session = spotify.Session()

# Process events in the background
loop = spotify.EventLoop(session)
loop.start()

# Connect an audio sink
if config['audiosink'] == 'portaudio':
  audio = spotify.PortAudioSink(session)
elif config['audiosink'] == 'alsaaudio':
  audio = spotify.AlsaSink(session)
else:
  print "No valid audio sink config, using default"
  audio = spotify.AlsaSink(session)

# Events for coordination
logged_in = threading.Event()
end_of_track = threading.Event()
playing = threading.Event()
loading = threading.Event()

if __name__ == '__main__':
    if config['platform']['name'] == "raspberrypi":
      t = threading.Thread(target=pi_monitor)
      t.start()


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
            loading.set()
            print "Getting track from db"
            track = get_track_online(card_id)
            if track:
              play(track)
            else: 
              print "Card ID not found"
        time.sleep(0.1)
        pass
