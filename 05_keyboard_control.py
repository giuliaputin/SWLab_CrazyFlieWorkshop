"""
05_keyboard_control.py

Goal: Control the drone using the keyboard.
Key Concepts: Real-time Input, Setpoints

Prerequisites:
    pip install pynput

Controls:
    Arrow Keys: Move Forward/Backward/Left/Right
    W/S: Up/Down
    A/D: Rotate Yaw
    Space: Land/Stop
"""
import logging
import sys
import time
from threading import Thread

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper
from pynput import keyboard

# URI to the Crazyflie to connect to
URI = uri_helper.uri_from_env(default='radio://0/100/2M/247E000002')

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

class KeyboardController:
    def __init__(self, scf):
        self.scf = scf
        self.cf = scf.cf
        
        # Current setpoints
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.yaw_rate = 0.0
        self.running = True
        self.flying = False

        # Constants
        self.VELOCITY = 0.5 # m/s
        self.RATE = 360.0 # deg/s

        # Start the control loop
        Thread(target=self._control_loop).start()

    def on_press(self, key):
        if not self.flying:
            return

        try:
            if key == keyboard.Key.up:
                self.vx = self.VELOCITY
            elif key == keyboard.Key.down:
                self.vx = -self.VELOCITY
            elif key == keyboard.Key.left:
                self.vy = self.VELOCITY
            elif key == keyboard.Key.right:
                self.vy = -self.VELOCITY
            elif key.char == 'w':
                self.vz = self.VELOCITY
            elif key.char == 's':
                self.vz = -self.VELOCITY
            elif key.char == 'a':
                self.yaw_rate = self.RATE
            elif key.char == 'd':
                self.yaw_rate = -self.RATE
            elif key == keyboard.Key.space:
                self.flying = False
        except AttributeError:
            pass

    def on_release(self, key):
        try:
            if key == keyboard.Key.up or key == keyboard.Key.down:
                self.vx = 0.0
            elif key == keyboard.Key.left or key == keyboard.Key.right:
                self.vy = 0.0
            elif key.char == 'w' or key.char == 's':
                self.vz = 0.0
            elif key.char == 'a' or key.char == 'd':
                self.yaw_rate = 0.0
        except AttributeError:
            if key == keyboard.Key.space:
                # Emergency stop or land
                pass

    def _control_loop(self):
        print("Waiting for takeoff...")
        # Simple takeoff
        commander = self.cf.high_level_commander
        commander.takeoff(0.5, 2.0)
        time.sleep(3)
        self.flying = True
        print("Ready! Use arrow keys and W/S/A/D.")

        while self.running and self.flying:
            # Send velocity setpoints
            # We use the low-level commander for direct velocity control
            self.cf.commander.send_velocity_world_setpoint(
                self.vx, self.vy, self.vz, self.yaw_rate
            )
            time.sleep(0.1)
        
        print("Landing...")
        commander.land(0.0, 2.0)
        time.sleep(2)
        commander.stop()
        self.running = False

def run_keyboard_control(scf):
    controller = KeyboardController(scf)
    
    # Collect events until released
    with keyboard.Listener(
            on_press=controller.on_press,
            on_release=controller.on_release) as listener:
        
        while controller.running:
            time.sleep(0.1)
        
        listener.stop()

if __name__ == '__main__':
    cflib.crtp.init_drivers()
    
    print(f"Connecting to {URI}...")
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        run_keyboard_control(scf)
