import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library
from cv_save import *

def main():
    GPIO.setmode(GPIO.BOARD) # Use physical pin numbering

    button_pin = 3

    GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    ButtonHandler(button_pin, GPIO.FALLING, button_callback)

    message = input("Press enter to quit\n\n") # Run until someone presses enter

def button_callback(args):
    print(f"Generating haiku")
    haiku = generate_haiku()
    print(f"-" * 40)
    print(haiku)
    print(f"-" * 40)
    to_audio(hf, haiku)
    # print(audio)
    to_speech(haiku)


import threading
import time

class ButtonHandler():
    def __init__(self, pin, edge, func, cooldown_time_s = 0.1):

        self.pin = pin
        self.edge = edge
        self.func = func
        self.cooldown_time_s = cooldown_time_s  # The time after a found trigger until another trigger can happen in seconds
        self.last_trigger = 0
        self.trigger_count = 0
        self.lock = threading.Lock()

        GPIO.add_event_detect(pin, edge, callback=self)

    def __call__(self, *args):
        # print("trigger")

        if time.time() < self.last_trigger + self.cooldown_time_s:
            print("Looking for trigger blocked because still on cooldown")
            return

        if not self.lock.acquire(blocking=False):
            print("Looking for trigger blocked because already looking")
            return

        t = threading.Thread(None, self.look_for_triggers, args=args, daemon=True)
        t.start()

    def look_for_triggers(self, *args):

        if self.edge == GPIO.FALLING:
            trigger_value = GPIO.LOW
            # print("count low")
        elif self.edge == GPIO.RISING:
            trigger_value = GPIO.HIGH
             # print("count high")
        else:
            raise Exception("Either rising or falling edge, both makes no sence?")

        # Look 10 timeframes for a button-trigger
        for i in range(10):
            # Look in 20ms intervals for triggers
            rate = self.check_timeframe(trigger_value, 0.02)
            # print(f"rate={rate}")

            # If the watched timeframe contains a minimum of 90% the trigger_value, then a button-trigger is detected
            if rate > 0.9:
                self.last_trigger = time.time()
                self.trigger_count += 1
                print(f"trigger_count=({self.trigger_count})")
                self.func(*args)
                break

        self.lock.release()

    def check_timeframe(self, trigger_value, timeout_s = 0.5):
        """
        Get the percentage the pin has the 'trigger_value' in the 'timeout_s'-timeframe
        Arguments:
            trigger_value: The value that should be counted
            timeout_s: The timeframe in which the pin will be watched
        Returns:
            The percentage the pin has the value of 'trigger_value'
        """
        timeout_start = time.time()

        pinval_counter = 0
        poll_counter = 0

        while time.time() < timeout_start + timeout_s:
            pinval = GPIO.input(self.pin)
            # print(f"Pinval={pinval} ({self.button_press_count})")
            if pinval == trigger_value:
                pinval_counter += 1

            poll_counter +=1

        timeout_stop = time.time()
        # print(f"start={timeout_start} stop={timeout_stop} poll_counter={poll_counter} pinval_counter={pinval_counter}")

        rate = pinval_counter / poll_counter
        return rate


if __name__ == "__main__":
    hf = load_space()
    try:
        main()
    finally:
        print("Execute GPIO-cleanup")
        # Cleanup is important when working with interrupts, so the pins not remain blocked. When used by another program.
        GPIO.cleanup()
