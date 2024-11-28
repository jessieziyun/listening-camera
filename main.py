import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library
from cv import generate_audio  # Import the generate_audio function from cv.py

def main():
    GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering

    button_pin = 3

    GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    ButtonHandler(button_pin, GPIO.FALLING, button_callback)

    message = input("Press enter to quit\n\n")  # Run until enter key pressed

def button_callback(args):
    # print("Button pressed, generating audio...")
    try:
        timestamp = int(time.time())
        generate_audio(timestamp)  # Call the function to generate audio
    except Exception as e:
        print(f"Error generating audio: {e}")

import threading
import time

class ButtonHandler():
    def __init__(self, pin, edge, func, cooldown_time_s=0.1):
        self.pin = pin
        self.edge = edge
        self.func = func
        self.cooldown_time_s = cooldown_time_s  # The time after a found trigger until another trigger can happen in seconds
        self.last_trigger = 0
        self.trigger_count = 0
        self.lock = threading.Lock()

        GPIO.add_event_detect(pin, edge, callback=self)

    def __call__(self, *args):
        if time.time() < self.last_trigger + self.cooldown_time_s:
            # print("Looking for trigger blocked because still on cooldown")
            return

        if not self.lock.acquire(blocking=False):
            # print("Looking for trigger blocked because already looking")
            return

        t = threading.Thread(None, self.look_for_triggers, args=args, daemon=True)
        t.start()

    def look_for_triggers(self, *args):
        if self.edge == GPIO.FALLING:
            trigger_value = GPIO.LOW
        elif self.edge == GPIO.RISING:
            trigger_value = GPIO.HIGH
        else:
            raise Exception("Either rising or falling edge, both makes no sense?")

        for i in range(10):
            rate = self.check_timeframe(trigger_value, 0.02)

            if rate > 0.9:
                self.last_trigger = time.time()
                self.trigger_count += 1
                # print(f"trigger_count=({self.trigger_count})")
                self.func(*args)
                break

        self.lock.release()

    def check_timeframe(self, trigger_value, timeout_s=0.5):
        timeout_start = time.time()
        pinval_counter = 0
        poll_counter = 0

        while time.time() < timeout_start + timeout_s:
            pinval = GPIO.input(self.pin)
            if pinval == trigger_value:
                pinval_counter += 1
            poll_counter += 1

        rate = pinval_counter / poll_counter
        return rate

if __name__ == "__main__":
    try:
        main()
    finally:
        print("Execute GPIO-cleanup")
        GPIO.cleanup()
