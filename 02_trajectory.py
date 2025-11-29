"""
02_trajectory.py

Goal: Fly a square trajectory using position setpoints.
Key Concepts: Position Setpoints, Commander, Coordinate System

The coordinate system is:
X: Front
Y: Left
Z: Up
"""
import time
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

URI = uri_helper.uri_from_env(default='radio://0/100/2M/247E000002')

def fly_square(scf):
    cf = scf.cf
    commander = cf.commander

    # Define the square path (x, y, z, yaw)
    # Flying at 0.5m height
    # Square side length: 0.5m
    sequence = [
        (0.0, 0.0, 0.5, 0),   # Hover at origin
        (0.5, 0.0, 0.5, 0),   # Move forward
        (0.5, 0.5, 0.5, 0),   # Move left
        (0.0, 0.5, 0.5, 0),   # Move backward
        (0.0, 0.0, 0.5, 0),   # Move right (back to origin)
    ]

    print("Taking off...")
    # Takeoff helper (simple ramp up)
    for z in range(10):
        commander.send_position_setpoint(0, 0, z/20.0, 0)
        time.sleep(0.1)

    print("Starting trajectory...")
    for position in sequence:
        x, y, z, yaw = position
        print(f"Going to {x}, {y}, {z}")
        
        # Send the setpoint for 2 seconds (20Hz * 2s = 40 steps)
        # We need to send setpoints continuously to keep the drone flying
        for _ in range(40):
            commander.send_position_setpoint(x, y, z, yaw)
            time.sleep(0.05)

    print("Landing...")
    # Landing helper (simple ramp down)
    for z in range(10, -1, -1):
        commander.send_position_setpoint(0, 0, z/20.0, 0)
        time.sleep(0.1)
        
    commander.send_stop_setpoint()

if __name__ == '__main__':
    cflib.crtp.init_drivers()
    
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        fly_square(scf)
