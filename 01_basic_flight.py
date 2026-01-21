# """
# 01_basic_flight.py

# Goal: Connect to a Crazyflie, take off, hover, and land.
# Key Concepts: SyncCrazyflie, MotionCommander

# Prerequisites:
#     pip install cflib
# """
# import logging
# import time

# import cflib.crtp
# from cflib.crazyflie import Crazyflie
# from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
# from cflib.positioning.motion_commander import MotionCommander
# from cflib.utils import uri_helper

# # URI to the Crazyflie to connect to
# # radio://0/80/2M/E7E7E7E7E7 is the default URI
# # You can change this to match your drone's address
# URI = uri_helper.uri_from_env(default='radio://0/80/2M/247E000044')

# # Only output errors from the logging framework
# logging.basicConfig(level=logging.ERROR)

# def simple_flight(scf):
#     """
#     This function uses the MotionCommander to control the drone.
#     The MotionCommander handles the takeoff and landing automatically
#     when used as a context manager.
#     """
#     print("Taking off...")
#     with MotionCommander(scf, default_height=0.5) as mc:
#         print("Hovering...")
#         time.sleep(3)
        
#         # You can also do simple movements here
#         # mc.forward(0.5)
#         # mc.back(0.5)
        
#         print("Landing...")
#         # Landing happens automatically when exiting the 'with' block

# if __name__ == '__main__':
#     # Initialize the low-level drivers
#     cflib.crtp.init_drivers()

#     print(f"Connecting to {URI}...")
    
#     # Connect to the Crazyflie
#     # SyncCrazyflie is a wrapper that handles the connection synchronously
#     with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
#         print("Connected!")
#         simple_flight(scf)
#######################################

"""
01_basic_flight_brushless.py

Goal: Connect to a Crazyflie Bolt (Brushless), ARM motors, take off, hover, and land.
"""
import logging
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper

# URI to the Crazyflie to connect to
URI = uri_helper.uri_from_env(default='radio://0/80/2M/247E000044')

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

def simple_flight(scf):
    """
    This function uses the MotionCommander to control the drone.
    """
    print("Taking off...")
    with MotionCommander(scf, default_height=0.5) as mc:
        print("Hovering...")
        time.sleep(3)
        print("Landing...")

if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    print(f"Connecting to {URI}...")
    
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        print("Connected!")

        # --- BRUSHLESS FIX: ARMING SEQUENCE ---
        print("Arming motors...")
        scf.cf.platform.send_arming_request(True)
        time.sleep(2.0) # Wait a moment for the arming to register
        # --------------------------------------

        # Now start the flight
        simple_flight(scf)

        # Optional: Disarm after landing for safety
        print("Disarming...")
        scf.cf.platform.send_arming_request(False)