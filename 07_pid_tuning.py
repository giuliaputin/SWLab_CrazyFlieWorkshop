"""
07_pid_tuning.py

Goal: Real-time PID Tuning
Key Concepts: Control Theory, Parameter Framework, Stability

This example allows you to tune the Roll PID controller in real-time.
WARNING: Be careful! Unstable gains can cause the drone to crash.

Controls:
    Enter: Takeoff
    Space: Land/Stop
    
    1 / 2: Decrease / Increase Roll KP (Proportional)
    3 / 4: Decrease / Increase Roll KI (Integral)
    5 / 6: Decrease / Increase Roll KD (Derivative)
"""
import logging
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

class PIDTuner:
    def __init__(self, scf):
        self.scf = scf
        self.cf = scf.cf
        self.running = True
        self.flying = False
        
        # Initial Gains (will be read from drone)
        self.kp = 0.0
        self.ki = 0.0
        self.kd = 0.0
        
        # Parameter names
        self.PARAM_KP = 'pid_attitude.roll_kp'
        self.PARAM_KI = 'pid_attitude.roll_ki'
        self.PARAM_KD = 'pid_attitude.roll_kd'

        # Read initial values
        print("Reading initial parameters...")
        # We need to wait a bit for params to be available if we just connected
        time.sleep(1) 
        self.kp = float(self.cf.param.get_value(self.PARAM_KP))
        self.ki = float(self.cf.param.get_value(self.PARAM_KI))
        self.kd = float(self.cf.param.get_value(self.PARAM_KD))
        
        print(f"Initial Gains -> KP: {self.kp:.2f}, KI: {self.ki:.2f}, KD: {self.kd:.2f}")

        # Start the control loop thread (handles flight)
        Thread(target=self._flight_loop).start()

    def update_param(self, name, value):
        self.cf.param.set_value(name, value)
        print(f"Updated {name} to {value:.2f}")

    def on_press(self, key):
        STEP = 0.5 # Step size for tuning
        
        try:
            if key == keyboard.Key.enter:
                if not self.flying:
                    self.flying = True
                    print("Taking off...")
            elif key == keyboard.Key.space:
                self.flying = False
                print("Landing...")
            
            # Tuning Keys
            elif hasattr(key, 'char'):
                if key.char == '1':
                    self.kp -= STEP
                    self.update_param(self.PARAM_KP, self.kp)
                elif key.char == '2':
                    self.kp += STEP
                    self.update_param(self.PARAM_KP, self.kp)
                elif key.char == '3':
                    self.ki -= STEP
                    self.update_param(self.PARAM_KI, self.ki)
                elif key.char == '4':
                    self.ki += STEP
                    self.update_param(self.PARAM_KI, self.ki)
                elif key.char == '5':
                    self.kd -= STEP
                    self.update_param(self.PARAM_KD, self.kd)
                elif key.char == '6':
                    self.kd += STEP
                    self.update_param(self.PARAM_KD, self.kd)
                    
        except AttributeError:
            pass

    def _flight_loop(self):
        commander = self.cf.high_level_commander
        
        while self.running:
            if self.flying:
                # Takeoff if not already flying (handled by logic flag, but commander handles state)
                # We just send a setpoint to stay in air
                # Actually, high level commander needs explicit takeoff
                commander.takeoff(0.5, 2.0)
                
                # We just hover while the user tunes
                while self.flying and self.running:
                    time.sleep(0.1)
                
                # Land when loop breaks
                commander.land(0.0, 2.0)
                time.sleep(2)
                commander.stop()
            
            time.sleep(0.1)

def run_tuner(scf):
    tuner = PIDTuner(scf)
    
    print("Controls:")
    print("  Enter: Takeoff")
    print("  Space: Land")
    print("  1/2: -/+ KP")
    print("  3/4: -/+ KI")
    print("  5/6: -/+ KD")
    
    with keyboard.Listener(on_press=tuner.on_press) as listener:
        listener.join()
        tuner.running = False

if __name__ == '__main__':
    cflib.crtp.init_drivers()
    
    print(f"Connecting to {URI}...")
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        run_tuner(scf)
