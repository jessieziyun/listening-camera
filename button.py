import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library
import time

#from cv import generate_haiku, to_speech
from cv import *

GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)

def button_pressed(channel):
  print("Generating haiku")
  haiku = generate_haiku()
  print("-" * 40)
  print(haiku)
  print("-" * 40)
  to_speech(haiku)

GPIO.add_event_detect(3, GPIO.RISING, callback=button_pressed, bouncetime=1000)  # add rising edge detection on a channel

while True:
    pass
