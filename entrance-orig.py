#!/usr/bin/python
import os
import pprint
import signal
import sys
import threading
import time

import spotify
import RPi.GPIO as GPIO

LED_RED = 18
LED_GREEN = 23 
BUTTON = 25
ENTRANCE_LENGTH =30 
playing = False

if sys.argv[1:]:
 track_uri = sys.argv[1]
else:
  # because Seth Rollins
  track_uri = "https://open.spotify.com/track/0RmrR9GMr2Y4iie4f3gK4y"

### Bunch of stuff stolen from pyspotify play_track.py

def on_connection_state_updated(session):
  if session.connection.state is spotify.ConnectionState.LOGGED_IN:
    logged_in.set()

def on_end_of_track(self):
  led_state(LED_RED,0)
  end_of_track.set()

def led_state(led, state):
    if state == 0:
      print "led off"
      GPIO.output(led, False)
      return 0
    elif state == 1:
      print "led on"
      GPIO.output(led, True)
      return 1
    elif state == 2:
      print "led blink"
      def blink(led, stop_event):
        while(stop_event.is_set()):
          GPIO.output(led, True)
          time.sleep(0.1)
          GPIO.output(led,False)
          time.sleep(0.1)
      blinking.set()
      t = threading.Thread(target=blink,args=(led,blinking))
      t.start()
      return 2

def play():
  playing = True

  # background blink. I'm not convinced this works right
  t = led_state(LED_GREEN,2)

  # can move this into initialize for preload
  track = session.get_track(track_uri).load(timeout=30)
  session.player.load(track)

  blinking.clear()
  
  led_state(LED_RED,1)
  led_state(LED_GREEN,0)
  session.player.play()
  # don't play whole track - just let it background play for a predefined amount of time, then stop
  time.sleep(ENTRANCE_LENGTH)
  pause()

def pause():
  playing = False
  led_state(LED_RED,0)
  led_state(LED_GREEN,1)
  session.player.pause()

def exit_gracefully(signum, frame):
  signal.signal(signal.SIGINT, original_sigint)
  led_state(LED_RED,0)
  led_state(LED_GREEN,0)
  sys.exit(1)

print "Initialize..."

# init GPIO first so we can show state 

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_GREEN, GPIO.OUT)
GPIO.setup(LED_RED, GPIO.OUT)
GPIO.setup(BUTTON, GPIO.IN)

led_state(LED_GREEN, 0)
led_state(LED_RED, 1)

# Assuming a spotify_appkey.key in the current dir
session = spotify.Session()

# Process events in the background
loop = spotify.EventLoop(session)
loop.start()

# Connect an audio sink
# PortAudio for OSX
audio = spotify.PortAudioSink(session)

# Events for coordination
logged_in = threading.Event()
end_of_track = threading.Event()
blinking = threading.Event()

if __name__ == "__main__":
  print "Setting up..."
  # Register event listeners
  session.on(
    spotify.SessionEvent.CONNECTION_STATE_UPDATED, on_connection_state_updated)
  session.on(spotify.SessionEvent.END_OF_TRACK, on_end_of_track)

  # this is my actual credentials, don't keep these
  session.login(os.environ["SPOTIFY_USER"], os.environ["SPOTIFY_PASS"] )

  logged_in.wait()

  original_sigint = signal.getsignal(signal.SIGINT)
  signal.signal(signal.SIGINT, exit_gracefully)

  print "Ready!"

  led_state(LED_GREEN, 1)
  led_state(LED_RED, 0)

  while True:
    if (GPIO.input(BUTTON) == False):
      print "button pushed"
      if playing == False:
        print "start track"
        play()
      else:
        pause()
      
    time.sleep(0.1);
