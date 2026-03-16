"""
04_swarm_dance.py

Goal: Advanced Swarm Control - Synchronized "Dance"
Key Concepts: HighLevelCommander, Trajectory, Synchronization

This example makes two drones perform a synchronized pattern:
1. Takeoff
2. Fly a small circle (relative to start)
3. Land

Note: Ensure drones have at least 1m spacing!
"""
import math
import time
import cflib.crtp
from cflib.crazyflie.swarm import CachedCfFactory
from cflib.crazyflie.swarm import Swarm

# List of URIs for the swarm
uris = [
    'radio://0/100/2M/247E000003',  # Drone 1
    'radio://0/80/2M/247E000008',  # Drone 2
    'radio://0/80/2M/247E000007',  # Drone 3
]

def run_sequence(scf):
    """
    This function runs on each drone.
    We use the URI to decide which 'role' the drone plays if needed,
    but here they will do the same relative motion (synchronized).
    """
    commander = scf.cf.high_level_commander
    
    # 1. Takeoff
    commander.takeoff(0.5, 2.0)
    time.sleep(3)
    
    # 2. Fly a Circle (radius 0.3m)
    # We use go_to with relative=True to fly a polygon approximation of a circle
    steps = 8
    radius = 0.3
    duration_per_step = 1.0
    
    for i in range(steps):
        angle = (i / steps) * 2 * math.pi
        next_angle = ((i + 1) / steps) * 2 * math.pi
        
        # Calculate relative movement
        x_current = radius * math.cos(angle)
        y_current = radius * math.sin(angle)
        x_next = radius * math.cos(next_angle)
        y_next = radius * math.sin(next_angle)
        
        dx = x_next - x_current
        dy = y_next - y_current
        
        # Move
        commander.go_to(dx, dy, 0, 0, duration_per_step, relative=True)
        time.sleep(duration_per_step)

    # 3. Bob up and down
    commander.go_to(0, 0, 0.2, 0, 1.0, relative=True)
    time.sleep(1)
    commander.go_to(0, 0, -0.2, 0, 1.0, relative=True)
    time.sleep(1)

    # 4. Land
    commander.land(0.0, 2.0)
    time.sleep(2)
    commander.stop()

def run_swarm():
    factory = CachedCfFactory(rw_cache='./cache')
    with Swarm(uris, factory=factory) as swarm:
        print("Connected to Swarm!")
        swarm.reset_estimators()
        print("Starting Dance...")
        swarm.parallel_safe(run_sequence)
        print("Finished!")

if __name__ == '__main__':
    cflib.crtp.init_drivers()
    run_swarm()
