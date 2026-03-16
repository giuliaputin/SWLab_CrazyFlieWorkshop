"""
03_swarm_dance.py

Goal: Control multiple drones simultaneously.
Key Concepts: Swarm, Parallel Execution, HighLevelCommander

Note: You need TWO Crazyflies for this example.
"""
import time
import cflib.crtp
from cflib.crazyflie.swarm import CachedCfFactory
from cflib.crazyflie.swarm import Swarm

# List of URIs for the swarm
# Replace with your actual URIs
uris = [
    'radio://0/100/2M/247E000003',  # Drone 1
    'radio://0/80/2M/247E000008',  # Drone 2
    'radio://0/80/2M/247E000007',  # Drone 3
]

def take_off(scf):
    """
    Simple takeoff function for a single drone.
    This will be run in parallel for each drone.
    """
    # We use the HighLevelCommander which is designed for this
    commander = scf.cf.high_level_commander
    
    # Take off to 0.5m with 2.0 seconds duration
    commander.takeoff(0.5, 2.0)
    time.sleep(3) # Wait for takeoff to finish + hover
    
    # Land with 2.0 seconds duration
    commander.land(0.0, 2.0)
    time.sleep(2) # Wait for landing to finish
    
    commander.stop()

def run_swarm():
    # The factory handles caching of Crazyflie instances
    factory = CachedCfFactory(rw_cache='./cache')
    
    # Map URIs to Crazyflie instances
    with Swarm(uris, factory=factory) as swarm:
        print("Connected to Swarm!")
        
        # Reset estimators in parallel
        swarm.reset_estimators()
        
        print("Taking off...")
        # Run the take_off function for all drones in parallel
        # The swarm library automatically passes 'scf' to the function
        swarm.parallel_safe(take_off)
        print("Landed!")

if __name__ == '__main__':
    cflib.crtp.init_drivers()
    run_swarm()
