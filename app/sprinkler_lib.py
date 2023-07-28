import os
os.environ["PIGPIO_ADDR"] = "gunther"

from gpiozero import LED
from time import sleep
from datetime import datetime
from threading import Event
import signal
import sys

import logging
logging.basicConfig(filename='sprink.log', encoding='utf-8', level=logging.DEBUG)

red_txt = "\33[0;31m"
green_txt='\033[0;32m'
txt_clr_reset='\033[0m'

def mins(secs):
  return secs * 60

def color_txt(clr, txt):
  return clr + txt + txt_clr_reset

def timestamp():
  return datetime.now().strftime('%a %b %d %Y %I:%M %p')

SECTORS = {
  'Front': 'front',
  'Back': 'back'
}

sprink1 = {
  'id': '1',
  'name': "Front 1",
  'pin': LED(13),
  'sector': SECTORS['Front'],
}
sprink2 = {
  'id': '2',
  'name': "Front 2",
  'pin': LED(19),
  'sector': SECTORS['Front'],
}
sprink3 = {
  'id': '3',
  'name': "Front 3",
  'pin': LED(26),
  'sector': SECTORS['Front'],
}
sprink4 = {
  'id': '4',
  'name': "Back 4",
  'pin': LED(16),
  'sector': SECTORS['Back'],
}
sprink5 = {
  'id': '5',
  'name': "Back 5",
  'pin': LED(20),
  'sector': SECTORS['Back'],
}
sprink6 = {
  'id': '6',
  'name': "Back 6",
  'pin': LED(21),
  'sector': SECTORS['Back'],
}

SPRINK_LIST = (
  sprink1,
  sprink2,
  sprink3,
  sprink4,
  sprink5,
  sprink6
)

SPRINKS = {
  SECTORS['Front']: [
    sprink1,
    sprink2,
    sprink3
  ],
  SECTORS['Back']: [
    sprink4,
    sprink5,
    sprink6
  ]
}

SPRINK_QUEUE:list = []
SPRINK_INTERRUPT = Event()
COUNTDOWN_TIMER = ''
QUEUE_RUNNING = False
DURATION_BETWEEN_ACTIVATION = 5

def get_sprinks_by_ids(ids):
  filtered_list = []
  for sprink in SPRINK_LIST:
    if sprink['id'] in ids:
      filtered_list.append(sprink)
  return filtered_list



def run_sprinks(sprink_list, dur_on = 5):
  print('💦 Adding sprinks to the queue', [sprink['id'] for sprink in sprink_list], 'for', dur_on, 'seconds')
  for sprink in sprink_list:
    queue_sprink(sprink['id'], dur_on)
  if not QUEUE_RUNNING:
    run_sprink_queue()



def run_sprink_queue():
  global SPRINK_QUEUE, SPRINK_INTERRUPT, QUEUE_RUNNING
  # if the queue is already running exit out.
  if (QUEUE_RUNNING): return

  # setup a new interrupt
  SPRINK_INTERRUPT = Event()
  QUEUE_RUNNING = True

  print('💦 Starting up sprinks! 💦')

  # for each sprink in the queue
  while SPRINK_QUEUE:
    queue_item = SPRINK_QUEUE[0]
    sprink_id = queue_item['id']
    sprink_duration = queue_item['duration']
    print('SPRINK_QUEUE', SPRINK_QUEUE)
    # get the sprink object
    sprink = get_sprinks_by_ids([sprink_id])[0]
    # turn on the sprink, and wait for it to finish
    queue_item['started_at'] = timestamp()
    turn_on_sprink(sprink, sprink_duration)
    queue_item['completed_at'] = timestamp()
    print('Queue item completed', queue_item)
    # after it's finished running, shut it off
    shut_off_sprink(sprink)
    # dequeue the sprink that just ran
    dequeue_sprink(queue_item)
    # pause between sprink activations to let water pressure stabilize
    sleep(DURATION_BETWEEN_ACTIVATION)

  print('Sprink queue complete!')
  QUEUE_RUNNING = False



# Turn on a single sprink, update countdown, and wait
def turn_on_sprink(sprink, dur_on = 15):
  global SPRINK_INTERRUPT
  # turn on the sprink
  sprink['pin'].on()
  # log the activation
  print(color_txt(green_txt, 'Activating:'), '\"{}\" at {} - {} for {}secs'.format(sprink['name'], sprink['pin'].pin, "ON" if sprink['pin'].is_active else "OFF", dur_on))
  # update the countdown
  countdown(dur_on, SPRINK_INTERRUPT)
  print('countdown complete for', sprink['id'])


def countdown(t, interrupt):
  global COUNTDOWN_TIMER
  t = int(t)
  # while the timer is > 0
  while t:
    # if the interrupt is tripped exit the countdown
    if (interrupt.is_set()):
      print('countdown interrupted')
      return False
    # update the timer
    mins, secs = divmod(t, 60)
    COUNTDOWN_TIMER = '{:02d}:{:02d}'.format(mins, secs)
    print(COUNTDOWN_TIMER, end="\r")
    # decrement the timer
    t -= 1
    # wait for next update
    sleep(1)
  # when the timer reaches zero
  COUNTDOWN_TIMER = '{:02d}:{:02d}'.format(0, 0)
  print(COUNTDOWN_TIMER, end="\r")
  print('countdown complete')


def shut_off_all_sprinks():
  global SPRINK_INTERRUPT, SPRINK_QUEUE
  # trip interrupt
  SPRINK_INTERRUPT.set()
  SPRINK_INTERRUPT = Event()
  # empty the queue
  SPRINK_QUEUE = []
  # shut off all sprinks
  for sprink in SPRINK_LIST:
    shut_off_sprink(sprink)

def shut_off_sprink(sprink):
  sprink['pin'].off()
  print(color_txt(red_txt, 'Deactivating:'), '\"{}\" at {} - {}'.format(sprink['name'], sprink['pin'].pin, "ON" if sprink['pin'].is_active else "OFF"))


def queue_sprink(sprink_id, duration):
  global SPRINK_QUEUE
  queued_sprink = {'id':sprink_id, 'duration':duration, 'queued_at':timestamp()}
  SPRINK_QUEUE.append(queued_sprink)

def dequeue_sprink(queue_item):
  global SPRINK_QUEUE
  if (queue_item in SPRINK_QUEUE):
    SPRINK_QUEUE.remove(queue_item)


def get_sprink_status():
  return {
    'sprinks': [{
      'id': sprink['id'],
      'name': sprink['name'],
      'sector': sprink['sector'],
      'is_active': sprink['pin'].is_active,
      'pin': sprink['pin'].pin,
    } for sprink in SPRINK_LIST],
    'queue': SPRINK_QUEUE,
    'timer': COUNTDOWN_TIMER,
  }

def graceful_shutdown(sig, frame):
  print('\n☀️  Shutting off sprinklers!');
  shut_off_all_sprinks()
  sys.exit(0)

signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)
signal.signal(signal.SIGUSR2, graceful_shutdown)

# signal.pause();

# ps aux | grep colinsharp | grep sprink
# kill -SIGINT $pid
